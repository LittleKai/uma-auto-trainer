import json
import os
import tkinter as tk


class WindowSizeManager:
    """Manages window sizing and positioning with persistent preferences"""

    def __init__(self, root):
        self.root = root
        self.settings_file = "window_settings.json"
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()

        # Define minimum window dimensions
        self.min_width = 650
        self.min_height = 750

        # Default dimensions
        self.default_width = 650
        self.default_height = 750

    def load_window_settings(self):
        """Load window settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading window settings: {e}")

        return self.get_default_settings()

    def save_window_settings(self, width, height, x, y):
        """Save window settings to file"""
        try:
            settings = {
                'width': width,
                'height': height,
                'x': x,
                'y': y
            }
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving window settings: {e}")

    def get_default_settings(self):
        """Get default window settings"""
        x = max(20, self.screen_width // 2) + 20
        y = max(20, (self.screen_height - self.default_height) // 4)

        return {
            'width': self.default_width,
            'height': self.default_height,
            'x': x,
            'y': y
        }

    def setup_window(self):
        """Setup window with saved or default settings"""
        settings = self.load_window_settings()

        width = max(self.min_width, settings.get('width', self.default_width))
        height = max(self.min_height, settings.get('height', self.default_height))
        x = settings.get('x', self.get_default_settings()['x'])
        y = settings.get('y', self.get_default_settings()['y'])

        # Ensure window fits on screen
        if x + width > self.screen_width:
            x = max(0, self.screen_width - width)
        if y + height > self.screen_height:
            y = max(0, self.screen_height - height)

        # Set window properties
        self.root.minsize(self.min_width, self.min_height)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.resizable(True, True)
        self.root.attributes('-topmost', True)

    def save_current_settings(self):
        """Save current window settings"""
        try:
            self.root.update_idletasks()
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            self.save_window_settings(width, height, x, y)
        except Exception as e:
            print(f"Error saving current window settings: {e}")