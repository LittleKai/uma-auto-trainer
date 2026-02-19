import pyautogui
import time
import json
import pygetwindow as gw
from typing import Dict, Optional, Callable, Any

pyautogui.useImageNotFoundException(False)

# Import handlers
from core.training_handler import TrainingHandler
from core.race_handler import RaceHandler
from core.rest_handler import RestHandler
from core.event_handler import EventChoiceHandler
from core.click_handler import enhanced_click

# Import core systems
from core.state import (
    check_turn, check_mood, check_current_year, check_criteria,
    get_current_date_info, check_energy_percentage, detect_finale_stage
)
from core.logic import training_decision, fallback_training
from core.recognizer import is_infirmary_active
from core.race_manager import RaceManager, DateManager
from utils.constants import (
    MOOD_LIST, MINIMUM_ENERGY_PERCENTAGE, CRITICAL_ENERGY_PERCENTAGE,
    MAX_CAREER_LOBBY_ATTEMPTS
)

# Import helper classes
from core.execute_helpers import (
    EventHandler, CareerLobbyManager, StatusLogger
)


class BotController:
    """Main bot controller that orchestrates all operations"""

    def __init__(self):
        """Initialize the bot controller"""
        self.should_stop = False
        self.career_lobby_attempts = 0
        self.log_callback = None
        self.window_inactive_start_time = None

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

        self.event_choice_handler = EventChoiceHandler(
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
            return True
        return False

    def is_game_window_active(self) -> bool:
        """Check if Umamusume window is currently active with timeout monitoring"""
        try:
            windows = gw.getWindowsWithTitle("Umamusume")
            is_active = windows and windows[0].isActive

            # Track inactive time
            current_time = time.time()

            if not is_active:
                if self.window_inactive_start_time is None:
                    self.window_inactive_start_time = current_time
                elif current_time - self.window_inactive_start_time >= 120:  # 2 minutes
                    self.log_message("[ERROR] Game window inactive for 2 minutes - Stopping bot")
                    self.set_stop_flag(True)
                    return False
            else:
                self.window_inactive_start_time = None

            return is_active
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
            self.career_lobby_attempts = 0
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
            energy_percentage, energy_max = check_energy_percentage(True)
            print(f'energy: {energy_percentage} - {energy_max}')
            current_date = get_current_date_info()

            if current_date is None:
                self.controller.log_message("[ERROR] Date parsing failed, using safe fallback behavior")
                current_date = {
                    'year': 'Classic',
                    'absolute_day': 50,
                    'is_pre_debut': False,
                    'is_finale': False
                }

            # Check CRITERIA_REGION for Finale stage detection
            if year != "Finale Season":
                finale_day = detect_finale_stage()
                if finale_day is not None:
                    print(f"[INFO] Finale stage detected via CRITERIA_REGION: Day {finale_day}")
                    year = "Finale Season"
                    current_date = {
                        'year': 'Finale Season',
                        'month': 'Season',
                        'period': 'End',
                        'day': 1,
                        'absolute_day': finale_day,
                        'month_num': 13,
                        'is_pre_debut': False,
                        'is_finale': True
                    }
            else:
                # Year is already Finale Season, refine absolute_day from CRITERIA_REGION
                finale_day = detect_finale_stage()
                if finale_day is not None:
                    current_date['absolute_day'] = finale_day
                    print(f"[INFO] Finale stage refined via CRITERIA_REGION: Day {finale_day}")

            self.current_state = {
                'mood': mood,
                'turn': turn,
                'year': year,
                'energy_percentage': energy_percentage,
                'energy_max': energy_max,
                'current_date': current_date
            }

            return self.current_state

        except Exception as e:
            self.controller.log_message(f"Error in game state update: {e}")
            return {
                'mood': 'UNKNOWN',
                'turn': -1,
                'year': 'Unknown',
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


class DecisionEngine:
    """Makes training and racing decisions based on game state"""

    def __init__(self, controller: BotController):
        self.controller = controller
        self.date_turn = {}

    def _stopped(self) -> bool:
        """Check if bot should stop"""
        return self.controller.check_should_stop()

    def _log(self, message: str):
        """Log message via controller"""
        self.controller.log_message(message)

    def _stop_bot(self, gui, message: str) -> bool:
        """Log message, stop bot via GUI, and return False"""
        self._log(message)
        if gui:
            gui.root.after(0, gui.stop_bot)
        return False

    def _navigate_and_train(self, training_key: str, label: str = "Training") -> bool:
        """Navigate to training screen, execute training, and log. Returns True on success, False if stopped."""
        if self._stopped():
            return False
        self.controller.training_handler.go_to_training()
        time.sleep(0.5)
        if self._stopped():
            return False
        self.controller.training_handler.execute_training(training_key)
        self._log(f"{label}: {training_key.upper()}")
        return True

    def _try_race_or_rest(self, allow_continuous_racing: bool, energy_percentage: int,
                          strategy_settings: Dict[str, Any], current_date: Dict[str, Any],
                          gui=None, back_log: str = "") -> bool:
        """Try to race; if race not found, click back and rest. Returns True."""
        race_found = self.controller.race_handler.start_race_flow(
            allow_continuous_racing=allow_continuous_racing)
        if race_found:
            return True
        if not self._stopped():
            self._click_back_button(back_log)
            time.sleep(0.5)
            self._handle_rest_case(energy_percentage, strategy_settings, current_date, gui,
                                   click_back=False, click_log="")
        return True

    def _try_race_or_training_fallback(self, allow_continuous_racing: bool, energy_percentage: int,
                                       energy_max: int, strategy_settings: Dict[str, Any],
                                       current_date: Dict[str, Any], race_manager,
                                       gui=None, back_log: str = "") -> bool:
        """Try to race; if race not found, click back and fall through to training flow."""
        race_found = self.controller.race_handler.start_race_flow(
            allow_continuous_racing=allow_continuous_racing)
        if race_found:
            return True
        if self._stopped():
            return False
        self._click_back_button(back_log)
        time.sleep(0.5)
        return self._execute_training_flow(energy_percentage, energy_max, strategy_settings,
                                           current_date, race_manager, gui)

    def _execute_training_flow(self, energy_percentage: int, energy_max: int, strategy_settings: Dict[str, Any],
                               current_date: Dict[str, Any], race_manager, gui=None) -> bool:
        """Execute complete training flow: check options, make decision, execute training or rest"""
        if not self.controller.training_handler.go_to_training():
            print('not go_to_training')
            return True

        if self._stopped():
            return False

        time.sleep(0.5)
        results_training, current_stats = self.controller.training_handler.check_all_training(energy_percentage, energy_max)

        if self._stopped():
            return False

        best_training = training_decision(
            results_training,
            energy_percentage, energy_max,
            strategy_settings,
            current_date,
            current_stats=current_stats
        )
        print(f'best_training: {best_training}')
        return self._handle_training_decision(
            best_training, results_training, energy_percentage,
            strategy_settings, current_date, race_manager, gui,
            current_stats=current_stats
        )

    def _handle_training_decision(self, best_training: str, results_training: Dict,
                                  energy_percentage: int, strategy_settings: Dict[str, Any],
                                  current_date: Dict[str, Any], race_manager, gui=None,
                                  current_stats=None) -> bool:
        """Handle the training decision result - execute training, rest, or race"""
        allow_continuous_racing = strategy_settings.get('allow_continuous_racing', True)

        if best_training and best_training not in ["SHOULD_REST", "NO_TRAINING", "STRATEGY_NOT_MET"]:
            return self._execute_selected_training(best_training)

        # SHOULD_REST: energy shortage with low scores - try race first, then rest (no fallback train)
        if best_training == "SHOULD_REST":
            return self._handle_should_rest(
                energy_percentage, strategy_settings, current_date,
                race_manager, gui
            )

        # best_training is None or STRATEGY_NOT_MET - no suitable training found
        return self._handle_no_suitable_training(
            results_training, energy_percentage, strategy_settings,
            current_date, race_manager, gui,
            current_stats=current_stats
        )

    def _execute_selected_training(self, best_training: str) -> bool:
        """Execute the selected training"""
        return self._navigate_and_train(best_training)

    def _handle_should_rest(self, energy_percentage: int, strategy_settings: Dict[str, Any],
                            current_date: Dict[str, Any], race_manager, gui=None) -> bool:
        """Handle SHOULD_REST: check race first, then rest if no race (no fallback training)"""
        allow_continuous_racing = strategy_settings.get('allow_continuous_racing', True)
        priority_strategy = strategy_settings.get('priority_strategy', 'Train Score 2.5+')
        is_pre_debut = current_date and current_date.get('absolute_day', 0) <= 16

        # Try race first (unless pre-debut)
        if "Train Score" in priority_strategy and not is_pre_debut:
            should_race, available_races = race_manager.should_race_today(current_date)

            if should_race and available_races:
                self._log(f"Energy shortage: No suitable training, but found {len(available_races)} matching races - Racing instead")

                if self._stopped():
                    return False

                race_found = self.controller.race_handler.start_race_flow(
                    allow_continuous_racing=allow_continuous_racing
                )

                if race_found:
                    return True
                else:
                    if self._stopped():
                        return False
                    self._click_back_button("Race not found in game, resting instead")
                    time.sleep(0.5)

        # No race available or race failed - rest
        return self._handle_rest_case(energy_percentage, strategy_settings, current_date, gui)

    def _handle_rest_case(self, energy_percentage: int, strategy_settings: Dict[str, Any],
                          current_date: Dict[str, Any], gui=None, click_back=False, click_log="") -> bool:
        """Handle the case when bot should rest"""

        # Stop condition only applies after day 24
        if (strategy_settings.get('enable_stop_conditions', False) and strategy_settings.get('stop_on_need_rest', False)
            and current_date and current_date.get('absolute_day', 0) > 24) and self.date_turn != "Race Day":
            self._click_back_button("")
            return self._stop_bot(gui, "Stop condition: Need rest detected - Stopping bot")

        if energy_percentage < MINIMUM_ENERGY_PERCENTAGE:
            self._log(f"Low energy ({energy_percentage}%) - Resting")
        else:
            self._log(
                f"Medium energy ({energy_percentage}%) with low training scores - Resting instead of inefficient training")

        if self._stopped():
            return False

        if click_back:
            self._click_back_button(click_log)
            time.sleep(0.5)

        strategy_context = strategy_settings.get('priority_strategy', '')
        self.controller.rest_handler.execute_rest(strategy_context=strategy_context)
        return True

    def _handle_no_suitable_training(self, results_training: Dict, energy_percentage: int,
                                     strategy_settings: Dict[str, Any], current_date: Dict[str, Any],
                                     race_manager, gui=None, current_stats=None) -> bool:
        """Handle when no suitable training found - check race first, then fallback training or rest"""
        is_pre_debut = current_date and current_date.get('absolute_day', 0) <= 16
        priority_strategy = strategy_settings.get('priority_strategy', 'Train Score 2.5+')
        allow_continuous_racing = strategy_settings.get('allow_continuous_racing', True)

        if is_pre_debut:
            self._log("Pre-Debut period: No suitable training found")
        else:
            self._log(f"No training meets {priority_strategy} strategy requirements")

        # For "Train Score X+" strategies, check if race is available first
        if "Train Score" in priority_strategy and not is_pre_debut:
            should_race, available_races = race_manager.should_race_today(current_date)

            if should_race and available_races:
                self._log(
                    f"{priority_strategy}: No suitable training, but found {len(available_races)} matching races - Racing instead")

                if self._stopped():
                    return False

                race_found = self.controller.race_handler.start_race_flow(
                    allow_continuous_racing=allow_continuous_racing
                )

                if race_found:
                    return True
                else:
                    # Race failed, continue to fallback training
                    if self._stopped():
                        return False
                    self._click_back_button("Race not found in game, proceeding to fallback training")
                    time.sleep(0.5)

        # Try fallback training if we have normal energy and no race (or race failed)
        if energy_percentage >= MINIMUM_ENERGY_PERCENTAGE and results_training:
            fallback_result = fallback_training(results_training, current_date, current_stats=current_stats)
            if fallback_result:
                best_key, score_info = fallback_result
                return self._navigate_and_train(best_key, "Fallback Training")

        # If low energy or no fallback training, rest
        if self._stopped():
            return False

        self._handle_rest_case(energy_percentage, strategy_settings, current_date, gui, click_back=False, click_log="")

        if not results_training:
            self._log("No training available!")
        elif energy_percentage < MINIMUM_ENERGY_PERCENTAGE:
            self._log(f"Low energy ({energy_percentage}%) - Resting")
        else:
            self._log("No support cards found in any training - Resting")

        return True

    def make_decision(self, game_state: Dict[str, Any], strategy_settings: Dict[str, Any],
                      race_manager, gui=None) -> bool:
        """Make training/racing decision based on current game state"""
        self.date_turn = game_state['turn']
        current_date = game_state.get('current_date', {})
        absolute_day = current_date.get('absolute_day', 0)

        year_txt = game_state['year']
        turn = game_state['turn']
        print(f'{year_txt} - {turn}')

        # Handle URA Finale
        if game_state['year'] == "Finale Season":
            stop_on_ura_final = strategy_settings.get('stop_on_ura_final', False)

            if game_state['turn'] == "Race Day":
                self._log("URA Finale detected - Starting finale race")
                if self._stopped():
                    return False
                return self.controller.race_handler.handle_race_day(is_ura_final=True)
            elif stop_on_ura_final:
                return self._stop_bot(gui, "URA Final reached - Stopping bot")

        # Handle Race Day (Normal)
        if game_state['turn'] == "Race Day" and game_state['year'] != "Finale Season":
            if (strategy_settings.get('enable_stop_conditions', False) and
                    strategy_settings.get('stop_on_race_day', False)):
                return self._stop_bot(gui, "Stop condition: Race Day detected - Stopping bot")

            self._log("Race Day.")
            if self._stopped():
                return False

            # Get style settings for pre-debut style selection
            style_settings = {'style': 'none'}
            is_pre_debut = current_date.get('is_pre_debut', False)
            if is_pre_debut and gui:
                event_settings = gui.get_event_choice_settings()
                style_settings = event_settings.get('debut_style', {'style': 'none'})

            return self.controller.race_handler.handle_race_day(
                is_ura_final=False,
                style_settings=style_settings,
                is_pre_debut=is_pre_debut
            )

        if self._stopped():
            return False

        mood = game_state['mood']
        current_date = game_state['current_date']
        energy_percentage = game_state['energy_percentage']
        max_energy = game_state['energy_max']
        priority_strategy = strategy_settings.get('priority_strategy', 'Train Score 2.5+')
        allow_continuous_racing = strategy_settings.get('allow_continuous_racing', True)

        if not self._handle_mood_requirement(mood, strategy_settings, current_date, gui):
            return False

        if "G1 (no training)" in priority_strategy:
            return self._handle_race_priority_strategy(game_state, strategy_settings, race_manager, gui)

        energy_action = self._handle_energy_based_action(
            energy_percentage, max_energy, current_date, race_manager, allow_continuous_racing, strategy_settings, gui
        )
        if energy_action is not None:
            return energy_action

        if self._should_prioritize_racing(current_date, energy_percentage, priority_strategy, race_manager):
            race_found = self.controller.race_handler.start_race_flow(allow_continuous_racing=allow_continuous_racing)
            if race_found:
                return True
            else:
                self._click_back_button("Matching race not found in game. Proceeding to training.")
                time.sleep(0.5)

        if self._stopped():
            return False

        return self._execute_training_flow(energy_percentage, max_energy, strategy_settings, current_date, race_manager, gui)

    def _handle_mood_requirement(self, mood: str, strategy_settings: Dict[str, Any],
                                 current_date: Dict[str, Any], gui=None) -> bool:
        """Check and handle mood requirements. Returns False if bot should stop."""
        mood_index = MOOD_LIST.index(mood) if mood in MOOD_LIST else 0
        minimum_mood_index = MOOD_LIST.index(strategy_settings.get('minimum_mood', 'NORMAL'))

        if mood_index < minimum_mood_index:
            # Stop condition using separate stop_mood_threshold and only applies after day 24
            if (strategy_settings.get('enable_stop_conditions', False) and
                strategy_settings.get('stop_on_low_mood', False) and
                current_date and current_date.get('absolute_day', 0) > 24) and self.date_turn != "Race Day":

                stop_mood_threshold = strategy_settings.get('stop_mood_threshold', 'BAD')
                stop_mood_index = MOOD_LIST.index(stop_mood_threshold) if stop_mood_threshold in MOOD_LIST else 1

                if mood_index < stop_mood_index:
                    return self._stop_bot(gui,
                        f"Stop condition: Mood ({mood}) below threshold ({stop_mood_threshold}) - Stopping bot")

            is_junior_year = current_date and current_date.get('absolute_day', 0) <= 24

            if not is_junior_year:
                self._log(
                    f"Mood is {mood}, below minimum {strategy_settings.get('minimum_mood', 'NORMAL')}. Trying recreation to increase mood")
                if self._stopped():
                    return False
                self.controller.rest_handler.execute_recreation()
                return True

        return True

    def _handle_energy_based_action(self, energy_percentage: int, energy_max: int, current_date: Dict[str, Any],
                                    race_manager, allow_continuous_racing: bool, strategy_settings: Dict[str, Any],
                                    gui=None) -> Optional[bool]:
        """Handle actions based on energy level. Returns None if should continue to normal training flow."""
        if energy_percentage < CRITICAL_ENERGY_PERCENTAGE:
            return self._handle_critical_energy(
                energy_percentage, current_date, race_manager, allow_continuous_racing, strategy_settings, gui)
        elif energy_percentage < MINIMUM_ENERGY_PERCENTAGE:
            return self._handle_medium_energy(
                energy_percentage, energy_max, current_date, race_manager, allow_continuous_racing, strategy_settings, gui)
        return None

    def _handle_critical_energy(self, energy_percentage: int, current_date: Dict[str, Any],
                                race_manager, allow_continuous_racing: bool, strategy_settings: Dict[str, Any],
                                gui=None) -> bool:
        """Handle critical energy - no training allowed, race or rest only."""
        should_race, available_races = race_manager.should_race_today(current_date)
        if should_race:
            self._log(
                f"Critical energy ({energy_percentage}%) - found {len(available_races)} matching races. Racing to avoid training.")
            if self._stopped():
                return False
            return self._try_race_or_rest(
                allow_continuous_racing, energy_percentage, strategy_settings, current_date, gui,
                back_log="Race not found. Critical energy - will rest.")
        else:
            self._log(
                f"Critical energy ({energy_percentage}%) and no matching races today. Resting immediately.")
            if self._stopped():
                return False
            self._handle_rest_case(energy_percentage, strategy_settings, current_date, gui,
                                   click_back=False, click_log="")
            return True

    def _handle_medium_energy(self, energy_percentage: int, energy_max: int, current_date: Dict[str, Any],
                              race_manager, allow_continuous_racing: bool, strategy_settings: Dict[str, Any],
                              gui=None) -> Optional[bool]:
        """Handle medium energy - check WIT first, then race, then rest."""
        self._log(f"Medium energy ({energy_percentage}%) - checking WIT training first")

        if self._stopped():
            return False

        if not self.controller.training_handler.go_to_training():
            return None

        time.sleep(0.5)

        if self._stopped():
            return False

        results_training, _ = self.controller.training_handler.check_all_training(energy_percentage, energy_max)

        if self._stopped():
            return False

        from core.logic import medium_energy_wit_training
        wit_decision = medium_energy_wit_training(results_training, current_date)

        if wit_decision == "wit":
            self._log(
                f"Medium energy ({energy_percentage}%) - WIT training meets score requirement, training WIT")
            return self._navigate_and_train("wit", "Training")

        # WIT doesn't meet score - back and check race
        self._click_back_button(f"Medium energy ({energy_percentage}%) - WIT doesn't meet score requirement")
        time.sleep(0.5)

        if self._stopped():
            return False

        # Check race
        should_race, available_races = race_manager.should_race_today(current_date)
        if should_race:
            self._log(
                f"Medium energy ({energy_percentage}%) - WIT insufficient, but found {len(available_races)} matching races. Racing instead.")
            if self._stopped():
                return False
            return self._try_race_or_rest(
                allow_continuous_racing, energy_percentage, strategy_settings, current_date, gui,
                back_log="Matching race not found in game. Medium energy - will rest.")
        else:
            # No race - rest
            self._log(
                f"Medium energy ({energy_percentage}%) - WIT insufficient and no matching races. Resting.")
            if self._stopped():
                return False
            self._handle_rest_case(energy_percentage, strategy_settings, current_date, gui,
                                   click_back=False, click_log="")
            return True

    def _should_prioritize_racing(self, current_date: Dict[str, Any], energy_percentage: int,
                                  priority_strategy: str, race_manager) -> bool:
        """Check if should prioritize racing based on strategy and available races"""
        if not current_date or energy_percentage < MINIMUM_ENERGY_PERCENTAGE:
            return False

        should_race, available_races = race_manager.should_race_today(current_date)

        if not should_race or not available_races:
            if DateManager.is_restricted_period(current_date):
                if current_date['absolute_day'] <= 16:
                    self._log("In restricted racing period (Career days 1-16). No racing allowed.")
                else:
                    self._log("In restricted racing period (Jul-Aug). No racing allowed.")
            return False

        # For Pre-Debut period, don't apply priority strategies
        is_pre_debut = current_date.get('absolute_day', 0) <= 16
        if is_pre_debut:
            self._log("Pre-Debut period: Priority strategies not applied, will check training first")
            return False

        # Check priority strategy
        if "G1" in priority_strategy:
            g1_races = [race for race in available_races
                        if race_manager.extract_race_properties(race)['grade_type'] == 'g1']
            if g1_races:
                self._log(f"G1 priority: Found {len(g1_races)} G1 races matching filters - Racing immediately")
                return True
            else:
                self._log("G1 priority: No G1 races found, will check training first")

        elif "Train Score" in priority_strategy:
            self._log(f"{priority_strategy}: Will check training first, then race if requirements not met")

        return False

    def _handle_race_priority_strategy(self, game_state: Dict[str, Any], strategy_settings: Dict[str, Any],
                                       race_manager, gui=None) -> bool:
        """Handle G1 priority strategies - race only, no training"""
        priority_strategy = strategy_settings.get('priority_strategy', 'Train Score 2.5+')
        allow_continuous_racing = strategy_settings.get('allow_continuous_racing', True)
        current_date = game_state['current_date']
        energy_percentage = game_state['energy_percentage']
        energy_max = game_state['energy_max']

        # Check if racing is possible today
        should_race, available_races = race_manager.should_race_today(current_date)

        if not should_race or not available_races:
            self._log_no_races_available(current_date)
            self._log(f"{priority_strategy}: No races available, proceeding with normal training/rest logic")
            return self._execute_training_flow(energy_percentage, energy_max, strategy_settings, current_date, race_manager, gui)

        # Check grade priority
        if not self._check_priority_race_grade(priority_strategy, available_races, race_manager):
            self._log(f"{priority_strategy}: No suitable races, proceeding with normal training/rest logic")
            return self._execute_training_flow(energy_percentage, energy_max, strategy_settings, current_date, race_manager, gui)

        # Attempt to race, fallback to training
        if self._stopped():
            return False

        return self._try_race_or_training_fallback(
            allow_continuous_racing, energy_percentage, energy_max, strategy_settings,
            current_date, race_manager, gui,
            back_log=f"{priority_strategy}: Race failed, going back to lobby")

    def _log_no_races_available(self, current_date: Dict[str, Any]):
        """Log message when no races are available"""
        if DateManager.is_restricted_period(current_date):
            if current_date['absolute_day'] <= 16:
                self._log("In restricted racing period (Career days 1-16). No racing allowed.")
            else:
                self._log("In restricted racing period (Jul-Aug). No racing allowed.")
        else:
            self._log("No matching races available today.")

    def _check_priority_race_grade(self, priority_strategy: str, available_races: list, race_manager) -> bool:
        """Check if available races match the priority strategy grade. Returns True if matches."""
        if "G1 (no training)" in priority_strategy:
            g1_races = [race for race in available_races
                        if race_manager.extract_race_properties(race)['grade_type'] == 'g1']

            if g1_races:
                self._log(f"G1 priority: Found {len(g1_races)} G1 races - Racing")
                return True
            else:
                self._log("G1 priority: No G1 races found in available races")
                return False

        return True

    def _click_back_button(self, text=""):
        """Click back button with logging"""
        time.sleep(0.5)
        enhanced_click(
            "assets/buttons/back_btn.png",
            text=text,
            check_stop_func=self.controller.check_should_stop,
            check_window_func=self.controller.is_game_window_active,
            log_func=self.controller.log_message
        )


class MainExecutor:
    """Main executor class that orchestrates all bot operations"""

    def __init__(self):
        """Initialize the main executor"""
        self.controller = BotController()
        self.game_state_manager = GameStateManager(self.controller)
        self.event_handler = EventHandler(self.controller, check_stop_func=self.controller.check_should_stop,
                                          check_window_func=self.controller.is_game_window_active,
                                          log_func=self.controller.log_message)
        self.decision_engine = DecisionEngine(self.controller)
        self.lobby_manager = CareerLobbyManager(self.controller)
        self.status_logger = StatusLogger(self.controller)

    def execute_single_iteration(self, race_manager, gui=None) -> bool:
        """Execute single iteration of main bot logic with stop conditions check"""
        try:
            if self.controller.check_should_stop():
                return False

            # Priority 1: Handle UI elements first (including event choices)
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
            year_txt = game_state['year']
            print(f'{year_txt}')
            # Check stop conditions immediately after getting game state
            if gui and hasattr(gui, 'should_stop_for_conditions'):
                if gui.should_stop_for_conditions(game_state):
                    self.controller.log_message("Stop condition met - Stopping bot")
                    if gui:
                        gui.root.after(0, gui.stop_bot)
                    return False

            # Check if career is completed (only if in lobby)
            # if self.game_state_manager.is_career_completed():
            #     return self._handle_career_completion(gui)

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

        return False

    def _get_strategy_settings(self, gui) -> Dict[str, Any]:
        """Get strategy settings from GUI or defaults"""
        default_settings = {
            'minimum_mood': 'NORMAL',
            'priority_strategy': 'Train Score 2.5+',
            'allow_continuous_racing': True,
            'manual_event_handling': False,
            'stop_on_ura_final': False,
            'stop_on_warning': False,
            'enable_stop_conditions': False,
            'stop_on_infirmary': False,
            'stop_on_need_rest': False,
            'stop_on_low_mood': False,
            'stop_on_race_day': False,
            'stop_mood_threshold': 'BAD',
            'stop_before_summer': False,
            'stop_at_month': False,
            'target_month': 'June',
            'event_choice': {
                'auto_event_map': False,
                'auto_first_choice': True,
                'uma_musume': 'None',
                'support_cards': ['None'] * 6
            }
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
    window_check_failures = 0
    max_window_check_failures = 10

    if gui:
        race_manager = gui.race_manager

        while gui.is_running and not _main_executor.controller.should_stop:
            if not gui.is_running or _main_executor.controller.should_stop:
                break

            # Check if game window is active with retry mechanism
            if not check_and_focus_game_window(gui, window_check_failures, max_window_check_failures):
                window_check_failures += 1
                if window_check_failures >= max_window_check_failures:
                    gui.log_message(
                        f"Failed to activate game window after {max_window_check_failures} attempts. Stopping bot.")
                    _main_executor.controller.set_stop_flag(True)
                    break
                time.sleep(2)
                continue
            else:
                # Reset failure counter on successful window check
                window_check_failures = 0

            if not _main_executor.execute_single_iteration(race_manager, gui):
                time.sleep(1)


def check_and_focus_game_window(gui, current_failures, max_failures):
    """Check if game window is active and attempt to focus if not active"""
    try:
        if not _main_executor.controller.is_game_window_active():
            # Log the attempt to focus window
            if gui:
                gui.log_message(
                    f"Game window not active. Attempting to focus... (Attempt {current_failures + 1}/{max_failures})")
            else:
                print(f"Game window not active. Attempting to focus... (Attempt {current_failures + 1}/{max_failures})")

            # Use the existing focus_umamusume function
            focus_umamusume()

            # Wait a moment and check again after focusing
            time.sleep(1)
            if _main_executor.controller.is_game_window_active():
                if gui:
                    gui.log_message("Successfully focused game window.")
                else:
                    print("Successfully focused game window.")
                return True
            else:
                # If focus_umamusume didn't work, try GUI's focus method as fallback
                if gui and hasattr(gui, 'game_monitor') and hasattr(gui.game_monitor, 'focus_game_window'):
                    if gui.game_monitor.focus_game_window():
                        time.sleep(1)
                        if _main_executor.controller.is_game_window_active():
                            gui.log_message("Successfully focused game window using GUI method.")
                            return True

            return False
        return True

    except Exception as e:
        # Log the exception and treat as failure
        error_msg = f"Error checking/focusing game window: {str(e)}"
        if gui:
            gui.log_message(error_msg)
        else:
            print(error_msg)
        return False


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
    'BotController', 'GameStateManager', 'DecisionEngine', 'MainExecutor',
    'career_lobby', 'set_log_callback', 'set_stop_flag', 'check_should_stop',
    'log_message', 'focus_umamusume'
]
