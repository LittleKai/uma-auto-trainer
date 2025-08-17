import pyautogui
import time
from typing import Callable, Optional, List, Tuple

from core.click_handler import enhanced_click, random_click_in_region
from core.state import get_current_date_info

class RestHandler:
    """Handles rest and recreation operations"""

    def __init__(self, check_stop_func: Callable, check_window_func: Callable, log_func: Callable):
        """
        Initialize rest handler

        Args:
            check_stop_func: Function to check if should stop
            check_window_func: Function to check if game window is active
            log_func: Function to log messages
        """
        self.check_stop = check_stop_func
        self.check_window = check_window_func
        self.log = log_func

    def execute_rest(self) -> bool:
        """
        Execute rest action with seasonal handling

        Returns:
            bool: True if rest was executed successfully
        """
        if self.check_stop():
            self.log("[STOP] Rest cancelled due to F3 press")
            return False

        if not self.check_window():
            self.log("[WARNING] Game window not active, cannot rest")
            return False

        # Get current date to check if in summer period
        current_date = get_current_date_info()
        is_summer = self._is_summer_period(current_date)

        # Try to find rest buttons
        rest_attempts = self._get_rest_button_attempts()

        for button_path, button_name in rest_attempts:
            if self.check_stop():
                return False

            btn_region = pyautogui.locateOnScreen(button_path, confidence=0.8, minSearchTime=1.0)

            if btn_region:
                if self.check_stop():
                    return False

                # Random click within the button region
                random_click_in_region(btn_region.left, btn_region.top,
                                       btn_region.width, btn_region.height, duration=0.15)

                # Handle summer vacation dialog if needed
                if is_summer and "rest" in button_path:
                    self._handle_summer_vacation()

                return True
            else:
                self.log(f"[DEBUG] {button_name} not found")

        # If all buttons failed, try diagnostic
        self._handle_rest_failure()
        return False

    def execute_recreation(self) -> bool:
        """
        Execute recreation action

        Returns:
            bool: True if recreation was executed successfully
        """
        if self.check_stop():
            self.log("[STOP] Recreation cancelled due to F3 press")
            return False

        if not self.check_window():
            self.log("[WARNING] Game window not active, cannot do recreation")
            return False

        recreation_attempts = self._get_recreation_button_attempts()

        for button_path, button_name in recreation_attempts:
            if self.check_stop():
                return False

            btn_region = pyautogui.locateOnScreen(button_path, confidence=0.8, minSearchTime=1.0)

            if btn_region:
                if self.check_stop():
                    return False

                # Random click within the button region
                random_click_in_region(btn_region.left, btn_region.top,
                                       btn_region.width, btn_region.height, duration=0.15)
                return True
            else:
                self.log(f"[DEBUG] {button_name} not found")

        self.log("[ERROR] All recreation attempts failed")
        return False

    def handle_critical_energy_rest(self) -> bool:
        """
        Handle resting when critical energy after failed race attempt

        Returns:
            bool: True if critical energy rest was handled successfully
        """
        if self.check_stop():
            return False

        self.log("[INFO] Critical energy - attempting to rest after failed race")

        # First ensure we're at main menu
        if not self._ensure_main_menu():
            self.log("[ERROR] Could not return to main menu")
            return False

        # Try to rest
        if self.execute_rest():
            self.log("[SUCCESS] Critical energy - Successfully rested")
            return True
        else:
            self.log("[WARNING] Rest failed, trying recreation as fallback")
            if self.execute_recreation():
                self.log("[SUCCESS] Critical energy - Used recreation as fallback")
                return True
            else:
                self.log("[ERROR] Both rest and recreation failed")
                return False

    def _is_summer_period(self, current_date: Optional[dict]) -> bool:
        """Check if current date is in summer period (July-August)"""
        if not current_date:
            return False

        month_num = current_date.get('month_num', 0)
        return month_num == 7 or month_num == 8

    def _get_rest_button_attempts(self) -> List[Tuple[str, str]]:
        """Get list of rest buttons to try in order"""
        return [
            ("assets/buttons/rest_btn.png", "Regular rest button"),
            ("assets/buttons/rest_summer_btn.png", "Summer rest button"),
            ("assets/buttons/recreation_btn.png", "Recreation button (fallback)")
        ]

    def _get_recreation_button_attempts(self) -> List[Tuple[str, str]]:
        """Get list of recreation buttons to try in order"""
        return [
            ("assets/buttons/recreation_btn.png", "Recreation button"),
            ("assets/buttons/rest_summer_btn.png", "Summer recreation button")
        ]

    def _handle_summer_vacation(self) -> None:
        """Handle summer vacation dialog if it appears"""
        self.log("[INFO] Summer period - waiting for vacation dialog")
        time.sleep(0.8)  # Wait for dialog to appear

        # Try to click OK button for vacation confirmation
        ok_found = False
        for attempt in range(3):
            if self.check_stop():
                return

            if enhanced_click(
                    "assets/buttons/ok_btn.png",
                    minSearch=0.5,
                    text="Summer vacation - clicking OK",
                    check_stop_func=self.check_stop,
                    check_window_func=self.check_window,
                    log_func=self.log
            ):
                ok_found = True
                break
            time.sleep(0.3)

        if not ok_found:
            self.log("[WARNING] Summer vacation dialog OK button not found")

    def _handle_rest_failure(self) -> None:
        """Handle case when all rest buttons fail"""
        self.log("[WARNING] All rest buttons failed")
        self.log("[ERROR] All rest attempts failed")

    def _ensure_main_menu(self) -> bool:
        """
        Ensure we're at the main career lobby menu

        Returns:
            bool: True if at main menu
        """
        if self.check_stop():
            return False

        if not self.check_window():
            return False

        max_attempts = 5
        for attempt in range(max_attempts):
            if self.check_stop():
                return False

            # Check if we're already at main menu by looking for tazuna hint
            tazuna_hint = pyautogui.locateCenterOnScreen("assets/ui/tazuna_hint.png",
                                                         confidence=0.8, minSearchTime=0.3)

            if tazuna_hint:
                self.log(f"[INFO] At main menu (attempt {attempt + 1})")
                return True

            # If not at main menu, try to go back
            self.log(f"[DEBUG] Not at main menu, clicking back button (attempt {attempt + 1})")

            # Try different back buttons
            back_buttons = [
                "assets/buttons/back_btn.png",
                "assets/buttons/cancel_btn.png"
            ]

            back_clicked = False
            for back_btn in back_buttons:
                if self.check_stop():
                    return False

                if enhanced_click(
                        back_btn,
                        minSearch=0.3,
                        check_stop_func=self.check_stop,
                        check_window_func=self.check_window,
                        log_func=self.log
                ):
                    back_clicked = True
                    break

            if back_clicked:
                time.sleep(0.5)  # Wait for UI transition
            else:
                # If no back button found, try pressing ESC key
                self.log(f"[DEBUG] No back button found, trying ESC key")
                if not self.check_stop():
                    pyautogui.press('esc')
                    time.sleep(0.5)

        self.log(f"[ERROR] Failed to reach main menu after {max_attempts} attempts")
        return False

    def get_rest_recommendation(self, energy_percentage: float, mood: str, current_date: Optional[dict] = None) -> dict:
        """
        Get rest/recreation recommendation based on current state with corrected stage definitions
        """
        from utils.constants import CRITICAL_ENERGY_PERCENTAGE, MINIMUM_ENERGY_PERCENTAGE

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
            # Check if in periods where recreation should be skipped with corrected definitions
            absolute_day = current_date.get('absolute_day', 0) if current_date else 0
            is_pre_debut = absolute_day <= 16  # Pre-Debut: Days 1-16 (corrected)
            is_junior_year = current_date and current_date.get('year') == 'Junior'

            if is_pre_debut or is_junior_year:
                return {
                    'action': 'skip',
                    'priority': 'low',
                    'reason': f'Poor mood ({mood}) but in restricted period (Pre-Debut: Days 1-16)',
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