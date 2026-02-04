import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime

from gui.window_manager import WindowManager
from gui.bot_controller import BotController
from gui.components.status_section import StatusSection
from gui.components.log_section import LogSection
from gui.tabs.strategy_tab import StrategyTab
from gui.tabs.event_choice_tab import EventChoiceTab
from gui.tabs.team_trials_tab import TeamTrialsTab
from gui.utils.game_window_monitor import GameWindowMonitor

from core.execute import set_log_callback
from core.race_manager import RaceManager
from key_validator import validate_application_key


class UmaAutoGUI:
    """Main GUI application class with tabbed interface"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Uma Musume Auto Train - Developed by LittleKai!")

        from utils.constants import load_scenario_from_settings
        load_scenario_from_settings()

        # Initialize managers first
        self.game_monitor = GameWindowMonitor(self)
        self.race_manager = RaceManager()  # Initialize race_manager early

        # Initialize components
        self.window_manager = WindowManager(self)
        self.bot_controller = BotController(self)

        # Initialize variables
        self.init_variables()

        # Load settings first to get window position
        self.window_manager.load_initial_settings()

        # Setup GUI components
        self.setup_gui()

        # Initialize core systems
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
        self.scenario_selection = tk.StringVar(value="URA Final")
        # All settings will be handled by tab modules
        self.all_settings = {}

    def setup_gui(self):
        """Setup the main GUI interface"""
        # Setup window from loaded settings
        self.window_manager.setup_window()

        # Create main container with scrollable area
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create scrollable content
        self.create_scrollable_content(main_container)

        # Load tab settings after GUI is created
        self.window_manager.load_tab_settings()

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
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Bind canvas resize to stretch scrollable_frame width
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(window_id, width=e.width))

        # Main content frame
        main_frame = ttk.Frame(scrollable_frame, padding="5")
        main_frame.pack(fill=tk.X, expand=False)
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

        # Settings buttons container
        settings_container = ttk.Frame(header_frame)
        settings_container.pack(side=tk.RIGHT)

        ttk.Button(settings_container, text="⚙ Config",
                   command=self.open_config_settings).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(settings_container, text="⚙ Region Settings",
                   command=self.open_region_settings).pack(side=tk.LEFT)

    def create_tabbed_section(self, parent, row):
        """Create tabbed section with Strategy, Event Choice, and Team Trials tabs"""
        notebook = ttk.Notebook(parent)
        # Add sticky N to prevent vertical expansion
        notebook.grid(row=row, column=0, sticky=(tk.W, tk.E, tk.N), pady=(0, 15))

        # Strategy tab
        strategy_frame = ttk.Frame(notebook)
        notebook.add(strategy_frame, text="Strategy & Filters")
        self.strategy_tab = StrategyTab(strategy_frame, self)

        # Event Choice tab
        event_choice_frame = ttk.Frame(notebook)
        notebook.add(event_choice_frame, text="Event Choice")
        self.event_choice_tab = EventChoiceTab(event_choice_frame, self)

        # Daily Activities tab
        team_trials_frame = ttk.Frame(notebook)
        notebook.add(team_trials_frame, text="Daily Activities")
        self.team_trials_tab = TeamTrialsTab(team_trials_frame, self)

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
        self.bot_controller.setup_keyboard_shortcuts()

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

    def open_config_settings(self):
        """Open config settings dialog"""
        try:
            from gui.dialogs.config_dialog import ConfigDialog
            ConfigDialog(self.root)
        except ImportError as e:
            self.log_message(f"Error: Could not import config dialog: {e}")
            messagebox.showerror("Error", "Config dialog module not found.")
        except Exception as e:
            self.log_message(f"Error opening config settings: {e}")
            messagebox.showerror("Error", f"Failed to open config settings: {e}")


    # Settings methods
    def get_event_choice_settings(self):
        """Get current event choice settings"""
        return self.event_choice_tab.get_settings()

    def get_team_trials_settings(self):
        """Get current team trials settings"""
        return self.team_trials_tab.get_settings()

    def get_current_settings(self):
        """Get current strategy settings for bot logic"""
        strategy_settings = self.strategy_tab.get_settings()
        event_choice_settings = self.event_choice_tab.get_settings()
        team_trials_settings = self.team_trials_tab.get_settings()

        # Combine settings for bot logic
        return {
            **strategy_settings,
            'event_choice': event_choice_settings,
            'team_trials': team_trials_settings
        }

    def save_settings(self):
        """Save all settings to file"""
        self.window_manager.save_settings()

    def load_settings(self):
        """Load settings from file"""
        self.window_manager.load_settings()

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

    # Bot control delegation methods
    def start_bot(self):
        """Delegate to bot controller"""
        self.bot_controller.start_bot()

    # Cleanup methods
    def on_closing(self):
        """Handle window close event"""
        self.save_settings()
        self.stop_bot()

        try:
            import keyboard
            keyboard.unhook_all()
        except:
            pass

        self.root.destroy()

    def set_running_state(self, is_running):
        """Update button states based on running status"""
        if is_running:
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
        else:
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")

    def set_team_trials_running_state(self, is_running):
        """Update button states when team trials is running"""
        if is_running:
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
        else:
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")

    def stop_bot(self):
        """Delegate to bot controller and handle team trials"""
        # Stop main bot
        self.bot_controller.stop_bot()

        # Also stop team trials if running
        if hasattr(self, 'team_trials_tab'):
            team_trials_tab = self.team_trials_tab
            if hasattr(team_trials_tab, 'is_team_trials_running') and team_trials_tab.is_team_trials_running:
                team_trials_tab.stop_team_trials()

    def enhanced_stop_bot(self):
        """Delegate to bot controller"""
        self.bot_controller.enhanced_stop_bot()

    def force_exit_program(self):
        """Delegate to bot controller"""
        self.bot_controller.force_exit_program()

    def should_stop_for_conditions(self, game_state):
        """
        Check all stop conditions and return True if any condition is met
        This function should be added to the main GUI window class
        """
        return self.bot_controller.should_stop_for_conditions(game_state)

    def update_strategy_filters(self, uma_data):
        """Update Strategy Tab filters based on Uma Musume data

        Args:
            uma_data (dict): Dictionary containing track and distance preferences
                            Format: {'turf': bool, 'dirt': bool, 'sprint': bool,
                                    'mile': bool, 'medium': bool, 'long': bool}
        """
        try:
            # Get strategy tab reference
            strategy_tab = getattr(self, 'strategy_tab', None)
            if strategy_tab:
                # Update track filters
                strategy_tab.track_filters['turf'].set(uma_data.get('turf', False))
                strategy_tab.track_filters['dirt'].set(uma_data.get('dirt', False))

                # Update distance filters
                strategy_tab.distance_filters['sprint'].set(uma_data.get('sprint', False))
                strategy_tab.distance_filters['mile'].set(uma_data.get('mile', False))
                strategy_tab.distance_filters['medium'].set(uma_data.get('medium', False))
                strategy_tab.distance_filters['long'].set(uma_data.get('long', False))

                # Trigger auto-save for strategy tab
                self.save_settings()

        except Exception as e:
            print(f"Warning: Could not update strategy filters: {e}")

    # Alternative method if you want to call strategy tab directly
    def update_strategy_filters_direct(self, uma_data):
        """Direct update of Strategy Tab filters without going through main window

        Args:
            uma_data (dict): Dictionary containing track and distance preferences
        """
        try:
            # Access strategy tab through tabs collection
            if hasattr(self, 'tabs') and 'Strategy' in self.tabs:
                strategy_tab = self.tabs['Strategy']
            elif hasattr(self, 'strategy_tab'):
                strategy_tab = self.strategy_tab
            else:
                return

            # Update track filters
            if hasattr(strategy_tab, 'track_filters'):
                strategy_tab.track_filters['turf'].set(uma_data.get('turf', False))
                strategy_tab.track_filters['dirt'].set(uma_data.get('dirt', False))

            # Update distance filters
            if hasattr(strategy_tab, 'distance_filters'):
                strategy_tab.distance_filters['sprint'].set(uma_data.get('sprint', False))
                strategy_tab.distance_filters['mile'].set(uma_data.get('mile', False))
                strategy_tab.distance_filters['medium'].set(uma_data.get('medium', False))
                strategy_tab.distance_filters['long'].set(uma_data.get('long', False))

            # Save settings
            self.save_settings()

        except Exception as e:
            print(f"Warning: Could not update strategy filters: {e}")

    def run(self):
        """Start the GUI application"""
        self.log_message("Configure strategy settings and race filters before starting.")
        self.log_message("Priority Strategies:")
        self.log_message("• G1/G2 (no training): Prioritize racing, skip training")
        self.log_message("• Train Score 2.5+/3+/3.5+/4+: Train only if score meets threshold")
        self.log_message("Use F1 to start, F3 to stop, F5 to force exit program.")

        self.root.mainloop()