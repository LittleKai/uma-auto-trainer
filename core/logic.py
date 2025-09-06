import json

from core.state import check_current_year, stat_state

with open("config.json", "r", encoding="utf-8") as file:
  config = json.load(file)

PRIORITY_STAT = config["priority_stat"]
MINIMUM_ENERGY_PERCENTAGE = config["minimum_energy_percentage"]
CRITICAL_ENERGY_PERCENTAGE = config["critical_energy_percentage"]
STAT_CAPS = config["stat_caps"]

# Load scoring configuration
SCORING_CONFIG = config.get("scoring_config", {})

# Career Stage Constants
PRE_DEBUT_THRESHOLD = SCORING_CONFIG.get("stage_thresholds", {}).get("pre_debut", 16)
EARLY_STAGE_THRESHOLD = SCORING_CONFIG.get("stage_thresholds", {}).get("early_stage", 24)
MID_STAGE_THRESHOLD = SCORING_CONFIG.get("stage_thresholds", {}).get("mid_stage", 48)

def get_scoring_config():
  """Get scoring configuration from config file"""
  return SCORING_CONFIG

def get_hint_score_value(absolute_day):
  """Get hint score value based on day"""
  hint_config = SCORING_CONFIG.get("hint_score", {})
  day_threshold = hint_config.get("day_threshold", 24)
  early_score = hint_config.get("early_stage", 1.0)
  late_score = hint_config.get("late_stage", 0.5)

  return early_score if absolute_day < day_threshold else late_score

def get_npc_score_value():
  """Get NPC base score value"""
  npc_config = SCORING_CONFIG.get("npc_score", {})
  return npc_config.get("base_value", 0.5)

def get_support_base_score():
  """Get support card base score value"""
  support_config = SCORING_CONFIG.get("support_score", {})
  return support_config.get("base_value", 1.0)

def get_friend_multiplier(training_type=None, current_date=None):
  """Get friend card score multiplier based on training type and stage"""
  support_config = SCORING_CONFIG.get("support_score", {})
  friend_config = support_config.get("friend_multiplier", {})

  # If friend_multiplier is not a dict (old config format), return it directly
  if not isinstance(friend_config, dict):
    return friend_config

  # Check if we're in early stage (day < 24)
  is_early_stage = False
  if current_date:
    absolute_day = current_date.get('absolute_day', 0)
    is_early_stage = absolute_day < EARLY_STAGE_THRESHOLD

  # Special handling for WIT training - always 0.5 regardless of stage
  if training_type == "wit":
    return friend_config.get("friend_wit_multiplier", 0.5)

  # For other training types
  if is_early_stage:
    return friend_config.get("early_stage", 1.1)
  else:
    # Default multiplier for late stage (if not specified in nested config, use 1.0)
    return friend_config.get("late_stage", 1.0)

def get_rainbow_multiplier(stage):
  """Get rainbow card multiplier based on stage"""
  support_config = SCORING_CONFIG.get("support_score", {})
  rainbow_config = support_config.get("rainbow_multiplier", {})

  return rainbow_config.get(stage, 1.0)

def get_wit_score_requirement(energy_type, is_pre_debut):
  """Get WIT training score requirement"""
  wit_config = SCORING_CONFIG.get("wit_training", {})
  requirement_type = wit_config.get(f"{energy_type}_score_requirement", {})

  stage = "pre_debut" if is_pre_debut else "post_debut"
  return requirement_type.get(stage, 2.0)

def get_wit_early_stage_bonus():
  """Get WIT early stage bonus value from configuration"""
  wit_config = SCORING_CONFIG.get("wit_training", {})
  return wit_config.get("early_stage_bonus", 0.25)

def get_energy_restriction_config():
  """Get energy restriction configuration"""
  scoring_config = get_scoring_config()
  energy_config = scoring_config.get("energy_restrictions", {})
  return {
    'medium_energy_upper_limit': energy_config.get("medium_energy_upper_limit", 50),
    'medium_energy_max_score_threshold': energy_config.get("medium_energy_max_score_threshold", 2.5)
  }

def get_career_stage_info(current_date):
  """Get comprehensive career stage information"""
  if not current_date:
    return {
      'is_pre_debut': False,
      'stage': 'unknown',
      'absolute_day': 0,
      'should_apply_strategy': False
    }

  absolute_day = current_date.get('absolute_day', 0)

  # Define stages with configurable thresholds
  is_pre_debut = absolute_day <= PRE_DEBUT_THRESHOLD

  if absolute_day <= EARLY_STAGE_THRESHOLD:
    stage = 'early'
  elif absolute_day <= MID_STAGE_THRESHOLD:
    stage = 'mid'
  else:
    stage = 'late'

  return {
    'is_pre_debut': is_pre_debut,
    'stage': stage,
    'absolute_day': absolute_day,
    'should_apply_strategy': absolute_day > PRE_DEBUT_THRESHOLD
  }

def get_stat_priority(stat_key: str) -> int:
  """Get priority index of stat from config"""
  return PRIORITY_STAT.index(stat_key) if stat_key in PRIORITY_STAT else 999

def get_priority_by_stage(stat_key, current_date):
  """Get stat priority based on career stage"""
  stage_info = get_career_stage_info(current_date)

  # Use normal priority from config for all stages
  if stat_key in PRIORITY_STAT:
    priority_index = PRIORITY_STAT.index(stat_key)
    return priority_index
  else:
    return 999

def filter_by_stat_caps(results, current_stats):
  """Filter training results by stat caps to exclude capped stats"""
  return {
    stat: data for stat, data in results.items()
    if current_stats.get(stat, 0) < STAT_CAPS.get(stat, 1200)
  }

def apply_early_stage_wit_bonus(training_key, total_score, current_date):
  """Apply early stage bonus to WIT training score"""
  if not current_date or training_key != "wit":
    return total_score

  absolute_day = current_date.get('absolute_day', 0)

  # Apply WIT bonus for days < 24 (includes Pre-Debut period)
  if absolute_day < EARLY_STAGE_THRESHOLD:
    bonus = get_wit_early_stage_bonus()
    return total_score + bonus

  return total_score

def calculate_training_score(training_key, training_data, current_date):
  """Calculate training score using the same unified logic as state.py"""
  # Use the total_score directly from training_data which was calculated by unified logic
  total_score = training_data.get("total_score", 0)

  # Apply early stage WIT bonus if applicable
  total_score = apply_early_stage_wit_bonus(training_key, total_score, current_date)

  support_counts = training_data.get("support", {})
  rainbow_count = support_counts.get(training_key, 0)
  hint_score = training_data.get("hint_score", 0)
  npc_score = training_data.get("npc_score", 0)
  support_count = sum(count for key, count in support_counts.items() if key != "npc")

  return total_score, rainbow_count, hint_score, npc_score, support_count

def format_score_info(training_key, training_data, current_date):
  """Format training score information for logging"""
  total_score, rainbow_count, hint_score, npc_score, support_count = calculate_training_score(training_key, training_data, current_date)

  stage_info = get_career_stage_info(current_date)

  hint_info = f" + {training_data.get('hint_count', 0)} hints ({hint_score})" if hint_score > 0 else ""
  npc_info = f" + {training_data.get('npc_count', 0)} NPCs ({npc_score})" if npc_score > 0 else ""

  # Add WIT bonus info for early stage (< day 24)
  wit_bonus_info = ""
  if training_key == "wit" and current_date:
    absolute_day = current_date.get('absolute_day', 0)
    if absolute_day < EARLY_STAGE_THRESHOLD:
      bonus = get_wit_early_stage_bonus()
      wit_bonus_info = f" + Early WIT bonus ({bonus})"

  if stage_info['is_pre_debut']:
    return f"(score: {total_score} - {support_count} supports{hint_info}{npc_info}{wit_bonus_info} - Pre-Debut: Score-based selection)"
  elif stage_info['stage'] == 'early':
    return f"(score: {total_score} - {support_count} supports{hint_info}{npc_info}{wit_bonus_info} - Early Stage: Strategy applies, no rainbow bonus)"
  elif stage_info['stage'] == 'mid':
    rainbow_multiplier = get_rainbow_multiplier('mid_stage')
    return f"(score: {total_score} - {support_count} supports{hint_info}{npc_info}{wit_bonus_info} - Mid Stage: {rainbow_multiplier}x rainbow bonus)"
  else:
    rainbow_multiplier = get_rainbow_multiplier('late_stage')
    return f"(score: {total_score} - {support_count} supports{hint_info}{npc_info}{wit_bonus_info} - Late Stage: {rainbow_multiplier}x rainbow bonus)"

def extract_score_threshold(priority_strategy):
  """Extract score threshold from priority strategy string"""
  if "G1" in priority_strategy or "G2" in priority_strategy:
    return None  # Race priority - no training
  elif "Score 2.5+" in priority_strategy:
    return 2.5
  elif "Score 3+" in priority_strategy:
    return 3.0
  elif "Score 3.5+" in priority_strategy:
    return 3.5
  elif "Score 4+" in priority_strategy:
    return 4.0
  elif "Score 4.5+" in priority_strategy:
    return 4.5
  else:
    return 3.5  # Default threshold

def find_best_training_by_score(results, current_date, min_score_threshold):
  """Find best training that meets minimum score threshold using unified scoring with WIT early stage bonus"""
  if not results:
    return None

  stage_info = get_career_stage_info(current_date)

  # Apply strategy scoring using unified total_score with WIT bonus for all stages
  valid_trainings = {}
  for key, data in results.items():
    total_score = data.get("total_score", 0)

    # Apply early stage WIT bonus if applicable
    total_score = apply_early_stage_wit_bonus(key, total_score, current_date)

    # Use small epsilon for floating point comparison
    if total_score >= min_score_threshold - 1e-10:
      valid_trainings[key] = data
      valid_trainings[key]["adjusted_score"] = total_score  # Store adjusted score

  if not valid_trainings:
    return None

  # Find best training among valid ones using adjusted score first, then priority
  best_training = max(
    valid_trainings.items(),
    key=lambda x: (
      x[1].get("adjusted_score", x[1].get("total_score", 0)),
      -get_priority_by_stage(x[0], current_date)
    )
  )

  best_key, best_data = best_training
  best_score = best_data.get("adjusted_score", best_data.get("total_score", 0))

  return best_key

def score_based_training_selection(results, current_date):
  """Score-based training selection for all stages including Pre-Debut"""
  if not results:
    return None

  # Calculate score for each training with WIT bonus applied
  training_list = []
  for key, data in results.items():
    score = data.get("total_score", 0)
    adjusted_score = apply_early_stage_wit_bonus(key, score, current_date)
    priority_index = get_priority_by_stage(key, current_date)
    training_list.append((key, data, adjusted_score, priority_index))

  # Sort by adjusted score (descending), then by priority (ascending - lower index = higher priority)
  training_list.sort(key=lambda x: (-x[2], x[3]))

  best_key, best_data, best_score, best_priority = training_list[0]

  # Return None if no valid training found
  if best_score <= 0:
    return None

  score_info = format_score_info(best_key, best_data, current_date)
  return best_key, score_info

def training_decision(results_training, energy_percentage, strategy_settings, current_date):
  """Enhanced training decision with unified scoring system and WIT early stage bonus"""
  if not results_training:
    return None

  stage_info = get_career_stage_info(current_date)

  # Get current stats for caps filtering
  current_stats = stat_state()

  # Filter by stat caps
  filtered_results = filter_by_stat_caps(results_training, current_stats)
  if not filtered_results:
    return None

  # Check energy level for critical energy (no training allowed)
  if energy_percentage < CRITICAL_ENERGY_PERCENTAGE:
    return None

  # Check energy level for medium energy logic (between critical and minimum)
  if energy_percentage < MINIMUM_ENERGY_PERCENTAGE and energy_percentage >= CRITICAL_ENERGY_PERCENTAGE:
    return medium_energy_wit_training(filtered_results, current_date)

  # Mid-game energy restriction for low score training (only after early stage) - using config
  energy_restrictions = get_energy_restriction_config()
  medium_upper_limit = energy_restrictions['medium_energy_upper_limit']
  max_score_threshold = energy_restrictions['medium_energy_max_score_threshold']

  if (stage_info['stage'] in ['mid', 'late'] and
          MINIMUM_ENERGY_PERCENTAGE <= energy_percentage < medium_upper_limit):
    # Check if best available training score is <= threshold using unified scoring with WIT bonus
    best_score = 0
    for key, data in filtered_results.items():
      total_score = data.get('total_score', 0)
      total_score = apply_early_stage_wit_bonus(key, total_score, current_date)
      if total_score > best_score:
        best_score = total_score

    if best_score <= max_score_threshold:
      return "NO_TRAINING"

  # Get strategy
  priority_strategy = strategy_settings.get('priority_strategy', 'Train Score 3.5+')
  score_threshold = extract_score_threshold(priority_strategy)

  if score_threshold is None:
    # G1 or G2 strategy - prioritize racing, no training
    return None
  else:
    # Score-based training strategy for all stages
    if stage_info['is_pre_debut']:
      # Pre-Debut
      result = score_based_training_selection(filtered_results, current_date)
      if result:
        return result[0]  # Return only the training key
      return None
    else:
      # Post Pre-Debut
      result = find_best_training_by_score(filtered_results, current_date, score_threshold)

      if result:
        return result
      else:
        return "STRATEGY_NOT_MET"

def medium_energy_wit_training(results, current_date):
  """Medium energy training - only WIT with configurable score requirements and early stage bonus"""
  wit_data = results.get("wit")
  if not wit_data:
    return None

  stage_info = get_career_stage_info(current_date)
  total_score = wit_data.get("total_score", 0)

  # Apply early stage bonus to WIT
  total_score = apply_early_stage_wit_bonus("wit", total_score, current_date)

  required_score = get_wit_score_requirement("medium_energy", stage_info['is_pre_debut'])

  if total_score >= required_score:
    return "wit"

  return None

def low_energy_training(results, current_date=None):
  """Enhanced low energy training logic with configurable score requirements and early stage bonus"""
  wit_data = results.get("wit")

  if not wit_data:
    return None

  stage_info = get_career_stage_info(current_date)
  total_score = wit_data.get("total_score", 0)

  # Apply early stage bonus to WIT
  total_score = apply_early_stage_wit_bonus("wit", total_score, current_date)

  required_score = get_wit_score_requirement("low_energy", stage_info['is_pre_debut'])

  if total_score >= required_score:
    return "wit"

  return None

def fallback_training(results, current_date):
  """Enhanced fallback training using original scores without artificial bonuses"""
  if not results:
    return None

  stage_info = get_career_stage_info(current_date)

  # Calculate best training using ORIGINAL scores only (no WIT bonus for fairness in fallback)
  training_list = []
  for key, data in results.items():
    original_score = data.get("total_score", 0)
    priority_index = get_priority_by_stage(key, current_date)
    training_list.append((key, data, original_score, priority_index))

    # DEBUG: Log original scores used for fallback selection
    print(f"[DEBUG] Fallback {key.upper()}: Original Score={original_score:.2f}, Priority={priority_index}")

  # Sort by original score (descending), then by priority (ascending - lower index = higher priority)
  training_list.sort(key=lambda x: (-x[2], x[3]))

  # DEBUG: Show selection reasoning
  print(f"[DEBUG] Fallback selected: {training_list[0][0].upper()} with original score {training_list[0][2]:.2f}")

  best_key, best_data, original_score, best_priority = training_list[0]

  if original_score <= 0:
    return None

  score_info = format_score_info(best_key, best_data, current_date)
  return best_key, score_info

def do_something(results, energy_percentage=100, strategy_settings=None):
  """Enhanced training decision with unified scoring system and WIT early stage bonus"""
  year = check_current_year()
  current_stats = stat_state()

  # Default strategy settings if not provided
  if strategy_settings is None:
    strategy_settings = {
      'minimum_mood': 'NORMAL',
      'priority_strategy': 'Train Score 3.5+'
    }

  priority_strategy = strategy_settings.get('priority_strategy', 'Train Score 3.5+')

  # Get current date info to check stage
  from core.state import get_current_date_info
  current_date = get_current_date_info()

  stage_info = get_career_stage_info(current_date)

  # Filter by stat caps
  filtered = filter_by_stat_caps(results, current_stats)

  if not filtered:
    return None

  # Check if energy is critical
  if energy_percentage < CRITICAL_ENERGY_PERCENTAGE:
    return None

  # Check if energy is medium (between critical and minimum)
  if energy_percentage < MINIMUM_ENERGY_PERCENTAGE:
    return medium_energy_wit_training(filtered, current_date)

  # Normal energy logic with unified strategy system and WIT bonus
  # Check priority strategy type
  score_threshold = extract_score_threshold(priority_strategy)

  if score_threshold is None:
    # G1 or G2 strategy - prioritize racing, no training
    return None
  else:
    # Score-based training strategy for all stages
    if stage_info['is_pre_debut']:
      # Use score-based selection for Pre-Debut
      result = score_based_training_selection(filtered, current_date)
      if result:
        return result[0]  # Return only the training key
      return None
    else:
      result = find_best_training_by_score(filtered, current_date, score_threshold)

      if result is None:
        pass

      return result