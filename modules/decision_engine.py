"""
Uma Musume Auto Train - Complete Decision Engine
Contains the full original training and racing decision logic
"""

import time
from typing import Dict, Any
from core.logic import training_decision, fallback_training
from core.click_handler import enhanced_click
from utils.constants import MINIMUM_ENERGY_PERCENTAGE, CRITICAL_ENERGY_PERCENTAGE


class DecisionEngine:
    """Makes training and racing decisions using complete original logic"""

    def __init__(self, controller):
        self.controller = controller

    def make_decision(self, game_state: Dict[str, Any], strategy_settings: Dict[str, Any],
                      race_manager, gui=None) -> bool:
        """Make training/racing decision using complete original execute.py logic"""

        # FIXED: Check stop conditions first in decision engine
        if gui and self._check_stop_conditions(game_state, strategy_settings, gui):
            return False

        # Handle URA Finale
        if game_state['year'] == "Finale Season" and game_state['turn'] == "Race Day":
            self.controller.log_message("URA Finale")
            if self.controller.check_should_stop():
                return False
            return self.controller.race_handler.handle_ura_finale()

        # Handle Race Day with stop condition check
        if game_state['turn'] == "Race Day" and game_state['year'] != "Finale Season":
            if (strategy_settings.get('enable_stop_conditions', False) and
                    strategy_settings.get('stop_on_race_day', False)):
                self.controller.log_message("Stop condition: Race Day detected - Stopping bot")
                if gui:
                    gui.root.after(0, gui.stop_bot)
                return False

            self.controller.log_message("Race Day.")
            return self._handle_race_day(game_state, strategy_settings, race_manager, gui)

        # Handle normal training/rest decisions using COMPLETE original logic
        return self._handle_training_turn_complete_original(game_state, strategy_settings, race_manager, gui)

    def _check_stop_conditions(self, game_state: Dict[str, Any], strategy_settings: Dict[str, Any], gui) -> bool:
        """Check all stop conditions and return True if should stop"""
        if not strategy_settings.get('enable_stop_conditions', False):
            return False

        # Check using game state manager's method
        if hasattr(gui, 'should_stop_for_conditions'):
            if gui.should_stop_for_conditions(game_state):
                self.controller.log_message("Stop condition triggered - Stopping bot")
                self.controller.set_stop_flag(True)
                gui.root.after(0, gui.stop_bot)
                return True

        return False

    def _handle_race_day(self, game_state: Dict[str, Any], strategy_settings: Dict[str, Any],
                         race_manager, gui) -> bool:
        """Handle race day decisions"""
        try:
            if self.controller.check_should_stop():
                return False

            # Check if racing is allowed
            if not strategy_settings.get('allow_continuous_racing', True):
                # Check race count and energy before racing
                pass

            # Execute race handling
            return self.controller.race_handler.handle_race_day(race_manager)

        except Exception as e:
            self.controller.log_message(f"Error handling race day: {e}")
            return False

    def _handle_training_turn_complete_original(self, game_state: Dict[str, Any], strategy_settings: Dict[str, Any],
                                                race_manager, gui) -> bool:
        """Handle training turn using COMPLETE original execute.py logic"""
        try:
            if self.controller.check_should_stop():
                return False

            # Get strategy info
            priority_strategy = strategy_settings.get('priority_strategy', 'Train Score 2.5+')
            allow_continuous_racing = strategy_settings.get('allow_continuous_racing', True)

            # Get current date and energy
            from core.state import get_current_date_info
            current_date = get_current_date_info()
            energy_percentage = game_state.get('energy_percentage', 50)

            self.controller.log_message(f"Priority strategy: {priority_strategy}")

            # ORIGINAL LOGIC: Check if this is a score-based training strategy
            if any(score in priority_strategy for score in ["Score 2+", "Score 2.5+", "Score 3+", "Score 3.5+", "Score 4+"]):
                return self._execute_score_based_training(priority_strategy, energy_percentage, current_date, strategy_settings)

            # ORIGINAL LOGIC: Handle G1/G2 racing strategies
            elif "G1 (no training)" in priority_strategy:
                return self._execute_g1_racing_strategy(race_manager, allow_continuous_racing, energy_percentage, current_date, strategy_settings)

            elif "G2 (no training)" in priority_strategy:
                return self._execute_g2_racing_strategy(race_manager, allow_continuous_racing, energy_percentage, current_date, strategy_settings)

            else:
                # Default to score-based training
                return self._execute_score_based_training("Train Score 2.5+", energy_percentage, current_date, strategy_settings)

        except Exception as e:
            self.controller.log_message(f"Error handling training turn: {e}")
            return False

    def _execute_score_based_training(self, priority_strategy: str, energy_percentage: int, current_date: dict, strategy_settings: dict) -> bool:
        """Execute score-based training strategy using original logic"""
        try:
            # Critical energy check - MUST REST
            if energy_percentage < CRITICAL_ENERGY_PERCENTAGE:
                self.controller.log_message(f"Critical energy ({energy_percentage}%). Resting immediately.")
                if self.controller.check_should_stop():
                    return False
                self.controller.rest_handler.execute_rest()
                return True

            # Go to training menu (ORIGINAL LOGIC)
            if not self.controller.training_handler.go_to_training():
                return True

            if self.controller.check_should_stop():
                return False

            time.sleep(0.5)

            # Check all training options (ORIGINAL LOGIC)
            results_training = self.controller.training_handler.check_all_training(energy_percentage)

            if self.controller.check_should_stop():
                return False

            # Make training decision using original logic
            best_training = training_decision(
                results_training,
                energy_percentage,
                strategy_settings,
                current_date
            )

            # Execute training or fallback (ORIGINAL LOGIC)
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
                # Handle rest or fallback training (ORIGINAL LOGIC)
                if energy_percentage < MINIMUM_ENERGY_PERCENTAGE or best_training == "SHOULD_REST":
                    self.controller.rest_handler.execute_rest()
                    self.controller.log_message(f"No suitable training or low energy ({energy_percentage}%) - Resting")
                    return True
                else:
                    # Try fallback training (ORIGINAL LOGIC)
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

                    # No training options available - rest
                    self.controller.rest_handler.execute_rest()
                    self.controller.log_message("No training options available - Resting")
                    return True

        except Exception as e:
            self.controller.log_message(f"Error in score-based training: {e}")
            return False

    def _execute_g1_racing_strategy(self, race_manager, allow_continuous_racing: bool, energy_percentage: int, current_date: dict, strategy_settings: dict) -> bool:
        """Execute G1 racing strategy using original logic"""
        try:
            # Check for available races
            available_races = race_manager.get_available_races() if race_manager else []

            # Check for G1 races
            g1_races = [race for race in available_races
                        if race_manager.extract_race_properties(race).get('grade_type') == 'g1']

            if g1_races:
                self.controller.log_message(f"G1 priority: Found {len(g1_races)} G1 races - Racing")
            else:
                self.controller.log_message("G1 priority: No G1 races found in available races")
                self.controller.log_message("G1 priority: No G1 races, proceeding with normal training/rest logic")

                # No G1 races - proceed with training/rest logic (ORIGINAL LOGIC)
                return self._execute_training_fallback_for_racing_strategy(energy_percentage, current_date, strategy_settings)

            # Attempt to race (ORIGINAL LOGIC)
            if self.controller.check_should_stop():
                return False

            race_found = self.controller.race_handler.start_race_flow(
                allow_continuous_racing=allow_continuous_racing)

            if race_found:
                return True
            else:
                # Race failed, click back button then proceed with training logic (ORIGINAL LOGIC)
                if self.controller.check_should_stop():
                    return False
                self._click_back_button(f"G1 priority: Race failed, going back to lobby")
                time.sleep(0.5)

                return self._execute_training_fallback_for_racing_strategy(energy_percentage, current_date, strategy_settings)

        except Exception as e:
            self.controller.log_message(f"Error in G1 racing strategy: {e}")
            return False

    def _execute_g2_racing_strategy(self, race_manager, allow_continuous_racing: bool, energy_percentage: int, current_date: dict, strategy_settings: dict) -> bool:
        """Execute G2 racing strategy using original logic"""
        try:
            # Similar to G1 but for G2 races
            available_races = race_manager.get_available_races() if race_manager else []

            # Check for G2 races
            g2_races = [race for race in available_races
                        if race_manager.extract_race_properties(race).get('grade_type') == 'g2']

            if g2_races:
                self.controller.log_message(f"G2 priority: Found {len(g2_races)} G2 races - Racing")
            else:
                self.controller.log_message("G2 priority: No G2 races found in available races")
                self.controller.log_message("G2 priority: No G2 races, proceeding with normal training/rest logic")

                return self._execute_training_fallback_for_racing_strategy(energy_percentage, current_date, strategy_settings)

            # Attempt to race
            if self.controller.check_should_stop():
                return False

            race_found = self.controller.race_handler.start_race_flow(
                allow_continuous_racing=allow_continuous_racing)

            if race_found:
                return True
            else:
                if self.controller.check_should_stop():
                    return False
                self._click_back_button(f"G2 priority: Race failed, going back to lobby")
                time.sleep(0.5)

                return self._execute_training_fallback_for_racing_strategy(energy_percentage, current_date, strategy_settings)

        except Exception as e:
            self.controller.log_message(f"Error in G2 racing strategy: {e}")
            return False

    def _execute_training_fallback_for_racing_strategy(self, energy_percentage: int, current_date: dict, strategy_settings: dict) -> bool:
        """Execute training fallback when racing strategy fails (ORIGINAL LOGIC)"""
        try:
            # Critical energy check
            if energy_percentage < CRITICAL_ENERGY_PERCENTAGE:
                self.controller.log_message(f"Critical energy ({energy_percentage}%). Resting immediately.")
                if self.controller.check_should_stop():
                    return False
                self.controller.rest_handler.execute_rest()
                return True

            # Use the same training logic as score-based training (ORIGINAL LOGIC)
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
                if energy_percentage < MINIMUM_ENERGY_PERCENTAGE or best_training == "SHOULD_REST":
                    self.controller.rest_handler.execute_rest()
                    self.controller.log_message(f"No suitable training or low energy ({energy_percentage}%) - Resting")
                    return True
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

        except Exception as e:
            self.controller.log_message(f"Error in training fallback: {e}")
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