"""
Uma Musume Auto Train - Modules Package
New modular architecture components
"""

# Import main classes
from .bot_controller import BotController
from .game_state_manager import GameStateManager
from .lobby_manager import CareerLobbyManager
from .event_manager import EventManager
from .decision_engine import DecisionEngine
from .status_logger import StatusLogger
from .main_executor import MainExecutor, initialize_executor, get_controller

# Import backward compatibility functions
from .main_executor import (
    set_log_callback,
    set_stop_flag,
    check_should_stop,
    log_message,
    focus_umamusume
)

# Export all important components
__all__ = [
    # Main classes
    'BotController',
    'GameStateManager',
    'CareerLobbyManager',
    'EventManager',
    'DecisionEngine',
    'StatusLogger',
    'MainExecutor',

    # Initialization functions
    'initialize_executor',
    'get_controller',

    # Global functions (backward compatibility)
    'set_log_callback',
    'set_stop_flag',
    'check_should_stop',
    'log_message',
    'focus_umamusume'
]


def create_bot_instance():
    """Factory function to create a complete bot instance"""
    initialize_executor()
    return MainExecutor()


def get_version_info():
    """Get version information for the refactored core"""
    return {
        'version': '2.0.0',
        'description': 'Refactored modular architecture',
        'features': [
            'Modular design',
            'Improved stop condition handling',
            'Separated concerns architecture',
            'Enhanced error handling',
            'Better maintainability'
        ],
        'components': [
            'BotController - Main coordination',
            'GameStateManager - State tracking',
            'CareerLobbyManager - Lobby navigation',
            'EventManager - Event handling',
            'DecisionEngine - Decision logic',
            'StatusLogger - Logging and GUI updates',
            'MainExecutor - Orchestration'
        ]
    }