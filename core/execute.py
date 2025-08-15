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
        from utils.constants import MAX_CAREER_LOBBY_ATTEMPTS

        self.career_lobby_attempts += 1

        if self.career_lobby_attempts >= MAX_CAREER_LOBBY_ATTEMPTS:
            self.log_message(f"[ERROR] Career lobby detection failed {MAX_CAREER_LOBBY_ATTEMPTS} times")
            self.log_message("[ERROR] Bot appears to be stuck - stopping program")
            self.set_stop_flag(True)
            return True

        return False

class GameStateManager:

    def __init__(self, controller: BotController):
        self.controller = controller
        self.current_state = {}

    def update_game_state(self) -> Dict[str, Any]:
        try:
            mood = check_mood()
            turn = check_turn()
            year = check_current_year()
            criteria = check_criteria()
            energy_percentage = check_energy_percentage()
            current_date = get_current_date_info()

            if current_date is None:
                self.controller.log_message("[ERROR] Date parsing failed, using safe fallback behavior")
                # Safe fallback - assume it's not pre-debut and continue with basic logic
                current_date = {
                    'year': 'Classic',  # Safe assumption
                    'absolute_day': 50,  # Mid-game assumption
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
            self.controller.log_message(f"Error in career lobby iteration: {e}")
            # Return safe fallback state
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

        return self.current_state.get('current_date', {}).get('is_finale', False)

    def is_race_day(self) -> bool:
        """Check if current turn is race day"""
        return self.current_state.get('turn') == "Race Day"

    def is_ura_finale(self) -> bool:
        """Check if this is URA finale"""
        return (self.current_state.get('year') == "Finale Season" and
                self.current_state.get('turn') == "Race Day")

class EventHandler:

    def __init__(self, controller: BotController):
        self.controller = controller

    def handle_ui_elements(self, gui=None) -> bool:

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
                # Manual event handling - pause bot and wait for user action
                self.controller.log_message("🎭 EVENT DETECTED! Manual event handling enabled.")
                self.controller.log_message("⏳ Waiting for you to select event choice manually...")

                if gui:
                    # Automatically pause the bot
                    gui.root.after(0, gui.pause_bot)

                # Wait with improved logic
                event_handled = self._wait_for_event_completion(gui)

                if not event_handled:
                    return False  # Bot was stopped

                self.controller.log_message("✅ Event completed! Continuing bot...")
                return True
            else:
                # Automatic event handling (original behavior)
                if self._click("assets/icons/event_choice_1.png", minSearch=0.2, text="Event found, automatically select top choice."):
                    return True

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
        if self.controller.check_should_stop():
            return False

        if not self.controller.is_game_window_active():
            return False

        btn = pyautogui.locateCenterOnScreen(img, confidence=confidence, minSearchTime=minSearch)
        if btn:
            if text:
                self.controller.log_message(text)
            if self.controller.check_should_stop():  # Check again before clicking
                return False
            pyautogui.moveTo(btn, duration=0.175)
            pyautogui.click(clicks=click_count)
            return True

        return False

    def _wait_for_event_completion(self, gui=None, max_wait_time=300):

        import time

        start_time = time.time()

        while True:
            # Check if bot was stopped
            if gui and not gui.is_running:
                return False

            if self.controller.check_should_stop():
                return False

            time.sleep(1)

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
                    if gui and gui.is_paused:
                        gui.root.after(0, gui.pause_bot)  # Resume if still paused
                    return True
                else:
                    # Check for other game states that indicate event is progressing
                    next_btn = pyautogui.locateCenterOnScreen(
                        "assets/buttons/next_btn.png",
                        confidence=0.8,
                        minSearchTime=0.2
                    )
                    if next_btn:
                        # Event is progressing, continue waiting
                        continue

            # Timeout check (5 minutes max)
            if time.time() - start_time > max_wait_time:
                self.controller.log_message("⚠️ Event waiting timeout - resuming bot")
                if gui and gui.is_paused:
                    gui.root.after(0, gui.pause_bot)  # Resume if still paused
                return True

            # Show waiting message every 30 seconds
            elapsed = time.time() - start_time
            if elapsed > 0 and int(elapsed) % 30 == 0:
                self.controller.log_message(f"⏳ Still waiting for event completion... ({int(elapsed)}s elapsed)")

class DecisionEngine:

    def __init__(self, controller: BotController):
        self.controller = controller

    def make_decision(self, game_state: Dict[str, Any], strategy_settings: Dict[str, Any],
                      race_manager, gui=None) -> bool:

        if game_state['year'] == "Finale Season" and game_state['turn'] == "Race Day":
            self.controller.log_message("URA Finale")
            if self.controller.check_should_stop():
                return False

            # Use race handler with preserved timing
            return self.controller.race_handler.handle_ura_finale()

        if game_state['turn'] == "Race Day" and game_state['year'] != "Finale Season":
            self.controller.log_message("Race Day.")
            if self.controller.check_should_stop():
                return False

            # Use race handler with preserved timing
            return self.controller.race_handler.handle_race_day()

        if self.controller.check_should_stop():
            return False

        mood = game_state['mood']
        year = game_state['year']
        current_date = game_state['current_date']
        energy_percentage = game_state['energy_percentage']

        MOOD_LIST = ["AWFUL", "BAD", "NORMAL", "GOOD", "GREAT", "UNKNOWN"]
        mood_index = MOOD_LIST.index(mood) if mood in MOOD_LIST else 0
        minimum_mood_index = MOOD_LIST.index(strategy_settings.get('minimum_mood', 'NORMAL'))

        if mood_index < minimum_mood_index:
            # Check if in Pre-Debut period or Junior Year - skip recreation
            is_pre_debut = current_date and current_date.get('absolute_day', 0) < 24
            is_junior_year = "Junior Year" in year

            if is_pre_debut:
                self.controller.log_message(f"Mood is {mood}, below minimum {strategy_settings.get('minimum_mood', 'NORMAL')}. Skipping recreation (Pre-Debut period)")
            elif is_junior_year:
                self.controller.log_message(f"Mood is {mood}, below minimum {strategy_settings.get('minimum_mood', 'NORMAL')}. Skipping recreation (Junior Year)")
            else:
                self.controller.log_message(f"Mood is {mood}, below minimum {strategy_settings.get('minimum_mood', 'NORMAL')}. Trying recreation to increase mood")
                if self.controller.check_should_stop():
                    return False
                self.controller.rest_handler.execute_recreation()
                return True

        if self.controller.check_should_stop():
            return False

        priority_strategy = strategy_settings.get('priority_strategy', 'Train Score 2.5+')
        allow_continuous_racing = strategy_settings.get('allow_continuous_racing', True)

        if energy_percentage < CRITICAL_ENERGY_PERCENTAGE:
            should_race, available_races = race_manager.should_race_today(current_date)
            if should_race:
                self.controller.log_message(f"Critical energy ({energy_percentage}%) - found {len(available_races)} matching races. Racing to avoid training.")
                if self.controller.check_should_stop():
                    return False
                race_found = self._do_race(allow_continuous_racing=allow_continuous_racing)
                if race_found:
                    return True
                else:
                    if not self.controller.check_should_stop():
                        self._click_back_button("Race not found. Critical energy - will rest.")
                        time.sleep(0.5)
                        self.controller.rest_handler.execute_rest()
                        self.controller.log_message("Critical energy - Resting")
                    return True
            else:
                self.controller.log_message(f"Critical energy ({energy_percentage}%) and no matching races today. Resting immediately.")
                if self.controller.check_should_stop():
                    return False
                self.controller.rest_handler.execute_rest()
                self.controller.log_message("Critical energy - Resting")
                return True

        elif energy_percentage < MINIMUM_ENERGY_PERCENTAGE:
            should_race, available_races = race_manager.should_race_today(current_date)
            if should_race:
                self.controller.log_message(f"Low energy ({energy_percentage}%) but found {len(available_races)} matching races for today. Racing instead of training.")
                if self.controller.check_should_stop():
                    return False
                race_found = self._do_race(allow_continuous_racing=allow_continuous_racing)
                if race_found:
                    return True
                else:
                    if not self.controller.check_should_stop():
                        self._click_back_button("Matching race not found in game. Low energy - will check WIT training.")
                        time.sleep(0.5)
            else:
                self.controller.log_message(f"Low energy ({energy_percentage}%) and no matching races today. Will check WIT training or rest.")

        if self.controller.check_should_stop():
            return False

        if current_date and energy_percentage >= MINIMUM_ENERGY_PERCENTAGE:
            should_race, available_races = race_manager.should_race_today(current_date)

            if should_race and available_races:
                self.controller.log_message(f"Found {len(available_races)} races matching filters today:")
                for race in available_races:
                    props = race_manager.extract_race_properties(race)
                    self.controller.log_message(f"  - {race['name']} ({props['track_type']}, {props['distance_type']}, {props['grade_type']})")

                race_matches_priority = False

                if "G1" in priority_strategy:
                    # Only race if there's a G1 race available
                    g1_races = [race for race in available_races
                                if race_manager.extract_race_properties(race)['grade_type'] == 'g1']
                    if g1_races:
                        race_matches_priority = True
                        self.controller.log_message(f"G1 priority: Found {len(g1_races)} G1 races matching filters - Racing immediately")
                    else:
                        self.controller.log_message(f"G1 priority: No G1 races found, will check training first")

                elif "G2" in priority_strategy:
                    # Race if there's a G1 or G2 race available
                    high_grade_races = [race for race in available_races
                                        if race_manager.extract_race_properties(race)['grade_type'] in ['g1', 'g2']]
                    if high_grade_races:
                        race_matches_priority = True
                        self.controller.log_message(f"G2 priority: Found {len(high_grade_races)} G1/G2 races matching filters - Racing immediately")
                    else:
                        self.controller.log_message(f"G2 priority: No G1/G2 races found, will check training first")

                elif "Train Score" in priority_strategy:
                    # For score strategies, always check training first
                    self.controller.log_message(f"{priority_strategy}: Will check training first, then race if requirements not met")
                    race_matches_priority = False

                if race_matches_priority:
                    if self.controller.check_should_stop():
                        return False
                    race_found = self._do_race(allow_continuous_racing=allow_continuous_racing)
                    if race_found:
                        return True
                    else:
                        if not self.controller.check_should_stop():
                            self._click_back_button("Matching race not found in game. Proceeding to training.")
                            time.sleep(0.5)
            else:
                if DateManager.is_restricted_period(current_date):
                    if current_date.get('is_pre_debut', False):
                        self.controller.log_message("In Pre-Debut period. No racing allowed.")
                    elif current_date['absolute_day'] <= 16:
                        self.controller.log_message("In restricted racing period (Career days 1-16). No racing allowed.")
                    else:
                        self.controller.log_message("In restricted racing period (Jul-Aug). No racing allowed.")

        if self.controller.check_should_stop():
            return False

        if not self.controller.training_handler.go_to_training():
            self.controller.log_message("Training button is not found.")
            return True

        if self.controller.check_should_stop():
            return False

        time.sleep(0.5)
        results_training = self.controller.training_handler.check_all_training(energy_percentage)

        if self.controller.check_should_stop():
            return False

        best_training = self._enhanced_training_decision(results_training, energy_percentage, strategy_settings, current_date)

        if best_training:
            # Training found that meets strategy requirements
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

            # If we haven't tried racing yet, try now
            if current_date and energy_percentage >= MINIMUM_ENERGY_PERCENTAGE:
                should_race, available_races = race_manager.should_race_today(current_date)

                if should_race:
                    self.controller.log_message(f"Attempting race from {len(available_races)} available races as fallback.")
                    if self.controller.check_should_stop():
                        return False
                    race_found = self._do_race(allow_continuous_racing=allow_continuous_racing)
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
                # Energy is normal but no suitable strategy training found
                self.controller.log_message(f"Normal energy but no {priority_strategy} training found - doing fallback training")

                # Use fallback training logic with proper score-based scoring
                if results_training:
                    fallback_result = self._enhanced_fallback_training(results_training, current_date)
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
                    self.controller.rest_handler.execute_rest()
                    self.controller.log_message("No training available - Resting")

        return True

    def _do_race(self, prioritize_g1=False, prioritize_g2=False, allow_continuous_racing=True):
        if self.controller.check_should_stop():
            self.controller.log_message("[STOP] Race cancelled due to F3 press")
            return False

        if not self.controller.is_game_window_active():
            return False

        return self.controller.race_handler.start_race_flow(
            prioritize_g1=prioritize_g1,
            prioritize_g2=prioritize_g2,
            allow_continuous_racing=allow_continuous_racing
        )

    def _click_back_button(self, text=""):
        enhanced_click(
            "assets/buttons/back_btn.png",
            text=text,
            check_stop_func=self.controller.check_should_stop,
            check_window_func=self.controller.is_game_window_active,
            log_func=self.controller.log_message
        )

    def _enhanced_training_decision(self, results_training, energy_percentage, strategy_settings, current_date):
        if self.controller.check_should_stop():
            return None

        if not results_training:
            print(f"[DEBUG] enhanced_training_decision: No results_training provided")
            return None

        print(f"[DEBUG] enhanced_training_decision: Received {len(results_training)} training results")
        for key, data in results_training.items():
            print(f"[DEBUG] Input data - {key.upper()}: total_score={data.get('total_score', 'MISSING')}")

        # Import the correct logic functions from core.logic
        from core.logic import enhanced_training_decision as logic_enhanced_training_decision

        # Use the proper logic function that handles score-based training and respects strategy
        return logic_enhanced_training_decision(results_training, energy_percentage, strategy_settings, current_date)

    def _enhanced_fallback_training(self, results, current_date):
        from core.logic import get_stat_priority

        is_rainbow_stage = current_date and current_date.get('absolute_day', 0) > 24
        is_early_stage = current_date and current_date.get('absolute_day', 0) < 16

        def calculate_fallback_score(training_key, training_data):
            support_counts = training_data["support"]

            if is_rainbow_stage:
                rainbow_count = support_counts.get(training_key, 0)
                rainbow_score = rainbow_count * 2
                other_support_score = sum(count for stat, count in support_counts.items() if stat != training_key)
                return rainbow_score + other_support_score, rainbow_count
            else:
                total_support = sum(support_counts.values())
                rainbow_count = support_counts.get(training_key, 0)
                return total_support, rainbow_count

        def get_fallback_priority(stat_key):
            if is_early_stage:
                early_priority = ["wit", "spd", "sta", "pwr", "guts"]
                return early_priority.index(stat_key) if stat_key in early_priority else 999
            else:
                return get_stat_priority(stat_key)

        # Find best fallback training
        fallback_training = max(
            results.items(),
            key=lambda x: (
                calculate_fallback_score(x[0], x[1])[0],
                -get_fallback_priority(x[0])
            )
        )

        best_key, best_data = fallback_training
        best_score, rainbow_count = calculate_fallback_score(best_key, best_data)

        if best_score <= 0:
            return None

        if is_rainbow_stage:
            score_info = f"(score: {best_score} - {rainbow_count} rainbow × 2 + {best_data['total_support'] - rainbow_count} others × 1)"
        elif is_early_stage:
            score_info = f"({best_data['total_support']} support cards - Early stage WIT priority)"
        else:
            score_info = f"({best_data['total_support']} support cards)"

        return best_key, score_info


class CareerLobbyManager:
    """Manages career lobby detection and navigation"""

    def __init__(self, controller: BotController):
        self.controller = controller

    def verify_lobby_state(self, gui=None) -> bool:
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

            pyautogui.click(debuffed)
            self.controller.log_message("Character has debuff, go to infirmary instead.")
            return True

        return False

class StatusLogger:

    def __init__(self, controller: BotController):
        self.controller = controller

    def log_current_status(self, game_state: Dict[str, Any],
                           strategy_settings: Dict[str, Any], race_manager):

        self.controller.log_message("=" * 50)
        self.controller.log_message(f"Year: {game_state['year']}")
        self.controller.log_message(f"Mood: {game_state['mood']}")
        self.controller.log_message(f"Turn: {game_state['turn']}")
        self.controller.log_message(f"Energy: {game_state['energy_percentage']}%")
        self.controller.log_message(f"Strategy: {strategy_settings.get('priority_strategy', 'Train Score 2.5+')}")

        if strategy_settings.get('manual_event_handling', False):
            self.controller.log_message(f"Manual Events: Enabled")

        self._log_date_and_race_info(game_state['current_date'], race_manager)

    def _log_date_and_race_info(self, current_date: Dict[str, Any], race_manager):
        if not current_date:
            return

        if current_date.get('is_finale', False):
            self.controller.log_message(f"Current Date: Finale Season (Career Completed)")
        elif current_date.get('is_pre_debut', False):
            self.controller.log_message(f"Current Date: {current_date['year']} Year Pre-Debut (Day {current_date['absolute_day']}/72)")
        else:
            self.controller.log_message(f"Current Date: {current_date['year']} {current_date['month']} {current_date['period']} (Day {current_date['absolute_day']}/72)")

        available_races = race_manager.get_available_races(current_date)
        all_filtered_races = race_manager.get_filtered_races_for_date(current_date)

        from core.race_manager import DateManager

        if DateManager.is_restricted_period(current_date):
            if current_date.get('is_pre_debut', False):
                self.controller.log_message("📍 Racing Status: Disabled (Pre-Debut period)")
            else:
                absolute_day = current_date['absolute_day']

                if absolute_day <= 16:
                    self.controller.log_message(f"📍 Racing Status: Disabled (Career days 1-16 restriction, current: Day {absolute_day}/72)")
                else:
                    self.controller.log_message("📍 Racing Status: Disabled (July-August restriction)")

            # Show filtered races that would be available if not restricted
            if all_filtered_races:
                self.controller.log_message(f"📍 Today's Races: {len(all_filtered_races)} matching filters (restricted)")
                for race in all_filtered_races[:3]:  # Show max 3
                    race_props = race_manager.extract_race_properties(race)
                    self.controller.log_message(f"  - {race['name']} ({race_props['grade_type'].upper()}, {race_props['track_type']}, {race_props['distance_type']})")
                if len(all_filtered_races) > 3:
                    self.controller.log_message(f"  ... and {len(all_filtered_races) - 3} more")
            else:
                self.controller.log_message("📍 Today's Races: None match current filters")
        else:
            # Normal racing periods - only show races that match filters
            if available_races:
                self.controller.log_message(f"📍 Today's Races: {len(available_races)} matching filters")
                for race in available_races:
                    race_props = race_manager.extract_race_properties(race)
                    self.controller.log_message(f"  - {race['name']} ({race_props['grade_type'].upper()}, {race_props['track_type']}, {race_props['distance_type']})")
            else:
                self.controller.log_message("📍 Today's Races: None match current filters")

    def update_gui_status(self, gui, game_state: Dict[str, Any]):
        if not gui:
            return

        if game_state['current_date']:
            gui.update_current_date(game_state['current_date'])

        gui.update_energy_display(game_state['energy_percentage'])

class MainExecutor:
    """Main executor class with minimal timing changes, only adding verification"""

    def __init__(self):
        """Initialize the main executor"""
        self.controller = BotController()
        self.game_state_manager = GameStateManager(self.controller)
        self.event_handler = EventHandler(self.controller)
        self.decision_engine = DecisionEngine(self.controller)
        self.lobby_manager = CareerLobbyManager(self.controller)
        self.status_logger = StatusLogger(self.controller)

    def execute_single_iteration(self, race_manager, gui=None) -> bool:
        """Execute single iteration of main bot logic with proper event handling order"""
        try:
            if self.controller.check_should_stop():
                return False

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
                    # Manual event handling - pause bot and wait for user action
                    self.controller.log_message("🎭 EVENT DETECTED! Manual event handling enabled.")
                    self.controller.log_message("⏳ Waiting for you to select event choice manually...")

                    if gui:
                        # Automatically pause the bot
                        gui.root.after(0, gui.pause_bot)

                    # Wait with improved logic
                    event_handled = self.event_handler._wait_for_event_completion(gui)

                    if not event_handled:
                        return False  # Bot was stopped

                    self.controller.log_message("✅ Event completed! Continuing bot...")
                    return True
                else:
                    # Automatic event handling (original behavior)
                    if self.event_handler._click("assets/icons/event_choice_1.png", minSearch=0.2, text="Event found, automatically select top choice."):
                        return True

            # Priority 2: Handle other UI elements (buttons, inspiration, etc.)
            if self.event_handler._click("assets/buttons/inspiration_btn.png", minSearch=0.2, text="Inspiration found."):
                return True

            if self.event_handler._click("assets/buttons/next_btn.png", minSearch=0.2):
                return True

            if self.event_handler._click("assets/buttons/cancel_btn.png", minSearch=0.2):
                return True

            if self.event_handler._click("assets/buttons/next2_btn.png", minSearch=0.2):
                return True

            # Priority 3: Check if we're in career lobby (after handling all UI elements)
            if not self.lobby_manager.verify_lobby_state(gui):
                # Not in lobby - wait and try again in next iteration
                time.sleep(1)
                return True

            # Only proceed with status checks and game logic if confirmed in lobby
            if self.controller.check_should_stop():
                return False

            time.sleep(1)

            # Handle debuff status (only if in lobby)
            if self.lobby_manager.handle_debuff_status():
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
        """Handle career completion scenario (unchanged)"""
        self.controller.log_message("🎉 CAREER COMPLETED! Finale Season detected.")
        self.controller.log_message("🎊 Congratulations! Your Uma Musume has finished their career!")
        self.controller.log_message("🏆 Bot will now stop automatically.")

        if gui:
            gui.root.after(0, gui.stop_bot)
            gui.root.after(0, lambda: gui.log_message("🎉 Career completed! Bot stopped automatically."))

        return False

    def _get_strategy_settings(self, gui) -> Dict[str, Any]:
        """Get strategy settings from GUI or defaults (unchanged)"""
        default_settings = {
            'minimum_mood': 'NORMAL',
            'priority_strategy': 'Train Score 2.5+',
            'allow_continuous_racing': True,
            'manual_event_handling': False
        }

        if gui:
            return gui.get_current_settings()
        return default_settings


class CareerLobbyManager:

    def __init__(self, controller: BotController):
        self.controller = controller

    def verify_lobby_state(self, gui=None) -> bool:
        """
        Verify if currently in career lobby
        Returns True only if confirmed in lobby, False otherwise
        """
        tazuna_hint = pyautogui.locateCenterOnScreen(
            "assets/ui/tazuna_hint.png",
            confidence=0.8,
            minSearchTime=0.2
        )

        if tazuna_hint is None:
            # Not in lobby - log and increment counter
            self.controller.log_message("Should be in career lobby.")

            # Check if we've exceeded maximum attempts
            if self.controller.increment_career_lobby_counter():
                # Force stop the bot if too many failed attempts
                if gui:
                    gui.root.after(0, gui.stop_bot)
                return False

            # Return False because we're NOT in lobby
            return False
        else:
            # Successfully detected career lobby, reset counter
            self.controller.reset_career_lobby_counter()
            # Return True because we ARE in lobby
            return True

    def handle_debuff_status(self) -> bool:
        debuffed = pyautogui.locateOnScreen(
            "assets/buttons/infirmary_btn2.png",
            confidence=0.9,
            minSearchTime=1  
        )

        if debuffed:
            if is_infirmary_active((debuffed.left, debuffed.top, debuffed.width, debuffed.height)):
                if self.controller.check_should_stop():
                    return False
                pyautogui.click(debuffed)
                self.controller.log_message("Character has debuff, go to infirmary instead.")
                return True

        return False

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
        # standalone mode
        while not _main_executor.controller.should_stop:
            if not _main_executor.execute_single_iteration(race_manager):
                time.sleep(1)

# Legacy function wrappers for backward compatibility
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