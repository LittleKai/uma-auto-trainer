import tkinter as tk
from tkinter import ttk


class ControlSection:
    """Bot control buttons section component"""

    def __init__(self, parent, main_window, row=0):
        self.parent = parent
        self.main_window = main_window
        self.row = row

        self.create_section()

    def create_section(self):
        """Create the control buttons section"""
        self.frame = ttk.Frame(self.parent)
        self.frame.grid(row=self.row, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)

        # Start button
        self.start_button = ttk.Button(
            self.frame,
            text="Start (F1)",
            command=self.main_window.start_bot
        )
        self.start_button.grid(row=0, column=0, padx=(0, 5), sticky=(tk.W, tk.E), ipady=5)

        # Stop button
        self.stop_button = ttk.Button(
            self.frame,
            text="Stop (F3)",
            command=self.main_window.stop_bot,
            state="disabled"
        )
        self.stop_button.grid(row=0, column=1, padx=(5, 0), sticky=(tk.W, tk.E), ipady=5)

    def set_running_state(self, is_running):
        """Update button states based on running status"""
        if is_running:
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
        else:
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")