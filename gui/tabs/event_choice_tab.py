import tkinter as tk
from tkinter import ttk
import os
import glob


class EventChoiceTab:
    """Event choice configuration tab"""

    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window

        # Initialize variables
        self.init_variables()

        # Create tab content
        self.create_content()

    def init_variables(self):
        """Initialize tab variables"""
        self.auto_event_map_var = tk.BooleanVar(value=False)
        self.auto_first_choice_var = tk.BooleanVar(value=True)
        self.selected_uma_musume = tk.StringVar(value="None")
        self.support_cards = [tk.StringVar(value="None") for _ in range(6)]
        self.unknown_event_action = tk.StringVar(value="Auto select first choice")

        # Bind variable changes to auto-save
        self.bind_variable_changes()

    def bind_variable_changes(self):
        """Bind variable change events to auto-save"""
        variables = [
            self.auto_event_map_var,
            self.auto_first_choice_var,
            self.selected_uma_musume,
            self.unknown_event_action,
            *self.support_cards
        ]

        for var in variables:
            var.trace('w', lambda *args: self.main_window.save_settings())

    def create_content(self):
        """Create tab content"""
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

        # Main content frame with wider padding
        content_frame = ttk.Frame(scrollable_frame, padding="10")
        content_frame.pack(fill=tk.BOTH, expand=True)
        content_frame.columnconfigure(0, weight=1)

        # Create sections
        self.create_mode_selection(content_frame, row=0)
        self.create_uma_selection(content_frame, row=1)
        self.create_support_selection(content_frame, row=2)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel for scrolling
        self.bind_mousewheel(canvas)

    def bind_mousewheel(self, canvas):
        """Bind mousewheel events for scrolling"""
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        def on_mousewheel_linux(event):
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")

        canvas.bind("<MouseWheel>", on_mousewheel)
        canvas.bind("<Button-4>", on_mousewheel_linux)
        canvas.bind("<Button-5>", on_mousewheel_linux)

    def create_mode_selection(self, parent, row):
        """Create event handling mode selection with checkboxes on same line and unknown event action below"""
        mode_frame = ttk.LabelFrame(parent, text="Event Handling Mode", padding="10")
        mode_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        mode_frame.columnconfigure(0, weight=1)

        # Checkbox container - same line
        checkbox_frame = ttk.Frame(mode_frame)
        checkbox_frame.pack(fill=tk.X, pady=(0, 15))

        self.auto_event_check = ttk.Checkbutton(
            checkbox_frame,
            text="Auto select events using event map",
            variable=self.auto_event_map_var,
            command=self.on_mode_change
        )
        self.auto_event_check.pack(side=tk.LEFT)

        self.auto_first_check = ttk.Checkbutton(
            checkbox_frame,
            text="Always select first choice",
            variable=self.auto_first_choice_var,
            command=self.on_mode_change
        )
        self.auto_first_check.pack(side=tk.LEFT, padx=(30, 0))

        # Unknown event action container
        action_container = ttk.Frame(mode_frame)
        action_container.pack(fill=tk.X)
        action_container.columnconfigure(1)

        ttk.Label(action_container, text="When event not in map:", font=("Arial", 9, "bold")).grid(
            row=0, column=0, sticky=tk.W, padx=(0, 15))

        action_dropdown = ttk.Combobox(
            action_container,
            textvariable=self.unknown_event_action,
            values=["Auto select first choice", "Wait for user selection"],
            state="readonly",
            font=("Arial", 9),
            width=30
        )
        action_dropdown.grid(row=0, column=1, sticky=(tk.W, tk.E))

    def create_uma_selection(self, parent, row):
        """Create Uma Musume selection"""
        uma_frame = ttk.LabelFrame(parent, text="Uma Musume Selection", padding="10")
        uma_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 20))

        uma_container = ttk.Frame(uma_frame)
        uma_container.pack(fill=tk.X)

        ttk.Label(uma_container, text="Select Uma Musume:", font=("Arial", 9, "bold")).pack(
            side=tk.LEFT, padx=(0, 15))

        self.uma_dropdown = ttk.Combobox(
            uma_container,
            textvariable=self.selected_uma_musume,
            values=self.get_uma_musume_list(),
            state="readonly",
            font=("Arial", 9),
            width=30
        )
        self.uma_dropdown.pack(side=tk.LEFT)

    def create_support_selection(self, parent, row):
        """Create Support Card selection with 2x3 grid layout"""
        support_frame = ttk.LabelFrame(parent, text="Support Card Selection", padding="10")
        support_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # Configure columns for equal distribution
        for i in range(2):
            support_frame.columnconfigure(i, weight=1)

        support_cards_list = self.get_support_cards_list()

        # Create 3 rows of 2 support cards each
        for i in range(6):
            row_pos = i // 2  # 0,1,2 for rows
            col_pos = i % 2   # 0,1 for columns

            card_frame = ttk.Frame(support_frame)
            card_frame.grid(row=row_pos, column=col_pos, sticky=(tk.W, tk.E),
                            padx=5, pady=10)
            card_frame.columnconfigure(1, weight=1)

            ttk.Label(
                card_frame,
                text=f"Support {i+1}:",
                width=12,
                font=("Arial", 9, "bold")
            ).grid(row=0, column=0, sticky=tk.W, padx=(0, 10))

            support_combo = ttk.Combobox(
                card_frame,
                textvariable=self.support_cards[i],
                values=["None"] + support_cards_list,
                state="readonly",
                font=("Arial", 9)
            )
            support_combo.grid(row=0, column=1, sticky=(tk.W, tk.E))

    def on_mode_change(self):
        """Handle mode change to ensure exactly one mode is selected"""
        # If both are unchecked, automatically check auto_first_choice
        if not self.auto_event_map_var.get() and not self.auto_first_choice_var.get():
            self.auto_first_choice_var.set(True)
            return

        # If both are checked, uncheck the other one based on which was clicked
        if self.auto_event_map_var.get() and self.auto_first_choice_var.get():
            sender = self.parent.focus_get()
            if sender == self.auto_event_check:
                self.auto_first_choice_var.set(False)
            else:
                self.auto_event_map_var.set(False)

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
            uma_list.sort()
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
            support_list.sort()
        except Exception as e:
            print(f"Error loading Support Cards list: {e}")
        return support_list

    def get_settings(self):
        """Get current tab settings"""
        return {
            'auto_event_map': self.auto_event_map_var.get(),
            'auto_first_choice': self.auto_first_choice_var.get(),
            'uma_musume': self.selected_uma_musume.get(),
            'support_cards': [card.get() for card in self.support_cards],
            'unknown_event_action': self.unknown_event_action.get()
        }

    def load_settings(self, settings):
        """Load settings into tab with validation for checkbox states"""
        try:
            auto_event_map = settings.get('auto_event_map', False)
            auto_first_choice = settings.get('auto_first_choice', True)

            # Ensure at least one checkbox is selected
            if not auto_event_map and not auto_first_choice:
                auto_first_choice = True

            # Temporarily disable trace to prevent auto-save during loading
            self.auto_event_map_var.trace_vdelete('w', self.auto_event_map_var.trace_vinfo()[0][1] if self.auto_event_map_var.trace_vinfo() else None)
            self.auto_first_choice_var.trace_vdelete('w', self.auto_first_choice_var.trace_vinfo()[0][1] if self.auto_first_choice_var.trace_vinfo() else None)

            # Set checkbox values
            self.auto_event_map_var.set(auto_event_map)
            self.auto_first_choice_var.set(auto_first_choice)

            # Re-enable trace
            self.auto_event_map_var.trace('w', lambda *args: self.main_window.save_settings())
            self.auto_first_choice_var.trace('w', lambda *args: self.main_window.save_settings())

            if 'uma_musume' in settings:
                self.selected_uma_musume.set(settings['uma_musume'])
            if 'unknown_event_action' in settings:
                self.unknown_event_action.set(settings['unknown_event_action'])

            support_cards = settings.get('support_cards', ['None'] * 6)
            for i, card in enumerate(support_cards[:6]):
                self.support_cards[i].set(card)

        except Exception as e:
            print(f"Warning: Could not load event choice tab settings: {e}")