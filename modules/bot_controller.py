"""
Uma Musume Auto Train - Core Bot Controller
Main bot controller that orchestrates all operations
"""

import time
import json
import pygetwindow as gw
from typing import Dict, Optional, Callable, Any


class BotController:
    """Main bot controller that orchestrates all operations"""

    def __init__(self):
        """Initialize the bot controller"""
        self.should_stop = False
        self.career_lobby_attempts = 0
        self.log_callback = None
        self.window_inactive_start_time = None
        self.config = {}

        # Initialize handlers (will be set by executor)
        self.training_handler = None
        self.race_handler = None
        self.rest_handler = None
        self.event_choice_handler = None

        # Load configuration
        self._load_config()

    def _load_config(self):
        """Load configuration from config.json"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                self.config = json.load(f)
                self.log_message("Configuration loaded successfully")
        except Exception as e:
            self.log_message(f"Error loading config: {e}")
            self._create_default_config()

    def _create_default_config(self):
        """Create default configuration if config.json doesn't exist"""
        default_config = {
            "priority_stat": ["spd", "pwr", "sta", "wit", "guts"],
            "maximum_failure": 15,
            "minimum_energy_percentage": 40,
            "critical_energy_percentage": 20,
            "stat_caps": {
                "spd": 1120,
                "sta": 1120,
                "pwr": 1120,
                "guts": 500,
                "wit": 500
            }
        }

        try:
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            self.config = default_config
            self.log_message("Default configuration created")
        except Exception as e:
            self.log_message(f"Error creating default config: {e}")
            self.config = default_config

    def set_log_callback(self, callback: Callable[[str], None]):
        """Set callback function for logging"""
        self.log_callback = callback

    def log_message(self, message: str):
        """Log message using callback or fallback to print"""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def set_stop_flag(self, value: bool = True):
        """Set the stop flag to control bot execution"""
        self.should_stop = value
        if value:
            self.log_message("Stop flag set - Bot will stop")

    def check_should_stop(self) -> bool:
        """Check if bot should stop execution"""
        return self.should_stop

    def is_game_window_active(self) -> bool:
        """Check if game window is active and handle inactive states"""
        try:
            windows = gw.getWindowsWithTitle("Umamusume")

            if not windows:
                return False

            win = windows[0]
            is_active = win.isActive

            if not is_active:
                current_time = time.time()
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
        from utils.constants import MAX_CAREER_LOBBY_ATTEMPTS

        self.career_lobby_attempts += 1

        if self.career_lobby_attempts >= MAX_CAREER_LOBBY_ATTEMPTS:
            self.log_message(f"[ERROR] Career lobby detection failed {MAX_CAREER_LOBBY_ATTEMPTS} times")
            self.log_message("[ERROR] Bot appears to be stuck - stopping program")
            self.set_stop_flag(True)
            return True

        return False

    def get_config(self, key: str, default=None):
        """Get configuration value"""
        return self.config.get(key, default)

    def focus_game_window(self):
        """Focus Umamusume window"""
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
            self.log_message(f"Error focusing Umamusume window: {e}")