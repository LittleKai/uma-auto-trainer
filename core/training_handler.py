import pyautogui
import time
from typing import Dict, Optional, Callable, Any

from core.state import check_support_card, get_current_date_info
from core.click_handler import enhanced_click, random_click_in_region, triple_click_random
from utils.constants import MINIMUM_ENERGY_PERCENTAGE, CRITICAL_ENERGY_PERCENTAGE

class TrainingHandler:
    """Handles all training-related operations with corrected stage definitions"""

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

    def check_training_support_stable(self, training_type: str, max_retries: int = 3) -> Optional[Dict]:
        """
        Check training support with stability verification and correct stage definitions
        """
        if self.check_stop():
            return None

        # Get current date info to check stage with corrected definitions
        current_date = get_current_date_info()
        absolute_day = current_date.get('absolute_day', 0) if current_date else 0

        # Updated stage logic: Pre-Debut is days 1-16
        is_pre_debut = absolute_day <= 16

        # First check
        support_counts = check_support_card(
            is_pre_debut=is_pre_debut,
            training_type=training_type,
            current_date=current_date
        )

        # Get total_score from check_support_card (already calculated with grouped NPC support)
        total_score = support_counts.get("total_score", 0)
        total_support = sum(count for key, count in support_counts.items()
                            if key not in ["hint", "hint_score", "total_score", "npc_count", "npc_score"])

        first_result = {
            'support': {k: v for k, v in support_counts.items()
                        if k not in ["hint", "hint_score", "total_score", "npc_count", "npc_score"]},
            'total_support': total_support,
            'hint_count': support_counts.get("hint", 0),
            'hint_score': support_counts.get("hint_score", 0),
            'npc_count': support_counts.get("npc_count", 0),
            'npc_score': support_counts.get("npc_score", 0),
            'total_score': total_score
        }

        # If total support <= 6, return immediately (no need for multiple checks)
        if total_support <= 6:
            return first_result

        # If total support > 6, perform additional checks for stability
        self.log(f"[{training_type.upper()}] High support count ({total_support}), performing additional checks for accuracy...")

        support_results = [first_result]

        for attempt in range(1, max_retries):
            if self.check_stop():
                return first_result

            # Small delay between checks for stability
            time.sleep(0.1)

            support_counts = check_support_card(
                is_pre_debut=is_pre_debut,
                training_type=training_type,
                current_date=current_date
            )
            total_score = support_counts.get("total_score", 0)
            total_support = sum(count for key, count in support_counts.items()
                                if key not in ["hint", "hint_score", "total_score", "npc_count", "npc_score"])

            support_results.append({
                'support': {k: v for k, v in support_counts.items()
                            if k not in ["hint", "hint_score", "total_score", "npc_count", "npc_score"]},
                'total_support': total_support,
                'hint_count': support_counts.get("hint", 0),
                'hint_score': support_counts.get("hint_score", 0),
                'npc_count': support_counts.get("npc_count", 0),
                'npc_score': support_counts.get("npc_score", 0),
                'total_score': total_score
            })

        # Use the result with median total score
        support_results.sort(key=lambda x: x['total_score'])
        median_index = len(support_results) // 2
        result = support_results[median_index]

        # Enhanced logging with hint and grouped NPC information
        hint_info = f" + {result['hint_count']} hints ({result['hint_score']} score)" if result['hint_count'] > 0 else ""
        npc_info = f" + {result['npc_count']} NPCs ({result['npc_score']} score)" if result['npc_count'] > 0 else ""

        self.log(f"[{training_type.upper()}] Multiple checks completed, using median result: "
                 f"{result['support']} (total: {result['total_support']}{hint_info}{npc_info}, "
                 f"final score: {result['total_score']})")

        return result

    def check_all_training(self, energy_percentage: float = 100) -> Dict[str, Any]:
        """
        Check all available training options with corrected stage definitions
        """
        if self.check_stop():
            return {}

        if not self.check_window():
            return {}

        # Check stage with corrected definitions
        current_date = get_current_date_info()
        absolute_day = current_date.get('absolute_day', 0) if current_date else 0
        is_pre_debut = absolute_day <= 16  # Pre-Debut: Days 1-16

        # Define which training types to check based on energy level
        if energy_percentage < CRITICAL_ENERGY_PERCENTAGE:
            # Critical energy: no training check at all
            self.log(f"Critical energy ({energy_percentage}%), skipping all training checks")
            return {}
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

        # Execute mouse handling logic for each training type
        for key, icon_path in training_types.items():
            if self.check_stop():
                break

            pos = pyautogui.locateCenterOnScreen(icon_path, confidence=0.8)
            if pos:
                pyautogui.moveTo(pos, duration=0.1)
                pyautogui.mouseDown()

                # Use improved support checking with stability verification and hint detection
                training_result = self.check_training_support_stable(key)

                if training_result is None:  # Could be due to stop flag
                    pyautogui.mouseUp()
                    break

                results[key] = training_result

                # Enhanced logging with correct stage information
                self._log_training_result(key, training_result, energy_percentage, is_pre_debut)
                time.sleep(0.1)

        # Move mouse to specific position before releasing if only one training type to avoid accidental clicks
        if len(training_types) == 1:
            current_x, current_y = pyautogui.position()
            pyautogui.moveTo(current_x, current_y-100, duration=0.1)

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

        return results

    def _log_training_result(self, key: str, training_result: Dict, energy_percentage: float, is_pre_debut: bool) -> None:
        """Log training result with detailed information and correct stage info"""
        hint_info = ""
        if training_result.get('hint_count', 0) > 0:
            hint_info = f" + {training_result['hint_count']} hints ({training_result['hint_score']} score)"

        npc_info = ""
        if training_result.get('npc_count', 0) > 0:
            npc_info = f" + {training_result['npc_count']} NPCs ({training_result['npc_score']} score)"

        # Enhanced stage info
        if is_pre_debut:
            self.log(f"[{key.upper()}] → {training_result['support']} (score: {training_result['total_score']}{hint_info}{npc_info}) (Pre-Debut)")
        else:
            self.log(f"[{key.upper()}] → {training_result['support']} (score: {training_result['total_score']}{hint_info}{npc_info})")

    def execute_training(self, training_type: str) -> bool:
        """
        Execute the specified training with triple click logic
        """
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

    def get_training_energy_requirements(self, training_type: str, current_date: Optional[Dict] = None) -> Dict[str, float]:
        """
        Get energy requirements for different training scenarios with corrected stage definitions
        """
        absolute_day = current_date.get('absolute_day', 0) if current_date else 0
        is_pre_debut = absolute_day <= 16  # Pre-Debut: Days 1-16

        if training_type == "wit" and current_date:
            # Medium energy WIT requirements
            if is_pre_debut:
                return {
                    'critical_threshold': CRITICAL_ENERGY_PERCENTAGE,
                    'medium_threshold': MINIMUM_ENERGY_PERCENTAGE,
                    'medium_score_required': 2.0,
                    'normal_score_required': 2.5
                }
            else:
                return {
                    'critical_threshold': CRITICAL_ENERGY_PERCENTAGE,
                    'medium_threshold': MINIMUM_ENERGY_PERCENTAGE,
                    'medium_score_required': 3.0,
                    'normal_score_required': 2.5
                }

        # Default requirements for other training types
        return {
            'critical_threshold': CRITICAL_ENERGY_PERCENTAGE,
            'medium_threshold': MINIMUM_ENERGY_PERCENTAGE,
            'medium_score_required': 0,  # Not available in medium energy
            'normal_score_required': 2.5
        }