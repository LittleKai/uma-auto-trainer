import pyautogui
import time
from typing import Callable, Optional, Dict, List, Tuple

from core.click_handler import enhanced_click, random_click_in_region, move_to_random_position, random_screen_click
from core.recognizer import match_template

class RaceHandler:
    """Handles all race-related operations with conservative timing improvements"""

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
        """
        Start the complete race flow from lobby to finish
        Uses original timing but adds lobby verification
        """
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

        # Select race using original logic
        race_found = self.select_race(prioritize_g1=prioritize_g1, prioritize_g2=prioritize_g2)
        if not race_found or self.check_stop():
            self.log("No race found or operation cancelled.")
            return False

        # Prepare for race (original timing)
        if not self.prepare_race() or self.check_stop():
            return False

        # KEEP ORIGINAL TIMING: time.sleep(1)
        time.sleep(1)

        # Handle post-race (original timing)
        if not self.handle_after_race() or self.check_stop():
            return False

        # ONLY ADD: Verify return to lobby
        self._verify_lobby_return()

        return True

    def handle_race_day(self) -> bool:
        """Handle race day using original execute_old timing"""
        if self.check_stop():
            self.log("[STOP] Race day cancelled due to F3 press")
            return False

        if not self.check_window():
            return False

        # Original execute_old logic
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

        # Original timing
        enhanced_click(
            "assets/buttons/ok_btn.png",
            minSearch=0.7,
            check_stop_func=self.check_stop,
            check_window_func=self.check_window,
            log_func=self.log
        )
        time.sleep(0.5)  # Keep original timing

        # Original race button logic
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
            time.sleep(0.5)  # Keep original timing

        if self.check_stop():
            return False

        # Original race flow with original timing
        if not self.prepare_race():
            return False

        time.sleep(1)  # Keep original timing

        if not self.handle_after_race():
            return False

        # ONLY ADD: Verify return to lobby
        self._verify_lobby_return()

        return True

    def prepare_race(self) -> bool:
        """
        Prepare for race using EXACT original execute_old timing
        """
        if self.check_stop():
            return False

        if not self.check_window():
            return False

        # Original execute_old logic
        view_result_btn_region = pyautogui.locateOnScreen(
            "assets/buttons/view_results.png",
            confidence=0.8,
            minSearchTime=20  # Keep original
        )

        if view_result_btn_region:
            if self.check_stop():
                return False

            # Random click within the view results button
            random_click_in_region(
                view_result_btn_region.left, view_result_btn_region.top,
                view_result_btn_region.width, view_result_btn_region.height
            )

            # KEEP ORIGINAL TIMING: time.sleep(5)
            time.sleep(5)

            # KEEP ORIGINAL LOGIC: Triple click with original intervals
            for i in range(3):
                if self.check_stop():
                    return False

                # Random click in center area with offset
                random_screen_click(offset_range=0)
                time.sleep(0.5)  # Keep original timing

        return True

    def handle_after_race(self) -> bool:
        """
        Handle post-race using EXACT original execute_old timing
        """
        if self.check_stop():
            return False

        if not self.check_window():
            return False

        # KEEP ORIGINAL: minSearch=5
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

        # KEEP ORIGINAL TIMING: time.sleep(0.3)
        time.sleep(0.3)

        # KEEP ORIGINAL: random screen click
        random_screen_click(offset_range=100)

        if self.check_stop():
            return False

        # KEEP ORIGINAL: next2 button with minSearch=5
        enhanced_click(
            "assets/buttons/next2_btn.png",
            minSearch=5,
            check_stop_func=self.check_stop,
            check_window_func=self.check_window,
            log_func=self.log
        )

        return True

    def _verify_lobby_return(self, max_attempts: int = 5) -> bool:
        """
        ONLY ADDITION: Verify return to lobby without changing original flow
        This is called AFTER original race logic completes
        """
        for attempt in range(max_attempts):
            if self.check_stop():
                return False

            # Check for tazuna hint indicating we're in career lobby
            tazuna_hint = pyautogui.locateCenterOnScreen(
                "assets/ui/tazuna_hint.png",
                confidence=0.8,
                minSearchTime=0.5
            )

            if tazuna_hint:
                if attempt > 0:
                    self.log(f"[DEBUG] Successfully returned to lobby (attempt {attempt + 1})")
                return True

            # If not in lobby, wait a bit and try clicking any remaining UI elements
            self.log(f"[DEBUG] Not yet in lobby, waiting... (attempt {attempt + 1}/{max_attempts})")

            # Try to clear any remaining UI elements
            remaining_elements = [
                "assets/buttons/next_btn.png",
                "assets/buttons/next2_btn.png"
            ]

            for element in remaining_elements:
                enhanced_click(
                    element,
                    minSearch=0.3,
                    check_stop_func=self.check_stop,
                    check_window_func=self.check_window,
                    log_func=lambda msg: None  # Silent
                )

            time.sleep(0.5)  # Short wait between attempts

        self.log("[WARNING] Could not verify return to lobby, but continuing...")
        return True  # Don't block execution if verification fails

    def handle_ura_finale(self) -> bool:
        """
        Handle URA finale using original execute_old timing
        """
        if self.check_stop():
            return False

        self.log("URA Finale")

        # Original execute_old logic
        try:
            from utils.scenario import ura
            ura()
        except ImportError:
            self.log("[WARNING] URA scenario not available")

        # Original race button logic
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
                time.sleep(0.5)  # Keep original timing

        if self.check_stop():
            return False

        # Original flow with original timing
        self.prepare_race()
        time.sleep(1)  # Keep original timing
        self.handle_after_race()

        # ONLY ADD: Verify return to lobby
        self._verify_lobby_return()

        return True

    def select_race(self, prioritize_g1: bool = False, prioritize_g2: bool = False) -> bool:
        """UNCHANGED: Keep exact original logic"""
        if self.check_stop():
            return False

        if not self.check_window():
            return False

        # Move to race list area
        pyautogui.moveTo(x=560, y=680)
        time.sleep(0.2)

        # Handle G1 priority
        if prioritize_g1:
            return self._select_g1_race_original()

        # Handle G2 priority (try G2 first, then G1)
        elif prioritize_g2:
            self.log("Looking for G2 race, fallback to G1.")
            if self._select_g2_race_original():
                return True
            # Fallback to G1 if no G2 found
            return self._select_g1_race_original()

        # Default: any race
        else:
            return self._select_any_race_original()

    def _select_g1_race_original(self) -> bool:
        """UNCHANGED: Exact original logic"""
        self.log("Looking for G1 race.")

        for scroll_attempt in range(2):
            if self.check_stop():
                return False

            race_cards = match_template("assets/ui/g1_race.png", threshold=0.8)

            if race_cards:
                for x, y, w, h in race_cards:
                    if self.check_stop():
                        return False

                    # Original region logic
                    region = (x, y, 310, 90)
                    match_aptitude = pyautogui.locateCenterOnScreen(
                        "assets/ui/match_track.png",
                        confidence=0.8,
                        minSearchTime=0.7,
                        region=region
                    )

                    if match_aptitude:
                        self.log("G1 race with matching aptitude found.")
                        if self.check_stop():
                            return False

                        # Click on aptitude match
                        pyautogui.moveTo(match_aptitude, duration=0.2)
                        pyautogui.click()

                        # Click race buttons
                        return self._click_race_buttons_original()

            # Scroll down to find more races
            for i in range(4):
                if self.check_stop():
                    return False
                pyautogui.scroll(-300)

        self.log("No G1 race with matching aptitude found.")
        return False

    def _select_g2_race_original(self) -> bool:
        """UNCHANGED: Exact original logic"""
        self.log("Looking for G2 race.")

        for scroll_attempt in range(2):
            if self.check_stop():
                return False

            race_cards = match_template("assets/ui/g2_race.png", threshold=0.8)

            if race_cards:
                for x, y, w, h in race_cards:
                    if self.check_stop():
                        return False

                    # Original region logic
                    region = (x, y, 310, 90)
                    match_aptitude = pyautogui.locateCenterOnScreen(
                        "assets/ui/match_track.png",
                        confidence=0.8,
                        minSearchTime=0.7,
                        region=region
                    )

                    if match_aptitude:
                        self.log("G2 race with matching aptitude found.")
                        if self.check_stop():
                            return False

                        # Click on aptitude match
                        pyautogui.moveTo(match_aptitude, duration=0.2)
                        pyautogui.click()

                        # Click race buttons
                        return self._click_race_buttons_original()

            # Scroll down to find more races
            for i in range(4):
                if self.check_stop():
                    return False
                pyautogui.scroll(-300)

        self.log("No G2 race with matching aptitude found.")
        return False

    def _select_any_race_original(self) -> bool:
        """UNCHANGED: Exact original logic"""
        self.log("Looking for any matching race.")

        for scroll_attempt in range(4):
            if self.check_stop():
                return False

            match_aptitude = pyautogui.locateCenterOnScreen(
                "assets/ui/match_track.png",
                confidence=0.8,
                minSearchTime=0.7
            )

            if match_aptitude:
                self.log("Matching race found.")
                if self.check_stop():
                    return False

                # Click on aptitude match
                pyautogui.moveTo(match_aptitude, duration=0.2)
                pyautogui.click(match_aptitude)

                # Click race buttons
                return self._click_race_buttons_original()

            # Scroll down to find more races
            for i in range(4):
                if self.check_stop():
                    return False
                pyautogui.scroll(-300)

        return False

    def _click_race_buttons_original(self) -> bool:
        """UNCHANGED: Exact original logic"""
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

    # Keep all other methods unchanged...
    def get_race_status_info(self, race_manager, current_date: Optional[Dict]) -> Dict:
        """Get comprehensive race status information (unchanged)"""
        if not current_date:
            return {
                'available_races': [],
                'filtered_races': [],
                'is_restricted': True,
                'restriction_reason': 'No date information',
                'total_available': 0,
                'total_filtered': 0
            }

        try:
            available_races = race_manager.get_available_races(current_date)
            all_filtered_races = race_manager.get_filtered_races_for_date(current_date)

            from core.race_manager import DateManager
            is_restricted = DateManager.is_restricted_period(current_date)

            restriction_reason = ""
            if is_restricted:
                if current_date.get('is_pre_debut', False):
                    restriction_reason = "Pre-Debut period"
                elif current_date.get('absolute_day', 0) <= 16:
                    restriction_reason = f"Career days 1-16 restriction (current: Day {current_date['absolute_day']}/72)"
                else:
                    restriction_reason = "July-August restriction"

            return {
                'available_races': available_races,
                'filtered_races': all_filtered_races,
                'is_restricted': is_restricted,
                'restriction_reason': restriction_reason,
                'total_available': len(available_races),
                'total_filtered': len(all_filtered_races)
            }
        except Exception as e:
            self.log(f"[WARNING] Error getting race status: {e}")
            return {
                'available_races': [],
                'filtered_races': [],
                'is_restricted': True,
                'restriction_reason': f'Error: {e}',
                'total_available': 0,
                'total_filtered': 0
            }