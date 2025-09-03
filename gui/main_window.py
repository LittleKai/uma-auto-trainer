import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from datetime import datetime
import keyboard
import json

from core.execute import set_log_callback, career_lobby, set_stop_flag
from core.race_manager import RaceManager, DateManager
from key_validator import validate_application_key, is_key_valid

from gui.window_manager import WindowSizeManager
from gui.dialogs.event_choice_dialog import EventChoiceWindow
from gui.dialogs.stop_conditions_dialog import StopConditionsWindow
from gui.components.status_section import StatusSection
from gui.components.strategy_section import StrategySection
from gui.components.filters_section import FiltersSection
from gui.components.control_section import ControlSection
from gui.components.log_section import LogSection
from gui.utils.game_window_monitor import GameWindowMonitor


class UmaAutoGUI:
    """Main GUI application class"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Uma Musume Auto Train - Developed by LittleKai!")

        # Initialize managers
        self.window_manager = WindowSizeManager(self.root)
        self.game_monitor = GameWindowMonitor(self)

        # Initialize variables
        self.init_variables()

        # Setup GUI components
        self.setup_gui()

        # Initialize core systems
        self.race_manager = RaceManager()
        set_log_callback(self.log_message)

        # Setup events and monitoring
        self.setup_events()
        self.load_settings()
        self.start_monitoring()

    def init_variables(self):
        """Initialize all GUI variables"""
        # Bot state
        self.is_running = False
        self.bot_thread = None
        self.key_valid = False
        self.initial_key_validation_done = False

        # Race filter variables
        self.track_filters = {
            'turf': tk.BooleanVar(value=True),
            'dirt': tk.BooleanVar(value=True)
        }

        self.distance_filters = {
            'sprint': tk.BooleanVar(value=True),
            'mile': tk.BooleanVar(value=True),
            'medium': tk.BooleanVar(value=True),
            'long': tk.BooleanVar(value=True)
        }

        self.grade_filters = {
            'g1': tk.BooleanVar(value=True),
            'g2': tk.BooleanVar(value=True),
            'g3': tk.BooleanVar(value=True)
        }

        # Strategy variables
        self.minimum_mood = tk.StringVar(value="NORMAL")
        self.priority_strategy = tk.StringVar(value="Train Score 2.5+")
        self.allow_continuous_racing = tk.BooleanVar(value=True)
        self.manual_event_handling = tk.BooleanVar(value=False)

        # Stop condition variables
        self.enable_stop_conditions = tk.BooleanVar(value=False)
        self.stop_on_infirmary = tk.BooleanVar(value=False)
        self.stop_on_need_rest = tk.BooleanVar(value=False)
        self.stop_on_low_mood = tk.BooleanVar(value=False)
        self.stop_on_race_day = tk.BooleanVar(value=False)
        self.stop_mood_threshold = tk.StringVar(value="BAD")
        self.stop_before_summer = tk.BooleanVar(value=False)
        self.stop_at_month = tk.BooleanVar(value=False)
        self.target_month = tk.StringVar(value="June")

        # Event choice settings
        self.event_choice_settings = {
            'auto_event_map': False,
            'auto_first_choice': True,
            'uma_musume': 'None',
            'support_cards': ['None'] * 6
        }

    def setup_gui(self):
        """Setup the main GUI interface"""
        # Setup window
        self.window_manager.setup_window()

        # Create main container with scrollable area
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create scrollable content
        self.create_scrollable_content(main_container)

    def create_scrollable_content(self, parent):
        """Create scrollable content area with all sections"""
        # Create canvas and scrollbar
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        # Configure scrolling
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Main content frame
        main_frame = ttk.Frame(scrollable_frame, padding="5")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=1)

        # Create all sections
        self.create_header_section(main_frame, row=0)
        self.status_section = StatusSection(main_frame, self, row=1)
        self.strategy_section = StrategySection(main_frame, self, row=2)
        self.filters_section = FiltersSection(main_frame, self, row=3)
        self.control_section = ControlSection(main_frame, self, row=4)
        self.log_section = LogSection(main_frame, self, row=5)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel
        self.bind_mousewheel(canvas)

        # Configure scrolling region
        self.root.after(100, lambda: canvas.configure(scrollregion=canvas.bbox("all")))

    def create_header_section(self, parent, row):
        """Create header section with title and settings buttons"""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        header_frame.columnconfigure(0, weight=1)

        # Title
        title_container = ttk.Frame(header_frame)
        title_container.pack(side=tk.LEFT)

        title_label = ttk.Label(title_container, text="Uma Musume Auto Train",
                                font=("Arial", 14, "bold"))
        title_label.pack(anchor=tk.W)

        # Settings buttons
        settings_container = ttk.Frame(header_frame)
        settings_container.pack(side=tk.RIGHT)

        ttk.Button(settings_container, text="⚙ Region Settings",
                   command=self.open_region_settings).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(settings_container, text="🎭 Event Choice",
                   command=self.open_event_choice_window).pack(side=tk.LEFT)

    def bind_mousewheel(self, canvas):
        """Bind mousewheel events for scrolling"""
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        def on_mousewheel_linux(event):
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")

        canvas.bind("<MouseWheel>", on_mousewheel)
        canvas.bind("<Button-4>", on_mousewheel_linux)
        canvas.bind("<Button-5>", on_mousewheel_linux)

    def setup_events(self):
        """Setup event handlers"""
        # Window events
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Keyboard shortcuts
        self.setup_keyboard_shortcuts()

        # Variable change events
        self.bind_variable_changes()

    def setup_keyboard_shortcuts(self):
        """Setup global keyboard shortcuts"""
        try:
            keyboard.add_hotkey('f1', self.start_bot)
            keyboard.add_hotkey('f3', self.enhanced_stop_bot)
            keyboard.add_hotkey('f5', self.force_exit_program)
        except Exception as e:
            self.log_message(f"Warning: Could not setup keyboard shortcuts: {e}")

    def bind_variable_changes(self):
        """Bind variable change events to auto-save"""
        variables = [
            *self.track_filters.values(),
            *self.distance_filters.values(),
            *self.grade_filters.values(),
            self.minimum_mood,
            self.priority_strategy,
            self.allow_continuous_racing,
            self.manual_event_handling,
            self.enable_stop_conditions
        ]

        for var in variables:
            var.trace('w', lambda *args: self.save_settings())

    def start_monitoring(self):
        """Start background monitoring"""
        self.game_monitor.start()
        self.check_key_validation()

    def check_key_validation(self):
        """Check key validation status on startup"""
        def check_in_background():
            try:
                is_valid, message = validate_application_key()
                self.key_valid = is_valid
                self.initial_key_validation_done = True
                self.root.after(0, self.status_section.update_key_status, is_valid, message)
            except Exception as e:
                self.initial_key_validation_done = True
                self.root.after(0, self.status_section.update_key_status, False, f"Validation error: {e}")

        threading.Thread(target=check_in_background, daemon=True).start()

    # Dialog methods
    def open_event_choice_window(self):
        """Open event choice configuration window"""
        try:
            EventChoiceWindow(self)
        except Exception as e:
            self.log_message(f"Error opening event choice window: {e}")
            messagebox.showerror("Error", f"Failed to open event choice window: {e}")

    def open_stop_conditions_window(self):
        """Open stop conditions configuration window"""
        try:
            StopConditionsWindow(self)
        except Exception as e:
            self.log_message(f"Error opening stop conditions window: {e}")
            messagebox.showerror("Error", f"Failed to open stop conditions window: {e}")

    def open_region_settings(self):
        """Open region settings window"""
        try:
            from region_settings import RegionSettingsWindow
            RegionSettingsWindow(self.root)
        except ImportError as e:
            self.log_message(f"Error: Could not import region settings: {e}")
            messagebox.showerror("Error", "Region settings module not found.")
        except Exception as e:
            self.log_message(f"Error opening region settings: {e}")
            messagebox.showerror("Error", f"Failed to open region settings: {e}")

    # Bot control methods
    def start_bot(self):
        """Start the bot"""
        if self.is_running:
            return

        if not self.initial_key_validation_done:
            self.log_message("Waiting for key validation to complete...")
            return

        if not self.key_valid:
            messagebox.showerror("Key Validation Failed", "Invalid key. Cannot start bot.")
            self.log_message("Bot start failed: Invalid key")
            return

        if not self.game_monitor.focus_game_window():
            self.log_message("Cannot start bot: Game window not found or cannot be focused")
            return

        set_stop_flag(False)
        self.is_running = True

        # Update UI
        self.control_section.set_running_state(True)
        self.status_section.set_bot_status("Running", "green")

        # Start bot thread
        self.bot_thread = threading.Thread(target=self.bot_loop, daemon=True)
        self.bot_thread.start()

        self.log_message("Bot started successfully!")

    def stop_bot(self):
        """Stop the bot"""
        if not self.is_running:
            return

        set_stop_flag(True)
        self.is_running = False

        # Update UI
        self.control_section.set_running_state(False)
        self.status_section.set_bot_status("Stopped", "red")

        self.log_message("Bot stopped")

    def enhanced_stop_bot(self):
        """Enhanced F3 stop functionality"""
        set_stop_flag(True)
        self.stop_bot()

    def force_exit_program(self):
        """Force exit program - F5 key handler"""
        self.log_message("F5 pressed - Force exiting program...")
        self.stop_bot()
        try:
            keyboard.unhook_all()
        except:
            pass
        import os
        os._exit(0)

    def bot_loop(self):
        """Main bot loop running in separate thread"""
        try:
            career_lobby(self)
        except Exception as e:
            self.log_message(f"Bot error: {e}")
        finally:
            self.root.after(0, self.stop_bot)

    # Settings methods
    def get_event_choice_settings(self):
        """Get current event choice settings"""
        return self.event_choice_settings.copy()

    def save_event_choice_settings(self, settings):
        """Save event choice settings"""
        self.event_choice_settings = settings.copy()
        self.save_settings()

    def get_current_settings(self):
        """Get current strategy settings for bot logic"""
        return {
            'minimum_mood': self.minimum_mood.get(),
            'priority_strategy': self.priority_strategy.get(),
            'allow_continuous_racing': self.allow_continuous_racing.get(),
            'manual_event_handling': self.manual_event_handling.get(),
            'enable_stop_conditions': self.enable_stop_conditions.get(),
            'stop_on_infirmary': self.stop_on_infirmary.get(),
            'stop_on_need_rest': self.stop_on_need_rest.get(),
            'stop_on_low_mood': self.stop_on_low_mood.get(),
            'stop_on_race_day': self.stop_on_race_day.get(),
            'stop_mood_threshold': self.stop_mood_threshold.get(),
            'stop_before_summer': self.stop_before_summer.get(),
            'stop_at_month': self.stop_at_month.get(),
            'target_month': self.target_month.get(),
            'event_choice': self.event_choice_settings
        }

    def save_settings(self):
        """Save all settings to file"""
        settings = {
            'track': {k: v.get() for k, v in self.track_filters.items()},
            'distance': {k: v.get() for k, v in self.distance_filters.items()},
            'grade': {k: v.get() for k, v in self.grade_filters.items()},
            'minimum_mood': self.minimum_mood.get(),
            'priority_strategy': self.priority_strategy.get(),
            'allow_continuous_racing': self.allow_continuous_racing.get(),
            'manual_event_handling': self.manual_event_handling.get(),
            'enable_stop_conditions': self.enable_stop_conditions.get(),
            'stop_on_infirmary': self.stop_on_infirmary.get(),
            'stop_on_need_rest': self.stop_on_need_rest.get(),
            'stop_on_low_mood': self.stop_on_low_mood.get(),
            'stop_on_race_day': self.stop_on_race_day.get(),
            'stop_mood_threshold': self.stop_mood_threshold.get(),
            'stop_before_summer': self.stop_before_summer.get(),
            'stop_at_month': self.stop_at_month.get(),
            'target_month': self.target_month.get(),
            'event_choice': self.event_choice_settings
        }

        try:
            with open('bot_settings.json', 'w') as f:
                json.dump(settings, f, indent=2)

            # Update race manager
            race_filters = {
                'track': settings['track'],
                'distance': settings['distance'],
                'grade': settings['grade']
            }
            self.race_manager.update_filters(race_filters)

        except Exception as e:
            self.log_message(f"Warning: Could not save settings: {e}")

    def load_settings(self):
        """Load settings from file"""
        try:
            if not os.path.exists('bot_settings.json'):
                return

            with open('bot_settings.json', 'r') as f:
                settings = json.load(f)

            # Apply loaded filters
            for k, v in settings.get('track', {}).items():
                if k in self.track_filters:
                    self.track_filters[k].set(v)

            for k, v in settings.get('distance', {}).items():
                if k in self.distance_filters:
                    self.distance_filters[k].set(v)

            for k, v in settings.get('grade', {}).items():
                if k in self.grade_filters:
                    self.grade_filters[k].set(v)

            # Apply strategy settings
            if 'minimum_mood' in settings:
                self.minimum_mood.set(settings['minimum_mood'])
            if 'priority_strategy' in settings:
                self.priority_strategy.set(settings['priority_strategy'])
            if 'allow_continuous_racing' in settings:
                self.allow_continuous_racing.set(settings['allow_continuous_racing'])
            if 'manual_event_handling' in settings:
                self.manual_event_handling.set(settings['manual_event_handling'])

            # Apply stop condition settings
            stop_condition_keys = [
                'enable_stop_conditions', 'stop_on_infirmary', 'stop_on_need_rest',
                'stop_on_low_mood', 'stop_on_race_day', 'stop_mood_threshold',
                'stop_before_summer', 'stop_at_month', 'target_month'
            ]

            for key in stop_condition_keys:
                if key in settings:
                    getattr(self, key).set(settings[key])

            # Apply event choice settings
            if 'event_choice' in settings:
                self.event_choice_settings = settings['event_choice']

            # Update race manager
            race_filters = {
                'track': settings.get('track', {}),
                'distance': settings.get('distance', {}),
                'grade': settings.get('grade', {})
            }
            self.race_manager.update_filters(race_filters)

        except Exception as e:
            self.log_message(f"Warning: Could not load settings: {e}")

    # Status update methods
    def log_message(self, message):
        """Add message to log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        self.root.after(0, self.log_section.add_message, formatted_message)

    def update_current_date(self, date_info):
        """Update current date display"""
        self.status_section.update_date(date_info)

    def update_energy_display(self, energy_percentage):
        """Update energy display"""
        self.status_section.update_energy(energy_percentage)

    def update_game_status(self, status, color):
        """Update game status display"""
        self.status_section.update_game_status(status, color)

    # Cleanup methods
    def on_closing(self):
        """Handle window close event"""
        self.window_manager.save_current_settings()
        self.stop_bot()

        try:
            keyboard.unhook_all()
        except:
            pass

        self.root.destroy()

    def run(self):
        """Start the GUI application"""
        self.log_message("Configure strategy settings and race filters before starting.")
        self.log_message("Priority Strategies:")
        self.log_message("• G1/G2 (no training): Prioritize racing, skip training")
        self.log_message("• Train Score 2.5+/3+/3.5+/4+: Train only if score meets threshold")
        self.log_message("Use F1 to start, F3 to stop, F5 to force exit program.")

        self.root.mainloop()