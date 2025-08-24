import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import pygetwindow as gw
from datetime import datetime
import keyboard
import sys
import os
import json

from core.execute import set_log_callback, career_lobby, set_stop_flag
from core.race_manager import RaceManager, DateManager
from key_validator import validate_application_key, is_key_valid

class UmaAutoGUI:
  def __init__(self):
    self.root = tk.Tk()
    self.root.title("Uma Musume Auto Train")

    # Calculate window dimensions based on content
    screen_width = self.root.winfo_screenwidth()
    screen_height = self.root.winfo_screenheight()

    # Adjusted window dimensions for better content fit
    window_width = 700
    window_height = 950

    # Position window on the right side with better spacing
    x = screen_width // 2 + 20
    y = max(50, (screen_height - window_height) // 2)

    self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    self.root.minsize(600, 750)

    # Keep window always on top
    self.root.attributes('-topmost', True)

    # Variables
    self.is_running = False
    self.bot_thread = None
    self.key_valid = False
    self.initial_key_validation_done = False

    # Race manager
    self.race_manager = RaceManager()

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

    # Option variables
    self.allow_continuous_racing = tk.BooleanVar(value=True)
    self.manual_event_handling = tk.BooleanVar(value=False)

    # Stop condition variables
    self.stop_on_infirmary = tk.BooleanVar(value=False)
    self.stop_on_need_rest = tk.BooleanVar(value=False)
    self.stop_on_low_mood = tk.BooleanVar(value=False)
    self.stop_on_race_day = tk.BooleanVar(value=False)

    # Setup GUI
    self.setup_gui()

    # Setup keyboard shortcuts
    self.setup_keyboard_shortcuts()

    # Set log callback for execute module
    set_log_callback(self.log_message)

    # Bind window close event
    self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # Load settings from file if exists
    self.load_settings()

    # Check key validation on startup
    self.check_key_validation()

    # Start game window monitoring
    self.start_game_window_monitoring()

  def setup_gui(self):
    """Setup the main GUI interface with improved layout"""
    # Create main container with padding
    main_container = ttk.Frame(self.root)
    main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Create canvas and scrollbar for scrollable content
    canvas = tk.Canvas(main_container)
    scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    # Configure scrollable frame
    scrollable_frame.bind(
      "<Configure>",
      lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Main content frame with proper padding
    main_frame = ttk.Frame(scrollable_frame)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Configure grid weights for proper resizing
    main_frame.columnconfigure(0, weight=1)

    # Setup all sections with improved spacing
    self.setup_header_section(main_frame)
    self.setup_status_section(main_frame)
    self.setup_strategy_section(main_frame)
    self.setup_race_filters_and_stop_conditions_section(main_frame)
    self.setup_control_buttons_section(main_frame)
    self.setup_activity_log_section(main_frame)
    self.setup_shortcuts_info_section(main_frame)

    # Pack canvas and scrollbar with proper fill
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Bind mousewheel to canvas for better scrolling
    def on_mousewheel(event):
      canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    canvas.bind("<MouseWheel>", on_mousewheel)

  def setup_header_section(self, parent):
    """Setup the header section with title and settings button"""
    title_frame = ttk.Frame(parent)
    title_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
    title_frame.columnconfigure(0, weight=1)

    # Title container
    title_container = ttk.Frame(title_frame)
    title_container.pack(side=tk.LEFT)

    # Main title
    title_label = ttk.Label(title_container, text="Uma Musume Auto Train",
                            font=("Arial", 16, "bold"))
    title_label.pack(anchor=tk.W)

    # Subtitle
    subtitle_label = ttk.Label(title_container, text="(Developed by LittleKai!)",
                               font=("Arial", 10), foreground="gray")
    subtitle_label.pack(anchor=tk.W)

    # Settings button
    settings_button = ttk.Button(title_frame, text="⚙ Region Settings",
                                 command=self.open_region_settings)
    settings_button.pack(side=tk.RIGHT)

  def setup_status_section(self, parent):
    """Setup the status monitoring section with improved layout"""
    status_frame = ttk.LabelFrame(parent, text="Status", padding="10")
    status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
    status_frame.columnconfigure(0, weight=1)
    status_frame.columnconfigure(1, weight=1)

    # Left column frame
    left_column = ttk.Frame(status_frame)
    left_column.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N), padx=(0, 15))
    left_column.columnconfigure(1, weight=1)

    # Right column frame
    right_column = ttk.Frame(status_frame)
    right_column.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N))
    right_column.columnconfigure(1, weight=1)

    # Left column content
    ttk.Label(left_column, text="Bot Status:", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky=tk.W, pady=2)
    self.status_label = ttk.Label(left_column, text="Stopped", foreground="red")
    self.status_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)

    ttk.Label(left_column, text="Current Date:", font=("Arial", 9, "bold")).grid(row=1, column=0, sticky=tk.W, pady=2)
    self.date_label = ttk.Label(left_column, text="Unknown", foreground="blue")
    self.date_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)

    ttk.Label(left_column, text="Energy:", font=("Arial", 9, "bold")).grid(row=2, column=0, sticky=tk.W, pady=2)
    self.energy_label = ttk.Label(left_column, text="Unknown", foreground="blue")
    self.energy_label.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=2)

    # Right column content
    ttk.Label(right_column, text="Game Window:", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky=tk.W, pady=2)
    self.game_status_label = ttk.Label(right_column, text="Checking...", foreground="orange")
    self.game_status_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)

    ttk.Label(right_column, text="Key Status:", font=("Arial", 9, "bold")).grid(row=1, column=0, sticky=tk.W, pady=2)
    self.key_status_label = ttk.Label(right_column, text="Checking...", foreground="orange")
    self.key_status_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)

  def setup_strategy_section(self, parent):
    """Setup the strategy settings section with better spacing"""
    strategy_frame = ttk.LabelFrame(parent, text="Strategy Settings", padding="10")
    strategy_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
    strategy_frame.columnconfigure(1, weight=1)
    strategy_frame.columnconfigure(3, weight=1)

    # Row 0: Minimum Mood and Priority Strategy
    ttk.Label(strategy_frame, text="Minimum Mood:", font=("Arial", 9)).grid(row=0, column=0, sticky=tk.W, padx=(0, 5), pady=5)
    mood_dropdown = ttk.Combobox(strategy_frame, textvariable=self.minimum_mood,
                                 values=["AWFUL", "BAD", "NORMAL", "GOOD", "GREAT"],
                                 state="readonly", width=12)
    mood_dropdown.grid(row=0, column=1, sticky=tk.W, padx=(0, 20), pady=5)
    mood_dropdown.bind('<<ComboboxSelected>>', lambda e: self.save_settings())

    ttk.Label(strategy_frame, text="Priority Strategy:", font=("Arial", 9)).grid(row=0, column=2, sticky=tk.W, padx=(0, 5), pady=5)
    priority_dropdown = ttk.Combobox(strategy_frame, textvariable=self.priority_strategy,
                                     values=[
                                       "G1 (no training)",
                                       "G2 (no training)",
                                       "Train Score 2.5+",
                                       "Train Score 3+",
                                       "Train Score 3.5+",
                                       "Train Score 4+",
                                       "Train Score 4.5+"
                                     ],
                                     state="readonly", width=22)
    priority_dropdown.grid(row=0, column=3, sticky=tk.W, pady=5)
    priority_dropdown.bind('<<ComboboxSelected>>', lambda e: self.save_settings())

    # Row 1: Checkboxes with better spacing
    continuous_racing_check = ttk.Checkbutton(strategy_frame,
                                              text="Allow Continuous Racing (>3 races)",
                                              variable=self.allow_continuous_racing,
                                              command=self.save_settings)
    continuous_racing_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))

    manual_event_check = ttk.Checkbutton(strategy_frame,
                                         text="Manual Event Handling (pause on events)",
                                         variable=self.manual_event_handling,
                                         command=self.save_settings)
    manual_event_check.grid(row=1, column=2, columnspan=2, sticky=tk.W, pady=(10, 5))

  def setup_race_filters_and_stop_conditions_section(self, parent):
    """Setup the race filters and stop conditions section with horizontal layout"""
    # Main container for race filters and stop conditions
    filters_container = ttk.Frame(parent)
    filters_container.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
    filters_container.columnconfigure(0, weight=1)
    filters_container.columnconfigure(1, weight=1)

    # Race filters section
    filter_frame = ttk.LabelFrame(filters_container, text="Race Filters", padding="10")
    filter_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N), padx=(0, 10))
    filter_frame.columnconfigure(0, weight=1)
    filter_frame.columnconfigure(1, weight=1)
    filter_frame.columnconfigure(2, weight=1)

    # Track filters
    track_frame = ttk.LabelFrame(filter_frame, text="Track Type", padding="8")
    track_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N), padx=(0, 5))

    ttk.Checkbutton(track_frame, text="Turf", variable=self.track_filters['turf'],
                    command=self.save_settings).pack(anchor=tk.W, pady=2)
    ttk.Checkbutton(track_frame, text="Dirt", variable=self.track_filters['dirt'],
                    command=self.save_settings).pack(anchor=tk.W, pady=2)

    # Distance filters
    distance_frame = ttk.LabelFrame(filter_frame, text="Distance", padding="8")
    distance_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N), padx=5)

    # Create 2x2 grid for distance checkboxes
    distance_inner = ttk.Frame(distance_frame)
    distance_inner.pack(fill=tk.BOTH, expand=True)

    ttk.Checkbutton(distance_inner, text="Sprint", variable=self.distance_filters['sprint'],
                    command=self.save_settings).grid(row=0, column=0, sticky=tk.W, pady=2)
    ttk.Checkbutton(distance_inner, text="Mile", variable=self.distance_filters['mile'],
                    command=self.save_settings).grid(row=1, column=0, sticky=tk.W, pady=2)
    ttk.Checkbutton(distance_inner, text="Medium", variable=self.distance_filters['medium'],
                    command=self.save_settings).grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
    ttk.Checkbutton(distance_inner, text="Long", variable=self.distance_filters['long'],
                    command=self.save_settings).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)

    # Grade filters
    grade_frame = ttk.LabelFrame(filter_frame, text="Grade", padding="8")
    grade_frame.grid(row=0, column=2, sticky=(tk.W, tk.E, tk.N), padx=(5, 0))

    # Create 2x2 grid for grade checkboxes
    grade_inner = ttk.Frame(grade_frame)
    grade_inner.pack(fill=tk.BOTH, expand=True)

    ttk.Checkbutton(grade_inner, text="G1", variable=self.grade_filters['g1'],
                    command=self.save_settings).grid(row=0, column=0, sticky=tk.W, pady=2)
    ttk.Checkbutton(grade_inner, text="G2", variable=self.grade_filters['g2'],
                    command=self.save_settings).grid(row=1, column=0, sticky=tk.W, pady=2)
    ttk.Checkbutton(grade_inner, text="G3", variable=self.grade_filters['g3'],
                    command=self.save_settings).grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)

    # Stop conditions section
    stop_conditions_frame = ttk.LabelFrame(filters_container, text="Stop Conditions", padding="10")
    stop_conditions_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N))

    ttk.Checkbutton(stop_conditions_frame, text="Stop when infirmary needed (day >24)",
                    variable=self.stop_on_infirmary, command=self.save_settings).pack(anchor=tk.W, pady=2)
    ttk.Checkbutton(stop_conditions_frame, text="Stop when need rest (day >24)",
                    variable=self.stop_on_need_rest, command=self.save_settings).pack(anchor=tk.W, pady=2)
    ttk.Checkbutton(stop_conditions_frame, text="Stop when low mood (day >24)",
                    variable=self.stop_on_low_mood, command=self.save_settings).pack(anchor=tk.W, pady=2)
    ttk.Checkbutton(stop_conditions_frame, text="Stop when race day",
                    variable=self.stop_on_race_day, command=self.save_settings).pack(anchor=tk.W, pady=2)

  def setup_control_buttons_section(self, parent):
    """Setup the control buttons section without pause button"""
    button_frame = ttk.Frame(parent)
    button_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
    button_frame.columnconfigure(0, weight=1)
    button_frame.columnconfigure(1, weight=1)

    # Start button
    self.start_button = ttk.Button(button_frame, text="Start (F1)",
                                   command=self.start_bot)
    self.start_button.grid(row=0, column=0, padx=(0, 5), sticky=(tk.W, tk.E), ipady=5)

    # Stop button
    self.stop_button = ttk.Button(button_frame, text="Stop (F3)",
                                  command=self.stop_bot, state="disabled")
    self.stop_button.grid(row=0, column=1, padx=(5, 0), sticky=(tk.W, tk.E), ipady=5)

  def setup_activity_log_section(self, parent):
    """Setup the activity log section with proper sizing"""
    log_frame = ttk.LabelFrame(parent, text="Activity Log", padding="10")
    log_frame.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
    log_frame.columnconfigure(0, weight=1)
    log_frame.rowconfigure(0, weight=1)

    # Log text area with appropriate height
    self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=70, wrap=tk.WORD)
    self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    # Clear log button
    clear_button = ttk.Button(log_frame, text="Clear Log", command=self.clear_log)
    clear_button.grid(row=1, column=0, sticky=tk.W, pady=(8, 0))

  def setup_shortcuts_info_section(self, parent):
    """Setup the keyboard shortcuts info section without F2"""
    shortcuts_frame = ttk.LabelFrame(parent, text="Keyboard Shortcuts", padding="8")
    shortcuts_frame.grid(row=6, column=0, sticky=(tk.W, tk.E))

    shortcuts_text = ("F1: Start Bot | F3: Stop Bot | F5: Force Exit Program")
    ttk.Label(shortcuts_frame, text=shortcuts_text, font=("Arial", 9)).pack()

  def start_game_window_monitoring(self):
    """Start monitoring game window status in background"""
    def monitor_game_window():
      while True:
        try:
          self.check_game_window()
          time.sleep(2)
        except Exception as e:
          pass

    monitor_thread = threading.Thread(target=monitor_game_window, daemon=True)
    monitor_thread.start()

  def check_game_window(self):
    """Enhanced game window detection with multiple search patterns"""
    try:
      window_titles = ["Umamusume", "ウマ娘", "Uma Musume", "DMM GAME PLAYER"]

      found_window = None
      window_title_found = ""

      for title in window_titles:
        try:
          windows = gw.getWindowsWithTitle(title)
          if windows:
            found_window = windows[0]
            window_title_found = title
            break
        except Exception:
          continue

      if found_window:
        try:
          is_active = found_window.isActive
          window_info = f"Found ({window_title_found})"

          if is_active:
            self.root.after(0, self._update_game_status, f"{window_info} - Active", "green")
            return True
          else:
            self.root.after(0, self._update_game_status, f"{window_info} - Inactive", "orange")
            return False
        except Exception as e:
          self.root.after(0, self._update_game_status, f"{window_info} - Error", "red")
          return False
      else:
        all_windows = []
        try:
          all_windows = gw.getAllWindows()
          game_related = [w for w in all_windows if any(keyword in w.title.lower()
                                                        for keyword in ['uma', 'ウマ', 'dmm', 'game']) and w.title.strip()]

          if game_related:
            titles = [w.title[:30] + "..." if len(w.title) > 30 else w.title for w in game_related[:3]]
            hint = f"Similar: {', '.join(titles)}"
            self.root.after(0, self._update_game_status, f"Not Found - {hint}", "red")
          else:
            self.root.after(0, self._update_game_status, "Not Found - Please start game", "red")
        except Exception:
          self.root.after(0, self._update_game_status, "Not Found - Detection Error", "red")

        return False

    except Exception as e:
      self.root.after(0, self._update_game_status, f"Error: {str(e)[:30]}", "red")
      return False

  def focus_umamusume(self):
    """Enhanced game window focusing with multiple title search"""
    try:
      window_titles = ["Umamusume", "ウマ娘", "Uma Musume", "DMM GAME PLAYER"]

      found_window = None
      for title in window_titles:
        try:
          windows = gw.getWindowsWithTitle(title)
          if windows:
            found_window = windows[0]
            break
        except Exception:
          continue

      if not found_window:
        all_windows = gw.getAllWindows()
        game_windows = [w for w in all_windows if any(keyword in w.title.lower()
                                                      for keyword in ['uma', 'ウマ', 'dmm']) and w.title.strip()]
        if game_windows:
          found_window = game_windows[0]

      if not found_window:
        raise Exception("No game window found with any recognized title")

      if found_window.isMinimized:
        found_window.restore()
      found_window.activate()

      try:
        found_window.maximize()
      except:
        pass

      time.sleep(0.5)
      return True

    except Exception as e:
      self.log_message(f"Error focusing game window: {e}")
      self.log_message("Please ensure the game is running and window title contains 'Umamusume', 'ウマ娘', 'Uma Musume', or 'DMM GAME PLAYER'")
      return False

  def check_key_validation(self):
    """Check key validation status on startup"""
    def check_in_background():
      try:
        is_valid, message = validate_application_key()
        self.key_valid = is_valid
        self.initial_key_validation_done = True

        self.root.after(0, self.update_key_status, is_valid, message)

      except Exception as e:
        self.initial_key_validation_done = True
        self.root.after(0, self.update_key_status, False, f"Validation error: {e}")

    threading.Thread(target=check_in_background, daemon=True).start()

  def update_key_status(self, is_valid, message):
    """Update key status in UI"""
    if is_valid:
      self.key_status_label.config(text="Valid ✓", foreground="green")
    else:
      self.key_status_label.config(text="Invalid ✗", foreground="red")

  def open_region_settings(self):
    """Open the region settings window"""
    try:
      from region_settings import RegionSettingsWindow
      RegionSettingsWindow(self.root)
    except ImportError as e:
      self.log_message(f"Error: Could not import region settings: {e}")
      messagebox.showerror("Error", "Region settings module not found. Please ensure region_settings.py is available.")
    except Exception as e:
      self.log_message(f"Error opening region settings: {e}")
      messagebox.showerror("Error", f"Failed to open region settings: {e}")

  def setup_keyboard_shortcuts(self):
    """Setup global keyboard shortcuts without F2"""
    try:
      keyboard.add_hotkey('f1', self.start_bot)
      keyboard.add_hotkey('f3', self.enhanced_stop_bot)
      keyboard.add_hotkey('f5', self.force_exit_program)
    except Exception as e:
      self.log_message(f"Warning: Could not setup keyboard shortcuts: {e}")

  def enhanced_stop_bot(self):
    """Enhanced F3 stop functionality that immediately stops all operations"""
    self.log_message("[F3] Emergency stop triggered - Stopping all bot operations immediately")
    set_stop_flag(True)
    self.stop_bot()

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
      'stop_on_infirmary': self.stop_on_infirmary.get(),
      'stop_on_need_rest': self.stop_on_need_rest.get(),
      'stop_on_low_mood': self.stop_on_low_mood.get(),
      'stop_on_race_day': self.stop_on_race_day.get()
    }

    try:
      with open('bot_settings.json', 'w') as f:
        json.dump(settings, f, indent=2)

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
      if os.path.exists('bot_settings.json'):
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
          old_strategy = settings['priority_strategy']
          if old_strategy in ["Train 1+ Rainbow", "Train 2+ Rainbow", "Train 3+ Rainbow"]:
            self.priority_strategy.set("Train Score 2.5+")
          elif "với score" in old_strategy:
            if "2 +" in old_strategy:
              self.priority_strategy.set("Train Score 2+")
            elif "2.5 +" in old_strategy:
              self.priority_strategy.set("Train Score 2.5+")
            elif "3 +" in old_strategy:
              self.priority_strategy.set("Train Score 3+")
            elif "3.5 +" in old_strategy:
              self.priority_strategy.set("Train Score 3.5+")
            else:
              self.priority_strategy.set("Train Score 2.5+")
          elif old_strategy == "G1":
            self.priority_strategy.set("G1 (no training)")
          elif old_strategy == "G2":
            self.priority_strategy.set("G2 (no training)")
          else:
            self.priority_strategy.set(old_strategy)

        # Apply option settings
        if 'allow_continuous_racing' in settings:
          self.allow_continuous_racing.set(settings['allow_continuous_racing'])

        if 'manual_event_handling' in settings:
          self.manual_event_handling.set(settings['manual_event_handling'])

        # Apply stop condition settings
        if 'stop_on_infirmary' in settings:
          self.stop_on_infirmary.set(settings['stop_on_infirmary'])
        if 'stop_on_need_rest' in settings:
          self.stop_on_need_rest.set(settings['stop_on_need_rest'])
        if 'stop_on_low_mood' in settings:
          self.stop_on_low_mood.set(settings['stop_on_low_mood'])
        if 'stop_on_race_day' in settings:
          self.stop_on_race_day.set(settings['stop_on_race_day'])

        # Update race manager
        race_filters = {
          'track': settings.get('track', {}),
          'distance': settings.get('distance', {}),
          'grade': settings.get('grade', {})
        }
        self.race_manager.update_filters(race_filters)

    except Exception as e:
      self.log_message(f"Warning: Could not load settings: {e}")

  def get_current_settings(self):
    """Get current strategy settings for bot logic"""
    return {
      'minimum_mood': self.minimum_mood.get(),
      'priority_strategy': self.priority_strategy.get(),
      'allow_continuous_racing': self.allow_continuous_racing.get(),
      'manual_event_handling': self.manual_event_handling.get(),
      'stop_on_infirmary': self.stop_on_infirmary.get(),
      'stop_on_need_rest': self.stop_on_need_rest.get(),
      'stop_on_low_mood': self.stop_on_low_mood.get(),
      'stop_on_race_day': self.stop_on_race_day.get()
    }

  def log_message(self, message):
    """Add message to log with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    formatted_message = f"[{timestamp}] {message}\n"

    self.root.after(0, self._update_log, formatted_message)

  def _update_log(self, message):
    """Update log text widget (must be called from main thread)"""
    self.log_text.insert(tk.END, message)
    self.log_text.see(tk.END)

  def clear_log(self):
    """Clear the log text"""
    self.log_text.delete(1.0, tk.END)

  def update_current_date(self, date_info):
    """Update current date display"""
    if date_info:
      if date_info.get('is_pre_debut', False):
        date_str = f"{date_info['year']} Year Pre-Debut (Day {date_info['absolute_day']}/72)"
      else:
        date_str = f"{date_info['year']} {date_info['month']} {date_info['period']} (Day {date_info['absolute_day']}/72)"
      self.root.after(0, lambda: self.date_label.config(text=date_str, foreground="blue"))
    else:
      self.root.after(0, lambda: self.date_label.config(text="Unknown", foreground="red"))

  def update_energy_display(self, energy_percentage):
    """Update energy display"""
    try:
      with open('config.json', 'r') as f:
        config = json.load(f)
      minimum_energy = config.get('minimum_energy_percentage', 40)
      critical_energy = config.get('critical_energy_percentage', 20)

      if energy_percentage >= minimum_energy:
        color = "green"
      elif energy_percentage >= critical_energy:
        color = "orange"
      else:
        color = "red"

      energy_str = f"{energy_percentage}%"
      self.root.after(0, lambda: self.energy_label.config(text=energy_str, foreground=color))
    except Exception as e:
      self.root.after(0, lambda: self.energy_label.config(text="Error", foreground="red"))

  def _update_game_status(self, status, color):
    """Update game status label"""
    self.game_status_label.config(text=status, foreground=color)

  def start_bot(self):
    """Start the bot using cached key validation result"""
    if self.is_running:
      return

    if not self.initial_key_validation_done:
      self.log_message("Waiting for key validation to complete...")
      return

    if not self.key_valid:
      messagebox.showerror("Key Validation Failed", "Invalid key. Cannot start bot.")
      self.log_message("Bot start failed: Invalid key")
      return

    if not self.focus_umamusume():
      self.log_message("Cannot start bot: Game window not found or cannot be focused")
      return

    set_stop_flag(False)

    self.is_running = True

    # Update UI
    self.start_button.config(state="disabled")
    self.stop_button.config(state="normal")
    self.status_label.config(text="Running", foreground="green")

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
    self.start_button.config(state="normal")
    self.stop_button.config(state="disabled")
    self.status_label.config(text="Stopped", foreground="red")

    self.log_message("Bot stopped")

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

  def emergency_stop(self):
    """Emergency stop - can be called from anywhere"""
    self.root.after(0, self.enhanced_stop_bot)
    self.root.after(0, lambda: self.log_message("EMERGENCY STOP ACTIVATED!"))

  def bot_loop(self):
    """Main bot loop running in separate thread"""
    try:
      self.modified_career_lobby()
    except Exception as e:
      self.log_message(f"Bot error: {e}")
    finally:
      self.root.after(0, self.stop_bot)

  def modified_career_lobby(self):
    """Modified career_lobby that respects GUI controls"""
    career_lobby(self)

  def on_closing(self):
    """Handle window close event"""
    self.stop_bot()
    try:
      keyboard.unhook_all()
    except:
      pass
    self.root.destroy()

  def run(self):
    """Start the GUI"""
    self.log_message("Configure strategy settings and race filters before starting.")
    self.log_message("Priority Strategies:")
    self.log_message("• G1/G2 (no training): Prioritize racing, skip training")
    self.log_message("• Train Score 2+/2.5+/3+/3.5+: Train only if score meets threshold")
    self.log_message("Use F1 to start, F3 to stop, F5 to force exit program.")

    self.root.mainloop()


def main():
  """Main function - create and run GUI"""
  print("Uma Auto - Developed by LittleKai!")
  app = UmaAutoGUI()
  app.run()


if __name__ == "__main__":
  main()