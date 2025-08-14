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
from core.logic import enhanced_training_decision
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

        # Cache for training results to avoid re-checking
        self.training_cache = {}
        self.training_cache_timestamp = 0
        self.training_cache_timeout = 30  # 30 seconds cache timeout

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

    def clear_training_cache(self):
        """Clear training results cache"""
        self.training_cache = {}
        self.training_cache_timestamp = 0

    def get_cached_training_results(self, energy_percentage: float) -> Optional[Dict]:
        """Get cached training results if still valid"""
        current_time = time.time()

        # Check if cache is still valid (within timeout period)
        if (current_time - self.training_cache_timestamp > self.training_cache_timeout):
            return None

        # Check if we have cached results for this energy level
        cache_key = f"energy_{int(energy_percentage)}"
        return self.training_cache.get(cache_key)

    def cache_training_results(self, energy_percentage: float, results: Dict):
        """Cache training results"""
        cache_key = f"energy_{int(energy_percentage)}"
        self.training_cache[cache_key] = results
        self.training_cache_timestamp = time.time()

class GameStateManager:
    """Manages current game state information"""

    def __init__(self, controller: BotController):
        self.controller = controller

    def update_game_state(self) -> Dict[str, Any]:
        """Update and return current game state"""
        try:
            self.current_state = {
                'mood': check_mood(),
                'turn': check_turn(),
                'year': check_current_year(),
                'criteria': check_criteria(),
                'energy_percentage': check_energy_percentage(),
                'current_date': get_current_date_info()
            }

            # Handle date parsing failure
            if self.current_state['current_date'] is None:
                self.current_state['current_date'] = self._get_fallback_date()

            return self.current_state

        except Exception as e:
            self.controller.log_message(f"[ERROR] Failed to update game state: {e}")
            return self._get_emergency_state()

    def _get_fallback_date(self) -> Dict[str, Any]:
        """Get fallback date when parsing fails"""
        self.controller.log_message("[ERROR] Date parsing failed, using safe fallback")
        return {
            'year': 'Classic',
            'absolute_day': 50,
            'is_pre_debut': False,
            'is_finale': False,
            'month': 'Unknown',
            'period': 'Unknown'
        }

    def _get_emergency_state(self) -> Dict[str, Any]:
        """Get emergency state when everything fails"""
        return {
            'mood': 'UNKNOWN',
            'turn': -1,
            'year': 'Unknown',
            'criteria': 'Unknown',
            'energy_percentage': 50,
            'current_date': self._get_fallback_date()
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
    """Handles game events and UI interactions"""

    def __init__(self, controller: BotController):
        self.controller = controller

    def handle_ui_elements(self, gui=None) -> bool:
        """Handle various UI elements and events"""
        # Handle manual events
        if self._handle_events(gui):
            return True

        # Handle other UI elements
        ui_elements = [
            ("assets/buttons/inspiration_btn.png", "Inspiration found."),
            ("assets/buttons/next_btn.png", ""),
            ("assets/buttons/cancel_btn.png", ""),
            ("assets/buttons/next2_btn.png", "")
        ]

        for element_path, message in ui_elements:
            if enhanced_click(
                    element_path,
                    minSearch=0.2,
                    text=message,
                    check_stop_func=self.controller.check_should_stop,
                    check_window_func=self.controller.is_game_window_active,
                    log_func=self.controller.log_message
            ):
                return True

        return False

    def _handle_events(self, gui=None) -> bool:
        """Handle event choices"""
        event_choice_found = pyautogui.locateCenterOnScreen(
            "assets/icons/event_choice_1.png",
            confidence=0.8,
            minSearchTime=0.2
        )

        if not event_choice_found:
            return False

        # Check if manual event handling is enabled
        manual_event_handling = False
        if gui:
            settings = gui.get_current_settings()
            manual_event_handling = settings.get('manual_event_handling', False)

        if manual_event_handling:
            return self._handle_manual_event(gui)
        else:
            return self._handle_automatic_event()

    def _handle_manual_event(self, gui) -> bool:
        """Handle manual event processing"""
        self.controller.log_message("🎭 EVENT DETECTED! Manual event handling enabled.")
        self.controller.log_message("⏳ Waiting for you to select event choice manually...")

        if gui:
            gui.root.after(0, gui.pause_bot)

        return self._wait_for_event_completion(gui)

    def _handle_automatic_event(self) -> bool:
        """Handle automatic event processing"""
        return enhanced_click(
            "assets/icons/event_choice_1.png",
            minSearch=0.2,
            text="Event found, automatically select top choice.",
            check_stop_func=self.controller.check_should_stop,
            check_window_func=self.controller.is_game_window_active,
            log_func=self.controller.log_message
        )

    def _wait_for_event_completion(self, gui=None, max_wait_time: int = 300) -> bool:
        """Wait for user to complete event manually"""
        start_time = time.time()

        while True:
            if gui and not gui.is_running:
                return False
            if self.controller.check_should_stop():
                return False

            time.sleep(2.0)

            # Check if event is still present
            event_still_present = pyautogui.locateCenterOnScreen(
                "assets/icons/event_choice_1.png",
                confidence=0.8,
                minSearchTime=0.2
            )

            if not event_still_present:
                # Check if back to main menu
                tazuna_hint = pyautogui.locateCenterOnScreen(
                    "assets/ui/tazuna_hint.png",
                    confidence=0.8,
                    minSearchTime=0.2
                )

                if tazuna_hint:
                    if gui and gui.is_paused:
                        gui.root.after(0, gui.pause_bot)
                    self.controller.log_message("✅ Event completed! Continuing bot...")
                    return True
                else:
                    # Check if event is progressing
                    next_btn = pyautogui.locateCenterOnScreen(
                        "assets/buttons/next_btn.png",
                        confidence=0.8,
                        minSearchTime=0.2
                    )
                    if next_btn:
                        continue

            # Timeout check
            if time.time() - start_time > max_wait_time:
                self.controller.log_message("⚠️ Event waiting timeout - resuming bot")
                if gui and gui.is_paused:
                    gui.root.after(0, gui.pause_bot)
                return True

            # Progress logging
            elapsed = time.time() - start_time
            if elapsed > 0 and int(elapsed) % 30 == 0:
                self.controller.log_message(f"⏳ Still waiting for event completion... ({int(elapsed)}s elapsed)")

class DecisionEngine:
    """Main decision engine for bot actions"""

    def __init__(self, controller: BotController):
        self.controller = controller

    def make_decision(self, game_state: Dict[str, Any], strategy_settings: Dict[str, Any],
                      race_manager, gui=None) -> bool:
        """Make main bot decision based on current state"""
        # Handle special scenarios first
        if self._handle_special_scenarios(game_state):
            return True

        # Handle mood requirements
        if self._handle_mood_requirements(game_state, strategy_settings):
            return True

        # Handle energy-based decisions
        return self._handle_energy_based_decisions(game_state, strategy_settings, race_manager)

    def _handle_special_scenarios(self, game_state: Dict[str, Any]) -> bool:
        """Handle special game scenarios"""
        # URA Finale
        if (game_state['year'] == "Finale Season" and
                game_state['turn'] == "Race Day"):
            return self.controller.race_handler.handle_ura_finale()

        # Regular Race Day
        if (game_state['turn'] == "Race Day" and
                game_state['year'] != "Finale Season"):
            self.controller.log_message("Race Day.")
            if self.controller.check_should_stop():
                return False
            return self.controller.race_handler.handle_race_day()

        return False

    def _handle_mood_requirements(self, game_state: Dict[str, Any],
                                  strategy_settings: Dict[str, Any]) -> bool:
        """Handle mood-based requirements"""
        mood = game_state['mood']
        current_date = game_state['current_date']

        mood_index = MOOD_LIST.index(mood) if mood in MOOD_LIST else 0
        minimum_mood_index = MOOD_LIST.index(strategy_settings.get('minimum_mood', 'NORMAL'))

        if mood_index < minimum_mood_index:
            # Check if in restricted periods for recreation
            is_junior_year = current_date and current_date.get('absolute_day', 0) < 24

            if not is_junior_year:
                self.controller.log_message(
                    f"Mood is {mood}, below minimum {strategy_settings.get('minimum_mood', 'NORMAL')}. "
                    "Trying recreation to increase mood"
                )
                if self.controller.check_should_stop():
                    return False
                self.controller.rest_handler.execute_recreation()
                return True

        return False

    def _handle_energy_based_decisions(self, game_state: Dict[str, Any],
                                       strategy_settings: Dict[str, Any],
                                       race_manager) -> bool:
        """Handle energy-based decision logic"""
        energy_percentage = game_state['energy_percentage']
        current_date = game_state['current_date']

        # Critical energy handling
        if energy_percentage < CRITICAL_ENERGY_PERCENTAGE:
            return self._handle_critical_energy(current_date, race_manager, strategy_settings)

        # Medium energy handling
        elif energy_percentage < MINIMUM_ENERGY_PERCENTAGE:
            return self._handle_medium_energy(current_date, race_manager, strategy_settings)

        # Normal energy handling
        else:
            return self._handle_normal_energy(game_state, strategy_settings, race_manager)

    def _handle_critical_energy(self, current_date: Dict[str, Any], race_manager,
                                strategy_settings: Dict[str, Any]) -> bool:
        """Handle critical energy scenarios"""
        should_race, available_races = race_manager.should_race_today(current_date)
        allow_continuous_racing = strategy_settings.get('allow_continuous_racing', True)

        if should_race:
            self.controller.log_message(
                f"Critical energy ({CRITICAL_ENERGY_PERCENTAGE}%) - "
                f"found {len(available_races)} matching races. Racing to avoid training."
            )

            if self.controller.check_should_stop():
                return False

            race_found = self.controller.race_handler.start_race_flow(
                allow_continuous_racing=allow_continuous_racing
            )

            if race_found:
                return True
            else:
                if not self.controller.check_should_stop():
                    enhanced_click(
                        "assets/buttons/back_btn.png",
                        text="Race not found. Critical energy - will rest.",
                        check_stop_func=self.controller.check_should_stop,
                        check_window_func=self.controller.is_game_window_active,
                        log_func=self.controller.log_message
                    )
                    time.sleep(0.5)
                    self.controller.rest_handler.execute_rest()
                    self.controller.log_message("Critical energy - Resting")
                return True
        else:
            if self.controller.check_should_stop():
                return False
            self.controller.rest_handler.execute_rest()
            self.controller.log_message("Critical energy - Resting")
            return True

    def _handle_medium_energy(self, current_date: Dict[str, Any], race_manager,
                              strategy_settings: Dict[str, Any]) -> bool:
        """Handle medium energy scenarios"""
        should_race, available_races = race_manager.should_race_today(current_date)
        allow_continuous_racing = strategy_settings.get('allow_continuous_racing', True)

        if should_race:
            self.controller.log_message(
                f"Medium energy ({MINIMUM_ENERGY_PERCENTAGE}%) but found {len(available_races)} "
                "matching races for today. Racing instead of training."
            )

            if self.controller.check_should_stop():
                return False

            race_found = self.controller.race_handler.start_race_flow(
                allow_continuous_racing=allow_continuous_racing
            )

            if race_found:
                return True
            else:
                if not self.controller.check_should_stop():
                    enhanced_click(
                        "assets/buttons/back_btn.png",
                        text="Matching race not found in game. Medium energy - will check WIT training.",
                        check_stop_func=self.controller.check_should_stop,
                        check_window_func=self.controller.is_game_window_active,
                        log_func=self.controller.log_message
                    )
                    time.sleep(0.5)

        # Check medium energy WIT training
        return self._check_medium_energy_training(current_date)

    def _handle_normal_energy(self, game_state: Dict[str, Any],
                              strategy_settings: Dict[str, Any], race_manager) -> bool:
        """Handle normal energy scenarios"""
        current_date = game_state['current_date']
        priority_strategy = strategy_settings.get('priority_strategy', 'Train Score 2.5+')
        allow_continuous_racing = strategy_settings.get('allow_continuous_racing', True)

        should_race, available_races = race_manager.should_race_today(current_date)

        if should_race and available_races:
            # Check race priority
            should_race_immediately, reason = self.controller.race_handler.should_prioritize_race(
                priority_strategy, available_races, race_manager
            )

            if should_race_immediately:
                self.controller.log_message(reason + " - Racing immediately")
                if self.controller.check_should_stop():
                    return False

                # Use enhanced race flow with grade priority
                race_found = self._execute_prioritized_race(available_races, race_manager, allow_continuous_racing, priority_strategy)

                if race_found:
                    return True
                else:
                    if not self.controller.check_should_stop():
                        enhanced_click(
                            "assets/buttons/back_btn.png",
                            text="Matching race not found. Proceeding to training.",
                            check_stop_func=self.controller.check_should_stop,
                            check_window_func=self.controller.is_game_window_active,
                            log_func=self.controller.log_message
                        )
                        time.sleep(0.5)

        else:
            # Log racing restrictions
            if DateManager.is_restricted_period(current_date):
                if current_date.get('is_pre_debut', False):
                    self.controller.log_message("In Pre-Debut period. No racing allowed.")
                elif current_date['absolute_day'] <= 16:
                    self.controller.log_message("In restricted racing period (Career days 1-16). No racing allowed.")
                else:
                    self.controller.log_message("In restricted racing period (Jul-Aug). No racing allowed.")

        # Proceed to normal training
        return self._check_normal_training(game_state, strategy_settings, race_manager)

    def _execute_prioritized_race(self, available_races, race_manager, allow_continuous_racing, priority_strategy):
        """Execute race with proper grade priority checking"""
        if self.controller.check_should_stop():
            return False

        # Click races button first
        if not enhanced_click(
                "assets/buttons/races_btn.png",
                minSearch=10,
                check_stop_func=self.controller.check_should_stop,
                check_window_func=self.controller.is_game_window_active,
                log_func=self.controller.log_message
        ):
            return False

        if self.controller.check_should_stop():
            return False

        # Check for OK button (indicates more than 3 races recently)
        ok_btn_found = False
        if not self.controller.check_should_stop():
            ok_btn_found = enhanced_click(
                "assets/buttons/ok_btn.png",
                minSearch=0.7,
                check_stop_func=self.controller.check_should_stop,
                check_window_func=self.controller.is_game_window_active,
                log_func=self.controller.log_message
            )

        if ok_btn_found and not allow_continuous_racing:
            self.controller.log_message("Continuous racing disabled - canceling race due to recent racing limit")
            if not self.controller.check_should_stop():
                enhanced_click(
                    "assets/buttons/cancel_btn.png",
                    minSearch=0.2,
                    check_stop_func=self.controller.check_should_stop,
                    check_window_func=self.controller.is_game_window_active,
                    log_func=self.controller.log_message
                )
            return False

        if self.controller.check_should_stop():
            return False

        # Determine grade priority based on strategy
        prioritize_g1 = "G1" in priority_strategy
        prioritize_g2 = "G2" in priority_strategy

        # Select race with enhanced grade checking
        race_found = self.controller.race_handler.select_race(
            prioritize_g1=prioritize_g1,
            prioritize_g2=prioritize_g2
        )

        if not race_found or self.controller.check_should_stop():
            self.controller.log_message("No matching race found with required grade priority.")
            return False

        # Prepare for race
        if not self.controller.race_handler.prepare_race() or self.controller.check_should_stop():
            return False

        time.sleep(1)

        # Handle post-race
        if not self.controller.race_handler.handle_after_race() or self.controller.check_should_stop():
            return False

        return True

    def _check_medium_energy_training(self, current_date: Dict[str, Any]) -> bool:
        """Check medium energy WIT training with proper menu handling"""
        if self.controller.check_should_stop():
            return False

        # Check for cached training results first
        cached_results = self.controller.get_cached_training_results(MINIMUM_ENERGY_PERCENTAGE - 1)

        if cached_results:
            self.controller.log_message("Using cached training results for medium energy check")
            results_training = cached_results
        else:
            # Go to training
            if not self.controller.training_handler.go_to_training():
                return True

            if self.controller.check_should_stop():
                return False

            # Check WIT training only - this will automatically exit training menu
            time.sleep(0.5)
            results_training = self.controller.training_handler.check_all_training(MINIMUM_ENERGY_PERCENTAGE - 1)

            # Cache the results
            self.controller.cache_training_results(MINIMUM_ENERGY_PERCENTAGE - 1, results_training)

        if self.controller.check_should_stop():
            return False

        # Use medium energy logic
        from core.logic import medium_energy_wit_training
        best_training = medium_energy_wit_training(results_training, current_date)

        if best_training:
            # Execute WIT training - need to go to training menu again
            if self.controller.check_should_stop():
                return False

            self.controller.training_handler.go_to_training()
            time.sleep(0.5)

            if self.controller.check_should_stop():
                return False

            self.controller.training_handler.execute_training(best_training)
            self.controller.log_message(f"Training: {best_training.upper()}")
        else:
            # No suitable WIT training - just rest (training menu already exited)
            self.controller.log_message("Medium energy - No suitable WIT training found. Resting.")
            self.controller.rest_handler.execute_rest()

        return True

    def _check_normal_training(self, game_state: Dict[str, Any],
                               strategy_settings: Dict[str, Any], race_manager) -> bool:
        """Check normal energy training with cache optimization"""
        if self.controller.check_should_stop():
            return False

        energy_percentage = game_state['energy_percentage']

        # Check for cached training results first
        cached_results = self.controller.get_cached_training_results(energy_percentage)

        if cached_results:
            self.controller.log_message("Using cached training results")
            results_training = cached_results
        else:
            # Go to training
            if not self.controller.training_handler.go_to_training():
                self.controller.log_message("Training button is not found.")
                return True

            if self.controller.check_should_stop():
                return False

            # Check all training
            time.sleep(0.5)
            results_training = self.controller.training_handler.check_all_training(energy_percentage)

            # Cache the results
            self.controller.cache_training_results(energy_percentage, results_training)

        if self.controller.check_should_stop():
            return False

        # Make training decision
        best_training = enhanced_training_decision(
            results_training,
            energy_percentage,
            strategy_settings,
            game_state['current_date']
        )

        if best_training:
            # Execute selected training
            if self.controller.check_should_stop():
                return False

            self.controller.training_handler.go_to_training()
            time.sleep(0.5)

            if self.controller.check_should_stop():
                return False

            self.controller.training_handler.execute_training(best_training)
            self.controller.log_message(f"Training: {best_training.upper()}")
        else:
            # No suitable training - try racing or rest as fallback
            return self._handle_no_training_fallback(game_state, strategy_settings, race_manager, results_training)

        return True

    def _handle_no_training_fallback(self, game_state: Dict[str, Any],
                                     strategy_settings: Dict[str, Any], race_manager, training_results: Dict = None) -> bool:
        """Handle fallback when no suitable training is found with cached results"""
        priority_strategy = strategy_settings.get('priority_strategy', 'Train Score 2.5+')
        current_date = game_state['current_date']
        energy_percentage = game_state['energy_percentage']
        allow_continuous_racing = strategy_settings.get('allow_continuous_racing', True)

        self.controller.log_message(f"No training meets {priority_strategy} strategy requirements")

        # Try racing as first priority fallback
        if current_date:
            should_race, available_races = race_manager.should_race_today(current_date)

            if should_race:
                self.controller.log_message(f"Strategy fallback: Attempting race from {len(available_races)} available races.")
                if self.controller.check_should_stop():
                    return False

                # Use enhanced race flow with grade priority
                prioritize_g1 = "G1" in priority_strategy
                prioritize_g2 = "G2" in priority_strategy
                race_found = self._execute_prioritized_race(available_races, race_manager, allow_continuous_racing, priority_strategy)

                if race_found:
                    self.controller.log_message(f"Strategy fallback: Race completed successfully")
                    return True
                else:
                    if not self.controller.check_should_stop():
                        enhanced_click(
                            "assets/buttons/back_btn.png",
                            text="Race not found in strategy fallback.",
                            check_stop_func=self.controller.check_should_stop,
                            check_window_func=self.controller.is_game_window_active,
                            log_func=self.controller.log_message
                        )
                        time.sleep(0.5)

        if self.controller.check_should_stop():
            return False

        # Only use training fallback if energy is below minimum threshold OR no races available
        from utils.constants import MINIMUM_ENERGY_PERCENTAGE

        if energy_percentage < MINIMUM_ENERGY_PERCENTAGE:
            self.controller.log_message(f"Energy is low ({energy_percentage}% < {MINIMUM_ENERGY_PERCENTAGE}%) - Resting")
            self.controller.rest_handler.execute_rest()
        else:
            # Try any available training as final fallback only if energy is good AND no races
            should_race, available_races = race_manager.should_race_today(current_date) if current_date else (False, [])

            if not should_race:  # Only try training fallback if no races available
                self.controller.log_message(f"No races available and energy is good ({energy_percentage}%) - Looking for any available training as final fallback")

                # Use cached training results if available, otherwise get fresh results
                if training_results is None:
                    # Go to training and check all available options
                    if not self.controller.training_handler.go_to_training():
                        self.controller.log_message("Training button not found - Resting as final fallback")
                        self.controller.rest_handler.execute_rest()
                        return True

                    time.sleep(0.5)

                    # Check all training without energy restrictions
                    training_results = self.controller.training_handler.check_all_training(100)

                if self.controller.check_should_stop():
                    return False

                # Use fallback logic to find any training
                from core.logic import most_support_card
                fallback_training = most_support_card(training_results, current_date)

                if fallback_training:
                    self.controller.log_message(f"Found fallback training: {fallback_training.upper()}")

                    # Execute the fallback training
                    if not self.controller.check_should_stop():
                        self.controller.training_handler.go_to_training()
                        time.sleep(0.5)
                        self.controller.training_handler.execute_training(fallback_training)
                        self.controller.log_message(f"Training: {fallback_training.upper()}")
                else:
                    self.controller.log_message("No fallback training available - Resting")
                    enhanced_click(
                        "assets/buttons/back_btn.png",
                        check_stop_func=self.controller.check_should_stop,
                        check_window_func=self.controller.is_game_window_active,
                        log_func=self.controller.log_message
                    )
                    time.sleep(0.5)
                    self.controller.rest_handler.execute_rest()
            else:
                # Has races but racing failed - just rest
                self.controller.log_message(f"Racing failed but races are available - Resting to preserve energy")
                self.controller.rest_handler.execute_rest()

        return True
    
class CareerLobbyManager:
    """Manages career lobby detection and navigation"""

    def __init__(self, controller: BotController):
        self.controller = controller

    def verify_lobby_state(self, gui=None) -> bool:
        """Verify we're in the career lobby"""
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

            time.sleep(1)
            return True
        else:
            self.controller.reset_career_lobby_counter()
            # Clear training cache when returning to lobby to ensure fresh results
            self.controller.clear_training_cache()
            return True

    def handle_debuff_status(self) -> bool:
        """Handle character debuff status"""
        debuffed = pyautogui.locateOnScreen(
            "assets/buttons/infirmary_btn2.png",
            confidence=0.9,
            minSearchTime=1
        )

        if debuffed and is_infirmary_active((debuffed.left, debuffed.top, debuffed.width, debuffed.height)):
            if self.controller.check_should_stop():
                return False

            from core.click_handler import random_click_in_region
            random_click_in_region(debuffed.left, debuffed.top, debuffed.width, debuffed.height)
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
        # self.controller.log_message(f"Turn: {game_state['turn']}")
        self.controller.log_message(f"Energy: {game_state['energy_percentage']}%")
        self.controller.log_message(f"Strategy: {strategy_settings.get('priority_strategy', 'Train Score 2.5+')}")

        if strategy_settings.get('manual_event_handling', False):
            self.controller.log_message("Manual Events: Enabled")

        self._log_date_and_race_info(game_state['current_date'], race_manager)

    def _log_date_and_race_info(self, current_date: Dict[str, Any], race_manager):
        """Log current date and race information"""
        if not current_date:
            return

        # Log current date
        if current_date.get('is_finale', False):
            self.controller.log_message("Current Date: Finale Season (Career Completed)")
        elif current_date.get('is_pre_debut', False):
            self.controller.log_message(
                f"Current Date: {current_date['year']} Year Pre-Debut "
                f"(Day {current_date['absolute_day']}/72)"
            )
        else:
            self.controller.log_message(
                f"Current Date: {current_date['year']} {current_date['month']} "
                f"{current_date['period']} (Day {current_date['absolute_day']}/72)"
            )

        # Log race information
        race_status = self.controller.race_handler.get_race_status_info(race_manager, current_date)
        self.controller.race_handler.log_race_status(race_status)

    def update_gui_status(self, gui, game_state: Dict[str, Any]):
        """Update GUI with current status"""
        if not gui:
            return

        if game_state['current_date']:
            gui.update_current_date(game_state['current_date'])

        gui.update_energy_display(game_state['energy_percentage'])

class MainExecutor:
    """Main executor class that coordinates all components"""

    def __init__(self):
        """Initialize the main executor"""
        self.controller = BotController()
        self.game_state_manager = GameStateManager(self.controller)
        self.event_handler = EventHandler(self.controller)
        self.decision_engine = DecisionEngine(self.controller)
        self.lobby_manager = CareerLobbyManager(self.controller)
        self.status_logger = StatusLogger(self.controller)

    def execute_single_iteration(self, race_manager, gui=None) -> bool:
        """Execute a single iteration of the main loop"""
        try:
            if self.controller.check_should_stop():
                return False

            # Handle events and UI interactions
            if self.event_handler.handle_ui_elements(gui):
                return True

            # Verify we're in career lobby
            if not self.lobby_manager.verify_lobby_state(gui):
                return True

            if self.controller.check_should_stop():
                return False

            time.sleep(1)

            # Handle debuff status
            if self.lobby_manager.handle_debuff_status():
                return True

            if self.controller.check_should_stop():
                return False

            # Update game state
            game_state = self.game_state_manager.update_game_state()

            # Check if career is completed
            if self.game_state_manager.is_career_completed():
                return self._handle_career_completion(gui)

            if self.controller.check_should_stop():
                return False

            # Get strategy settings
            strategy_settings = self._get_strategy_settings(gui)

            # Update GUI status
            self.status_logger.update_gui_status(gui, game_state)

            # Log current status
            self.status_logger.log_current_status(game_state, strategy_settings, race_manager)

            if self.controller.check_should_stop():
                return False

            # Make main decision
            self.decision_engine.make_decision(game_state, strategy_settings, race_manager, gui)

            time.sleep(1)
            return True

        except Exception as e:
            self.controller.log_message(f"Error in main iteration: {e}")
            return False

    def _handle_career_completion(self, gui) -> bool:
        """Handle career completion scenario"""
        self.controller.log_message("🎉 CAREER COMPLETED! Finale Season detected.")
        self.controller.log_message("🎊 Congratulations! Your Uma Musume has finished their career!")
        self.controller.log_message("🏆 Bot will now stop automatically.")

        if gui:
            gui.root.after(0, gui.stop_bot)
            gui.root.after(0, lambda: gui.log_message("🎉 Career completed! Bot stopped automatically."))

        return False

    def _get_strategy_settings(self, gui) -> Dict[str, Any]:
        """Get strategy settings from GUI or defaults"""
        default_settings = {
            'minimum_mood': 'NORMAL',
            'priority_strategy': 'Train Score 2.5+',
            'allow_continuous_racing': True,
            'manual_event_handling': False
        }

        if gui:
            return gui.get_current_settings()
        return default_settings

# Global instances and functions for backward compatibility
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

    # Initialize if needed
    if _main_executor is None:
        initialize_executor()

    # Reset stop flag when starting
    _main_executor.controller.set_stop_flag(False)

    # Initialize race manager
    race_manager = RaceManager()

    # Check if running with GUI
    if gui:
        race_manager = gui.race_manager

        while gui.is_running and not _main_executor.controller.should_stop:
            # Check if paused
            while gui.is_paused and gui.is_running and not _main_executor.controller.should_stop:
                time.sleep(0.1)

            if not gui.is_running or _main_executor.controller.should_stop:
                break

            # Check if game window is active
            if not _main_executor.controller.is_game_window_active():
                gui.log_message("Waiting for game window to be active...")
                time.sleep(2)
                continue

            # Run one iteration of the main loop
            if not _main_executor.execute_single_iteration(race_manager, gui):
                time.sleep(1)
    else:
        # Original standalone mode
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

# Individual handler access for backward compatibility
def get_training_handler():
    """Get training handler instance"""
    return get_controller().training_handler

def get_race_handler():
    """Get race handler instance"""
    return get_controller().race_handler

def get_rest_handler():
    """Get rest handler instance"""
    return get_controller().rest_handler

# Legacy function wrappers for backward compatibility
def go_to_training():
    """Legacy wrapper for go_to_training"""
    return get_training_handler().go_to_training()

def check_training(energy_percentage=100):
    """Legacy wrapper for check_training"""
    return get_training_handler().check_all_training(energy_percentage)

def do_train(training_type):
    """Legacy wrapper for do_train"""
    return get_training_handler().execute_training(training_type)

def do_race(prioritize_g1=False, allow_continuous_racing=True):
    """Legacy wrapper for do_race"""
    return get_race_handler().start_race_flow(prioritize_g1, allow_continuous_racing)

def race_day():
    """Legacy wrapper for race_day"""
    return get_race_handler().handle_race_day()

def do_rest():
    """Legacy wrapper for do_rest"""
    return get_rest_handler().execute_rest()

def do_recreation():
    """Legacy wrapper for do_recreation"""
    return get_rest_handler().execute_recreation()

def is_game_window_active():
    """Legacy wrapper for is_game_window_active"""
    return get_controller().is_game_window_active()

# Enhanced error handling and diagnostics
def get_system_status() -> Dict[str, Any]:
    """Get comprehensive system status for debugging"""
    controller = get_controller()

    return {
        'controller_initialized': controller is not None,
        'should_stop': controller.should_stop if controller else False,
        'career_lobby_attempts': controller.career_lobby_attempts if controller else 0,
        'game_window_active': controller.is_game_window_active() if controller else False,
        'handlers_initialized': {
            'training': hasattr(controller, 'training_handler') if controller else False,
            'race': hasattr(controller, 'race_handler') if controller else False,
            'rest': hasattr(controller, 'rest_handler') if controller else False
        }
    }

def reset_system():
    """Reset the entire system (for debugging)"""
    global _main_executor, _global_controller
    _main_executor = None
    _global_controller = None
    initialize_executor()

# Export main classes for advanced usage
__all__ = [
    'BotController', 'GameStateManager', 'EventHandler', 'DecisionEngine',
    'CareerLobbyManager', 'StatusLogger', 'MainExecutor',
    'career_lobby', 'set_log_callback', 'set_stop_flag', 'check_should_stop',
    'log_message', 'focus_umamusume', 'get_system_status', 'reset_system'
]