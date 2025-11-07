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

def get_wit_score_requirement(energy_type, training_day):
  """Get WIT training score requirement"""
  wit_config = SCORING_CONFIG.get("wit_training", {})
  requirement_stages = wit_config.get(f"{energy_type}_score_requirement", {}).get("stages", [])

  # Find the appropriate score based on training day
  for stage in requirement_stages:
    if stage["end_day"] is None or training_day <= stage["end_day"]:
      score =  stage["score"]
      print(f"wit score: {score}")
      return stage["score"]
  # Fallback to default score if no matching stage found
  return 2.0

def get_wit_early_stage_bonus():
  """Get WIT early stage bonus value from configuration"""
  wit_config = SCORING_CONFIG.get("wit_training", {})
  return wit_config.get("early_stage_bonus", 0.25)

def get_energy_restriction_config():
  """Get energy restriction configuration"""
  scoring_config = get_scoring_config()
  energy_config = scoring_config.get("energy_restrictions", {})
  return {
    'medium_energy_shortage': energy_config.get("medium_energy_shortage", 50),
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

def filter_by_stat_caps(results, current_stats, current_date=None):
  """Filter training results by stat caps, only applies after configured threshold day"""

  # Check if stat cap filtering should be applied based on date
  if current_date:
    absolute_day = current_date.get('absolute_day', 0)
    stat_cap_threshold_day = config.get("stat_cap_threshold_day", 60)

    # Print current stats when reaching threshold day for the first time
    if absolute_day == stat_cap_threshold_day:
      print(f"[STAT CAPS] Current stats vs caps:")
      for stat in ["spd", "sta", "pwr", "guts", "wit"]:
        current_value = current_stats.get(stat, 0)
        cap_value = STAT_CAPS.get(stat, 1200)
        status = "CAPPED" if current_value >= cap_value else "OK"
        print(f"[STAT CAPS]   {stat.upper()}: {current_value}/{cap_value} ({status})")

    # Apply stat cap filtering for days >= threshold
    filtered_results = {}
    for stat, data in results.items():
      current_value = current_stats.get(stat, 0)
      cap_value = STAT_CAPS.get(stat, 1200)

      if current_value < cap_value:
        filtered_results[stat] = data
      else:
        print(f"[STAT CAPS] Filtered out {stat.upper()} training: {current_value}/{cap_value} (capped)")

    return filtered_results
  else:
    # If no current_date provided, return all results without filtering
    return results

def calculate_training_score(training_key, training_data, current_date):
  """Calculate training score using the same unified logic as state.py"""
  # Use the total_score directly from training_data which was calculated by unified logic
  # WIT bonus is now applied only once in calculate_unified_training_score()
  total_score = training_data.get("total_score", 0)

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

  # Add WIT bonus info for early stage (< day 24) - this will show in logging
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

def unified_training_selection(results, current_date, min_score_threshold=None):
  """Unified training selection for all stages - prioritize absolute highest score with threshold check"""

  if not results:
    return None

  # Calculate score for each training using total_score with WIT bonus applied
  training_list = []

  for key, data in results.items():
    total_score = data.get("total_score", 0)

    priority_index = get_priority_by_stage(key, current_date)
    training_list.append((key, data, total_score, priority_index))

  # Sort by total_score (descending) with epsilon for tie-breaking, then by priority only for exact ties
  # Use epsilon to handle floating point precision issues
  EPSILON = 1e-6

  def sort_key(item):
    key, data, total_score, priority_index = item
    # Round score to avoid floating point precision issues
    rounded_score = round(total_score, 6)
    return (-rounded_score, priority_index)

  training_list.sort(key=sort_key)

  best_key, best_data, best_score, best_priority = training_list[0]

  # Check minimum score threshold if provided
  if min_score_threshold is not None and best_score < min_score_threshold - 1e-10:
    return None

  # Return None if no valid training found
  if best_score <= 0:
    return None

  score_info = format_score_info(best_key, best_data, current_date)
  return best_key, score_info

def training_decision(results_training, energy_percentage, energy_max, strategy_settings, current_date):
  """Enhanced training decision with unified scoring system"""
  print(f"[DEBUG] === training_decision CALLED ===")
  print(f"[DEBUG] Energy: {energy_percentage}%, Strategy: {strategy_settings.get('priority_strategy', 'Unknown')}")

  if not results_training:
    print(f"[DEBUG] No training results provided")
    return None

  stage_info = get_career_stage_info(current_date)
  print(f"[DEBUG] Stage info: {stage_info}")

  absolute_day = current_date.get('absolute_day', 0)
  stat_cap_threshold_day = config.get("stat_cap_threshold_day", 60)
  filtered_results = results_training

  # Never apply stat cap filtering before threshold day
  if absolute_day >= stat_cap_threshold_day:
    # Get current stats for caps filtering
    current_stats = stat_state()
    print(f'Stat: {current_stats}')
    # Filter by stat caps
    filtered_results = filter_by_stat_caps(results_training, current_stats, current_date)
    if not filtered_results:
      print(f"[DEBUG] All training filtered out by stat caps")
      return None

  # Check energy level for critical energy (no training allowed)
  if energy_percentage < CRITICAL_ENERGY_PERCENTAGE:
    print(f"[DEBUG] Critical energy ({energy_percentage}% < {CRITICAL_ENERGY_PERCENTAGE}%), no training allowed")
    return None

  # Check energy level for medium energy logic (between critical and minimum)
  if energy_percentage < MINIMUM_ENERGY_PERCENTAGE and energy_percentage >= CRITICAL_ENERGY_PERCENTAGE:
    print(f"[DEBUG] Medium energy ({energy_percentage}%), checking WIT only")
    return medium_energy_wit_training(filtered_results, current_date)

  # Mid-game energy restriction for low score training (only after early stage) - using config
  energy_restrictions = get_energy_restriction_config()
  medium_energy_shortage = energy_restrictions['medium_energy_shortage']
  max_score_threshold = energy_restrictions['medium_energy_max_score_threshold']

  energy_shortage_absolute = energy_max - energy_percentage
  print(f' energy_shortage_absolute: {energy_max} - {energy_percentage}')

  stage = stage_info['stage']
  print(f'{stage} - e: {energy_shortage_absolute} - {medium_energy_shortage}')
  if (stage_info['stage'] in ['mid', 'late'] and energy_shortage_absolute >= medium_energy_shortage):
    # Check if any available training score is > threshold using total_score with WIT bonus
    has_high_score_training = False
    best_score_for_debug = 0

    for key, data in filtered_results.items():
      total_score = data.get('total_score', 0)

      if total_score > best_score_for_debug:
        best_score_for_debug = total_score

      if total_score > max_score_threshold:
        has_high_score_training = True
        break

    if not has_high_score_training:
      print(f"[DEBUG] Energy shortage ({energy_shortage_absolute} >= {medium_energy_shortage}) and all scores <= {max_score_threshold} (best: {best_score_for_debug:.2f}), prioritizing race or rest")
      return "SHOULD_REST"  # This will trigger race check first, then rest if no suitable race
    else:
      print(f"[DEBUG] Energy shortage detected but high score training available (best: {best_score_for_debug:.2f} > {max_score_threshold}), continuing normal logic")

  # Priority strategy and training selection logic continues...
  priority_strategy = strategy_settings.get('priority_strategy', 'Train Score 3.5+')

  # Check priority strategy type
  score_threshold = extract_score_threshold(priority_strategy)

  if score_threshold is None:
    return None
  else:
    result = unified_training_selection(filtered_results, current_date, score_threshold)
    if result:
      return result[0]
    return None

def medium_energy_wit_training(results, current_date):
  """Medium energy training - only WIT with configurable score requirements"""
  wit_data = results.get("wit")
  if not wit_data:
    return None
  stage_info = get_career_stage_info(current_date)
  total_score = wit_data.get("total_score", 0)

  absolute_day = current_date.get('absolute_day', 0)
  required_score = get_wit_score_requirement("medium_energy", absolute_day)

  if total_score >= required_score:
    return "wit"

  return None

def fallback_training(results, current_date):
  """Enhanced fallback training using original scores without artificial bonuses"""
  if not results:
    return None

  # Apply filter by stat caps if on or after threshold day
  absolute_day = current_date.get('absolute_day', 0)
  stat_cap_threshold_day = config.get("stat_cap_threshold_day", 60)

  if absolute_day >= stat_cap_threshold_day:
    from core.state import stat_state
    current_stats = stat_state()
    results = filter_by_stat_caps(results, current_stats, current_date)

    if not results:
      print(f"[DEBUG] All training filtered out by stat caps in fallback_training")
      return None

  # Calculate best training using total_score
  training_list = []
  for key, data in results.items():
    total_score = data.get("total_score", 0)
    priority_index = get_priority_by_stage(key, current_date)
    training_list.append((key, data, total_score, priority_index))

    # DEBUG: Log scores used for fallback selection
    print(f"[DEBUG] Fallback {key.upper()}: Total Score={total_score:.2f}, Priority={priority_index}")

  # Sort by total_score (descending), then by priority (ascending - lower index = higher priority)
  training_list.sort(key=lambda x: (-x[2], x[3]))

  # DEBUG: Show selection reasoning
  print(f"[DEBUG] Fallback selected: {training_list[0][0].upper()} with total score {training_list[0][2]:.2f}")

  best_key, best_data, total_score, best_priority = training_list[0]

  if total_score <= 0:
    return None

  score_info = format_score_info(best_key, best_data, current_date)
  return best_key, score_info

def do_something(results, energy_percentage=100, strategy_settings=None):
  """Enhanced training decision with unified scoring system"""
  year = check_current_year()
  current_stats = stat_state()

  # Default strategy settings if not provided
  if strategy_settings is None:
    strategy_settings = {
      'minimum_mood': 'NORMAL',
      'priority_strategy': 'Train Score 3.5+'
    }

  priority_strategy = strategy_settings.get('priority_strategy', 'Train Score 3+')

  # Get current date info to check stage
  from core.state import get_current_date_info
  current_date = get_current_date_info()

  stage_info = get_career_stage_info(current_date)

  # Filter by stat caps
  filtered = filter_by_stat_caps(results, current_stats, current_date)

  if not filtered:
    return None

  # Check if energy is critical
  if energy_percentage < CRITICAL_ENERGY_PERCENTAGE:
    return None

  # Check if energy is medium (between critical and minimum)
  if energy_percentage < MINIMUM_ENERGY_PERCENTAGE:
    return medium_energy_wit_training(filtered, current_date)

  # Normal energy logic with unified strategy system
  # Check priority strategy type
  score_threshold = extract_score_threshold(priority_strategy)

  if score_threshold is None:
    # G1 or G2 strategy - prioritize racing, no training
    return None
  else:
    # Unified training strategy for all stages
    result = unified_training_selection(filtered, current_date, score_threshold)
    if result:
      return result[0]  # Return only the training key
    return None