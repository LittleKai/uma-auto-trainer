import tkinter as tk
from tkinter import ttk, messagebox
import json
import os


class ToolTip:
    """Simple tooltip class for showing help text on hover"""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind('<Enter>', self.show_tooltip)
        self.widget.bind('<Leave>', self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window:
            return

        # Position tooltip to the right of the widget
        x = self.widget.winfo_rootx() + self.widget.winfo_width() + 5
        y = self.widget.winfo_rooty()

        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_attributes('-topmost', True)  # Keep tooltip on top
        tw.wm_geometry(f"+{x}+{y}")

        # Create tooltip content
        frame = tk.Frame(tw, bg="#ffffe0", relief=tk.SOLID, borderwidth=1)
        frame.pack()

        label = tk.Label(
            frame,
            text=self.text,
            bg="#ffffe0",
            fg="#333333",
            font=("Arial", 9),
            justify=tk.LEFT,
            wraplength=300,
            padx=8,
            pady=5
        )
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class DraggableStatButton(tk.Label):
    """A draggable button/label for stat priority ordering"""

    def __init__(self, master, stat_key, display_name, color, manager, **kw):
        super().__init__(master, **kw)
        self.stat_key = stat_key
        self.display_name = display_name
        self.color = color
        self.manager = manager
        self.dragging = False
        self.start_x = 0

        # Configure appearance
        self.configure(
            text=display_name,
            font=("Arial", 10, "bold"),
            bg=color,
            fg="white",
            padx=10,
            pady=8,
            relief=tk.RAISED,
            cursor="hand2"
        )

        # Bind events
        self.bind('<Button-1>', self.on_press)
        self.bind('<B1-Motion>', self.on_drag)
        self.bind('<ButtonRelease-1>', self.on_release)
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)

    def on_press(self, event):
        self.dragging = True
        self.start_x = event.x_root
        self.configure(relief=tk.SUNKEN)
        self.lift()  # Bring to front

    def on_drag(self, event):
        if not self.dragging:
            return
        # Calculate movement and check for swap
        self.manager.check_swap(self, event.x_root)

    def on_release(self, event):
        self.dragging = False
        self.configure(relief=tk.RAISED)
        self.manager.finalize_positions()

    def on_enter(self, event):
        if not self.dragging:
            self.configure(relief=tk.GROOVE)

    def on_leave(self, event):
        if not self.dragging:
            self.configure(relief=tk.RAISED)


class StatPriorityManager:
    """Manages the horizontal draggable stat buttons"""

    def __init__(self, parent_frame):
        self.parent = parent_frame
        self.buttons = []
        self.order = []  # Current order of stat keys

    def create_buttons(self, stat_order, stat_display):
        """Create draggable buttons for each stat"""
        # Clear existing buttons
        for btn in self.buttons:
            btn.destroy()
        self.buttons = []
        self.order = list(stat_order)

        # Create buttons
        for i, stat_key in enumerate(stat_order):
            display_name, color = stat_display.get(stat_key, (stat_key.upper(), "#666666"))
            btn = DraggableStatButton(
                self.parent,
                stat_key=stat_key,
                display_name=display_name,
                color=color,
                manager=self
            )
            btn.grid(row=0, column=i, padx=3, pady=5)
            self.buttons.append(btn)

        # Configure columns to be equal width
        for i in range(len(stat_order)):
            self.parent.columnconfigure(i, weight=1)

    def check_swap(self, dragged_btn, current_x):
        """Check if buttons should be swapped based on drag position"""
        dragged_idx = self.buttons.index(dragged_btn)

        for i, btn in enumerate(self.buttons):
            if btn == dragged_btn:
                continue

            # Get button position
            btn_x = btn.winfo_rootx()
            btn_width = btn.winfo_width()
            btn_center = btn_x + btn_width // 2

            # Check if dragged button crossed this button's center
            if dragged_idx < i and current_x > btn_center:
                # Moving right, swap with button on the right
                self._swap_buttons(dragged_idx, i)
                break
            elif dragged_idx > i and current_x < btn_center:
                # Moving left, swap with button on the left
                self._swap_buttons(dragged_idx, i)
                break

    def _swap_buttons(self, idx1, idx2):
        """Swap two buttons in the order"""
        # Swap in list
        self.buttons[idx1], self.buttons[idx2] = self.buttons[idx2], self.buttons[idx1]
        self.order[idx1], self.order[idx2] = self.order[idx2], self.order[idx1]

        # Re-grid buttons
        for i, btn in enumerate(self.buttons):
            btn.grid(row=0, column=i, padx=3, pady=5)

    def finalize_positions(self):
        """Ensure all buttons are in correct grid positions"""
        for i, btn in enumerate(self.buttons):
            btn.grid(row=0, column=i, padx=3, pady=5)

    def get_order(self):
        """Get current stat order"""
        return list(self.order)

    def set_order(self, new_order, stat_display):
        """Set a new order and recreate buttons"""
        self.create_buttons(new_order, stat_display)


class ConfigDialog:
    """Dialog for configuring config.json settings"""

    # Stat display names and colors
    STAT_DISPLAY = {
        'spd': ('SPEED', '#0066CC'),
        'sta': ('STAMINA', '#CC0066'),
        'pwr': ('POWER', '#CC6600'),
        'guts': ('GUTS', '#CC8800'),
        'wit': ('WISDOM', '#007733')
    }

    # Help texts for each setting
    HELP_TEXTS = {
        # Energy Settings
        "Minimum Energy %:": "Minimum energy percentage required before training. Bot will rest if energy is below this value.",
        "Critical Energy %:": "Critical energy threshold. Bot will prioritize rest when energy drops below this level.",

        # Other Settings
        "Stat Cap Threshold Day:": "Day after which stat caps are considered in scoring. Before this day, stat caps are ignored.",
        "Maximum Failure:": "Maximum number of consecutive failures allowed before bot stops or takes alternative action.",

        # Hint Score
        "Early Stage:": "Bonus score for hint events during early game stage.",
        "Late Stage:": "Bonus score for hint events during late game stage.",
        "Day Threshold:": "Day that separates early and late stages for hint scoring.",

        # NPC Score
        "Base Value:": "Base score value for NPC characters appearing in training.",

        # Support Score
        "Score Bonus:": "Bonus score added when support cards of matching type are present.",
        "Threshold Day:": "Day after which support card bonus is applied.",
        "Max Bonus Types:": "Maximum number of card types that can receive bonus.",

        # Unity Cup
        "Special Training Score:": "Score bonus for special training options in Unity Cup scenario.",
        "Spirit Explosion Score:": "Score bonus for spirit explosion events.",

        # WIT Training
        "Early Stage Bonus:": "Bonus score for WIT training during early game stages.",

        # Energy Restrictions
        "Medium Energy Shortage:": "Energy threshold for medium shortage penalty.",
        "Max Score Threshold:": "Maximum score threshold when energy is in shortage.",

        # Stage Thresholds
        "Pre-Debut End:": "Day when pre-debut stage ends (exclusive). Days 1 to this value are pre-debut.",
        "Early Stage End:": "Day when early stage ends. Early stage is from pre-debut end to this day.",
        "Mid Stage End:": "Day when mid stage ends. Late stage starts after this day.",

        # Friend Multiplier
        "WIT Multiplier:": "Score multiplier for friend cards when training WIT.",

        # Rainbow Multiplier
        "Pre-Debut:": "Score multiplier for rainbow training during pre-debut stage.",
    }

    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Bot Configuration")
        self.window.resizable(False, False)

        # Keep window on top and set as dialog
        self.window.attributes('-topmost', True)
        self.window.transient(parent)
        self.window.grab_set()  # Make it modal

        # Load current config
        self.config_path = "config.json"
        self.bot_settings_path = "bot_settings.json"
        self.config = self.load_config()
        self.bot_settings = self.load_bot_settings()

        # Initialize variables
        self.init_variables()

        # Setup UI
        self.setup_ui()

        # Load current values
        self.load_current_values()

        # Bind events
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.center_window()

    def load_config(self):
        """Load config from file"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}

    def load_bot_settings(self):
        """Load bot settings from file"""
        try:
            with open(self.bot_settings_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading bot settings: {e}")
            return {}

    def save_bot_settings(self):
        """Save bot settings to file"""
        try:
            with open(self.bot_settings_path, "w", encoding="utf-8") as f:
                json.dump(self.bot_settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving bot settings: {e}")
            return False

    def save_config(self):
        """Save config to file"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def init_variables(self):
        """Initialize dialog variables"""
        # Priority stat order - stored as list
        self.priority_stat_order = ["spd", "pwr", "sta", "wit", "guts"]

        # Energy settings
        self.minimum_energy_var = tk.IntVar()
        self.critical_energy_var = tk.IntVar()
        self.stat_cap_threshold_day_var = tk.IntVar()
        self.maximum_failure_var = tk.IntVar()

        # Scoring config - Hint score
        self.hint_early_var = tk.DoubleVar()
        self.hint_late_var = tk.DoubleVar()
        self.hint_threshold_var = tk.IntVar()

        # Scoring config - NPC score
        self.npc_base_var = tk.DoubleVar()

        # Scoring config - Support score
        self.support_base_var = tk.DoubleVar()

        # Scoring config - Friend multiplier
        self.friend_early_var = tk.DoubleVar()
        self.friend_late_var = tk.DoubleVar()
        self.friend_wit_var = tk.DoubleVar()

        # Scoring config - Rainbow multiplier
        self.rainbow_pre_debut_var = tk.DoubleVar()
        self.rainbow_early_var = tk.DoubleVar()
        self.rainbow_mid_var = tk.DoubleVar()
        self.rainbow_late_var = tk.DoubleVar()

        # Scoring config - Stage thresholds
        self.pre_debut_threshold_var = tk.IntVar()
        self.early_threshold_var = tk.IntVar()
        self.mid_threshold_var = tk.IntVar()

        # Scoring config - Support card bonus
        self.support_card_bonus_var = tk.DoubleVar()
        self.support_card_threshold_var = tk.IntVar()
        self.support_card_max_bonus_var = tk.IntVar()

        # Scoring config - Unity Cup
        self.special_training_score_var = tk.DoubleVar()
        self.spirit_explosion_score_var = tk.DoubleVar()

        # Scoring config - WIT training
        self.wit_early_bonus_var = tk.DoubleVar()

        # Scoring config - Energy restrictions
        self.medium_energy_shortage_var = tk.IntVar()
        self.medium_energy_max_score_var = tk.DoubleVar()

        # Scoring config - Stat Cap Penalty
        self.cap_penalty_enabled_var = tk.BooleanVar()
        self.cap_penalty_max_var = tk.IntVar()
        self.cap_penalty_start_var = tk.IntVar()
        self.cap_penalty_gap_var = tk.IntVar()

        # Event Choice Mode settings (from bot_settings.json)
        self.auto_event_map_var = tk.BooleanVar()
        self.auto_first_choice_var = tk.BooleanVar()
        self.unknown_event_action_var = tk.StringVar()

    def setup_ui(self):
        """Setup the user interface"""
        # Create notebook for tabbed interface
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab 1: Basic Settings
        basic_frame = ttk.Frame(notebook, padding="10")
        notebook.add(basic_frame, text="Basic Settings")
        self.create_basic_settings(basic_frame)

        # Tab 2: Scoring Config
        scoring_frame = ttk.Frame(notebook, padding="10")
        notebook.add(scoring_frame, text="Scoring Config")
        self.create_scoring_settings(scoring_frame)

        # Tab 3: Stage & Multipliers
        stage_frame = ttk.Frame(notebook, padding="10")
        notebook.add(stage_frame, text="Stage & Multipliers")
        self.create_stage_settings(stage_frame)

        # Buttons at bottom
        self.create_buttons()

    def create_basic_settings(self, parent):
        """Create basic settings section"""
        # Priority Stat Order with horizontal drag-drop buttons
        priority_frame = ttk.LabelFrame(parent, text="Priority Stat Order (Drag to reorder, left = highest)", padding="8")
        priority_frame.pack(fill=tk.X, pady=(0, 10))

        # Instructions
        ttk.Label(
            priority_frame,
            text="Drag buttons left/right to change priority:",
            font=("Arial", 9),
            foreground="gray"
        ).pack(anchor=tk.W, pady=(0, 5))

        # Priority indicator
        indicator_frame = ttk.Frame(priority_frame)
        indicator_frame.pack(fill=tk.X, pady=(0, 2))
        ttk.Label(indicator_frame, text="High", font=("Arial", 8), foreground="green").pack(side=tk.LEFT)
        ttk.Label(indicator_frame, text="Low", font=("Arial", 8), foreground="red").pack(side=tk.RIGHT)

        # Container for draggable buttons
        self.priority_buttons_frame = ttk.Frame(priority_frame)
        self.priority_buttons_frame.pack(fill=tk.X, pady=(5, 5))

        # Create stat priority manager
        self.stat_priority_manager = StatPriorityManager(self.priority_buttons_frame)

        # Energy Settings
        energy_frame = ttk.LabelFrame(parent, text="Energy Settings", padding="8")
        energy_frame.pack(fill=tk.X, pady=(0, 10))

        self.create_labeled_entry(energy_frame, "Minimum Energy %:", self.minimum_energy_var,
                                  "Minimum energy percentage required before training. Bot will rest if energy is below this value.")
        self.create_labeled_entry(energy_frame, "Critical Energy %:", self.critical_energy_var,
                                  "Critical energy threshold. Bot will prioritize rest when energy drops below this level.")

        # Other Settings
        other_frame = ttk.LabelFrame(parent, text="Other Settings", padding="8")
        other_frame.pack(fill=tk.X, pady=(0, 10))

        self.create_labeled_entry(other_frame, "Maximum Failure:", self.maximum_failure_var,
                                  "Maximum number of consecutive failures allowed before bot stops or takes alternative action.")

        # Event Choice Mode (from bot_settings.json)
        event_mode_frame = ttk.LabelFrame(parent, text="Event Choice Mode", padding="8")
        event_mode_frame.pack(fill=tk.X, pady=(0, 10))

        # Checkboxes row
        checkbox_row = ttk.Frame(event_mode_frame)
        checkbox_row.pack(fill=tk.X, pady=(0, 5))

        ttk.Checkbutton(
            checkbox_row,
            text="Auto Event Map",
            variable=self.auto_event_map_var,
            command=self._on_event_mode_change
        ).pack(side=tk.LEFT)

        help_auto_event = tk.Label(checkbox_row, text="?", font=("Arial", 9, "bold"),
                                   fg="white", bg="#888888", width=2, cursor="question_arrow")
        help_auto_event.pack(side=tk.LEFT, padx=(2, 15))
        ToolTip(help_auto_event, "Use event map database to automatically select best choice based on conditions.")

        ttk.Checkbutton(
            checkbox_row,
            text="Auto First Choice",
            variable=self.auto_first_choice_var,
            command=self._on_event_mode_change
        ).pack(side=tk.LEFT)

        help_auto_first = tk.Label(checkbox_row, text="?", font=("Arial", 9, "bold"),
                                   fg="white", bg="#888888", width=2, cursor="question_arrow")
        help_auto_first.pack(side=tk.LEFT, padx=(2, 0))
        ToolTip(help_auto_first, "Always automatically select the first choice for all events.")

        # Unknown Event Action dropdown
        action_row = ttk.Frame(event_mode_frame)
        action_row.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(action_row, text="Unknown Event Action:").pack(side=tk.LEFT, padx=(0, 5))

        self.unknown_event_dropdown = ttk.Combobox(
            action_row,
            textvariable=self.unknown_event_action_var,
            values=["Auto select first choice", "Wait for user selection", "Search in other special events"],
            state="readonly",
            width=30
        )
        self.unknown_event_dropdown.pack(side=tk.LEFT, padx=(0, 5))

        help_unknown = tk.Label(action_row, text="?", font=("Arial", 9, "bold"),
                                fg="white", bg="#888888", width=2, cursor="question_arrow")
        help_unknown.pack(side=tk.LEFT)
        ToolTip(help_unknown, "Action to take when an event is not found in the database.\n• Auto select first choice: Pick the first option\n• Wait for user selection: Pause and wait\n• Search in other special events: Try to find similar event")

    def get_priority_stat_order(self):
        """Get current priority stat order from buttons"""
        return self.stat_priority_manager.get_order()

    def _on_event_mode_change(self):
        """Handle event mode checkbox change to ensure at least one is selected"""
        if not self.auto_event_map_var.get() and not self.auto_first_choice_var.get():
            self.auto_first_choice_var.set(True)

        # Update dropdown state
        if self.auto_first_choice_var.get():
            self.unknown_event_dropdown.configure(state="disabled")
        else:
            self.unknown_event_dropdown.configure(state="readonly")

    def create_scoring_settings(self, parent):
        """Create scoring config section"""
        # Create a canvas with scrollbar for scrolling
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Hint Score
        hint_frame = ttk.LabelFrame(scrollable_frame, text="Hint Score", padding="8")
        hint_frame.pack(fill=tk.X, pady=(0, 10))

        self.create_labeled_entry(hint_frame, "Early Stage:", self.hint_early_var,
                                  "Bonus score for hint events during early game stage.")
        self.create_labeled_entry(hint_frame, "Late Stage:", self.hint_late_var,
                                  "Bonus score for hint events during late game stage.")
        self.create_labeled_entry(hint_frame, "Day Threshold:", self.hint_threshold_var,
                                  "Day that separates early and late stages for hint scoring.")

        # NPC Score
        npc_frame = ttk.LabelFrame(scrollable_frame, text="NPC Score", padding="8")
        npc_frame.pack(fill=tk.X, pady=(0, 10))

        self.create_labeled_entry(npc_frame, "Base Value:", self.npc_base_var,
                                  "Base score value for NPC characters appearing in training.")

        # Support Score
        support_frame = ttk.LabelFrame(scrollable_frame, text="Support Score", padding="8")
        support_frame.pack(fill=tk.X, pady=(0, 10))

        self.create_labeled_entry(support_frame, "Base Value:", self.support_base_var,
                                  "Base score value for each support card in training.")

        # Support Card Bonus
        card_bonus_frame = ttk.LabelFrame(scrollable_frame, text="Support Card Bonus", padding="8")
        card_bonus_frame.pack(fill=tk.X, pady=(0, 10))

        self.create_labeled_entry(card_bonus_frame, "Score Bonus:", self.support_card_bonus_var,
                                  "Bonus score when support cards of matching type are present in training.")
        self.create_labeled_entry(card_bonus_frame, "Threshold Day:", self.support_card_threshold_var,
                                  "Day after which support card bonus is applied.")
        self.create_labeled_entry(card_bonus_frame, "Max Bonus Types:", self.support_card_max_bonus_var,
                                  "Maximum number of card types that can receive bonus.")

        # Unity Cup
        unity_frame = ttk.LabelFrame(scrollable_frame, text="Unity Cup", padding="8")
        unity_frame.pack(fill=tk.X, pady=(0, 10))

        self.create_labeled_entry(unity_frame, "Special Training Score:", self.special_training_score_var,
                                  "Score bonus for special training options in Unity Cup scenario.")
        self.create_labeled_entry(unity_frame, "Spirit Explosion Score:", self.spirit_explosion_score_var,
                                  "Score bonus for spirit explosion events in Unity Cup.")

        # WIT Training
        wit_frame = ttk.LabelFrame(scrollable_frame, text="WIT Training", padding="8")
        wit_frame.pack(fill=tk.X, pady=(0, 10))

        self.create_labeled_entry(wit_frame, "Early Stage Bonus:", self.wit_early_bonus_var,
                                  "Bonus score for WIT training during early game stages.")

        # Energy Restrictions
        energy_rest_frame = ttk.LabelFrame(scrollable_frame, text="Energy Restrictions", padding="8")
        energy_rest_frame.pack(fill=tk.X, pady=(0, 10))

        self.create_labeled_entry(energy_rest_frame, "Medium Energy Shortage:", self.medium_energy_shortage_var,
                                  "Energy threshold for medium shortage penalty.")
        self.create_labeled_entry(energy_rest_frame, "Max Score Threshold:", self.medium_energy_max_score_var,
                                  "Maximum score threshold when energy is in medium shortage.")

        # Stat Cap Penalty
        cap_penalty_frame = ttk.LabelFrame(scrollable_frame, text="Stat Cap Penalty", padding="8")
        cap_penalty_frame.pack(fill=tk.X, pady=(0, 10))

        # Enable checkbox
        ttk.Checkbutton(cap_penalty_frame, text="Enable Stat Cap Penalty",
                        variable=self.cap_penalty_enabled_var).pack(anchor=tk.W, pady=(0, 5))

        # Threshold Day
        self.create_labeled_entry(cap_penalty_frame, "Threshold Day:", self.stat_cap_threshold_day_var,
                                  "Day after which stat cap penalty is applied. Before this day, stat caps are ignored.")

        # Max Penalty
        self.create_labeled_entry(cap_penalty_frame, "Max Penalty %:", self.cap_penalty_max_var,
                                  "Maximum penalty percentage for stats approaching target (0-100). "
                                  "Training score will be reduced by up to this amount.")

        # Start Penalty % and Start Penalty Gap on same row
        start_row = ttk.Frame(cap_penalty_frame)
        start_row.pack(fill=tk.X, pady=2)

        # Start Penalty %
        ttk.Label(start_row, text="Start Penalty %:", width=15).pack(side=tk.LEFT)
        ttk.Entry(start_row, textvariable=self.cap_penalty_start_var, width=6).pack(side=tk.LEFT, padx=(5, 0))
        help_start = tk.Label(start_row, text="?", font=("Arial", 9, "bold"),
                              fg="white", bg="#888888", width=2, cursor="question_arrow")
        help_start.pack(side=tk.LEFT, padx=(5, 15))
        ToolTip(help_start, "Penalty starts when stat reaches this % of effective cap.\nE.g., 80 = penalty starts at 80% of cap.")

        # Start Penalty Gap
        ttk.Label(start_row, text="Gap:", width=4).pack(side=tk.LEFT)
        ttk.Entry(start_row, textvariable=self.cap_penalty_gap_var, width=6).pack(side=tk.LEFT, padx=(5, 0))
        help_gap = tk.Label(start_row, text="?", font=("Arial", 9, "bold"),
                            fg="white", bg="#888888", width=2, cursor="question_arrow")
        help_gap.pack(side=tk.LEFT, padx=(5, 0))
        ToolTip(help_gap, "Penalty also starts when stat is within this many points of cap.\nHybrid trigger: uses whichever condition is met first.")

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_stage_settings(self, parent):
        """Create stage and multiplier settings"""
        # Stage Thresholds
        stage_frame = ttk.LabelFrame(parent, text="Stage Thresholds (Day)", padding="8")
        stage_frame.pack(fill=tk.X, pady=(0, 10))

        self.create_labeled_entry(stage_frame, "Pre-Debut End:", self.pre_debut_threshold_var,
                                  "Day when pre-debut stage ends. Days 1 to this value are pre-debut.")
        self.create_labeled_entry(stage_frame, "Early Stage End:", self.early_threshold_var,
                                  "Day when early stage ends. Early stage is from pre-debut end to this day.")
        self.create_labeled_entry(stage_frame, "Mid Stage End:", self.mid_threshold_var,
                                  "Day when mid stage ends. Late stage starts after this day.")

        # Friend Multiplier
        friend_frame = ttk.LabelFrame(parent, text="Friend Multiplier", padding="8")
        friend_frame.pack(fill=tk.X, pady=(0, 10))

        self.create_labeled_entry(friend_frame, "Early Stage:", self.friend_early_var,
                                  "Score multiplier for friend cards during early stage.")
        self.create_labeled_entry(friend_frame, "Late Stage:", self.friend_late_var,
                                  "Score multiplier for friend cards during late stage.")
        self.create_labeled_entry(friend_frame, "WIT Multiplier:", self.friend_wit_var,
                                  "Score multiplier for friend cards when training WIT.")

        # Rainbow Multiplier
        rainbow_frame = ttk.LabelFrame(parent, text="Rainbow Multiplier", padding="8")
        rainbow_frame.pack(fill=tk.X, pady=(0, 10))

        self.create_labeled_entry(rainbow_frame, "Pre-Debut:", self.rainbow_pre_debut_var,
                                  "Score multiplier for rainbow training during pre-debut stage.")
        self.create_labeled_entry(rainbow_frame, "Early Stage:", self.rainbow_early_var,
                                  "Score multiplier for rainbow training during early stage.")
        self.create_labeled_entry(rainbow_frame, "Mid Stage:", self.rainbow_mid_var,
                                  "Score multiplier for rainbow training during mid stage.")
        self.create_labeled_entry(rainbow_frame, "Late Stage:", self.rainbow_late_var,
                                  "Score multiplier for rainbow training during late stage.")

    def create_labeled_entry(self, parent, label_text, variable, help_text=None):
        """Create a labeled entry widget with optional help tooltip"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=2)

        ttk.Label(frame, text=label_text, width=22).pack(side=tk.LEFT)
        entry = ttk.Entry(frame, textvariable=variable, width=10)
        entry.pack(side=tk.LEFT, padx=(5, 0))

        # Add help icon with tooltip
        tooltip_text = help_text or self.HELP_TEXTS.get(label_text)
        if tooltip_text:
            help_label = tk.Label(
                frame,
                text="?",
                font=("Arial", 9, "bold"),
                fg="white",
                bg="#888888",
                width=2,
                cursor="question_arrow"
            )
            help_label.pack(side=tk.LEFT, padx=(5, 0))
            ToolTip(help_label, tooltip_text)

    def create_buttons(self):
        """Create button section"""
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Reset to defaults button
        reset_btn = ttk.Button(button_frame, text="Reset to Defaults", command=self.reset_to_defaults)
        reset_btn.pack(side=tk.LEFT)

        # Cancel and Save buttons
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.on_closing)
        cancel_btn.pack(side=tk.RIGHT, padx=(5, 0))

        save_btn = ttk.Button(button_frame, text="Save", command=self.save_settings)
        save_btn.pack(side=tk.RIGHT)

    def load_current_values(self):
        """Load current values from config"""
        # Priority stat - create draggable buttons
        priority_stat = self.config.get("priority_stat", ["spd", "pwr", "sta", "wit", "guts"])
        self.stat_priority_manager.create_buttons(priority_stat, self.STAT_DISPLAY)

        # Energy settings
        self.minimum_energy_var.set(self.config.get("minimum_energy_percentage", 43))
        self.critical_energy_var.set(self.config.get("critical_energy_percentage", 20))

        # Other settings
        self.stat_cap_threshold_day_var.set(self.config.get("stat_cap_threshold_day", 30))
        self.maximum_failure_var.set(self.config.get("maximum_failure", 15))

        # Scoring config
        scoring = self.config.get("scoring_config", {})

        # Hint score
        hint = scoring.get("hint_score", {})
        self.hint_early_var.set(hint.get("early_stage", 1.0))
        self.hint_late_var.set(hint.get("late_stage", 0.75))
        self.hint_threshold_var.set(hint.get("day_threshold", 24))

        # NPC score
        npc = scoring.get("npc_score", {})
        self.npc_base_var.set(npc.get("base_value", 0.4))

        # Support score
        support = scoring.get("support_score", {})
        self.support_base_var.set(support.get("base_value", 1.0))

        # Friend multiplier
        friend = support.get("friend_multiplier", {})
        self.friend_early_var.set(friend.get("early_stage", 1.2))
        self.friend_late_var.set(friend.get("late_stage", 1.1))
        self.friend_wit_var.set(friend.get("friend_wit_multiplier", 0.5))

        # Rainbow multiplier
        rainbow = support.get("rainbow_multiplier", {})
        self.rainbow_pre_debut_var.set(rainbow.get("pre_debut", 1.0))
        self.rainbow_early_var.set(rainbow.get("early_stage", 1.0))
        self.rainbow_mid_var.set(rainbow.get("mid_stage", 2.25))
        self.rainbow_late_var.set(rainbow.get("late_stage", 2.25))

        # Stage thresholds
        stages = scoring.get("stage_thresholds", {})
        self.pre_debut_threshold_var.set(stages.get("pre_debut", 16))
        self.early_threshold_var.set(stages.get("early_stage", 24))
        self.mid_threshold_var.set(stages.get("mid_stage", 48))

        # Support card bonus
        card_bonus = scoring.get("support_card_bonus", {})
        self.support_card_bonus_var.set(card_bonus.get("score_bonus", 0.5))
        self.support_card_threshold_var.set(card_bonus.get("threshold_day", 24))
        self.support_card_max_bonus_var.set(card_bonus.get("max_bonus_types", 2))

        # Unity cup
        unity = scoring.get("unity_cup", {})
        self.special_training_score_var.set(unity.get("special_training_score", 0.15))
        self.spirit_explosion_score_var.set(unity.get("spirit_explosion_score", 2.25))

        # WIT training
        wit = scoring.get("wit_training", {})
        self.wit_early_bonus_var.set(wit.get("early_stage_bonus", 0.1))

        # Energy restrictions
        energy = scoring.get("energy_restrictions", {})
        self.medium_energy_shortage_var.set(energy.get("medium_energy_shortage", 45))
        self.medium_energy_max_score_var.set(energy.get("medium_energy_max_score_threshold", 2.9))

        # Stat cap penalty
        cap_penalty = scoring.get("stat_cap_penalty", {})
        self.cap_penalty_enabled_var.set(cap_penalty.get("enabled", True))
        self.cap_penalty_max_var.set(cap_penalty.get("max_penalty_percent", 40))
        self.cap_penalty_start_var.set(cap_penalty.get("start_penalty_percent", 80))
        self.cap_penalty_gap_var.set(cap_penalty.get("start_penalty_gap", 200))

        # Event Choice Mode (from bot_settings.json)
        event_choice = self.bot_settings.get("event_choice", {})
        self.auto_event_map_var.set(event_choice.get("auto_event_map", False))
        self.auto_first_choice_var.set(event_choice.get("auto_first_choice", True))
        self.unknown_event_action_var.set(event_choice.get("unknown_event_action", "Auto select first choice"))

        # Update dropdown state based on mode
        self._on_event_mode_change()

    def save_settings(self):
        """Save settings to config file"""
        try:
            # Update config with new values
            # Priority stat from listbox
            self.config["priority_stat"] = self.get_priority_stat_order()

            # Energy settings
            self.config["minimum_energy_percentage"] = self.minimum_energy_var.get()
            self.config["critical_energy_percentage"] = self.critical_energy_var.get()

            # Other settings
            self.config["stat_cap_threshold_day"] = self.stat_cap_threshold_day_var.get()
            self.config["maximum_failure"] = self.maximum_failure_var.get()

            # Scoring config
            if "scoring_config" not in self.config:
                self.config["scoring_config"] = {}

            scoring = self.config["scoring_config"]

            # Hint score
            scoring["hint_score"] = {
                "early_stage": self.hint_early_var.get(),
                "late_stage": self.hint_late_var.get(),
                "day_threshold": self.hint_threshold_var.get()
            }

            # NPC score
            scoring["npc_score"] = {
                "base_value": self.npc_base_var.get()
            }

            # Support score
            if "support_score" not in scoring:
                scoring["support_score"] = {}

            scoring["support_score"]["base_value"] = self.support_base_var.get()
            scoring["support_score"]["friend_multiplier"] = {
                "early_stage": self.friend_early_var.get(),
                "late_stage": self.friend_late_var.get(),
                "friend_wit_multiplier": self.friend_wit_var.get()
            }
            scoring["support_score"]["rainbow_multiplier"] = {
                "pre_debut": self.rainbow_pre_debut_var.get(),
                "early_stage": self.rainbow_early_var.get(),
                "mid_stage": self.rainbow_mid_var.get(),
                "late_stage": self.rainbow_late_var.get()
            }

            # Stage thresholds
            scoring["stage_thresholds"] = {
                "pre_debut": self.pre_debut_threshold_var.get(),
                "early_stage": self.early_threshold_var.get(),
                "mid_stage": self.mid_threshold_var.get()
            }

            # Support card bonus
            scoring["support_card_bonus"] = {
                "score_bonus": self.support_card_bonus_var.get(),
                "threshold_day": self.support_card_threshold_var.get(),
                "max_bonus_types": self.support_card_max_bonus_var.get()
            }

            # Unity cup
            scoring["unity_cup"] = {
                "special_training_score": self.special_training_score_var.get(),
                "spirit_explosion_score": self.spirit_explosion_score_var.get()
            }

            # WIT training - preserve existing medium_energy_score_requirement
            wit_config = scoring.get("wit_training", {})
            wit_config["early_stage_bonus"] = self.wit_early_bonus_var.get()
            scoring["wit_training"] = wit_config

            # Energy restrictions
            scoring["energy_restrictions"] = {
                "medium_energy_shortage": self.medium_energy_shortage_var.get(),
                "medium_energy_max_score_threshold": self.medium_energy_max_score_var.get()
            }

            # Stat cap penalty - preserve day_cap_adjustments
            existing_cap_penalty = scoring.get("stat_cap_penalty", {})
            day_adjustments = existing_cap_penalty.get("day_cap_adjustments", {
                "day_75": 30,
                "day_74": 45,
                "day_73_and_below": 60
            })
            scoring["stat_cap_penalty"] = {
                "enabled": self.cap_penalty_enabled_var.get(),
                "max_penalty_percent": self.cap_penalty_max_var.get(),
                "start_penalty_percent": self.cap_penalty_start_var.get(),
                "start_penalty_gap": self.cap_penalty_gap_var.get(),
                "day_cap_adjustments": day_adjustments
            }

            # Save Event Choice Mode to bot_settings
            if "event_choice" not in self.bot_settings:
                self.bot_settings["event_choice"] = {}

            self.bot_settings["event_choice"]["auto_event_map"] = self.auto_event_map_var.get()
            self.bot_settings["event_choice"]["auto_first_choice"] = self.auto_first_choice_var.get()
            self.bot_settings["event_choice"]["unknown_event_action"] = self.unknown_event_action_var.get()

            # Save both config and bot_settings
            config_saved = self.save_config()
            bot_settings_saved = self.save_bot_settings()

            if config_saved and bot_settings_saved:
                # Reload config in logic module (hot reload - no restart needed)
                try:
                    from core.logic import reload_config
                    reload_config()
                except Exception as e:
                    print(f"Warning: Could not reload config: {e}")

                messagebox.showinfo("Success", "Configuration saved and applied!")
                self.window.destroy()
            else:
                messagebox.showerror("Error", "Failed to save configuration.")

        except Exception as e:
            messagebox.showerror("Error", f"Error saving configuration: {e}")

    def reset_to_defaults(self):
        """Reset all values to defaults"""
        if messagebox.askyesno("Confirm Reset", "Reset all configuration to default values?"):
            # Reset priority stat buttons
            default_order = ["spd", "pwr", "sta", "wit", "guts"]
            self.stat_priority_manager.set_order(default_order, self.STAT_DISPLAY)

            # Energy settings
            self.minimum_energy_var.set(43)
            self.critical_energy_var.set(20)
            self.stat_cap_threshold_day_var.set(30)
            self.maximum_failure_var.set(15)

            # Scoring defaults
            self.hint_early_var.set(1.0)
            self.hint_late_var.set(0.75)
            self.hint_threshold_var.set(24)
            self.npc_base_var.set(0.4)
            self.support_base_var.set(1.0)
            self.friend_early_var.set(1.2)
            self.friend_late_var.set(1.1)
            self.friend_wit_var.set(0.5)
            self.rainbow_pre_debut_var.set(1.0)
            self.rainbow_early_var.set(1.0)
            self.rainbow_mid_var.set(2.25)
            self.rainbow_late_var.set(2.25)
            self.pre_debut_threshold_var.set(16)
            self.early_threshold_var.set(24)
            self.mid_threshold_var.set(48)
            self.support_card_bonus_var.set(0.5)
            self.support_card_threshold_var.set(24)
            self.support_card_max_bonus_var.set(2)
            self.special_training_score_var.set(0.15)
            self.spirit_explosion_score_var.set(2.25)
            self.wit_early_bonus_var.set(0.1)
            self.medium_energy_shortage_var.set(45)
            self.medium_energy_max_score_var.set(2.9)

            # Stat cap penalty defaults
            self.cap_penalty_enabled_var.set(True)
            self.cap_penalty_max_var.set(40)
            self.cap_penalty_start_var.set(80)
            self.cap_penalty_gap_var.set(200)

            # Event Choice Mode defaults
            self.auto_event_map_var.set(False)
            self.auto_first_choice_var.set(True)
            self.unknown_event_action_var.set("Auto select first choice")
            self._on_event_mode_change()

    def center_window(self):
        """Center the window on screen with auto-fit height"""
        # Let window calculate its required size first
        self.window.update_idletasks()

        # Get the required size from content
        width = max(500, self.window.winfo_reqwidth())
        content_height = self.window.winfo_reqheight()

        # Cap maximum height to screen height - 100
        screen_height = self.window.winfo_screenheight()
        max_height = screen_height - 100
        height = min(content_height, max_height)

        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        x = parent_x + (parent_width // 2) - (width // 2)
        y = parent_y + (parent_height // 2) - (height // 2)

        # Ensure window is not off-screen
        if y < 50:
            y = 50

        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def on_closing(self):
        """Handle window closing"""
        self.window.destroy()
