import tkinter as tk
from tkinter import ttk
import os
import glob
import csv

from gui.dialogs.support_card_dialog import SupportCardDialog
from gui.dialogs.preset_dialog import PresetDialog
from gui.dialogs.uma_musume_dialog import UmaMusumeDialog


class EventChoiceTab:
    """Event choice configuration tab with enhanced UI - dropdown presets and card boxes"""

    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window

        # Initialize variables
        self.init_variables()

        # Load Uma Musume data from CSV
        self.uma_musume_data = self.load_uma_musume_data()


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

        # Default stat caps
        self.default_stat_caps = {
            "spd": 1130,
            "sta": 1100,
            "pwr": 1080,
            "guts": 1100,
            "wit": 1130
        }

        # Variables for 20 preset sets with custom names
        self.current_set = tk.IntVar(value=1)
        self.preset_names = {}
        self.preset_sets = {}

        for i in range(1, 21):
            self.preset_names[i] = tk.StringVar(value=f"Preset {i}")
            self.preset_sets[i] = {
                'uma_musume': tk.StringVar(value="None"),
                'support_cards': [tk.StringVar(value="None") for _ in range(6)],
                'stat_caps': {
                    'spd': tk.IntVar(value=1130),
                    'sta': tk.IntVar(value=1100),
                    'pwr': tk.IntVar(value=1080),
                    'guts': tk.IntVar(value=1100),
                    'wit': tk.IntVar(value=1130)
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

        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Bind canvas resize to stretch scrollable_frame width
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(window_id, width=e.width))

        # Main content frame - don't expand
        content_frame = ttk.Frame(scrollable_frame, padding="8")
        content_frame.pack(anchor=tk.NW)

        # Create sections
        self.create_support_selection(content_frame, row=0)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill=tk.BOTH, expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_support_selection(self, parent, row):
        """Create enhanced support card selection with dropdown presets and card boxes"""
        support_frame = ttk.LabelFrame(parent, text="Support Card Selection", padding="2")
        # Don't stretch - use natural width
        support_frame.grid(row=row, column=0, sticky=(tk.W,), padx=(0, 5))

        # Uma Musume and Preset selection in same row
        selection_container = ttk.Frame(support_frame)
        selection_container.grid(row=0, column=0, sticky=(tk.W,), pady=(0, 5))

        # Left side - Uma Musume (clickable box)
        uma_container = ttk.Frame(selection_container)
        uma_container.grid(row=0, column=0, sticky=(tk.W,), padx=(0, 20))

        ttk.Label(
            uma_container,
            text="Uma Musume:",
            font=("Arial", 10),
            foreground="#CC0066"
        ).pack(side=tk.LEFT, padx=(0, 10))

        # Clickable box for Uma Musume selection
        self.uma_selection_box = tk.Label(
            uma_container,
            text="None",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#CC0066",
            relief=tk.SUNKEN,
            padx=10,
            pady=5,
            width=20,
            cursor="hand2"
        )
        self.uma_selection_box.pack(side=tk.LEFT)
        self.uma_selection_box.bind('<Button-1>', lambda e: self._open_uma_musume_dialog())

        # Update display when variable changes
        self.selected_uma_musume.trace('w', lambda *args: self._update_uma_display())

        # Right side - Preset (clickable box)
        preset_container = ttk.Frame(selection_container)
        preset_container.grid(row=0, column=1, sticky=(tk.W,))

        ttk.Label(
            preset_container,
            text="Preset:",
            font=("Arial", 10, "bold"),
            foreground="#0066CC"
        ).pack(side=tk.LEFT, padx=(0, 10))

        # Clickable box for preset selection
        self.preset_selection_box = tk.Label(
            preset_container,
            text="Preset 1",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#0066CC",
            relief=tk.SUNKEN,
            padx=10,
            pady=5,
            width=22,
            cursor="hand2"
        )
        self.preset_selection_box.pack(side=tk.LEFT)
        self.preset_selection_box.bind('<Button-1>', lambda e: self._open_preset_dialog())

        # Support card boxes (6 boxes in 1 row) - fixed equal width
        support_container = ttk.Frame(support_frame)
        support_container.grid(row=1, column=0, sticky=(tk.W,), pady=(5, 0))

        self.support_card_boxes = []
        for i in range(6):
            box = self._create_support_card_box(support_container, i)
            box.grid(row=0, column=i, padx=3, pady=3, sticky=(tk.N, tk.S))
            self.support_card_boxes.append(box)
            # Use uniform group to make all columns equal width
            support_container.columnconfigure(i, weight=1, uniform="card_box")

        # Stat Caps section
        self.create_stat_caps_section(support_frame, row=2)

        # Update preset display to show current selection
        self._update_preset_display()

    def create_stat_caps_section(self, parent, row):
        """Create stat caps configuration section"""
        stat_caps_frame = ttk.Frame(parent)
        stat_caps_frame.grid(row=row, column=0, sticky=(tk.W,), pady=(8, 0))

        # Label
        ttk.Label(
            stat_caps_frame,
            text="Stat Caps:",
            font=("Arial", 10, "bold"),
            foreground="#666666"
        ).pack(side=tk.LEFT, padx=(0, 10))

        # Stat cap inputs in a row
        self.stat_cap_entries = {}
        stat_labels = [
            ('spd', 'SPD', '#0066CC'),
            ('sta', 'STA', '#CC0066'),
            ('pwr', 'PWR', '#CC6600'),
            ('guts', 'GUTS', '#CC8800'),
            ('wit', 'WIT', '#007733')
        ]

        for stat_key, stat_label, color in stat_labels:
            stat_container = ttk.Frame(stat_caps_frame)
            stat_container.pack(side=tk.LEFT, padx=(0, 8))

            ttk.Label(
                stat_container,
                text=stat_label + ":",
                font=("Arial", 10),
                foreground=color
            ).pack(side=tk.LEFT, padx=(0, 2))

            # Get current preset's stat cap variable
            current_preset = self.current_set.get()
            stat_var = self.preset_sets[current_preset]['stat_caps'][stat_key]

            entry = ttk.Entry(
                stat_container,
                textvariable=stat_var,
                width=5,
                font=("Arial", 10),
                justify=tk.CENTER
            )
            entry.pack(side=tk.LEFT)
            self.stat_cap_entries[stat_key] = entry

            # Bind to auto-save and update logic
            stat_var.trace('w', lambda *args, sk=stat_key: self._on_stat_cap_change(sk))

    def _on_stat_cap_change(self, stat_key):
        """Handle stat cap value change"""
        try:
            # Update the logic module with new stat caps
            self._update_logic_stat_caps()
            # Auto-save settings
            self.main_window.save_settings()
        except Exception as e:
            print(f"Error updating stat cap: {e}")

    def _update_logic_stat_caps(self):
        """Update the logic module and constants with current preset's stat caps"""
        try:
            from core.logic import set_stat_caps
            from utils.constants import set_deck_info

            current_preset = self.current_set.get()

            # Get stat caps
            stat_caps = {}
            for stat_key in ['spd', 'sta', 'pwr', 'guts', 'wit']:
                stat_caps[stat_key] = self.preset_sets[current_preset]['stat_caps'][stat_key].get()

            # Get support cards
            support_cards = [card.get() for card in self.support_cards]

            # Get uma musume
            uma_musume = self.selected_uma_musume.get()

            # Update logic module
            set_stat_caps(stat_caps)

            # Update global constants (for event handler deck conditions)
            set_deck_info(uma_musume, support_cards, stat_caps)

        except Exception as e:
            print(f"Error updating logic stat caps: {e}")

    def _update_stat_cap_entries(self):
        """Update stat cap entry widgets to show current preset's values"""
        if not hasattr(self, 'stat_cap_entries'):
            return
        current_preset = self.current_set.get()
        for stat_key, entry in self.stat_cap_entries.items():
            # Update the entry's textvariable to point to current preset's stat cap
            entry.configure(textvariable=self.preset_sets[current_preset]['stat_caps'][stat_key])
        # Update logic module
        self._update_logic_stat_caps()

    # Card type colors
    CARD_TYPE_COLORS = {
        'spd': {'color': '#0066CC', 'name': 'SPEED'},
        'sta': {'color': '#CC0066', 'name': 'STAMINA'},
        'pow': {'color': '#CC6600', 'name': 'POWER'},
        'gut': {'color': '#CC8800', 'name': 'GUTS'},
        'wit': {'color': '#007733', 'name': 'WISDOM'},
        'frd': {'color': '#AA8800', 'name': 'FRIEND'}
    }

    def _get_card_type_info(self, card_value, index):
        """Get display text and color for card type label"""
        default_color = "#006600"
        default_text = f"Support {index + 1}"

        if not card_value or card_value == "None" or ":" not in card_value:
            return default_text, default_color, "#f0f0f0"

        card_type = card_value.split(":")[0].strip().lower()

        if card_type not in self.CARD_TYPE_COLORS:
            return default_text, default_color, "#f0f0f0"

        type_info = self.CARD_TYPE_COLORS[card_type]
        type_name = type_info['name']
        color = type_info['color']
        bg_color = self._lighten_color(color, 0.85)

        return type_name, color, bg_color

    def _lighten_color(self, hex_color, factor):
        """Lighten a hex color by a factor (0-1)"""
        try:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)

            r = int(r + (255 - r) * factor)
            g = int(g + (255 - g) * factor)
            b = int(b + (255 - b) * factor)

            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return "#f0f0f0"

    def _get_card_type_display(self, card_value, index):
        """Get display text for card type label (backward compatibility)"""
        type_name, _, _ = self._get_card_type_info(card_value, index)
        return type_name

    def _create_support_card_box(self, parent, index):
        """Create individual support card selection box with fixed size"""
        # Fixed width for each card box - font size 10
        BOX_WIDTH = 92

        box_frame = tk.Frame(
            parent,
            relief=tk.RAISED,
            borderwidth=2,
            bg="#f0f0f0",
            cursor="hand2",
            width=BOX_WIDTH,
            height=70
        )
        box_frame.pack_propagate(False)  # Prevent frame from shrinking to fit content

        # Label - will be updated based on card type
        label = tk.Label(
            box_frame,
            text=f"Support {index + 1}",
            font=("Arial", 10, "bold"),
            bg="#f0f0f0",
            fg="#006600"
        )
        label.pack(pady=(2, 1))

        # Card name display
        card_display = tk.Label(
            box_frame,
            text="None",
            font=("Arial", 10),
            bg="white",
            relief=tk.SUNKEN,
            height=3,
            wraplength=85,
            justify=tk.CENTER
        )
        card_display.pack(padx=1, pady=(0, 2), fill=tk.BOTH, expand=True)

        # Bind click event
        box_frame.bind('<Button-1>', lambda e, idx=index: self._open_support_card_dialog(idx))
        label.bind('<Button-1>', lambda e, idx=index: self._open_support_card_dialog(idx))
        card_display.bind('<Button-1>', lambda e, idx=index: self._open_support_card_dialog(idx))

        # Store references for updates
        box_frame.card_display = card_display
        box_frame.type_label = label
        box_frame.index = index

        # Update initial display
        self._update_card_display(box_frame, self.support_cards[index].get())

        # Bind variable change to update display
        self.support_cards[index].trace('w', lambda *args, frame=box_frame, idx=index:
        self._update_card_display(frame, self.support_cards[idx].get()))

        return box_frame

    def _update_card_display(self, box_frame, card_value):
        """Update card display label, type label, and colors"""
        # Get type info including colors
        if hasattr(box_frame, 'type_label') and hasattr(box_frame, 'index'):
            type_text, type_color, bg_color = self._get_card_type_info(card_value, box_frame.index)

            # Update type label with color
            box_frame.type_label.config(text=type_text, fg=type_color, bg=bg_color)

            # Update box frame background
            box_frame.config(bg=bg_color)

        # Update card name display
        if card_value == "None" or not card_value:
            display_text = "None"
            box_frame.card_display.config(text=display_text, fg="gray")
            # Reset to default colors
            if hasattr(box_frame, 'type_label'):
                box_frame.type_label.config(bg="#f0f0f0")
                box_frame.config(bg="#f0f0f0")
        else:
            # Extract card name (remove type prefix if present)
            if ":" in card_value:
                display_text = card_value.split(":", 1)[1].strip()
            else:
                display_text = card_value

            box_frame.card_display.config(text=display_text, fg="black", font=("Arial", 9, "bold"))

    def _open_support_card_dialog(self, index):
        """Open support card selection dialog"""
        current_selection = self.support_cards[index].get()

        def on_card_selected(selected_card):
            self.support_cards[index].set(selected_card)

        SupportCardDialog(self.parent, current_selection, on_card_selected)

    def _open_uma_musume_dialog(self):
        """Open Uma Musume selection dialog"""
        current_selection = self.selected_uma_musume.get()

        def on_uma_selected(selected_uma):
            self.selected_uma_musume.set(selected_uma)

        UmaMusumeDialog(self.parent, current_selection, on_uma_selected)

    def _update_uma_display(self):
        """Update Uma Musume display box"""
        if hasattr(self, 'uma_selection_box'):
            uma_name = self.selected_uma_musume.get()
            if uma_name and uma_name != "None":
                self.uma_selection_box.config(text=uma_name, fg="#CC0066")
            else:
                self.uma_selection_box.config(text="None", fg="gray")

    def _update_preset_display(self):
        """Update preset selection box to show current selection"""
        if hasattr(self, 'preset_selection_box'):
            current_set = self.current_set.get()
            preset_name = self.preset_names[current_set].get()
            self.preset_selection_box.config(text=f"#{current_set}: {preset_name}")

    def _open_preset_dialog(self):
        """Open preset selection dialog"""
        def on_preset_selected(preset_num):
            self.switch_preset_set(preset_num)
            self._update_preset_display()

        PresetDialog(
            self.parent,
            self.preset_names,
            self.preset_sets,
            self.current_set.get(),
            on_preset_selected
        )

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

        # Update UI elements
        self._update_uma_display()
        self._update_preset_display()

        # Update stat cap entries to show new preset's values
        self._update_stat_cap_entries()

        # Update strategy checkboxes
        self.update_strategy_checkboxes(selected_uma)

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
        current_preset = self.current_set.get()
        current_stat_caps = {}
        for stat_key in ['spd', 'sta', 'pwr', 'guts', 'wit']:
            current_stat_caps[stat_key] = self.preset_sets[current_preset]['stat_caps'][stat_key].get()

        settings = {
            'auto_event_map': self.auto_event_map_var.get(),
            'auto_first_choice': self.auto_first_choice_var.get(),
            'uma_musume': self.selected_uma_musume.get(),
            'support_cards': [card.get() for card in self.support_cards],
            'unknown_event_action': self.unknown_event_action.get(),
            'current_set': self.current_set.get(),
            'stat_caps': current_stat_caps,
            'preset_names': {},
            'preset_sets': {}
        }

        # Save preset names
        for set_num, name_var in self.preset_names.items():
            settings['preset_names'][set_num] = name_var.get()

        # Save preset sets
        for set_num, preset in self.preset_sets.items():
            preset_stat_caps = {}
            for stat_key in ['spd', 'sta', 'pwr', 'guts', 'wit']:
                preset_stat_caps[stat_key] = preset['stat_caps'][stat_key].get()

            settings['preset_sets'][set_num] = {
                'uma_musume': preset['uma_musume'].get(),
                'support_cards': [card.get() for card in preset['support_cards']],
                'stat_caps': preset_stat_caps
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
                        # Load stat caps for this preset
                        preset_stat_caps = preset_data.get('stat_caps', self.default_stat_caps)
                        for stat_key in ['spd', 'sta', 'pwr', 'guts', 'wit']:
                            cap_value = preset_stat_caps.get(stat_key, self.default_stat_caps.get(stat_key, 1200))
                            self.preset_sets[set_num]['stat_caps'][stat_key].set(cap_value)

            # Load current set
            if 'current_set' in settings:
                self.current_set.set(settings['current_set'])

            # Update preset display
            self._update_preset_display()

            # Update Uma Musume display
            self._update_uma_display()

            # Update stat cap entries to show current preset's values
            self._update_stat_cap_entries()

            # Update strategy checkboxes
            self.update_strategy_checkboxes(self.selected_uma_musume.get())

        except Exception as e:
            print(f"Warning: Could not load event choice tab settings: {e}")