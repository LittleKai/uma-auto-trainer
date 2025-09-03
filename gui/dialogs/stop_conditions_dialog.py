import tkinter as tk
from tkinter import ttk


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

        # Initialize variables
        self.init_variables()

        # Setup UI and load settings
        self.setup_ui()
        self.load_current_values()

        # Bind events
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.center_window()

    def init_variables(self):
        """Initialize dialog variables"""
        self.infirmary_var = tk.BooleanVar()
        self.need_rest_var = tk.BooleanVar()
        self.low_mood_var = tk.BooleanVar()
        self.race_day_var = tk.BooleanVar()
        self.mood_threshold_var = tk.StringVar()
        self.stop_before_summer_var = tk.BooleanVar()
        self.stop_at_month_var = tk.BooleanVar()
        self.target_month_var = tk.StringVar()

    def setup_ui(self):
        """Setup the user interface"""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        self.create_title(main_frame)

        # Info text
        self.create_info(main_frame)

        # Stop conditions
        self.create_conditions(main_frame)

        # Buttons
        self.create_buttons(main_frame)

    def create_title(self, parent):
        """Create title section"""
        title_label = ttk.Label(parent, text="Stop Conditions Configuration",
                                font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))

    def create_info(self, parent):
        """Create info section"""
        info_label = ttk.Label(
            parent,
            text="Configure when the bot should automatically stop.\n" +
                 "Conditions marked with (day >24) only apply after day 24.",
            font=("Arial", 9),
            justify=tk.CENTER,
            foreground="blue"
        )
        info_label.pack(pady=(0, 15))

    def create_conditions(self, parent):
        """Create stop conditions section"""
        conditions_frame = ttk.Frame(parent)
        conditions_frame.pack(fill=tk.BOTH, expand=True)

        # Stop when infirmary needed
        infirmary_check = ttk.Checkbutton(
            conditions_frame,
            text="Stop when infirmary needed (day >24)",
            variable=self.infirmary_var
        )
        infirmary_check.pack(anchor=tk.W, pady=5)

        # Stop when need rest
        need_rest_check = ttk.Checkbutton(
            conditions_frame,
            text="Stop when need rest (day >24)",
            variable=self.need_rest_var
        )
        need_rest_check.pack(anchor=tk.W, pady=5)

        # Stop when low mood (with dropdown)
        self.create_mood_condition(conditions_frame)

        # Stop when race day
        race_day_check = ttk.Checkbutton(
            conditions_frame,
            text="Stop when race day",
            variable=self.race_day_var
        )
        race_day_check.pack(anchor=tk.W, pady=5)

        # Stop before summer (June)
        stop_summer_check = ttk.Checkbutton(
            conditions_frame,
            text="Stop before summer (June) (day >24)",
            variable=self.stop_before_summer_var
        )
        stop_summer_check.pack(anchor=tk.W, pady=5)

        # Stop at specific month (with dropdown)
        self.create_month_condition(conditions_frame)

    def create_mood_condition(self, parent):
        """Create mood condition with dropdown"""
        mood_frame = ttk.Frame(parent)
        mood_frame.pack(fill=tk.X, pady=5)

        low_mood_check = ttk.Checkbutton(
            mood_frame,
            text="Stop when mood below:",
            variable=self.low_mood_var
        )
        low_mood_check.pack(side=tk.LEFT)

        mood_dropdown = ttk.Combobox(
            mood_frame,
            textvariable=self.mood_threshold_var,
            values=["AWFUL", "BAD", "NORMAL", "GOOD", "GREAT"],
            state="readonly",
            width=10
        )
        mood_dropdown.pack(side=tk.LEFT, padx=(10, 0))

        mood_info_label = ttk.Label(
            mood_frame,
            text="(day >24)",
            font=("Arial", 8),
            foreground="gray"
        )
        mood_info_label.pack(side=tk.LEFT, padx=(5, 0))

    def create_month_condition(self, parent):
        """Create month condition with dropdown"""
        month_frame = ttk.Frame(parent)
        month_frame.pack(fill=tk.X, pady=5)

        stop_month_check = ttk.Checkbutton(
            month_frame,
            text="Stop at month:",
            variable=self.stop_at_month_var
        )
        stop_month_check.pack(side=tk.LEFT)

        month_dropdown = ttk.Combobox(
            month_frame,
            textvariable=self.target_month_var,
            values=["January", "February", "March", "April",
                    "May", "June", "July", "August",
                    "September", "October", "November", "December"],
            state="readonly",
            width=12
        )
        month_dropdown.pack(side=tk.LEFT, padx=(10, 0))

        month_info_label = ttk.Label(
            month_frame,
            text="(day >24)",
            font=("Arial", 8),
            foreground="gray"
        )
        month_info_label.pack(side=tk.LEFT, padx=(5, 0))

    def create_buttons(self, parent):
        """Create button section"""
        # Separator
        separator = ttk.Separator(parent, orient='horizontal')
        separator.pack(fill=tk.X, pady=15)

        # Button frame
        button_frame = ttk.Frame(parent)
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

        x = parent_x + (parent_width // 2) - (width // 2) + 20
        y = parent_y + (parent_height // 2) - (height // 2)

        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def on_closing(self):
        """Handle window closing"""
        self.window.destroy()