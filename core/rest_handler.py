import pyautogui
import time
import json
from typing import Callable, Optional, List, Tuple

from core.click_handler import enhanced_click, random_click_in_region
from core.state import get_current_date_info, get_stage_thresholds

def load_scoring_config():
    """Load scoring configuration from config file"""
    try:
        with open("config.json", "r", encoding="utf-8") as file:
            config = json.load(file)
        return config.get("scoring_config", {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

class RestHandler:
    """Handles rest and recreation operations with improved logic"""

    def __init__(self, check_stop_func: Callable, check_window_func: Callable, log_func: Callable):
        """
        Initialize rest handler with callback functions
        """
        self.check_stop = check_stop_func
        self.check_window = check_window_func
        self.log = log_func

    def execute_rest(self, strategy_context: Optional[str] = None) -> bool:
        """
        Execute rest action with strategy-aware logic

        Args:
            strategy_context: Optional context about current strategy (G1/G2/etc)
        """
        if self.check_stop():
            self.log("[STOP] Rest cancelled due to F3 press")
            return False

        if not self.check_window():
            self.log("[WARNING] Game window not active, cannot rest")
            return False

        # Get current date info
        current_date = get_current_date_info()
        is_summer = self._is_summer_period(current_date)

        # Determine rest strategy based on context
        avoid_summer_rest = self._should_avoid_summer_rest(strategy_context, is_summer)

        # Get rest button attempts based on strategy
        rest_attempts = self._get_rest_button_attempts(is_summer, avoid_summer_rest)

        # Try each rest button in order
        for button_path, button_name, button_type in rest_attempts:
            if self.check_stop():
                return False

            btn_region = pyautogui.locateOnScreen(button_path, confidence=0.8, minSearchTime=1.0)

            if btn_region:
                if self.check_stop():
                    return False

                # Execute click
                success = self._execute_rest_click(btn_region, button_name, button_type, is_summer)

                if success:
                    return True

        # All rest attempts failed
        self.log("[ERROR] All rest attempts failed")
        return False

    def execute_recreation(self) -> bool:
        """Execute recreation action"""
        if self.check_stop():
            self.log("[STOP] Recreation cancelled due to F3 press")
            return False

        if not self.check_window():
            self.log("[WARNING] Game window not active, cannot do recreation")
            return False

        # Get recreation button attempts
        recreation_attempts = self._get_recreation_button_attempts()

        for button_path, button_name in recreation_attempts:
            if self.check_stop():
                return False

            btn_region = pyautogui.locateOnScreen(button_path, confidence=0.8, minSearchTime=1.0)

            if btn_region:
                if self.check_stop():
                    return False

                # Random click within button region
                random_click_in_region(btn_region.left, btn_region.top,
                                       btn_region.width, btn_region.height, duration=0.15)

                return True

        self.log("[ERROR] All recreation attempts failed")
        return False

    def handle_critical_energy_rest(self, strategy_context: Optional[str] = None) -> bool:
        """Handle resting when critical energy after failed race attempt"""
        if self.check_stop():
            return False

        self.log("[INFO] Critical energy - attempting to rest after failed race")

        # Ensure we're at main menu first
        if not self._ensure_main_menu():
            self.log("[ERROR] Could not return to main menu")
            return False

        # Try to rest with strategy context
        if self.execute_rest(strategy_context):
            return True
        else:
            self.log("[WARNING] Rest failed, trying recreation as fallback")
            if self.execute_recreation():
                return True
            else:
                self.log("[ERROR] Both rest and recreation failed")
                return False

    def _should_avoid_summer_rest(self, strategy_context: Optional[str], is_summer: bool) -> bool:
        """Determine if should avoid summer rest button based on strategy"""
        if not is_summer:
            return False

        # For G1/G2 strategies, avoid summer rest to prevent training interruption
        if strategy_context and ("G1" in strategy_context or "G2" in strategy_context):
            self.log("[DEBUG] G1/G2 strategy detected - avoiding summer rest button")
            return True

        return False

    def _is_summer_period(self, current_date: Optional[dict]) -> bool:
        """Check if current date is in summer period (July-August)"""
        if not current_date:
            return False

        month_num = current_date.get('month_num', 0)
        return month_num == 7 or month_num == 8

    def _get_rest_button_attempts(self, is_summer: bool, avoid_summer_rest: bool) -> List[Tuple[str, str, str]]:
        """
        Get list of rest buttons to try in order

        Returns:
            List of (button_path, button_name, button_type) tuples
        """
        if is_summer and not avoid_summer_rest:
            # Summer period - try summer rest first if not avoiding it
            return [
                ("assets/buttons/rest_summer_btn.png", "Summer rest button", "summer_rest"),
                ("assets/buttons/rest_btn.png", "Regular rest button", "regular_rest"),
                ("assets/buttons/recreation_btn.png", "Recreation button (fallback)", "recreation")
            ]
        else:
            # Non-summer period or avoiding summer rest
            return [
                ("assets/buttons/rest_btn.png", "Regular rest button", "regular_rest"),
                ("assets/buttons/recreation_btn.png", "Recreation button (fallback)", "recreation")
            ]

    def _get_recreation_button_attempts(self) -> List[Tuple[str, str]]:
        """Get list of recreation buttons to try in order"""
        return [
            ("assets/buttons/recreation_btn.png", "Recreation button"),
            ("assets/buttons/rest_summer_btn.png", "Summer recreation button")
        ]

    def _execute_rest_click(self, btn_region, button_name: str, button_type: str, is_summer: bool) -> bool:
        """Execute rest button click with appropriate handling"""
        try:
            # Random click within button region
            random_click_in_region(btn_region.left, btn_region.top,
                                   btn_region.width, btn_region.height, duration=0.15)

            # Handle summer vacation dialog if needed
            if button_type == "regular_rest" and is_summer:
                self._handle_summer_vacation_dialog()
            elif button_type == "summer_rest":
                self._handle_summer_vacation_dialog()

            return True

        except Exception as e:
            self.log(f"[ERROR] Failed to click {button_name}: {e}")
            return False

    def _handle_summer_vacation_dialog(self) -> None:
        """Handle summer vacation dialog if it appears"""
        self.log("[DEBUG] Checking for summer vacation dialog")

        # Wait for potential dialog to appear
        time.sleep(0.8)

        # Try to click OK button for vacation confirmation
        for attempt in range(3):
            if self.check_stop():
                return

            if enhanced_click(
                    "assets/buttons/ok_btn.png",
                    minSearch=0.5,
                    text="Summer vacation dialog - clicking OK",
                    check_stop_func=self.check_stop,
                    check_window_func=self.check_window,
                    log_func=self.log
            ):
                break

            time.sleep(0.3)

    def _ensure_main_menu(self) -> bool:
        """Ensure we're at the main career lobby menu"""
        if self.check_stop():
            return False

        if not self.check_window():
            return False

        max_attempts = 5
        for attempt in range(max_attempts):
            if self.check_stop():
                return False

            # Check if we're already at main menu
            tazuna_hint = pyautogui.locateCenterOnScreen("assets/ui/tazuna_hint.png",
                                                         confidence=0.8, minSearchTime=0.3)

            if tazuna_hint:
                self.log(f"[INFO] At main menu (attempt {attempt + 1})")
                return True

            # Not at main menu - try to navigate back
            self.log(f"[DEBUG] Not at main menu, attempting to return (attempt {attempt + 1})")

            # Try back buttons
            back_buttons = [
                ("assets/buttons/back_btn.png", "Back button"),
                ("assets/buttons/cancel_btn.png", "Cancel button")
            ]

            back_clicked = False
            for back_btn, btn_name in back_buttons:
                if self.check_stop():
                    return False

                if enhanced_click(
                        back_btn,
                        minSearch=0.3,
                        text=f"Clicking {btn_name}",
                        check_stop_func=self.check_stop,
                        check_window_func=self.check_window,
                        log_func=self.log
                ):
                    back_clicked = True
                    break

            if back_clicked:
                time.sleep(0.5)  # Wait for UI transition
            else:
                # Try ESC key as fallback
                self.log("[DEBUG] No back button found, trying ESC key")
                if not self.check_stop():
                    pyautogui.press('esc')
                    time.sleep(0.5)

        self.log(f"[ERROR] Failed to reach main menu after {max_attempts} attempts")
        return False

    def get_rest_recommendation(self, energy_percentage: float, mood: str, current_date: Optional[dict] = None) -> dict:
        """Get rest/recreation recommendation based on current state"""
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            CRITICAL_ENERGY_PERCENTAGE = config.get('critical_energy_percentage', 20)
            MINIMUM_ENERGY_PERCENTAGE = config.get('minimum_energy_percentage', 40)
        except:
            CRITICAL_ENERGY_PERCENTAGE = 20
            MINIMUM_ENERGY_PERCENTAGE = 40

        # Energy-based recommendations
        if energy_percentage < CRITICAL_ENERGY_PERCENTAGE:
            return {
                'action': 'rest',
                'priority': 'critical',
                'reason': f'Critical energy ({energy_percentage}%)',
                'urgency': 'immediate'
            }
        elif energy_percentage < MINIMUM_ENERGY_PERCENTAGE:
            return {
                'action': 'rest',
                'priority': 'high',
                'reason': f'Low energy ({energy_percentage}%)',
                'urgency': 'recommended'
            }

        # Mood-based recommendations
        mood_priority = {
            'AWFUL': 'critical',
            'BAD': 'high',
            'NORMAL': 'low',
            'GOOD': 'none',
            'GREAT': 'none'
        }

        mood_level = mood_priority.get(mood, 'low')

        if mood_level in ['critical', 'high']:
            # Check if in restricted periods
            stage_thresholds = get_stage_thresholds()
            absolute_day = current_date.get('absolute_day', 0) if current_date else 0
            is_pre_debut = absolute_day <= stage_thresholds.get("pre_debut", 16)
            is_junior_year = current_date and current_date.get('year') == 'Junior'

            if is_pre_debut or is_junior_year:
                return {
                    'action': 'skip',
                    'priority': 'low',
                    'reason': f'Poor mood ({mood}) but in restricted period (Pre-Debut: Days 1-{stage_thresholds.get("pre_debut", 16)})',
                    'urgency': 'skip'
                }
            else:
                return {
                    'action': 'recreation',
                    'priority': mood_level,
                    'reason': f'Poor mood ({mood})',
                    'urgency': 'recommended'
                }

        return {
            'action': 'none',
            'priority': 'none',
            'reason': f'Good condition (Energy: {energy_percentage}%, Mood: {mood})',
            'urgency': 'none'
        }

    def get_strategy_aware_rest_action(self, energy_percentage: float, mood: str,
                                       current_date: Optional[dict] = None,
                                       strategy_context: Optional[str] = None) -> dict:
        """Get rest recommendation with strategy awareness"""
        base_recommendation = self.get_rest_recommendation(energy_percentage, mood, current_date)

        # Add strategy context to recommendation
        if strategy_context:
            base_recommendation['strategy_context'] = strategy_context

            # Special handling for G1/G2 strategies in summer
            if ("G1" in strategy_context or "G2" in strategy_context) and self._is_summer_period(current_date):
                base_recommendation['avoid_summer_rest'] = True
                base_recommendation['reason'] += f" ({strategy_context} - avoiding summer rest)"

        return base_recommendation