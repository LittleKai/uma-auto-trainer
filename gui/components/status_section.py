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
        """Create left column with bot status, date, and energy"""
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

        # Energy
        ttk.Label(left_column, text="Energy:", font=("Arial", 10, "bold")).grid(
            row=2, column=0, sticky=tk.W, pady=3)
        self.energy_label = ttk.Label(left_column, text="Unknown", foreground="blue")
        self.energy_label.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=3)

    def create_right_column(self):
        """Create right column with game window and key status"""
        right_column = ttk.Frame(self.frame)
        right_column.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N))
        right_column.columnconfigure(1, weight=1)

        # Game Window Status
        ttk.Label(right_column, text="Game Window:", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, pady=3)
        self.game_status_label = ttk.Label(right_column, text="Checking...", foreground="orange")
        self.game_status_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=3)

        # Key Status
        ttk.Label(right_column, text="Key Status:", font=("Arial", 10, "bold")).grid(
            row=1, column=0, sticky=tk.W, pady=3)
        self.key_status_label = ttk.Label(right_column, text="Checking...", foreground="orange")
        self.key_status_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=3)

    def set_bot_status(self, status, color):
        """Update bot status display"""
        self.status_label.config(text=status, foreground=color)

    def update_date(self, date_info):
        """Update current date display"""
        if date_info:
            if date_info.get('is_pre_debut', False):
                date_str = f"{date_info['year']} Year Pre-Debut (Day {date_info['absolute_day']}/72)"
            else:
                date_str = f"{date_info['year']} {date_info['month']} {date_info['period']} (Day {date_info['absolute_day']}/72)"
            self.date_label.config(text=date_str, foreground="blue")
        else:
            self.date_label.config(text="Unknown", foreground="red")

    def update_energy(self, energy_percentage):
        """Update energy display with color coding"""
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            minimum_energy = config.get('minimum_energy_percentage', 40)
            critical_energy = config.get('critical_energy_percentage', 20)
        except:
            minimum_energy = 40
            critical_energy = 20

        # Determine color based on energy level
        if energy_percentage >= minimum_energy:
            color = "green"
        elif energy_percentage >= critical_energy:
            color = "orange"
        else:
            color = "red"

        energy_str = f"{energy_percentage}%"
        self.energy_label.config(text=energy_str, foreground=color)

    def update_game_status(self, status, color):
        """Update game window status display"""
        self.game_status_label.config(text=status, foreground=color)

    def update_key_status(self, is_valid, message):
        """Update key validation status display"""
        if is_valid:
            self.key_status_label.config(text="Valid ✓", foreground="green")
        else:
            self.key_status_label.config(text="Invalid ✗", foreground="red")