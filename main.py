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
import platform

from core.execute import set_log_callback, career_lobby, set_stop_flag
from core.race_manager import RaceManager, DateManager
from key_validator import validate_application_key, is_key_valid


class ResponsiveUIManager:
  """Manages responsive UI scaling and positioning based on screen properties"""

  def __init__(self, root):
    self.root = root
    self.screen_width = root.winfo_screenwidth()
    self.screen_height = root.winfo_screenheight()
    self.dpi_scale = self._get_dpi_scale()
    self.screen_category = self._categorize_screen_size()

  def _get_dpi_scale(self):
    """Detect DPI scaling factor"""
    try:
      if platform.system() == "Windows":
        import ctypes
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        dpi = user32.GetDpiForSystem()
        return dpi / 96.0  # 96 DPI is standard
      else:
        # For macOS and Linux, use tkinter's pixel scaling
        return self.root.tk.call('tk', 'scaling')
    except:
      return 1.0

  def _categorize_screen_size(self):
    """Categorize screen size for responsive design"""
    effective_width = self.screen_width / self.dpi_scale
    effective_height = self.screen_height / self.dpi_scale

    if effective_width <= 1366 and effective_height <= 768:
      return "small"  # Small laptops, tablets
    elif effective_width <= 1920 and effective_height <= 1080:
      return "medium"  # Standard monitors
    elif effective_width <= 2560 and effective_height <= 1440:
      return "large"  # Large monitors
    else:
      return "xlarge"  # 4K and above

  def get_responsive_dimensions(self):
    """Calculate responsive window dimensions"""
    base_dimensions = {
      "small": {"min_width": 600, "min_height": 650, "preferred_width": 650, "preferred_height": 720},
      "medium": {"min_width": 650, "min_height": 750, "preferred_width": 700, "preferred_height": 800},
      "large": {"min_width": 700, "min_height": 800, "preferred_width": 800, "preferred_height": 900},
      "xlarge": {"min_width": 800, "min_height": 900, "preferred_width": 900, "preferred_height": 1000}
    }

    return base_dimensions.get(self.screen_category, base_dimensions["medium"])

  def get_responsive_position(self, window_width, window_height):
    """Calculate responsive window position"""
    # Calculate position based on screen percentage
    if self.screen_category == "small":
      # Center on small screens
      x = (self.screen_width - window_width) // 2
      y = (self.screen_height - window_height) // 2
    else:
      # Right side positioning for larger screens
      margin = int(20 * self.dpi_scale)
      x = self.screen_width // 2 + margin
      y = margin

      # Ensure window doesn't go off screen
      x = min(x, self.screen_width - window_width - margin)
      y = min(y, self.screen_height - window_height - margin)

    return max(0, x), max(0, y)

  def get_responsive_padding(self):
    """Get responsive padding values"""
    padding_map = {
      "small": {"main": 8, "section": 8, "element": 4},
      "medium": {"main": 10, "section": 10, "element": 5},
      "large": {"main": 12, "section": 12, "element": 6},
      "xlarge": {"main": 15, "section": 15, "element": 8}
    }

    return padding_map.get(self.screen_category, padding_map["medium"])

  def get_responsive_font_sizes(self):
    """Get responsive font sizes"""
    base_font = max(8, int(9 * self.dpi_scale))
    return {
      "title": base_font + 6,
      "section": base_font + 2,
      "label": base_font,
      "small": base_font - 1
    }

  def get_log_area_height(self):
    """Get responsive log area height"""
    height_map = {
      "small": 8,
      "medium": 10,
      "large": 12,
      "xlarge": 15
    }

    return height_map.get(self.screen_category, 10)


class StopConditionsWindow:
  """Window for configuring stop conditions"""

  def __init__(self, parent):
    self.parent = parent
    self.window = tk.Toplevel(parent.root)
    self.window.title("Stop Conditions Configuration")
    self.window.resizable(False, False)

    # Keep window on top and set as dialog
    self.window.attributes('-topmost', True)
    self.window.transient(parent.root)
    self.window.grab_set()  # Make it modal

    self.setup_ui()
    self.load_current_values()

    # Bind window close event
    self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

    # Center window on screen
    self.center_window()

  def center_window(self):
    """Center the window on screen"""
    self.window.update_idletasks()

    req_width = self.window.winfo_reqwidth()
    req_height = self.window.winfo_reqheight()

    width = max(400, req_width + 40)
    height = max(300, req_height + 40)

    parent_x = self.parent.root.winfo_x()
    parent_y = self.parent.root.winfo_y()
    parent_width = self.parent.root.winfo_width()
    parent_height = self.parent.root.winfo_height()

    x = parent_x + (parent_width // 2) - (width // 2)
    y = parent_y + (parent_height // 2) - (height // 2)

    self.window.geometry(f"{width}x{height}+{x}+{y}")

  def setup_ui(self):
    """Setup the user interface"""
    padding = self.parent.ui_manager.get_responsive_padding()

    main_frame = ttk.Frame(self.window, padding=str(padding["main"]))
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Title
    fonts = self.parent.ui_manager.get_responsive_font_sizes()
    title_label = ttk.Label(main_frame, text="Stop Conditions Configuration",
                            font=("Arial", fonts["section"], "bold"))
    title_label.pack(pady=(0, padding["section"]))

    # Info text
    info_label = ttk.Label(main_frame,
                           text="Configure when the bot should automatically stop.\n" +
                                "Conditions marked with (day >24) only apply after day 24.",
                           font=("Arial", fonts["small"]), justify=tk.CENTER, foreground="blue")
    info_label.pack(pady=(0, padding["section"]))

    # Stop conditions frame
    conditions_frame = ttk.Frame(main_frame)
    conditions_frame.pack(fill=tk.BOTH, expand=True)

    # Stop when infirmary needed
    self.infirmary_var = tk.BooleanVar()
    infirmary_check = ttk.Checkbutton(conditions_frame,
                                      text="Stop when infirmary needed (day >24)",
                                      variable=self.infirmary_var)
    infirmary_check.pack(anchor=tk.W, pady=padding["element"])

    # Stop when need rest
    self.need_rest_var = tk.BooleanVar()
    need_rest_check = ttk.Checkbutton(conditions_frame,
                                      text="Stop when need rest (day >24)",
                                      variable=self.need_rest_var)
    need_rest_check.pack(anchor=tk.W, pady=padding["element"])

    # Stop when low mood (with dropdown)
    mood_frame = ttk.Frame(conditions_frame)
    mood_frame.pack(fill=tk.X, pady=padding["element"])

    self.low_mood_var = tk.BooleanVar()
    low_mood_check = ttk.Checkbutton(mood_frame,
                                     text="Stop when mood below:",
                                     variable=self.low_mood_var)
    low_mood_check.pack(side=tk.LEFT)

    self.mood_threshold_var = tk.StringVar()
    mood_dropdown = ttk.Combobox(mood_frame, textvariable=self.mood_threshold_var,
                                 values=["AWFUL", "BAD", "NORMAL", "GOOD", "GREAT"],
                                 state="readonly", width=10)
    mood_dropdown.pack(side=tk.LEFT, padx=(10, 0))

    mood_info_label = ttk.Label(mood_frame, text="(day >24)",
                                font=("Arial", fonts["small"]), foreground="gray")
    mood_info_label.pack(side=tk.LEFT, padx=(5, 0))

    # Stop when race day
    self.race_day_var = tk.BooleanVar()
    race_day_check = ttk.Checkbutton(conditions_frame,
                                     text="Stop when race day",
                                     variable=self.race_day_var)
    race_day_check.pack(anchor=tk.W, pady=padding["element"])

    # Stop before summer (June)
    self.stop_before_summer_var = tk.BooleanVar()
    stop_summer_check = ttk.Checkbutton(conditions_frame,
                                        text="Stop before summer (June) (day >24)",
                                        variable=self.stop_before_summer_var)
    stop_summer_check.pack(anchor=tk.W, pady=padding["element"])

    # Stop at specific month (with dropdown)
    month_frame = ttk.Frame(conditions_frame)
    month_frame.pack(fill=tk.X, pady=padding["element"])

    self.stop_at_month_var = tk.BooleanVar()
    stop_month_check = ttk.Checkbutton(month_frame,
                                       text="Stop at month:",
                                       variable=self.stop_at_month_var)
    stop_month_check.pack(side=tk.LEFT)

    self.target_month_var = tk.StringVar()
    month_dropdown = ttk.Combobox(month_frame, textvariable=self.target_month_var,
                                  values=["January", "February", "March", "April",
                                          "May", "June", "July", "August",
                                          "September", "October", "November", "December"],
                                  state="readonly", width=12)
    month_dropdown.pack(side=tk.LEFT, padx=(10, 0))

    month_info_label = ttk.Label(month_frame, text="(day >24)",
                                 font=("Arial", fonts["small"]), foreground="gray")
    month_info_label.pack(side=tk.LEFT, padx=(5, 0))

    # Separator
    separator = ttk.Separator(main_frame, orient='horizontal')
    separator.pack(fill=tk.X, pady=padding["section"])

    # Button frame
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill=tk.X)

    # Cancel and Save buttons
    cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.on_closing)
    cancel_btn.pack(side=tk.RIGHT, padx=(5, 0))

    save_btn = ttk.Button(button_frame, text="Save", command=self.save_settings)
    save_btn.pack(side=tk.RIGHT)

  def load_current_values(self):
    """Load current values from parent"""
    self.infirmary_var.set(self.parent.stop_on_infirmary.get())
    self.need_rest_var.set(self.parent.stop_on_need_rest.get())
    self.low_mood_var.set(self.parent.stop_on_low_mood.get())
    self.race_day_var.set(self.parent.stop_on_race_day.get())
    self.mood_threshold_var.set(self.parent.stop_mood_threshold.get())
    self.stop_before_summer_var.set(self.parent.stop_before_summer.get())
    self.stop_at_month_var.set(self.parent.stop_at_month.get())
    self.target_month_var.set(self.parent.target_month.get())

  def save_settings(self):
    """Save settings and close window"""
    self.parent.stop_on_infirmary.set(self.infirmary_var.get())
    self.parent.stop_on_need_rest.set(self.need_rest_var.get())
    self.parent.stop_on_low_mood.set(self.low_mood_var.get())
    self.parent.stop_on_race_day.set(self.race_day_var.get())
    self.parent.stop_mood_threshold.set(self.mood_threshold_var.get())
    self.parent.stop_before_summer.set(self.stop_before_summer_var.get())
    self.parent.stop_at_month.set(self.stop_at_month_var.get())
    self.parent.target_month.set(self.target_month_var.get())

    self.parent.save_settings()
    self.window.destroy()

  def on_closing(self):
    """Handle window closing"""
    self.window.destroy()


class UmaAutoGUI:
  def __init__(self):
    self.root = tk.Tk()
    self.root.title("Uma Musume Auto Train - Developed by LittleKai!")

    # Initialize responsive UI manager
    self.ui_manager = ResponsiveUIManager(self.root)

    # Get responsive dimensions and positioning
    dimensions = self.ui_manager.get_responsive_dimensions()
    self.setup_window_properties(dimensions)

    # Variables
    self.is_running = False
    self.bot_thread = None
    self.key_valid = False
    self.initial_key_validation_done = False

    # Race manager
    self.race_manager = RaceManager()

    # Initialize all variables
    self.init_variables()

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

    # Apply final responsive sizing
    self.apply_responsive_sizing()

  def setup_window_properties(self, dimensions):
    """Setup window properties with responsive values"""
    self.root.minsize(dimensions["min_width"], dimensions["min_height"])

    # Calculate initial position
    initial_width = dimensions["preferred_width"]
    initial_height = dimensions["preferred_height"]
    x, y = self.ui_manager.get_responsive_position(initial_width, initial_height)

    self.root.geometry(f"{initial_width}x{initial_height}+{x}+{y}")
    self.root.resizable(True, True)
    self.root.attributes('-topmost', True)

  def init_variables(self):
    """Initialize all tkinter variables"""
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
    self.enable_stop_conditions = tk.BooleanVar(value=False)
    self.stop_on_infirmary = tk.BooleanVar(value=False)
    self.stop_on_need_rest = tk.BooleanVar(value=False)
    self.stop_on_low_mood = tk.BooleanVar(value=False)
    self.stop_on_race_day = tk.BooleanVar(value=False)
    self.stop_mood_threshold = tk.StringVar(value="BAD")
    self.stop_before_summer = tk.BooleanVar(value=False)
    self.stop_at_month = tk.BooleanVar(value=False)
    self.target_month = tk.StringVar(value="June")

  def setup_gui(self):
    """Setup the main GUI interface with responsive design"""
    padding = self.ui_manager.get_responsive_padding()

    # Create main container with responsive padding
    main_container = ttk.Frame(self.root)
    main_container.pack(fill=tk.BOTH, expand=True, padx=padding["main"], pady=padding["main"])

    # Create scrollable content area
    self.create_scrollable_area(main_container, padding)

  def create_scrollable_area(self, parent, padding):
    """Create scrollable content area with responsive sizing"""
    # Create canvas and scrollbar for scrollable content
    canvas = tk.Canvas(parent)
    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    # Configure scrollable frame
    scrollable_frame.bind(
      "<Configure>",
      lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Main content frame
    main_frame = ttk.Frame(scrollable_frame)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=padding["element"], pady=padding["element"])
    main_frame.columnconfigure(0, weight=1)

    # Setup all sections
    self.setup_all_sections(main_frame, padding)

    # Pack canvas and scrollbar
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Bind mousewheel to canvas
    self.bind_mousewheel(canvas)

    # Configure canvas scrolling region after content is loaded
    self.root.after(100, lambda: canvas.configure(scrollregion=canvas.bbox("all")))

  def bind_mousewheel(self, canvas):
    """Bind mousewheel events to canvas for scrolling"""
    def on_mousewheel(event):
      canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def on_mousewheel_linux(event):
      if event.num == 4:
        canvas.yview_scroll(-1, "units")
      elif event.num == 5:
        canvas.yview_scroll(1, "units")

    # Windows and macOS
    canvas.bind("<MouseWheel>", on_mousewheel)
    # Linux
    canvas.bind("<Button-4>", on_mousewheel_linux)
    canvas.bind("<Button-5>", on_mousewheel_linux)

  def setup_all_sections(self, parent, padding):
    """Setup all GUI sections with responsive spacing"""
    section_spacing = padding["section"]

    self.setup_header_section(parent, padding)
    self.setup_status_section(parent, padding, row=1, pady=(0, section_spacing))
    self.setup_strategy_section(parent, padding, row=2, pady=(0, section_spacing))
    self.setup_race_filters_and_stop_conditions_section(parent, padding, row=3, pady=(0, section_spacing))
    self.setup_control_buttons_section(parent, padding, row=4, pady=(0, section_spacing))
    self.setup_activity_log_section(parent, padding, row=5, pady=(0, section_spacing))

  def setup_header_section(self, parent, padding, row=0, pady=(0, 15)):
    """Setup the header section with responsive fonts"""
    fonts = self.ui_manager.get_responsive_font_sizes()

    title_frame = ttk.Frame(parent)
    title_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=pady)
    title_frame.columnconfigure(0, weight=1)

    # Title container
    title_container = ttk.Frame(title_frame)
    title_container.pack(side=tk.LEFT)

    # Main title with responsive font
    title_label = ttk.Label(title_container, text="Uma Musume Auto Train",
                            font=("Arial", fonts["title"], "bold"))
    title_label.pack(anchor=tk.W)

    # Settings button
    settings_button = ttk.Button(title_frame, text="⚙ Region Settings",
                                 command=self.open_region_settings)
    settings_button.pack(side=tk.RIGHT)

  def setup_status_section(self, parent, padding, row=1, pady=(0, 15)):
    """Setup the status monitoring section with responsive layout"""
    fonts = self.ui_manager.get_responsive_font_sizes()

    status_frame = ttk.LabelFrame(parent, text="Status", padding=str(padding["section"]))
    status_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=pady)
    status_frame.columnconfigure(0, weight=1)
    status_frame.columnconfigure(1, weight=1)

    # Left column frame
    left_column = ttk.Frame(status_frame)
    left_column.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N), padx=(0, padding["section"]))
    left_column.columnconfigure(1, weight=1)

    # Right column frame
    right_column = ttk.Frame(status_frame)
    right_column.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N))
    right_column.columnconfigure(1, weight=1)

    # Left column content with responsive fonts
    self.create_status_labels(left_column, fonts, padding)

    # Right column content with responsive fonts
    self.create_status_labels_right(right_column, fonts, padding)

  def create_status_labels(self, parent, fonts, padding):
    """Create left column status labels"""
    ttk.Label(parent, text="Bot Status:", font=("Arial", fonts["label"], "bold")).grid(row=0, column=0, sticky=tk.W, pady=padding["element"]//2)
    self.status_label = ttk.Label(parent, text="Stopped", foreground="red")
    self.status_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=padding["element"]//2)

    ttk.Label(parent, text="Current Date:", font=("Arial", fonts["label"], "bold")).grid(row=1, column=0, sticky=tk.W, pady=padding["element"]//2)
    self.date_label = ttk.Label(parent, text="Unknown", foreground="blue")
    self.date_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=padding["element"]//2)

    ttk.Label(parent, text="Energy:", font=("Arial", fonts["label"], "bold")).grid(row=2, column=0, sticky=tk.W, pady=padding["element"]//2)
    self.energy_label = ttk.Label(parent, text="Unknown", foreground="blue")
    self.energy_label.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=padding["element"]//2)

  def create_status_labels_right(self, parent, fonts, padding):
    """Create right column status labels"""
    ttk.Label(parent, text="Game Window:", font=("Arial", fonts["label"], "bold")).grid(row=0, column=0, sticky=tk.W, pady=padding["element"]//2)
    self.game_status_label = ttk.Label(parent, text="Checking...", foreground="orange")
    self.game_status_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=padding["element"]//2)

    ttk.Label(parent, text="Key Status:", font=("Arial", fonts["label"], "bold")).grid(row=1, column=0, sticky=tk.W, pady=padding["element"]//2)
    self.key_status_label = ttk.Label(parent, text="Checking...", foreground="orange")
    self.key_status_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=padding["element"]//2)

  def setup_strategy_section(self, parent, padding, row=2, pady=(0, 15)):
    """Setup the strategy settings section with responsive spacing"""
    fonts = self.ui_manager.get_responsive_font_sizes()

    strategy_frame = ttk.LabelFrame(parent, text="Strategy Settings", padding=str(padding["section"]))
    strategy_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=pady)
    strategy_frame.columnconfigure(1, weight=1)
    strategy_frame.columnconfigure(3, weight=1)

    # Row 0: Minimum Mood and Priority Strategy
    ttk.Label(strategy_frame, text="Minimum Mood:", font=("Arial", fonts["label"])).grid(row=0, column=0, sticky=tk.W, padx=(0, 5), pady=padding["element"])
    mood_dropdown = ttk.Combobox(strategy_frame, textvariable=self.minimum_mood,
                                 values=["AWFUL", "BAD", "NORMAL", "GOOD", "GREAT"],
                                 state="readonly", width=12)
    mood_dropdown.grid(row=0, column=1, sticky=tk.W, padx=(0, 20), pady=padding["element"])
    mood_dropdown.bind('<<ComboboxSelected>>', lambda e: self.save_settings())

    ttk.Label(strategy_frame, text="Priority Strategy:", font=("Arial", fonts["label"])).grid(row=0, column=2, sticky=tk.W, padx=(0, 5), pady=padding["element"])
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
    priority_dropdown.grid(row=0, column=3, sticky=tk.W, pady=padding["element"])
    priority_dropdown.bind('<<ComboboxSelected>>', lambda e: self.save_settings())

    # Row 1: Checkboxes with responsive spacing
    continuous_racing_check = ttk.Checkbutton(strategy_frame,
                                              text="Allow Continuous Racing (>3 races)",
                                              variable=self.allow_continuous_racing,
                                              command=self.save_settings)
    continuous_racing_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(padding["section"], padding["element"]))

    manual_event_check = ttk.Checkbutton(strategy_frame,
                                         text="Manual Event Handling (pause on events)",
                                         variable=self.manual_event_handling,
                                         command=self.save_settings)
    manual_event_check.grid(row=1, column=2, columnspan=2, sticky=tk.W, pady=(padding["section"], padding["element"]))

  def setup_race_filters_and_stop_conditions_section(self, parent, padding, row=3, pady=(0, 15)):
    """Setup the race filters and stop conditions section with responsive layout"""
    # Main container for race filters and stop conditions
    filters_container = ttk.Frame(parent)
    filters_container.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=pady)
    filters_container.columnconfigure(0, weight=1)
    filters_container.columnconfigure(1, weight=1)

    # Race filters section
    self.create_race_filters_section(filters_container, padding)

    # Stop conditions section
    self.create_stop_conditions_section(filters_container, padding)

  def create_race_filters_section(self, parent, padding):
    """Create race filters section with responsive layout"""
    filter_frame = ttk.LabelFrame(parent, text="Race Filters", padding=str(padding["section"]))
    filter_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N), padx=(0, padding["section"]))
    filter_frame.columnconfigure(0, weight=1)
    filter_frame.columnconfigure(1, weight=1)
    filter_frame.columnconfigure(2, weight=1)

    # Track filters
    track_frame = ttk.LabelFrame(filter_frame, text="Track Type", padding=str(padding["element"]))
    track_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N), padx=(0, padding["element"]))

    ttk.Checkbutton(track_frame, text="Turf", variable=self.track_filters['turf'],
                    command=self.save_settings).pack(anchor=tk.W, pady=padding["element"]//2)
    ttk.Checkbutton(track_frame, text="Dirt", variable=self.track_filters['dirt'],
                    command=self.save_settings).pack(anchor=tk.W, pady=padding["element"]//2)

    # Distance filters
    distance_frame = ttk.LabelFrame(filter_frame, text="Distance", padding=str(padding["element"]))
    distance_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N), padx=padding["element"])

    distance_inner = ttk.Frame(distance_frame)
    distance_inner.pack(fill=tk.BOTH, expand=True)

    ttk.Checkbutton(distance_inner, text="Sprint", variable=self.distance_filters['sprint'],
                    command=self.save_settings).grid(row=0, column=0, sticky=tk.W, pady=padding["element"]//2)
    ttk.Checkbutton(distance_inner, text="Mile", variable=self.distance_filters['mile'],
                    command=self.save_settings).grid(row=1, column=0, sticky=tk.W, pady=padding["element"]//2)
    ttk.Checkbutton(distance_inner, text="Medium", variable=self.distance_filters['medium'],
                    command=self.save_settings).grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=padding["element"]//2)
    ttk.Checkbutton(distance_inner, text="Long", variable=self.distance_filters['long'],
                    command=self.save_settings).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=padding["element"]//2)

    # Grade filters
    grade_frame = ttk.LabelFrame(filter_frame, text="Grade", padding=str(padding["element"]))
    grade_frame.grid(row=0, column=2, sticky=(tk.W, tk.E, tk.N), padx=(padding["element"], 0))

    grade_inner = ttk.Frame(grade_frame)
    grade_inner.pack(fill=tk.BOTH, expand=True)

    ttk.Checkbutton(grade_inner, text="G1", variable=self.grade_filters['g1'],
                    command=self.save_settings).grid(row=0, column=0, sticky=tk.W, pady=padding["element"]//2)
    ttk.Checkbutton(grade_inner, text="G2", variable=self.grade_filters['g2'],
                    command=self.save_settings).grid(row=1, column=0, sticky=tk.W, pady=padding["element"]//2)
    ttk.Checkbutton(grade_inner, text="G3", variable=self.grade_filters['g3'],
                    command=self.save_settings).grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=padding["element"]//2)

  def create_stop_conditions_section(self, parent, padding):
    """Create stop conditions section with responsive layout"""
    stop_conditions_frame = ttk.LabelFrame(parent, text="Stop Conditions", padding=str(padding["section"]))
    stop_conditions_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N))

    # Enable stop conditions checkbox
    enable_stop_check = ttk.Checkbutton(stop_conditions_frame, text="Enable stop conditions",
                                        variable=self.enable_stop_conditions, command=self.save_settings)
    enable_stop_check.pack(anchor=tk.W, pady=(0, padding["section"]))

    # Configure stop conditions button
    config_stop_button = ttk.Button(stop_conditions_frame, text="⚙ Configure Stop Conditions",
                                    command=self.open_stop_conditions_window)
    config_stop_button.pack(fill=tk.X)

  def setup_control_buttons_section(self, parent, padding, row=4, pady=(0, 15)):
    """Setup the control buttons section with responsive sizing"""
    button_frame = ttk.Frame(parent)
    button_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=pady)
    button_frame.columnconfigure(0, weight=1)
    button_frame.columnconfigure(1, weight=1)

    # Calculate button padding based on screen size
    button_padding = max(3, int(5 * self.ui_manager.dpi_scale))

    # Start button
    self.start_button = ttk.Button(button_frame, text="Start (F1)",
                                   command=self.start_bot)
    self.start_button.grid(row=0, column=0, padx=(0, padding["element"]), sticky=(tk.W, tk.E), ipady=button_padding)

    # Stop button
    self.stop_button = ttk.Button(button_frame, text="Stop (F3)",
                                  command=self.stop_bot, state="disabled")
    self.stop_button.grid(row=0, column=1, padx=(padding["element"], 0), sticky=(tk.W, tk.E), ipady=button_padding)

  def setup_activity_log_section(self, parent, padding, row=5, pady=(0, 15)):
    """Setup the activity log section with responsive sizing"""
    log_frame = ttk.LabelFrame(parent, text="Activity Log", padding=str(padding["section"]))
    log_frame.grid(row=row, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=pady)
    log_frame.columnconfigure(0, weight=1)
    log_frame.rowconfigure(0, weight=1)

    # Log text area with responsive height
    log_height = self.ui_manager.get_log_area_height()
    self.log_text = scrolledtext.ScrolledText(log_frame, height=log_height, width=70, wrap=tk.WORD)
    self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    # Clear log button
    clear_button = ttk.Button(log_frame, text="Clear Log", command=self.clear_log)
    clear_button.grid(row=1, column=0, sticky=tk.W, pady=(padding["element"], 0))

  def apply_responsive_sizing(self):
    """Apply final responsive sizing after all content is loaded"""
    self.root.after(200, self._finalize_window_size)

  def _finalize_window_size(self):
    """Finalize window size based on content requirements"""
    self.root.update_idletasks()

    # Get required dimensions
    req_width = self.root.winfo_reqwidth()
    req_height = self.root.winfo_reqheight()

    # Get responsive dimensions and padding
    dimensions = self.ui_manager.get_responsive_dimensions()
    padding = self.ui_manager.get_responsive_padding()

    # Calculate final dimensions
    content_padding = padding["main"] * 4
    final_width = max(dimensions["min_width"], req_width + content_padding)
    final_height = max(dimensions["min_height"], req_height + content_padding)

    # Ensure window doesn't exceed screen bounds
    max_width = int(self.ui_manager.screen_width * 0.9)
    max_height = int(self.ui_manager.screen_height * 0.9)

    final_width = min(final_width, max_width)
    final_height = min(final_height, max_height)

    # Get responsive position
    x, y = self.ui_manager.get_responsive_position(final_width, final_height)

    # Update geometry
    self.root.geometry(f"{final_width}x{final_height}+{x}+{y}")

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

  def open_stop_conditions_window(self):
    """Open the stop conditions configuration window"""
    try:
      StopConditionsWindow(self)
    except Exception as e:
      self.log_message(f"Error opening stop conditions window: {e}")
      messagebox.showerror("Error", f"Failed to open stop conditions window: {e}")

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
      'enable_stop_conditions': self.enable_stop_conditions.get(),
      'stop_on_infirmary': self.stop_on_infirmary.get(),
      'stop_on_need_rest': self.stop_on_need_rest.get(),
      'stop_on_low_mood': self.stop_on_low_mood.get(),
      'stop_on_race_day': self.stop_on_race_day.get(),
      'stop_mood_threshold': self.stop_mood_threshold.get(),
      'stop_before_summer': self.stop_before_summer.get(),
      'stop_at_month': self.stop_at_month.get(),
      'target_month': self.target_month.get()
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
        if 'enable_stop_conditions' in settings:
          self.enable_stop_conditions.set(settings['enable_stop_conditions'])
        if 'stop_on_infirmary' in settings:
          self.stop_on_infirmary.set(settings['stop_on_infirmary'])
        if 'stop_on_need_rest' in settings:
          self.stop_on_need_rest.set(settings['stop_on_need_rest'])
        if 'stop_on_low_mood' in settings:
          self.stop_on_low_mood.set(settings['stop_on_low_mood'])
        if 'stop_on_race_day' in settings:
          self.stop_on_race_day.set(settings['stop_on_race_day'])
        if 'stop_mood_threshold' in settings:
          self.stop_mood_threshold.set(settings['stop_mood_threshold'])
        if 'stop_before_summer' in settings:
          self.stop_before_summer.set(settings['stop_before_summer'])
        if 'stop_at_month' in settings:
          self.stop_at_month.set(settings['stop_at_month'])
        if 'target_month' in settings:
          self.target_month.set(settings['target_month'])

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
      'enable_stop_conditions': self.enable_stop_conditions.get(),
      'stop_on_infirmary': self.stop_on_infirmary.get(),
      'stop_on_need_rest': self.stop_on_need_rest.get(),
      'stop_on_low_mood': self.stop_on_low_mood.get(),
      'stop_on_race_day': self.stop_on_race_day.get(),
      'stop_mood_threshold': self.stop_mood_threshold.get(),
      'stop_before_summer': self.stop_before_summer.get(),
      'stop_at_month': self.stop_at_month.get(),
      'target_month': self.target_month.get()
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
    self.log_message("• Train Score 2.5+/3+/3.5+/4+: Train only if score meets threshold")
    self.log_message("Use F1 to start, F3 to stop, F5 to force exit program.")

    self.root.mainloop()


def main():
  """Main function - create and run GUI"""
  app = UmaAutoGUI()
  app.run()


if __name__ == "__main__":
  main()