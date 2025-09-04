"""
Uma Musume Auto Train - Status Logger
Handles status logging and GUI updates
"""

from typing import Dict, Any


class StatusLogger:
    """Handles status logging and GUI updates"""

    def __init__(self, controller):
        self.controller = controller

    def update_gui_status(self, gui, game_state: Dict[str, Any]):
        """Update GUI with current game state"""
        if not gui:
            return

        try:
            # Update mood display
            mood = game_state.get('mood', 'UNKNOWN')
            if hasattr(gui, 'update_mood_display'):
                gui.update_mood_display(mood)

            # Update energy display
            energy = game_state.get('energy_percentage', 0)
            if hasattr(gui, 'update_energy_display'):
                gui.update_energy_display(energy)

            # Update turn display
            turn = game_state.get('turn', 'Unknown')
            year = game_state.get('year', 'Unknown')
            if hasattr(gui, 'update_turn_display'):
                gui.update_turn_display(f"{year} - {turn}")

            # Update date display
            absolute_day = game_state.get('absolute_day', 0)
            if hasattr(gui, 'update_date_display'):
                gui.update_date_display(f"Day {absolute_day}")

        except Exception as e:
            self.controller.log_message(f"Error updating GUI status: {e}")

    def log_current_status(self, game_state: Dict[str, Any], strategy_settings: Dict[str, Any], race_manager):
        """Log current game status"""
        try:
            mood = game_state.get('mood', 'UNKNOWN')
            turn = game_state.get('turn', 'Unknown')
            year = game_state.get('year', 'Unknown')
            energy = game_state.get('energy_percentage', 0)
            absolute_day = game_state.get('absolute_day', 0)

            # Create status message
            status_parts = [
                f"Day {absolute_day}",
                f"{year}",
                f"{turn}",
                f"Mood: {mood}",
                f"Energy: {energy}%"
            ]

            status_message = " | ".join(status_parts)

            # Add strategy info
            strategy = strategy_settings.get('priority_strategy', 'Unknown')
            minimum_mood = strategy_settings.get('minimum_mood', 'NORMAL')

            strategy_info = f" | Strategy: {strategy} | Min Mood: {minimum_mood}"

            full_status = status_message + strategy_info

            self.controller.log_message(f"📊 Status: {full_status}")

            # Log special conditions
            self._log_special_conditions(game_state, strategy_settings)

        except Exception as e:
            self.controller.log_message(f"Error logging status: {e}")

    def _log_special_conditions(self, game_state: Dict[str, Any], strategy_settings: Dict[str, Any]):
        """Log special conditions and warnings"""
        try:
            # Check for low energy warning
            energy = game_state.get('energy_percentage', 50)
            critical_energy = self.controller.get_config('critical_energy_percentage', 20)
            minimum_energy = self.controller.get_config('minimum_energy_percentage', 40)

            if energy <= critical_energy:
                self.controller.log_message(f"⚠️ CRITICAL ENERGY: {energy}% - Will rest")
            elif energy <= minimum_energy:
                self.controller.log_message(f"⚠️ Low energy: {energy}% - May need rest")

            # Check for mood warnings
            mood = game_state.get('mood', 'NORMAL')
            minimum_mood = strategy_settings.get('minimum_mood', 'NORMAL')

            from utils.constants import MOOD_LIST
            if (mood in MOOD_LIST and minimum_mood in MOOD_LIST and
                    MOOD_LIST.index(mood) < MOOD_LIST.index(minimum_mood)):
                self.controller.log_message(f"⚠️ Mood below minimum: {mood} < {minimum_mood}")

            # Check for pre-debut status
            if game_state.get('is_pre_debut', False):
                self.controller.log_message("📝 Currently in pre-debut period")

            # Check for finale status
            if game_state.get('is_finale', False):
                self.controller.log_message("🏆 Currently in finale season")

            # Log stop condition status
            if strategy_settings.get('enable_stop_conditions', False):
                active_conditions = self._get_active_stop_conditions(strategy_settings)
                if active_conditions:
                    self.controller.log_message(f"🛑 Active stop conditions: {', '.join(active_conditions)}")

        except Exception as e:
            self.controller.log_message(f"Error logging special conditions: {e}")

    def _get_active_stop_conditions(self, strategy_settings: Dict[str, Any]) -> list:
        """Get list of active stop conditions"""
        active_conditions = []

        if strategy_settings.get('stop_on_infirmary', False):
            active_conditions.append('Infirmary')

        if strategy_settings.get('stop_on_low_mood', False):
            threshold = strategy_settings.get('stop_mood_threshold', 'BAD')
            active_conditions.append(f'Low Mood ({threshold})')

        if strategy_settings.get('stop_on_race_day', False):
            active_conditions.append('Race Day')

        if strategy_settings.get('stop_on_need_rest', False):
            active_conditions.append('Need Rest')

        return active_conditions

    def log_training_decision(self, decision_info: Dict[str, Any]):
        """Log training decision details"""
        try:
            training_type = decision_info.get('type', 'Unknown')
            location = decision_info.get('location', 'Unknown')
            score = decision_info.get('score', 0)
            failure_rate = decision_info.get('failure_rate', 0)

            self.controller.log_message(
                f"🎯 Training Decision: {training_type} at {location} "
                f"(Score: {score:.1f}, Failure: {failure_rate}%)"
            )

        except Exception as e:
            self.controller.log_message(f"Error logging training decision: {e}")

    def log_race_decision(self, race_info: Dict[str, Any]):
        """Log race decision details"""
        try:
            race_name = race_info.get('name', 'Unknown Race')
            race_grade = race_info.get('grade', 'Unknown')
            distance = race_info.get('distance', 'Unknown')
            track = race_info.get('track', 'Unknown')

            self.controller.log_message(
                f"🏁 Race Decision: {race_name} "
                f"({race_grade}, {distance}, {track})"
            )

        except Exception as e:
            self.controller.log_message(f"Error logging race decision: {e}")

    def log_rest_decision(self, rest_info: Dict[str, Any]):
        """Log rest decision details"""
        try:
            reason = rest_info.get('reason', 'General rest')
            current_energy = rest_info.get('current_energy', 0)
            current_mood = rest_info.get('current_mood', 'Unknown')

            self.controller.log_message(
                f"😴 Rest Decision: {reason} "
                f"(Energy: {current_energy}%, Mood: {current_mood})"
            )

        except Exception as e:
            self.controller.log_message(f"Error logging rest decision: {e}")

    def log_error_recovery(self, error_info: Dict[str, Any]):
        """Log error recovery attempts"""
        try:
            error_type = error_info.get('type', 'Unknown Error')
            recovery_action = error_info.get('recovery_action', 'None')

            self.controller.log_message(
                f"🔧 Error Recovery: {error_type} -> {recovery_action}"
            )

        except Exception as e:
            self.controller.log_message(f"Error logging error recovery: {e}")