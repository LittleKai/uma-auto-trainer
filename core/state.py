import re
from PIL import Image
import time
from utils.screenshot import capture_region, enhanced_screenshot
from core.ocr import extract_text, extract_number
from core.recognizer import match_template
from core.race_manager import DateManager

from utils.constants import (
  SUPPORT_CARD_ICON_REGION, MOOD_REGION, TURN_REGION, FAILURE_REGION,
  YEAR_REGION, MOOD_LIST, CRITERIA_REGION, ENERGY_BAR, MOOD_PATTERNS,
  STAT_REGIONS, get_current_regions
)

# Global variable to store current date info
current_date_info = None

def stat_state():
  """Get current character stats using configurable regions"""
  # Get current region settings in case they were updated
  current_regions = get_current_regions()
  stat_regions = current_regions['STAT_REGIONS']

  raw_values = {}
  result = {}

  # Read raw OCR values first
  for stat, region in stat_regions.items():
    img = enhanced_screenshot(region)
    raw_val = extract_number(img)
    raw_values[stat] = raw_val

    # Process the value
    digits = ''.join(filter(str.isdigit, raw_val))
    result[stat] = int(digits) if digits.isdigit() else 0

  # Create single line log with both raw and processed values
  raw_str = ", ".join([f"{stat}:'{raw_values[stat]}'" for stat in stat_regions.keys()])
  processed_str = ", ".join([f"{stat}:{result[stat]}" for stat in stat_regions.keys()])

  print(f"[STATS OCR] Raw: [{raw_str}] | Processed: [{processed_str}]")

  return result

def check_energy_percentage():
  """Check energy percentage by counting gray pixels in energy bar"""
  try:
    # Get current region settings in case they were updated
    current_regions = get_current_regions()
    energy_bar = current_regions['ENERGY_BAR']

    # Energy bar is stored as (x1, y1, x2, y2) format
    x1, y1, x2, y2 = energy_bar

    # Convert to region format (left, top, width, height) for capture
    # Use 1 pixel height for energy bar scanning
    region = (x1, y1, x2 - x1, 1)

    screenshot = capture_region(region)

    # Convert to RGB if needed
    if screenshot.mode != 'RGB':
      screenshot = screenshot.convert('RGB')

    # Count pixels with gray color (RGB: 118, 117, 118 which is hex 767576)
    target_color = (118, 117, 118)
    gray_pixel_count = 0
    total_width = x2 - x1

    # Check each pixel in the horizontal line
    for x in range(total_width):
      try:
        pixel_color = screenshot.getpixel((x, 0))
        # Allow some tolerance for color matching (±2 for each RGB component)
        if (abs(pixel_color[0] - target_color[0]) <= 2 and
                abs(pixel_color[1] - target_color[1]) <= 2 and
                abs(pixel_color[2] - target_color[2]) <= 2):
          gray_pixel_count += 1
      except:
        continue

    # Calculate energy percentage
    # Formula: 100 - (gray_pixels * 100 / total_width)
    energy_percentage = 100 - (gray_pixel_count * 100 / total_width)

    # Clamp between 0 and 100
    energy_percentage = max(0, min(100, energy_percentage))

    return round(energy_percentage, 1)

  except Exception as e:
    print(f"[WARNING] Energy detection failed: {e}")
    return 100  # Return 100% if detection fails (safe default)

def match_mood_with_patterns(ocr_text):
  """Enhanced mood detection with pattern matching for OCR errors"""
  ocr_text = ocr_text.upper().strip()

  # First try exact match
  if ocr_text in MOOD_LIST:
    return ocr_text

  # Try pattern matching for each mood
  for mood, patterns in MOOD_PATTERNS.items():
    for pattern in patterns:
      # Direct match
      if pattern == ocr_text:
        print(f"[INFO] Mood pattern matched: '{ocr_text}' -> {mood}")
        return mood

      # Partial match for missing characters
      if len(ocr_text) >= 2:
        # Check if OCR text is contained in pattern (missing end characters)
        if pattern.startswith(ocr_text):
          print(f"[INFO] Mood partial match (missing end): '{ocr_text}' -> {mood}")
          return mood

        # Check if pattern is contained in OCR text (missing start characters)
        if ocr_text.endswith(pattern):
          print(f"[INFO] Mood partial match (missing start): '{ocr_text}' -> {mood}")
          return mood

        # Check for character substitution (allow 1-2 character differences)
        if len(pattern) == len(ocr_text):
          differences = sum(1 for a, b in zip(pattern, ocr_text) if a != b)
          if differences <= 2:
            print(f"[INFO] Mood fuzzy match ({differences} differences): '{ocr_text}' -> {mood}")
            return mood

  print(f"[WARNING] Mood not recognized with patterns: '{ocr_text}'")
  return "UNKNOWN"

def validate_region_coordinates(region):
  """Validate region coordinates to prevent PyAutoGUI errors"""
  if not region or len(region) != 4:
    print(f"[ERROR] Invalid region format: {region}")
    return None

  left, top, width, height = region

  # Check for valid coordinate types
  try:
    left, top, width, height = int(left), int(top), int(width), int(height)
  except (ValueError, TypeError):
    print(f"[ERROR] Invalid coordinate types in region: {region}")
    return None

  # Check for positive dimensions
  if width <= 0 or height <= 0:
    print(f"[ERROR] Invalid region dimensions - width: {width}, height: {height}")
    return None

  # Check for reasonable coordinates (not negative)
  if left < 0 or top < 0:
    print(f"[WARNING] Negative coordinates detected - left: {left}, top: {top}")

  return (left, top, width, height)

def check_support_card(threshold=0.8, is_pre_debut=False, training_type=None, current_date=None):
  """Check support card in each training with correct Pre-Debut score calculation"""
  # Get current region settings in case they were updated
  current_regions = get_current_regions()
  support_region = current_regions['SUPPORT_CARD_ICON_REGION']

  SUPPORT_ICONS = {
    "spd": "assets/icons/support_card_type_spd.png",
    "sta": "assets/icons/support_card_type_sta.png",
    "pwr": "assets/icons/support_card_type_pwr.png",
    "guts": "assets/icons/support_card_type_guts.png",
    "wit": "assets/icons/support_card_type_wit.png",
    "friend": "assets/icons/support_card_type_friend1.png"
  }

  # NPC support icons grouped as 'npc'
  NPC_ICONS = {
    "akikawa": "assets/icons/support_npc_akikawa.png",
    "etsuko": "assets/icons/support_npc_etsuko.png"
  }

  count_result = {}

  time.sleep(0.3)

  # Count regular support cards
  for key, icon_path in SUPPORT_ICONS.items():
    matches = match_template(icon_path, support_region, threshold)
    count_result[key] = len(matches)

  # Count NPC support cards and group them as 'npc'
  total_npc_count = 0
  for npc_name, icon_path in NPC_ICONS.items():
    matches = match_template(icon_path, support_region, threshold)
    npc_found = len(matches)
    total_npc_count += npc_found

  # Add grouped NPC count
  count_result["npc"] = total_npc_count

  # Find hint cards
  hint_matches = match_template("assets/icons/support_card_hint.png", support_region, threshold)
  hint_count = len(hint_matches)

  # Calculate hint score based on day - maximum 1 hint counts for score
  hint_score = 0
  if hint_count > 0 and current_date:
    absolute_day = current_date.get('absolute_day', 0)

    if absolute_day < 24:
      hint_score = 1.0
    else:
      hint_score = 0.5

  # Calculate NPC score - each NPC adds 0.5 score
  npc_score = total_npc_count * 0.5

  # Determine career stage based on absolute day with corrected definitions
  absolute_day = current_date.get('absolute_day', 0) if current_date else 0

  # Updated stage determination:
  # Pre-Debut: Days 1-16
  # Early: Days 1-24 (includes Pre-Debut)
  # Mid: Days 25-48
  # Late: Days 49-72
  is_pre_debut = absolute_day <= 16
  is_early_stage = absolute_day <= 24
  is_mid_stage = 25 <= absolute_day <= 48
  is_late_stage = absolute_day > 48

  # Handle friend cards in Pre-Debut period - convert to current training type
  if is_pre_debut and count_result["friend"] > 0 and training_type:
    friend_count = count_result["friend"]
    # Add friend cards to the current training type count
    count_result[training_type] = count_result.get(training_type, 0) + friend_count
    # Set friend count to 0 since they're now counted as training type
    count_result["friend"] = 0

  # Calculate total support (excluding hint and NPC)
  total_support = sum(count for key, count in count_result.items()
                      if key not in ["hint", "npc"])

  # Calculate total score based on career stage
  if is_pre_debut:
    # Pre-debut (Days 1-16): all support = 1 point each, no rainbow bonus
    # FIXED: Simple calculation for Pre-Debut
    total_score = total_support + hint_score + npc_score

  elif is_early_stage:
    # Early stage (Days 17-24): all support = 1 point each, no rainbow bonus yet
    total_score = total_support + hint_score + npc_score

  elif is_mid_stage:
    # Mid stage (Days 25-48): rainbow cards = 2 points, friend cards = 0.75 points, others = 1 point
    if training_type:
      rainbow_count = count_result.get(training_type, 0)
      friend_count = count_result.get("friend", 0)
      other_support = total_support - rainbow_count - friend_count

      rainbow_score = rainbow_count * 2.0
      friend_score = friend_count * 0.75
      other_score = other_support * 1.0

      total_score = rainbow_score + friend_score + other_score + hint_score + npc_score
    else:
      # No training type specified, treat friend cards as 0.75 points
      friend_count = count_result.get("friend", 0)
      other_support = total_support - friend_count
      friend_score = friend_count * 0.75
      other_score = other_support * 1.0

      total_score = friend_score + other_score + hint_score + npc_score

  elif is_late_stage:
    # Late stage (Days 49-72): rainbow cards = 2.5 points, friend cards = 0.75 points, others = 1 point
    if training_type:
      rainbow_count = count_result.get(training_type, 0)
      friend_count = count_result.get("friend", 0)
      other_support = total_support - rainbow_count - friend_count

      rainbow_score = rainbow_count * 2.5
      friend_score = friend_count * 0.75
      other_score = other_support * 1.0

      total_score = rainbow_score + friend_score + other_score + hint_score + npc_score
    else:
      # No training type specified, treat friend cards as 0.75 points
      friend_count = count_result.get("friend", 0)
      other_support = total_support - friend_count
      friend_score = friend_count * 0.75
      other_score = other_support * 1.0

      total_score = friend_score + other_score + hint_score + npc_score

  else:
    # Fallback: all = 1 point
    total_score = total_support + hint_score + npc_score

  # Add additional info to results
  count_result["hint"] = hint_count
  count_result["hint_score"] = hint_score
  count_result["npc_count"] = total_npc_count
  count_result["npc_score"] = npc_score
  count_result["total_score"] = total_score

  return count_result

def check_failure():
  """Get failure chance from UI region"""
  # Get current region settings in case they were updated
  current_regions = get_current_regions()
  failure_region = current_regions['FAILURE_REGION']

  failure = enhanced_screenshot(failure_region)
  failure_text = extract_text(failure).lower()

  if not failure_text.startswith("failure"):
    return -1

  # Extract percentage from failure text
  # 1. If there is a %, extract the number before the %
  match_percent = re.search(r"failure\s+(\d{1,3})%", failure_text)
  if match_percent:
    return int(match_percent.group(1))

  # 2. If there is no %, but there is a 9, extract digits before the 9
  match_number = re.search(r"failure\s+(\d+)", failure_text)
  if match_number:
    digits = match_number.group(1)
    idx = digits.find("9")
    if idx > 0:
      num = digits[:idx]
      return int(num) if num.isdigit() else -1
    elif digits.isdigit():
      return int(digits)  # fallback

  return -1

def check_mood():
  """Enhanced mood check with pattern matching"""
  # Get current region settings in case they were updated
  current_regions = get_current_regions()
  mood_region = current_regions['MOOD_REGION']

  mood = capture_region(mood_region)
  mood_text = extract_text(mood).upper()

  # Use enhanced pattern matching for mood detection
  detected_mood = match_mood_with_patterns(mood_text)

  if detected_mood != "UNKNOWN":
    return detected_mood

  # Fallback: try original method for exact matches
  for known_mood in MOOD_LIST:
    if known_mood in mood_text:
      return known_mood

  print(f"[WARNING] Mood not recognized: {mood_text}")
  return "UNKNOWN"

def check_turn():
  """Check current turn number or race day"""
  # Get current region settings in case they were updated
  current_regions = get_current_regions()
  turn_region = current_regions['TURN_REGION']

  turn = enhanced_screenshot(turn_region)
  turn_text = extract_text(turn)
  print(f"Turn detected: {turn_text}")

  if "Race" in turn_text:
    return "Race Day"

  # Sometimes OCR misreads characters instead of numbers
  cleaned_text = (
    turn_text
      .replace("T", "1")
      .replace("I", "1")
      .replace("O", "0")
      .replace("S", "5")
  )

  digits_only = re.sub(r"[^\d]", "", cleaned_text)

  if digits_only:
    return int(digits_only)

  return -1

def check_current_year():
  """Enhanced year checking with date parsing"""
  global current_date_info

  # Get current region settings in case they were updated
  current_regions = get_current_regions()
  year_region = current_regions['YEAR_REGION']

  year = enhanced_screenshot(year_region)
  text = extract_text(year)

  # Parse the year text to extract date information
  current_date_info = DateManager.parse_year_text(text)

  if current_date_info is None:
    print(f"[ERROR] Failed to parse year text: {text}")
    # Stop the program if date parsing fails after retries
    raise Exception(f"Critical error: Cannot parse date from OCR text: {text}")

  return text

def get_current_date_info():
  """Get the current parsed date information"""
  return current_date_info

def check_criteria():
  """Check criteria text from UI region"""
  # Get current region settings in case they were updated
  current_regions = get_current_regions()
  criteria_region = current_regions['CRITERIA_REGION']

  img = enhanced_screenshot(criteria_region)
  text = extract_text(img)
  return text