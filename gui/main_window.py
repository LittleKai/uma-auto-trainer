import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from datetime import datetime
import keyboard
import json
import os

from core.execute import set_log_callback, career_lobby, set_stop_flag
from core.race_manager import RaceManager, DateManager
from key_validator import validate_application_key, is_key_valid

from gui.components.status_section import StatusSection
from gui.components.log_section import LogSection
from gui.tabs.strategy_tab import StrategyTab
from gui.tabs.event_choice_tab import EventChoiceTab
from gui.utils.game_window_monitor import GameWindowMonitor


class UmaAutoGUI:
    """Main GUI application class with tabbed interface"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Uma Musume Auto Train - Developed by LittleKai!")

        # Initialize managers
        self.game_monitor = GameWindowMonitor(self)

        # Initialize variables
        self.init_variables()

        # Load settings first to get window position
        self.load_initial_settings()

        # Setup GUI components
        self.setup_gui()

        # Initialize core systems
        self.race_manager = RaceManager()
        set_log_callback(self.log_message)

        # Setup events and monitoring
        self.setup_events()
        self.start_monitoring()

    def init_variables(self):
        """Initialize all GUI variables"""
        # Bot state
        self.is_running = False
        self.bot_thread = None
        self.key_valid = False
        self.initial_key_validation_done = False

        # Default window settings
        self.window_settings = {
            'width': 700,
            'height': 900,
            'x': 100,
            'y': 20
        }

        # All settings will be handled by tab modules
        self.all_settings = {}

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

    def setup_gui(self):
        """Setup the main GUI interface"""
        # Setup window from loaded settings
        self.setup_window()

        # Create main container with scrollable area
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create scrollable content
        self.create_scrollable_content(main_container)

        # Load tab settings after GUI is created
        self.load_tab_settings()

    def load_tab_settings(self):
        """Load tab settings after tabs are created"""
        try:
            if not os.path.exists('bot_settings.json'):
                return

            with open('bot_settings.json', 'r') as f:
                settings = json.load(f)

            # Load tab settings
            self.strategy_tab.load_settings(settings)
            self.event_choice_tab.load_settings(settings.get('event_choice', {}))

            # Update race manager filters
            race_filters = {
                'track': settings.get('track', {}),
                'distance': settings.get('distance', {}),
                'grade': settings.get('grade', {})
            }
            self.race_manager.update_filters(race_filters)

        except Exception as e:
            self.log_message(f"Warning: Could not load tab settings: {e}")

    def setup_window(self):
        """Setup window with loaded settings"""
        settings = self.window_settings

        width = max(650, settings.get('width', 700))
        height = max(850, settings.get('height', 900))

        # Get saved position or use default
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

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
        self.root.minsize(650, 850)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.resizable(True, True)
        self.root.attributes('-topmost', True)

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
        self.create_tabbed_section(main_frame, row=2)
        self.create_control_section(main_frame, row=3)
        self.log_section = LogSection(main_frame, self, row=4)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel
        self.bind_mousewheel(canvas)

        # Configure scrolling region
        self.root.after(100, lambda: canvas.configure(scrollregion=canvas.bbox("all")))

    def create_header_section(self, parent, row):
        """Create header section with title and region settings button"""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        header_frame.columnconfigure(0, weight=1)

        # Title
        title_container = ttk.Frame(header_frame)
        title_container.pack(side=tk.LEFT)

        title_label = ttk.Label(title_container, text="Uma Musume Auto Train",
                                font=("Arial", 14, "bold"))
        title_label.pack(anchor=tk.W)

        # Settings button
        settings_container = ttk.Frame(header_frame)
        settings_container.pack(side=tk.RIGHT)

        ttk.Button(settings_container, text="⚙ Region Settings",
                   command=self.open_region_settings).pack()

    def create_tabbed_section(self, parent, row):
        """Create tabbed section with Strategy and Event Choice tabs"""
        notebook = ttk.Notebook(parent)
        notebook.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 15))

        # Strategy tab
        strategy_frame = ttk.Frame(notebook)
        notebook.add(strategy_frame, text="Strategy & Filters")
        self.strategy_tab = StrategyTab(strategy_frame, self)

        # Event Choice tab
        event_choice_frame = ttk.Frame(notebook)
        notebook.add(event_choice_frame, text="Event Choice")
        self.event_choice_tab = EventChoiceTab(event_choice_frame, self)

    def create_control_section(self, parent, row):
        """Create bot control buttons section"""
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        control_frame.columnconfigure(0, weight=1)
        control_frame.columnconfigure(1, weight=1)

        # Start button
        self.start_button = ttk.Button(
            control_frame,
            text="Start (F1)",
            command=self.start_bot
        )
        self.start_button.grid(row=0, column=0, padx=(0, 5), sticky=(tk.W, tk.E), ipady=5)

        # Stop button
        self.stop_button = ttk.Button(
            control_frame,
            text="Stop (F3)",
            command=self.stop_bot,
            state="disabled"
        )
        self.stop_button.grid(row=0, column=1, padx=(5, 0), sticky=(tk.W, tk.E), ipady=5)

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

    def setup_keyboard_shortcuts(self):
        """Setup global keyboard shortcuts"""
        try:
            keyboard.add_hotkey('f1', self.start_bot)
            keyboard.add_hotkey('f3', self.enhanced_stop_bot)
            keyboard.add_hotkey('f5', self.force_exit_program)
        except Exception as e:
            self.log_message(f"Warning: Could not setup keyboard shortcuts: {e}")

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
        self.set_running_state(True)
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
        self.set_running_state(False)
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

    def set_running_state(self, is_running):
        """Update button states based on running status"""
        if is_running:
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
        else:
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")

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
        return self.event_choice_tab.get_settings()

    def get_current_settings(self):
        """Get current strategy settings for bot logic"""
        strategy_settings = self.strategy_tab.get_settings()
        event_choice_settings = self.event_choice_tab.get_settings()

        # Combine settings for bot logic
        return {
            **strategy_settings,
            'event_choice': event_choice_settings
        }

    def save_settings(self):
        """Save all settings to file"""
        try:
            # Collect settings from all tabs
            strategy_settings = self.strategy_tab.get_settings()
            event_choice_settings = self.event_choice_tab.get_settings()

            # Save current window settings
            try:
                self.root.update_idletasks()
                self.window_settings = {
                    'width': self.root.winfo_width(),
                    'height': self.root.winfo_height(),
                    'x': self.root.winfo_x(),
                    'y': self.root.winfo_y()
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

            # Update race manager filters
            race_filters = {
                'track': strategy_settings.get('track', {}),
                'distance': strategy_settings.get('distance', {}),
                'grade': strategy_settings.get('grade', {})
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

            # Load window settings if they exist
            if 'window' in settings:
                self.window_settings = settings['window']

            # Load tab settings
            self.strategy_tab.load_settings(settings)
            self.event_choice_tab.load_settings(settings.get('event_choice', {}))

            # Update race manager filters
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
        self.save_settings()
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