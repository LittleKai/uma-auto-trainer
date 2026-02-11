import json

from core.state import check_current_year, stat_state

# Global config cache
_config_cache = None

def _load_config():
  """Load config from file"""
  with open("config.json", "r", encoding="utf-8") as file:
    return json.load(file)

def get_config():
  """Get current config, loading from file if not cached"""
  global _config_cache
  if _config_cache is None:
    _config_cache = _load_config()
  return _config_cache

def reload_config():
  """Reload config from file - call this after config changes"""
  global _config_cache
  _config_cache = _load_config()
  print("[CONFIG] Configuration reloaded from file")
  return _config_cache

# Legacy support - these will be updated on reload
config = _load_config()
PRIORITY_STAT = config["priority_stat"]
MINIMUM_ENERGY_PERCENTAGE = config["minimum_energy_percentage"]
CRITICAL_ENERGY_PERCENTAGE = config["critical_energy_percentage"]


def set_stat_caps(new_stat_caps):
    """Update stat caps in constants module (single source of truth)"""
    try:
        from utils.constants import CURRENT_DECK
        if new_stat_caps:
            CURRENT_DECK["stat_caps"] = new_stat_caps.copy()
            print(f"[STAT CAPS] Updated stat caps: {new_stat_caps}")
    except Exception as e:
        print(f"[STAT CAPS] Error updating stat caps: {e}")


def get_stat_caps():
    """Get current stat caps from constants module"""
    try:
        from utils.constants import get_stat_caps as get_caps
        return get_caps()
    except Exception as e:
        print(f"[STAT CAPS] Error getting stat caps: {e}")
        return {
            "spd": 1200,
            "sta": 1100,
            "pwr": 1200,
            "guts": 1200,
            "wit": 1200
        }



# Load scoring configuration (initial)
SCORING_CONFIG = config.get("scoring_config", {})

# Career Stage Constants (will be updated on reload)
PRE_DEBUT_THRESHOLD = SCORING_CONFIG.get("stage_thresholds", {}).get("pre_debut", 16)
EARLY_STAGE_THRESHOLD = SCORING_CONFIG.get("stage_thresholds", {}).get("early_stage", 24)
MID_STAGE_THRESHOLD = SCORING_CONFIG.get("stage_thresholds", {}).get("mid_stage", 48)

def get_scoring_config():
  """Get scoring configuration from current config (supports hot reload)"""
  return get_config().get("scoring_config", {})

def get_priority_stat():
  """Get priority stat list from current config"""
  return get_config().get("priority_stat", ["spd", "pwr", "sta", "wit", "guts"])

def get_minimum_energy():
  """Get minimum energy percentage from current config"""
  return get_config().get("minimum_energy_percentage", 43)

def get_critical_energy():
  """Get critical energy percentage from current config"""
  return get_config().get("critical_energy_percentage", 20)

def get_stage_thresholds():
  """Get stage thresholds from current config"""
  scoring = get_scoring_config()
  thresholds = scoring.get("stage_thresholds", {})
  return {
    'pre_debut': thresholds.get("pre_debut", 16),
    'early_stage': thresholds.get("early_stage", 24),
    'mid_stage': thresholds.get("mid_stage", 48)
  }

def get_hint_score_value(absolute_day):
  """Get hint score value based on day (supports hot reload)"""
  hint_config = get_scoring_config().get("hint_score", {})
  day_threshold = hint_config.get("day_threshold", 24)
  early_score = hint_config.get("early_stage", 1.0)
  late_score = hint_config.get("late_stage", 0.5)

  return early_score if absolute_day < day_threshold else late_score

def get_npc_score_value():
  """Get NPC base score value"""
  npc_config = get_scoring_config().get("npc_score", {})
  return npc_config.get("base_value", 0.5)

def get_support_base_score():
  """Get support card base score value"""
  support_config = get_scoring_config().get("support_score", {})
  return support_config.get("base_value", 1.0)

def get_friend_multiplier(training_type=None, current_date=None):
  """Get friend card score multiplier based on training type and stage"""
  support_config = get_scoring_config().get("support_score", {})
  friend_config = support_config.get("friend_multiplier", {})

  # If friend_multiplier is not a dict (old config format), return it directly
  if not isinstance(friend_config, dict):
    return friend_config

  # Check if we're in early stage (day < 24)
  is_early_stage = False
  if current_date:
    absolute_day = current_date.get('absolute_day', 0)
    thresholds = get_stage_thresholds()
    is_early_stage = absolute_day < thresholds['early_stage']

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
  support_config = get_scoring_config().get("support_score", {})
  rainbow_config = support_config.get("rainbow_multiplier", {})

  return rainbow_config.get(stage, 1.0)

def get_wit_score_requirement(energy_type, training_day):
  """Get WIT training score requirement"""
  wit_config = get_scoring_config().get("wit_training", {})
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
  wit_config = get_scoring_config().get("wit_training", {})
  return wit_config.get("early_stage_bonus", 0.25)

def get_energy_restriction_config():
  """Get energy restriction configuration"""
  scoring_config = get_scoring_config()
  energy_config = scoring_config.get("energy_restrictions", {})
  return {
    'medium_energy_shortage': energy_config.get("medium_energy_shortage", 50),
    'medium_energy_max_score_threshold': energy_config.get("medium_energy_max_score_threshold", 2.5)
  }

def get_stat_cap_penalty_config():
  """Get stat cap penalty configuration"""
  scoring_config = get_scoring_config()
  penalty_config = scoring_config.get("stat_cap_penalty", {})
  day_adjustments = penalty_config.get("day_cap_adjustments", {})
  return {
    'enabled': penalty_config.get("enabled", True),
    'max_penalty_percent': penalty_config.get("max_penalty_percent", 40),
    'start_penalty_percent': penalty_config.get("start_penalty_percent", 80),
    'start_penalty_gap': penalty_config.get("start_penalty_gap", 200),
    'day_75_adjustment': day_adjustments.get("day_75", 30),
    'day_74_adjustment': day_adjustments.get("day_74", 45),
    'day_73_and_below_adjustment': day_adjustments.get("day_73_and_below", 60)
  }


def get_effective_stat_cap(base_cap, absolute_day, penalty_config=None):
  """
  Calculate effective stat cap based on current day.

  Day-based adjustments:
  - Day 75: base_cap - 30
  - Day 74: base_cap - 45
  - Day <= 73: base_cap - 60

  Args:
    base_cap: The configured stat cap
    absolute_day: Current day in the career (1-75)
    penalty_config: Optional penalty config dict (will fetch if not provided)

  Returns:
    Effective stat cap after day adjustment
  """
  if penalty_config is None:
    penalty_config = get_stat_cap_penalty_config()

  if absolute_day >= 75:
    adjustment = penalty_config.get('day_75_adjustment', 30)
  elif absolute_day == 74:
    adjustment = penalty_config.get('day_74_adjustment', 45)
  else:  # day <= 73
    adjustment = penalty_config.get('day_73_and_below_adjustment', 60)

  return base_cap - adjustment


def get_all_effective_stat_caps(absolute_day, penalty_config=None):
  """
  Get all effective stat caps for the current day.

  Args:
    absolute_day: Current day in the career (1-75)
    penalty_config: Optional penalty config dict

  Returns:
    Dictionary of effective stat caps {spd, sta, pwr, guts, wit}
  """
  if penalty_config is None:
    penalty_config = get_stat_cap_penalty_config()

  base_caps = get_stat_caps()
  effective_caps = {}

  for stat, base_cap in base_caps.items():
    effective_caps[stat] = get_effective_stat_cap(base_cap, absolute_day, penalty_config)

  return effective_caps

# Secondary stat gains from training
# Training stat X also gives a % of gains to stat Y
TRAINING_SECONDARY_STATS = {
  'spd':  [('pwr', 0.3)],
  'sta':  [('guts', 0.3)],
  'pwr':  [('sta', 0.3)],
  'guts': [('spd', 0.2), ('pwr', 0.2)],
  'wit':  [('spd', 0.15)],
}

def _calculate_single_stat_penalty(current_stat, effective_cap, penalty_config):
  """
  Calculate penalty percentage for a single stat approaching its effective cap.

  Uses hybrid trigger: penalty starts when EITHER condition is met:
  - Stat reaches start_penalty_percent of effective cap (e.g., 80%)
  - Stat is within start_penalty_gap of effective cap (e.g., 200 points)

  Formula:
  1. trigger_by_percent = effective_cap * (start_penalty_percent / 100)
  2. trigger_by_gap = effective_cap - start_penalty_gap
  3. actual_trigger = MIN(trigger_by_percent, trigger_by_gap)
  4. fill_factor = (current_stat - actual_trigger) / (effective_cap - actual_trigger)
  5. penalty = fill_factor² * max_penalty_percent

  Args:
    current_stat: Current stat value
    effective_cap: Effective stat cap (already adjusted for day)
    penalty_config: Penalty configuration dict

  Returns: penalty_percent (0 to max_penalty_percent)
  """
  max_penalty_percent = penalty_config['max_penalty_percent']
  start_penalty_percent = penalty_config['start_penalty_percent']
  start_penalty_gap = penalty_config['start_penalty_gap']

  # If already at or above effective cap, return max penalty
  if current_stat >= effective_cap:
    return max_penalty_percent

  # Calculate both trigger points
  trigger_by_percent = effective_cap * (start_penalty_percent / 100)
  trigger_by_gap = effective_cap - start_penalty_gap

  # Use the trigger that activates first (lower value)
  actual_trigger = min(trigger_by_percent, trigger_by_gap)

  # Below trigger threshold: no penalty
  if current_stat < actual_trigger:
    return 0.0

  # Avoid division by zero
  if effective_cap <= actual_trigger:
    return max_penalty_percent

  # Calculate fill factor (0 at trigger, 1 at cap)
  fill_factor = (current_stat - actual_trigger) / (effective_cap - actual_trigger)

  # Quadratic scaling: penalty increases faster as stat approaches cap
  penalty_percent = (fill_factor ** 2) * max_penalty_percent

  return min(max_penalty_percent, max(0, penalty_percent))

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

  # Define stages with configurable thresholds (supports hot reload)
  thresholds = get_stage_thresholds()
  pre_debut_threshold = thresholds['pre_debut']
  early_threshold = thresholds['early_stage']
  mid_threshold = thresholds['mid_stage']

  is_pre_debut = absolute_day <= pre_debut_threshold

  if absolute_day <= early_threshold:
    stage = 'early'
  elif absolute_day <= mid_threshold:
    stage = 'mid'
  else:
    stage = 'late'

  return {
    'is_pre_debut': is_pre_debut,
    'stage': stage,
    'absolute_day': absolute_day,
    'should_apply_strategy': absolute_day > pre_debut_threshold
  }

def get_stat_priority(stat_key: str) -> int:
  """Get priority index of stat from config (supports hot reload)"""
  priority_stat = get_priority_stat()
  return priority_stat.index(stat_key) if stat_key in priority_stat else 999

def get_priority_by_stage(stat_key, current_date):
  """Get stat priority based on career stage (supports hot reload)"""
  stage_info = get_career_stage_info(current_date)

  # Use normal priority from config for all stages
  priority_stat = get_priority_stat()
  if stat_key in priority_stat:
    priority_index = priority_stat.index(stat_key)
    return priority_index
  else:
    return 999

def filter_by_stat_caps(results, current_stats, current_date=None):
  """Filter training results by effective stat caps, only applies after configured threshold day"""

  penalty_config = get_stat_cap_penalty_config()
  if not penalty_config['enabled']:
    return results

  # Check if stat cap filtering should be applied based on date
  if current_date:
    absolute_day = current_date.get('absolute_day', 0)
    stat_cap_threshold_day = get_config().get("stat_cap_threshold_day", 30)

    # Get effective stat caps (adjusted for current day)
    effective_caps = get_all_effective_stat_caps(absolute_day, penalty_config)
    base_caps = get_stat_caps()

    # Print current stats when reaching threshold day for the first time
    # Also print for days 73, 74, 75 to show effective cap changes
    if absolute_day == stat_cap_threshold_day or absolute_day in [73, 74, 75]:
      print(f"[STAT CAPS] Day {absolute_day} - Current stats vs effective caps:")
      for stat in ["spd", "sta", "pwr", "guts", "wit"]:
        current_value = current_stats.get(stat, 0)
        base_cap = base_caps.get(stat, 1200)
        effective_cap = effective_caps.get(stat, 1200)
        status = "CAPPED" if current_value >= effective_cap else "OK"
        if base_cap != effective_cap:
          print(f"[STAT CAPS]   {stat.upper()}: {current_value}/{effective_cap} (base: {base_cap}, adj: -{base_cap - effective_cap}) ({status})")
        else:
          print(f"[STAT CAPS]   {stat.upper()}: {current_value}/{effective_cap} ({status})")

    # Apply stat cap filtering for days >= threshold using effective caps
    filtered_results = {}
    for stat, data in results.items():
      current_value = current_stats.get(stat, 0)
      effective_cap = effective_caps.get(stat, 1200)

      if current_value < effective_cap:
        filtered_results[stat] = data
      else:
        print(f"[STAT CAPS] Filtered out {stat.upper()} training: {current_value}/{effective_cap} (capped)")

    return filtered_results
  else:
    # If no current_date provided, return all results without filtering
    return results

def apply_single_training_penalty(stat_key, data, current_date, current_stats=None):
  """
  Apply stat cap penalty to a single training result.
  Uses effective stat caps (adjusted for current day).
  Considers cross-training: training X also gives gains to secondary stats.
  If both primary and secondary stats have penalty, only the larger one applies.
  Mutates data dict in-place. Returns True if penalty was applied.
  """
  if not current_date:
    return False

  penalty_config = get_stat_cap_penalty_config()
  if not penalty_config['enabled']:
    return False

  absolute_day = current_date.get('absolute_day', 0)
  stat_cap_threshold_day = get_config().get("stat_cap_threshold_day", 30)

  if absolute_day < stat_cap_threshold_day:
    return False

  if current_stats is None:
    current_stats = stat_state()

  # Get effective stat caps (adjusted for current day)
  effective_caps = get_all_effective_stat_caps(absolute_day, penalty_config)
  base_caps = get_stat_caps()

  # Primary penalty
  current_stat = current_stats.get(stat_key, 0)
  effective_cap = effective_caps.get(stat_key, 1200)
  base_cap = base_caps.get(stat_key, 1200)

  # Calculate trigger point for debug
  trigger_by_percent = effective_cap * (penalty_config['start_penalty_percent'] / 100)
  trigger_by_gap = effective_cap - penalty_config['start_penalty_gap']
  actual_trigger = min(trigger_by_percent, trigger_by_gap)

  # Debug log: show stat vs effective cap for all training
  print(f"[CAP CHECK] {stat_key.upper()}: {current_stat}/{effective_cap} (trigger: {actual_trigger:.0f}, base: {base_cap})")

  primary_penalty_pct = _calculate_single_stat_penalty(
    current_stat, effective_cap, penalty_config
  )

  # Secondary penalties
  max_secondary_penalty_pct = 0
  secondary_source = ""
  for sec_stat, ratio in TRAINING_SECONDARY_STATS.get(stat_key, []):
    sec_current = current_stats.get(sec_stat, 0)
    sec_effective_cap = effective_caps.get(sec_stat, 1200)
    sec_penalty_pct = _calculate_single_stat_penalty(
      sec_current, sec_effective_cap, penalty_config
    )
    scaled_penalty = sec_penalty_pct * ratio
    if scaled_penalty > max_secondary_penalty_pct:
      max_secondary_penalty_pct = scaled_penalty
      secondary_source = f"{sec_stat.upper()} {sec_current}/{sec_effective_cap} x{ratio}"

  final_penalty_pct = max(primary_penalty_pct, max_secondary_penalty_pct)

  if final_penalty_pct > 0:
    multiplier = 1.0 - (final_penalty_pct / 100)
    original_score = data.get("total_score", 0)
    penalized_score = original_score * multiplier
    data["total_score"] = penalized_score
    data["cap_penalty_multiplier"] = multiplier
    data["original_score"] = original_score

    # Build penalty info string (show effective cap, and base cap if different)
    if primary_penalty_pct >= max_secondary_penalty_pct:
      if base_cap != effective_cap:
        penalty_info = f" - Cap penalty: -{final_penalty_pct:.1f}% ({current_stat}/{effective_cap}, base:{base_cap})"
      else:
        penalty_info = f" - Cap penalty: -{final_penalty_pct:.1f}% ({current_stat}/{effective_cap})"
    else:
      penalty_info = f" - Cap penalty: -{final_penalty_pct:.1f}% (via {secondary_source})"
    data["cap_penalty_info"] = penalty_info

    print(f"[CAP PENALTY] {stat_key.upper()}: {original_score:.2f} -> {penalized_score:.2f} ({penalty_info.strip()})")
    return True

  return False

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
    thresholds = get_stage_thresholds()
    if absolute_day < thresholds['early_stage']:
      bonus = get_wit_early_stage_bonus()
      wit_bonus_info = f" + Early WIT bonus ({bonus})"

  # Add cap penalty info if present
  cap_penalty_info = training_data.get("cap_penalty_info", "")
  original_score = training_data.get("original_score")
  if original_score is not None and cap_penalty_info:
    score_display = f"{total_score:.2f} (was {original_score:.2f}{cap_penalty_info})"
  else:
    score_display = f"{total_score:.2f}" if isinstance(total_score, float) else str(total_score)

  if stage_info['is_pre_debut']:
    return f"(score: {score_display} - {support_count} supports{hint_info}{npc_info}{wit_bonus_info} - Pre-Debut: Score-based selection)"
  elif stage_info['stage'] == 'early':
    return f"(score: {score_display} - {support_count} supports{hint_info}{npc_info}{wit_bonus_info} - Early Stage: Strategy applies, no rainbow bonus)"
  elif stage_info['stage'] == 'mid':
    rainbow_multiplier = get_rainbow_multiplier('mid_stage')
    return f"(score: {score_display} - {support_count} supports{hint_info}{npc_info}{wit_bonus_info} - Mid Stage: {rainbow_multiplier}x rainbow bonus)"
  else:
    rainbow_multiplier = get_rainbow_multiplier('late_stage')
    return f"(score: {score_display} - {support_count} supports{hint_info}{npc_info}{wit_bonus_info} - Late Stage: {rainbow_multiplier}x rainbow bonus)"

def extract_score_threshold(priority_strategy):
  """Extract score threshold from priority strategy string"""
  if "G1" in priority_strategy:
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

def training_decision(results_training, energy_percentage, energy_max, strategy_settings, current_date, current_stats=None):
  """Enhanced training decision with unified scoring system"""
  print(f"[DEBUG] === training_decision CALLED ===")
  print(f"[DEBUG] Energy: {energy_percentage}%, Strategy: {strategy_settings.get('priority_strategy', 'Unknown')}")

  if not results_training:
    print(f"[DEBUG] No training results provided")
    return None

  stage_info = get_career_stage_info(current_date)
  print(f"[DEBUG] Stage info: {stage_info}")

  absolute_day = current_date.get('absolute_day', 0)
  current_config = get_config()
  stat_cap_threshold_day = current_config.get("stat_cap_threshold_day", 60)
  filtered_results = results_training

  # Never apply stat cap filtering before threshold day
  if absolute_day >= stat_cap_threshold_day:
    # Get current stats for caps filtering (read once, reuse)
    if current_stats is None:
      current_stats = stat_state()
    print(f'Stat: {current_stats}')
    # Filter by stat caps (remove completely capped stats)
    filtered_results = filter_by_stat_caps(results_training, current_stats, current_date)
    if not filtered_results:
      print(f"[DEBUG] All training filtered out by stat caps")
      return None

  # Check energy level for critical energy (no training allowed)
  critical_energy = get_critical_energy()
  minimum_energy = get_minimum_energy()

  if energy_percentage < critical_energy:
    print(f"[DEBUG] Critical energy ({energy_percentage}% < {critical_energy}%), no training allowed")
    return None

  # Check energy level for medium energy logic (between critical and minimum)
  if energy_percentage < minimum_energy and energy_percentage >= critical_energy:
    print(f"[DEBUG] Medium energy ({energy_percentage}%), checking WIT only")
    return medium_energy_wit_training(filtered_results, current_date)

  # Mid-game energy restriction for low score training (only after early stage) - using config
  if stage_info['stage'] in ['mid', 'late']:
    energy_restrictions = get_energy_restriction_config()
    medium_energy_shortage = energy_restrictions['medium_energy_shortage']
    max_score_threshold = energy_restrictions['medium_energy_max_score_threshold']

    # Check if in summer period (July-August) after day 24
    if current_date:
      month_num = current_date.get('month_num', 0)
      absolute_day = current_date.get('absolute_day', 0)
      is_summer = (month_num == 7 or month_num == 8) and absolute_day > 24

      if is_summer:
        medium_energy_shortage = 40
  else:
    medium_energy_shortage = 48
    max_score_threshold = 1.15

  energy_shortage_absolute = energy_max - energy_percentage
  print(f' energy_shortage_absolute: {energy_max} - {energy_percentage}')

  stage = stage_info['stage']
  print(f'{stage} - e: {energy_shortage_absolute} - {medium_energy_shortage}')
  if (energy_shortage_absolute >= medium_energy_shortage):
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

def fallback_training(results, current_date, current_stats=None):
  """Enhanced fallback training using original scores without artificial bonuses.
  Note: Penalty is already applied by training_decision on the same results dict,
  so we only filter by stat caps here (no double-penalty).
  """
  if not results:
    return None

  # Apply filter by stat caps if on or after threshold day
  absolute_day = current_date.get('absolute_day', 0)
  stat_cap_threshold_day = get_config().get("stat_cap_threshold_day", 60)

  if absolute_day >= stat_cap_threshold_day:
    if current_stats is None:
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
  # Round score to avoid floating point precision issues (consistent with unified_training_selection)
  training_list.sort(key=lambda x: (-round(x[2], 6), x[3]))

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

  # Check if energy is critical (supports hot reload)
  critical_energy = get_critical_energy()
  minimum_energy = get_minimum_energy()

  if energy_percentage < critical_energy:
    return None

  # Check if energy is medium (between critical and minimum)
  if energy_percentage < minimum_energy:
    return medium_energy_wit_training(filtered, current_date)

  # Normal energy logic with unified strategy system
  # Check priority strategy type
  score_threshold = extract_score_threshold(priority_strategy)

  if score_threshold is None:
    # G1 strategy - prioritize racing, no training
    return None
  else:
    # Unified training strategy for all stages
    result = unified_training_selection(filtered, current_date, score_threshold)
    if result:
      return result[0]  # Return only the training key
    return None