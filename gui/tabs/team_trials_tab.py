import tkinter as tk
from tkinter import ttk


class TeamTrialsTab:
    """Team Trials configuration tab for opponent selection and PVP settings"""

    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window

        # Initialize variables
        self.init_variables()

        # Bind variable changes to auto-save
        self.bind_variable_changes()

        # Create tab content
        self.create_content()

    def init_variables(self):
        """Initialize tab variables with default values"""
        self.opponent_type = tk.StringVar(value="Opponent 3")
        self.use_parfait_gift_pvp = tk.BooleanVar(value=True)
        self.stop_on_shop = tk.BooleanVar(value=False)

    def bind_variable_changes(self):
        """Bind variable changes to trigger auto-save"""
        def auto_save(*args):
            if hasattr(self.main_window, 'save_settings'):
                self.main_window.save_settings()

        # Bind all variables to auto-save
        self.opponent_type.trace('w', auto_save)
        self.use_parfait_gift_pvp.trace('w', auto_save)
        self.stop_on_shop.trace('w', auto_save)

    def create_content(self):
        """Create tab content with opponent selection and settings"""
        # Create scrollable frame
        canvas = tk.Canvas(self.parent)
        scrollbar = ttk.Scrollbar(self.parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Main content frame
        content_frame = ttk.Frame(scrollable_frame, padding="10")
        content_frame.pack(fill=tk.BOTH, expand=True)
        content_frame.columnconfigure(0, weight=1, minsize=470)

        # Create sections
        self.create_opponent_selection(content_frame, row=0)
        self.create_pvp_settings(content_frame, row=1)
        self.create_control_section(content_frame, row=2)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_opponent_selection(self, parent, row):
        """Create opponent type selection section"""
        opponent_frame = ttk.LabelFrame(parent, text="Opponent Selection", padding="10")
        opponent_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        opponent_frame.columnconfigure(1, weight=1)

        # Opponent Type Dropdown
        ttk.Label(opponent_frame, text="Opponent Type:").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10), pady=5)

        opponent_dropdown = ttk.Combobox(
            opponent_frame,
            textvariable=self.opponent_type,
            values=["Opponent 1", "Opponent 2", "Opponent 3"],
            state="readonly",
            width=15
        )
        opponent_dropdown.grid(row=0, column=1, sticky=tk.W, pady=5)

    def create_pvp_settings(self, parent, row):
        """Create PVP settings section"""
        pvp_frame = ttk.LabelFrame(parent, text="PVP Settings", padding="10")
        pvp_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 15))

        # Use Parfait checkbox
        parfait_check = ttk.Checkbutton(
            pvp_frame,
            text="Sử dụng parfait nếu là gift pvp",
            variable=self.use_parfait_gift_pvp
        )
        parfait_check.grid(row=0, column=0, sticky=tk.W, pady=(0, 8))

        # Stop on shop checkbox
        shop_check = ttk.Checkbutton(
            pvp_frame,
            text="Dừng nếu có shop",
            variable=self.stop_on_shop
        )
        shop_check.grid(row=1, column=0, sticky=tk.W, pady=0)

    def create_control_section(self, parent, row):
        """Create control buttons section"""
        control_frame = ttk.LabelFrame(parent, text="Team Trials Control", padding="10")
        control_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        control_frame.columnconfigure(0, weight=1)

        # Start button (without hotkey)
        self.start_button = ttk.Button(
            control_frame,
            text="Start",
            command=self.start_team_trials,
            style="Accent.TButton"
        )
        self.start_button.grid(row=0, column=0, sticky=(tk.W, tk.E), ipady=8)

    def start_team_trials(self):
        """Handle Team Trials start button click"""
        # Get current settings
        settings = self.get_settings()

        # Log the start action
        if hasattr(self.main_window, 'log_message'):
            self.main_window.log_message(f"Starting Team Trials with {settings['opponent_type']}")
            if settings['use_parfait_gift_pvp']:
                self.main_window.log_message("Parfait enabled for gift PVP")
            if settings['stop_on_shop']:
                self.main_window.log_message("Will stop on shop appearance")

        # TODO: Implement actual Team Trials logic here
        # This is where you would call the appropriate Team Trials function
        # For now, just show a message
        if hasattr(self.main_window, 'log_message'):
            self.main_window.log_message("Team Trials feature is ready to be implemented")

    def get_settings(self):
        """Get current tab settings"""
        return {
            'opponent_type': self.opponent_type.get(),
            'use_parfait_gift_pvp': self.use_parfait_gift_pvp.get(),
            'stop_on_shop': self.stop_on_shop.get()
        }

    def load_settings(self, settings):
        """Load settings into tab"""
        try:
            # Load opponent type
            if 'opponent_type' in settings:
                self.opponent_type.set(settings['opponent_type'])

            # Load PVP settings
            if 'use_parfait_gift_pvp' in settings:
                self.use_parfait_gift_pvp.set(settings['use_parfait_gift_pvp'])

            if 'stop_on_shop' in settings:
                self.stop_on_shop.set(settings['stop_on_shop'])

        except Exception as e:
            print(f"Warning: Could not load Team Trials settings: {e}")
            # Set defaults if loading fails
            self.opponent_type.set("Opponent 3")
            self.use_parfait_gift_pvp.set(True)
            self.stop_on_shop.set(False)