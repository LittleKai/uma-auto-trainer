import tkinter as tk
from tkinter import ttk
import os
import glob
import csv

from gui.dialogs.support_card_dialog import SupportCardDialog
from gui.dialogs.preset_name_dialog import PresetNameDialog


class EventChoiceTab:
    """Event choice configuration tab with enhanced UI - dropdown presets and card boxes"""

    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window

        # Initialize variables
        self.init_variables()

        # Load Uma Musume data from CSV
        self.uma_musume_data = self.load_uma_musume_data()

        # Store reference to unknown event action dropdown
        self.action_dropdown = None

        # Store support card selection boxes
        self.support_card_boxes = []

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

        # Variables for 20 preset sets with custom names
        self.current_set = tk.IntVar(value=1)
        self.preset_names = {}
        self.preset_sets = {}

        for i in range(1, 21):
            self.preset_names[i] = tk.StringVar(value=f"Preset {i}")
            self.preset_sets[i] = {
                'uma_musume': tk.StringVar(value="None"),
                'support_cards': [tk.StringVar(value="None") for _ in range(6)]
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

        # Add preset names
        for preset_name in self.preset_names.values():
            variables.append(preset_name)

        for var in variables:
            var.trace('w', lambda *args: self.main_window.save_settings())

        # Special handling for Uma Musume selection to update strategy
        self.selected_uma_musume.trace('w', self.on_uma_musume_change)
        self.selected_uma_musume.trace('w', lambda *args: self.main_window.save_settings())

    def create_content(self):
        """Create tab content with enhanced UI"""
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

        # Main content frame
        content_frame = ttk.Frame(scrollable_frame, padding="8")
        content_frame.pack(fill=tk.BOTH, expand=True)
        content_frame.columnconfigure(0, weight=1, minsize=720)

        # Create sections
        self.create_support_selection(content_frame, row=0)
        self.create_mode_selection(content_frame, row=1)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_mode_selection(self, parent, row):
        """Create mode selection section"""
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
        """Create enhanced support card selection with dropdown presets and card boxes"""
        support_frame = ttk.LabelFrame(parent, text="Support Card Selection", padding="2")
        support_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), padx=(0, 25))
        support_frame.columnconfigure(0, weight=1)

        # Uma Musume and Preset selection in same row
        selection_container = ttk.Frame(support_frame)
        selection_container.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        selection_container.columnconfigure(0, weight=0)  # 1/3 width for Uma
        selection_container.columnconfigure(1, weight=1)  # 2/3 width for Preset

        # Left side - Uma Musume
        uma_container = ttk.Frame(selection_container)
        uma_container.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 20))

        ttk.Label(
            uma_container,
            text="Uma Musume:",
            font=("Arial", 9),
            foreground="#CC0066"
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.uma_dropdown = ttk.Combobox(
            uma_container,
            textvariable=self.selected_uma_musume,
            values=self.get_uma_musume_list(),
            state="readonly",
            font=("Arial", 9),
            width=20
        )
        self.uma_dropdown.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Right side - Preset
        preset_container = ttk.Frame(selection_container)
        preset_container.grid(row=0, column=1, sticky=(tk.W, tk.E))

        ttk.Label(
            preset_container,
            text="Preset:",
            font=("Arial", 9, "bold"),
            foreground="#0066CC"
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.preset_dropdown = ttk.Combobox(
            preset_container,
            values=self._get_preset_names(),
            state="readonly",
            font=("Arial", 9),
            width=20
        )
        self.preset_dropdown.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.preset_dropdown.bind('<<ComboboxSelected>>', self._on_preset_selected)

        # Edit button
        edit_button = ttk.Button(
            preset_container,
            text="✏",
            width=3,
            command=self._edit_preset_name
        )
        edit_button.pack(side=tk.LEFT)

        # Support card boxes (6 boxes in 1 row)
        support_container = ttk.Frame(support_frame)
        support_container.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))

        self.support_card_boxes = []
        for i in range(6):
            box = self._create_support_card_box(support_container, i)
            box.grid(row=0, column=i, padx=3, pady=3, sticky=(tk.W, tk.E, tk.N, tk.S))
            self.support_card_boxes.append(box)
            support_container.columnconfigure(i, weight=1)

        # Update preset dropdown to show current selection
        self._update_preset_dropdown_selection()

    def _create_support_card_box(self, parent, index):
        """Create individual support card selection box"""
        box_frame = tk.Frame(
            parent,
            relief=tk.RAISED,
            borderwidth=2,
            bg="#f0f0f0",
            cursor="hand2"
        )

        # Label
        label = tk.Label(
            box_frame,
            text=f"Support {index + 1}",
            font=("Arial", 9, "bold"),
            bg="#f0f0f0",
            fg="#006600"
        )
        label.pack(pady=(3, 2))

        # Card name display
        card_display = tk.Label(
            box_frame,
            text="None",
            font=("Arial", 9),
            bg="white",
            relief=tk.SUNKEN,
            height=3,
            wraplength=100,
            justify=tk.CENTER
        )
        card_display.pack(padx=2, pady=(0, 2), fill=tk.BOTH, expand=True)

        # Bind click event
        box_frame.bind('<Button-1>', lambda e, idx=index: self._open_support_card_dialog(idx))
        label.bind('<Button-1>', lambda e, idx=index: self._open_support_card_dialog(idx))
        card_display.bind('<Button-1>', lambda e, idx=index: self._open_support_card_dialog(idx))

        # Store card display label for updates
        box_frame.card_display = card_display

        # Update initial display
        self._update_card_display(box_frame, self.support_cards[index].get())

        # Bind variable change to update display
        self.support_cards[index].trace('w', lambda *args, frame=box_frame, idx=index:
        self._update_card_display(frame, self.support_cards[idx].get()))

        return box_frame

    def _update_card_display(self, box_frame, card_value):
        """Update card display label"""
        if card_value == "None" or not card_value:
            display_text = "None"
            box_frame.card_display.config(text=display_text, fg="gray")
        else:
            # Extract card name (remove type prefix if present)
            if ":" in card_value:
                display_text = card_value.split(":", 1)[1].strip()
            else:
                display_text = card_value
            box_frame.card_display.config(text=display_text, fg="black")

    def _open_support_card_dialog(self, index):
        """Open support card selection dialog"""
        current_selection = self.support_cards[index].get()

        def on_card_selected(selected_card):
            self.support_cards[index].set(selected_card)

        SupportCardDialog(self.parent, current_selection, on_card_selected)

    def _get_preset_names(self):
        """Get list of preset names for dropdown"""
        names = []
        for i in range(1, 9):
            name = self.preset_names[i].get()
            names.append(name)
        return names

    def _update_preset_dropdown_selection(self):
        """Update preset dropdown to show current selection"""
        current_set = self.current_set.get()
        preset_name = self.preset_names[current_set].get()
        self.preset_dropdown.set(preset_name)

    def _on_preset_selected(self, event=None):
        """Handle preset selection from dropdown"""
        selected_name = self.preset_dropdown.get()

        # Find preset number by name
        for preset_num, name_var in self.preset_names.items():
            if name_var.get() == selected_name:
                self.switch_preset_set(preset_num)
                break

    def _edit_preset_name(self):
        """Open dialog to edit current preset name"""
        current_set = self.current_set.get()
        current_name = self.preset_names[current_set].get()

        def on_name_changed(new_name):
            self.preset_names[current_set].set(new_name)
            self.preset_dropdown['values'] = self._get_preset_names()
            self._update_preset_dropdown_selection()

        PresetNameDialog(self.parent, current_name, on_name_changed)

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

        # Update dropdown values
        self.uma_dropdown['values'] = self.get_uma_musume_list()
        self._update_preset_dropdown_selection()

        # Update strategy checkboxes
        self.update_strategy_checkboxes(selected_uma)

    def on_mode_change(self):
        """Handle mode change to ensure exactly one mode is selected"""
        if not self.auto_event_map_var.get() and not self.auto_first_choice_var.get():
            self.auto_first_choice_var.set(True)
            return

        if self.auto_event_map_var.get() and self.auto_first_choice_var.get():
            sender = self.parent.focus_get()
            if sender == self.auto_event_check:
                self.auto_first_choice_var.set(False)
            else:
                self.auto_event_map_var.set(False)

        self.update_action_dropdown_visibility()

    def update_action_dropdown_visibility(self):
        """Update visibility of unknown event action dropdown"""
        if hasattr(self, 'action_dropdown') and self.action_dropdown:
            if self.auto_first_choice_var.get():
                self.action_dropdown.configure(state="disabled")
            else:
                self.action_dropdown.configure(state="readonly")

    def get_uma_musume_list(self):
        """Get list of available Uma Musume"""
        uma_list = ["None"]
        try:
            uma_folder = "assets/event_map/uma_musume"
            if os.path.exists(uma_folder):
                json_files = glob.glob(os.path.join(uma_folder, "*.json"))
                for file_path in json_files:
                    filename = os.path.basename(file_path).replace('.json', '')
                    uma_list.append(filename)

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

    def update_strategy_checkboxes(self, uma_musume_name):
        """Update Strategy Tab checkboxes based on Uma Musume data"""
        if uma_musume_name == "None" or uma_musume_name not in self.uma_musume_data:
            return

        uma_data = self.uma_musume_data[uma_musume_name]

        try:
            if hasattr(self.main_window, 'update_strategy_filters'):
                self.main_window.update_strategy_filters(uma_data)
                return

            strategy_tab = getattr(self.main_window, 'strategy_tab', None)
            if strategy_tab and hasattr(strategy_tab, 'update_filters_from_uma_data'):
                strategy_tab.update_filters_from_uma_data(uma_data)
                return

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
        """Handle Uma Musume selection change"""
        selected_uma = self.selected_uma_musume.get()
        self.update_strategy_checkboxes(selected_uma)

    def get_settings(self):
        """Get current tab settings"""
        settings = {
            'auto_event_map': self.auto_event_map_var.get(),
            'auto_first_choice': self.auto_first_choice_var.get(),
            'uma_musume': self.selected_uma_musume.get(),
            'support_cards': [card.get() for card in self.support_cards],
            'unknown_event_action': self.unknown_event_action.get(),
            'current_set': self.current_set.get(),
            'preset_names': {},
            'preset_sets': {}
        }

        # Save preset names
        for set_num, name_var in self.preset_names.items():
            settings['preset_names'][set_num] = name_var.get()

        # Save preset sets
        for set_num, preset in self.preset_sets.items():
            settings['preset_sets'][set_num] = {
                'uma_musume': preset['uma_musume'].get(),
                'support_cards': [card.get() for card in preset['support_cards']]
            }

        return settings

    def load_settings(self, settings):
        """Load settings into tab"""
        try:
            auto_event_map = settings.get('auto_event_map', False)
            auto_first_choice = settings.get('auto_first_choice', True)

            if not auto_event_map and not auto_first_choice:
                auto_first_choice = True

            # Temporarily disable trace
            self.auto_event_map_var.trace_vdelete('w', self.auto_event_map_var.trace_vinfo()[0][1] if self.auto_event_map_var.trace_vinfo() else None)
            self.auto_first_choice_var.trace_vdelete('w', self.auto_first_choice_var.trace_vinfo()[0][1] if self.auto_first_choice_var.trace_vinfo() else None)

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

            # Load preset names
            if 'preset_names' in settings:
                for set_num, name in settings['preset_names'].items():
                    set_num = int(set_num)
                    if set_num in self.preset_names:
                        self.preset_names[set_num].set(name)

            # Load preset sets
            if 'preset_sets' in settings:
                for set_num, preset_data in settings['preset_sets'].items():
                    set_num = int(set_num)
                    if set_num in self.preset_sets:
                        self.preset_sets[set_num]['uma_musume'].set(preset_data.get('uma_musume', 'None'))
                        preset_support_cards = preset_data.get('support_cards', ['None'] * 6)
                        for i, card in enumerate(preset_support_cards[:6]):
                            self.preset_sets[set_num]['support_cards'][i].set(card)

            # Load current set
            if 'current_set' in settings:
                self.current_set.set(settings['current_set'])

            # Update preset dropdown
            if hasattr(self, 'preset_dropdown'):
                self.preset_dropdown['values'] = self._get_preset_names()
                self._update_preset_dropdown_selection()

            # Update strategy checkboxes
            self.update_strategy_checkboxes(self.selected_uma_musume.get())

            # Update dropdown visibility
            self.update_action_dropdown_visibility()

        except Exception as e:
            print(f"Warning: Could not load event choice tab settings: {e}")