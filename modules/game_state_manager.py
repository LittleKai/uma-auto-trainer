"""
Uma Musume Auto Train - Game State Manager
Manages current game state information
"""

from typing import Dict, Any
from core.state import (
    check_turn, check_mood, check_current_year, check_criteria,
    get_current_date_info, check_energy_percentage
)


class GameStateManager:
    """Manages current game state information"""

    def __init__(self, controller):
        self.controller = controller
        self.current_state = {}

    def update_game_state(self) -> Dict[str, Any]:
        """Update and return current game state"""
        try:
            mood = check_mood()
            turn = check_turn()
            year = check_current_year()
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
                'energy_percentage': energy_percentage,
                'date_info': current_date,
                'absolute_day': current_date.get('absolute_day', 0) if current_date else 0,
                'is_pre_debut': current_date.get('is_pre_debut', False) if current_date else False,
                'is_finale': current_date.get('is_finale', False) if current_date else False
            }

            return self.current_state

        except Exception as e:
            self.controller.log_message(f"Error updating game state: {e}")
            return self._get_fallback_state()

    def _get_fallback_state(self) -> Dict[str, Any]:
        """Return safe fallback state when detection fails"""
        fallback_state = {
            'mood': 'UNKNOWN',
            'turn': 'Unknown',
            'year': 'Classic',
            'energy_percentage': 50,
            'date_info': {
                'year': 'Classic',
                'absolute_day': 50,
                'is_pre_debut': False,
                'is_finale': False
            },
            'absolute_day': 50,
            'is_pre_debut': False,
            'is_finale': False
        }

        self.current_state = fallback_state
        return fallback_state

    def is_career_completed(self) -> bool:
        """Check if career is completed (Finale Season detected)"""
        try:
            return (self.current_state.get('year') == "Finale Season" and
                    self.current_state.get('turn') != "Race Day" and
                    self.current_state.get('is_finale', False))
        except:
            return False

    def is_race_day(self) -> bool:
        """Check if current turn is Race Day"""
        return self.current_state.get('turn') == "Race Day"

    def is_ura_finale(self) -> bool:
        """Check if current turn is URA Finale"""
        return (self.current_state.get('year') == "Finale Season" and
                self.current_state.get('turn') == "Race Day")

    def get_current_mood(self) -> str:
        """Get current mood state"""
        return self.current_state.get('mood', 'UNKNOWN')

    def get_energy_percentage(self) -> int:
        """Get current energy percentage"""
        return self.current_state.get('energy_percentage', 50)

    def get_absolute_day(self) -> int:
        """Get absolute day number"""
        return self.current_state.get('absolute_day', 0)

    def is_pre_debut(self) -> bool:
        """Check if currently in pre-debut period"""
        return self.current_state.get('is_pre_debut', False)

    def meets_stop_conditions(self, settings: Dict[str, Any]) -> bool:
        """Check if current state meets any configured stop conditions"""
        if not settings.get('enable_stop_conditions', False):
            return False

        # Check infirmary condition
        if (settings.get('stop_on_infirmary', False) and
                self.get_absolute_day() > 24):  # Only apply after day 24
            from core.recognizer import is_infirmary_active
            import pyautogui

            debuffed = pyautogui.locateOnScreen(
                "assets/buttons/infirmary_btn2.png",
                confidence=0.9,
                minSearchTime=1
            )

            if debuffed and is_infirmary_active((debuffed.left, debuffed.top, debuffed.width, debuffed.height)):
                return True

        # Check low mood condition
        if settings.get('stop_on_low_mood', False):
            current_mood = self.get_current_mood()
            threshold_mood = settings.get('stop_mood_threshold', 'BAD')

            from utils.constants import MOOD_LIST
            if (current_mood in MOOD_LIST and threshold_mood in MOOD_LIST and
                    MOOD_LIST.index(current_mood) <= MOOD_LIST.index(threshold_mood)):
                return True

        # Check race day condition
        if (settings.get('stop_on_race_day', False) and
                self.is_race_day() and
                not self.is_ura_finale()):
            return True

        # Check need rest condition
        if settings.get('stop_on_need_rest', False):
            energy = self.get_energy_percentage()
            critical_threshold = self.controller.get_config('critical_energy_percentage', 20)
            if energy <= critical_threshold:
                return True

        return False