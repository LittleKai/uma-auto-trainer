import pyautogui
import time
from typing import Callable, Optional, Dict, List, Tuple

from core.click_handler import enhanced_click, random_click_in_region, move_to_random_position, random_screen_click
from core.recognizer import match_template

class RaceHandler:
    """Handles all race-related operations with simplified logic based on original"""

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

        Args:
            prioritize_g1: Whether to prioritize G1 races
            prioritize_g2: Whether to prioritize G2 races
            allow_continuous_racing: Whether to allow continuous racing

        Returns:
            bool: True if race was completed successfully
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

        # Prepare for race
        if not self.prepare_race() or self.check_stop():
            return False

        time.sleep(1)

        # Handle post-race
        if not self.handle_after_race() or self.check_stop():
            return False

        return True

    def select_race(self, prioritize_g1: bool = False, prioritize_g2: bool = False) -> bool:
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
        """Original G1 race selection logic"""
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

    def handle_race_day(self) -> bool:

        if self.check_stop():
            self.log("[STOP] Race day cancelled due to F3 press")
            return False

        if not self.check_window():
            return False

        # Click race day button
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

        # Click OK if present
        enhanced_click(
            "assets/buttons/ok_btn.png",
            minSearch=0.7,
            check_stop_func=self.check_stop,
            check_window_func=self.check_window,
            log_func=self.log
        )
        time.sleep(0.5)

        # Click race button(s)
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

        # Prepare and handle race
        if not self.prepare_race():
            return False

        time.sleep(1)

        if not self.handle_after_race():
            return False

        return True

    def prepare_race(self) -> bool:
        """
        Prepare for race by watching results

        Returns:
            bool: True if preparation was successful
        """
        if self.check_stop():
            return False

        if not self.check_window():
            return False

        # Wait for view results button
        view_result_btn_region = pyautogui.locateOnScreen(
            "assets/buttons/view_results.png",
            confidence=0.8,
            minSearchTime=20
        )

        if view_result_btn_region:
            if self.check_stop():
                return False

            # Random click within the view results button
            random_click_in_region(
                view_result_btn_region.left, view_result_btn_region.top,
                view_result_btn_region.width, view_result_btn_region.height
            )
            time.sleep(5)

            # Triple click with slight randomization for skipping
            for i in range(3):
                if self.check_stop():
                    return False

                # Random click in center area with offset
                random_screen_click(offset_range=0)
                time.sleep(0.5)

        return True

    def handle_after_race(self) -> bool:

        if self.check_stop():
            return False

        if not self.check_window():
            return False

        # Click next button
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

        # Random click in center area
        random_screen_click(offset_range=100)

        if self.check_stop():
            return False

        # Click final next button
        enhanced_click(
            "assets/buttons/next2_btn.png",
            minSearch=5,
            check_stop_func=self.check_stop,
            check_window_func=self.check_window,
            log_func=self.log
        )

        return True

    def handle_ura_finale(self) -> bool:
        """
        Handle URA finale race scenario

        Returns:
            bool: True if URA finale was handled successfully
        """
        if self.check_stop():
            return False

        self.log("URA Finale")

        # Import and execute URA scenario
        try:
            from utils.scenario import ura
            ura()
        except ImportError:
            self.log("[WARNING] URA scenario not available")

        # Click race buttons
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

        # Prepare and handle race
        self.prepare_race()
        time.sleep(1)
        self.handle_after_race()

        return True

    def get_race_status_info(self, race_manager, current_date: Optional[Dict]) -> Dict:
        """
        Get comprehensive race status information

        Args:
            race_manager: Race manager instance
            current_date: Current date information

        Returns:
            dict: Race status information
        """
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

            # Import DateManager for restriction check
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

    def log_race_status(self, race_status: Dict) -> None:
        """
        Log race status information in a formatted way

        Args:
            race_status: Race status information from get_race_status_info
        """
        try:
            if race_status['is_restricted']:
                self.log(f"📍 Racing Status: Disabled ({race_status['restriction_reason']})")

                # Show filtered races that would be available if not restricted
                if race_status['filtered_races']:
                    self.log(f"📍 Today's Races: {race_status['total_filtered']} matching filters (restricted)")
                    for race in race_status['filtered_races'][:3]:  # Show max 3
                        # Extract basic race information safely
                        race_name = race.get('name', 'Unknown Race')
                        race_grade = race.get('grade', 'Unknown')
                        race_track = race.get('track', 'Unknown')
                        race_distance = race.get('distance', 'Unknown')

                        self.log(f"  - {race_name} (Grade: {race_grade}, Track: {race_track}, Distance: {race_distance})")

                    if race_status['total_filtered'] > 3:
                        self.log(f"  ... and {race_status['total_filtered'] - 3} more")
                else:
                    self.log("📍 Today's Races: None match current filters")
            else:
                # Normal racing periods - only show races that match filters
                if race_status['available_races']:
                    self.log(f"📍 Today's Races: {race_status['total_available']} matching filters")
                    for race in race_status['available_races']:
                        # Extract basic race information safely
                        race_name = race.get('name', 'Unknown Race')
                        race_grade = race.get('grade', 'Unknown')
                        race_track = race.get('track', 'Unknown')
                        race_distance = race.get('distance', 'Unknown')

                        self.log(f"  - {race_name} (Grade: {race_grade}, Track: {race_track}, Distance: {race_distance})")
                else:
                    self.log("📍 Today's Races: None match current filters")
        except Exception as e:
            self.log(f"[WARNING] Error logging race status: {e}")
            # Fallback logging
            self.log(f"📍 Racing Status: {race_status.get('restriction_reason', 'Unknown')}")

    def should_prioritize_race(self, priority_strategy: str, available_races: List, race_manager) -> Tuple[bool, str]:
        """
        Determine if racing should be prioritized based on strategy and available races

        Args:
            priority_strategy: Current priority strategy
            available_races: List of available races
            race_manager: Race manager instance for race analysis

        Returns:
            tuple: (should_race_immediately, reason)
        """
        if not available_races:
            return False, "No races available"

        try:
            if "G1" in priority_strategy:
                # Only race if there's a G1 race available
                g1_races = []
                for race in available_races:
                    try:
                        race_props = race_manager.extract_race_properties(race)
                        if race_props.get('grade_type') == 'g1':
                            g1_races.append(race)
                    except:
                        continue

                if g1_races:
                    return True, f"G1 priority: Found {len(g1_races)} G1 races matching filters"
                else:
                    return False, "G1 priority: No G1 races found"

            elif "G2" in priority_strategy:
                # Race if there's a G1 or G2 race available
                high_grade_races = []
                for race in available_races:
                    try:
                        race_props = race_manager.extract_race_properties(race)
                        if race_props.get('grade_type') in ['g1', 'g2']:
                            high_grade_races.append(race)
                    except:
                        continue

                if high_grade_races:
                    return True, f"G2 priority: Found {len(high_grade_races)} G1/G2 races matching filters"
                else:
                    return False, "G2 priority: No G1/G2 races found"

            elif "Train Score" in priority_strategy:
                # For score strategies, always check training first
                return False, f"{priority_strategy}: Will check training first"

            return False, "Unknown strategy"

        except Exception as e:
            self.log(f"[WARNING] Error checking race priority: {e}")
            return False, f"Error checking priority: {e}"

    def extract_race_info_safe(self, race: Dict) -> Dict[str, str]:
        """
        Safely extract race information for logging

        Args:
            race: Race dictionary

        Returns:
            dict: Safely extracted race information
        """
        return {
            'name': race.get('name', 'Unknown Race'),
            'grade': race.get('grade', 'Unknown'),
            'track': race.get('track', 'Unknown'),
            'distance': race.get('distance', 'Unknown'),
            'year': race.get('year', 'Unknown'),
            'date': race.get('date', 'Unknown')
        }

    def is_racing_available(self, current_date: Optional[Dict], race_manager) -> Tuple[bool, str]:
        """
        Check if racing is available for the current date

        Args:
            current_date: Current date information
            race_manager: Race manager instance

        Returns:
            tuple: (is_available, reason)
        """
        if not current_date:
            return False, "No date information available"

        try:
            from core.race_manager import DateManager

            if DateManager.is_restricted_period(current_date):
                if current_date.get('is_pre_debut', False):
                    return False, "Pre-Debut period restriction"
                elif current_date.get('absolute_day', 0) <= 16:
                    return False, f"Career days 1-16 restriction (Day {current_date['absolute_day']}/72)"
                else:
                    return False, "July-August restriction"

            available_races = race_manager.get_available_races(current_date)
            if not available_races:
                return False, "No races match current filters"

            return True, f"{len(available_races)} races available"

        except Exception as e:
            return False, f"Error checking availability: {e}"