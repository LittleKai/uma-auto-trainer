import pyautogui
import time
from typing import Callable, Optional, Dict, List, Tuple
from core.recognizer import find_template_position

from core.click_handler import enhanced_click, random_click_in_region, move_to_random_position, random_screen_click
from utils.constants import RACE_REGION

class RaceHandler:
    """Handles all race-related operations with panel-based race detection"""

    def __init__(self, check_stop_func: Callable, check_window_func: Callable, log_func: Callable):
        """
        Initialize race handler

        Args:
            check_stop_func: Function to check if should stop
            check_window_func: Function to check if game window is active
            log_func: Function to log messages
        """
        self.check_stop = check_stop_func
        self.check_window = check_window_func
        self.log = log_func

    def start_race_flow(self, prioritize_g1: bool = False, prioritize_g2: bool = False,
                        allow_continuous_racing: bool = True) -> bool:
        """Start the complete race flow from lobby to finish"""
        if self.check_stop():
            self.log("[STOP] Race cancelled due to F3 press")
            return False

        if not self.check_window():
            return False

        # Click races button
        if not enhanced_click(
                "assets/buttons/races_btn.png",
                minSearch=10,
                check_stop_func=self.check_stop,
                check_window_func=self.check_window,
                log_func=self.log
        ):
            return False

        if self.check_stop():
            return False

        # Check for OK button (indicates more than 3 races recently)
        ok_btn_found = False
        if not self.check_stop():
            ok_btn_found = enhanced_click(
                "assets/buttons/ok_btn.png",
                minSearch=0.7,
                check_stop_func=self.check_stop,
                check_window_func=self.check_window,
                log_func=self.log
            )

        if ok_btn_found and not allow_continuous_racing:
            self.log("Continuous racing disabled - canceling race due to recent racing limit")
            if not self.check_stop():
                enhanced_click(
                    "assets/buttons/cancel_btn.png",
                    minSearch=0.2,
                    check_stop_func=self.check_stop,
                    check_window_func=self.check_window,
                    log_func=self.log
                )
            return False

        if self.check_stop():
            return False

        # Use new panel-based race selection
        race_found = self._select_race_by_panels()

        if not race_found or self.check_stop():
            return False

        # Continue with race preparation
        if not self.prepare_race() or self.check_stop():
            return False

        time.sleep(1)

        if not self.handle_after_race() or self.check_stop():
            return False

        return True

    def _select_race_by_panels(self) -> bool:
        """Select race using panel-based detection with grade priority"""

        # Get enabled grades from filters
        enabled_grades = self._get_enabled_grades()

        # Calculate panel dimensions (split race region into smaller panels)
        left, top, width, height = RACE_REGION
        panel_height = height // 2  # Split vertically into 2 panels
        scroll_amount = panel_height  # Scroll by one panel height


        for scroll_attempt in range(3):
            if self.check_stop():
                return False

            # Check both upper and lower panels
            panels = [
                (left, top, width, panel_height),  # Upper panel
                (left, top + panel_height, width, panel_height)  # Lower panel
            ]

            for panel_index, panel_region in enumerate(panels):
                if self.check_stop():
                    return False


                # Find matching race in this panel
                race_match = self._find_matching_race_in_panel(panel_region, enabled_grades)

                if race_match:
                    grade, match_pos = race_match

                    # Click on the match position
                    pyautogui.moveTo(match_pos, duration=0.2)
                    pyautogui.click()

                    # Click race buttons
                    return self._click_race_buttons_original()

            # Scroll down by panel height to see new races
            self.log(f"[DEBUG] Scrolling down by {scroll_amount} pixels (attempt {scroll_attempt + 1})")

            # Move mouse to center of race region before scrolling
            center_x = left + width // 2
            center_y = top + height // 2
            pyautogui.moveTo(center_x, center_y, duration=0.2)

            # Scroll in increments for better control
            scroll_increments = scroll_amount // 50  # 50px per scroll
            for i in range(scroll_increments):
                if self.check_stop():
                    return False
                pyautogui.scroll(-50)
                time.sleep(0.05)  # Small delay between scroll increments

            # Final delay after scrolling
            time.sleep(0.5)

        self.log("[DEBUG] No matching race found after all scroll attempts")
        return False

    def _find_matching_race_in_panel(self, panel_region: tuple, enabled_grades: list) -> Optional[Tuple[str, tuple]]:
        """
        Find a race with both grade indicator and match_track in the same panel
        Returns: (grade, match_position) or None
        Priority: G1 > G2 > G3
        """
        # Define grade priority order
        grade_priority = ['g1', 'g2', 'g3']

        # Only check grades that are enabled in filters
        enabled_priority_grades = [grade for grade in grade_priority if grade in enabled_grades]

        if not enabled_priority_grades:
            return None


        # Check each grade in priority order
        for grade in enabled_priority_grades:
            grade_matches = self._find_grade_and_match_track_pair(panel_region, grade)

            if grade_matches:
                # Return the first (highest priority) match found
                return (grade.upper(), grade_matches)

        return None

    def _find_grade_and_match_track_pair(self, panel_region: tuple, grade: str) -> Optional[tuple]:
        """
        Find single grade indicator + match_track pair in the same panel
        Returns: match_track position tuple (x, y) if both are found in the same race entry
        """
        try:
            # Find first grade indicator in this panel
            template_path = f"assets/ui/{grade}_race2.png"
            grade_location = find_template_position(
                template_path=template_path,
                region=panel_region,
                threshold=0.8,
                region_format='xywh'
            )

            if not grade_location:
                return None

            # Find first match_track indicator in this panel
            # Convert panel_region from (x, y, width, height) to (left, top, right, bottom)
            left, top, width, height = panel_region
            region_ltrb = (left, top, left + width, top + height)

            match_track_location = pyautogui.locateCenterOnScreen(
                "assets/ui/match_track.png",
                confidence=0.8,
                minSearchTime=0.3,
                region=region_ltrb
            )

            if not match_track_location:
                return None

            # Check if they are in the same race entry (vertically close)
            vertical_distance = abs(grade_location[1] - match_track_location.y)
            horizontal_distance = abs(grade_location[0] - match_track_location.x)

            if vertical_distance <= 50 and horizontal_distance <= 300:  # Same race entry
                # Return tuple coordinates instead of pyautogui object
                return (match_track_location.x, match_track_location.y)
            else:
                return None

        except Exception as e:
            self.log(f"[DEBUG] Error finding {grade.upper()} + match_track pair: {e}")
            return None

    def _get_enabled_grades(self) -> list:
        """Get list of enabled grade filters"""
        try:
            import json
            with open('bot_settings.json', 'r') as f:
                settings = json.load(f)
                filters = settings.get('grade', {})

            enabled_grades = [grade for grade, enabled in filters.items() if enabled]
            return enabled_grades
        except Exception as e:
            self.log(f"[DEBUG] Could not get grade filters, defaulting to all: {e}")
            return ['g1', 'g2', 'g3']

    def _click_race_buttons_original(self) -> bool:
        """Click race buttons to confirm selection"""
        for i in range(2):
            if self.check_stop():
                return False

            race_btn = pyautogui.locateCenterOnScreen(
                "assets/buttons/race_btn.png",
                confidence=0.8,
                minSearchTime=2
            )

            if race_btn:
                pyautogui.moveTo(race_btn, duration=0.2)
                pyautogui.click(race_btn)
                time.sleep(0.5)
            else:
                break

        return True

    def prepare_race(self) -> bool:
        """Prepare for race using original timing"""
        if self.check_stop():
            return False

        if not self.check_window():
            return False

        view_result_btn_region = pyautogui.locateOnScreen(
            "assets/buttons/view_results.png",
            confidence=0.8,
            minSearchTime=20
        )

        if view_result_btn_region:
            if self.check_stop():
                return False

            random_click_in_region(
                view_result_btn_region.left, view_result_btn_region.top,
                view_result_btn_region.width, view_result_btn_region.height
            )

            time.sleep(5)

            for i in range(3):
                if self.check_stop():
                    return False

                random_screen_click(offset_range=0)
                time.sleep(0.5)

        return True

    def handle_after_race(self) -> bool:
        """Handle post-race using original timing"""
        if self.check_stop():
            return False

        if not self.check_window():
            return False

        if not enhanced_click(
                "assets/buttons/next_btn.png",
                minSearch=5,
                check_stop_func=self.check_stop,
                check_window_func=self.check_window,
                log_func=self.log
        ):
            return False

        if self.check_stop():
            return False

        time.sleep(0.3)
        random_screen_click(offset_range=100)

        if self.check_stop():
            return False

        enhanced_click(
            "assets/buttons/next2_btn.png",
            minSearch=5,
            check_stop_func=self.check_stop,
            check_window_func=self.check_window,
            log_func=self.log
        )

        return True

    def handle_race_day(self) -> bool:
        """Handle race day using original timing"""
        if self.check_stop():
            self.log("[STOP] Race day cancelled due to F3 press")
            return False

        if not self.check_window():
            return False

        if not enhanced_click(
                "assets/buttons/race_day_btn.png",
                minSearch=10,
                check_stop_func=self.check_stop,
                check_window_func=self.check_window,
                log_func=self.log
        ):
            return False

        if self.check_stop():
            return False

        enhanced_click(
            "assets/buttons/ok_btn.png",
            minSearch=0.7,
            check_stop_func=self.check_stop,
            check_window_func=self.check_window,
            log_func=self.log
        )
        time.sleep(0.5)

        for i in range(2):
            if self.check_stop():
                return False

            if not enhanced_click(
                    "assets/buttons/race_btn.png",
                    minSearch=2,
                    check_stop_func=self.check_stop,
                    check_window_func=self.check_window,
                    log_func=self.log
            ):
                break
            time.sleep(0.5)

        if self.check_stop():
            return False

        if not self.prepare_race():
            return False

        time.sleep(1)

        if not self.handle_after_race():
            return False

        return True

    def handle_ura_finale(self) -> bool:
        """Handle URA finale using original timing"""
        if self.check_stop():
            return False

        self.log("URA Finale")

        try:
            from utils.scenario import ura
            ura()
        except ImportError:
            self.log("[WARNING] URA scenario not available")

        for i in range(2):
            if self.check_stop():
                return False

            if enhanced_click(
                    "assets/buttons/race_btn.png",
                    minSearch=2,
                    check_stop_func=self.check_stop,
                    check_window_func=self.check_window,
                    log_func=self.log
            ):
                time.sleep(0.5)

        if self.check_stop():
            return False

        self.prepare_race()
        time.sleep(1)
        self.handle_after_race()
        return True
