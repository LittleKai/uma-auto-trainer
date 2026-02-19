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
    GRADE_OPTIONS = ['All', 'G1', 'G2', 'G3', 'OP']

    DEFAULT_FILTERS = {
        'year': 'All',
        'grade': 'All',
    }

    def __init__(self, parent, callback=None, filters=None, on_filters_changed=None):
        """
        Args:
            parent: Parent widget
            callback: Called with selected race dict on Add
            filters: Dict of saved filter values (year, grade)
            on_filters_changed: Called with new filter dict when filters change
        """
        self.parent = parent
        self.callback = callback
        self.on_filters_changed = on_filters_changed
        self.selected_race = None

        # Load race data
        self.races = self._load_races()

        # Init filter vars with saved values
        saved = filters or {}
        self.filter_year = tk.StringVar(value=saved.get('year', 'All'))
        self.filter_grade = tk.StringVar(value=saved.get('grade', 'All'))

        # Create dialog
        self.window = tk.Toplevel(parent)
        self.window.title("Select Race")
        self.window.geometry("750x500")
        self.window.resizable(True, True)
        self.window.minsize(600, 400)

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

        # Sort by absolute_day
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
        ).pack(pady=(0, 8))

        # Filter + Search row
        filter_frame = ttk.Frame(main_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 8))

        # Year filter
        ttk.Label(filter_frame, text="Year:").pack(side=tk.LEFT, padx=(0, 3))
        year_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.filter_year,
            values=self.YEAR_OPTIONS,
            state="readonly",
            width=12
        )
        year_combo.pack(side=tk.LEFT, padx=(0, 10))
        year_combo.bind("<<ComboboxSelected>>", lambda e: self._on_filter_change())

        # Grade filter
        ttk.Label(filter_frame, text="Grade:").pack(side=tk.LEFT, padx=(0, 3))
        grade_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.filter_grade,
            values=self.GRADE_OPTIONS,
            state="readonly",
            width=6
        )
        grade_combo.pack(side=tk.LEFT, padx=(0, 15))
        grade_combo.bind("<<ComboboxSelected>>", lambda e: self._on_filter_change())

        # Search
        ttk.Label(filter_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 3))
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self._apply_filters())

        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=25)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        search_entry.focus_set()

        # Treeview frame
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Treeview with columns
        columns = ("day", "name", "year", "date", "grade", "track", "distance", "fan_gain")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=scrollbar.set,
            selectmode="browse"
        )
        scrollbar.config(command=self.tree.yview)

        # Configure columns
        self.tree.heading("day", text="Day")
        self.tree.heading("name", text="Race Name")
        self.tree.heading("year", text="Year")
        self.tree.heading("date", text="Date")
        self.tree.heading("grade", text="Grade")
        self.tree.heading("track", text="Track")
        self.tree.heading("distance", text="Distance")
        self.tree.heading("fan_gain", text="Fan Gain")

        self.tree.column("day", width=40, anchor=tk.CENTER)
        self.tree.column("name", width=200)
        self.tree.column("year", width=90)
        self.tree.column("date", width=90)
        self.tree.column("grade", width=55, anchor=tk.CENTER)
        self.tree.column("track", width=70, anchor=tk.CENTER)
        self.tree.column("distance", width=90)
        self.tree.column("fan_gain", width=65, anchor=tk.CENTER)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Double-click to select
        self.tree.bind("<Double-Button-1>", lambda e: self._on_select())

        # Populate treeview
        self._apply_filters()

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Add", command=self._on_select).pack(side=tk.RIGHT)

    def _get_current_filters(self):
        """Get current filter values as dict"""
        return {
            'year': self.filter_year.get(),
            'grade': self.filter_grade.get(),
        }

    def _on_filter_change(self):
        """Handle filter combobox change"""
        self._apply_filters()
        # Persist filters globally
        if self.on_filters_changed:
            self.on_filters_changed(self._get_current_filters())

    def _apply_filters(self):
        """Apply all filters and repopulate tree"""
        self.tree.delete(*self.tree.get_children())

        search_lower = self.search_var.get().lower()
        year_filter = self.filter_year.get()
        grade_filter = self.filter_grade.get()

        for race in self.races:
            name = race.get("name", "")

            # Search filter
            if search_lower and search_lower not in name.lower():
                continue

            # Year filter
            if year_filter != "All" and race.get("year", "") != year_filter:
                continue

            # Grade filter
            if grade_filter != "All" and race.get("grade", "") != grade_filter:
                continue

            abs_day = race.get("absolute_day", "?")
            year = race.get("year", "")
            date = race.get("date", "")
            grade = race.get("grade", "")
            track = race.get("track", "")
            distance = race.get("distance", "")
            fan_gain = race.get("fan_gain", 0)

            self.tree.insert("", tk.END, values=(
                abs_day, name, year, date, grade, track, distance, fan_gain
            ))

    def _on_select(self):
        """Handle add button or double-click"""
        selection = self.tree.selection()
        if not selection:
            return

        values = self.tree.item(selection[0], "values")
        if values:
            day = int(values[0]) if values[0] != "?" else 0
            name = values[1]
            grade = values[4]

            self.selected_race = {"name": name, "day": day, "grade": grade}

            if self.callback:
                self.callback(self.selected_race)
            self.window.destroy()

    def _on_cancel(self):
        """Handle cancel"""
        self.window.destroy()

    def _center_window(self):
        """Center window on screen"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.window.geometry(f"{width}x{height}+{x}+{y}")
