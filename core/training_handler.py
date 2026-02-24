import pyautogui
import time
import json
from typing import Dict, Optional, Callable, Any

from core.state import check_support_card, get_current_date_info, get_stage_thresholds, stat_state
from core.click_handler import enhanced_click, random_click_in_region, triple_click_random
from utils.constants import MINIMUM_ENERGY_PERCENTAGE, CRITICAL_ENERGY_PERCENTAGE


def load_scoring_config():
    """Load scoring configuration from config file"""
    try:
        with open("config.json", "r", encoding="utf-8") as file:
            config = json.load(file)
        return config.get("scoring_config", {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


class TrainingHandler:
    """Handles all training-related operations with unified score calculation"""

    def __init__(self, check_stop_func: Callable, check_window_func: Callable, log_func: Callable):
        """
        Initialize training handler

        Args:
            check_stop_func: Function to check if should stop
            check_window_func: Function to check if game window is active
            log_func: Function to log messages
        """
        self.check_stop = check_stop_func
        self.check_window = check_window_func
        self.log = log_func

    def go_to_training(self) -> bool:
        """Navigate to training menu"""
        if self.check_stop():
            self.log("[STOP] Training cancelled due to F3 press")
            return False

        return enhanced_click(
            "assets/buttons/training_btn.png",
            check_stop_func=self.check_stop,
            check_window_func=self.check_window,
            log_func=self.log
        )

    def check_training_support_stable(self, training_type: str, energy_shortage: float, max_retries: int = 3) -> \
    Optional[
        Dict]:
        """Check training support with stability verification and unified score calculation"""
        if self.check_stop():
            return None

        current_date = get_current_date_info()
        absolute_day = current_date.get('absolute_day', 0) if current_date else 0

        stage_thresholds = get_stage_thresholds()
        is_pre_debut = absolute_day <= stage_thresholds.get("pre_debut", 16)

        support_counts = check_support_card(
            is_pre_debut=is_pre_debut,
            training_type=training_type,
            current_date=current_date, energy_shortage = energy_shortage
        )

        total_score = support_counts.get("total_score", 0)
        total_support = sum(count for key, count in support_counts.items()
                            if key not in ["hint", "hint_score", "total_score", "npc_count", "npc_score",
                                           "support_card_bonus", "special_training", "special_training_score",
                                           "spirit_explosion", "spirit_explosion_score"])

        _SUPPORT_EXCLUDE = ["hint", "hint_score", "total_score", "npc_count", "npc_score",
                            "support_card_bonus", "special_training", "special_training_score",
                            "spirit_explosion", "spirit_explosion_score", "energy_recovery_penalty"]
        first_result = {
            'support': {k: v for k, v in support_counts.items() if k not in _SUPPORT_EXCLUDE},
            'hint_count': support_counts.get("hint", 0),
            'hint_score': support_counts.get("hint_score", 0),
            'npc_count': support_counts.get("npc_count", 0),
            'npc_score': support_counts.get("npc_score", 0),
            'special_training_count': support_counts.get("special_training", 0),
            'special_training_score': support_counts.get("special_training_score", 0),
            'spirit_explosion_count': support_counts.get("spirit_explosion", 0),
            'spirit_explosion_score': support_counts.get("spirit_explosion_score", 0),
            'energy_recovery_penalty': support_counts.get("energy_recovery_penalty", 0),
            'total_score': total_score,
            'support_card_bonus': support_counts.get("support_card_bonus", 0)
        }

        if total_support <= 6:
            return first_result

        self.log(
            f"[{training_type.upper()}] High support count ({total_support}), performing additional checks for accuracy...")

        support_results = [first_result]

        for attempt in range(1, max_retries):
            if self.check_stop():
                return first_result

            time.sleep(0.1)

            support_counts = check_support_card(
                is_pre_debut=is_pre_debut,
                training_type=training_type,
                current_date=current_date
            )
            total_score = support_counts.get("total_score", 0)
            total_support = sum(count for key, count in support_counts.items()
                                if key not in ["hint", "hint_score", "total_score", "npc_count", "npc_score",
                                               "support_card_bonus", "special_training", "special_training_score",
                                               "spirit_explosion", "spirit_explosion_score"])

            support_results.append({
                'support': {k: v for k, v in support_counts.items() if k not in _SUPPORT_EXCLUDE},
                'hint_count': support_counts.get("hint", 0),
                'hint_score': support_counts.get("hint_score", 0),
                'npc_count': support_counts.get("npc_count", 0),
                'npc_score': support_counts.get("npc_score", 0),
                'special_training_count': support_counts.get("special_training", 0),
                'special_training_score': support_counts.get("special_training_score", 0),
                'spirit_explosion_count': support_counts.get("spirit_explosion", 0),
                'spirit_explosion_score': support_counts.get("spirit_explosion_score", 0),
                'energy_recovery_penalty': support_counts.get("energy_recovery_penalty", 0),
                'total_score': total_score,
                'support_card_bonus': support_counts.get("support_card_bonus", 0)
            })

        support_results.sort(key=lambda x: x['total_score'])
        median_index = len(support_results) // 2
        result = support_results[median_index]

        self.log(f"[{training_type.upper()}] Multiple checks completed, using median result: "
                 f"{result['support']} (final score: {result['total_score']})")

        return result

    def _log_training_result(self, key: str, data: Dict) -> None:
        """Log a single training result with penalty info inline."""
        bonus_components = []

        if data.get('support_card_bonus', 0) > 0:
            bonus_components.append(f"Support Bonus +{data['support_card_bonus']}")
        if data.get('hint_count', 0) > 0:
            bonus_components.append(f"hints +{data['hint_score']}")
        if data.get('npc_count', 0) > 0:
            bonus_components.append(f"NPCs +{data['npc_score']}")
        if data.get('special_training_count', 0) > 0:
            bonus_components.append(f"Special Training +{data['special_training_score']}")
        if data.get('spirit_explosion_count', 0) > 0:
            bonus_components.append(f"Spirit Explosion +{data['spirit_explosion_score']}")
        if data.get('energy_recovery_penalty', 0) > 0:
            bonus_components.append(f"Energy Excess -{round(data['energy_recovery_penalty'], 2)}")

        is_early_stage = False
        current_date = get_current_date_info()
        if current_date and key == "wit":
            stage_thresholds = get_stage_thresholds()
            absolute_day = current_date.get('absolute_day', 0)
            is_early_stage = absolute_day <= stage_thresholds.get("early_stage", 24)
            if is_early_stage:
                from core.logic import get_wit_early_stage_bonus
                bonus_components.append(f"early WIT +{get_wit_early_stage_bonus()}")

        total_score = round(data.get('total_score', 0), 2)

        # Build score display with penalty info inline (only show if >= 1% and score > 0)
        original_score = data.get("original_score")
        cap_penalty_info = data.get("cap_penalty_info", "")
        multiplier = data.get("cap_penalty_multiplier", 1.0)
        penalty_pct = (1.0 - multiplier) * 100
        if original_score is not None and cap_penalty_info and penalty_pct >= 1.0 and original_score > 0:
            score_display = f"{total_score} (was {round(original_score, 2)}{cap_penalty_info})"
        else:
            score_display = str(total_score)

        base_message = f"[{key.upper()}] → {data['support']} score: {score_display}"

        if bonus_components:
            base_message += " (" + ", ".join(bonus_components) + ")"
        if is_early_stage:
            base_message += " (Early-Stage)"

        self.log(base_message)

    def check_all_training(self, energy_percentage: float = 100, energy_max: float = 100):
        """Check all available training options with unified score calculation.
        Returns (results_dict, current_stats) tuple.
        """
        if self.check_stop():
            return {}, None

        if not self.check_window():
            return {}, None

        # Check stage with configurable definitions
        current_date = get_current_date_info()
        absolute_day = current_date.get('absolute_day', 0) if current_date else 0
        stage_thresholds = get_stage_thresholds()
        is_pre_debut = absolute_day <= stage_thresholds.get("pre_debut", 16)
        energy_shortage = energy_max - energy_percentage
        # Define which training types to check based on energy level
        if energy_percentage < CRITICAL_ENERGY_PERCENTAGE:
            # Critical energy: no training check at all
            self.log(f"Critical energy ({energy_percentage}%), skipping all training checks")
            return {}, None
        elif energy_percentage < MINIMUM_ENERGY_PERCENTAGE:
            # Low energy: only check WIT
            training_types = {
                "wit": "assets/icons/train_wit.png"
            }
            self.log(f"Low energy ({energy_percentage}%), only checking WIT training")
        else:
            # Normal energy: check all training types
            training_types = {
                "spd": "assets/icons/train_spd.png",
                "sta": "assets/icons/train_sta.png",
                "pwr": "assets/icons/train_pwr.png",
                "guts": "assets/icons/train_guts.png",
                "wit": "assets/icons/train_wit.png"
            }

        results = {}

        # Only read stats when needed for stat cap penalty (after threshold day)
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                stat_cap_threshold_day = json.load(f).get("stat_cap_threshold_day", 30)
        except Exception:
            stat_cap_threshold_day = 30
        if absolute_day >= stat_cap_threshold_day:
            # When only checking WIT, read only SPD and WIT stats
            wit_only = list(training_types.keys()) == ["wit"]
            current_stats = stat_state(stats_filter=['spd', 'wit'] if wit_only else None)
        else:
            current_stats = None

        # Execute mouse handling logic for each training type
        for key, icon_path in training_types.items():
            if self.check_stop():
                break

            pos = pyautogui.locateCenterOnScreen(icon_path, confidence=0.8)
            if pos:
                pyautogui.moveTo(pos, duration=0.1)
                pyautogui.mouseDown()

                # Use unified support checking with stability verification
                training_result = self.check_training_support_stable(key, energy_shortage=energy_shortage)

                if training_result is None:  # Could be due to stop flag
                    pyautogui.mouseUp()
                    break

                results[key] = training_result

                # Apply penalty and log immediately
                from core.logic import apply_single_training_penalty
                current_date = get_current_date_info()
                apply_single_training_penalty(key, training_result, current_date, current_stats=current_stats)
                self._log_training_result(key, training_result)
                time.sleep(0.1)

        # Move mouse to specific position before releasing if only one training type to avoid accidental clicks
        if len(training_types) == 1:
            current_x, current_y = pyautogui.position()
            pyautogui.moveTo(current_x, current_y - 100, duration=0.1)

        # Mouse release and back navigation
        pyautogui.mouseUp()
        if not self.check_stop():
            enhanced_click(
                "assets/buttons/back_btn.png",
                minSearch=1.0,
                check_stop_func=self.check_stop,
                check_window_func=self.check_window,
                log_func=self.log
            )

        return results, current_stats

    def execute_training(self, training_type: str) -> bool:
        """Execute the specified training with triple click logic"""
        if self.check_stop():
            self.log(f"[STOP] Training {training_type} cancelled due to F3 press")
            return False

        if not self.check_window():
            return False

        # Direct triple click logic
        train_btn = pyautogui.locateCenterOnScreen(f"assets/icons/train_{training_type}.png", confidence=0.8)
        if train_btn:
            if self.check_stop():
                return False
            pyautogui.tripleClick(train_btn, interval=0.1, duration=0.2)
            return True
        else:
            self.log(f"[ERROR] Could not find {training_type.upper()} training button")
            return False
