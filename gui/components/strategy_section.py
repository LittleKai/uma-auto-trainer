import tkinter as tk
from tkinter import ttk


class StrategySection:
    """Strategy settings section component"""

    def __init__(self, parent, main_window, row=0):
        self.parent = parent
        self.main_window = main_window
        self.row = row

        self.create_section()

    def create_section(self):
        """Create the strategy settings section"""
        self.frame = ttk.LabelFrame(self.parent, text="Strategy Settings", padding="10")
        self.frame.grid(row=self.row, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        self.frame.columnconfigure(1, weight=1)
        self.frame.columnconfigure(3, weight=1)

        self.create_mood_and_strategy_controls()
        self.create_option_checkboxes()

    def create_mood_and_strategy_controls(self):
        """Create minimum mood and priority strategy controls"""
        # Minimum Mood
        ttk.Label(self.frame, text="Minimum Mood:").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 5), pady=5)

        mood_dropdown = ttk.Combobox(
            self.frame,
            textvariable=self.main_window.minimum_mood,
            values=["AWFUL", "BAD", "NORMAL", "GOOD", "GREAT"],
            state="readonly",
            width=12
        )
        mood_dropdown.grid(row=0, column=1, sticky=tk.W, padx=(0, 20), pady=5)
        mood_dropdown.bind('<<ComboboxSelected>>', lambda e: self.main_window.save_settings())

        # Priority Strategy
        ttk.Label(self.frame, text="Priority Strategy:").grid(
            row=0, column=2, sticky=tk.W, padx=(0, 5), pady=5)

        priority_dropdown = ttk.Combobox(
            self.frame,
            textvariable=self.main_window.priority_strategy,
            values=[
                "G1 (no training)",
                "G2 (no training)",
                "Train Score 2.5+",
                "Train Score 3+",
                "Train Score 3.5+",
                "Train Score 4+",
                "Train Score 4.5+"
            ],
            state="readonly",
            width=22
        )
        priority_dropdown.grid(row=0, column=3, sticky=tk.W, pady=5)
        priority_dropdown.bind('<<ComboboxSelected>>', lambda e: self.main_window.save_settings())

    def create_option_checkboxes(self):
        """Create option checkboxes"""
        # Allow Continuous Racing
        continuous_racing_check = ttk.Checkbutton(
            self.frame,
            text="Allow Continuous Racing (>3 races)",
            variable=self.main_window.allow_continuous_racing,
            command=self.main_window.save_settings
        )
        continuous_racing_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))

        # Manual Event Handling
        manual_event_check = ttk.Checkbutton(
            self.frame,
            text="Manual Event Handling (pause on events)",
            variable=self.main_window.manual_event_handling,
            command=self.main_window.save_settings
        )
        manual_event_check.grid(row=1, column=2, columnspan=2, sticky=tk.W, pady=(10, 5))