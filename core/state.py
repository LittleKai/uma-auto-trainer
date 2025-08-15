import re
from PIL import Image

from utils.screenshot import capture_region, enhanced_screenshot
from core.ocr import extract_text, extract_number
from core.recognizer import match_template
from core.race_manager import DateManager

from utils.constants import SUPPORT_CARD_ICON_REGION, MOOD_REGION, TURN_REGION, FAILURE_REGION, YEAR_REGION, MOOD_LIST, CRITERIA_REGION, ENERGY_BAR, MOOD_PATTERNS

# Global variable to store current date info
current_date_info = None

# Get Stat
def stat_state():

  stat_regions = {
    "spd": (310, 723, 55, 20),
    "sta": (405, 723, 55, 20),
    "pwr": (500, 723, 55, 20),
    "guts": (595, 723, 55, 20),
    "wit": (690, 723, 55, 20)
  }

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

# Check energy percentage by counting gray pixels in energy bar
def check_energy_percentage():
  """
  Check energy percentage by counting pixels with color 767576 in energy bar
  Returns energy percentage (0-100)
  """
  try:
    # Capture the energy bar region - create a region with height of 1 pixel
    x1, y1, x2, y2 = ENERGY_BAR
    # Create region (left, top, width, height)
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

# Enhanced mood detection with pattern matching for OCR errors
def match_mood_with_patterns(ocr_text):
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

# Check support card in each training with NPC grouping
def check_support_card(threshold=0.8, is_pre_debut=False, training_type=None, current_date=None):
  SUPPORT_ICONS = {
    "spd": "assets/icons/support_card_type_spd2.png",
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

  # Count regular support cards
  for key, icon_path in SUPPORT_ICONS.items():
    matches = match_template(icon_path, SUPPORT_CARD_ICON_REGION, threshold)
    count_result[key] = len(matches)

  # Count NPC support cards and group them as 'npc'
  total_npc_count = 0
  for npc_name, icon_path in NPC_ICONS.items():
    matches = match_template(icon_path, SUPPORT_CARD_ICON_REGION, threshold)
    npc_found = len(matches)
    total_npc_count += npc_found

  # Add grouped NPC count
  count_result["npc"] = total_npc_count

  # Find hint cards
  hint_matches = match_template("assets/icons/support_card_hint.png", SUPPORT_CARD_ICON_REGION, threshold)
  hint_count = len(hint_matches)

  # Calculate hint score based on day - maximum 1 hint counts for score
  hint_score = 0
  if hint_count > 0 and current_date:
    absolute_day = current_date.get('absolute_day', 0)
    # Only count 1 hint maximum for score calculation
    effective_hints = min(hint_count, 1)

    if absolute_day < 36:
      hint_score = effective_hints * 1.0  # Each hint = 1 point (max 1)
    else:
      hint_score = effective_hints * 0.5  # Each hint = 0.5 point (max 1)

  # Calculate NPC score - each NPC adds 0.5 score
  npc_score = total_npc_count * 0.5

  # Determine career stage based on absolute day
  absolute_day = current_date.get('absolute_day', 0) if current_date else 0

  # Stage determination: Pre-debut (day < 24), Mid stage (24-48), Late stage (>48)
  is_mid_stage = 24 <= absolute_day <= 48
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
    # Pre-debut: all support = 1 point each, no rainbow bonus
    total_score = total_support + hint_score + npc_score

  elif is_mid_stage:
    # Mid stage (day 24-48): rainbow cards = 2 points, friend cards = 0.75 points, others = 1 point
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
    # Late stage (day > 48): rainbow cards = 2.5 points, friend cards = 0.75 points, others = 1 point
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
    # Early stage (day < 24 but not pre-debut): all = 1 point
    total_score = total_support + hint_score + npc_score

  # Add additional info to results
  count_result["hint"] = hint_count
  count_result["hint_score"] = hint_score
  count_result["npc_count"] = total_npc_count
  count_result["npc_score"] = npc_score
  count_result["total_score"] = total_score

  return count_result

# Get failure chance (kept for compatibility but not used in low energy logic)
def check_failure():
  failure = enhanced_screenshot(FAILURE_REGION)
  failure_text = extract_text(failure).lower()

  if not failure_text.startswith("failure"):
    return -1

  # SAFE CHECK
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

# Enhanced mood check with pattern matching
def check_mood():
  mood = capture_region(MOOD_REGION)
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

# Check turn
def check_turn():
  turn = enhanced_screenshot(TURN_REGION)
  turn_text = extract_text(turn)
  print(f"Turn detected: {turn_text}")

  if "Race" in turn_text:
    # if "Race Day" in turn_text:
    return "Race Day"

  # sometimes easyocr misreads characters instead of numbers
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

# Enhanced year checking with date parsing
def check_current_year():
  global current_date_info

  year = enhanced_screenshot(YEAR_REGION)
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

# Check criteria
def check_criteria():
  img = enhanced_screenshot(CRITERIA_REGION)
  text = extract_text(img)
  return text