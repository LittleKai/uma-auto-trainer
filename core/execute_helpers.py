import pyautogui
import time
from typing import Dict, Any, Callable
from core.race_handler import RaceHandler


class EventHandler:
    """Handles UI events and manual event processing"""

    def __init__(self, controller, check_stop_func: Callable, check_window_func: Callable, log_func: Callable):
        self.controller = controller
        self.check_stop = check_stop_func
        self.check_window = check_window_func
        self.log = log_func
        self.race_handler = RaceHandler(
            check_stop_func=self.check_stop,
            check_window_func=self.check_window,
            log_func=self.log
        )

    def handle_ui_elements(self, gui=None) -> bool:
        """Handle various UI elements with priority order including event choice"""
        if self._handle_event_choices(gui):
            self.controller.reset_career_lobby_counter()
            return True

        if self._click("assets/buttons/inspiration_btn.png", minSearch=0.2, text="Inspiration found."):
            self.controller.reset_career_lobby_counter()
            return True

        if self._click("assets/buttons/next_btn.png", minSearch=0.2):
            self.controller.reset_career_lobby_counter()
            return True

        if self._handle_cancel_button(gui):
            self.controller.reset_career_lobby_counter()
            return True

        if self._click("assets/buttons/next2_btn.png", minSearch=0.2):
            self.controller.reset_career_lobby_counter()
            return True
        from utils.constants import SCENARIO_NAME

        if SCENARIO_NAME == "Unity Cup":
            if self._click("assets/buttons/unity_cup/edit_team.png", minSearch=0.2,click_count=0):
                if self._click("assets/buttons/close_btn.png", minSearch=0.2):
                    self.controller.reset_career_lobby_counter()
                    return True

            if self._click("assets/buttons/unity_cup/unity_cup_btn.png", minSearch=0.2, text="Unity Cup Race found."):
                self.race_handler.unity_race_flow()
                self.controller.reset_career_lobby_counter()
                return True

        return False

    def _handle_cancel_button(self, gui=None) -> bool:
        """Handle cancel button with warning detection"""
        cancel_btn = pyautogui.locateCenterOnScreen("assets/buttons/cancel_btn.png", confidence=0.8,
                                                    minSearchTime=0.2)
        if not cancel_btn:
            return False
        else:
            try_again_btn = pyautogui.locateCenterOnScreen("assets/buttons/try_again_btn.png", confidence=0.95,
                                                      minSearchTime=0.2)
            if try_again_btn:
                self.controller.log_message("⚠ Race Failed !")

                # self.controller.log_message("⚠️ Failed Race Day - Trying again!")
                # return self._click("assets/buttons/try_again_btn.png", minSearch=0.2)
                if gui:
                    gui.root.after(0, gui.stop_bot)
                return True

        if gui:
            strategy_settings = gui.get_current_settings()
            stop_on_warning = strategy_settings.get('stop_on_warning', False)

            if stop_on_warning:
                if cancel_btn:
                    race_btn = pyautogui.locateCenterOnScreen("assets/buttons/race_btn.png", confidence=0.8,
                                                              minSearchTime=0.2)
                    if race_btn:
                        self.controller.log_message("⚠️ Warning detected - Stopping bot")
                        if gui:
                            gui.root.after(0, gui.stop_bot)
                        return True


        return self._click("assets/buttons/cancel_btn.png", minSearch=0.2)

    def _handle_event_choices(self, gui=None) -> bool:
        """Handle event choices using the improved event choice system"""
        if not self.controller.event_choice_handler.is_event_choice_visible():
            return False

        if gui:
            event_settings = gui.get_event_choice_settings()
            manual_event_handling = gui.get_current_settings().get('manual_event_handling', False)
        else:
            event_settings = {
                'auto_event_map': False,
                'auto_first_choice': True,
                'uma_musume': 'None',
                'support_cards': ['None'] * 6,
                'unknown_event_action': 'Auto select first choice'
            }
            manual_event_handling = False

        if manual_event_handling:
            self.controller.log_message("🎭 EVENT DETECTED! Manual event handling enabled.")
            self.controller.log_message("⏳ Waiting for you to select event choice manually...")

            event_handled = self._wait_for_event_completion(gui)

            if not event_handled:
                self.controller.log_message("⚠️ Event timeout - Stopping bot")
                if gui:
                    gui.root.after(0, gui.stop_bot)
                return False

            return True

        try:
            handled = self.controller.event_choice_handler.handle_event_choice(event_settings)

            if handled:
                return True
            else:
                unknown_action = event_settings.get('unknown_event_action', 'Auto select first choice')

                if not unknown_action == "Auto select first choice":
                    self.controller.log_message("⏳ Event may not in database - waiting for manual selection...")

                    event_handled = self._wait_for_event_completion(gui)

                    if not event_handled:
                        self.controller.log_message("⚠️ Event timeout - Stopping bot")
                        if gui:
                            gui.root.after(0, gui.stop_bot)
                        return False

                    return True
                else:
                    self.controller.log_message("🎭 Could not handle event automatically - using fallback choice 1")
                    return self.controller.event_choice_handler.click_choice(1)

        except Exception as e:
            self.controller.log_message(f"[ERROR] Event choice handling failed: {e}")
            return self.controller.event_choice_handler.click_choice(1)

    def _click(self, img, confidence=0.8, minSearch=1.0, click_count=1, text=""):
        """Click UI element with stop and window checks"""
        if self.controller.check_should_stop():
            return False

        if not self.controller.is_game_window_active():
            return False

        btn = pyautogui.locateCenterOnScreen(img, confidence=confidence, minSearchTime=minSearch)
        if btn:
            if click_count==0:
                return True
            if text:
                self.controller.log_message(text)
            if self.controller.check_should_stop():
                return False
            pyautogui.moveTo(btn, duration=0.175)
            pyautogui.click(clicks=click_count)
            return True

        return False

    def _wait_for_event_completion(self, gui=None, max_wait_time=120):
        """Wait for manual event completion with proper timeout handling"""
        start_time = time.time()
        last_log_time = 0

        while True:
            if self.controller.check_should_stop():
                return False

            if not self.controller.is_game_window_active():
                time.sleep(1)
                continue

            if not self.controller.event_choice_handler.is_event_choice_visible():
                if gui:
                    from core.state import check_mood
                    current_mood = check_mood()

                    if current_mood != "UNKNOWN":
                        self.controller.log_message("✅ Event completed - Event progressing - Resuming bot operations")
                        return True
                    else:
                        continue

            elapsed = time.time() - start_time
            if elapsed > max_wait_time:
                self.controller.log_message("⚠️ Event waiting timeout - Stopping bot")
                self.controller.set_stop_flag(True)
                return False

            current_time = time.time()
            if elapsed > 10 and (current_time - last_log_time) >= 30:
                self.controller.log_message(f"⏳ Still waiting for event completion... ({int(elapsed)}s elapsed)")
                last_log_time = current_time

            time.sleep(1)


class CareerLobbyManager:
    """Manages career lobby detection and navigation"""

    def __init__(self, controller):
        self.controller = controller
        self.lobby_log_counter = 0

    def verify_lobby_state(self, gui=None) -> bool:
        """Verify if currently in career lobby"""
        tazuna_hint = pyautogui.locateCenterOnScreen(
            "assets/ui/tazuna_hint.png",
            confidence=0.8,
            minSearchTime=0.2
        )

        if tazuna_hint is None:
            self.lobby_log_counter += 1
            if self.lobby_log_counter >= 3:
                self.controller.log_message("Should be in career lobby.")
                self.lobby_log_counter = 0

            if self.controller.increment_career_lobby_counter():
                if gui:
                    gui.root.after(0, gui.stop_bot)
                return False

            return False
        else:
            self.controller.reset_career_lobby_counter()
            self.lobby_log_counter = 0
            return True

    def handle_debuff_status(self, gui=None) -> bool:
        """Handle character debuff status"""
        from core.recognizer import is_infirmary_active

        debuffed = pyautogui.locateOnScreen(
            "assets/buttons/infirmary_btn2.png",
            confidence=0.9,
            minSearchTime=1
        )

        if debuffed:
            if is_infirmary_active((debuffed.left, debuffed.top, debuffed.width, debuffed.height)):
                if (gui and gui.get_current_settings().get('enable_stop_conditions', False) and
                        gui.get_current_settings().get('stop_on_infirmary', False)):
                    from core.state import get_current_date_info
                    current_date = get_current_date_info()
                    absolute_day = current_date.get('absolute_day', 0) if current_date else 0

                    if absolute_day > 24:
                        self.controller.log_message("Stop condition: Infirmary needed - Stopping bot")
                        gui.root.after(0, gui.stop_bot)
                        return True

                if self.controller.check_should_stop():
                    return False
                pyautogui.click(debuffed)
                self.controller.log_message("Character has debuff, go to infirmary instead.")
                self.controller.reset_career_lobby_counter()
                return True

        return False


class StatusLogger:
    """Handles status logging and GUI updates"""

    def __init__(self, controller):
        self.controller = controller

    def log_current_status(self, game_state: Dict[str, Any],
                           strategy_settings: Dict[str, Any], race_manager):
        """Log current game status"""
        self.controller.log_message("=" * 50)
        self.controller.log_message(f"Year: {game_state['year']}")
        self.controller.log_message(f"Mood: {game_state['mood']}")
        self.controller.log_message(f"Energy: {game_state['energy_percentage']}%")
        self._log_date_and_race_info(game_state['current_date'], race_manager)

    def _log_date_and_race_info(self, current_date: Dict[str, Any], race_manager):
        """Log date and race information"""
        from core.race_manager import DateManager

        if not current_date:
            return

        if current_date.get('is_finale', False):
            self.controller.log_message(f"Current Date: Finale Season (Career Completed)")
        elif current_date.get('is_pre_debut', False):
            self.controller.log_message(
                f"Current Date: {current_date['year']} Year Pre-Debut (Day {current_date['absolute_day']}/72)")
        else:
            self.controller.log_message(
                f"Current Date: {current_date['year']} {current_date['month']} {current_date['period']} (Day {current_date['absolute_day']}/72)")

        available_races = race_manager.get_available_races(current_date)
        all_filtered_races = race_manager.get_filtered_races_for_date(current_date)

        if DateManager.is_restricted_period(current_date):
            if all_filtered_races:
                self.controller.log_message(
                    f"🏁 Today's Races: {len(all_filtered_races)} matching filters (restricted)")
                for race in all_filtered_races[:3]:
                    race_props = race_manager.extract_race_properties(race)
                    self.controller.log_message(
                        f"  - {race['name']} ({race_props['grade_type'].upper()}, {race_props['track_type']}, {race_props['distance_type']})")
                if len(all_filtered_races) > 3:
                    self.controller.log_message(f"  ... and {len(all_filtered_races) - 3} more")
            else:
                self.controller.log_message("🏁 Today's Races: None match current filters (restricted)")
        else:
            if all_filtered_races:
                self.controller.log_message(f"🏁 Today's Races: {len(all_filtered_races)} matching filters")
                for race in all_filtered_races[:3]:
                    race_props = race_manager.extract_race_properties(race)
                    self.controller.log_message(
                        f"  - {race['name']} ({race_props['grade_type'].upper()}, {race_props['track_type']}, {race_props['distance_type']})")
                if len(all_filtered_races) > 3:
                    self.controller.log_message(f"  ... and {len(all_filtered_races) - 3} more")
            else:
                self.controller.log_message("🏁 Today's Races: None match current filters")

    def log_game_state(self, game_state: Dict[str, Any], race_manager=None, gui=None):
        """Log current game state information"""
        if not game_state:
            return

        self.controller.log_message(f"Mood: {game_state.get('mood', 'UNKNOWN')}")
        self.controller.log_message(f"Turn: {game_state.get('turn', 'Unknown')}")
        self.controller.log_message(f"Year: {game_state.get('year', 'Unknown')}")

        energy_percentage = game_state.get('energy_percentage', 0)
        energy_max = game_state.get('energy_max', 0)
        self.controller.log_message(f"Energy: {energy_percentage}% (Max: {energy_max})")

        current_date = game_state.get('current_date')
        if current_date:
            self.controller.log_message(
                f"Date: {current_date.get('year', 'Unknown')} - Day {current_date.get('absolute_day', 0)}"
            )

        if race_manager and game_state.get('turn') == "Race Day":
            self._log_race_info(race_manager, game_state, gui)

    def _log_race_info(self, race_manager, game_state: Dict[str, Any], gui=None):
        """Log race information for Race Day"""
        current_date = game_state.get('current_date')
        if not current_date:
            return

        available_races = race_manager.get_available_races(current_date)

        if gui:
            all_filtered_races = race_manager.get_filtered_races_for_date(current_date)
            available_races = all_filtered_races[:3]

            if available_races:
                self.controller.log_message(f"🏁 Today's Races (showing top 3):")
                for race in available_races:
                    race_props = race_manager.extract_race_properties(race)
                    self.controller.log_message(
                        f"  - {race['name']} ({race_props['grade_type'].upper()}, {race_props['track_type']}, {race_props['distance_type']})")
                if len(all_filtered_races) > 3:
                    self.controller.log_message(f"  ... and {len(all_filtered_races) - 3} more")
            else:
                self.controller.log_message("🏁 Today's Races: None match current filters")
        else:
            if available_races:
                self.controller.log_message(f"🏁 Today's Races: {len(available_races)} matching filters")
                for race in available_races:
                    race_props = race_manager.extract_race_properties(race)
                    self.controller.log_message(
                        f"  - {race['name']} ({race_props['grade_type'].upper()}, {race_props['track_type']}, {race_props['distance_type']})")
            else:
                self.controller.log_message("🏁 Today's Races: None match current filters")

    def update_gui_status(self, gui, game_state: Dict[str, Any]):
        """Update GUI status displays"""
        if not gui:
            return

        if game_state['current_date']:
            gui.update_current_date(game_state['current_date'])

        gui.update_energy_display((game_state['energy_percentage'], game_state['energy_max']))


__all__ = ['EventHandler', 'CareerLobbyManager', 'StatusLogger']