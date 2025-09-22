import json
import os


class WindowManager:
    """Manages window settings, positioning, and file I/O operations"""

    def __init__(self, main_window):
        self.main_window = main_window

        # Default window settings
        self.window_settings = {
            'width': 700,
            'height': 900,
            'x': 100,
            'y': 20
        }

    def load_initial_settings(self):
        """Load initial settings including window position before GUI setup"""
        try:
            if os.path.exists('bot_settings.json'):
                with open('bot_settings.json', 'r') as f:
                    settings = json.load(f)

                # Load window settings if they exist
                if 'window' in settings:
                    self.window_settings.update(settings['window'])

        except Exception as e:
            print(f"Warning: Could not load initial settings: {e}")

    def setup_window(self):
        """Setup window with loaded settings"""
        settings = self.window_settings

        width = max(650, settings.get('width', 700))
        height = max(850, settings.get('height', 900))

        # Get saved position or use default
        screen_width = self.main_window.root.winfo_screenwidth()
        screen_height = self.main_window.root.winfo_screenheight()

        # Use saved position if available, otherwise use default
        if 'x' in settings and 'y' in settings:
            x = settings['x']
            y = settings['y']
        else:
            # Default position: right half of screen + 20px, y = 20
            default_x = max(20, screen_width // 2) + 20
            default_y = 20
            x = default_x
            y = default_y

        # Ensure window fits on screen
        if x + width > screen_width:
            x = max(0, screen_width - width)
        if y + height > screen_height:
            y = max(0, screen_height - height)

        # Ensure minimum position values
        x = max(0, x)
        y = max(0, y)

        # Set window properties
        self.main_window.root.minsize(650, 850)
        self.main_window.root.geometry(f"{width}x{height}+{x}+{y}")
        self.main_window.root.resizable(True, True)
        self.main_window.root.attributes('-topmost', True)

    def load_tab_settings(self):
        """Load tab settings after tabs are created"""
        try:
            if not os.path.exists('bot_settings.json'):
                return

            with open('bot_settings.json', 'r') as f:
                settings = json.load(f)

            # Load tab settings
            self.main_window.strategy_tab.load_settings(settings)
            self.main_window.event_choice_tab.load_settings(settings.get('event_choice', {}))

            # Update race manager filters - now safely initialized
            race_filters = {
                'track': settings.get('track', {}),
                'distance': settings.get('distance', {}),
                'grade': settings.get('grade', {})
            }
            self.main_window.race_manager.update_filters(race_filters)

        except Exception as e:
            self.main_window.log_message(f"Warning: Could not load tab settings: {e}")

    def save_settings(self):
        """Save all settings to file"""
        try:
            # Collect settings from all tabs
            strategy_settings = self.main_window.strategy_tab.get_settings()
            event_choice_settings = self.main_window.event_choice_tab.get_settings()

            # Save current window settings
            try:
                self.main_window.root.update_idletasks()
                self.window_settings = {
                    'width': self.main_window.root.winfo_width(),
                    'height': self.main_window.root.winfo_height(),
                    'x': self.main_window.root.winfo_x(),
                    'y': self.main_window.root.winfo_y()
                }
            except:
                pass

            # Combine all settings
            all_settings = {
                **strategy_settings,
                'event_choice': event_choice_settings,
                'window': self.window_settings
            }

            # Save to file
            with open('bot_settings.json', 'w') as f:
                json.dump(all_settings, f, indent=2)

            # Update race manager filters - race_manager is now safely initialized
            if hasattr(self.main_window, 'race_manager') and self.main_window.race_manager:
                race_filters = {
                    'track': strategy_settings.get('track', {}),
                    'distance': strategy_settings.get('distance', {}),
                    'grade': strategy_settings.get('grade', {})
                }
                self.main_window.race_manager.update_filters(race_filters)

        except Exception as e:
            self.main_window.log_message(f"Warning: Could not save settings: {e}")

    def load_settings(self):
        """Load settings from file"""
        try:
            if not os.path.exists('bot_settings.json'):
                return

            with open('bot_settings.json', 'r') as f:
                settings = json.load(f)

            # Load window settings if they exist
            if 'window' in settings:
                self.window_settings = settings['window']

            # Load tab settings
            self.main_window.strategy_tab.load_settings(settings)
            self.main_window.event_choice_tab.load_settings(settings.get('event_choice', {}))

            # Update race manager filters - race_manager is now safely initialized
            if hasattr(self.main_window, 'race_manager') and self.main_window.race_manager:
                race_filters = {
                    'track': settings.get('track', {}),
                    'distance': settings.get('distance', {}),
                    'grade': settings.get('grade', {})
                }
                self.main_window.race_manager.update_filters(race_filters)

        except Exception as e:
            self.main_window.log_message(f"Warning: Could not load settings: {e}")