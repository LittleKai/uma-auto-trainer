"""
Uma Musume Auto Train - Refactored Execute Module
Main entry point maintaining backward compatibility while using new modular structure
"""

import time
from typing import Callable
from modules.main_executor import (
    MainExecutor, initialize_executor, get_controller,
    set_log_callback as _set_log_callback,
    set_stop_flag as _set_stop_flag,
    check_should_stop as _check_should_stop,
    log_message as _log_message,
    focus_umamusume as _focus_umamusume
)
from core.race_manager import RaceManager


def career_lobby(gui=None):
    """Main career lobby function - entry point for bot execution with improved stop condition handling"""
    global _main_executor

    # Initialize executor if not already done
    initialize_executor()
    _main_executor = MainExecutor()

    # Reset stop flag
    _main_executor.controller.set_stop_flag(False)

    # Create race manager
    race_manager = RaceManager()

    if gui:
        # Use GUI's race manager if available
        if hasattr(gui, 'race_manager'):
            race_manager = gui.race_manager

        # Main execution loop with GUI
        while gui.is_running and not _main_executor.controller.should_stop:
            try:
                # Check if GUI is still running
                if not gui.is_running or _main_executor.controller.should_stop:
                    break

                # Check if game window is active
                if not _main_executor.controller.is_game_window_active():
                    gui.log_message("Waiting for game window to be active...")
                    time.sleep(2)
                    continue

                # Execute single iteration with improved stop condition handling
                if not _main_executor.execute_single_iteration(race_manager, gui):
                    time.sleep(1)

            except Exception as e:
                _main_executor.controller.log_message(f"Error in main loop: {e}")
                time.sleep(2)

    else:
        # Standalone execution without GUI
        while not _main_executor.controller.should_stop:
            try:
                if not _main_executor.execute_single_iteration(race_manager):
                    time.sleep(1)

            except KeyboardInterrupt:
                _main_executor.controller.log_message("Bot stopped by user")
                break
            except Exception as e:
                _main_executor.controller.log_message(f"Error in main loop: {e}")
                time.sleep(2)

    _main_executor.controller.log_message("Bot execution completed")


# Backward compatibility functions
def set_log_callback(callback: Callable[[str], None]):
    """Set the logging callback function"""
    return _set_log_callback(callback)


def set_stop_flag(value: bool = True):
    """Set the global stop flag (called when F3 is pressed)"""
    return _set_stop_flag(value)


def check_should_stop() -> bool:
    """Check if bot should stop due to F3 press"""
    return _check_should_stop()


def log_message(message: str):
    """Log message using global controller"""
    return _log_message(message)


def focus_umamusume():
    """Focus Umamusume window for compatibility"""
    return _focus_umamusume()


# Additional compatibility functions for any existing imports
def get_main_executor():
    """Get the main executor instance"""
    initialize_executor()
    return MainExecutor()


def get_bot_controller():
    """Get the bot controller instance"""
    return get_controller()


# Export all important functions and classes
__all__ = [
    'career_lobby',
    'set_log_callback',
    'set_stop_flag',
    'check_should_stop',
    'log_message',
    'focus_umamusume',
    'get_main_executor',
    'get_bot_controller',
    'MainExecutor',
    'initialize_executor',
    'get_controller'
]