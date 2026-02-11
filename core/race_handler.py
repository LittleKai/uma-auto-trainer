import pyautogui
import time
from typing import Callable, Optional, Dict, List, Tuple, Any
from core.recognizer import find_template_position

from core.click_handler import find_and_click, random_click_in_region, random_screen_click
from utils.constants import RACE_REGION

# Style assets folder
STYLE_ASSETS_FOLDER = 'assets/buttons/style'


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

    def unity_race_flow(self):
        """Handle Unity Cup race flow with opponent selection and race execution"""
        # Step 1: Check and click opponent selection or race button
        if not find_and_click(
                "assets/buttons/unity_cup/select_opponent_btn.png", max_attempts=3, delay_between=2,
                check_stop_func=self.check_stop):
            if not find_and_click(
                    "assets/buttons/unity_cup/unity_cup_race_btn.png", max_attempts=1, delay_between=2,
                    check_stop_func=self.check_stop):
                return

        # If opponent selection found, click begin showdown
        if not find_and_click(
                "assets/buttons/unity_cup/bebin_showdown_btn.png", max_attempts=3, delay_between=2,
                check_stop_func=self.check_stop):
            return

        # Step 2: Click see all race results
        if not find_and_click(
                "assets/buttons/unity_cup/see_all_race_results_2.png", confidence=0.7, max_attempts=5, delay_between=3,
                check_stop_func=self.check_stop):
            print('fail check')
            return

        # Step 3: Click skip button
        if not find_and_click(
                "assets/buttons/skip_btn.png", max_attempts=3, delay_between=3, check_stop_func=self.check_stop):
            return

        # Step 4: Click next button
        if not find_and_click(
                "assets/buttons/next_btn.png", max_attempts=3, delay_between=2, check_stop_func=self.check_stop):
            return

        # Step 5: Click next2 button
        if not find_and_click(
                "assets/buttons/next2_btn.png", max_attempts=3, delay_between=2, check_stop_func=self.check_stop
        ):
            return

        # Step 6: Click next button
        if not find_and_click(
                "assets/buttons/next_btn.png", max_attempts=3, delay_between=2, check_stop_func=self.check_stop
        ):
            return

    def start_race_flow(self, prioritize_g1: bool = False, prioritize_g2: bool = False,
                        allow_continuous_racing: bool = True) -> bool:
        """Start the complete race flow from lobby to finish"""
        if self.check_stop():
            self.log("[STOP] Race cancelled due to F3 press")
            return False

        if not self.check_window():
            return False

        # Click races button
        if not find_and_click(
                "assets/buttons/races_btn.png", max_attempts=3, delay_between=2,
                check_stop_func=self.check_stop):
            return False

        if self.check_stop():
            return False

        # Check for OK button (indicates more than 3 races recently)
        ok_btn_found = False
        if not self.check_stop():
            ok_btn_found = find_and_click(
                "assets/buttons/ok_btn.png", max_attempts=3, delay_between=2,
                check_stop_func=self.check_stop)

        if ok_btn_found and not allow_continuous_racing:
            self.log("Continuous racing disabled - canceling race due to recent racing limit")
            if not self.check_stop():
                find_and_click(
                    "assets/buttons/cancel_btn.png", max_attempts=3, delay_between=2,
                    check_stop_func=self.check_stop)
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
        """Select race using panel-based detection with grade priority and fallback mechanism"""

        # Get enabled grades from filters
        enabled_grades = self._get_enabled_grades()

        # Calculate panel dimensions (split race region into smaller panels)
        left, top, width, height = RACE_REGION
        panel_height = height // 2  # Split vertically into 2 panels
        scroll_amount = panel_height  # Scroll by panel height

        # Primary search with grade filtering
        for scroll_attempt in range(4):
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

            # Move mouse to center of race region before scrolling
            center_x = left + width // 2
            center_y = top + height // 2
            pyautogui.moveTo(center_x, center_y, duration=0.2)

            # Scroll by panel height amount
            pyautogui.scroll(-scroll_amount)
            time.sleep(0.3)  # Wait after scrolling

        self.log("[DEBUG] Primary search completed, no matching race found. Starting fallback search...")

        # Fallback search: scroll up and look for any match_track
        return self._fallback_race_search()

    def _fallback_race_search(self) -> bool:
        """Fallback race search that only looks for match_track indicator"""

        left, top, width, height = RACE_REGION
        panel_height = height // 2
        scroll_amount = panel_height

        # Move mouse to center of race region
        center_x = left + width // 2
        center_y = top + height // 2
        pyautogui.moveTo(center_x, center_y, duration=0.2)

        # Scroll up by panel_height * 4 to reset position
        reset_scroll_amount = panel_height * 4

        self.log("[DEBUG] Scrolling up to reset position for fallback search...")
        pyautogui.scroll(reset_scroll_amount)  # Scroll up
        time.sleep(0.5)  # Wait for scroll to complete

        # Now scroll down and look for any match_track
        self.log("[DEBUG] Searching for any available race with match_track indicator...")

        for scroll_attempt in range(4):
            if self.check_stop():
                return False

            # Check both upper and lower panels for match_track only
            panels = [
                (left, top, width, panel_height),  # Upper panel
                (left, top + panel_height, width, panel_height)  # Lower panel
            ]

            for panel_index, panel_region in enumerate(panels):
                if self.check_stop():
                    return False

                # Look for match_track in this panel
                match_track_pos = self._find_match_track_in_panel(panel_region)

                if match_track_pos:
                    self.log("[DEBUG] Found race with match_track in fallback search")

                    # Click on the match_track position
                    pyautogui.moveTo(match_track_pos, duration=0.2)
                    pyautogui.click()

                    # Click race buttons
                    return self._click_race_buttons_original()

            # Move mouse to center before scrolling
            pyautogui.moveTo(center_x, center_y, duration=0.2)

            # Scroll down by panel height amount
            pyautogui.scroll(-scroll_amount)
            time.sleep(0.5)  # Wait after scrolling

        self.log("[DEBUG] Fallback search completed, no race with match_track found")
        return False

    def _find_matching_race_in_panel(self, panel_region: tuple, enabled_grades: list) -> Optional[tuple]:
        """Find matching race in the specified panel region based on enabled grades"""
        try:
            # Check grades in priority order: G1 > G2 > G3
            grade_priority = ['g1', 'g2', 'g3']

            for grade in grade_priority:
                if grade not in enabled_grades:
                    continue

                if self.check_stop():
                    return None

                # Find grade + match_track pair in this panel
                match_pos = self._find_grade_and_match_track_pair(panel_region, grade)

                if match_pos:
                    return (grade, match_pos)

            return None

        except Exception as e:
            self.log(f"[DEBUG] Error finding matching race in panel: {e}")
            return None

    def _find_grade_and_match_track_pair(self, panel_region: tuple, grade: str) -> Optional[tuple]:
        """Find single grade indicator + match_track pair in the same panel"""
        try:
            # Find first grade indicator in this panel
            template_path = f"assets/ui/{grade}_race.png"
            grade_location = find_template_position(
                template_path=template_path,
                region=panel_region,
                threshold=0.8,
                region_format='xywh'
            )

            if not grade_location:
                # Try alternative naming convention
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

    def _find_match_track_in_panel(self, panel_region: tuple) -> Optional[tuple]:
        """Find match_track indicator in the specified panel region"""
        try:
            # Convert panel_region from (x, y, width, height) to (left, top, right, bottom)
            left, top, width, height = panel_region
            region_ltrb = (left, top, left + width, top + height)

            match_track_location = pyautogui.locateCenterOnScreen(
                "assets/ui/match_track.png",
                confidence=0.8,
                minSearchTime=0.3,
                region=region_ltrb
            )

            if match_track_location:
                # Return tuple coordinates
                return (match_track_location.x, match_track_location.y)
            else:
                return None

        except Exception as e:
            self.log(f"[DEBUG] Error finding match_track in panel: {e}")
            return None

    def _click_race_buttons_original(self) -> bool:
        """Click race buttons to confirm selection"""
        for i in range(2):
            if self.check_stop():
                return False

            if not find_and_click(
                    "assets/buttons/race_btn.png", max_attempts=3, delay_between=1,
                    check_stop_func=self.check_stop):
                break

        return True

    def prepare_race(self, style_settings: Dict[str, Any] = None, is_pre_debut: bool = False) -> bool:
        """Prepare for race - handle style selection for pre-debut, then wait for results"""
        if self.check_stop():
            return False

        if not self.check_window():
            return False

        # Handle style selection during pre-debut race day
        if is_pre_debut and style_settings and style_settings.get('style', 'none') != 'none':
            target_style = style_settings.get('style')
            self.log(f"Pre-debut race - selecting style: {target_style}")
            time.sleep(1.0)
            # Click style_selection button first
            if find_and_click(f"{STYLE_ASSETS_FOLDER}/style_selection.png", max_attempts=3, delay_between=1,
                              check_stop_func=self.check_stop):
                time.sleep(0.5)
                # Click target style button
                if find_and_click(f"{STYLE_ASSETS_FOLDER}/{target_style}.png", max_attempts=3, delay_between=1,
                                  check_stop_func=self.check_stop):
                    # Click confirm button
                    find_and_click(f"{STYLE_ASSETS_FOLDER}/confirm.png", max_attempts=3, delay_between=1,
                                   check_stop_func=self.check_stop)

        # Wait for view results button (race animation takes time)
        view_result = find_and_click(
            "assets/buttons/view_results.png", max_attempts=10, delay_between=1,
            check_stop_func=self.check_stop)

        if view_result:
            if self.check_stop():
                return False

            time.sleep(5)

            for i in range(5):
                if self.check_stop():
                    return False

                random_screen_click(offset_range=0)
                time.sleep(1)

        return True

    def handle_after_race(self) -> bool:
        """Handle post-race - find next buttons with random screen clicks between checks"""
        if self.check_stop():
            return False

        if not self.check_window():
            return False

        # Find next_btn, with random_screen_click each attempt
        found_next = False
        for i in range(5):
            if self.check_stop():
                return False
            if find_and_click(
                    "assets/buttons/next_btn.png", max_attempts=1, delay_between=1,
                    check_stop_func=self.check_stop):
                found_next = True
                break
            random_screen_click(offset_range=100)
            time.sleep(1)

        if not found_next:
            return False

        if self.check_stop():
            return False

        # Find next2_btn, with random_screen_click each attempt
        for i in range(5):
            if self.check_stop():
                return False
            if find_and_click(
                    "assets/buttons/next2_btn.png", max_attempts=1, delay_between=1,
                    check_stop_func=self.check_stop):
                break
            random_screen_click(offset_range=100)

        return True

    def handle_race_day(self, is_ura_final: bool = False,
                        style_settings: Dict[str, Any] = None,
                        is_pre_debut: bool = False) -> bool:
        """Handle race day or URA finale race day"""
        if self.check_stop():
            self.log("[STOP] Race day cancelled due to F3 press")
            return False

        if is_ura_final:
            race_day_btn = "assets/buttons/ura_final_race_day_btn.png"
            print(f'race_day_btn {race_day_btn}')
        else:
            race_day_btn = "assets/buttons/race_day_btn.png"

        if not find_and_click(
                race_day_btn, max_attempts=3, delay_between=1,
                check_stop_func=self.check_stop):
            return False

        if self.check_stop():
            return False

        find_and_click(
            "assets/buttons/ok_btn.png", max_attempts=3, delay_between=1,
            check_stop_func=self.check_stop)

        for i in range(2):
            if self.check_stop():
                return False

            if not find_and_click(
                    "assets/buttons/race_btn.png", max_attempts=3, delay_between=1,
                    check_stop_func=self.check_stop):
                break

        if self.check_stop():
            return False

        if not self.prepare_race(style_settings=style_settings, is_pre_debut=is_pre_debut):
            return False


        if not self.handle_after_race():
            return False

        return True
