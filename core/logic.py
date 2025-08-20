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

def get_friend_multiplier():
  """Get friend card score multiplier"""
  support_config = SCORING_CONFIG.get("support_score", {})
  return support_config.get("friend_multiplier", 0.75)

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
  """Get stat priority based on career stage with WIT priority in pre-debut and early stage"""
  stage_info = get_career_stage_info(current_date)

  if stage_info['is_pre_debut'] or (stage_info['stage'] == 'early' and stage_info['absolute_day'] <= 24):
    # Pre-debut and early stage (first 24 days): prioritize WIT first, then follow config order
    config_priority = PRIORITY_STAT.copy()
    if 'wit' in config_priority:
      config_priority.remove('wit')
    config_priority.insert(0, 'wit')
    return config_priority.index(stat_key) if stat_key in config_priority else 999
  else:
    # Normal priority from config
    return get_stat_priority(stat_key)

def filter_by_stat_caps(results, current_stats):
  """Filter training results by stat caps to exclude capped stats"""
  return {
    stat: data for stat, data in results.items()
    if current_stats.get(stat, 0) < STAT_CAPS.get(stat, 1200)
  }

def calculate_training_score(training_key, training_data, current_date):
  """Calculate training score with stage-based bonuses using configurable values"""
  support_counts = training_data["support"]
  hint_score = training_data.get("hint_score", 0)
  npc_score = training_data.get("npc_score", 0)
  support_count = sum(count for key, count in support_counts.items() if key != "npc")

  stage_info = get_career_stage_info(current_date)
  base_score = get_support_base_score()
  friend_multiplier = get_friend_multiplier()

  if stage_info['is_pre_debut']:
    # Pre-debut: No rainbow bonus, all support cards = base score
    rainbow_multiplier = get_rainbow_multiplier('pre_debut')
    total_score = support_count * base_score + hint_score + npc_score
    rainbow_count = support_counts.get(training_key, 0)
    return total_score, rainbow_count, hint_score, npc_score, support_count

  elif stage_info['stage'] == 'early':
    # Early stage: Still no rainbow bonus but strategy applies
    rainbow_multiplier = get_rainbow_multiplier('early_stage')
    total_score = support_count * base_score + hint_score + npc_score
    rainbow_count = support_counts.get(training_key, 0)
    return total_score, rainbow_count, hint_score, npc_score, support_count

  elif stage_info['stage'] == 'mid':
    # Mid stage: Rainbow cards get multiplier, friend cards get friend multiplier
    rainbow_count = support_counts.get(training_key, 0)
    friend_count = support_counts.get("friend", 0)
    other_support = support_count - rainbow_count - friend_count

    rainbow_multiplier = get_rainbow_multiplier('mid_stage')
    rainbow_score = rainbow_count * rainbow_multiplier
    friend_score = friend_count * friend_multiplier
    other_score = other_support * base_score

    total_score = rainbow_score + friend_score + other_score + hint_score + npc_score
    return total_score, rainbow_count, hint_score, npc_score, support_count

  else:
    # Late stage: Higher rainbow multiplier
    rainbow_count = support_counts.get(training_key, 0)
    friend_count = support_counts.get("friend", 0)
    other_support = support_count - rainbow_count - friend_count

    rainbow_multiplier = get_rainbow_multiplier('late_stage')
    rainbow_score = rainbow_count * rainbow_multiplier
    friend_score = friend_count * friend_multiplier
    other_score = other_support * base_score

    total_score = rainbow_score + friend_score + other_score + hint_score + npc_score
    return total_score, rainbow_count, hint_score, npc_score, support_count

def format_score_info(training_key, training_data, current_date):
  """Format training score information for logging"""
  total_score, rainbow_count, hint_score, npc_score, support_count = calculate_training_score(training_key, training_data, current_date)

  stage_info = get_career_stage_info(current_date)

  hint_info = f" + {training_data.get('hint_count', 0)} hints ({hint_score})" if hint_score > 0 else ""
  npc_info = f" + {training_data.get('npc_count', 0)} NPCs ({npc_score})" if npc_score > 0 else ""

  if stage_info['is_pre_debut']:
    return f"(score: {total_score} - {support_count} supports{hint_info}{npc_info} - Pre-Debut: No strategy, no rainbow bonus)"
  elif stage_info['stage'] == 'early':
    return f"(score: {total_score} - {support_count} supports{hint_info}{npc_info} - Early Stage: Strategy applies, no rainbow bonus)"
  elif stage_info['stage'] == 'mid':
    rainbow_multiplier = get_rainbow_multiplier('mid_stage')
    return f"(score: {total_score} - {support_count} supports{hint_info}{npc_info} - Mid Stage: {rainbow_multiplier}x rainbow bonus)"
  else:
    rainbow_multiplier = get_rainbow_multiplier('late_stage')
    return f"(score: {total_score} - {support_count} supports{hint_info}{npc_info} - Late Stage: {rainbow_multiplier}x rainbow bonus)"

def extract_score_threshold(priority_strategy):
  """Extract score threshold from priority strategy string"""
  if "G1" in priority_strategy or "G2" in priority_strategy:
    return None  # Race priority - no training
  elif "Score 2+" in priority_strategy:
    return 2.0
  elif "Score 2.5+" in priority_strategy:
    return 2.5
  elif "Score 3+" in priority_strategy:
    return 3.0
  elif "Score 3.5+" in priority_strategy:
    return 3.5
  elif "Score 4+" in priority_strategy:
    return 4.0
  else:
    return 2.5  # Default threshold

def find_best_training_by_score(results, current_date, min_score_threshold):
  """Find best training that meets minimum score threshold"""
  if not results:
    return None

  stage_info = get_career_stage_info(current_date)

  print(f"[DEBUG] Stage: {stage_info['stage']}, Day: {stage_info['absolute_day']}, Pre-Debut: {stage_info['is_pre_debut']}, Apply Strategy: {stage_info['should_apply_strategy']}")

  # In Pre-Debut period, don't apply strategy scoring
  if stage_info['is_pre_debut']:
    print(f"[INFO] Pre-Debut period (Day {stage_info['absolute_day']}/72) - Strategy scoring disabled, will use fallback logic")
    return None

  print(f"[DEBUG] find_best_training_by_score: checking {len(results)} trainings with threshold {min_score_threshold}")

  # After Pre-Debut, apply strategy scoring
  valid_trainings = {}
  for key, data in results.items():
    total_score = data.get("total_score", 0)

    if total_score >= min_score_threshold:
      valid_trainings[key] = data

  if not valid_trainings:
    return None

  # Find best training among valid ones using score first, then priority
  best_training = max(
    valid_trainings.items(),
    key=lambda x: (
      x[1].get("total_score", 0),
      -get_priority_by_stage(x[0], current_date)
    )
  )

  best_key, best_data = best_training
  return best_key

def training_decision(results_training, energy_percentage, strategy_settings, current_date):
  """Enhanced training decision with configurable scoring parameters"""
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
          MINIMUM_ENERGY_PERCENTAGE <= energy_percentage < medium_upper_limit and
          energy_percentage >= CRITICAL_ENERGY_PERCENTAGE):

    # Check if best available training score is <= threshold
    best_score = 0
    for key, data in filtered_results.items():
      total_score = data.get('total_score', 0)
      if total_score > best_score:
        best_score = total_score

    if best_score <= max_score_threshold:
      print(f"[INFO] {stage_info['stage'].title()} stage + medium energy: Best training score ({best_score}) <= {max_score_threshold}, should race instead")
      return None

  # Get strategy
  priority_strategy = strategy_settings.get('priority_strategy', 'Train Score 2.5+')
  score_threshold = extract_score_threshold(priority_strategy)

  if score_threshold is None:
    # G1 or G2 strategy - prioritize racing, no training
    return None
  else:
    # Score-based training strategy
    if stage_info['is_pre_debut']:
      # Pre-Debut: Use fallback logic (most_support_card)
      print(f'[INFO] Pre-debut period (Day {stage_info["absolute_day"]}/72): Using fallback logic instead of {priority_strategy}')
      return most_support_card(filtered_results, current_date)
    else:
      # Post Pre-Debut: Apply strategy scoring
      print(f'[INFO] {stage_info["stage"].title()} stage (Day {stage_info["absolute_day"]}/72): Applying {priority_strategy}')
      result = find_best_training_by_score(filtered_results, current_date, score_threshold)

      if result:
        return result
      else:
        print(f'[INFO] No training meets {priority_strategy} requirements - should try racing instead')
        return None

def medium_energy_wit_training(results, current_date):
  """Medium energy training - only WIT with configurable score requirements"""
  wit_data = results.get("wit")
  if not wit_data:
    print(f"[DEBUG] Medium energy - No WIT training available")
    return None

  stage_info = get_career_stage_info(current_date)
  total_score = wit_data.get("total_score", 0)
  required_score = get_wit_score_requirement("medium_energy", stage_info['is_pre_debut'])

  if total_score >= required_score:
    support_breakdown = wit_data["support"]
    hint_info = ""
    if wit_data.get('hint_count', 0) > 0:
      hint_info = f" + {wit_data['hint_count']} hints ({wit_data['hint_score']} score)"

    npc_info = ""
    if wit_data.get('npc_count', 0) > 0:
      npc_info = f" + {wit_data['npc_count']} NPCs ({wit_data['npc_score']} score)"

    stage_name = f"{stage_info['stage'].title()} {'(Pre-Debut)' if stage_info['is_pre_debut'] else ''}"
    print(f"[INFO] Medium energy - WIT training selected with total score {total_score} (required: {required_score}+)")
    print(f"[INFO] Breakdown: {wit_data['total_support']} supports{hint_info}{npc_info} ({stage_name})")
    print(f"[INFO] Support types: {support_breakdown}")

    return "wit"

  stage_name = f"{stage_info['stage'].title()} {'(Pre-Debut)' if stage_info['is_pre_debut'] else ''}"
  print(f"[INFO] Medium energy - WIT has insufficient score ({total_score}/{required_score}) for {stage_name} stage - should rest or race")
  return None

def most_support_card(results, current_date=None):
  """Fallback logic for Pre-Debut period and when no training meets strategy requirements"""
  stage_info = get_career_stage_info(current_date)

  # In pre-debut, prioritize by highest score first, then WIT priority
  if stage_info['is_pre_debut']:
    valid_trainings = {k: v for k, v in results.items() if v.get("total_score", 0) > 0}

    if valid_trainings:
      # Sort by score first (highest), then by WIT priority (lowest index = highest priority)
      best_training = max(
        valid_trainings.items(),
        key=lambda x: (
          x[1].get("total_score", 0),
          -get_priority_by_stage(x[0], current_date)
        )
      )

      best_key, best_data = best_training
      score_info = format_score_info(best_key, best_data, current_date)
      print(f"\n[INFO] Pre-debut fallback training: {best_key.upper()} {score_info}")

      # Debug log to verify selection
      print(f"[DEBUG] Pre-debut selection - WIT score: {results.get('wit', {}).get('total_score', 0)}, STA score: {results.get('sta', {}).get('total_score', 0)}, Selected: {best_key.upper()}")

      return best_key

    print(f"\n[INFO] Pre-debut: No training with score > 0 found")
    return None

  # Post Pre-Debut fallback logic
  if not results:
    print("\n[INFO] No training found.")
    return None

  # Find best training based on total score and priority
  best_training = max(
    results.items(),
    key=lambda x: (
      calculate_training_score(x[0], x[1], current_date)[0],
      -get_priority_by_stage(x[0], current_date)
    )
  )

  best_key, best_data = best_training
  total_score = calculate_training_score(best_key, best_data, current_date)[0]

  # Check minimum score requirements
  if total_score <= 1:
    if best_key == "wit":
      print(f"\n[INFO] Only {total_score} score and it's WIT. Skipping.")
      return None
    print(f"\n[INFO] Only {total_score} score. Prioritizing based on priority list: {best_key.upper()}")
    return best_key

  score_info = format_score_info(best_key, best_data, current_date)
  print(f"\nFallback training: {best_key.upper()} {score_info}")
  return best_key

def low_energy_training(results, current_date=None):
  """Enhanced low energy training logic with configurable score requirements"""
  wit_data = results.get("wit")

  if not wit_data:
    print(f"\n[INFO] Low energy - No WIT training available")
    return None

  stage_info = get_career_stage_info(current_date)
  total_score = wit_data.get("total_score", 0)
  required_score = get_wit_score_requirement("low_energy", stage_info['is_pre_debut'])

  print(f"\n[INFO] {stage_info['stage'].title()} stage detected (Day {stage_info['absolute_day']}/72)")

  if total_score >= required_score:
    support_breakdown = wit_data["support"]
    hint_info = ""
    if wit_data.get('hint_count', 0) > 0:
      hint_info = f" + {wit_data['hint_count']} hints ({wit_data['hint_score']} score)"

    npc_info = ""
    if wit_data.get('npc_count', 0) > 0:
      npc_info = f" + {wit_data['npc_count']} NPCs ({wit_data['npc_score']} score)"

    stage_name = f"{stage_info['stage'].title()} {'(Pre-Debut)' if stage_info['is_pre_debut'] else ''}"
    print(f"\n[INFO] Low energy - WIT training selected with total score {total_score} (required: {required_score}+)")
    print(f"[INFO] Breakdown: {wit_data['total_support']} supports{hint_info}{npc_info}")
    print(f"[INFO] Support types: {support_breakdown}")
    print(f"[INFO] Stage: {stage_name}")
    return "wit"

  stage_name = f"{stage_info['stage'].title()} {'(Pre-Debut)' if stage_info['is_pre_debut'] else ''}"
  print(f"\n[INFO] Low energy - WIT has insufficient score ({total_score}/{required_score}) for {stage_name}, should rest or race")
  return None

def fallback_training(results, current_date):
  """Enhanced fallback training with configurable stage-based scoring"""
  if not results:
    return None

  stage_info = get_career_stage_info(current_date)

  # Calculate best training using enhanced scoring
  best_training = max(
    results.items(),
    key=lambda x: (
      calculate_training_score(x[0], x[1], current_date)[0],
      -get_priority_by_stage(x[0], current_date)
    )
  )

  best_key, best_data = best_training
  total_score = calculate_training_score(best_key, best_data, current_date)[0]

  if total_score <= 0:
    return None

  score_info = format_score_info(best_key, best_data, current_date)
  print(f"\n[INFO] Fallback training for {stage_info['stage']} stage: {best_key.upper()} {score_info}")
  return best_key, score_info

def do_something(results, energy_percentage=100, strategy_settings=None):
  """Enhanced training decision with configurable scoring system"""
  year = check_current_year()
  current_stats = stat_state()
  print(f"Current stats: {current_stats}")
  print(f"Current energy: {energy_percentage}%")

  # Default strategy settings if not provided
  if strategy_settings is None:
    strategy_settings = {
      'minimum_mood': 'NORMAL',
      'priority_strategy': 'Train Score 2.5+'
    }

  priority_strategy = strategy_settings.get('priority_strategy', 'Train Score 2.5+')
  print(f"Priority Strategy: {priority_strategy}")

  # Get current date info to check stage
  from core.state import get_current_date_info
  current_date = get_current_date_info()

  stage_info = get_career_stage_info(current_date)
  print(f"Career Stage: {stage_info['stage'].title()} (Day {stage_info['absolute_day']}/72)")
  if stage_info['is_pre_debut']:
    print(f"Pre-Debut Period: Strategy scoring disabled")
  else:
    print(f"Post Pre-Debut: Strategy scoring enabled")

  # Filter by stat caps
  filtered = filter_by_stat_caps(results, current_stats)

  if not filtered:
    print("[INFO] All stats capped or no valid training.")
    return None

  # Check if energy is critical
  if energy_percentage < CRITICAL_ENERGY_PERCENTAGE:
    print(f"[INFO] Energy is critical ({energy_percentage}% < {CRITICAL_ENERGY_PERCENTAGE}%), no training allowed.")
    return None

  # Check if energy is medium (between critical and minimum)
  if energy_percentage < MINIMUM_ENERGY_PERCENTAGE:
    print(f"[INFO] Energy is medium ({energy_percentage}% < {MINIMUM_ENERGY_PERCENTAGE}%), using medium energy WIT logic.")
    return medium_energy_wit_training(filtered, current_date)

  # Normal energy logic with configurable strategy system
  print(f"[INFO] Using strategy: {priority_strategy}")

  # Check priority strategy type
  score_threshold = extract_score_threshold(priority_strategy)

  if score_threshold is None:
    # G1 or G2 strategy - prioritize racing, no training
    print(f"[INFO] {priority_strategy} priority strategy - prioritizing race over training")
    return None
  else:
    # Score-based training strategy
    if stage_info['is_pre_debut']:
      print(f"[INFO] Pre-Debut period: Using fallback logic instead of score threshold {score_threshold}")
      return most_support_card(filtered, current_date)
    else:
      print(f"[INFO] {stage_info['stage'].title()} stage: Using score-based training strategy with threshold {score_threshold}")
      result = find_best_training_by_score(filtered, current_date, score_threshold)

      if result is None:
        print(f"[INFO] No training meets score threshold {score_threshold} - should try race or fallback")

      return result