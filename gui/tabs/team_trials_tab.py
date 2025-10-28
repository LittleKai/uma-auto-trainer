import tkinter as tk
from tkinter import ttk
from .team_trials_logic import TeamTrialsLogic


class TeamTrialsTab:
    """Team Trials configuration tab - UI with dynamic options"""

    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window

        # Initialize variables
        self.init_variables()

        # Create tab content
        self.create_content()

        # Bind variable changes to auto-save
        self.bind_variable_changes()

        # Initialize logic handler
        self.logic = TeamTrialsLogic(self.main_window, self)

    def init_variables(self):
        """Initialize tab variables"""
        # Daily Activity dropdown
        self.daily_activity_type = tk.StringVar(value="Team Trial")

        # Team Trial variables
        self.opponent_type = tk.StringVar(value="Opponent 3")
        self.use_parfait_gift_pvp = tk.BooleanVar(value=True)
        self.stop_if_shop = tk.BooleanVar(value=False)

        # Daily Race variables
        self.default_race = tk.StringVar(value="Moonlight Sho")
        self.daily_race_stop_if_shop = tk.BooleanVar(value=False)

        # Legend Race variables
        self.legend_race_use_parfait = tk.BooleanVar(value=False)

    def bind_variable_changes(self):
        """Bind variable change events to auto-save"""
        variables = [
            self.daily_activity_type,
            self.opponent_type,
            self.use_parfait_gift_pvp,
            self.stop_if_shop,
            self.default_race,
            self.daily_race_stop_if_shop,
            self.legend_race_use_parfait
        ]

        for var in variables:
            var.trace('w', lambda *args: self.main_window.save_settings())

    def create_content(self):
        """Create dynamic tab content"""
        # Main content frame
        content_frame = ttk.Frame(self.parent, padding="15")
        content_frame.pack(fill=tk.BOTH, expand=True)
        content_frame.columnconfigure(0, weight=1)

        # Daily Activity Type dropdown
        daily_activity_frame = ttk.LabelFrame(content_frame, text="Daily Activity Type", padding="10")
        daily_activity_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        daily_activity_frame.columnconfigure(1, weight=1)

        ttk.Label(daily_activity_frame, text="Activity:").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 5), pady=5)

        daily_activity_dropdown = ttk.Combobox(
            daily_activity_frame,
            textvariable=self.daily_activity_type,
            values=["Team Trial", "Daily Races", "Legend Race"],
            state="readonly",
            width=15
        )
        daily_activity_dropdown.grid(row=0, column=1, sticky=tk.W, pady=5)
        daily_activity_dropdown.bind('<<ComboboxSelected>>', self.update_options_section)

        # Options section for dynamic content
        self.options_frame = ttk.LabelFrame(content_frame, text="Options", padding="10")
        self.options_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        self.options_frame.columnconfigure(0, weight=1)
        self.options_frame.columnconfigure(1, weight=1)

        # Initial options setup
        self.update_options_section()

    def update_options_section(self, event=None):
        """Update options section based on daily activity type"""
        # Clear existing widgets
        for widget in self.options_frame.winfo_children():
            widget.destroy()

        activity_type = self.daily_activity_type.get()

        if activity_type == "Team Trial":
            self.create_team_trial_options()
        elif activity_type == "Daily Races":
            self.create_daily_race_options()
        elif activity_type == "Legend Race":
            self.create_legend_race_options()

    def create_team_trial_options(self):
        """Create options for Team Trial"""
        # Opponent type dropdown
        ttk.Label(self.options_frame, text="Default Opponent:").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 5), pady=5)

        opponent_dropdown = ttk.Combobox(
            self.options_frame,
            textvariable=self.opponent_type,
            values=["Opponent 1", "Opponent 2", "Opponent 3"],
            state="readonly",
            width=15
        )
        opponent_dropdown.grid(row=0, column=1, sticky=tk.W, pady=5)

        # Checkboxes
        parfait_check = ttk.Checkbutton(
            self.options_frame,
            text="Use parfait if gift PvP",
            variable=self.use_parfait_gift_pvp
        )
        parfait_check.grid(row=1, column=0, sticky=tk.W, pady=5)

        shop_check = ttk.Checkbutton(
            self.options_frame,
            text="Stop if shop available",
            variable=self.stop_if_shop
        )
        shop_check.grid(row=1, column=1, sticky=tk.W, pady=5)

    def create_daily_race_options(self):
        """Create options for Daily Races"""
        # Race dropdown
        ttk.Label(self.options_frame, text="Default Race:").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 5), pady=5)

        race_dropdown = ttk.Combobox(
            self.options_frame,
            textvariable=self.default_race,
            values=["Moonlight Sho", "Jupiter Cup"],
            state="readonly",
            width=15
        )
        race_dropdown.grid(row=0, column=1, sticky=tk.W, pady=5)

        # Stop if shop available
        shop_check = ttk.Checkbutton(
            self.options_frame,
            text="Stop if shop available",
            variable=self.daily_race_stop_if_shop
        )
        shop_check.grid(row=1, column=0, sticky=tk.W, pady=5)

    def create_legend_race_options(self):
        """Create options for Legend Race"""
        # Use parfait if gift PvP
        parfait_check = ttk.Checkbutton(
            self.options_frame,
            text="Use parfait if gift PvP",
            variable=self.legend_race_use_parfait
        )
        parfait_check.grid(row=0, column=0, sticky=tk.W, pady=5)

    def start_team_trials(self):
        """Start functionality based on selected daily activity type"""
        activity_type = self.daily_activity_type.get()

        if activity_type == "Team Trial":
            return self.logic.start_team_trials()
        elif activity_type == "Daily Races":
            return self.logic.start_daily_races()
        elif activity_type == "Legend Race":
            return self.logic.start_legend_race()

    def stop_team_trials(self):
        """Stop team trials - delegates to logic handler"""
        self.logic.stop_team_trials()

    def is_active_tab(self):
        """Check if team trials tab is currently active"""
        try:
            # Get the parent notebook widget
            parent = self.parent
            while parent and not isinstance(parent.master, ttk.Notebook):
                parent = parent.master

            if parent and isinstance(parent.master, ttk.Notebook):
                notebook = parent.master
                current_tab = notebook.select()
                current_tab_text = notebook.tab(current_tab, "text")
                return current_tab_text == "Team Trials"
            return False
        except:
            return False

    def is_running(self):
        """Check if team trials is currently running - delegates to logic handler"""
        return self.logic.is_team_trials_running if hasattr(self, 'logic') else False

    @property
    def is_team_trials_running(self):
        """Property for backward compatibility"""
        return self.is_running()

    def get_settings(self):
        """Get current tab settings"""
        settings = {
            'daily_activity_type': self.daily_activity_type.get(),
            'opponent_type': self.opponent_type.get(),
            'use_parfait_gift_pvp': self.use_parfait_gift_pvp.get(),
            'stop_if_shop': self.stop_if_shop.get(),
            'default_race': self.default_race.get(),
            'daily_race_stop_if_shop': self.daily_race_stop_if_shop.get(),
            'legend_race_use_parfait': self.legend_race_use_parfait.get()
        }
        return settings

    def load_settings(self, settings):
        """Load settings into tab"""
        try:
            if 'daily_activity_type' in settings:
                self.daily_activity_type.set(settings['daily_activity_type'])
                self.update_options_section()

            if 'opponent_type' in settings:
                self.opponent_type.set(settings['opponent_type'])
            if 'use_parfait_gift_pvp' in settings:
                self.use_parfait_gift_pvp.set(settings['use_parfait_gift_pvp'])
            if 'stop_if_shop' in settings:
                self.stop_if_shop.set(settings['stop_if_shop'])
            if 'default_race' in settings:
                self.default_race.set(settings['default_race'])
            if 'daily_race_stop_if_shop' in settings:
                self.daily_race_stop_if_shop.set(settings['daily_race_stop_if_shop'])
            if 'legend_race_use_parfait' in settings:
                self.legend_race_use_parfait.set(settings['legend_race_use_parfait'])
        except Exception as e:
            print(f"Warning: Could not load team trials tab settings: {e}")