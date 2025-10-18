import re
import json
from PIL import Image, ImageEnhance, ImageFilter
import time
import numpy as np
from utils.screenshot import capture_region, enhanced_screenshot
from core.ocr import extract_text, extract_text_advanced, extract_stat_number
from core.recognizer import match_template
from core.race_manager import DateManager

from utils.constants import (
  SUPPORT_CARD_ICON_REGION, MOOD_REGION, TURN_REGION, FAILURE_REGION,
  YEAR_REGION, MOOD_LIST, CRITERIA_REGION, ENERGY_BAR, MOOD_PATTERNS,
  STAT_REGIONS, get_current_regions
)

# Global variable to store current date info
current_date_info = None
# Global variable to store support card state
_support_card_state = {}

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
  """Calculate unified training score with all bonuses applied"""
  from core.logic import get_friend_multiplier, get_wit_early_stage_bonus, EARLY_STAGE_THRESHOLD

  base_score = get_support_base_score()
  hint_score = support_counts.get("hint_score", 0)
  npc_score = support_counts.get("npc_score", 0)

  stage_thresholds = get_stage_thresholds()
  absolute_day = current_date.get('absolute_day', 0) if current_date else 0

  is_pre_debut = absolute_day <= stage_thresholds.get("pre_debut", 16)
  is_early_stage = absolute_day <= stage_thresholds.get("early_stage", 24)
  is_mid_stage = stage_thresholds.get("early_stage", 24) < absolute_day <= stage_thresholds.get("mid_stage", 48)
  is_late_stage = absolute_day > stage_thresholds.get("mid_stage", 48)

  rainbow_count = support_counts.get(training_type, 0)
  friend_count = support_counts.get("friend", 0)

  friend_score = 0
  if friend_count > 0:
    friend_multiplier = get_friend_multiplier(training_type, current_date)
    friend_score = friend_count * friend_multiplier

  other_support = sum(count for key, count in support_counts.items()
                      if key not in [training_type, "friend", "hint", "hint_score",
                                     "total_score", "npc", "npc_count", "npc_score"])

  if is_pre_debut:
    rainbow_multiplier = get_rainbow_multiplier("pre_debut")
  elif is_early_stage:
    rainbow_multiplier = get_rainbow_multiplier("early_stage")
  elif is_mid_stage:
    rainbow_multiplier = get_rainbow_multiplier("mid_stage")
  else:
    rainbow_multiplier = get_rainbow_multiplier("late_stage")

  rainbow_score = rainbow_count * rainbow_multiplier * base_score
  other_score = other_support * base_score
  total_score = rainbow_score + friend_score + other_score + hint_score + npc_score

  if training_type == "wit" and current_date:
    if absolute_day < EARLY_STAGE_THRESHOLD:
      wit_bonus = get_wit_early_stage_bonus()
      total_score += wit_bonus

  return total_score


def validate_stat_value(stat_key, value, threshold=200):
  """Validate stat value and return warning if below threshold"""
  if value < threshold:
    return True, f"[VALIDATION WARNING] Stat {stat_key.upper()} is below {threshold}: {value}"
  return False, None


def extract_stat_number_enhanced(img):
  """Enhanced stat number extraction with multiple OCR methods"""
  results = []

  try:
    config_list = [
      r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789',
      r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789',
      r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789',
      r'--oem 1 --psm 8 -c tessedit_char_whitelist=0123456789',
      r'--oem 3 --psm 13 -c tessedit_char_whitelist=0123456789'
    ]

    import pytesseract
    from core.ocr import _clean_stat_number

    for config in config_list:
      try:
        raw_text = pytesseract.image_to_string(img, config=config)
        cleaned_val = _clean_stat_number(raw_text)

        if cleaned_val > 0:
          results.append(cleaned_val)
      except:
        continue

    if results:
      from collections import Counter
      counter = Counter(results)
      most_common_value = counter.most_common(1)[0][0]

      return most_common_value, results

    return 0, []

  except Exception as e:
    print(f"[WARNING] Enhanced stat extraction failed: {e}")
    return 0, []


def stat_state():
  """Get current character stats using configurable regions with improved OCR accuracy"""

  current_regions = get_current_regions()
  stat_regions = current_regions['STAT_REGIONS']

  # Get support card state and find the top 2 support card types
  support_card_counts = get_support_card_state()
  sorted_support_types = sorted(support_card_counts.items(), key=lambda x: x[1], reverse=True)
  top_types = [stat for stat, count in sorted_support_types if stat in ['spd', 'sta', 'pwr', 'guts', 'wit']][:2]

  result = {}
  validation_warnings = []
  reread_stats = []

  stat_threshold = 200

  for stat, region in stat_regions.items():
    # Only process OCR for top 2 support card types
    if stat in top_types:
      img = enhanced_screenshot(region)

      value = extract_stat_number(img)
      result[stat] = value

      print(f"[DEBUG] Stat {stat.upper()}: {value}")

      is_low, warning_msg = validate_stat_value(stat, value, stat_threshold)
      if is_low:
        validation_warnings.append(warning_msg)
        reread_stats.append((stat, region, img))
    else:
      # For other stats not in top 2, set value to 0 without validation
      result[stat] = 0

  if reread_stats:
    print(f"\n[OCR REREAD] Detected {len(reread_stats)} stat(s) below {stat_threshold}, performing enhanced OCR...")

    for stat, region, img in reread_stats:
      original_value = result[stat]

      enhanced_value, all_results = extract_stat_number_enhanced(img)

      if enhanced_value != original_value and enhanced_value > 0:
        print(f"[OCR REREAD] {stat.upper()}: Original={original_value}, Enhanced={enhanced_value}, All results={all_results}")

        if enhanced_value >= stat_threshold:
          result[stat] = enhanced_value
          print(f"[OCR REREAD] {stat.upper()} updated from {original_value} to {enhanced_value}")
        else:
          print(f"[OCR REREAD] {stat.upper()} still below threshold after reread: {enhanced_value}")
      else:
        print(f"[OCR REREAD] {stat.upper()}: No change from original value {original_value}")

  return result

def check_energy_percentage(return_max_energy=False):
  """Check energy percentage by scanning for white pixels boundaries in energy bar"""
  try:
    current_regions = get_current_regions()
    energy_bar = current_regions['ENERGY_BAR']

    x1, y1, x2, y2 = energy_bar

    bar_height = y2 - y1
    middle_y = y1 + (bar_height // 2)
    region = (x1, middle_y, x2 - x1, 1)

    screenshot = capture_region(region)

    if screenshot.mode != 'RGB':
      screenshot = screenshot.convert('RGB')

    white_color = (255, 255, 255)
    gray_color = (118, 117, 118)
    base_energy_pixels = 236.0
    total_energy_pixels_adjust = -1

    energy_start_pos = None
    energy_end_pos = None
    first_white_found = False
    min_boundary_distance = 20

    image_width = screenshot.width

    for x in range(image_width):
      try:
        pixel_color = screenshot.getpixel((x, 0))

        is_white = (abs(pixel_color[0] - white_color[0]) <= 5 and
                    abs(pixel_color[1] - white_color[1]) <= 5 and
                    abs(pixel_color[2] - white_color[2]) <= 5)

        if is_white and not first_white_found:
          first_white_found = True

        if first_white_found and not is_white and energy_start_pos is None:
          energy_start_pos = x

        if energy_start_pos is not None and is_white:
          potential_end = x
          distance = potential_end - energy_start_pos

          if distance >= min_boundary_distance:
            energy_end_pos = potential_end
            break
          else:
            energy_start_pos = None
            first_white_found = True

      except Exception as e:
        print(f"[DEBUG] Error at pixel {x}: {e}")
        continue

    if energy_start_pos is not None and energy_end_pos is None:
      for x in range(energy_start_pos + 1, image_width):
        try:
          pixel_color = screenshot.getpixel((x, 0))
          is_white = (abs(pixel_color[0] - white_color[0]) <= 5 and
                      abs(pixel_color[1] - white_color[1]) <= 5 and
                      abs(pixel_color[2] - white_color[2]) <= 5)

          if is_white:
            distance = x - energy_start_pos
            if distance >= min_boundary_distance:
              energy_end_pos = x
              break
        except:
          continue

    if energy_start_pos is not None and energy_end_pos is not None:
      total_energy_pixels = energy_end_pos - energy_start_pos + total_energy_pixels_adjust

      gray_pixel_count = 0

      for x in range(energy_start_pos, energy_end_pos):
        try:
          pixel_color = screenshot.getpixel((x, 0))
          is_gray = (abs(pixel_color[0] - gray_color[0]) <= 2 and
                     abs(pixel_color[1] - gray_color[1]) <= 2 and
                     abs(pixel_color[2] - gray_color[2]) <= 2)

          if is_gray:
            gray_pixel_count += 1
        except:
          continue

      current_energy_pixels = total_energy_pixels - gray_pixel_count

      max_energy = (total_energy_pixels * 100.0) / base_energy_pixels
      current_energy = (current_energy_pixels * 100.0) / base_energy_pixels

      max_energy = max(0.0, max_energy)
      current_energy = max(0.0, min(current_energy, max_energy))

      if return_max_energy:
        return (round(current_energy, 1), round(max_energy, 1))
      else:
        return round(current_energy, 1)

    elif first_white_found:
      gray_pixel_count = 0
      total_pixels = 0

      for x in range(image_width):
        try:
          pixel_color = screenshot.getpixel((x, 0))

          is_gray = (abs(pixel_color[0] - gray_color[0]) <= 2 and
                     abs(pixel_color[1] - gray_color[1]) <= 2 and
                     abs(pixel_color[2] - gray_color[2]) <= 2)

          is_white = (abs(pixel_color[0] - white_color[0]) <= 5 and
                      abs(pixel_color[1] - white_color[1]) <= 5 and
                      abs(pixel_color[2] - white_color[2]) <= 5)

          if not is_white:
            total_pixels += 1
            if is_gray:
              gray_pixel_count += 1

        except:
          continue

      if total_pixels > 0:
        current_energy_pixels = total_pixels - gray_pixel_count

        max_energy = (total_pixels * 100.0) / base_energy_pixels
        current_energy = (current_energy_pixels * 100.0) / base_energy_pixels

        max_energy = max(0.0, max_energy)
        current_energy = max(0.0, min(current_energy, max_energy))

        if return_max_energy:
          return (round(current_energy, 1), round(max_energy, 1))
        else:
          return round(current_energy, 1)

    else:
      if return_max_energy:
        return (100.0, 100.0)
      else:
        return 100.0

  except Exception as e:
    print(f"[WARNING] Energy detection failed: {e}")
    import traceback
    traceback.print_exc()
    if return_max_energy:
      return (100.0, 100.0)
    else:
      return 100.0

def extract_mood_with_dual_methods(img):
  """Extract text using two most effective OCR configurations"""
  ocr_results = []

  try:
    text1 = extract_text(img).upper().strip()
    if text1:
      ocr_results.append(text1)

    mood_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    text2 = extract_text_advanced(img, whitelist=mood_chars, psm=8).upper().strip()
    if text2 and text2 != text1:
      ocr_results.append(text2)

  except Exception as e:
    print(f"[WARNING] OCR extraction failed: {e}")

  return ocr_results


def match_mood_with_priority_patterns(ocr_text):
  """Enhanced mood detection with optimized pattern matching"""
  if not ocr_text:
    return "UNKNOWN"

  ocr_text = ocr_text.upper().strip()

  if ocr_text in MOOD_LIST:
    return ocr_text

  good_partials = ["GOD", "OOD", "GOO", "GOOP", "COOO", "G00D"]
  if ocr_text in good_partials:
    return "GOOD"

  bad_exact = ["BAD", "BD", "B4D", "BAP", "BAO", "AD"]
  if ocr_text in bad_exact:
    return "BAD"

  high_confidence_moods = ["AWFUL", "NORMAL", "GREAT"]
  for mood in high_confidence_moods:
    if mood in MOOD_PATTERNS:
      for pattern in MOOD_PATTERNS[mood]:
        if pattern == ocr_text:
          return mood

  medium_confidence_moods = ["GOOD", "BAD"]
  for mood in medium_confidence_moods:
    if mood in MOOD_PATTERNS:
      for pattern in MOOD_PATTERNS[mood]:
        if pattern == ocr_text:
          return mood

  for mood in MOOD_LIST:
    if len(ocr_text) >= len(mood) and mood in ocr_text:
      if mood == "BAD" and any(good_part in ocr_text for good_part in ["GOD", "OOD", "GOO"]):
        continue
      return mood

  for mood in MOOD_LIST:
    if len(ocr_text) == len(mood):
      differences = sum(1 for a, b in zip(mood, ocr_text) if a != b)
      if differences <= 1:
        if mood == "BAD" and ocr_text in ["GOD", "OOD", "GOO"]:
          continue
        return mood

  return "UNKNOWN"


def check_mood_optimized():
  """Optimized mood check with reduced processing steps"""
  current_regions = get_current_regions()
  mood_region = current_regions['MOOD_REGION']

  try:
    enhanced_img = enhanced_screenshot(mood_region)

    ocr_results = extract_mood_with_dual_methods(enhanced_img)

    for ocr_text in ocr_results:
      if ocr_text:
        mood = match_mood_with_priority_patterns(ocr_text)
        if mood != "UNKNOWN":
          return mood

    return "UNKNOWN"

  except Exception as e:
    print(f"[ERROR] Optimized mood check failed: {e}")
    return "UNKNOWN"


def check_mood():
  """Enhanced mood check with optimized processing"""
  return check_mood_optimized()


def validate_region_coordinates(region):
  """Validate region coordinates to prevent PyAutoGUI errors"""
  if not region or len(region) != 4:
    print(f"[ERROR] Invalid region format: {region}")
    return None

  left, top, width, height = region

  try:
    left, top, width, height = int(left), int(top), int(width), int(height)
  except (ValueError, TypeError):
    print(f"[ERROR] Invalid coordinate types in region: {region}")
    return None

  if width <= 0 or height <= 0:
    print(f"[ERROR] Invalid region dimensions - width: {width}, height: {height}")
    return None

  if left < 0 or top < 0:
    print(f"[WARNING] Negative coordinates detected - left: {left}, top: {top}")

  return (left, top, width, height)


def check_support_card(threshold=0.8, is_pre_debut=False, training_type=None, current_date=None):
  """Check support card in each training with unified score calculation and support card bonus"""
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

  NPC_ICONS = {
    "akikawa": "assets/icons/support_npc_akikawa.png",
    "etsuko": "assets/icons/support_npc_etsuko.png"
  }

  count_result = {}

  time.sleep(0.3)

  for key, icon_path in SUPPORT_ICONS.items():
    matches = match_template(icon_path, support_region, threshold)
    count_result[key] = len(matches)

  total_npc_count = 0
  for npc_name, icon_path in NPC_ICONS.items():
    matches = match_template(icon_path, support_region, threshold)
    npc_found = len(matches)
    total_npc_count += npc_found

  count_result["npc"] = total_npc_count

  hint_matches = match_template("assets/icons/support_card_hint.png", support_region, threshold)
  hint_count = len(hint_matches)

  hint_score = 0
  if hint_count > 0 and current_date:
    absolute_day = current_date.get('absolute_day', 0)
    hint_score = get_hint_score_value(absolute_day)

  npc_score_per_unit = get_npc_score_value()
  npc_score = total_npc_count * npc_score_per_unit

  count_result["hint"] = hint_count
  count_result["hint_score"] = hint_score
  count_result["npc_count"] = total_npc_count
  count_result["npc_score"] = npc_score

  total_score = calculate_unified_training_score(training_type, count_result, current_date)

  support_card_bonus = 0
  if training_type and current_date:
    bonus_dict = calculate_support_card_bonus(current_date)
    support_card_bonus = bonus_dict.get(training_type, 0)
    total_score += support_card_bonus

  count_result["support_card_bonus"] = support_card_bonus

  count_result["total_score"] = total_score

  return count_result


def check_failure():
  """Get failure chance from UI region"""
  current_regions = get_current_regions()
  failure_region = current_regions['FAILURE_REGION']

  failure = enhanced_screenshot(failure_region)
  failure_text = extract_text(failure).lower()

  if not failure_text.startswith("failure"):
    return -1

  match_percent = re.search(r"failure\s+(\d{1,3})%", failure_text)
  if match_percent:
    return int(match_percent.group(1))

  match_number = re.search(r"failure\s+(\d+)", failure_text)
  if match_number:
    digits = match_number.group(1)
    idx = digits.find("9")
    if idx > 0:
      num = digits[:idx]
      return int(num) if num.isdigit() else -1
    elif digits.isdigit():
      return int(digits)

  return -1


def check_turn():
  """Check current turn number or race day"""
  current_regions = get_current_regions()
  turn_region = current_regions['TURN_REGION']

  turn = enhanced_screenshot(turn_region)
  turn_text = extract_text(turn)

  if "Race" in turn_text:
    return "Race Day"

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

  current_regions = get_current_regions()
  year_region = current_regions['YEAR_REGION']

  year = enhanced_screenshot(year_region)
  text = extract_text(year)

  current_date_info = DateManager.parse_year_text(text)

  if current_date_info is None:
    print(f"[ERROR] Failed to parse year text: {text}")
    raise Exception(f"Critical error: Cannot parse date from OCR text: {text}")

  return text


def get_current_date_info():
  """Get the current parsed date information"""
  return current_date_info


def check_criteria():
  """Check criteria text from UI region"""
  current_regions = get_current_regions()
  criteria_region = current_regions['CRITERIA_REGION']

  img = enhanced_screenshot(criteria_region)
  text = extract_text(img)
  return text


def set_support_card_state(support_counts):
  """Set the support card state from preset when F1 is pressed"""
  global _support_card_state
  _support_card_state = support_counts.copy()


def get_support_card_state():
  """Get the current support card state"""
  global _support_card_state
  return _support_card_state.copy()


def get_support_card_bonus_config():
  """Get support card bonus configuration from config file"""
  current_date = get_current_date_info()

  if current_date:
    month_num = current_date.get('month_num', 0)
    absolute_day = current_date.get('absolute_day', 0)

    if (month_num == 7 or month_num == 8) and absolute_day > 24:
      return {
        "score_bonus": 0,
        "threshold_day": 24,
        "max_bonus_types": 2
      }

  scoring_config = load_scoring_config()
  return scoring_config.get("support_card_bonus", {
    "score_bonus": 0.5,
    "threshold_day": 24,
    "max_bonus_types": 2
  })


def calculate_support_card_bonus(current_date):
  """Calculate support card bonus based on preset counts and current date"""
  if not current_date:
    return {}

  absolute_day = current_date.get('absolute_day', 0)
  bonus_config = get_support_card_bonus_config()
  threshold_day = bonus_config.get("threshold_day", 24)

  if absolute_day <= threshold_day:
    return {}

  support_state = get_support_card_state()
  if not support_state:
    return {}

  score_bonus = bonus_config.get("score_bonus", 0.5)
  max_bonus_types = bonus_config.get("max_bonus_types", 2)

  training_types = ['spd', 'sta', 'pwr', 'guts', 'wit']
  type_counts = {t: support_state.get(t, 0) for t in training_types}

  sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)

  if not sorted_types or sorted_types[0][1] == 0:
    return {}

  max_count = sorted_types[0][1]
  max_count_types = [t for t, count in sorted_types if count == max_count]
  bonus_types = max_count_types[:max_bonus_types]

  if len(bonus_types) < max_bonus_types:
    remaining_types = [t for t, count in sorted_types if t not in bonus_types and count > 0]
    bonus_types.extend(remaining_types[:max_bonus_types - len(bonus_types)])

  bonus_dict = {}
  for training_type in bonus_types:
    bonus_dict[training_type] = score_bonus

  return bonus_dict