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
from gui.window_manager import WindowManager


class UmaAutoGUI:
    """Main GUI application class with tabbed interface"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Uma Musume Auto Train - Developed by LittleKai!")

        # Initialize window manager
        self.window_manager = WindowManager(self.root)

        # Initialize managers
        self.game_monitor = GameWindowMonitor(self)
        self.race_manager = RaceManager()

        # Initialize bot state variables
        self.is_running = False
        self.bot_thread = None
        self.key_valid = False
        self.initial_key_validation_done = False

        # All settings will be handled by tab modules
        self.all_settings = {}

        # Setup GUI using window manager
        self.window_manager.setup_window()
        self.setup_gui()

        # Initialize core systems
        set_log_callback(self.log_message)

        # Setup events and monitoring
        self.setup_events()
        self.start_monitoring()

    def setup_gui(self):
        """Setup the main GUI interface"""
        # Create main container with scrollable area
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create scrollable content
        self.create_scrollable_content(main_container)

        # Load tab settings after GUI is created
        self.load_tab_settings()

    def create_scrollable_content(self, parent):
        """Create the main scrollable content area"""
        # Canvas for scrolling
        self.canvas = tk.Canvas(parent, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Pack canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Bind mouse wheel to canvas
        self.bind_mousewheel()

        # Create GUI components
        self.create_components()

    def bind_mousewheel(self):
        """Bind mouse wheel scrolling to canvas"""
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        self.canvas.bind("<MouseWheel>", _on_mousewheel)

    def create_components(self):
        """Create main GUI components"""
        # Make scrollable frame columns expandable
        self.scrollable_frame.columnconfigure(0, weight=1)

        current_row = 0

        # Status section
        self.status_section = StatusSection(self.scrollable_frame, self, current_row)
        current_row += 1

        # Control buttons section
        self.create_control_section(current_row)
        current_row += 1

        # Tab system
        self.create_tab_system(current_row)
        current_row += 1

        # Log section
        self.log_section = LogSection(self.scrollable_frame, self, current_row)

    def create_control_section(self, row):
        """Create the control buttons section"""
        control_frame = ttk.LabelFrame(self.scrollable_frame, text="Controls", padding="10")
        control_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        control_frame.columnconfigure(0, weight=1)
        control_frame.columnconfigure(1, weight=1)
        control_frame.columnconfigure(2, weight=1)

        # Start button
        self.start_button = ttk.Button(
            control_frame,
            text="🚀 Start Bot (F1)",
            command=self.start_bot,
            style="Accent.TButton"
        )
        self.start_button.grid(row=0, column=0, padx=(0, 5), sticky=(tk.W, tk.E))

        # Pause/Resume button
        self.pause_button = ttk.Button(
            control_frame,
            text="⏸️ Pause (F2)",
            command=self.toggle_pause,
            state=tk.DISABLED
        )
        self.pause_button.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))

        # Stop button
        self.stop_button = ttk.Button(
            control_frame,
            text="🛑 Stop Bot (F3)",
            command=self.stop_bot,
            state=tk.DISABLED
        )
        self.stop_button.grid(row=0, column=2, padx=(5, 0), sticky=(tk.W, tk.E))

        # Hotkey instructions
        hotkey_label = ttk.Label(
            control_frame,
            text="Hotkeys: F1=Start | F2=Pause/Resume | F3=Stop | F5=Force Exit",
            font=("Arial", 8),
            foreground="gray"
        )
        hotkey_label.grid(row=1, column=0, columnspan=3, pady=(10, 0))

    def create_tab_system(self, row):
        """Create the tabbed interface"""
        self.notebook = ttk.Notebook(self.scrollable_frame)
        self.notebook.grid(row=row, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))

        # Strategy Tab
        self.strategy_tab = StrategyTab(self.notebook, self)
        self.notebook.add(self.strategy_tab.frame, text="⚡ Strategy & Filters")

        # Event Choice Tab
        self.event_choice_tab = EventChoiceTab(self.notebook, self)
        self.notebook.add(self.event_choice_tab.frame, text="🎯 Event Choices")

        # Region Settings Tab (using window manager)
        region_frame = self.window_manager.create_region_tab(self.notebook, self)
        self.notebook.add(region_frame, text="📍 Region Settings")

    def start_bot(self):
        """Start the bot"""
        if not self.key_valid:
            messagebox.showerror(
                "Invalid Key",
                "Please enter a valid application key to start the bot."
            )
            return

        if not self.is_running:
            # Save settings before starting
            self.save_all_settings()

            self.is_running = True
            set_stop_flag(False)

            # Update UI
            self.start_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.NORMAL)
            self.status_section.status_label.config(text="Running", foreground="green")

            # Start bot thread
            self.bot_thread = threading.Thread(target=self.bot_worker, daemon=True)
            self.bot_thread.start()

            self.log_message("🚀 Bot started!\n")

    def toggle_pause(self):
        """Toggle bot pause/resume"""
        if self.is_running:
            current_text = self.pause_button.cget("text")
            if "Pause" in current_text:
                # Pause the bot
                set_stop_flag(True)
                self.pause_button.config(text="▶️ Resume (F2)")
                self.status_section.status_label.config(text="Paused", foreground="orange")
                self.log_message("⏸️ Bot paused\n")
            else:
                # Resume the bot
                set_stop_flag(False)
                self.pause_button.config(text="⏸️ Pause (F2)")
                self.status_section.status_label.config(text="Running", foreground="green")
                self.log_message("▶️ Bot resumed\n")

    def stop_bot(self):
        """Stop the bot"""
        if self.is_running:
            self.is_running = False
            set_stop_flag(True)

            # Update UI
            self.start_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.DISABLED, text="⏸️ Pause (F2)")
            self.stop_button.config(state=tk.DISABLED)
            self.status_section.status_label.config(text="Stopped", foreground="red")

            self.log_message("🛑 Bot stopped!\n")

    def bot_worker(self):
        """Bot worker thread function"""
        try:
            # Load current settings for bot execution
            settings = self.get_current_settings()

            # Start the career lobby execution
            career_lobby()

        except Exception as e:
            self.log_message(f"❌ Bot error: {str(e)}\n")
        finally:
            # Ensure bot stops properly
            self.root.after(0, self.stop_bot)

    def setup_events(self):
        """Setup keyboard events and window events"""
        # Keyboard shortcuts
        keyboard.add_hotkey('f1', self.start_bot)
        keyboard.add_hotkey('f2', self.toggle_pause)
        keyboard.add_hotkey('f3', self.stop_bot)
        keyboard.add_hotkey('f5', self.force_exit)

        # Window events
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Bind window position saving
        self.root.bind('<Configure>', self.window_manager.on_window_configure)

    def start_monitoring(self):
        """Start various monitoring tasks"""
        # Start game window monitoring
        self.game_monitor.start_monitoring()

        # Start status updates
        self.update_status()

        # Validate key on startup
        self.root.after(1000, self.validate_key_on_startup)

    def validate_key_on_startup(self):
        """Validate application key on startup"""
        if not self.initial_key_validation_done:
            self.initial_key_validation_done = True
            if hasattr(self.strategy_tab, 'validate_key'):
                self.strategy_tab.validate_key()

    def update_status(self):
        """Update status information periodically"""
        if hasattr(self, 'status_section'):
            # Update date information
            if hasattr(self, 'race_manager') and self.race_manager:
                date_manager = DateManager()
                current_date = date_manager.get_formatted_date()
                if current_date:
                    self.status_section.date_label.config(text=current_date)

        # Schedule next update
        self.root.after(1000, self.update_status)

    def log_message(self, message):
        """Add message to log (thread-safe)"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"

        # Schedule GUI update in main thread
        self.root.after(0, lambda: self.log_section.add_message(formatted_message))

    def load_tab_settings(self):
        """Load settings for all tabs"""
        try:
            if os.path.exists('bot_settings.json'):
                with open('bot_settings.json', 'r') as f:
                    settings = json.load(f)

                # Load strategy tab settings
                if hasattr(self.strategy_tab, 'load_settings'):
                    self.strategy_tab.load_settings(settings)

                # Load event choice tab settings
                if hasattr(self.event_choice_tab, 'load_settings'):
                    self.event_choice_tab.load_settings(settings)

        except Exception as e:
            self.log_message(f"Warning: Could not load tab settings: {e}\n")

    def save_all_settings(self):
        """Save all settings from tabs and window"""
        try:
            settings = {}

            # Get settings from strategy tab
            if hasattr(self.strategy_tab, 'get_settings'):
                strategy_settings = self.strategy_tab.get_settings()
                settings.update(strategy_settings)

            # Get settings from event choice tab
            if hasattr(self.event_choice_tab, 'get_settings'):
                event_settings = self.event_choice_tab.get_settings()
                settings.update(event_settings)

            # Get window settings
            window_settings = self.window_manager.get_window_settings()
            settings['window'] = window_settings

            # Save to file
            with open('bot_settings.json', 'w') as f:
                json.dump(settings, f, indent=2)

            self.all_settings = settings

        except Exception as e:
            self.log_message(f"Warning: Could not save settings: {e}\n")

    def get_current_settings(self):
        """Get current settings from all tabs"""
        settings = {}

        # Get strategy settings
        if hasattr(self.strategy_tab, 'get_settings'):
            strategy_settings = self.strategy_tab.get_settings()
            settings.update(strategy_settings)

        # Get event choice settings
        if hasattr(self.event_choice_tab, 'get_settings'):
            event_settings = self.event_choice_tab.get_settings()
            settings.update(event_settings)

        return settings

    def force_exit(self):
        """Force exit the application"""
        self.log_message("🔴 Force exit triggered!\n")
        self.on_closing()

    def on_closing(self):
        """Handle application closing"""
        try:
            # Save settings before closing
            self.save_all_settings()

            # Stop the bot if running
            if self.is_running:
                self.stop_bot()

            # Stop monitoring
            if hasattr(self, 'game_monitor'):
                self.game_monitor.stop_monitoring()

            # Cleanup keyboard hooks
            keyboard.unhook_all()

        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            self.root.quit()
            self.root.destroy()

    def run(self):
        """Start the GUI application"""
        self.root.mainloop()