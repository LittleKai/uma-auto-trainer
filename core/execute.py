import pyautogui
import time
import json
import pygetwindow as gw
from typing import Dict, Optional, Callable, Any, Tuple

pyautogui.useImageNotFoundException(False)

# Import handlers
from core.training_handler import TrainingHandler
from core.race_handler import RaceHandler
from core.rest_handler import RestHandler
from core.click_handler import enhanced_click

# Import core systems
from core.state import (
    check_turn, check_mood, check_current_year, check_criteria,
    get_current_date_info, check_energy_percentage
)
from core.logic import training_decision, fallback_training
from core.recognizer import is_infirmary_active
from core.race_manager import RaceManager, DateManager
from utils.constants import (
    MOOD_LIST, MINIMUM_ENERGY_PERCENTAGE, CRITICAL_ENERGY_PERCENTAGE,
    MAX_CAREER_LOBBY_ATTEMPTS
)


class BotController:
    """Main bot controller that orchestrates all operations"""

    def __init__(self):
        """Initialize the bot controller"""
        self.should_stop = False
        self.career_lobby_attempts = 0
        self.log_callback = None

        # Initialize handlers
        self._init_handlers()

        # Load configuration
        self._load_config()

    def _init_handlers(self):
        """Initialize all handler instances"""
        self.training_handler = TrainingHandler(
            check_stop_func=self.check_should_stop,
            check_window_func=self.is_game_window_active,
            log_func=self.log_message
        )

        self.race_handler = RaceHandler(
            check_stop_func=self.check_should_stop,
            check_window_func=self.is_game_window_active,
            log_func=self.log_message
        )

        self.rest_handler = RestHandler(
            check_stop_func=self.check_should_stop,
            check_window_func=self.is_game_window_active,
            log_func=self.log_message
        )

    def _load_config(self):
        """Load configuration from file"""
        try:
            with open("config.json", "r", encoding="utf-8") as file:
                self.config = json.load(file)
        except FileNotFoundError:
            self.log_message("[WARNING] Config file not found, using defaults")
            self.config = {
                "minimum_energy_percentage": 40,
                "critical_energy_percentage": 25
            }

    def set_log_callback(self, callback: Callable[[str], None]):
        """Set logging callback function"""
        self.log_callback = callback

    def log_message(self, message: str):
        """Log message using callback or print"""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def set_stop_flag(self, value: bool = True):
        """Set the stop flag (called by F3 key)"""
        self.should_stop = value

    def check_should_stop(self) -> bool:
        """Check if bot should stop"""
        if self.should_stop:
            self.log_message("[STOP] Operation cancelled due to F3 press")
            return True
        return False

    def is_game_window_active(self) -> bool:
        """Check if Umamusume window is currently active"""
        try:
            windows = gw.getWindowsWithTitle("Umamusume")
            return windows and windows[0].isActive
        except:
            return False

    def reset_career_lobby_counter(self):
        """Reset career lobby detection counter"""
        self.career_lobby_attempts = 0

    def increment_career_lobby_counter(self) -> bool:
        """Increment career lobby counter and check limits"""
        self.career_lobby_attempts += 1

        if self.career_lobby_attempts >= MAX_CAREER_LOBBY_ATTEMPTS:
            self.log_message(f"[ERROR] Career lobby detection failed {MAX_CAREER_LOBBY_ATTEMPTS} times")
            self.log_message("[ERROR] Bot appears to be stuck - stopping program")
            self.set_stop_flag(True)
            return True

        return False


class GameStateManager:
    """Manages current game state information"""

    def __init__(self, controller: BotController):
        self.controller = controller
        self.current_state = {}

    def update_game_state(self) -> Dict[str, Any]:
        """Update and return current game state"""
        try:
            mood = check_mood()
            turn = check_turn()
            year = check_current_year()
            criteria = check_criteria()
            energy_percentage = check_energy_percentage()
            current_date = get_current_date_info()

            if current_date is None:
                self.controller.log_message("[ERROR] Date parsing failed, using safe fallback behavior")
                current_date = {
                    'year': 'Classic',
                    'absolute_day': 50,
                    'is_pre_debut': False,
                    'is_finale': False
                }

            self.current_state = {
                'mood': mood,
                'turn': turn,
                'year': year,
                'criteria': criteria,
                'energy_percentage': energy_percentage,
                'current_date': current_date
            }

            return self.current_state

        except Exception as e:
            self.controller.log_message(f"Error in game state update: {e}")
            return {
                'mood': 'UNKNOWN',
                'turn': -1,
                'year': 'Unknown',
                'criteria': 'Unknown',
                'energy_percentage': 50,
                'current_date': {
                    'year': 'Classic',
                    'absolute_day': 50,
                    'is_pre_debut': False,
                    'is_finale': False
                }
            }

    def is_career_completed(self) -> bool:
        """Check if career is completed"""
        return self.current_state.get('current_date', {}).get('is_finale', False)

    def is_race_day(self) -> bool:
        """Check if current turn is race day"""
        return self.current_state.get('turn') == "Race Day"

    def is_ura_finale(self) -> bool:
        """Check if this is URA finale"""
        return (self.current_state.get('year') == "Finale Season" and
                self.current_state.get('turn') == "Race Day")


class EventHandler:
    """Handles UI events and manual event processing"""

    def __init__(self, controller: BotController):
        self.controller = controller

    def handle_ui_elements(self, gui=None) -> bool:
        """Handle various UI elements with priority order"""
        # Priority 1: Handle event choices first (highest priority)
        event_choice_found = pyautogui.locateCenterOnScreen(
            "assets/icons/event_choice_1.png",
            confidence=0.8,
            minSearchTime=0.2
        )

        if event_choice_found:
            # Get manual event handling setting
            manual_event_handling = False
            if gui:
                settings = gui.get_current_settings()
                manual_event_handling = settings.get('manual_event_handling', False)

            if manual_event_handling:
                self.controller.log_message("🎭 EVENT DETECTED! Manual event handling enabled.")
                self.controller.log_message("⏳ Waiting for you to select event choice manually...")

                # Wait for event completion without stopping the bot
                event_handled = self._wait_for_event_completion(gui)

                if not event_handled:
                    return False

                return True
            else:
                if self._click("assets/icons/event_choice_1.png", minSearch=0.2,
                               text="Event found, automatically select top choice."):
                    return True

        # Priority 2: Handle other UI elements
        if self._click("assets/buttons/inspiration_btn.png", minSearch=0.2, text="Inspiration found."):
            return True

        if self._click("assets/buttons/next_btn.png", minSearch=0.2):
            return True

        if self._click("assets/buttons/cancel_btn.png", minSearch=0.2):
            return True

        if self._click("assets/buttons/next2_btn.png", minSearch=0.2):
            return True

        return False

    def _click(self, img, confidence=0.8, minSearch=2, click_count=1, text=""):
        """Click UI element with stop and window checks"""
        if self.controller.check_should_stop():
            return False

        if not self.controller.is_game_window_active():
            return False

        btn = pyautogui.locateCenterOnScreen(img, confidence=confidence, minSearchTime=minSearch)
        if btn:
            if text:
                self.controller.log_message(text)
            if self.controller.check_should_stop():
                return False
            pyautogui.moveTo(btn, duration=0.175)
            pyautogui.click(clicks=click_count)
            return True

        return False

    def _wait_for_event_completion(self, gui=None, max_wait_time=120):
        """Wait for manual event completion and stop bot on timeout"""
        import time

        start_time = time.time()

        while True:
            # Check if bot was stopped manually
            if self.controller.check_should_stop():
                return False

            time.sleep(0.5)

            # Check if event choice is still visible
            event_still_present = pyautogui.locateCenterOnScreen(
                "assets/icons/event_choice_1.png",
                confidence=0.8,
                minSearchTime=0.2
            )

            if not event_still_present:
                # Event is gone, check if we're back to normal game state
                tazuna_hint = pyautogui.locateCenterOnScreen(
                    "assets/ui/tazuna_hint.png",
                    confidence=0.8,
                    minSearchTime=0.2
                )

                if tazuna_hint:
                    # Back to main menu - event completed
                    return True
                else:
                    # Check for other game states that indicate event is progressing
                    other_btn = pyautogui.locateCenterOnScreen("assets/buttons/cancel_btn.png", confidence=0.8,
                                                               minSearchTime=0.2) or pyautogui.locateCenterOnScreen(
                        "assets/buttons/inspiration_btn.png", confidence=0.8, minSearchTime=0.2) or pyautogui.locateCenterOnScreen(
                        "assets/buttons/next_btn.png", confidence=0.8, minSearchTime=0.2)
                    if other_btn:
                        return True
                    else:
                        # Event is progressing, continue waiting
                        continue

            # Timeout check
            if time.time() - start_time > max_wait_time:
                self.controller.log_message("⚠️ Event waiting timeout - Stopping bot")
                # Actually stop the bot when timeout occurs
                if gui:
                    gui.root.after(0, gui.stop_bot)
                else:
                    self.controller.set_stop_flag(True)
                return False

            # Show waiting message every 30 seconds
            elapsed = time.time() - start_time
            if elapsed > 10 and int(elapsed) % 30 == 0:
                self.controller.log_message(f"⏳ Still waiting for event completion... ({int(elapsed)}s elapsed)")


class DecisionEngine:
    """Makes training and racing decisions based on game state"""

    def __init__(self, controller: BotController):
        self.controller = controller

    def make_decision(self, game_state: Dict[str, Any], strategy_settings: Dict[str, Any],
                      race_manager, gui=None) -> bool:
        """Make training/racing decision based on current game state"""

        # Check stop conditions first
        if gui:
            if self._check_stop_conditions(game_state, strategy_settings, gui):
                return False

        # Handle URA Finale
        if game_state['year'] == "Finale Season" and game_state['turn'] == "Race Day":
            self.controller.log_message("URA Finale")
            if self.controller.check_should_stop():
                return False
            return self.controller.race_handler.handle_ura_finale()

        # Handle Race Day
        if game_state['turn'] == "Race Day" and game_state['year'] != "Finale Season":
            if (strategy_settings.get('enable_stop_conditions', False) and
                    strategy_settings.get('stop_on_race_day', False)):
                self.controller.log_message("Stop condition: Race Day detected - Stopping bot")
                if gui:
                    gui.root.after(0, gui.stop_bot)
                return False

            self.controller.log_message("Race Day.")
            if self.controller.check_should_stop():
                return False
            return self.controller.race_handler.handle_race_day()

        if self.controller.check_should_stop():
            return False

        mood = game_state['mood']
        current_date = game_state['current_date']
        energy_percentage = game_state['energy_percentage']

        # Check mood requirements (using minimum_mood for training strategy)
        mood_index = MOOD_LIST.index(mood) if mood in MOOD_LIST else 0
        minimum_mood_index = MOOD_LIST.index(strategy_settings.get('minimum_mood', 'NORMAL'))

        if mood_index < minimum_mood_index:
            # Stop condition using separate stop_mood_threshold and only applies after day 24
            if (strategy_settings.get('enable_stop_conditions', False) and
                    strategy_settings.get('stop_on_low_mood', False) and
                    current_date and current_date.get('absolute_day', 0) > 24):

                stop_mood_threshold = strategy_settings.get('stop_mood_threshold', 'BAD')
                stop_mood_index = MOOD_LIST.index(stop_mood_threshold) if stop_mood_threshold in MOOD_LIST else 1

                if mood_index < stop_mood_index:
                    self.controller.log_message(f"Stop condition: Mood ({mood}) below threshold ({stop_mood_threshold}) after day 24 - Stopping bot")
                    if gui:
                        gui.root.after(0, gui.stop_bot)
                    return False

            is_junior_year = current_date and current_date.get('absolute_day', 0) < 24

            if not is_junior_year:
                self.controller.log_message(
                    f"Mood is {mood}, below minimum {strategy_settings.get('minimum_mood', 'NORMAL')}. Trying recreation to increase mood")
                if self.controller.check_should_stop():
                    return False
                self.controller.rest_handler.execute_recreation()
                return True

        if self.controller.check_should_stop():
            return False

        priority_strategy = strategy_settings.get('priority_strategy', 'Train Score 2.5+')
        allow_continuous_racing = strategy_settings.get('allow_continuous_racing', True)

        # Handle G1/G2 priority strategies - skip training check completely
        if "G1 (no training)" in priority_strategy or "G2 (no training)" in priority_strategy:
            return self._handle_race_priority_strategy(game_state, strategy_settings, race_manager, gui)

        # Handle critical energy
        if energy_percentage < CRITICAL_ENERGY_PERCENTAGE:
            should_race, available_races = race_manager.should_race_today(current_date)
            if should_race:
                self.controller.log_message(
                    f"Critical energy ({energy_percentage}%) - found {len(available_races)} matching races. Racing to avoid training.")
                if self.controller.check_should_stop():
                    return False
                race_found = self.controller.race_handler.start_race_flow(
                    allow_continuous_racing=allow_continuous_racing)
                if race_found:
                    return True
                else:
                    if not self.controller.check_should_stop():
                        self._click_back_button("Race not found. Critical energy - will rest.")
                        time.sleep(0.5)
                        self.controller.rest_handler.execute_rest()
                    return True
            else:
                self.controller.log_message(
                    f"Critical energy ({energy_percentage}%) and no matching races today. Resting immediately.")
                if self.controller.check_should_stop():
                    return False
                self.controller.rest_handler.execute_rest()
                return True

        # Handle low energy
        elif energy_percentage < MINIMUM_ENERGY_PERCENTAGE:
            should_race, available_races = race_manager.should_race_today(current_date)
            if should_race:
                self.controller.log_message(
                    f"Low energy ({energy_percentage}%) but found {len(available_races)} matching races for today. Racing instead of training.")
                if self.controller.check_should_stop():
                    return False
                race_found = self.controller.race_handler.start_race_flow(
                    allow_continuous_racing=allow_continuous_racing)
                if race_found:
                    return True
                else:
                    if not self.controller.check_should_stop():
                        self._click_back_button("Matching race not found in game. Low energy - will check WIT training.")
                        time.sleep(0.5)
            else:
                self.controller.log_message(
                    f"Low energy ({energy_percentage}%) and no matching races today. Will check WIT training or rest.")

        if self.controller.check_should_stop():
            return False

        # Handle normal energy with race priority check
        if current_date and energy_percentage >= MINIMUM_ENERGY_PERCENTAGE:
            should_race, available_races = race_manager.should_race_today(current_date)

            if should_race and available_races:

                race_matches_priority = False

                if "G1" in priority_strategy:
                    g1_races = [race for race in available_races
                                if race_manager.extract_race_properties(race)['grade_type'] == 'g1']
                    if g1_races:
                        race_matches_priority = True
                        self.controller.log_message(
                            f"G1 priority: Found {len(g1_races)} G1 races matching filters - Racing immediately")
                    else:
                        self.controller.log_message(f"G1 priority: No G1 races found, will check training first")

                elif "G2" in priority_strategy:
                    high_grade_races = [race for race in available_races
                                        if race_manager.extract_race_properties(race)['grade_type'] in ['g1', 'g2']]
                    if high_grade_races:
                        race_matches_priority = True
                        self.controller.log_message(
                            f"G2 priority: Found {len(high_grade_races)} G1/G2 races matching filters - Racing immediately")
                    else:
                        self.controller.log_message(f"G2 priority: No G1/G2 races found, will check training first")

                elif "Train Score" in priority_strategy:
                    self.controller.log_message(
                        f"{priority_strategy}: Will check training first, then race if requirements not met")
                    race_matches_priority = False

                if race_matches_priority:
                    if self.controller.check_should_stop():
                        return False
                    race_found = self.controller.race_handler.start_race_flow(
                        allow_continuous_racing=allow_continuous_racing)
                    if race_found:
                        return True
                    else:
                        if not self.controller.check_should_stop():
                            self._click_back_button("Matching race not found in game. Proceeding to training.")
                            time.sleep(0.5)
            else:
                if DateManager.is_restricted_period(current_date):
                    if current_date['absolute_day'] <= 16:
                        self.controller.log_message(
                            "In restricted racing period (Career days 1-16). No racing allowed.")
                    else:
                        self.controller.log_message("In restricted racing period (Jul-Aug). No racing allowed.")

        if self.controller.check_should_stop():
            return False

        # Check training options
        if not self.controller.training_handler.go_to_training():
            return True

        if self.controller.check_should_stop():
            return False

        time.sleep(0.5)
        results_training = self.controller.training_handler.check_all_training(energy_percentage)

        if self.controller.check_should_stop():
            return False

        best_training = training_decision(
            results_training,
            energy_percentage,
            strategy_settings,
            current_date
        )

        # Handle special case: SHOULD_REST
        if best_training == "SHOULD_REST":
            # Stop condition only applies after day 24
            if (strategy_settings.get('enable_stop_conditions', False) and
                    strategy_settings.get('stop_on_need_rest', False) and
                    current_date and current_date.get('absolute_day', 0) > 24):
                self.controller.log_message("Stop condition: Need rest detected after day 24 - Stopping bot")
                self._click_back_button("")
                if gui:
                    gui.root.after(0, gui.stop_bot)
                return False

            self.controller.log_message(f"Medium energy ({energy_percentage}%) with low training scores - Resting instead of inefficient training")
            if self.controller.check_should_stop():
                return False
            self._click_back_button("")
            time.sleep(0.5)
            self.controller.rest_handler.execute_rest()
            return True

        if best_training:
            if self.controller.check_should_stop():
                return False
            self.controller.training_handler.go_to_training()
            time.sleep(0.5)
            if self.controller.check_should_stop():
                return False
            self.controller.training_handler.execute_training(best_training)
            self.controller.log_message(f"Training: {best_training.upper()}")
        else:
            self.controller.log_message(f"No training meets {priority_strategy} strategy requirements")

            if current_date and energy_percentage >= MINIMUM_ENERGY_PERCENTAGE:
                should_race, available_races = race_manager.should_race_today(current_date)

                if should_race:
                    self.controller.log_message(
                        f"Attempting race from {len(available_races)} available races as fallback.")
                    if self.controller.check_should_stop():
                        return False
                    race_found = self.controller.race_handler.start_race_flow(
                        allow_continuous_racing=allow_continuous_racing)
                    if race_found:
                        return True
                    else:
                        if not self.controller.check_should_stop():
                            self._click_back_button("Race not found.")
                            time.sleep(0.5)

            if self.controller.check_should_stop():
                return False

            if energy_percentage < MINIMUM_ENERGY_PERCENTAGE:
                self.controller.rest_handler.execute_rest()
                self.controller.log_message(f"Low energy ({energy_percentage}%) - Resting")
            else:
                self.controller.log_message(
                    f"Normal energy but no {priority_strategy} training found - doing fallback training")

                if results_training:
                    fallback_result = fallback_training(results_training, current_date)
                    if fallback_result:
                        best_key, score_info = fallback_result
                        if self.controller.check_should_stop():
                            return False
                        self.controller.training_handler.go_to_training()
                        time.sleep(0.5)
                        if self.controller.check_should_stop():
                            return False
                        self.controller.training_handler.execute_training(best_key)
                        self.controller.log_message(f"Fallback Training: {best_key.upper()} {score_info}")
                    else:
                        if self.controller.check_should_stop():
                            return False
                        self.controller.rest_handler.execute_rest()
                        self.controller.log_message("No support cards found in any training - Resting")
                else:
                    if self.controller.check_should_stop():
                        return False
                    self.controller.log_message("No training available!")
                    return True

        return True

    def _handle_race_priority_strategy(self, game_state: Dict[str, Any], strategy_settings: Dict[str, Any],
                                       race_manager, gui=None) -> bool:
        """Handle G1/G2 priority strategies with fixed critical energy logic"""
        priority_strategy = strategy_settings.get('priority_strategy', 'Train Score 2.5+')
        allow_continuous_racing = strategy_settings.get('allow_continuous_racing', True)
        current_date = game_state['current_date']
        energy_percentage = game_state['energy_percentage']

        # Handle critical energy for G1/G2 strategies - rest instead of training
        if energy_percentage < CRITICAL_ENERGY_PERCENTAGE:
            should_race, available_races = race_manager.should_race_today(current_date)
            if should_race:
                self.controller.log_message(
                    f"{priority_strategy}: Critical energy ({energy_percentage}%) - found {len(available_races)} matching races. Racing to avoid training.")
                if self.controller.check_should_stop():
                    return False
                race_found = self.controller.race_handler.start_race_flow(
                    allow_continuous_racing=allow_continuous_racing)
                if race_found:
                    return True
                else:
                    if not self.controller.check_should_stop():
                        self._click_back_button(f"{priority_strategy}: Race not found. Critical energy - will rest.")
                        time.sleep(0.5)
                        self.controller.rest_handler.execute_rest()
                    return True
            else:
                self.controller.log_message(
                    f"{priority_strategy}: Critical energy ({energy_percentage}%) and no matching races today. Resting immediately.")
                if self.controller.check_should_stop():
                    return False
                self.controller.rest_handler.execute_rest()
                return True

        # Check if racing is possible today
        should_race, available_races = race_manager.should_race_today(current_date)

        if not should_race or not available_races:
            if DateManager.is_restricted_period(current_date):
                if current_date['absolute_day'] <= 16:
                    self.controller.log_message("In restricted racing period (Career days 1-16). No racing allowed.")
                else:
                    self.controller.log_message("In restricted racing period (Jul-Aug). No racing allowed.")
            else:
                self.controller.log_message("No matching races available today.")

            # No races available, proceed with normal training/rest logic instead of waiting
            self.controller.log_message(f"{priority_strategy}: No races available, proceeding with normal training/rest logic")

            # Check training options
            if not self.controller.training_handler.go_to_training():
                return True

            if self.controller.check_should_stop():
                return False

            time.sleep(0.5)
            results_training = self.controller.training_handler.check_all_training(energy_percentage)

            if self.controller.check_should_stop():
                return False

            best_training = training_decision(
                results_training,
                energy_percentage,
                strategy_settings,
                current_date
            )

            if best_training and best_training != "SHOULD_REST":
                if self.controller.check_should_stop():
                    return False
                self.controller.training_handler.go_to_training()
                time.sleep(0.5)
                if self.controller.check_should_stop():
                    return False
                self.controller.training_handler.execute_training(best_training)
                self.controller.log_message(f"Training: {best_training.upper()}")
                return True
            else:
                # No suitable training found or should rest
                if energy_percentage < MINIMUM_ENERGY_PERCENTAGE or best_training == "SHOULD_REST":
                    self.controller.rest_handler.execute_rest()
                    self.controller.log_message(f"No suitable training or low energy ({energy_percentage}%) - Resting")
                else:
                    # Try fallback training
                    if results_training:
                        fallback_result = fallback_training(results_training, current_date)
                        if fallback_result:
                            best_key, score_info = fallback_result
                            if self.controller.check_should_stop():
                                return False
                            self.controller.training_handler.go_to_training()
                            time.sleep(0.5)
                            if self.controller.check_should_stop():
                                return False
                            self.controller.training_handler.execute_training(best_key)
                            self.controller.log_message(f"Fallback Training: {best_key.upper()} {score_info}")
                            return True

                    # Last resort: rest
                    self.controller.rest_handler.execute_rest()
                    self.controller.log_message("No training options available - Resting")

            return True

        # Check grade priority for G2 strategy
        if "G2 (no training)" in priority_strategy:
            # For G2 strategy, prioritize G1 > G2 if both are enabled in filters
            g1_races = [race for race in available_races
                        if race_manager.extract_race_properties(race)['grade_type'] == 'g1']
            g2_races = [race for race in available_races
                        if race_manager.extract_race_properties(race)['grade_type'] == 'g2']

            if g1_races:
                self.controller.log_message(f"G2 priority: Found {len(g1_races)} G1 races (higher priority) - Racing")
            elif g2_races:
                self.controller.log_message(f"G2 priority: Found {len(g2_races)} G2 races - Racing")
            else:
                self.controller.log_message("G2 priority: No G1/G2 races found in available races")
                # No G1/G2 races, proceed with normal training/rest logic
                self.controller.log_message("G2 priority: No suitable races, proceeding with normal training/rest logic")

                # Use the same training logic as above for consistency
                if not self.controller.training_handler.go_to_training():
                    return True

                if self.controller.check_should_stop():
                    return False

                time.sleep(0.5)
                results_training = self.controller.training_handler.check_all_training(energy_percentage)

                if self.controller.check_should_stop():
                    return False

                best_training = training_decision(
                    results_training,
                    energy_percentage,
                    strategy_settings,
                    current_date
                )

                if best_training and best_training != "SHOULD_REST":
                    if self.controller.check_should_stop():
                        return False
                    self.controller.training_handler.go_to_training()
                    time.sleep(0.5)
                    if self.controller.check_should_stop():
                        return False
                    self.controller.training_handler.execute_training(best_training)
                    self.controller.log_message(f"Training: {best_training.upper()}")
                else:
                    if energy_percentage < MINIMUM_ENERGY_PERCENTAGE or best_training == "SHOULD_REST":
                        self.controller.rest_handler.execute_rest()
                        self.controller.log_message(f"No suitable training or low energy ({energy_percentage}%) - Resting")
                    else:
                        if results_training:
                            fallback_result = fallback_training(results_training, current_date)
                            if fallback_result:
                                best_key, score_info = fallback_result
                                if self.controller.check_should_stop():
                                    return False
                                self.controller.training_handler.go_to_training()
                                time.sleep(0.5)
                                if self.controller.check_should_stop():
                                    return False
                                self.controller.training_handler.execute_training(best_key)
                                self.controller.log_message(f"Fallback Training: {best_key.upper()} {score_info}")
                                return True

                        self.controller.rest_handler.execute_rest()
                        self.controller.log_message("No training options available - Resting")

                return True

        elif "G1 (no training)" in priority_strategy:
            g1_races = [race for race in available_races
                        if race_manager.extract_race_properties(race)['grade_type'] == 'g1']

            if g1_races:
                self.controller.log_message(f"G1 priority: Found {len(g1_races)} G1 races - Racing")
            else:
                self.controller.log_message("G1 priority: No G1 races found in available races")
                # No G1 races, proceed with normal training/rest logic
                self.controller.log_message("G1 priority: No G1 races, proceeding with normal training/rest logic")

                # Use the same training logic as above for consistency
                if not self.controller.training_handler.go_to_training():
                    return True

                if self.controller.check_should_stop():
                    return False

                time.sleep(0.5)
                results_training = self.controller.training_handler.check_all_training(energy_percentage)

                if self.controller.check_should_stop():
                    return False

                best_training = training_decision(
                    results_training,
                    energy_percentage,
                    strategy_settings,
                    current_date
                )

                if best_training and best_training != "SHOULD_REST":
                    if self.controller.check_should_stop():
                        return False
                    self.controller.training_handler.go_to_training()
                    time.sleep(0.5)
                    if self.controller.check_should_stop():
                        return False
                    self.controller.training_handler.execute_training(best_training)
                    self.controller.log_message(f"Training: {best_training.upper()}")
                else:
                    if energy_percentage < MINIMUM_ENERGY_PERCENTAGE or best_training == "SHOULD_REST":
                        self.controller.rest_handler.execute_rest()
                        self.controller.log_message(f"No suitable training or low energy ({energy_percentage}%) - Resting")
                    else:
                        if results_training:
                            fallback_result = fallback_training(results_training, current_date)
                            if fallback_result:
                                best_key, score_info = fallback_result
                                if self.controller.check_should_stop():
                                    return False
                                self.controller.training_handler.go_to_training()
                                time.sleep(0.5)
                                if self.controller.check_should_stop():
                                    return False
                                self.controller.training_handler.execute_training(best_key)
                                self.controller.log_message(f"Fallback Training: {best_key.upper()} {score_info}")
                                return True

                        self.controller.rest_handler.execute_rest()
                        self.controller.log_message("No training options available - Resting")

                return True

        # Attempt to race
        if self.controller.check_should_stop():
            return False

        race_found = self.controller.race_handler.start_race_flow(
            allow_continuous_racing=allow_continuous_racing)

        if race_found:
            return True
        else:
            # Race failed, click back button first then proceed with normal training/rest logic
            if self.controller.check_should_stop():
                return False
            self._click_back_button(f"{priority_strategy}: Race failed, going back to lobby")
            time.sleep(0.5)

            # Use the same training logic
            if not self.controller.training_handler.go_to_training():
                return True

            if self.controller.check_should_stop():
                return False

            time.sleep(0.5)
            results_training = self.controller.training_handler.check_all_training(energy_percentage)

            if self.controller.check_should_stop():
                return False

            best_training = training_decision(
                results_training,
                energy_percentage,
                strategy_settings,
                current_date
            )

            if best_training and best_training != "SHOULD_REST":
                if self.controller.check_should_stop():
                    return False
                self.controller.training_handler.go_to_training()
                time.sleep(0.5)
                if self.controller.check_should_stop():
                    return False
                self.controller.training_handler.execute_training(best_training)
                self.controller.log_message(f"Training: {best_training.upper()}")
            else:
                if energy_percentage < MINIMUM_ENERGY_PERCENTAGE or best_training == "SHOULD_REST":
                    self.controller.rest_handler.execute_rest()
                    self.controller.log_message(f"No suitable training or low energy ({energy_percentage}%) - Resting")
                else:
                    if results_training:
                        fallback_result = fallback_training(results_training, current_date)
                        if fallback_result:
                            best_key, score_info = fallback_result
                            if self.controller.check_should_stop():
                                return False
                            self.controller.training_handler.go_to_training()
                            time.sleep(0.5)
                            if self.controller.check_should_stop():
                                return False
                            self.controller.training_handler.execute_training(best_key)
                            self.controller.log_message(f"Fallback Training: {best_key.upper()} {score_info}")
                            return True

                    self.controller.rest_handler.execute_rest()
                    self.controller.log_message("No training options available - Resting")

            return True

    def _check_stop_conditions(self, game_state: Dict[str, Any], strategy_settings: Dict[str, Any], gui) -> bool:
        """Check if any stop conditions are met"""
        # Only check if stop conditions are enabled
        if not strategy_settings.get('enable_stop_conditions', False):
            return False

        current_date = game_state.get('current_date', {})
        absolute_day = current_date.get('absolute_day', 0)

        # Only apply stop conditions after day 24
        if absolute_day <= 24:
            return False

        # Check energy for need rest condition
        energy_percentage = game_state['energy_percentage']
        if strategy_settings.get('stop_on_need_rest', False):
            if energy_percentage < MINIMUM_ENERGY_PERCENTAGE:
                self.controller.log_message(f"Stop condition: Need rest detected after day 24 (Energy: {energy_percentage}%) - Stopping bot")
                gui.root.after(0, gui.stop_bot)
                return True

        # Check stop before summer (June)
        if strategy_settings.get('stop_before_summer', False):
            month_num = current_date.get('month_num', 0)
            if month_num == 6:  # June
                self.controller.log_message("Stop condition: Reached June (before summer) after day 24 - Stopping bot")
                gui.root.after(0, gui.stop_bot)
                return True

        # Check stop at specific month
        if strategy_settings.get('stop_at_month', False):
            target_month = strategy_settings.get('target_month', '')
            current_month = current_date.get('month', '')

            # Convert month names to compare properly
            month_mapping = {
                'Jan': 'January', 'Feb': 'February', 'Mar': 'March', 'Apr': 'April',
                'May': 'May', 'Jun': 'June', 'Jul': 'July', 'Aug': 'August',
                'Sep': 'September', 'Oct': 'October', 'Nov': 'November', 'Dec': 'December'
            }

            # Convert abbreviated month to full name for comparison
            full_current_month = month_mapping.get(current_month, current_month)

            if full_current_month == target_month:
                self.controller.log_message(f"Stop condition: Reached target month ({target_month}) after day 24 - Stopping bot")
                gui.root.after(0, gui.stop_bot)
                return True

        return False

    def _click_back_button(self, text=""):
        """Click back button with logging"""
        enhanced_click(
            "assets/buttons/back_btn.png",
            text=text,
            check_stop_func=self.controller.check_should_stop,
            check_window_func=self.controller.is_game_window_active,
            log_func=self.controller.log_message
        )


class CareerLobbyManager:
    """Manages career lobby detection and navigation"""

    def __init__(self, controller: BotController):
        self.controller = controller

    def verify_lobby_state(self, gui=None) -> bool:
        """Verify if currently in career lobby"""
        tazuna_hint = pyautogui.locateCenterOnScreen(
            "assets/ui/tazuna_hint.png",
            confidence=0.8,
            minSearchTime=0.2
        )

        if tazuna_hint is None:
            self.controller.log_message("Should be in career lobby.")

            if self.controller.increment_career_lobby_counter():
                if gui:
                    gui.root.after(0, gui.stop_bot)
                return False

            return False
        else:
            self.controller.reset_career_lobby_counter()
            return True

    def handle_debuff_status(self, gui=None) -> bool:
        """Handle character debuff status"""
        debuffed = pyautogui.locateOnScreen(
            "assets/buttons/infirmary_btn2.png",
            confidence=0.9,
            minSearchTime=1
        )

        if debuffed:
            if is_infirmary_active((debuffed.left, debuffed.top, debuffed.width, debuffed.height)):
                # Stop condition only applies after day 24
                if (gui and gui.get_current_settings().get('enable_stop_conditions', False) and
                        gui.get_current_settings().get('stop_on_infirmary', False)):
                    # Get current date info
                    from core.state import get_current_date_info
                    current_date = get_current_date_info()
                    absolute_day = current_date.get('absolute_day', 0) if current_date else 0

                    if absolute_day > 24:
                        self.controller.log_message("Stop condition: Infirmary needed after day 24 - Stopping bot")
                        gui.root.after(0, gui.stop_bot)
                        return True

                if self.controller.check_should_stop():
                    return False
                pyautogui.click(debuffed)
                self.controller.log_message("Character has debuff, go to infirmary instead.")
                return True

        return False


class StatusLogger:
    """Handles status logging and GUI updates"""

    def __init__(self, controller: BotController):
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
                    f"📍 Today's Races: {len(all_filtered_races)} matching filters (restricted)")
                for race in all_filtered_races[:3]:
                    race_props = race_manager.extract_race_properties(race)
                    self.controller.log_message(
                        f"  - {race['name']} ({race_props['grade_type'].upper()}, {race_props['track_type']}, {race_props['distance_type']})")
                if len(all_filtered_races) > 3:
                    self.controller.log_message(f"  ... and {len(all_filtered_races) - 3} more")
            else:
                self.controller.log_message("📍 Today's Races: None match current filters")
        else:
            if available_races:
                self.controller.log_message(f"📍 Today's Races: {len(available_races)} matching filters")
                for race in available_races:
                    race_props = race_manager.extract_race_properties(race)
                    self.controller.log_message(
                        f"  - {race['name']} ({race_props['grade_type'].upper()}, {race_props['track_type']}, {race_props['distance_type']})")
            else:
                self.controller.log_message("📍 Today's Races: None match current filters")

    def update_gui_status(self, gui, game_state: Dict[str, Any]):
        """Update GUI status displays"""
        if not gui:
            return

        if game_state['current_date']:
            gui.update_current_date(game_state['current_date'])

        gui.update_energy_display(game_state['energy_percentage'])


class MainExecutor:
    """Main executor class that orchestrates all bot operations"""

    def __init__(self):
        """Initialize the main executor"""
        self.controller = BotController()
        self.game_state_manager = GameStateManager(self.controller)
        self.event_handler = EventHandler(self.controller)
        self.decision_engine = DecisionEngine(self.controller)
        self.lobby_manager = CareerLobbyManager(self.controller)
        self.status_logger = StatusLogger(self.controller)

    def execute_single_iteration(self, race_manager, gui=None) -> bool:
        """Execute single iteration of main bot logic"""
        try:
            if self.controller.check_should_stop():
                return False

            # Priority 1: Handle UI elements first
            if self.event_handler.handle_ui_elements(gui):
                return True

            # Priority 2: Check if we're in career lobby
            if not self.lobby_manager.verify_lobby_state(gui):
                time.sleep(1)
                return True

            if self.controller.check_should_stop():
                return False

            time.sleep(2)

            # Handle debuff status (only if in lobby)
            if self.lobby_manager.handle_debuff_status(gui):
                return True

            if self.controller.check_should_stop():
                return False

            # Update game state (only if in lobby)
            game_state = self.game_state_manager.update_game_state()

            # Check if career is completed (only if in lobby)
            if self.game_state_manager.is_career_completed():
                return self._handle_career_completion(gui)

            if self.controller.check_should_stop():
                return False

            # Get strategy settings (only if in lobby)
            strategy_settings = self._get_strategy_settings(gui)

            # Update GUI status (only if in lobby)
            self.status_logger.update_gui_status(gui, game_state)

            # Log current status (only if in lobby)
            self.status_logger.log_current_status(game_state, strategy_settings, race_manager)

            if self.controller.check_should_stop():
                return False

            # Make training/racing decisions (only if in lobby)
            self.decision_engine.make_decision(game_state, strategy_settings, race_manager, gui)

            time.sleep(1)

            return True

        except Exception as e:
            self.controller.log_message(f"Error in main iteration: {e}")
            return False

    def _handle_career_completion(self, gui) -> bool:
        """Handle career completion scenario"""
        self.controller.log_message("🎉 CAREER COMPLETED! Finale Season detected.")

        if gui:
            gui.root.after(0, gui.stop_bot)
            gui.root.after(0, lambda: gui.log_message("🎉 Bot stopped automatically."))

        return False

    def _get_strategy_settings(self, gui) -> Dict[str, Any]:
        """Get strategy settings from GUI or defaults"""
        default_settings = {
            'minimum_mood': 'NORMAL',
            'priority_strategy': 'Train Score 2.5+',
            'allow_continuous_racing': True,
            'manual_event_handling': False,
            'enable_stop_conditions': False,
            'stop_on_infirmary': False,
            'stop_on_need_rest': False,
            'stop_on_low_mood': False,
            'stop_on_race_day': False,
            'stop_mood_threshold': 'BAD',
            'stop_before_summer': False,
            'stop_at_month': False,
            'target_month': 'June'
        }

        if gui:
            return gui.get_current_settings()
        return default_settings


# Global instances for backward compatibility
_main_executor = None
_global_controller = None


def initialize_executor():
    """Initialize the main executor"""
    global _main_executor, _global_controller
    if _main_executor is None:
        _main_executor = MainExecutor()
        _global_controller = _main_executor.controller


def get_controller() -> BotController:
    """Get the global controller instance"""
    global _global_controller
    if _global_controller is None:
        initialize_executor()
    return _global_controller


# Global functions for external access
def set_log_callback(callback: Callable[[str], None]):
    """Set the logging callback function"""
    controller = get_controller()
    controller.set_log_callback(callback)


def set_stop_flag(value: bool = True):
    """Set the global stop flag (called when F3 is pressed)"""
    controller = get_controller()
    controller.set_stop_flag(value)


def check_should_stop() -> bool:
    """Check if bot should stop due to F3 press"""
    controller = get_controller()
    return controller.check_should_stop()


def log_message(message: str):
    """Log message using global controller"""
    controller = get_controller()
    controller.log_message(message)


def career_lobby(gui=None):
    """Main career lobby function - entry point for bot execution"""
    global _main_executor

    if _main_executor is None:
        initialize_executor()

    _main_executor.controller.set_stop_flag(False)

    race_manager = RaceManager()

    if gui:
        race_manager = gui.race_manager

        while gui.is_running and not _main_executor.controller.should_stop:
            if not gui.is_running or _main_executor.controller.should_stop:
                break

            if not _main_executor.controller.is_game_window_active():
                gui.log_message("Waiting for game window to be active...")
                time.sleep(2)
                continue

            if not _main_executor.execute_single_iteration(race_manager, gui):
                time.sleep(1)
    else:
        while not _main_executor.controller.should_stop:
            if not _main_executor.execute_single_iteration(race_manager):
                time.sleep(1)


def focus_umamusume():
    """Focus Umamusume window for compatibility"""
    try:
        windows = gw.getWindowsWithTitle("Umamusume")
        if not windows:
            raise Exception("Umamusume not found.")

        win = windows[0]
        if win.isMinimized:
            win.restore()
        win.activate()
        win.maximize()
        time.sleep(0.5)
    except Exception as e:
        print(f"Error focusing Umamusume window: {e}")


# Export main classes for advanced usage
__all__ = [
    'BotController', 'GameStateManager', 'EventHandler', 'DecisionEngine',
    'CareerLobbyManager', 'StatusLogger', 'MainExecutor',
    'career_lobby', 'set_log_callback', 'set_stop_flag', 'check_should_stop',
    'log_message', 'focus_umamusume'
]