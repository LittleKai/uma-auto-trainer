import re
import json
from PIL import Image, ImageEnhance, ImageFilter
import time
import numpy as np
from utils.screenshot import capture_region, enhanced_screenshot
from core.ocr import extract_text, extract_number, extract_text_advanced
from core.recognizer import match_template
from core.race_manager import DateManager

from utils.constants import (
  SUPPORT_CARD_ICON_REGION, MOOD_REGION, TURN_REGION, FAILURE_REGION,
  YEAR_REGION, MOOD_LIST, CRITERIA_REGION, ENERGY_BAR, MOOD_PATTERNS,
  STAT_REGIONS, get_current_regions
)

# Global variable to store current date info
current_date_info = None

def load_scoring_config():
  """Load scoring configuration from config file"""
  try:
    with open("config.json", "r", encoding="utf-8") as file:
      config = json.load(file)
    return config.get("scoring_config", {})
  except (FileNotFoundError, json.JSONDecodeError):
    return {}

def get_hint_score_value(absolute_day):
  """Get hint score value based on configuration"""
  scoring_config = load_scoring_config()
  hint_config = scoring_config.get("hint_score", {})

  day_threshold = hint_config.get("day_threshold", 24)
  early_score = hint_config.get("early_stage", 1.0)
  late_score = hint_config.get("late_stage", 0.5)

  return early_score if absolute_day < day_threshold else late_score

def get_npc_score_value():
  """Get NPC base score value from configuration"""
  scoring_config = load_scoring_config()
  npc_config = scoring_config.get("npc_score", {})
  return npc_config.get("base_value", 0.5)

def get_support_base_score():
  """Get support card base score value from configuration"""
  scoring_config = load_scoring_config()
  support_config = scoring_config.get("support_score", {})
  return support_config.get("base_value", 1.0)

def get_friend_multiplier():
  """Get friend card score multiplier from configuration"""
  scoring_config = load_scoring_config()
  support_config = scoring_config.get("support_score", {})
  return support_config.get("friend_multiplier", 1.0)

def get_rainbow_multiplier(stage):
  """Get rainbow card multiplier based on stage from configuration"""
  scoring_config = load_scoring_config()
  support_config = scoring_config.get("support_score", {})
  rainbow_config = support_config.get("rainbow_multiplier", {})

  return rainbow_config.get(stage, 1.0)

def get_stage_thresholds():
  """Get stage thresholds from configuration"""
  scoring_config = load_scoring_config()
  return scoring_config.get("stage_thresholds", {
    "pre_debut": 16,
    "early_stage": 24,
    "mid_stage": 48
  })

def calculate_unified_training_score(training_type, support_counts, current_date):
  """Calculate training score using unified logic with early stage WIT bonus"""
  # Get configuration values
  base_score = get_support_base_score()
  friend_multiplier = get_friend_multiplier()
  hint_score = support_counts.get("hint_score", 0)
  npc_score = support_counts.get("npc_score", 0)

  # Determine career stage
  stage_thresholds = get_stage_thresholds()
  absolute_day = current_date.get('absolute_day', 0) if current_date else 0

  is_pre_debut = absolute_day <= stage_thresholds.get("pre_debut", 16)
  is_early_stage = absolute_day <= stage_thresholds.get("early_stage", 24)
  is_mid_stage = stage_thresholds.get("early_stage", 24) < absolute_day <= stage_thresholds.get("mid_stage", 48)
  is_late_stage = absolute_day > stage_thresholds.get("mid_stage", 48)

  # Calculate support card scores
  rainbow_count = support_counts.get(training_type, 0)
  friend_count = support_counts.get("friend", 0)

  # Special handling for friend cards in WIT training
  friend_score = 0
  if friend_count > 0:
    if training_type == "wit":
      friend_score = friend_count * 0.5  # Friend in WIT = 0.5 score each
    else:
      friend_score = friend_count * friend_multiplier

  # Calculate other support cards (excluding rainbow, friend, and npc)
  other_support = sum(count for key, count in support_counts.items()
                      if key not in [training_type, "friend", "npc", "hint", "hint_score", "total_score", "npc_count", "npc_score"])

  if is_pre_debut or is_early_stage:
    # Pre-debut and early stage: all support = base score each, no rainbow bonus
    rainbow_multiplier = get_rainbow_multiplier('pre_debut') if is_pre_debut else get_rainbow_multiplier('early_stage')
    rainbow_score = rainbow_count * base_score
    other_score = other_support * base_score

  elif is_mid_stage:
    # Mid stage: rainbow cards get multiplier
    rainbow_multiplier = get_rainbow_multiplier('mid_stage')
    rainbow_score = rainbow_count * rainbow_multiplier
    other_score = other_support * base_score

  else:
    # Late stage: higher rainbow multiplier
    rainbow_multiplier = get_rainbow_multiplier('late_stage')
    rainbow_score = rainbow_count * rainbow_multiplier
    other_score = other_support * base_score

  total_score = rainbow_score + friend_score + other_score + hint_score + npc_score

  # Apply early stage WIT bonus (for days < 24, including Pre-Debut)
  if training_type == "wit" and absolute_day < stage_thresholds.get("early_stage", 24):
    from core.logic import get_wit_early_stage_bonus
    wit_bonus = get_wit_early_stage_bonus()
    total_score += wit_bonus

  return total_score

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

def enhance_mood_image(img):
  """Enhanced image preprocessing specifically for mood text recognition"""
  try:
    # Convert to grayscale for better OCR
    if img.mode != 'L':
      img = img.convert('L')

    # Resize image to improve OCR accuracy (3x scale)
    width, height = img.size
    img = img.resize((width * 3, height * 3), Image.LANCZOS)

    # Apply contrast enhancement
    img_array = np.array(img)

    # Simple contrast enhancement
    img_array = np.clip(img_array * 1.2 + 10, 0, 255).astype(np.uint8)
    img = Image.fromarray(img_array)

    # Apply sharpening filter
    img = img.filter(ImageFilter.SHARPEN)

    # Enhance contrast further
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)

    # Apply threshold to create clean black and white image
    threshold = 128
    img = img.point(lambda x: 255 if x > threshold else 0, mode='1')

    return img

  except Exception as e:
    print(f"[WARNING] Image enhancement failed: {e}")
    return img

def extract_mood_with_multiple_methods(img):
  """Extract text using multiple OCR configurations"""
  ocr_results = []

  try:
    # Method 1: Standard text extraction
    text1 = extract_text(img).upper().strip()
    if text1:
      ocr_results.append(text1)
      print(f"[DEBUG] OCR Method 1 (standard): '{text1}'")

    # Method 2: Character whitelist for mood words
    mood_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    text2 = extract_text_advanced(img, whitelist=mood_chars, psm=8).upper().strip()
    if text2 and text2 != text1:
      ocr_results.append(text2)
      print(f"[DEBUG] OCR Method 2 (whitelist): '{text2}'")

    # Method 4: No whitelist, different PSM
    text3 = extract_text_advanced(img, psm=13).upper().strip()
    if text3 and text3 not in ocr_results:
      ocr_results.append(text3)
      print(f"[DEBUG] OCR Method 3 (PSM 13): '{text3}'")

  except Exception as e:
    print(f"[WARNING] OCR extraction failed: {e}")

  return ocr_results

def match_mood_with_enhanced_patterns(ocr_text):
  """Enhanced mood detection with better pattern matching for GOOD vs BAD confusion"""
  if not ocr_text:
    return "UNKNOWN"

  ocr_text = ocr_text.upper().strip()
  print(f"[DEBUG] Matching mood for: '{ocr_text}' (length: {len(ocr_text)})")

  # Direct exact match first
  if ocr_text in MOOD_LIST:
    return ocr_text

  # Special handling for GOOD vs BAD confusion (highest priority)
  if len(ocr_text) >= 3:
    # Handle cases where GOOD is partially read as GOD, OOD, GOO, etc.
    good_partials = ["GOD", "OOD", "GOO", "GOOD", "GOOP", "COOO", "G00D"]
    if ocr_text in good_partials:
      print(f"[DEBUG] GOOD partial match: {ocr_text} -> GOOD")
      return "GOOD"

  # Handle BAD detection - be more strict with BAD to avoid confusion with GOOD partials
  bad_exact = ["BAD", "BD", "B4D", "BAP", "BAO", "AD"]
  if ocr_text in bad_exact:
    print(f"[DEBUG] BAD exact match: {ocr_text} -> BAD")
    return "BAD"

  # Enhanced pattern matching with existing patterns
  for mood, patterns in MOOD_PATTERNS.items():
    for pattern in patterns:
      # Exact pattern match
      if pattern == ocr_text:
        print(f"[DEBUG] Pattern exact match: {ocr_text} -> {mood}")
        return mood

  # Substring matching with better logic
  for mood in MOOD_LIST:
    # Check if OCR text contains the mood (for longer OCR results)
    if len(ocr_text) >= len(mood) and mood in ocr_text:
      # Special case: don't match "BAD" if OCR text could be part of "GOOD"
      if mood == "BAD" and any(good_part in ocr_text for good_part in ["GOD", "OOD", "GOO"]):
        continue
      print(f"[DEBUG] Substring match: {ocr_text} contains {mood}")
      return mood

    # Check if mood contains OCR text (for shorter OCR results)
    if len(ocr_text) >= 3 and ocr_text in mood:
      # Special case: don't match "BAD" if OCR text could be part of "GOOD"
      if ocr_text in ["GOD", "OOD", "GOO"] and mood != "GOOD":
        continue
      print(f"[DEBUG] Reverse substring match: {mood} contains {ocr_text}")
      return mood

  # Fuzzy matching for character substitution
  for mood in MOOD_LIST:
    if len(ocr_text) == len(mood):
      differences = sum(1 for a, b in zip(mood, ocr_text) if a != b)
      if differences <= 1:  # Allow 1 character difference
        # Extra check for GOOD vs BAD confusion
        if mood == "BAD" and ocr_text in ["GOD", "OOD", "GOO"]:
          continue
        print(f"[DEBUG] Fuzzy match (1 char diff): {ocr_text} -> {mood}")
        return mood

  # Last resort: check if it's a known problematic pattern
  problematic_patterns = {
    "": "UNKNOWN",  # Empty string
    "GOD": "GOOD",  # Common GOOD misread
    "OOD": "GOOD",  # Common GOOD misread
    "GOO": "GOOD",  # Common GOOD misread
    "GOOP": "GOOD", # Common GOOD misread
    "COOO": "GOOD", # Common GOOD misread
    "G00D": "GOOD", # Common GOOD misread with 0 instead of O
    "AD": "BAD",    # Common BAD misread (missing B)
    "BD": "BAD",    # Common BAD misread (missing A)
  }

  if ocr_text in problematic_patterns:
    result = problematic_patterns[ocr_text]
    print(f"[DEBUG] Problematic pattern match: {ocr_text} -> {result}")
    return result

  print(f"[DEBUG] No match found for: '{ocr_text}'")
  return "UNKNOWN"

def check_mood_enhanced():
  """Enhanced mood check with multiple OCR attempts and image preprocessing"""
  # Get current region settings
  current_regions = get_current_regions()
  mood_region = current_regions['MOOD_REGION']

  try:
    # Capture base image
    base_img = capture_region(mood_region)

    # Try multiple image enhancement approaches
    enhanced_imgs = []

    # Original enhanced screenshot method
    try:
      enhanced_img1 = enhanced_screenshot(mood_region)
      enhanced_imgs.append(("enhanced_screenshot", enhanced_img1))
    except Exception as e:
      print(f"[DEBUG] Enhanced screenshot failed: {e}")

    # Original image as fallback
    # enhanced_imgs.append(("original", base_img))

    all_results = []

    # Try OCR on each enhanced image
    for method_name, img in enhanced_imgs:
      print(f"[DEBUG] Trying OCR on {method_name} image")

      try:
        # Get multiple OCR results for this image
        ocr_results = extract_mood_with_multiple_methods(img)

        for i, ocr_text in enumerate(ocr_results):
          if ocr_text:
            mood = match_mood_with_enhanced_patterns(ocr_text)
            if mood != "UNKNOWN":
              all_results.append((mood, method_name, f"method_{i+1}", ocr_text))
              print(f"[DEBUG] Found mood: {mood} from {method_name} method_{i+1}")
            else:
              print(f"[DEBUG] Unknown mood from {method_name} method_{i+1}: '{ocr_text}'")
          else:
            print(f"[DEBUG] Empty OCR result from {method_name} method_{i+1}")

      except Exception as e:
        print(f"[DEBUG] OCR failed for {method_name}: {e}")

    # Analyze all results and pick the best one
    if all_results:
      # Count occurrences of each mood
      mood_counts = {}
      for mood, method, ocr_method, text in all_results:
        if mood not in mood_counts:
          mood_counts[mood] = []
        mood_counts[mood].append((method, ocr_method, text))

      print(f"[DEBUG] Mood detection results: {mood_counts}")

      # Priority: most frequent mood, but prefer non-UNKNOWN
      best_mood = None
      max_count = 0

      for mood, detections in mood_counts.items():
        count = len(detections)
        if mood != "UNKNOWN" and count > max_count:
          max_count = count
          best_mood = mood

      # If no non-UNKNOWN mood found, use the most frequent one
      if best_mood is None:
        best_mood = max(mood_counts.keys(), key=lambda k: len(mood_counts[k]))

      print(f"[DEBUG] Selected mood: {best_mood} (appeared {len(mood_counts[best_mood])} times)")
      return best_mood

    else:
      print(f"[DEBUG] No valid mood detected from any method")
      return "UNKNOWN"

  except Exception as e:
    print(f"[ERROR] Enhanced mood check failed: {e}")
    return "UNKNOWN"

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
        return mood

      # Partial match for missing characters
      if len(ocr_text) >= 2:
        # Check if OCR text is contained in pattern (missing end characters)
        if pattern.startswith(ocr_text):
          return mood

        # Check if pattern is contained in OCR text (missing start characters)
        if ocr_text.endswith(pattern):
          return mood

        # Check for character substitution (allow 1-2 character differences)
        if len(pattern) == len(ocr_text):
          differences = sum(1 for a, b in zip(pattern, ocr_text) if a != b)
          if differences <= 2:
            return mood

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
  """Check support card in each training with unified score calculation"""
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

  # Calculate hint score based on configuration - maximum 1 hint counts for score
  hint_score = 0
  if hint_count > 0 and current_date:
    absolute_day = current_date.get('absolute_day', 0)
    hint_score = get_hint_score_value(absolute_day)

  # Calculate NPC score using configuration
  npc_score_per_unit = get_npc_score_value()
  npc_score = total_npc_count * npc_score_per_unit

  # Add additional info to results
  count_result["hint"] = hint_count
  count_result["hint_score"] = hint_score
  count_result["npc_count"] = total_npc_count
  count_result["npc_score"] = npc_score

  # Calculate total score using unified logic (this will include WIT bonus if applicable)
  total_score = calculate_unified_training_score(training_type, count_result, current_date)
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
  """Enhanced mood check with improved OCR and pattern matching"""
  return check_mood_enhanced()

def check_turn():
  """Check current turn number or race day"""
  # Get current region settings in case they were updated
  current_regions = get_current_regions()
  turn_region = current_regions['TURN_REGION']

  turn = enhanced_screenshot(turn_region)
  turn_text = extract_text(turn)

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