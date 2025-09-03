import tkinter as tk
from tkinter import ttk


class FiltersSection:
    """Race filters and stop conditions section component"""

    def __init__(self, parent, main_window, row=0):
        self.parent = parent
        self.main_window = main_window
        self.row = row

        self.create_section()

    def create_section(self):
        """Create the filters and stop conditions section"""
        # Main container
        self.container = ttk.Frame(self.parent)
        self.container.grid(row=self.row, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        self.container.columnconfigure(0, weight=1)
        self.container.columnconfigure(1, weight=1)

        # Create subsections
        self.create_race_filters()
        self.create_stop_conditions()

    def create_race_filters(self):
        """Create race filters section"""
        filter_frame = ttk.LabelFrame(self.container, text="Race Filters", padding="10")
        filter_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N), padx=(0, 10))
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
            variable=self.main_window.track_filters['turf'],
            command=self.main_window.save_settings
        ).pack(anchor=tk.W, pady=2)

        ttk.Checkbutton(
            track_frame,
            text="Dirt",
            variable=self.main_window.track_filters['dirt'],
            command=self.main_window.save_settings
        ).pack(anchor=tk.W, pady=2)

    def create_distance_filters(self, parent):
        """Create distance filters"""
        distance_frame = ttk.LabelFrame(parent, text="Distance", padding="5")
        distance_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N), padx=5)

        distance_inner = ttk.Frame(distance_frame)
        distance_inner.pack(fill=tk.BOTH, expand=True)

        # Sprint and Medium
        ttk.Checkbutton(
            distance_inner,
            text="Sprint",
            variable=self.main_window.distance_filters['sprint'],
            command=self.main_window.save_settings
        ).grid(row=0, column=0, sticky=tk.W, pady=2)

        ttk.Checkbutton(
            distance_inner,
            text="Medium",
            variable=self.main_window.distance_filters['medium'],
            command=self.main_window.save_settings
        ).grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)

        # Mile and Long
        ttk.Checkbutton(
            distance_inner,
            text="Mile",
            variable=self.main_window.distance_filters['mile'],
            command=self.main_window.save_settings
        ).grid(row=1, column=0, sticky=tk.W, pady=2)

        ttk.Checkbutton(
            distance_inner,
            text="Long",
            variable=self.main_window.distance_filters['long'],
            command=self.main_window.save_settings
        ).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)

    def create_grade_filters(self, parent):
        """Create grade filters"""
        grade_frame = ttk.LabelFrame(parent, text="Grade", padding="5")
        grade_frame.grid(row=0, column=2, sticky=(tk.W, tk.E, tk.N), padx=(5, 0))

        grade_inner = ttk.Frame(grade_frame)
        grade_inner.pack(fill=tk.BOTH, expand=True)

        # G1 and G3
        ttk.Checkbutton(
            grade_inner,
            text="G1",
            variable=self.main_window.grade_filters['g1'],
            command=self.main_window.save_settings
        ).grid(row=0, column=0, sticky=tk.W, pady=2)

        ttk.Checkbutton(
            grade_inner,
            text="G3",
            variable=self.main_window.grade_filters['g3'],
            command=self.main_window.save_settings
        ).grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)

        # G2
        ttk.Checkbutton(
            grade_inner,
            text="G2",
            variable=self.main_window.grade_filters['g2'],
            command=self.main_window.save_settings
        ).grid(row=1, column=0, sticky=tk.W, pady=2)

    def create_stop_conditions(self):
        """Create stop conditions section"""
        stop_conditions_frame = ttk.LabelFrame(self.container, text="Stop Conditions", padding="10")
        stop_conditions_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N))

        # Enable stop conditions checkbox
        enable_stop_check = ttk.Checkbutton(
            stop_conditions_frame,
            text="Enable stop conditions",
            variable=self.main_window.enable_stop_conditions,
            command=self.main_window.save_settings
        )
        enable_stop_check.pack(anchor=tk.W, pady=(0, 10))

        # Configure stop conditions button
        config_stop_button = ttk.Button(
            stop_conditions_frame,
            text="⚙ Configure Stop Conditions",
            command=self.main_window.open_stop_conditions_window
        )
        config_stop_button.pack(fill=tk.X)