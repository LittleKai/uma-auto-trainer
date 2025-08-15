import json

from core.state import check_current_year, stat_state

with open("config.json", "r", encoding="utf-8") as file:
  config = json.load(file)

PRIORITY_STAT = config["priority_stat"]
MINIMUM_ENERGY_PERCENTAGE = config["minimum_energy_percentage"]
CRITICAL_ENERGY_PERCENTAGE = config["critical_energy_percentage"]
STAT_CAPS = config["stat_caps"]

# Get priority stat from config
def get_stat_priority(stat_key: str) -> int:
  return PRIORITY_STAT.index(stat_key) if stat_key in PRIORITY_STAT else 999

def filter_by_stat_caps(results, current_stats):
  """Filter training results by stat caps"""
  return {
    stat: data for stat, data in results.items()
    if current_stats.get(stat, 0) < STAT_CAPS.get(stat, 1200)
  }

def get_priority_by_stage(stat_key, current_date):
  """Get stat priority based on career stage with config-based ordering"""
  is_pre_debut = current_date and current_date.get('absolute_day', 0) < 24

  if is_pre_debut:
    # Pre-debut: Use config priority but move WIT to highest priority if not already there
    config_priority = PRIORITY_STAT.copy()

    # Remove WIT from its current position and put it first
    if 'wit' in config_priority:
      config_priority.remove('wit')
    config_priority.insert(0, 'wit')

    return config_priority.index(stat_key) if stat_key in config_priority else 999
  else:
    # Normal priority from config
    return get_stat_priority(stat_key)

def calculate_training_score(training_key, training_data, current_date):
  """
  Calculate training score with rainbow bonus, hint scoring, and grouped NPC scoring
  FIXED: No rainbow bonus in pre-debut period
  Returns: (total_score, rainbow_count, hint_score, npc_score, support_count)
  """
  support_counts = training_data["support"]
  hint_score = training_data.get("hint_score", 0)
  npc_score = training_data.get("npc_score", 0)
  # Updated to exclude 'npc' from total_support calculation since it's now grouped
  support_count = sum(count for key, count in support_counts.items() if key != "npc")

  # Check if in pre-debut or rainbow stage
  is_pre_debut = current_date and current_date.get('absolute_day', 0) < 24
  is_rainbow_stage = current_date and current_date.get('absolute_day', 0) > 24

  if is_pre_debut:
    # Pre-debut: No rainbow bonus, all support cards = 1 point
    total_score = support_count + hint_score + npc_score
    rainbow_count = support_counts.get(training_key, 0)
    return total_score, rainbow_count, hint_score, npc_score, support_count
  elif is_rainbow_stage:
    # After day 24: Rainbow support cards get 2 points
    rainbow_count = support_counts.get(training_key, 0)
    rainbow_score = rainbow_count * 2
    other_support_score = sum(count for stat, count in support_counts.items()
                              if stat != training_key and stat != "npc")
    total_score = rainbow_score + other_support_score + hint_score + npc_score
    return total_score, rainbow_count, hint_score, npc_score, support_count
  else:
    # Day 24 and before: All support cards count equally
    total_score = support_count + hint_score + npc_score
    rainbow_count = support_counts.get(training_key, 0)
    return total_score, rainbow_count, hint_score, npc_score, support_count

def format_score_info(training_key, training_data, current_date):
  """Format training score information for logging with grouped NPC support"""
  total_score, rainbow_count, hint_score, npc_score, support_count = calculate_training_score(training_key, training_data, current_date)

  is_early_stage = current_date and current_date.get('absolute_day', 0) < 24
  is_rainbow_stage = current_date and current_date.get('absolute_day', 0) > 24

  hint_info = f" + {training_data.get('hint_count', 0)} hints ({hint_score})" if hint_score > 0 else ""
  npc_info = f" + {training_data.get('npc_count', 0)} NPCs ({npc_score})" if npc_score > 0 else ""

  if is_early_stage:
    return f"(score: {total_score} - {support_count} supports{hint_info}{npc_info} - Early Stage: No rainbow bonus, WIT priority)"
  elif is_rainbow_stage:
    return f"(score: {total_score})"
  else:
    return f"(score: {total_score} - {support_count} supports{hint_info}{npc_info})"

def extract_score_threshold(priority_strategy):
  """
  Extract score threshold from priority strategy
  Returns threshold value or None for race priority strategies
  """
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
  """
  Find best training that meets minimum score threshold with enhanced grouped NPC support
  FIXED: In Pre-Debut, prioritize highest score training even if not WIT
  """
  if not results:
    return None

  print(f"[DEBUG] find_best_training_by_score: checking {len(results)} trainings with threshold {min_score_threshold}")

  is_pre_debut = current_date and current_date.get('absolute_day', 0) < 16

  # Filter trainings that meet minimum score - use total_score from results
  valid_trainings = {}
  for key, data in results.items():
    total_score = data.get("total_score", 0)  # Use pre-calculated total_score
    print(f"[DEBUG] {key.upper()}: total_score={total_score}, threshold={min_score_threshold}")

    if total_score >= min_score_threshold:
      valid_trainings[key] = data
      print(f"[DEBUG] {key.upper()} PASSED threshold check ({total_score} >= {min_score_threshold})")
    else:
      print(f"[DEBUG] {key.upper()} FAILED threshold check ({total_score} < {min_score_threshold})")

  if not valid_trainings:
    print(f"\n[INFO] No training meets minimum score threshold {min_score_threshold}")

    # In pre-debut, try any training with score > 0, prioritize by score then WIT priority
    if is_pre_debut:
      # Find training with highest score > 0
      valid_pre_debut = {k: v for k, v in results.items() if v.get("total_score", 0) > 0}
      if valid_pre_debut:
        best_pre_debut = max(
          valid_pre_debut.items(),
          key=lambda x: (
            x[1].get("total_score", 0),  # Highest score first
            -get_priority_by_stage(x[0], current_date)  # Then WIT priority
          )
        )
        best_key, best_data = best_pre_debut
        total_score = best_data.get("total_score", 0)
        print(f"[INFO] Pre-debut: Using highest score training {best_key.upper()} with score {total_score}")
        return best_key

    return None

  print(f"[DEBUG] {len(valid_trainings)} trainings passed threshold: {list(valid_trainings.keys())}")

  # Find best training among valid ones using score first, then priority
  best_training = max(
    valid_trainings.items(),
    key=lambda x: (
      x[1].get("total_score", 0),  # Use total_score
      -get_priority_by_stage(x[0], current_date)  # Priority (negative for max)
    )
  )

  best_key, best_data = best_training
  total_score = best_data.get("total_score", 0)
  score_info = format_score_info(best_key, best_data, current_date)

  print(f"\n[INFO] Best training meeting score {min_score_threshold}+: {best_key.upper()} {score_info}")
  return best_key

def training_decision(results_training, energy_percentage, strategy_settings, current_date):
  """
  Enhanced training decision with new priority strategy system and grouped NPC support
  Added mid-game energy restriction for low score training
  """
  if not results_training:
    return None

  for key, data in results_training.items():
    total_score = data.get('total_score', 'MISSING')

  # Get current stats for caps filtering
  from core.state import stat_state
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

  # Mid-game energy restriction for low score training
  absolute_day = current_date.get('absolute_day', 0) if current_date else 0
  if (absolute_day > 16 and
          MINIMUM_ENERGY_PERCENTAGE <= energy_percentage < 50 and
          energy_percentage >= CRITICAL_ENERGY_PERCENTAGE):

    # Check if best available training score is <= 2.5
    best_score = 0
    for key, data in filtered_results.items():
      total_score = data.get('total_score', 0)
      if total_score > best_score:
        best_score = total_score

    if best_score <= 2.5:
      return None

  # Get strategy and date info
  priority_strategy = strategy_settings.get('priority_strategy', 'Train Score 2.5+')
  is_pre_debut = current_date and current_date.get('absolute_day', 0) < 16

  # Check priority strategy type
  score_threshold = extract_score_threshold(priority_strategy)

  if score_threshold is None:
    # G1 or G2 strategy - prioritize racing, no training
    return None
  else:
    # Score-based training strategy - APPLY TO ALL PERIODS
    result = find_best_training_by_score(filtered_results, current_date, score_threshold)

    if result:
      return result
    else:
      # In Pre-Debut, use fallback to most_support_card logic if no training meets threshold
      if is_pre_debut:
        print('is_pre_debut true')
        return most_support_card(filtered_results, current_date)

      return None


def do_something(results, energy_percentage=100, strategy_settings=None):
  """
  Enhanced training decision with new priority strategy system and grouped NPC support
  Added mid-game energy restriction for low score training
  """
  year = check_current_year()
  current_stats = stat_state()

  # Default strategy settings if not provided
  if strategy_settings is None:
    strategy_settings = {
      'minimum_mood': 'NORMAL',
      'priority_strategy': 'Train Score 2.5+'
    }

  priority_strategy = strategy_settings.get('priority_strategy', 'Train Score 2.5+')

  # Get current date info to check stage and Pre-Debut period
  from core.state import get_current_date_info
  current_date = get_current_date_info()

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

  # NEW: Mid-game energy restriction for low score training
  absolute_day = current_date.get('absolute_day', 0) if current_date else 0
  if (absolute_day > 24 and
          MINIMUM_ENERGY_PERCENTAGE <= energy_percentage < 50):

    # Check if best available training score is <= 2.5
    best_score = 0
    for key, data in filtered.items():
      # Calculate score for each training
      total_score, _, _, _, _ = calculate_training_score(key, data, current_date)
      if total_score > best_score:
        best_score = total_score

    if best_score <= 2.5:
      return None


  # Check priority strategy type
  score_threshold = extract_score_threshold(priority_strategy)

  if score_threshold is None:
    # G1 or G2 strategy - prioritize racing, no training
    return None
  else:
    # Score-based training strategy - APPLY REGARDLESS OF PERIOD
    result = find_best_training_by_score(filtered, current_date, score_threshold)


    return result

def medium_energy_wit_training(results, current_date):
  """
  Medium energy training - only WIT with enhanced score requirements
  Score 3+ normally, but Score 2+ in pre-debut
  """
  wit_data = results.get("wit")
  if not wit_data:
    print(f"[DEBUG] Medium energy - No WIT training available")
    return None

  # Get current date info to check if in Pre-Debut period
  is_pre_debut = current_date and current_date.get('absolute_day', 0) < 24

  # Use total score (support + hint + grouped NPC)
  total_score = wit_data.get("total_score", 0)

  # Different score requirements based on career stage
  required_score = 2.0 if is_pre_debut else 3.0

  if total_score >= required_score:
    support_breakdown = wit_data["support"]
    hint_info = ""
    if wit_data.get('hint_count', 0) > 0:
      hint_info = f" + {wit_data['hint_count']} hints ({wit_data['hint_score']} score)"

    npc_info = ""
    if wit_data.get('npc_count', 0) > 0:
      npc_info = f" + {wit_data['npc_count']} NPCs ({wit_data['npc_score']} score)"

    stage_info = "Pre-Debut" if is_pre_debut else "Normal"
    print(f"[INFO] Medium energy - WIT training selected with total score {total_score} (required: {required_score}+)")
    print(f"[INFO] Breakdown: {wit_data['total_support']} supports{hint_info}{npc_info} ({stage_info})")
    print(f"[INFO] Support types: {support_breakdown}")

    return "wit"

  stage_info = "Pre-Debut" if is_pre_debut else "Normal"
  print(f"[INFO] Medium energy - WIT has insufficient score ({total_score}/{required_score}) for {stage_info} stage - should rest or race")
  return None

# Main training decision functions
def most_support_card(results, current_date=None):
  """
  FIXED: Pre-Debut logic to prioritize highest score, then WIT priority
  """
  # Check if we're in Pre-Debut period (day < 24)
  is_pre_debut = current_date and current_date.get('absolute_day', 0) < 24

  # FIXED: In pre-debut, prioritize by score first, then WIT priority
  if is_pre_debut:
    # Find all trainings with score > 0
    valid_trainings = {k: v for k, v in results.items() if v.get("total_score", 0) > 0}

    if valid_trainings:
      # Sort by score first, then by WIT priority
      best_training = max(
        valid_trainings.items(),
        key=lambda x: (
          x[1].get("total_score", 0),  # Highest score first
          -get_priority_by_stage(x[0], current_date)  # Then WIT priority
        )
      )

      best_key, best_data = best_training
      score_info = format_score_info(best_key, best_data, current_date)
      print(f"\n[INFO] Pre-debut best training: {best_key.upper()} {score_info}")
      return best_key

    print(f"\n[INFO] Pre-debut: No training with score > 0 found")
    return None

  # Separate wit for special checking
  wit_data = results.get("wit")

  # Get all training but wit
  non_wit_results = {
    k: v for k, v in results.items()
    if k != "wit"
  }

  # Check if all non-wit training is bad
  all_others_bad = len(non_wit_results) == 0

  if all_others_bad and wit_data:
    wit_score = wit_data.get("total_score", 0)
    if wit_score >= 2:
      print(f"\n[INFO] All trainings are unsafe, but WIT is safe and has enough score ({wit_score}).")
      return "wit"

  filtered_results = results

  if not filtered_results:
    print("\n[INFO] No training found.")
    return None

  # Find best training based on total score and priority
  best_training = max(
    filtered_results.items(),
    key=lambda x: (
      calculate_training_score(x[0], x[1], current_date)[0],  # Total score
      -get_priority_by_stage(x[0], current_date)  # Priority (negative for max)
    )
  )

  best_key, best_data = best_training
  total_score = calculate_training_score(best_key, best_data, current_date)[0]

  # Check minimum score requirements
  if total_score <= 1:
    # WIT must be at least 2 score
    if best_key == "wit":
      print(f"\n[INFO] Only {total_score} score and it's WIT. Skipping.")
      return None
    print(f"\n[INFO] Only {total_score} score. Prioritizing based on priority list: {best_key.upper()}")
    return best_key

  # Generate detailed info
  score_info = format_score_info(best_key, best_data, current_date)

  if is_pre_debut:
    score_info += " (Pre-Debut: All types accepted)"

  print(f"\nBest training: {best_key.upper()} {score_info}")
  return best_key

def low_energy_training(results, current_date=None):
  """
  Enhanced low energy training logic with hint and grouped NPC scoring
  When energy is low, only train WIT if it has 3+ total score
  """
  wit_data = results.get("wit")

  if not wit_data:
    print(f"\n[INFO] Low energy - No WIT training available")
    return None

  # For low energy WIT training, use total score (support + hint + grouped NPC)
  total_score = wit_data.get("total_score", 0)

  # Check if we're in Pre-Debut period (day < 24)
  is_pre_debut = current_date and current_date.get('absolute_day', 0) < 24

  if is_pre_debut:
    print(f"\n[INFO] Pre-Debut period detected (Day {current_date.get('absolute_day', 0)}/72)")

  if total_score >= 3:
    support_breakdown = wit_data["support"]
    hint_info = ""
    if wit_data.get('hint_count', 0) > 0:
      hint_info = f" + {wit_data['hint_count']} hints ({wit_data['hint_score']} score)"

    npc_info = ""
    if wit_data.get('npc_count', 0) > 0:
      npc_info = f" + {wit_data['npc_count']} NPCs ({wit_data['npc_score']} score)"

    print(f"\n[INFO] Low energy - WIT training selected with total score {total_score}")
    print(f"[INFO] Breakdown: {wit_data['total_support']} supports{hint_info}{npc_info}")
    print(f"[INFO] Support types: {support_breakdown}")

    if is_pre_debut:
      print(f"[INFO] Pre-Debut: All support types accepted")
    else:
      print(f"[INFO] Low energy: All support types accepted for WIT training")
    return "wit"

  print(f"\n[INFO] Low energy - WIT has insufficient score ({total_score}/3), should rest or race")
  return None

def fallback_training(results, current_date):
  """
  Enhanced fallback training with proper hint and grouped NPC scoring
  Used when primary strategy doesn't find suitable training
  """
  if not results:
    return None

  # Calculate best training using enhanced scoring
  best_training = max(
    results.items(),
    key=lambda x: (
      calculate_training_score(x[0], x[1], current_date)[0],  # Total score
      -get_priority_by_stage(x[0], current_date)  # Priority
    )
  )

  best_key, best_data = best_training
  total_score = calculate_training_score(best_key, best_data, current_date)[0]

  if total_score <= 0:
    return None

  score_info = format_score_info(best_key, best_data, current_date)
  return best_key, score_info

# Main decision function
def do_something(results, energy_percentage=100, strategy_settings=None):
  """
  Enhanced training decision with new priority strategy system and grouped NPC support
  """
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

  # Get current date info to check stage and Pre-Debut period
  from core.state import get_current_date_info
  current_date = get_current_date_info()

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

  # Normal energy logic with new priority strategy system - ALWAYS RESPECT STRATEGY
  print(f"[INFO] Using strategy: {priority_strategy}")

  # Check priority strategy type
  score_threshold = extract_score_threshold(priority_strategy)

  if score_threshold is None:
    # G1 or G2 strategy - prioritize racing, no training
    print(f"[INFO] {priority_strategy} priority strategy - prioritizing race over training")
    return None
  else:
    # Score-based training strategy - APPLY REGARDLESS OF PERIOD
    print(f"[INFO] Using score-based training strategy with threshold {score_threshold}")
    result = find_best_training_by_score(filtered, current_date, score_threshold)

    if result is None:
      print(f"[INFO] No training meets score threshold {score_threshold} - should try race or fallback")

    return result