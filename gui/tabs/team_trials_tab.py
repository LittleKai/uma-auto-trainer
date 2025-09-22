import tkinter as tk
from tkinter import ttk


class TeamTrialsTab:
    """Team Trials configuration tab"""

    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window

        # Initialize variables
        self.init_variables()

        # Create tab content
        self.create_content()

        # Bind variable changes to auto-save
        self.bind_variable_changes()

    def init_variables(self):
        """Initialize tab variables"""
        self.opponent_type = tk.StringVar(value="Opponent 3")
        self.use_parfait_gift_pvp = tk.BooleanVar(value=True)
        self.stop_if_shop = tk.BooleanVar(value=False)

    def bind_variable_changes(self):
        """Bind variable change events to auto-save"""
        variables = [
            self.opponent_type,
            self.use_parfait_gift_pvp,
            self.stop_if_shop
        ]

        for var in variables:
            var.trace('w', lambda *args: self.main_window.save_settings())

    def create_content(self):
        """Create tab content"""
        # Main content frame
        content_frame = ttk.Frame(self.parent, padding="15")
        content_frame.pack(fill=tk.BOTH, expand=True)
        content_frame.columnconfigure(0, weight=1)

        # Create sections
        self.create_opponent_selection(content_frame, row=0)
        self.create_options_section(content_frame, row=1)
        self.create_control_section(content_frame, row=2)

    def create_opponent_selection(self, parent, row):
        """Create opponent type selection section"""
        opponent_frame = ttk.LabelFrame(parent, text="Opponent Selection", padding="10")
        opponent_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        opponent_frame.columnconfigure(1, weight=1)

        # Opponent type label and dropdown in same row
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

    def create_options_section(self, parent, row):
        """Create options section with checkboxes"""
        options_frame = ttk.LabelFrame(parent, text="Options", padding="10")
        options_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        options_frame.columnconfigure(0, weight=1)
        options_frame.columnconfigure(1, weight=1)

        # Two checkboxes in same row
        parfait_check = ttk.Checkbutton(
            options_frame,
            text="Use parfait if gift PvP",
            variable=self.use_parfait_gift_pvp
        )
        parfait_check.grid(row=0, column=0, sticky=tk.W, pady=5)

        shop_check = ttk.Checkbutton(
            options_frame,
            text="Stop if shop available",
            variable=self.stop_if_shop
        )
        shop_check.grid(row=0, column=1, sticky=tk.W, pady=5)

    def create_control_section(self, parent, row):
        """Create control section with start button"""
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 15))

        # Start button
        self.start_button = ttk.Button(
            control_frame,
            text="Start",
            command=self.start_team_trials
        )
        self.start_button.pack(pady=10, ipadx=20, ipady=5)

    def start_team_trials(self):
        """Start team trials functionality"""
        self.main_window.log_message("Team Trials started with settings:")
        self.main_window.log_message(f"Opponent Type: {self.opponent_type.get()}")
        self.main_window.log_message(f"Use parfait for gift PvP: {self.use_parfait_gift_pvp.get()}")
        self.main_window.log_message(f"Stop if shop: {self.stop_if_shop.get()}")

    def get_settings(self):
        """Get current tab settings"""
        settings = {
            'opponent_type': self.opponent_type.get(),
            'use_parfait_gift_pvp': self.use_parfait_gift_pvp.get(),
            'stop_if_shop': self.stop_if_shop.get()
        }
        return settings

    def load_settings(self, settings):
        """Load settings into tab"""
        try:
            if 'opponent_type' in settings:
                self.opponent_type.set(settings['opponent_type'])
            if 'use_parfait_gift_pvp' in settings:
                self.use_parfait_gift_pvp.set(settings['use_parfait_gift_pvp'])
            if 'stop_if_shop' in settings:
                self.stop_if_shop.set(settings['stop_if_shop'])
        except Exception as e:
            print(f"Warning: Could not load team trials tab settings: {e}")