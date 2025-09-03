import tkinter as tk
from tkinter import ttk, scrolledtext


class LogSection:
    """Activity log section component"""

    def __init__(self, parent, main_window, row=0):
        self.parent = parent
        self.main_window = main_window
        self.row = row

        self.create_section()

    def create_section(self):
        """Create the activity log section"""
        self.frame = ttk.LabelFrame(self.parent, text="Activity Log", padding="10")
        self.frame.grid(row=self.row, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)

        # Log text area
        self.log_text = scrolledtext.ScrolledText(
            self.frame,
            height=10,
            width=70,
            wrap=tk.WORD
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Clear log button
        clear_button = ttk.Button(
            self.frame,
            text="Clear Log",
            command=self.clear_log
        )
        clear_button.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))

    def add_message(self, message):
        """Add message to log (must be called from main thread)"""
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)

    def clear_log(self):
        """Clear the log text"""
        self.log_text.delete(1.0, tk.END)