import tkinter as tk
from tkinter import ttk, messagebox
import os
import glob


class EventChoiceWindow:
    """Window for configuring event choice settings"""

    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent.root)
        self.window.title("Event Choice Configuration")
        self.window.geometry("700x600")
        self.window.resizable(True, True)

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
        self.auto_event_map_var = tk.BooleanVar()
        self.auto_first_choice_var = tk.BooleanVar()
        self.selected_uma_musume = tk.StringVar()
        self.support_cards = [tk.StringVar() for _ in range(6)]

    def setup_ui(self):
        """Setup the user interface"""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        self.create_title(main_frame)

        # Mode selection
        self.create_mode_selection(main_frame)

        # Uma Musume selection
        self.create_uma_selection(main_frame)

        # Support Cards selection
        self.create_support_selection(main_frame)

        # Buttons
        self.create_buttons(main_frame)

    def create_title(self, parent):
        """Create title section"""
        title_label = ttk.Label(parent, text="Event Choice Configuration",
                                font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))

    def create_mode_selection(self, parent):
        """Create mode selection section"""
        mode_frame = ttk.LabelFrame(parent, text="Event Handling Mode", padding="10")
        mode_frame.pack(fill=tk.X, pady=(0, 15))

        self.auto_event_check = ttk.Checkbutton(
            mode_frame,
            text="Auto select events using event map",
            variable=self.auto_event_map_var,
            command=self.on_mode_change
        )
        self.auto_event_check.pack(anchor=tk.W, pady=5)

        self.auto_first_check = ttk.Checkbutton(
            mode_frame,
            text="Always select first choice",
            variable=self.auto_first_choice_var,
            command=self.on_mode_change
        )
        self.auto_first_check.pack(anchor=tk.W, pady=5)

    def create_uma_selection(self, parent):
        """Create Uma Musume selection section"""
        uma_frame = ttk.LabelFrame(parent, text="Uma Musume Selection", padding="10")
        uma_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(uma_frame, text="Select Uma Musume:").pack(anchor=tk.W, pady=(0, 5))

        self.uma_dropdown = ttk.Combobox(
            uma_frame,
            textvariable=self.selected_uma_musume,
            values=self.get_uma_musume_list(),
            state="readonly",
            width=40
        )
        self.uma_dropdown.pack(fill=tk.X, pady=(0, 5))

    def create_support_selection(self, parent):
        """Create Support Card selection section"""
        support_frame = ttk.LabelFrame(parent, text="Support Card Selection", padding="10")
        support_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        support_cards_list = self.get_support_cards_list()

        for i in range(6):
            row_frame = ttk.Frame(support_frame)
            row_frame.pack(fill=tk.X, pady=2)

            ttk.Label(row_frame, text=f"Support Card {i+1}:", width=15).pack(
                side=tk.LEFT, padx=(0, 10))

            support_combo = ttk.Combobox(
                row_frame,
                textvariable=self.support_cards[i],
                values=["None"] + support_cards_list,
                state="readonly",
                width=35
            )
            support_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def create_buttons(self, parent):
        """Create button section"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(15, 0))

        ttk.Button(button_frame, text="Cancel",
                   command=self.on_closing).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Save",
                   command=self.save_settings).pack(side=tk.RIGHT)

    def get_uma_musume_list(self):
        """Get list of available Uma Musume from event map folder"""
        uma_list = ["None"]
        try:
            uma_folder = "assets/event_map/uma_musume"
            if os.path.exists(uma_folder):
                json_files = glob.glob(os.path.join(uma_folder, "*.json"))
                for file_path in json_files:
                    filename = os.path.basename(file_path).replace('.json', '')
                    uma_list.append(filename)
        except Exception as e:
            print(f"Error loading Uma Musume list: {e}")
        return uma_list

    def get_support_cards_list(self):
        """Get list of available Support Cards from event map folder"""
        support_list = []
        try:
            support_folder = "assets/event_map/support_card"
            if os.path.exists(support_folder):
                json_files = glob.glob(os.path.join(support_folder, "*.json"))
                for file_path in json_files:
                    filename = os.path.basename(file_path).replace('.json', '')
                    support_list.append(filename)
        except Exception as e:
            print(f"Error loading Support Cards list: {e}")
        return support_list

    def on_mode_change(self):
        """Handle mode change - ensure only one mode is selected"""
        if self.auto_event_map_var.get() and self.auto_first_choice_var.get():
            # If both are checked, uncheck the other one
            sender = self.window.focus_get()
            if sender == self.auto_event_check:
                self.auto_first_choice_var.set(False)
            else:
                self.auto_event_map_var.set(False)

    def load_current_values(self):
        """Load current values from parent"""
        try:
            settings = self.parent.get_event_choice_settings()
            self.auto_event_map_var.set(settings.get('auto_event_map', False))
            self.auto_first_choice_var.set(settings.get('auto_first_choice', True))
            self.selected_uma_musume.set(settings.get('uma_musume', 'None'))

            support_cards = settings.get('support_cards', ['None'] * 6)
            for i, card in enumerate(support_cards[:6]):
                self.support_cards[i].set(card)
        except Exception as e:
            print(f"Error loading event choice settings: {e}")

    def save_settings(self):
        """Save settings and close window"""
        try:
            settings = {
                'auto_event_map': self.auto_event_map_var.get(),
                'auto_first_choice': self.auto_first_choice_var.get(),
                'uma_musume': self.selected_uma_musume.get(),
                'support_cards': [card.get() for card in self.support_cards]
            }

            self.parent.save_event_choice_settings(settings)
            self.window.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save event choice settings: {e}")

    def center_window(self):
        """Center the window on screen"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def on_closing(self):
        """Handle window closing"""
        self.window.destroy()