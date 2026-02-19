import tkinter as tk
from tkinter import ttk
import json


class StatusSection:
    """Status monitoring section component"""

    def __init__(self, parent, main_window, row=0):
        self.parent = parent
        self.main_window = main_window
        self.row = row

        self.create_section()

    def create_section(self):
        """Create the status section"""
        self.frame = ttk.LabelFrame(self.parent, text="Status", padding="10")
        self.frame.grid(row=self.row, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)

        # Create left and right columns
        self.create_left_column()
        self.create_right_column()

    def create_left_column(self):
        """Create left column with bot status and date"""
        left_column = ttk.Frame(self.frame)
        left_column.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N), padx=(0, 10))
        left_column.columnconfigure(1, weight=1)

        # Bot Status
        ttk.Label(left_column, text="Bot Status:", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, pady=3)
        self.status_label = ttk.Label(left_column, text="Stopped", foreground="red")
        self.status_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=3)

        # Current Date
        ttk.Label(left_column, text="Current Date:", font=("Arial", 10, "bold")).grid(
            row=1, column=0, sticky=tk.W, pady=3)
        self.date_label = ttk.Label(left_column, text="Unknown", foreground="blue")
        self.date_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=3)

    def create_right_column(self):
        """Create right column with energy and scenario"""
        right_column = ttk.Frame(self.frame)
        right_column.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N))
        right_column.columnconfigure(1, weight=1)

        # Energy
        ttk.Label(right_column, text="Energy:", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, pady=3)

        energy_frame = ttk.Frame(right_column)
        energy_frame.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=3)

        self.energy_current_label = ttk.Label(energy_frame, text="0", foreground="blue")
        self.energy_current_label.grid(row=0, column=0, sticky=tk.W)

        self.energy_separator_label = ttk.Label(energy_frame, text="/", foreground="gray")
        self.energy_separator_label.grid(row=0, column=1, sticky=tk.W)

        self.energy_max_label = ttk.Label(energy_frame, text="0", foreground="blue")
        self.energy_max_label.grid(row=0, column=2, sticky=tk.W)

        # Scenario Selection
        ttk.Label(right_column, text="Scenario:", font=("Arial", 10, "bold")).grid(
            row=1, column=0, sticky=tk.W, pady=3)
        self.scenario_dropdown = ttk.Combobox(
            right_column,
            textvariable=self.main_window.scenario_selection,
            values=["URA Final", "Unity Cup"],
            state="readonly",
            width=15
        )
        self.scenario_dropdown.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=3)
        self.scenario_dropdown.set("URA Final")
        self.scenario_dropdown.bind('<<ComboboxSelected>>', self.on_scenario_change)

    def on_scenario_change(self, event=None):
        from utils.constants import set_scenario

        scenario = self.main_window.scenario_selection.get()
        set_scenario(scenario)
        self.main_window.save_settings()

        self.main_window.log_message(f"Scenario changed to: {scenario}")

    def set_bot_status(self, status, color):
        """Update bot status display"""
        self.status_label.config(text=status, foreground=color)

    def update_date(self, date_info):
        """Update current date display"""
        if date_info:
            if date_info.get('is_pre_debut', False):
                date_str = f"{date_info['year']} Year Pre-Debut (Day {date_info['absolute_day']}/75)"
            else:
                date_str = f"{date_info['year']} {date_info['month']} {date_info['period']} (Day {date_info['absolute_day']}/75)"
            self.date_label.config(text=date_str, foreground="blue")
        else:
            self.date_label.config(text="Unknown", foreground="red")

    def update_energy(self, energy_data):
        """Update energy display with color coding"""
        try:
            if isinstance(energy_data, tuple):
                current_energy, max_energy = energy_data
                current_energy_display = round(current_energy)
                max_energy_display = round(max_energy)
                energy_percentage = current_energy

                self.energy_current_label.config(text=str(current_energy_display))
                self.energy_max_label.config(text=str(max_energy_display), foreground="blue")
                self.energy_separator_label.config(text="/")

            elif isinstance(energy_data, (int, float)):
                current_energy_display = round(energy_data)
                energy_percentage = energy_data

                self.energy_current_label.config(text=str(current_energy_display))
                self.energy_separator_label.config(text="")
                self.energy_max_label.config(text="")

            else:
                self.energy_current_label.config(text="0", foreground="red")
                self.energy_separator_label.config(text="/")
                self.energy_max_label.config(text="0", foreground="blue")
                energy_percentage = 0

            # Load energy thresholds for color coding
            try:
                with open('config.json', 'r') as f:
                    config = json.load(f)
                minimum_energy = config.get('minimum_energy_percentage', 40)
                critical_energy = config.get('critical_energy_percentage', 20)
            except Exception:
                minimum_energy = 40
                critical_energy = 20

            if energy_percentage >= minimum_energy:
                current_color = "green"
            elif energy_percentage >= critical_energy:
                current_color = "orange"
            else:
                current_color = "red"

            self.energy_current_label.config(foreground=current_color)

        except Exception:
            self.energy_current_label.config(text="0", foreground="red")
            self.energy_separator_label.config(text="/")
            self.energy_max_label.config(text="0", foreground="blue")

    def update_game_status(self, status, color):
        """No-op: game window status removed from UI"""
        pass
