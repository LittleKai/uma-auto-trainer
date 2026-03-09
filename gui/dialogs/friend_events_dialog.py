import tkinter as tk
from tkinter import ttk, messagebox
import copy


class ToolTip:
    """Simple tooltip shown on hover"""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        widget.bind('<Enter>', self.show)
        widget.bind('<Leave>', self.hide)

    def show(self, event=None):
        if self.tooltip_window:
            return
        x = self.widget.winfo_rootx() + self.widget.winfo_width() + 5
        y = self.widget.winfo_rooty()
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_attributes('-topmost', True)
        tw.wm_geometry(f"+{x}+{y}")
        frame = tk.Frame(tw, bg="#ffffe0", relief=tk.SOLID, borderwidth=1)
        frame.pack()
        tk.Label(frame, text=self.text, bg="#ffffe0", fg="#333333",
                 font=("Arial", 9), justify=tk.LEFT, wraplength=300,
                 padx=8, pady=5).pack()

    def hide(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

DEFAULT_DATE_MIN_DAYS = [25, 32, 44, 58, 70]
DEFAULT_FRIEND_EVENTS_CONFIG = {
    'skip_score': 4.0,
    'dates': [
        {'min_day': 25},
        {'min_day': 32},
        {'min_day': 44},
        {'min_day': 58},
        {'min_day': 70},
    ]
}


class FriendEventsWindow:
    """Window for configuring Friend Events automation settings (min day per date)"""

    def __init__(self, strategy_tab):
        self.strategy_tab = strategy_tab
        self.main_window = strategy_tab.main_window
        self.window = tk.Toplevel(self.main_window.root)
        self.window.title("Friend Events Configuration")
        self.window.resizable(False, False)

        self.window.attributes('-topmost', True)
        self.window.transient(self.main_window.root)
        self.window.grab_set()

        raw = getattr(strategy_tab, 'friend_events_config', copy.deepcopy(DEFAULT_FRIEND_EVENTS_CONFIG))
        # Normalise old list format to dict format
        if isinstance(raw, list):
            raw = {'skip_score': 4.0, 'dates': raw}
        self.config = copy.deepcopy(raw)

        self.skip_score_var = tk.StringVar()
        self.date_vars = []

        self.setup_ui()
        self.load_values()

        self.window.protocol("WM_DELETE_WINDOW", self.window.destroy)
        self.center_window()

    def _help_btn(self, parent, text):
        """Create a small (?) label with tooltip"""
        btn = tk.Label(parent, text="(?)", fg="#0066cc", cursor="hand2", font=("Arial", 8))
        ToolTip(btn, text)
        return btn

    def setup_ui(self):
        main_frame = ttk.Frame(self.window, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Friend Events Configuration",
                  font=("Arial", 12, "bold")).pack(pady=(0, 5))

        ttk.Label(
            main_frame,
            text="Set the minimum day for each friend event date.\n"
                 "Energy, mood and heal attributes are read from the support card JSON file.",
            font=("Arial", 9),
            justify=tk.CENTER,
            foreground="blue"
        ).pack(pady=(0, 10))

        # Skip score row
        skip_frame = ttk.Frame(main_frame)
        skip_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(skip_frame, text="Skip if Train Score ≥", font=("Arial", 9)).pack(side=tk.LEFT, padx=(0, 4))
        self._help_btn(skip_frame,
            "If the best available training score is ≥ this value,\n"
            "skip the friend event date and proceed with training.\n\n"
            "Example: skip_score = 4.0\n"
            "• Train score = 4.2 → skip date, go train\n"
            "• Train score = 3.5 → check and possibly click date"
        ).pack(side=tk.LEFT, padx=(0, 8))
        score_values = [str(round(v * 0.5, 1)) for v in range(7, 17)]  # 3.5 to 8.0
        score_cb = ttk.Combobox(skip_frame, textvariable=self.skip_score_var,
                                values=score_values, state='readonly', width=6)
        score_cb.pack(side=tk.LEFT)
        ttk.Label(skip_frame, text="  Energy check:", font=("Arial", 8),
                  foreground="#555555").pack(side=tk.LEFT, padx=(12, 4))
        self._help_btn(skip_frame,
            "The bot only clicks a date event if the effective energy\n"
            "shortage is large enough to justify it.\n\n"
            "Formula:\n"
            "  effective_shortage = (100 - energy%) - (4 × wit_cards)\n"
            "  Click date if: effective_shortage ≥ date energy recovery\n\n"
            "Example (energy 60%, date recovers 35%):\n"
            "  • 0 wit cards: 40 - 0 = 40 ≥ 35 → click date\n"
            "  • 3 wit cards: 40 - 12 = 28 < 35 → cancel\n\n"
            "Reason: wit support cards recover energy during WIT training,\n"
            "so more wit cards means less need for a date event."
        ).pack(side=tk.LEFT)

        # Dates table
        table_frame = ttk.LabelFrame(main_frame, text="Dates (5 total)", padding="10")
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Header
        ttk.Label(table_frame, text="Date", font=("Arial", 9, "bold"),
                  width=6, anchor=tk.CENTER).grid(row=0, column=0, padx=10, pady=(0, 6))

        min_day_hdr = ttk.Frame(table_frame)
        min_day_hdr.grid(row=0, column=1, padx=10, pady=(0, 6))
        ttk.Label(min_day_hdr, text="Min Day", font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        self._help_btn(min_day_hdr,
            "Minimum career day required to trigger this date event.\n"
            "The bot will not click the date before this day.\n\n"
            "Exception: if the date has a mood boost and current mood\n"
            "is below GREAT, the bot may still click before min day.\n\n"
            "Career days: Junior = 1-25, Classic = 26-50, Senior = 51-75"
        ).pack(side=tk.LEFT, padx=(4, 0))

        day_values = [str(d) for d in range(25, 76)]
        for i in range(5):
            row = i + 1
            ttk.Label(table_frame, text=f"{i + 1}", font=("Arial", 9, "bold"),
                      anchor=tk.CENTER).grid(row=row, column=0, padx=10, pady=5)

            day_var = tk.StringVar()
            day_cb = ttk.Combobox(table_frame, textvariable=day_var,
                                  values=day_values, state='readonly', width=8)
            day_cb.grid(row=row, column=1, padx=10, pady=5)
            self.date_vars.append(day_var)

        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=(0, 10))

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Cancel", command=self.window.destroy).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="Save", command=self.save).pack(side=tk.RIGHT)

    def load_values(self):
        self.skip_score_var.set(str(self.config.get('skip_score', 4.5)))
        dates = self.config.get('dates', [])
        for i, date_cfg in enumerate(dates):
            if i >= len(self.date_vars):
                break
            self.date_vars[i].set(str(date_cfg.get('min_day', DEFAULT_DATE_MIN_DAYS[i])))

    def save(self):
        try:
            skip_score_val = self.skip_score_var.get()
            if not skip_score_val:
                messagebox.showerror("Validation Error", "Skip Train Score is required.")
                return

            new_dates = []
            for i, day_var in enumerate(self.date_vars):
                val = day_var.get()
                if not val:
                    messagebox.showerror("Validation Error", f"Date {i + 1}: Min Day is required.")
                    return
                new_dates.append({'min_day': int(val)})

            # Validate: each date's day >= previous date's day
            for i in range(1, len(new_dates)):
                if new_dates[i]['min_day'] < new_dates[i - 1]['min_day']:
                    messagebox.showerror(
                        "Validation Error",
                        f"Date {i + 1} min day ({new_dates[i]['min_day']}) cannot be less than "
                        f"date {i} min day ({new_dates[i - 1]['min_day']})."
                    )
                    return

            self.strategy_tab.friend_events_config = {
                'skip_score': float(skip_score_val),
                'dates': new_dates,
            }
            self.main_window.save_settings()
            self.window.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")

    def center_window(self):
        self.window.update_idletasks()
        width = max(300, self.window.winfo_reqwidth() + 40)
        height = max(280, self.window.winfo_reqheight() + 40)
        parent_x = self.main_window.root.winfo_x()
        parent_y = self.main_window.root.winfo_y()
        parent_width = self.main_window.root.winfo_width()
        parent_height = self.main_window.root.winfo_height()
        x = parent_x + (parent_width // 2) - (width // 2)
        y = parent_y + (parent_height // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
