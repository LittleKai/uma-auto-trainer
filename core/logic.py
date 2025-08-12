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

# Will do train with the most support card
# Used in the first year (aim for rainbow)
def most_support_card(results, current_date=None):
  # Check if we're in Pre-Debut period (day < 24)
  is_pre_debut = current_date and current_date.get('absolute_day', 0) < 24

  # Seperate wit
  wit_data = results.get("wit")

  # Get all training but wit
  non_wit_results = {
    k: v for k, v in results.items()
    if k != "wit"
  }

  # Check if train is bad
  all_others_bad = len(non_wit_results) == 0

  if all_others_bad and wit_data and wit_data["total_support"] >= 2:
    print("\n[INFO] All trainings are unsafe, but WIT is safe and has enough support cards.")
    return "wit"

  filtered_results = results

  if not filtered_results:
    print("\n[INFO] No training found.")
    return None

  # Best training
  best_training = max(
    filtered_results.items(),
    key=lambda x: (
      x[1]["total_support"],
      -get_stat_priority(x[0])  # priority decides when supports are equal
    )
  )

  best_key, best_data = best_training

  if best_data["total_support"] <= 1:
    # WIT must be at least 2 support cards
    if best_key == "wit":
      print(f"\n[INFO] Only 1 support and it's WIT. Skipping.")
      return None
    print(f"\n[INFO] Only 1 support. Prioritizing based on priority list: {best_key.upper()}")
    return best_key

  support_info = f" with {best_data['total_support']} support cards"
  if is_pre_debut:
    support_info += f" (Pre-Debut: All types accepted)"

  print(f"\nBest training: {best_key.upper()}{support_info}")
  return best_key

# Do rainbow training
def rainbow_training(results):
  # Get rainbow training
  rainbow_candidates = {
    stat: data for stat, data in results.items()
    if data["support"].get(stat, 0) > 0
  }

  if not rainbow_candidates:
    print("\n[INFO] No rainbow training found.")
    return None

  # Find support card rainbow in training
  best_rainbow = max(
    rainbow_candidates.items(),
    key=lambda x: (
      x[1]["support"].get(x[0], 0),
      -get_stat_priority(x[0])
    )
  )

  best_key, best_data = best_rainbow
  print(f"\n[INFO] Rainbow training selected: {best_key.upper()} with {best_data['support'][best_key]} rainbow supports")
  return best_key

def filter_by_stat_caps(results, current_stats):
  return {
    stat: data for stat, data in results.items()
    if current_stats.get(stat, 0) < STAT_CAPS.get(stat, 1200)
  }

# Low energy training logic - only check WIT
def low_energy_training(results, current_date=None):
  """
  When energy is low, only train WIT if it has 3+ support cards
  In Pre-Debut period (day < 24), friend cards count as any type
  For low energy WIT, accept any support card types, not just WIT type
  Otherwise return None to indicate rest/race
  """
  wit_data = results.get("wit")

  if not wit_data:
    print(f"\n[INFO] Low energy - No WIT training available")
    return None

  # For low energy WIT training, count ALL support cards (any type)
  total_support_any_type = wit_data["total_support"]

  # Check if we're in Pre-Debut period (day < 24)
  is_pre_debut = current_date and current_date.get('absolute_day', 0) < 24

  if is_pre_debut:
    print(f"\n[INFO] Pre-Debut period detected (Day {current_date.get('absolute_day', 0)}/72)")

  if total_support_any_type >= 3:
    support_breakdown = wit_data["support"]
    print(f"\n[INFO] Low energy - WIT training selected with {total_support_any_type} total support cards")
    print(f"[INFO] Support breakdown: {support_breakdown}")
    if is_pre_debut:
      print(f"[INFO] Pre-Debut: All support types accepted")
    else:
      print(f"[INFO] Low energy: All support types accepted for WIT training")
    return "wit"

  print(f"\n[INFO] Low energy - WIT has insufficient support cards ({total_support_any_type}/3), should rest or race")
  return None

# NEW: Check rainbow training based on priority strategy
def check_rainbow_training_by_strategy(results, priority_strategy):
  """
  Check if rainbow training meets the priority strategy requirements
  """
  if "Rainbow" not in priority_strategy:
    return False, None

  # Extract required rainbow count from strategy
  if "1+" in priority_strategy:
    required_count = 1
  elif "2+" in priority_strategy:
    required_count = 2
  elif "3+" in priority_strategy:
    required_count = 3
  else:
    return False, None

  # Get rainbow training candidates
  rainbow_candidates = {
    stat: data for stat, data in results.items()
    if data["support"].get(stat, 0) >= required_count
  }

  if not rainbow_candidates:
    print(f"\n[INFO] No training with {required_count}+ rainbow supports found")
    return False, None

  # Find best rainbow training
  best_rainbow = max(
    rainbow_candidates.items(),
    key=lambda x: (
      x[1]["support"].get(x[0], 0),
      -get_stat_priority(x[0])
    )
  )

  best_key, best_data = best_rainbow
  rainbow_count = best_data['support'][best_key]
  print(f"\n[INFO] Found {best_key.upper()} training with {rainbow_count} rainbow supports (required: {required_count}+)")
  return True, best_key

# Decide training based on strategy settings
def do_something(results, energy_percentage=100, strategy_settings=None):
  """
  Enhanced training decision with priority strategy
  """
  year = check_current_year()
  current_stats = stat_state()
  print(f"Current stats: {current_stats}")
  print(f"Current energy: {energy_percentage}%")

  # Default strategy settings if not provided
  if strategy_settings is None:
    strategy_settings = {
      'minimum_mood': 'NORMAL',
      'priority_strategy': 'G1'
    }

  priority_strategy = strategy_settings.get('priority_strategy', 'G1')
  print(f"Priority Strategy: {priority_strategy}")

  # Get current date info to check if in Pre-Debut period
  from core.state import get_current_date_info
  current_date = get_current_date_info()

  filtered = filter_by_stat_caps(results, current_stats)

  if not filtered:
    print("[INFO] All stats capped or no valid training.")
    return None

  # Check if energy is low
  if energy_percentage < MINIMUM_ENERGY_PERCENTAGE:
    print(f"[INFO] Energy is low ({energy_percentage}% < {MINIMUM_ENERGY_PERCENTAGE}%), using low energy training logic.")
    return low_energy_training(filtered, current_date)

  # Normal energy logic with priority strategy

  # For Junior Year, always use most support card logic
  if "Junior Year" in year:
    print("[INFO] Junior Year - Using most support card strategy")
    return most_support_card(filtered, current_date)

  # For Classic/Senior years, check priority strategy
  if priority_strategy in ["G1", "G2"]:
    # Race priority strategies - return None to indicate should race instead of train
    # But only if we're checking training specifically for strategy compliance
    print(f"[INFO] {priority_strategy} priority strategy - checking if should prioritize race over training")
    return None

  elif "Rainbow" in priority_strategy:
    # Rainbow training priority strategies
    has_rainbow, training = check_rainbow_training_by_strategy(filtered, priority_strategy)

    if has_rainbow:
      print(f"[INFO] {priority_strategy} strategy satisfied - doing rainbow training")
      return training
    else:
      print(f"[INFO] {priority_strategy} strategy not satisfied - should try race or fallback training")
      return None

  else:
    # Fallback to rainbow training if strategy not recognized
    print("[INFO] Unknown strategy, falling back to rainbow training")
    result = rainbow_training(filtered)
    if result is None:
      print("[INFO] Falling back to most_support_card because rainbow not available.")
      return most_support_card(filtered, current_date)
    return result