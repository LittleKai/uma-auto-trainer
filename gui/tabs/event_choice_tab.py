import tkinter as tk
from tkinter import ttk
import os
import glob
import csv


class EventChoiceTab:
    """Event choice configuration tab with Uma Musume data integration and improved support card loading"""

    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window

        # Initialize variables
        self.init_variables()

        # Load Uma Musume data from CSV
        self.uma_musume_data = self.load_uma_musume_data()

        # Store reference to unknown event action dropdown
        self.action_dropdown = None

        # Store preset button references for styling
        self.preset_buttons = {}

        # Bind variable changes to auto-save and strategy updates
        self.bind_variable_changes()

        # Create tab content
        self.create_content()

    def init_variables(self):
        """Initialize tab variables"""
        self.auto_event_map_var = tk.BooleanVar(value=False)
        self.auto_first_choice_var = tk.BooleanVar(value=True)
        self.selected_uma_musume = tk.StringVar(value="None")
        self.support_cards = [tk.StringVar(value="None") for _ in range(6)]
        self.unknown_event_action = tk.StringVar(value="Auto select first choice")

        # Variables for 6 preset sets
        self.current_set = tk.IntVar(value=1)
        self.preset_sets = {
            1: {
                'uma_musume': tk.StringVar(value="None"),
                'support_cards': [tk.StringVar(value="None") for _ in range(6)]
            },
            2: {
                'uma_musume': tk.StringVar(value="None"),
                'support_cards': [tk.StringVar(value="None") for _ in range(6)]
            },
            3: {
                'uma_musume': tk.StringVar(value="None"),
                'support_cards': [tk.StringVar(value="None") for _ in range(6)]
            },
            4: {
                'uma_musume': tk.StringVar(value="None"),
                'support_cards': [tk.StringVar(value="None") for _ in range(6)]
            },
            5: {
                'uma_musume': tk.StringVar(value="None"),
                'support_cards': [tk.StringVar(value="None") for _ in range(6)]
            },
            6: {
                'uma_musume': tk.StringVar(value="None"),
                'support_cards': [tk.StringVar(value="None") for _ in range(6)]
            }
        }

    def load_uma_musume_data(self):
        """Load Uma Musume data from CSV file"""
        data = {}
        try:
            csv_path = "assets/uma_musume_data.csv"
            if os.path.exists(csv_path):
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        uma_name = row.get('uma_musume', '')
                        if uma_name:
                            data[uma_name] = {
                                'turf': row.get('Turf', '').upper() in ['A', 'B'],
                                'dirt': row.get('Dirt', '').upper() in ['A', 'B'],
                                'sprint': row.get('Sprint', '').upper() in ['A', 'B'],
                                'mile': row.get('Mile', '').upper() in ['A', 'B'],
                                'medium': row.get('Medium', '').upper() in ['A', 'B'],
                                'long': row.get('Long', '').upper() in ['A', 'B']
                            }
            else:
                print(f"Warning: Uma Musume data file not found: {csv_path}")
        except Exception as e:
            print(f"Error loading Uma Musume data: {e}")
        return data

    def bind_variable_changes(self):
        """Bind variable change events to auto-save and strategy updates"""
        variables = [
            self.auto_event_map_var,
            self.auto_first_choice_var,
            self.unknown_event_action,
            *self.support_cards,
            self.current_set
        ]

        # Add preset sets variables
        for preset in self.preset_sets.values():
            variables.extend([preset['uma_musume']] + preset['support_cards'])

        for var in variables:
            var.trace('w', lambda *args: self.main_window.save_settings())

        # Special handling for Uma Musume selection to update strategy
        self.selected_uma_musume.trace('w', self.on_uma_musume_change)
        self.selected_uma_musume.trace('w', lambda *args: self.main_window.save_settings())

    def create_content(self):
        """Create tab content with increased width"""
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

        # Main content frame with increased width and reduced padding
        content_frame = ttk.Frame(scrollable_frame, padding="8")
        content_frame.pack(fill=tk.BOTH, expand=True)
        content_frame.columnconfigure(0, weight=1, minsize=740)

        # Create sections
        self.create_support_selection(content_frame, row=0)
        self.create_mode_selection(content_frame, row=1)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_mode_selection(self, parent, row):
        """Create mode selection section with checkboxes in same row"""
        mode_frame = ttk.LabelFrame(parent, text="Event Choice Mode", padding="8")
        mode_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(8, 0))

        # Checkboxes container
        checkbox_container = ttk.Frame(mode_frame)
        checkbox_container.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 8))

        # Auto Event Map mode
        self.auto_event_check = ttk.Checkbutton(
            checkbox_container,
            text="Auto Event Map",
            variable=self.auto_event_map_var,
            command=self.on_mode_change
        )
        self.auto_event_check.pack(side=tk.LEFT, padx=(0, 20))

        # Auto First Choice mode
        auto_first_check = ttk.Checkbutton(
            checkbox_container,
            text="Auto First Choice",
            variable=self.auto_first_choice_var,
            command=self.on_mode_change
        )
        auto_first_check.pack(side=tk.LEFT)

        # Unknown Event Action
        action_container = ttk.Frame(mode_frame)
        action_container.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=0)

        ttk.Label(
            action_container,
            text="Unknown Event Action:",
            font=("Arial", 9)
        ).grid(row=0, column=0, sticky=tk.W, padx=(0, 10))

        self.action_dropdown = ttk.Combobox(
            action_container,
            textvariable=self.unknown_event_action,
            values=["Auto select first choice", "Wait for user selection", "Search in other special events"],
            state="readonly",
            font=("Arial", 9),
            width=30
        )
        self.action_dropdown.grid(row=0, column=1, sticky=(tk.W, tk.E))

        # Set initial visibility state
        self.update_action_dropdown_visibility()

    def create_support_selection(self, parent, row):
        """Create enhanced Support Card selection with preset sets"""
        support_frame = ttk.LabelFrame(parent, text="Support Card Selection", padding="8")
        support_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 8))

        # Uma Musume selection section with preset buttons
        uma_container = ttk.Frame(support_frame)
        uma_container.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 12))

        # Uma Musume label and dropdown
        ttk.Label(
            uma_container,
            text="Select Uma Musume:",
            font=("Arial", 9),
            foreground="#CC0066"
        ).pack(side=tk.LEFT, padx=(0, 15))

        self.uma_dropdown = ttk.Combobox(
            uma_container,
            textvariable=self.selected_uma_musume,
            values=self.get_uma_musume_list(),
            state="readonly",
            font=("Arial", 9),
            width=18
        )
        self.uma_dropdown.pack(side=tk.LEFT, padx=(0, 30))

        # Preset set buttons
        preset_container = ttk.Frame(uma_container)
        preset_container.pack(side=tk.LEFT, padx=(15, 0))

        ttk.Label(
            preset_container,
            text="Preset Sets:",
            font=("Arial", 9),
            foreground="#0066CC"
        ).pack(side=tk.LEFT, padx=(0, 8))

        # Create preset buttons with enhanced styling
        button_frame = ttk.Frame(preset_container)
        button_frame.pack(side=tk.LEFT)

        for i in range(1, 7):
            btn = tk.Button(
                button_frame,
                text=str(i),
                command=lambda x=i: self.switch_preset_set(x),
                width=3,
                height=1,
                font=("Arial", 9),
                relief="raised",
                bd=2
            )
            btn.pack(side=tk.LEFT, padx=1)
            self.preset_buttons[i] = btn

        # Set initial active button
        self.update_preset_button_styles()

        # Configure columns for equal distribution with increased space
        for i in range(3):
            support_frame.columnconfigure(i, weight=1, minsize=200)

        support_cards_list = self.get_support_cards_list()

        # Create 2 rows of 3 support cards each with original layout
        for i in range(6):
            row_pos = (i // 3) + 1  # Start from row 1
            col_pos = i % 3         # 0,1,2 for columns

            card_frame = ttk.Frame(support_frame)
            card_frame.grid(row=row_pos, column=col_pos, sticky=(tk.W, tk.E),
                            padx=8, pady=2)
            card_frame.columnconfigure(1, weight=1)

            # Support label on top
            ttk.Label(
                card_frame,
                text=f"Support {i+1}:",
                font=("Arial", 9),
                foreground="#006600"
            ).grid(row=0, column=0, sticky=tk.W, pady=(0, 4))

            # Dropdown below label
            support_combo = ttk.Combobox(
                card_frame,
                textvariable=self.support_cards[i],
                values=["None"] + support_cards_list,
                state="readonly",
                font=("Arial", 9),
                width=23
            )
            support_combo.grid(row=1, column=0, sticky=(tk.W, tk.E))

    def switch_preset_set(self, set_number):
        """Switch to a different preset set and update strategy checkboxes"""
        # Save current values to current set
        current = self.current_set.get()
        self.preset_sets[current]['uma_musume'].set(self.selected_uma_musume.get())
        for i, card in enumerate(self.support_cards):
            self.preset_sets[current]['support_cards'][i].set(card.get())

        # Load values from new set
        self.current_set.set(set_number)
        selected_uma = self.preset_sets[set_number]['uma_musume'].get()
        self.selected_uma_musume.set(selected_uma)

        for i, card in enumerate(self.support_cards):
            card.set(self.preset_sets[set_number]['support_cards'][i].get())

        # Update dropdown values to reflect new selection
        self.uma_dropdown['values'] = self.get_uma_musume_list()

        # Update button styles
        self.update_preset_button_styles()

        # Update strategy checkboxes based on new Uma Musume selection
        self.update_strategy_checkboxes(selected_uma)

    def update_preset_button_styles(self):
        """Update preset button visual styles to show active set"""
        current = self.current_set.get()

        for i, btn in self.preset_buttons.items():
            if i == current:
                # Active button - highlighted
                btn.configure(
                    bg="#4CAF50",
                    fg="white",
                    relief="sunken",
                    font=("Arial", 9, "bold")
                )
            else:
                # Inactive button - normal
                btn.configure(
                    bg="SystemButtonFace",
                    fg="black",
                    relief="raised",
                    font=("Arial", 9)
                )

    def on_mode_change(self):
        """Handle mode change to ensure exactly one mode is selected and update UI visibility"""
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

        # Update dropdown visibility based on mode
        self.update_action_dropdown_visibility()

    def update_action_dropdown_visibility(self):
        """Update visibility of unknown event action dropdown based on mode selection"""
        if hasattr(self, 'action_dropdown') and self.action_dropdown:
            if self.auto_first_choice_var.get():
                # Disable dropdown when auto first choice is selected (grayed out)
                self.action_dropdown.configure(state="disabled")
            else:
                # Enable dropdown when auto event map is selected
                self.action_dropdown.configure(state="readonly")

    def get_uma_musume_list(self):
        """Get list of available Uma Musume from event map folder with None at top"""
        uma_list = ["None"]
        try:
            uma_folder = "assets/event_map/uma_musume"
            if os.path.exists(uma_folder):
                json_files = glob.glob(os.path.join(uma_folder, "*.json"))
                for file_path in json_files:
                    filename = os.path.basename(file_path).replace('.json', '')
                    uma_list.append(filename)

                # Try to get additional Uma Musume from other sources
                other_uma_folder = "assets/uma_musume"
                if os.path.exists(other_uma_folder):
                    json_files = glob.glob(os.path.join(other_uma_folder, "*.json"))
                    other_uma = []
                    for file_path in json_files:
                        filename = os.path.basename(file_path).replace('.json', '')
                        other_uma.append(filename)
                    other_uma.sort()
                    uma_list.extend(other_uma)
        except Exception as e:
            print(f"Error loading Uma Musume list: {e}")
        return uma_list

    def get_support_cards_list(self):
        """Get list of available Support Cards from event map subfolders with formatted names"""
        support_list = []
        try:
            support_folder = "assets/event_map/support_card"
            if os.path.exists(support_folder):
                # Define the order of support card types: spd, sta, pow, gut, wit, frd
                card_types = ["spd", "sta", "pow", "gut", "wit", "frd"]

                for card_type in card_types:
                    type_folder = os.path.join(support_folder, card_type)
                    if os.path.exists(type_folder):
                        json_files = glob.glob(os.path.join(type_folder, "*.json"))
                        for file_path in json_files:
                            filename = os.path.basename(file_path).replace('.json', '')
                            # Format display name as "type: filename"
                            display_name = f"{card_type}: {filename}"
                            support_list.append(display_name)

                # Also check for any JSON files directly in the support_card folder for backward compatibility
                direct_json_files = glob.glob(os.path.join(support_folder, "*.json"))
                for file_path in direct_json_files:
                    filename = os.path.basename(file_path).replace('.json', '')
                    support_list.append(filename)

        except Exception as e:
            print(f"Error loading Support Cards list: {e}")
        return support_list

    def update_strategy_checkboxes(self, uma_musume_name):
        """Update Strategy Tab checkboxes based on Uma Musume data"""
        if uma_musume_name == "None" or uma_musume_name not in self.uma_musume_data:
            return

        uma_data = self.uma_musume_data[uma_musume_name]

        # Try multiple approaches to update strategy tab
        try:
            # Method 1: Call main window method
            if hasattr(self.main_window, 'update_strategy_filters'):
                self.main_window.update_strategy_filters(uma_data)
                return

            # Method 2: Call strategy tab method directly
            strategy_tab = getattr(self.main_window, 'strategy_tab', None)
            if strategy_tab and hasattr(strategy_tab, 'update_filters_from_uma_data'):
                strategy_tab.update_filters_from_uma_data(uma_data)
                return

            # Method 3: Direct access to strategy tab variables
            if strategy_tab:
                if hasattr(strategy_tab, 'track_filters'):
                    strategy_tab.track_filters['turf'].set(uma_data['turf'])
                    strategy_tab.track_filters['dirt'].set(uma_data['dirt'])

                if hasattr(strategy_tab, 'distance_filters'):
                    strategy_tab.distance_filters['sprint'].set(uma_data['sprint'])
                    strategy_tab.distance_filters['mile'].set(uma_data['mile'])
                    strategy_tab.distance_filters['medium'].set(uma_data['medium'])
                    strategy_tab.distance_filters['long'].set(uma_data['long'])

        except Exception as e:
            print(f"Warning: Could not update strategy checkboxes: {e}")

    def on_uma_musume_change(self, *args):
        """Handle Uma Musume selection change to update strategy checkboxes"""
        selected_uma = self.selected_uma_musume.get()
        self.update_strategy_checkboxes(selected_uma)

    def get_settings(self):
        """Get current tab settings including preset sets"""
        settings = {
            'auto_event_map': self.auto_event_map_var.get(),
            'auto_first_choice': self.auto_first_choice_var.get(),
            'uma_musume': self.selected_uma_musume.get(),
            'support_cards': [card.get() for card in self.support_cards],
            'unknown_event_action': self.unknown_event_action.get(),
            'current_set': self.current_set.get(),
            'preset_sets': {}
        }

        # Save preset sets
        for set_num, preset in self.preset_sets.items():
            settings['preset_sets'][set_num] = {
                'uma_musume': preset['uma_musume'].get(),
                'support_cards': [card.get() for card in preset['support_cards']]
            }

        return settings

    def load_settings(self, settings):
        """Load settings into tab with validation for checkbox states and preset sets"""
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

            # Load current selections
            if 'uma_musume' in settings:
                self.selected_uma_musume.set(settings['uma_musume'])
            if 'unknown_event_action' in settings:
                self.unknown_event_action.set(settings['unknown_event_action'])

            support_cards = settings.get('support_cards', ['None'] * 6)
            for i, card in enumerate(support_cards[:6]):
                self.support_cards[i].set(card)

            # Load preset sets
            if 'preset_sets' in settings:
                for set_num, preset_data in settings['preset_sets'].items():
                    set_num = int(set_num)
                    if set_num in self.preset_sets:
                        self.preset_sets[set_num]['uma_musume'].set(preset_data.get('uma_musume', 'None'))
                        preset_support_cards = preset_data.get('support_cards', ['None'] * 6)
                        for i, card in enumerate(preset_support_cards[:6]):
                            self.preset_sets[set_num]['support_cards'][i].set(card)

            # Load current set and update button styles
            if 'current_set' in settings:
                self.current_set.set(settings['current_set'])

            # Update button styles after loading
            self.update_preset_button_styles()

            # Update strategy checkboxes based on loaded Uma Musume
            self.update_strategy_checkboxes(self.selected_uma_musume.get())

            # Update dropdown visibility
            self.update_action_dropdown_visibility()

        except Exception as e:
            print(f"Warning: Could not load event choice tab settings: {e}")