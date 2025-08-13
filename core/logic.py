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
  """Get stat priority based on career stage"""
  is_early_stage = current_date and current_date.get('absolute_day', 0) < 16

  if is_early_stage:
    # Day < 16: WIT > SPD > STA > PWR > GUTS
    early_priority = ["wit", "spd", "sta", "pwr", "guts"]
    return early_priority.index(stat_key) if stat_key in early_priority else 999
  else:
    # Normal priority from config
    return get_stat_priority(stat_key)

def calculate_training_score(training_key, training_data, current_date):
  """
  Calculate training score with rainbow bonus and hint scoring
  Returns: (total_score, rainbow_count, hint_score, support_count)
  """
  support_counts = training_data["support"]
  hint_score = training_data.get("hint_score", 0)
  support_count = training_data.get("total_support", 0)

  # Check if in rainbow stage (day > 24)
  is_rainbow_stage = current_date and current_date.get('absolute_day', 0) > 24

  if is_rainbow_stage:
    # After day 24: Rainbow support cards get 2 points
    rainbow_count = support_counts.get(training_key, 0)
    rainbow_score = rainbow_count * 2
    other_support_score = sum(count for stat, count in support_counts.items() if stat != training_key)
    total_score = rainbow_score + other_support_score + hint_score
    return total_score, rainbow_count, hint_score, support_count
  else:
    # Before/at day 24: All support cards count equally
    total_score = support_count + hint_score
    rainbow_count = support_counts.get(training_key, 0)
    return total_score, rainbow_count, hint_score, support_count

def format_score_info(training_key, training_data, current_date):
  """Format training score information for logging"""
  total_score, rainbow_count, hint_score, support_count = calculate_training_score(training_key, training_data, current_date)

  is_early_stage = current_date and current_date.get('absolute_day', 0) < 16
  is_rainbow_stage = current_date and current_date.get('absolute_day', 0) > 24

  hint_info = f" + {training_data.get('hint_count', 0)} hints ({hint_score})" if hint_score > 0 else ""

  if is_rainbow_stage:
    other_supports = support_count - rainbow_count
    return f"(score: {total_score} - {rainbow_count} rainbow × 2 + {other_supports} others × 1{hint_info})"
  elif is_early_stage:
    return f"(score: {total_score} - {support_count} supports{hint_info} - Early stage WIT priority)"
  else:
    return f"(score: {total_score} - {support_count} supports{hint_info})"

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
  else:
    return 2.5  # Default threshold

def find_best_training_by_score(results, current_date, min_score_threshold):
  """
  Find best training that meets minimum score threshold
  """
  if not results:
    return None

  # Filter trainings that meet minimum score - use total_score from results
  valid_trainings = {}
  for key, data in results.items():
    total_score = data.get("total_score", 0)  # Sử dụng total_score đã tính sẵn
    print(f"[DEBUG] {key.upper()}: total_score={total_score}, threshold={min_score_threshold}")
    if total_score >= min_score_threshold:
      valid_trainings[key] = data

  if not valid_trainings:
    print(f"\n[INFO] No training meets minimum score threshold {min_score_threshold}")
    return None

  # Find best training among valid ones
  best_training = max(
    valid_trainings.items(),
    key=lambda x: (
      x[1].get("total_score", 0),  # Sử dụng total_score đã tính sẵn
      -get_priority_by_stage(x[0], current_date)  # Priority (negative for max)
    )
  )

  best_key, best_data = best_training
  total_score = best_data.get("total_score", 0)
  score_info = format_score_info(best_key, best_data, current_date)

  print(f"\n[INFO] Best training meeting score {min_score_threshold}+: {best_key.upper()} {score_info}")
  return best_key

# Main training decision functions
def most_support_card(results, current_date=None):
  """
  Enhanced most support card logic with hint scoring
  Used in Junior Year and when no specific strategy is applied
  """
  # Check if we're in Pre-Debut period (day < 24)
  is_pre_debut = current_date and current_date.get('absolute_day', 0) < 24

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
  Enhanced low energy training logic with hint scoring
  When energy is low, only train WIT if it has 3+ total score
  """
  wit_data = results.get("wit")

  if not wit_data:
    print(f"\n[INFO] Low energy - No WIT training available")
    return None

  # For low energy WIT training, use total score (support + hint)
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

    print(f"\n[INFO] Low energy - WIT training selected with total score {total_score}")
    print(f"[INFO] Breakdown: {wit_data['total_support']} supports{hint_info}")
    print(f"[INFO] Support types: {support_breakdown}")

    if is_pre_debut:
      print(f"[INFO] Pre-Debut: All support types accepted")
    else:
      print(f"[INFO] Low energy: All support types accepted for WIT training")
    return "wit"

  print(f"\n[INFO] Low energy - WIT has insufficient score ({total_score}/3), should rest or race")
  return None

def enhanced_fallback_training(results, current_date):
  """
  Enhanced fallback training with proper hint scoring
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
  Enhanced training decision with new priority strategy system
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

  # Check if energy is low
  if energy_percentage < MINIMUM_ENERGY_PERCENTAGE:
    print(f"[INFO] Energy is low ({energy_percentage}% < {MINIMUM_ENERGY_PERCENTAGE}%), using low energy training logic.")
    return low_energy_training(filtered, current_date)

  # Normal energy logic with new priority strategy system

  # For Junior Year, always use most support card logic
  if "Junior Year" in year:
    print("[INFO] Junior Year - Using most support card strategy")
    return most_support_card(filtered, current_date)

  # Check priority strategy type
  score_threshold = extract_score_threshold(priority_strategy)

  if score_threshold is None:
    # G1 or G2 strategy - prioritize racing, no training
    print(f"[INFO] {priority_strategy} priority strategy - prioritizing race over training")
    return None
  else:
    # Score-based training strategy
    print(f"[INFO] Using score-based training strategy with threshold {score_threshold}")
    result = find_best_training_by_score(filtered, current_date, score_threshold)

    if result is None:
      print(f"[INFO] No training meets score threshold {score_threshold} - should try race or fallback")

    return result

# Enhanced training decision functions for execute.py integration
def enhanced_training_decision(results_training, energy_percentage, strategy_settings, current_date):
  """
  Enhanced training decision with new priority strategy system
  Main function called from execute.py
  """
  if not results_training:
    print(f"[DEBUG] enhanced_training_decision: No results_training provided")
    return None

  print(f"[DEBUG] enhanced_training_decision: Received {len(results_training)} training results")
  for key, data in results_training.items():
    print(f"[DEBUG] Input data - {key.upper()}: total_score={data.get('total_score', 'MISSING')}")

  # Get current stats for caps filtering
  current_stats = stat_state()

  # Filter by stat caps
  filtered_results = filter_by_stat_caps(results_training, current_stats)
  if not filtered_results:
    print(f"[DEBUG] All trainings filtered out by stat caps")
    return None

  print(f"[DEBUG] After stat caps filtering: {len(filtered_results)} trainings remain")

  # Check energy level for low energy logic
  if energy_percentage < MINIMUM_ENERGY_PERCENTAGE:
    print(f"[DEBUG] Low energy detected ({energy_percentage}%), using low energy logic")
    return low_energy_training(filtered_results, current_date)

  # Get strategy and date info
  priority_strategy = strategy_settings.get('priority_strategy', 'Train Score 2.5+')
  is_pre_debut = current_date and current_date.get('absolute_day', 0) < 24

  print(f"[DEBUG] Priority strategy: {priority_strategy}")
  print(f"[DEBUG] Is pre-debut: {is_pre_debut}")

  # For Pre-Debut or Junior Year, use most support card logic
  year = check_current_year()
  if is_pre_debut or "Junior Year" in year:
    print(f"[DEBUG] Using most_support_card logic for {year}")
    return most_support_card(filtered_results, current_date)

  # Check priority strategy type
  score_threshold = extract_score_threshold(priority_strategy)

  if score_threshold is None:
    # G1 or G2 strategy - prioritize racing, no training
    print(f"[DEBUG] Race priority strategy detected - no training")
    return None
  else:
    # Score-based training strategy
    print(f"[DEBUG] Score-based strategy detected - threshold: {score_threshold}")
    return find_best_training_by_score(filtered_results, current_date, score_threshold)