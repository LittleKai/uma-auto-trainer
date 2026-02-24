import tkinter as tk
from tkinter import ttk
import json
import os


class RaceScheduleDialog:
    """Dialog to select races from race_list.json for the race schedule"""

    MONTHS = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }
    YEAR_INDICES = {'Junior': 0, 'Classic': 1, 'Senior': 2}

    YEAR_OPTIONS = ['All', 'Junior Year', 'Classic Year', 'Senior Year']

    GRADE_OPTIONS    = ['G1', 'G2', 'G3', 'OP', 'Pre-OP']
    TRACK_OPTIONS    = ['Turf', 'Dirt']
    DISTANCE_OPTIONS = ['Sprint', 'Mile', 'Medium', 'Long']

    DEFAULT_FILTERS = {
        'year':      'All',
        'grades':    GRADE_OPTIONS[:],
        'tracks':    TRACK_OPTIONS[:],
        'distances': DISTANCE_OPTIONS[:],
    }

    def __init__(self, parent, callback=None, filters=None, on_filters_changed=None):
        """
        Args:
            parent: Parent widget
            callback: Called with selected race dict on Add
            filters: Dict of saved filter values
            on_filters_changed: Called with new filter dict when filters change
        """
        self.parent = parent
        self.callback = callback
        self.on_filters_changed = on_filters_changed
        self.selected_race = None

        # Load race data
        self.races = self._load_races()

        saved = filters or {}

        # Year filter (combobox)
        self.filter_year = tk.StringVar(value=saved.get('year', 'All'))

        # Grade checkboxes
        saved_grades = saved.get('grades', self.GRADE_OPTIONS[:])
        self.filter_grades = {
            g: tk.BooleanVar(value=(g in saved_grades))
            for g in self.GRADE_OPTIONS
        }

        # Track checkboxes
        saved_tracks = saved.get('tracks', self.TRACK_OPTIONS[:])
        self.filter_tracks = {
            t: tk.BooleanVar(value=(t in saved_tracks))
            for t in self.TRACK_OPTIONS
        }

        # Distance checkboxes
        saved_distances = saved.get('distances', self.DISTANCE_OPTIONS[:])
        self.filter_distances = {
            d: tk.BooleanVar(value=(d in saved_distances))
            for d in self.DISTANCE_OPTIONS
        }

        # Create dialog
        self.window = tk.Toplevel(parent)
        self.window.title("Select Race")
        self.window.geometry("800x560")
        self.window.resizable(True, True)
        self.window.minsize(650, 450)

        # Make modal
        self.window.transient(parent)
        self.window.grab_set()

        # Setup UI
        self._setup_ui()

        # Center window
        self._center_window()

        # Bind close event
        self.window.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _load_races(self):
        """Load and enrich race data with absolute_day"""
        races = []
        try:
            race_file = os.path.join("assets", "race_list.json")
            if os.path.exists(race_file):
                with open(race_file, "r", encoding="utf-8") as f:
                    raw_races = json.load(f)

                for race in raw_races:
                    abs_day = self._compute_absolute_day(race)
                    if abs_day is not None:
                        race["absolute_day"] = abs_day
                        races.append(race)
        except Exception as e:
            print(f"Error loading races for dialog: {e}")

        races.sort(key=lambda r: r.get("absolute_day", 0))
        return races

    def _compute_absolute_day(self, race):
        """Compute absolute_day for a race"""
        try:
            year_str = race.get("year", "").split()[0]
            date_parts = race.get("date", "").split()
            if len(date_parts) < 2:
                return None
            month_str = date_parts[0][:3]
            day = int(date_parts[1])

            year_index = self.YEAR_INDICES.get(year_str)
            month_num = self.MONTHS.get(month_str)
            if year_index is None or month_num is None:
                return None

            return year_index * 24 + (month_num - 1) * 2 + (day - 1) + 1
        except Exception:
            return None

    def _setup_ui(self):
        """Setup dialog UI"""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(
            main_frame,
            text="Select Race to Add",
            font=("Arial", 12, "bold")
        ).pack(pady=(0, 6))

        # ── Row 1: Year + Search ──────────────────────────────────────
        top_row = ttk.Frame(main_frame)
        top_row.pack(fill=tk.X, pady=(0, 4))

        ttk.Label(top_row, text="Year:").pack(side=tk.LEFT, padx=(0, 3))
        year_combo = ttk.Combobox(
            top_row,
            textvariable=self.filter_year,
            values=self.YEAR_OPTIONS,
            state="readonly",
            width=13
        )
        year_combo.pack(side=tk.LEFT, padx=(0, 15))
        year_combo.bind("<<ComboboxSelected>>", lambda e: self._on_filter_change())

        ttk.Label(top_row, text="Search:").pack(side=tk.LEFT, padx=(0, 3))
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self._apply_filters())
        search_entry = ttk.Entry(top_row, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        search_entry.focus_set()

        # ── Row 2: Checkbox filters ───────────────────────────────────
        filter_row = ttk.Frame(main_frame)
        filter_row.pack(fill=tk.X, pady=(0, 6))

        self._build_checkbox_group(filter_row, "Grade", self.GRADE_OPTIONS, self.filter_grades)
        ttk.Separator(filter_row, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)
        self._build_checkbox_group(filter_row, "Track", self.TRACK_OPTIONS, self.filter_tracks)
        ttk.Separator(filter_row, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)
        self._build_checkbox_group(filter_row, "Distance", self.DISTANCE_OPTIONS, self.filter_distances)

        # ── Treeview ──────────────────────────────────────────────────
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        columns = ("day", "name", "year", "date", "grade", "track", "distance", "fan_gain")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=scrollbar.set,
            selectmode="browse"
        )
        scrollbar.config(command=self.tree.yview)

        self.tree.heading("day",      text="Day")
        self.tree.heading("name",     text="Race Name")
        self.tree.heading("year",     text="Year")
        self.tree.heading("date",     text="Date")
        self.tree.heading("grade",    text="Grade")
        self.tree.heading("track",    text="Track")
        self.tree.heading("distance", text="Distance")
        self.tree.heading("fan_gain", text="Fan Gain")

        self.tree.column("day",      width=40,  anchor=tk.CENTER)
        self.tree.column("name",     width=200)
        self.tree.column("year",     width=90)
        self.tree.column("date",     width=90)
        self.tree.column("grade",    width=55,  anchor=tk.CENTER)
        self.tree.column("track",    width=70,  anchor=tk.CENTER)
        self.tree.column("distance", width=90)
        self.tree.column("fan_gain", width=65,  anchor=tk.CENTER)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-Button-1>", lambda e: self._on_select())

        self._apply_filters()

        # ── Buttons ───────────────────────────────────────────────────
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Add",    command=self._on_select).pack(side=tk.RIGHT)

    def _build_checkbox_group(self, parent, label: str, options: list, var_dict: dict):
        """Build a labeled group of checkboxes inside parent (packed LEFT)."""
        group = ttk.Frame(parent)
        group.pack(side=tk.LEFT, anchor=tk.W)

        ttk.Label(group, text=f"{label}:", font=("Arial", 8, "bold")).pack(anchor=tk.W)

        cb_row = ttk.Frame(group)
        cb_row.pack(anchor=tk.W)
        for opt in options:
            ttk.Checkbutton(
                cb_row,
                text=opt,
                variable=var_dict[opt],
                command=self._on_filter_change
            ).pack(side=tk.LEFT, padx=(0, 2))

    # ── Filter helpers ─────────────────────────────────────────────────

    def _get_current_filters(self):
        """Get current filter values as dict (serialisable)."""
        return {
            'year':      self.filter_year.get(),
            'grades':    [g for g, v in self.filter_grades.items()    if v.get()],
            'tracks':    [t for t, v in self.filter_tracks.items()    if v.get()],
            'distances': [d for d, v in self.filter_distances.items() if v.get()],
        }

    def _on_filter_change(self):
        """Handle any filter change (combobox or checkbox)."""
        self._apply_filters()
        if self.on_filters_changed:
            self.on_filters_changed(self._get_current_filters())

    def _match_track(self, race_track: str, checked_tracks: list) -> bool:
        """True if race_track belongs to one of the checked track categories.
        'Varies' tracks always pass (satisfy all categories).
        """
        if race_track.startswith('Varies'):
            return True
        for t in checked_tracks:
            if race_track.startswith(t):
                return True
        return False

    def _match_distance(self, race_distance: str, checked_distances: list) -> bool:
        """True if race_distance belongs to one of the checked distance categories.
        'Varies' distances always pass (satisfy all categories).
        """
        if race_distance.startswith('Varies'):
            return True
        for d in checked_distances:
            if race_distance.startswith(d):
                return True
        return False

    def _apply_filters(self):
        """Apply all filters and repopulate tree."""
        self.tree.delete(*self.tree.get_children())

        search_lower      = self.search_var.get().lower()
        year_filter       = self.filter_year.get()
        checked_grades    = [g for g, v in self.filter_grades.items()    if v.get()]
        checked_tracks    = [t for t, v in self.filter_tracks.items()    if v.get()]
        checked_distances = [d for d, v in self.filter_distances.items() if v.get()]

        for race in self.races:
            name     = race.get("name", "")
            track    = race.get("track", "")
            distance = race.get("distance", "")
            grade    = race.get("grade", "")

            if search_lower and search_lower not in name.lower():
                continue
            if year_filter != "All" and race.get("year", "") != year_filter:
                continue
            if checked_grades and grade not in checked_grades:
                continue
            if checked_tracks and not self._match_track(track, checked_tracks):
                continue
            if checked_distances and not self._match_distance(distance, checked_distances):
                continue

            self.tree.insert("", tk.END, values=(
                race.get("absolute_day", "?"),
                name,
                race.get("year", ""),
                race.get("date", ""),
                grade,
                track,
                distance,
                race.get("fan_gain", 0)
            ))

    # ── Select / Cancel ────────────────────────────────────────────────

    def _on_select(self):
        """Handle Add button or double-click."""
        selection = self.tree.selection()
        if not selection:
            return

        values = self.tree.item(selection[0], "values")
        if values:
            day   = int(values[0]) if values[0] != "?" else 0
            name  = values[1]
            grade = values[4]

            self.selected_race = {"name": name, "day": day, "grade": grade}

            if self.callback:
                self.callback(self.selected_race)
            self.window.destroy()

    def _on_cancel(self):
        self.window.destroy()

    def _center_window(self):
        self.window.update_idletasks()
        w = self.window.winfo_width()
        h = self.window.winfo_height()
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        self.window.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
