import tkinter as tk
from tkinter import ttk
import os
import glob
import csv

from gui.dialogs.support_card_dialog import SupportCardDialog
from gui.dialogs.preset_dialog import PresetDialog
from gui.dialogs.uma_musume_dialog import UmaMusumeDialog
from gui.dialogs.race_schedule_dialog import RaceScheduleDialog

from core.style_handler import get_style_options, get_style_display_name


DEFAULT_RACE_SCHEDULE = [
    {"name": "Hanshin Juvenile Fillies", "day": 23},
    {"name": "Hopeful Stakes", "day": 24},
]


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

        # Debounce timers for wraplength updates
        self._wraplength_timers = {}

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

        # Debut style selection variable (none = disabled)
        self.debut_style = tk.StringVar(value="none")

        # Race schedule dialog filters (global, not per-preset)
        self.race_schedule_filters = dict(RaceScheduleDialog.DEFAULT_FILTERS)

        # Default stat caps
        self.default_stat_caps = {
            "spd": 1200,
            "sta": 1100,
            "pwr": 1200,
            "guts": 1200,
            "wit": 1200
        }

        # Default stop conditions
        self.default_stop_conditions = {
            'enable_stop_conditions': False,
            'stop_on_infirmary': False,
            'stop_on_need_rest': False,
            'stop_on_low_mood': False,
            'stop_on_race_day': False,
            'stop_mood_threshold': 'BAD',
            'stop_before_summer': False,
            'stop_at_month': False,
            'target_month': 'Classic Year Jun 1',
            'stop_on_ura_final': False,
            'stop_on_warning': False,
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
                    'spd': tk.IntVar(value=1200),
                    'sta': tk.IntVar(value=1100),
                    'pwr': tk.IntVar(value=1200),
                    'guts': tk.IntVar(value=1200),
                    'wit': tk.IntVar(value=1200)
                },
                'debut_style': 'none',
                'stop_conditions': dict(self.default_stop_conditions),
                'race_schedule': [dict(r) for r in DEFAULT_RACE_SCHEDULE]
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
            self.debut_style,
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
            var.trace('w', lambda *args: self._safe_save_settings())

        # Special handling for Uma Musume selection to update strategy
        self.selected_uma_musume.trace('w', self.on_uma_musume_change)
        self.selected_uma_musume.trace('w', lambda *args: self._safe_save_settings())

    def _safe_save_settings(self):
        """Safely save settings, checking if main_window is fully initialized"""
        try:
            # Skip auto-save during preset switching to avoid corrupting data
            if getattr(self, '_switching_preset', False):
                print(f"[DEBUG SAVE] _safe_save_settings BLOCKED (switching)")
                return
            # Check if main_window has all required attributes before saving
            if (hasattr(self.main_window, 'event_choice_tab') and
                hasattr(self.main_window, 'strategy_tab') and
                hasattr(self.main_window, 'log_section')):
                self.main_window.save_settings()
        except Exception as e:
            # Silently ignore errors during initialization
            pass

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

        # Main content frame - expand horizontally
        content_frame = ttk.Frame(scrollable_frame, padding="8")
        content_frame.pack(fill=tk.X, anchor=tk.NW)

        # Create sections
        self.create_support_selection(content_frame, row=0)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill=tk.BOTH, expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_support_selection(self, parent, row):
        """Create enhanced support card selection with dropdown presets and card boxes"""
        support_frame = ttk.LabelFrame(parent, text="Support Card Selection", padding="2")
        support_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        parent.columnconfigure(0, weight=1)

        # Uma Musume and Preset selection in same row
        selection_container = ttk.Frame(support_frame)
        selection_container.grid(row=0, column=0, sticky=(tk.W,), pady=(0, 5))

        # Left side - Uma Musume (clickable box)
        uma_container = ttk.Frame(selection_container)
        uma_container.grid(row=0, column=0, sticky=(tk.W,), padx=(0, 20))

        ttk.Label(
            uma_container,
            text="Uma:",
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
            width=18,
            cursor="hand2"
        )
        self.preset_selection_box.pack(side=tk.LEFT)
        self.preset_selection_box.bind('<Button-1>', lambda e: self._open_preset_dialog())

        # Edit preset name button (pencil icon)
        edit_name_btn = tk.Label(
            preset_container,
            text="\u270E",
            font=("Arial", 12),
            fg="#888888",
            cursor="hand2"
        )
        edit_name_btn.pack(side=tk.LEFT, padx=(4, 0))
        edit_name_btn.bind('<Button-1>', lambda e: self._edit_preset_name())

        # Support card boxes (6 boxes in 1 row) - distributed evenly
        support_container = ttk.Frame(support_frame)
        support_container.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        support_frame.columnconfigure(0, weight=1)

        self.support_card_boxes = []
        for i in range(6):
            box = self._create_support_card_box(support_container, i)
            box.grid(row=0, column=i, padx=3, pady=3, sticky=(tk.W, tk.E, tk.N, tk.S))
            self.support_card_boxes.append(box)
            # Use uniform group to make all columns equal width
            support_container.columnconfigure(i, weight=1, uniform="card_box")

        # Stat Caps section
        self.create_stat_caps_section(support_frame, row=2)

        # Debut Style + Race Schedule header on same row, treeview below
        row3_frame = ttk.Frame(support_frame)
        row3_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(8, 0))
        support_frame.columnconfigure(0, weight=1)

        header_row = ttk.Frame(row3_frame)
        header_row.pack(fill=tk.X)
        self.create_debut_style_section(header_row)
        self.create_race_schedule_header(header_row)

        self.create_race_schedule_tree(row3_frame)

        # Update preset display to show current selection
        self._update_preset_display()

    def _create_help_icon(self, parent, tooltip_text):
        """Create a (?) help icon with hover tooltip"""
        help_label = tk.Label(
            parent,
            text="(?)",
            font=("Arial", 9),
            fg="#888888",
            cursor="question_arrow"
        )
        help_label.pack(side=tk.LEFT, padx=(2, 0))

        # Tooltip on hover
        tooltip_window = [None]

        def show_tooltip(event):
            if tooltip_window[0]:
                return
            x = help_label.winfo_rootx() + help_label.winfo_width() + 5
            y = help_label.winfo_rooty()
            tw = tk.Toplevel(help_label)
            tw.wm_overrideredirect(True)
            tw.wm_attributes('-topmost', True)
            tw.wm_geometry(f"+{x}+{y}")
            frame = tk.Frame(tw, bg="#ffffe0", relief=tk.SOLID, borderwidth=1)
            frame.pack()
            tk.Label(
                frame, text=tooltip_text, bg="#ffffe0", fg="#333333",
                font=("Arial", 9), justify=tk.LEFT, wraplength=300, padx=8, pady=5
            ).pack()
            tooltip_window[0] = tw

        def hide_tooltip(event):
            if tooltip_window[0]:
                tooltip_window[0].destroy()
                tooltip_window[0] = None

        help_label.bind('<Enter>', show_tooltip)
        help_label.bind('<Leave>', hide_tooltip)

        return help_label

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
        ).pack(side=tk.LEFT, padx=(0, 0))

        self._create_help_icon(
            stat_caps_frame,
            "Set each stat's target cap value.\n"
            "When a stat approaches its cap, a score penalty is applied\n"
            "to training options that raise that stat, making the bot\n"
            "prefer training other stats instead.\n"
            "Penalty increases as stat gets closer to the cap."
        )

        # Spacer after (?)
        ttk.Frame(stat_caps_frame, width=8).pack(side=tk.LEFT)

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
            # Auto-save settings (respects _switching_preset flag)
            self._safe_save_settings()
        except Exception as e:
            print(f"Error updating stat cap: {e}")

    def create_debut_style_section(self, parent):
        """Create debut style selection section"""
        style_frame = ttk.Frame(parent)
        style_frame.pack(side=tk.LEFT, padx=(0, 20))

        # Style dropdown label
        ttk.Label(
            style_frame,
            text="Debut Style:",
            font=("Arial", 10, "bold"),
            foreground="#0066CC"
        ).pack(side=tk.LEFT, padx=(0, 0))

        self._create_help_icon(
            style_frame,
            "Auto-select running style at Pre-Debut race day.\n"
            "Set to 'None' to skip automatic style selection."
        )

        ttk.Frame(style_frame, width=5).pack(side=tk.LEFT)

        # Get style options
        style_options = get_style_options()
        style_values = [opt[1] for opt in style_options]

        # Style dropdown (separate display var to avoid overwriting debut_style with display name)
        self._style_display = tk.StringVar()
        self.style_combobox = ttk.Combobox(
            style_frame,
            textvariable=self._style_display,
            values=style_values,
            state="readonly",
            width=8
        )
        self.style_combobox.pack(side=tk.LEFT)

        # Set initial display value
        self._update_style_display()

        # Bind selection change
        self.style_combobox.bind('<<ComboboxSelected>>', self._on_style_combobox_change)

    def create_race_schedule_header(self, parent):
        """Create race schedule label and buttons (inline with debut style)"""
        schedule_header = ttk.Frame(parent)
        schedule_header.pack(side=tk.LEFT)

        ttk.Label(
            schedule_header,
            text="Race Schedule:",
            font=("Arial", 10, "bold"),
            foreground="#CC6600"
        ).pack(side=tk.LEFT, padx=(0, 0))

        self._create_help_icon(
            schedule_header,
            "Preferred races the bot will prioritize.\n"
            "On a scheduled race day, the bot will race\n"
            "instead of training (if race passes Strategy filters).\n"
            "Resets to defaults when Uma Musume changes."
        )

        ttk.Frame(schedule_header, width=5).pack(side=tk.LEFT)

        ttk.Button(
            schedule_header,
            text="Add",
            command=self._open_race_schedule_dialog,
            width=5
        ).pack(side=tk.LEFT, padx=(0, 3))

        ttk.Button(
            schedule_header,
            text="Del",
            command=self._delete_selected_race,
            width=4
        ).pack(side=tk.LEFT, padx=(0, 3))

        ttk.Button(
            schedule_header,
            text="Reset",
            command=self._reset_race_schedule,
            width=5
        ).pack(side=tk.LEFT)

    def create_race_schedule_tree(self, parent):
        """Create race schedule treeview (below header row)"""
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.X, pady=(4, 0))

        columns = ("day", "name", "grade")
        self.schedule_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            height=4,
            selectmode="browse"
        )

        self.schedule_tree.heading("day", text="Day")
        self.schedule_tree.heading("name", text="Race Name")
        self.schedule_tree.heading("grade", text="Grade")

        self.schedule_tree.column("day", width=40, anchor=tk.CENTER)
        self.schedule_tree.column("name", width=250)
        self.schedule_tree.column("grade", width=55, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.schedule_tree.yview)
        self.schedule_tree.configure(yscrollcommand=scrollbar.set)

        self.schedule_tree.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Delete key binding
        self.schedule_tree.bind("<Delete>", lambda e: self._delete_selected_race())

        # Populate with current preset's schedule
        self._refresh_schedule_tree()

    def _open_race_schedule_dialog(self):
        """Open race schedule selection dialog"""
        def on_race_selected(race_info):
            # race_info: {"name": str, "day": int, "grade": str}
            current_preset = self.current_set.get()
            schedule = self.preset_sets[current_preset].get('race_schedule', [])

            # Avoid duplicates by name
            if any(r['name'] == race_info['name'] for r in schedule):
                return

            schedule.append({"name": race_info["name"], "day": race_info["day"]})
            # Sort by day
            schedule.sort(key=lambda r: r["day"])
            self.preset_sets[current_preset]['race_schedule'] = schedule

            self._refresh_schedule_tree()
            self._safe_save_settings()

        def on_filters_changed(new_filters):
            self.race_schedule_filters = new_filters
            self._safe_save_settings()

        RaceScheduleDialog(
            self.parent,
            callback=on_race_selected,
            filters=self.race_schedule_filters,
            on_filters_changed=on_filters_changed
        )

    def _delete_selected_race(self):
        """Delete selected race from schedule"""
        selection = self.schedule_tree.selection()
        if not selection:
            return

        values = self.schedule_tree.item(selection[0], "values")
        if not values:
            return

        race_name = values[1]
        current_preset = self.current_set.get()
        schedule = self.preset_sets[current_preset].get('race_schedule', [])
        self.preset_sets[current_preset]['race_schedule'] = [
            r for r in schedule if r['name'] != race_name
        ]

        self._refresh_schedule_tree()
        self._safe_save_settings()

    def _reset_race_schedule(self):
        """Reset race schedule to defaults"""
        current_preset = self.current_set.get()
        self.preset_sets[current_preset]['race_schedule'] = [dict(r) for r in DEFAULT_RACE_SCHEDULE]
        self._refresh_schedule_tree()
        self._safe_save_settings()

    def _refresh_schedule_tree(self):
        """Refresh the schedule treeview from current preset data"""
        if not hasattr(self, 'schedule_tree'):
            return

        self.schedule_tree.delete(*self.schedule_tree.get_children())

        current_preset = self.current_set.get()
        schedule = self.preset_sets[current_preset].get('race_schedule', [])

        # Look up grade from race_list data
        race_grades = {}
        try:
            import json
            race_file = os.path.join("assets", "race_list.json")
            if os.path.exists(race_file):
                with open(race_file, "r", encoding="utf-8") as f:
                    all_races = json.load(f)
                for race in all_races:
                    race_grades[race.get("name", "")] = race.get("grade", "?")
        except Exception:
            pass

        for race in sorted(schedule, key=lambda r: r.get("day", 0)):
            grade = race_grades.get(race["name"], "?")
            self.schedule_tree.insert("", tk.END, values=(
                race.get("day", "?"),
                race["name"],
                grade
            ))

    def _update_style_display(self):
        """Update style combobox to show current selection"""
        if hasattr(self, 'style_combobox'):
            current_style = self.debut_style.get()
            display_name = get_style_display_name(current_style)
            self._style_display.set(display_name)

    def _on_style_combobox_change(self, event):
        """Handle style combobox selection change"""
        selected_display = self._style_display.get()
        # Convert display name back to style ID
        style_options = get_style_options()
        for style_id, display_name in style_options:
            if display_name == selected_display:
                self.debut_style.set(style_id)
                break

    def _update_logic_stat_caps(self):
        """Update the logic module and constants with current preset's stat caps.
        Skips update if nothing changed since last call (deduplication).
        """
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

            # Dedup: skip if nothing changed
            new_state = (uma_musume, tuple(support_cards), tuple(sorted(stat_caps.items())))
            if new_state == getattr(self, '_last_logic_state', None):
                return
            self._last_logic_state = new_state

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
        """Create individual support card selection box"""
        box_frame = tk.Frame(
            parent,
            relief=tk.RAISED,
            borderwidth=2,
            bg="#f0f0f0",
            cursor="hand2",
            height=70
        )

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
            justify=tk.CENTER
        )
        card_display.pack(padx=1, pady=(0, 2), fill=tk.BOTH, expand=True)

        # Dynamically update wraplength based on actual width (debounced)
        card_display.bind('<Configure>', lambda e, cd=card_display, idx=index: self._schedule_wraplength_update(cd, idx, e.width))

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

    def _schedule_wraplength_update(self, card_display, index, width):
        """Debounced wraplength update to avoid layout thrashing"""
        if index in self._wraplength_timers:
            card_display.after_cancel(self._wraplength_timers[index])
        self._wraplength_timers[index] = card_display.after(
            150, lambda: card_display.configure(wraplength=max(width - 6, 30))
        )

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

    # Card type sort order
    CARD_TYPE_ORDER = ['spd', 'sta', 'pow', 'gut', 'wit', 'frd']

    def _sort_support_cards(self):
        """Sort support cards by type so same types are grouped together"""
        values = [card.get() for card in self.support_cards]

        def sort_key(card_value):
            if not card_value or card_value == "None" or ":" not in card_value:
                return (len(self.CARD_TYPE_ORDER), card_value)
            card_type = card_value.split(":")[0].strip().lower()
            if card_type in self.CARD_TYPE_ORDER:
                return (self.CARD_TYPE_ORDER.index(card_type), card_value)
            return (len(self.CARD_TYPE_ORDER), card_value)

        sorted_values = sorted(values, key=sort_key)

        # Only update if order actually changed
        if sorted_values != values:
            for i, val in enumerate(sorted_values):
                self.support_cards[i].set(val)

    def _open_support_card_dialog(self, index):
        """Open support card selection dialog"""
        current_selection = self.support_cards[index].get()

        def on_card_selected(selected_card):
            self.support_cards[index].set(selected_card)
            self._sort_support_cards()

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

    def _edit_preset_name(self):
        """Open a small dialog to edit the current preset name"""
        current_set = self.current_set.get()
        current_name = self.preset_names[current_set].get()

        dialog = tk.Toplevel(self.parent)
        dialog.title(f"Edit Preset #{current_set} Name")
        dialog.resizable(False, False)
        dialog.transient(self.parent)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Preset name:").pack(anchor=tk.W)

        name_var = tk.StringVar(value=current_name)
        entry = ttk.Entry(frame, textvariable=name_var, width=30, font=("Arial", 10))
        entry.pack(fill=tk.X, pady=(5, 10))
        entry.select_range(0, tk.END)
        entry.focus_set()

        def save():
            new_name = name_var.get().strip()
            if new_name:
                self.preset_names[current_set].set(new_name)
                self._update_preset_display()
            dialog.destroy()

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="OK", command=save, width=8).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=8).pack(side=tk.RIGHT)

        entry.bind('<Return>', lambda e: save())
        entry.bind('<Escape>', lambda e: dialog.destroy())

        # Center on parent
        dialog.update_idletasks()
        px = self.parent.winfo_rootx()
        py = self.parent.winfo_rooty()
        pw = self.parent.winfo_width()
        ph = self.parent.winfo_height()
        dw = dialog.winfo_width()
        dh = dialog.winfo_height()
        dialog.geometry(f"+{px + (pw - dw) // 2}+{py + (ph - dh) // 2}")

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
        # Suppress auto-save and debut_style reset during switching
        self._switching_preset = True
        current = self.current_set.get()
        print(f"[DEBUG SWITCH] === Switching from preset {current} to {set_number} ===")

        try:
            # Save current values to current set (in memory)
            self.preset_sets[current]['uma_musume'].set(self.selected_uma_musume.get())
            for i, card in enumerate(self.support_cards):
                self.preset_sets[current]['support_cards'][i].set(card.get())
            self.preset_sets[current]['debut_style'] = self.debut_style.get()
            self._save_stop_conditions_to_preset(current)
            print(f"[DEBUG SWITCH] Saved to preset {current}: debut_style={self.preset_sets[current]['debut_style']}, stop_conditions={self.preset_sets[current]['stop_conditions']}")

            # Save to file BEFORE changing current_set (so get_settings syncs to old preset correctly)
            self.main_window.save_settings()
            print(f"[DEBUG SWITCH] Saved to file (current_set still={self.current_set.get()})")

            # Now switch current_set and reload new preset from file
            self.current_set.set(set_number)
            self._reload_preset_from_file(set_number)
            print(f"[DEBUG SWITCH] After reload from file: debut_style={self.preset_sets[set_number].get('debut_style', '???')}, stop_conditions={self.preset_sets[set_number].get('stop_conditions', '???')}")

            # Load working values from new preset
            selected_uma = self.preset_sets[set_number]['uma_musume'].get()
            self.selected_uma_musume.set(selected_uma)

            for i, card in enumerate(self.support_cards):
                card.set(self.preset_sets[set_number]['support_cards'][i].get())

            # Load debut style from new preset
            new_debut = self.preset_sets[set_number].get('debut_style', 'none')
            print(f"[DEBUG SWITCH] Setting debut_style to: {new_debut}")
            self.debut_style.set(new_debut)
            self._update_style_display()
            print(f"[DEBUG SWITCH] After set, debut_style.get()={self.debut_style.get()}")

            # Load stop conditions from new preset to strategy_tab
            self._load_stop_conditions_from_preset(set_number)

            # Update UI elements
            self._update_uma_display()
            self._update_preset_display()

            # Update stat cap entries to show new preset's values
            self._update_stat_cap_entries()

            # Refresh race schedule tree for new preset
            self._refresh_schedule_tree()

            # Update strategy checkboxes
            self.update_strategy_checkboxes(selected_uma)
        finally:
            self._switching_preset = False
            print(f"[DEBUG SWITCH] _switching_preset = False")

        # Save once with the new preset fully loaded
        self._safe_save_settings()
        print(f"[DEBUG SWITCH] === Switch complete ===")

    def _reload_preset_from_file(self, set_number):
        """Re-read bot_settings.json and update in-memory data for a specific preset"""
        try:
            import json
            if not os.path.exists('bot_settings.json'):
                return
            with open('bot_settings.json', 'r') as f:
                settings = json.load(f)

            event_settings = settings.get('event_choice', {})
            preset_sets_data = event_settings.get('preset_sets', {})
            preset_data = preset_sets_data.get(str(set_number), None)

            if not preset_data:
                print(f"[DEBUG RELOAD] No preset data found for set {set_number} in file")
                return

            print(f"[DEBUG RELOAD] File data for preset {set_number}: debut_style={preset_data.get('debut_style', 'MISSING')}, stop_conditions={preset_data.get('stop_conditions', 'MISSING')}")

            preset = self.preset_sets[set_number]

            # Update uma_musume
            preset['uma_musume'].set(preset_data.get('uma_musume', 'None'))

            # Update support cards
            preset_support_cards = preset_data.get('support_cards', ['None'] * 6)
            for i, card in enumerate(preset_support_cards[:6]):
                preset['support_cards'][i].set(card)

            # Update stat caps
            preset_stat_caps = preset_data.get('stat_caps', self.default_stat_caps)
            for stat_key in ['spd', 'sta', 'pwr', 'guts', 'wit']:
                cap_value = preset_stat_caps.get(stat_key, self.default_stat_caps.get(stat_key, 1200))
                preset['stat_caps'][stat_key].set(cap_value)

            # Update debut style
            preset['debut_style'] = preset_data.get('debut_style', 'none')

            # Update stop conditions
            preset['stop_conditions'] = dict(
                preset_data.get('stop_conditions', self.default_stop_conditions)
            )

            # Update race schedule
            preset['race_schedule'] = list(
                preset_data.get('race_schedule', [dict(r) for r in DEFAULT_RACE_SCHEDULE])
            )

            # Update preset name
            preset_names_data = event_settings.get('preset_names', {})
            name = preset_names_data.get(str(set_number), None)
            if name and set_number in self.preset_names:
                self.preset_names[set_number].set(name)

        except Exception as e:
            print(f"Warning: Could not reload preset from file: {e}")

    def _save_stop_conditions_to_preset(self, preset_num):
        """Save current stop conditions from strategy_tab to a preset"""
        strategy_tab = getattr(self.main_window, 'strategy_tab', None)
        if not strategy_tab:
            return
        sc = {}
        for key in self.default_stop_conditions:
            var = getattr(strategy_tab, key, None)
            if var is not None:
                sc[key] = var.get()
        self.preset_sets[preset_num]['stop_conditions'] = sc

    def _load_stop_conditions_from_preset(self, preset_num):
        """Load stop conditions from a preset to strategy_tab"""
        strategy_tab = getattr(self.main_window, 'strategy_tab', None)
        if not strategy_tab:
            print(f"[DEBUG LOAD_SC] No strategy_tab found!")
            return
        sc = self.preset_sets[preset_num].get('stop_conditions', self.default_stop_conditions)
        print(f"[DEBUG LOAD_SC] Loading stop conditions for preset {preset_num}: {sc}")
        for key, default_val in self.default_stop_conditions.items():
            var = getattr(strategy_tab, key, None)
            if var is not None:
                var.set(sc.get(key, default_val))

    def _read_stop_conditions_from_strategy_tab(self):
        """Read current stop conditions values from strategy_tab (without modifying anything)"""
        strategy_tab = getattr(self.main_window, 'strategy_tab', None)
        if not strategy_tab:
            return dict(self.default_stop_conditions)
        sc = {}
        for key, default_val in self.default_stop_conditions.items():
            var = getattr(strategy_tab, key, None)
            sc[key] = var.get() if var is not None else default_val
        return sc

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
            # Use update_filters_from_uma_data which has disable_auto_save protection
            # to avoid triggering save_settings() for each individual filter change
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

        # Reset debut style and race schedule when Uma Musume changes (but not during preset switch)
        switching = getattr(self, '_switching_preset', False)
        print(f"[DEBUG] on_uma_musume_change: uma={selected_uma}, _switching_preset={switching}")
        if not switching:
            self.debut_style.set('none')
            self._update_style_display()
            self._reset_race_schedule()

    def get_settings(self):
        """Get current tab settings"""
        current_preset = self.current_set.get()

        # Only sync working values to preset when NOT switching
        # During switching, preset data is managed by switch_preset_set directly
        if not getattr(self, '_switching_preset', False):
            self.preset_sets[current_preset]['debut_style'] = self.debut_style.get()
            self._save_stop_conditions_to_preset(current_preset)
            # race_schedule is already stored in preset_sets directly

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
            'debut_style': {
                'style': self.debut_style.get()
            },
            'race_schedule': list(self.preset_sets[current_preset].get(
                'race_schedule', [dict(r) for r in DEFAULT_RACE_SCHEDULE]
            )),
            'race_schedule_filters': dict(self.race_schedule_filters),
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
                'stat_caps': preset_stat_caps,
                'debut_style': preset.get('debut_style', 'none'),
                'stop_conditions': dict(preset.get('stop_conditions', self.default_stop_conditions)),
                'race_schedule': list(preset.get('race_schedule', [dict(r) for r in DEFAULT_RACE_SCHEDULE]))
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
            self.auto_event_map_var.trace('w', lambda *args: self._safe_save_settings())
            self.auto_first_choice_var.trace('w', lambda *args: self._safe_save_settings())

            # Load current selections
            if 'uma_musume' in settings:
                self.selected_uma_musume.set(settings['uma_musume'])
            if 'unknown_event_action' in settings:
                self.unknown_event_action.set(settings['unknown_event_action'])

            support_cards = settings.get('support_cards', ['None'] * 6)
            for i, card in enumerate(support_cards[:6]):
                self.support_cards[i].set(card)

            # Load debut style settings
            debut_style_settings = settings.get('debut_style', {})
            self.debut_style.set(debut_style_settings.get('style', 'none'))

            # Update style display if UI elements exist
            self._update_style_display()

            # Load race schedule dialog filters (global)
            if 'race_schedule_filters' in settings:
                self.race_schedule_filters = dict(settings['race_schedule_filters'])

            # Load preset names
            if 'preset_names' in settings:
                for set_num, name in settings['preset_names'].items():
                    set_num = int(set_num)
                    if set_num in self.preset_names:
                        self.preset_names[set_num].set(name)

            # Build fallback stop conditions from strategy_tab (already loaded from global settings)
            global_stop_conditions = self._read_stop_conditions_from_strategy_tab()

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
                        # Load debut style for this preset (fallback: global debut_style)
                        self.preset_sets[set_num]['debut_style'] = preset_data.get(
                            'debut_style', self.debut_style.get()
                        )
                        # Load stop conditions for this preset (fallback: global stop conditions)
                        self.preset_sets[set_num]['stop_conditions'] = dict(
                            preset_data.get('stop_conditions', global_stop_conditions)
                        )
                        # Load race schedule for this preset
                        self.preset_sets[set_num]['race_schedule'] = list(
                            preset_data.get('race_schedule', [dict(r) for r in DEFAULT_RACE_SCHEDULE])
                        )

            # Load current set
            if 'current_set' in settings:
                self.current_set.set(settings['current_set'])

            # Apply current preset's debut style
            current_preset = self.current_set.get()
            self.debut_style.set(self.preset_sets[current_preset].get('debut_style', 'none'))

            # Update preset display
            self._update_preset_display()

            # Update Uma Musume display
            self._update_uma_display()

            # Update style display
            self._update_style_display()

            # Update stat cap entries to show current preset's values
            self._update_stat_cap_entries()

            # Load current preset's stop conditions to strategy_tab
            self._load_stop_conditions_from_preset(current_preset)

            # Refresh race schedule tree
            self._refresh_schedule_tree()

            # Update strategy checkboxes
            self.update_strategy_checkboxes(self.selected_uma_musume.get())

        except Exception as e:
            print(f"Warning: Could not load event choice tab settings: {e}")