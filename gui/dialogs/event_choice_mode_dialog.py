import tkinter as tk
from tkinter import ttk


class EventChoiceModeDialog:
    """Dialog for configuring Event Choice Mode settings"""

    def __init__(self, parent, event_choice_tab):
        self.parent = parent
        self.event_choice_tab = event_choice_tab
        self.window = tk.Toplevel(parent)
        self.window.title("Event Choice Mode Configuration")
        self.window.resizable(False, False)

        # Keep window on top and set as dialog
        self.window.attributes('-topmost', True)
        self.window.transient(parent)
        self.window.grab_set()

        # Initialize variables (temporary copies)
        self.init_variables()

        # Setup UI
        self.setup_ui()

        # Load current values
        self.load_current_values()

        # Bind events
        self.window.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.center_window()

    def init_variables(self):
        """Initialize dialog variables"""
        self.auto_event_map_var = tk.BooleanVar()
        self.auto_first_choice_var = tk.BooleanVar()
        self.unknown_event_action = tk.StringVar()

    def setup_ui(self):
        """Setup the user interface"""
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Event Choice Mode Configuration",
            font=("Arial", 12, "bold")
        )
        title_label.pack(pady=(0, 15))

        # Info text
        info_label = ttk.Label(
            main_frame,
            text="Configure how the bot handles event choices during gameplay.",
            font=("Arial", 9),
            justify=tk.CENTER,
            foreground="blue"
        )
        info_label.pack(pady=(0, 15))

        # Mode selection frame
        mode_frame = ttk.LabelFrame(main_frame, text="Event Choice Mode", padding="10")
        mode_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Auto Event Map checkbox
        self.auto_event_check = ttk.Checkbutton(
            mode_frame,
            text="Auto Event Map (use event database)",
            variable=self.auto_event_map_var,
            command=self.on_mode_change
        )
        self.auto_event_check.pack(anchor=tk.W, pady=5)

        # Auto First Choice checkbox
        auto_first_check = ttk.Checkbutton(
            mode_frame,
            text="Auto First Choice (always select first option)",
            variable=self.auto_first_choice_var,
            command=self.on_mode_change
        )
        auto_first_check.pack(anchor=tk.W, pady=5)

        # Unknown Event Action frame
        action_frame = ttk.Frame(mode_frame)
        action_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(
            action_frame,
            text="Unknown Event Action:",
            font=("Arial", 9, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        self.action_dropdown = ttk.Combobox(
            action_frame,
            textvariable=self.unknown_event_action,
            values=[
                "Auto select first choice",
                "Wait for user selection",
                "Search in other special events"
            ],
            state="readonly",
            font=("Arial", 9),
            width=35
        )
        self.action_dropdown.pack(fill=tk.X)

        # Separator
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=15)

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        # Cancel button
        cancel_btn = ttk.Button(
            button_frame,
            text="Cancel",
            command=self.on_cancel
        )
        cancel_btn.pack(side=tk.RIGHT, padx=(5, 0))

        # Save button
        save_btn = ttk.Button(
            button_frame,
            text="Save",
            command=self.save_settings
        )
        save_btn.pack(side=tk.RIGHT)

    def load_current_values(self):
        """Load current values from event choice tab"""
        self.auto_event_map_var.set(
            self.event_choice_tab.auto_event_map_var.get()
        )
        self.auto_first_choice_var.set(
            self.event_choice_tab.auto_first_choice_var.get()
        )
        self.unknown_event_action.set(
            self.event_choice_tab.unknown_event_action.get()
        )
        self.update_action_dropdown_visibility()

    def on_mode_change(self):
        """Handle mode change to ensure exactly one mode is selected"""
        if not self.auto_event_map_var.get() and not self.auto_first_choice_var.get():
            self.auto_first_choice_var.set(True)
            return

        if self.auto_event_map_var.get() and self.auto_first_choice_var.get():
            sender = self.window.focus_get()
            if sender == self.auto_event_check:
                self.auto_first_choice_var.set(False)
            else:
                self.auto_event_map_var.set(False)

        self.update_action_dropdown_visibility()

    def update_action_dropdown_visibility(self):
        """Update visibility of unknown event action dropdown"""
        if self.auto_first_choice_var.get():
            self.action_dropdown.configure(state="disabled")
        else:
            self.action_dropdown.configure(state="readonly")

    def save_settings(self):
        """Save settings and close window"""
        self.event_choice_tab.auto_event_map_var.set(
            self.auto_event_map_var.get()
        )
        self.event_choice_tab.auto_first_choice_var.set(
            self.auto_first_choice_var.get()
        )
        self.event_choice_tab.unknown_event_action.set(
            self.unknown_event_action.get()
        )

        # Update main tab's dropdown visibility
        self.event_choice_tab.update_action_dropdown_visibility()

        # Trigger save
        self.event_choice_tab.main_window.save_settings()

        self.window.destroy()

    def on_cancel(self):
        """Handle cancel"""
        self.window.destroy()

    def center_window(self):
        """Center the window on screen"""
        self.window.update_idletasks()

        width = 450
        height = 350

        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        x = parent_x + (parent_width // 2) - (width // 2)
        y = parent_y + (parent_height // 2) - (height // 2)

        self.window.geometry(f"{width}x{height}+{x}+{y}")