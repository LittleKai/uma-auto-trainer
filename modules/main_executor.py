"""
Uma Musume Auto Train - Corrected Main Executor
Follows original execute.py logic exactly while maintaining modular structure
"""

import time
import pyautogui
from typing import Dict, Any, Callable
from modules.bot_controller import BotController
from modules.game_state_manager import GameStateManager
from modules.lobby_manager import CareerLobbyManager
from modules.event_manager import EventManager
from modules.decision_engine import DecisionEngine
from modules.status_logger import StatusLogger

# Import handlers from existing core directory
from core.training_handler import TrainingHandler
from core.race_handler import RaceHandler
from core.rest_handler import RestHandler
from core.event_handler import EventChoiceHandler


class MainExecutor:
    """Main executor following original execute.py logic exactly"""

    def __init__(self):
        """Initialize the main executor"""
        self.controller = BotController()
        self.game_state_manager = GameStateManager(self.controller)
        self.event_manager = EventManager(self.controller)
        self.decision_engine = DecisionEngine(self.controller)
        self.lobby_manager = CareerLobbyManager(self.controller)
        self.status_logger = StatusLogger(self.controller)

        # Initialize handlers
        self._init_handlers()

    def _init_handlers(self):
        """Initialize all handler instances"""
        self.controller.training_handler = TrainingHandler(
            check_stop_func=self.controller.check_should_stop,
            check_window_func=self.controller.is_game_window_active,
            log_func=self.controller.log_message
        )

        self.controller.race_handler = RaceHandler(
            check_stop_func=self.controller.check_should_stop,
            check_window_func=self.controller.is_game_window_active,
            log_func=self.controller.log_message
        )

        self.controller.rest_handler = RestHandler(
            check_stop_func=self.controller.check_should_stop,
            check_window_func=self.controller.is_game_window_active,
            log_func=self.controller.log_message
        )

        self.controller.event_choice_handler = EventChoiceHandler(
            check_stop_func=self.controller.check_should_stop,
            check_window_func=self.controller.is_game_window_active,
            log_func=self.controller.log_message
        )

    def execute_single_iteration(self, race_manager, gui=None) -> bool:
        """Execute single iteration following original career_lobby() logic EXACTLY"""
        try:
            # ORIGINAL LOGIC: First check, event
            if self.event_manager.handle_ui_elements(gui):
                return True  # Continue to next iteration

            # ORIGINAL LOGIC: Check if current menu is in career lobby
            tazuna_hint = pyautogui.locateCenterOnScreen(
                "assets/ui/tazuna_hint.png",
                confidence=0.8,
                minSearchTime=0.2
            )

            if tazuna_hint is None:
                self.controller.log_message("[INFO] Should be in career lobby.")

                if self.controller.increment_career_lobby_counter():
                    if gui:
                        gui.root.after(0, gui.stop_bot)
                    return False
                return True  # Continue trying
            else:
                self.controller.reset_career_lobby_counter()

            # ORIGINAL LOGIC: time.sleep(0.5)
            time.sleep(0.5)

            # ORIGINAL LOGIC: Check if there is debuff status
            debuffed = pyautogui.locateOnScreen(
                "assets/buttons/infirmary_btn2.png",
                confidence=0.9,
                minSearchTime=1
            )

            if debuffed:
                from core.recognizer import is_infirmary_active
                if is_infirmary_active((debuffed.left, debuffed.top, debuffed.width, debuffed.height)):

                    # FIXED: Check stop conditions for infirmary (after day 24)
                    if (gui and gui.get_current_settings().get('enable_stop_conditions', False) and
                            gui.get_current_settings().get('stop_on_infirmary', False)):

                        from core.state import get_current_date_info
                        current_date = get_current_date_info()
                        absolute_day = current_date.get('absolute_day', 0) if current_date else 0

                        if absolute_day > 24:
                            self.controller.log_message("Stop condition: Infirmary needed - Stopping bot")
                            if gui:
                                gui.root.after(0, gui.stop_bot)
                            return False

                    pyautogui.click(debuffed)
                    self.controller.log_message("[INFO] Character has debuff, go to infirmary instead.")
                    return True  # Continue to next iteration

            if self.controller.check_should_stop():
                return False

            # Update game state for decision making and GUI
            game_state = self.game_state_manager.update_game_state()

            # FIXED: Check other stop conditions in lobby (but only after the basic checks)
            if gui and self._check_additional_stop_conditions_in_lobby(game_state, gui):
                return False

            # Check if career is completed
            if self.game_state_manager.is_career_completed():
                return self._handle_career_completion(gui)

            # Get strategy settings
            strategy_settings = self._get_strategy_settings(gui)

            # Update GUI status
            if gui:
                self.status_logger.update_gui_status(gui, game_state)

            # Make training/racing decisions using COMPLETE original logic
            decision_result = self.decision_engine.make_decision(game_state, strategy_settings, race_manager, gui)

            # Always continue to next iteration (original behavior)
            return True

        except Exception as e:
            self.controller.log_message(f"Error in main iteration: {e}")
            time.sleep(1)
            return True  # Continue trying instead of stopping

    def _check_additional_stop_conditions_in_lobby(self, game_state: Dict[str, Any], gui) -> bool:
        """Check additional stop conditions (not infirmary) when in career lobby"""
        try:
            if not gui:
                return False

            settings = gui.get_current_settings() if hasattr(gui, 'get_current_settings') else {}

            if not settings.get('enable_stop_conditions', False):
                return False

            # Check low mood condition
            if settings.get('stop_on_low_mood', False):
                current_mood = game_state.get('mood', 'NORMAL')
                threshold_mood = settings.get('stop_mood_threshold', 'BAD')

                from utils.constants import MOOD_LIST
                if (current_mood in MOOD_LIST and threshold_mood in MOOD_LIST and
                        MOOD_LIST.index(current_mood) <= MOOD_LIST.index(threshold_mood)):
                    self.controller.log_message(f"Stop condition: Low mood ({current_mood}) - Stopping bot")
                    self.controller.set_stop_flag(True)
                    gui.root.after(0, gui.stop_bot)
                    return True

            # Check race day condition (will be handled in decision engine, but can also stop here)
            if (settings.get('stop_on_race_day', False) and
                    game_state.get('turn') == "Race Day" and
                    game_state.get('year') != "Finale Season"):
                self.controller.log_message("Stop condition: Race Day detected - Stopping bot")
                self.controller.set_stop_flag(True)
                gui.root.after(0, gui.stop_bot)
                return True

            # Check need rest condition
            if settings.get('stop_on_need_rest', False):
                energy = game_state.get('energy_percentage', 50)
                critical_threshold = self.controller.get_config('critical_energy_percentage', 20)
                if energy <= critical_threshold:
                    self.controller.log_message(f"Stop condition: Critical energy ({energy}%) - Stopping bot")
                    self.controller.set_stop_flag(True)
                    gui.root.after(0, gui.stop_bot)
                    return True

            return False

        except Exception as e:
            self.controller.log_message(f"Error checking additional stop conditions: {e}")
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
            'event_choice': {
                'auto_event_map': False,
                'auto_first_choice': True,
                'uma_musume': 'None',
                'support_cards': ['None'] * 6
            }
        }

        if gui and hasattr(gui, 'get_current_settings'):
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


# Global functions for external access (for backward compatibility)
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


def focus_umamusume():
    """Focus Umamusume window for compatibility"""
    controller = get_controller()
    controller.focus_game_window()


# Export main classes for advanced usage
__all__ = [
    'MainExecutor', 'BotController', 'GameStateManager', 'EventManager',
    'DecisionEngine', 'CareerLobbyManager', 'StatusLogger',
    'set_log_callback', 'set_stop_flag', 'check_should_stop',
    'log_message', 'focus_umamusume', 'get_controller', 'initialize_executor'
]