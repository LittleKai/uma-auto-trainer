import tkinter as tk
from tkinter import ttk


class StrategyTab:
    """Strategy settings, race filters and stop conditions tab"""

    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window

        # Initialize variables
        self.init_variables()

        # Create tab content
        self.create_content()

    def init_variables(self):
        """Initialize tab variables"""
        self.track_filters = {
            'turf': tk.BooleanVar(value=True),
            'dirt': tk.BooleanVar(value=True)
        }

        self.distance_filters = {
            'sprint': tk.BooleanVar(value=True),
            'mile': tk.BooleanVar(value=True),
            'medium': tk.BooleanVar(value=True),
            'long': tk.BooleanVar(value=True)
        }

        self.grade_filters = {
            'g1': tk.BooleanVar(value=True),
            'g2': tk.BooleanVar(value=True),
            'g3': tk.BooleanVar(value=True)
        }

        self.minimum_mood = tk.StringVar(value="NORMAL")
        self.priority_strategy = tk.StringVar(value="Train Score 3.5+")
        self.allow_continuous_racing = tk.BooleanVar(value=True)
        self.manual_event_handling = tk.BooleanVar(value=False)

        self.enable_stop_conditions = tk.BooleanVar(value=False)
        self.stop_on_infirmary = tk.BooleanVar(value=False)
        self.stop_on_need_rest = tk.BooleanVar(value=False)
        self.stop_on_low_mood = tk.BooleanVar(value=False)
        self.stop_on_race_day = tk.BooleanVar(value=False)
        self.stop_mood_threshold = tk.StringVar(value="BAD")
        self.stop_before_summer = tk.BooleanVar(value=False)
        self.stop_at_month = tk.BooleanVar(value=False)
        self.target_month = tk.StringVar(value="Classic Year Jun 1")
        self.stop_on_ura_final = tk.BooleanVar(value=False)
        self.stop_on_warning = tk.BooleanVar(value=False)

        self.bind_variable_changes()

    def update_filters_from_uma_data(self, uma_data):
        """Update filters based on Uma Musume data from Event Choice Tab

        Args:
            uma_data (dict): Dictionary containing track and distance preferences
                            Format: {'turf': bool, 'dirt': bool, 'sprint': bool,
                                    'mile': bool, 'medium': bool, 'long': bool}
        """
        try:
            # Temporarily disable auto-save to prevent multiple saves
            self.disable_auto_save = True

            # Update track filters
            self.track_filters['turf'].set(uma_data.get('turf', False))
            self.track_filters['dirt'].set(uma_data.get('dirt', False))

            # Update distance filters
            self.distance_filters['sprint'].set(uma_data.get('sprint', False))
            self.distance_filters['mile'].set(uma_data.get('mile', False))
            self.distance_filters['medium'].set(uma_data.get('medium', False))
            self.distance_filters['long'].set(uma_data.get('long', False))

            # Re-enable auto-save and trigger one save
            self.disable_auto_save = False
            self.main_window.save_settings()

        except Exception as e:
            print(f"Warning: Could not update strategy filters from Uma data: {e}")
            self.disable_auto_save = False

    def bind_variable_changes(self):
        """Bind variable change events to auto-save with immediate filter update"""
        variables = [
            *self.track_filters.values(),
            *self.distance_filters.values(),
            *self.grade_filters.values(),
            self.minimum_mood,
            self.priority_strategy,
            self.allow_continuous_racing,
            self.manual_event_handling,
            self.enable_stop_conditions,
            self.stop_on_infirmary,
            self.stop_on_need_rest,
            self.stop_on_low_mood,
            self.stop_on_race_day,
            self.stop_mood_threshold,
            self.stop_before_summer,
            self.stop_at_month,
            self.target_month
        ]

        # Modified auto-save function to check disable flag
        def auto_save_with_check(*args):
            if not getattr(self, 'disable_auto_save', False):
                self.main_window.save_settings()

        for var in variables:
            var.trace('w', auto_save_with_check)

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

        # Main content frame - pack without expand
        content_frame = ttk.Frame(scrollable_frame, padding="4")
        content_frame.pack(fill=tk.X, expand=False)  # Changed: expand=False, fill=tk.X only
        content_frame.columnconfigure(0, weight=1, minsize=470)

        # Create sections
        self.create_strategy_settings(content_frame, row=0)
        self.create_race_filters_section(content_frame, row=1)
        self.create_stop_conditions_section(content_frame, row=1)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_strategy_settings(self, parent, row):
        """Create strategy settings section"""
        strategy_frame = ttk.LabelFrame(parent, text="Strategy Settings", padding="5")
        strategy_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        strategy_frame.columnconfigure(1, weight=1)
        strategy_frame.columnconfigure(3, weight=1)

        ttk.Label(strategy_frame, text="Minimum Mood:").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 5), pady=5)

        mood_dropdown = ttk.Combobox(
            strategy_frame,
            textvariable=self.minimum_mood,
            values=["AWFUL", "BAD", "NORMAL", "GOOD", "GREAT"],
            state="readonly",
            width=12
        )
        mood_dropdown.grid(row=0, column=1, sticky=tk.W, padx=(0, 20), pady=5)

        ttk.Label(strategy_frame, text="Priority Strategy:").grid(
            row=0, column=2, sticky=tk.W, padx=(0, 5), pady=5)

        priority_dropdown = ttk.Combobox(
            strategy_frame,
            textvariable=self.priority_strategy,
            values=[
                "G1 (no training)",
                "G2 (no training)",
                "Train Score 2.5+",
                "Train Score 3+",
                "Train Score 3.5+",
                "Train Score 4+",
                "Train Score 4.5+"
            ],
            state="readonly",
            width=22
        )
        priority_dropdown.grid(row=0, column=3, sticky=tk.W, pady=5)

        continuous_racing_check = ttk.Checkbutton(
            strategy_frame,
            text="Allow Continuous Racing (>3 races)",
            variable=self.allow_continuous_racing
        )
        continuous_racing_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(5, 5))

        manual_event_check = ttk.Checkbutton(
            strategy_frame,
            text="Manual Event Handling (pause on events)",
            variable=self.manual_event_handling
        )
        manual_event_check.grid(row=1, column=2, columnspan=2, sticky=tk.W, pady=(5, 5))

        stop_ura_final_check = ttk.Checkbutton(
            strategy_frame,
            text="Stop when reach Ura Final",
            variable=self.stop_on_ura_final
        )
        stop_ura_final_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(5, 5))

        stop_warning_check = ttk.Checkbutton(
            strategy_frame,
            text="Stop when warning detected",
            variable=self.stop_on_warning
        )
        stop_warning_check.grid(row=2, column=2, columnspan=2, sticky=tk.W, pady=(5, 5))

    def create_race_filters_section(self, parent, row):
        """Create race filters section"""
        filter_frame = ttk.LabelFrame(parent, text="Race Filters", padding="10")
        filter_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        filter_frame.columnconfigure(0, weight=1)
        filter_frame.columnconfigure(1, weight=1)
        filter_frame.columnconfigure(2, weight=1)

        # Track filters
        self.create_track_filters(filter_frame)

        # Distance filters
        self.create_distance_filters(filter_frame)

        # Grade filters
        self.create_grade_filters(filter_frame)

    def create_track_filters(self, parent):
        """Create track type filters"""
        track_frame = ttk.LabelFrame(parent, text="Track Type", padding="5")
        track_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N), padx=(0, 5))

        ttk.Checkbutton(
            track_frame,
            text="Turf",
            variable=self.track_filters['turf']
        ).pack(anchor=tk.W, pady=2)

        ttk.Checkbutton(
            track_frame,
            text="Dirt",
            variable=self.track_filters['dirt']
        ).pack(anchor=tk.W, pady=2)

    def create_distance_filters(self, parent):
        """Create distance filters"""
        distance_frame = ttk.LabelFrame(parent, text="Distance", padding="5")
        distance_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N), padx=5)

        distance_inner = ttk.Frame(distance_frame)
        distance_inner.pack(fill=tk.BOTH, expand=True)

        ttk.Checkbutton(
            distance_inner,
            text="Sprint",
            variable=self.distance_filters['sprint']
        ).grid(row=0, column=0, sticky=tk.W, pady=2)

        ttk.Checkbutton(
            distance_inner,
            text="Medium",
            variable=self.distance_filters['medium']
        ).grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)

        ttk.Checkbutton(
            distance_inner,
            text="Mile",
            variable=self.distance_filters['mile']
        ).grid(row=1, column=0, sticky=tk.W, pady=2)

        ttk.Checkbutton(
            distance_inner,
            text="Long",
            variable=self.distance_filters['long']
        ).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)

    def create_grade_filters(self, parent):
        """Create grade filters"""
        grade_frame = ttk.LabelFrame(parent, text="Grade", padding="5")
        grade_frame.grid(row=0, column=2, sticky=(tk.W, tk.E, tk.N), padx=(5, 0))

        grade_inner = ttk.Frame(grade_frame)
        grade_inner.pack(fill=tk.BOTH, expand=True)

        ttk.Checkbutton(
            grade_inner,
            text="G1",
            variable=self.grade_filters['g1']
        ).grid(row=0, column=0, sticky=tk.W, pady=2)

        ttk.Checkbutton(
            grade_inner,
            text="G3",
            variable=self.grade_filters['g3']
        ).grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)

        ttk.Checkbutton(
            grade_inner,
            text="G2",
            variable=self.grade_filters['g2']
        ).grid(row=1, column=0, sticky=tk.W, pady=2)

    def create_stop_conditions_section(self, parent, row):
        """Create stop conditions section"""
        stop_frame = ttk.LabelFrame(parent, text="Stop Conditions", padding="10")
        stop_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=(0, 5))

        # Container for checkbox and button in same row
        # controls_frame = ttk.Frame(stop_frame)
        # controls_frame.pack(fill=tk.X)

        # Enable stop conditions checkbox
        enable_check = ttk.Checkbutton(
            stop_frame,
            text="Enable stop conditions",
            variable=self.enable_stop_conditions
        )
        # enable_check.pack(side=tk.LEFT)
        enable_check.pack(anchor=tk.W, pady=(0,10))

        # Configure stop conditions button
        config_button = ttk.Button(
            stop_frame,
            text="⚙ Configure Stop Conditions",
            command=self.open_stop_conditions_dialog
        )
        # config_button.pack(side=tk.LEFT, padx=(20, 0))
        config_button.pack(fill=tk.X)


    def open_stop_conditions_dialog(self):
        """Open stop conditions configuration dialog"""
        try:
            from gui.dialogs.stop_conditions_dialog import StopConditionsWindow
            StopConditionsWindow(self)
        except Exception as e:
            print(f"Error opening stop conditions dialog: {e}")

    def get_settings(self):
        """Get current tab settings"""
        settings = {
            'track': {k: v.get() for k, v in self.track_filters.items()},
            'distance': {k: v.get() for k, v in self.distance_filters.items()},
            'grade': {k: v.get() for k, v in self.grade_filters.items()},
            'minimum_mood': self.minimum_mood.get(),
            'priority_strategy': self.priority_strategy.get(),
            'allow_continuous_racing': self.allow_continuous_racing.get(),
            'manual_event_handling': self.manual_event_handling.get(),
            'enable_stop_conditions': self.enable_stop_conditions.get(),
            'stop_on_infirmary': self.stop_on_infirmary.get(),
            'stop_on_need_rest': self.stop_on_need_rest.get(),
            'stop_on_low_mood': self.stop_on_low_mood.get(),
            'stop_on_race_day': self.stop_on_race_day.get(),
            'stop_mood_threshold': self.stop_mood_threshold.get(),
            'stop_before_summer': self.stop_before_summer.get(),
            'stop_at_month': self.stop_at_month.get(),
            'target_month': self.target_month.get(),
            'stop_on_ura_final': self.stop_on_ura_final.get(),
            'stop_on_warning': self.stop_on_warning.get()
        }

        return settings

    def load_settings(self, settings):
        """Load settings into tab"""
        try:
            for k, v in settings.get('track', {}).items():
                if k in self.track_filters:
                    self.track_filters[k].set(v)

            for k, v in settings.get('distance', {}).items():
                if k in self.distance_filters:
                    self.distance_filters[k].set(v)

            for k, v in settings.get('grade', {}).items():
                if k in self.grade_filters:
                    self.grade_filters[k].set(v)

            if 'minimum_mood' in settings:
                self.minimum_mood.set(settings['minimum_mood'])
            if 'priority_strategy' in settings:
                self.priority_strategy.set(settings['priority_strategy'])
            if 'allow_continuous_racing' in settings:
                self.allow_continuous_racing.set(settings['allow_continuous_racing'])
            if 'manual_event_handling' in settings:
                self.manual_event_handling.set(settings['manual_event_handling'])

            stop_condition_keys = [
                'enable_stop_conditions', 'stop_on_infirmary', 'stop_on_need_rest',
                'stop_on_low_mood', 'stop_on_race_day', 'stop_mood_threshold',
                'stop_before_summer', 'stop_at_month', 'target_month',
                'stop_on_ura_final', 'stop_on_warning'
            ]

            for key in stop_condition_keys:
                if key in settings:
                    getattr(self, key).set(settings[key])

        except Exception as e:
            print(f"Warning: Could not load strategy tab settings: {e}")