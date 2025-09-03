import tkinter as tk
from tkinter import ttk, messagebox
import pyautogui
from PIL import ImageTk, Image
from utils.constants import get_current_regions, update_regions, DEFAULT_REGIONS

class RegionSettingsWindow:
    """Window for configuring OCR and UI detection regions"""

    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Region Settings")
        self.window.geometry("1000x800")
        self.window.resizable(True, True)

        # Keep window on top and set as dialog
        self.window.attributes('-topmost', True)
        self.window.transient(parent)
        self.window.grab_set()  # Make it modal

        # Current region values
        self.current_regions = get_current_regions()
        self.region_vars = {}

        # Preview variables
        self.preview_image = None
        self.screenshot_taken = False

        self.setup_ui()
        self.load_current_values()

        # Bind window close event
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Center window on screen
        self.center_window()

    def center_window(self):
        """Center the window on screen"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def setup_ui(self):
        """Setup the user interface"""
        # Create notebook for tabs
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab 1: Main Regions
        main_tab = ttk.Frame(notebook)
        notebook.add(main_tab, text="Main Regions")
        self.setup_main_regions_tab(main_tab)

        # Tab 2: Stat Regions
        stat_tab = ttk.Frame(notebook)
        notebook.add(stat_tab, text="Stat Regions")
        self.setup_stat_regions_tab(stat_tab)

        # Tab 3: Event Choice Regions
        event_tab = ttk.Frame(notebook)
        notebook.add(event_tab, text="Event Choice Regions")
        self.setup_event_regions_tab(event_tab)

        # Tab 4: Preview & Test
        preview_tab = ttk.Frame(notebook)
        notebook.add(preview_tab, text="Preview & Test")
        self.setup_preview_tab(preview_tab)

        # Bottom button frame
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Control buttons
        ttk.Button(button_frame, text="Reset to Defaults",
                   command=self.reset_to_defaults).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Test All Regions",
                   command=self.test_regions).pack(side=tk.LEFT, padx=5)

        # Right side buttons
        ttk.Button(button_frame, text="Cancel",
                   command=self.on_closing).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Save & Apply",
                   command=self.save_settings).pack(side=tk.RIGHT, padx=5)

    def setup_main_regions_tab(self, parent):
        """Setup main regions configuration tab"""
        # Create scrollable frame
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        main_frame = ttk.Frame(scrollable_frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Instructions
        instructions = ttk.Label(main_frame,
                                 text="Configure main OCR and UI detection regions\n" +
                                      "Format: X, Y, Width, Height (all in pixels)",
                                 font=("Arial", 10), justify=tk.CENTER,
                                 foreground="blue")
        instructions.pack(pady=(0, 15))

        # UI Detection Regions
        ui_frame = ttk.LabelFrame(main_frame, text="UI Detection Regions", padding="10")
        ui_frame.pack(fill=tk.X, pady=(0, 10))

        ui_regions = [
            ("Support Card Icon Region", "SUPPORT_CARD_ICON_REGION",
             "Area where support card icons appear during training selection"),
            ("Race List Region", "RACE_REGION",
             "Area containing the race selection list"),
            ("Energy Bar Region", "ENERGY_BAR",
             "Energy bar endpoints (format: x1, y1, x2, y2)"),
        ]

        for i, (label, key, desc) in enumerate(ui_regions):
            self.create_region_entry(ui_frame, i, label, key, desc)

        # OCR Text Regions
        ocr_frame = ttk.LabelFrame(main_frame, text="OCR Text Regions", padding="10")
        ocr_frame.pack(fill=tk.X, pady=(0, 10))

        ocr_regions = [
            ("Mood Region", "MOOD_REGION",
             "Character mood text area (AWFUL/BAD/NORMAL/GOOD/GREAT)"),
            ("Turn Region", "TURN_REGION",
             "Turn number or 'Race Day' text area"),
            ("Year Region", "YEAR_REGION",
             "Date/year information text area (e.g., 'Classic Year Late Oct')"),
            ("Criteria Region", "CRITERIA_REGION",
             "Race criteria or condition text area"),
            ("Failure Region", "FAILURE_REGION",
             "Training failure percentage text area"),
        ]

        for i, (label, key, desc) in enumerate(ocr_regions):
            self.create_region_entry(ocr_frame, i, label, key, desc)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def setup_stat_regions_tab(self, parent):
        """Setup stat regions configuration tab"""
        main_frame = ttk.Frame(parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Instructions
        instructions = ttk.Label(main_frame,
                                 text="Configure character stat number regions\n" +
                                      "These regions should contain only the numeric values",
                                 font=("Arial", 10), justify=tk.CENTER,
                                 foreground="blue")
        instructions.pack(pady=(0, 15))

        # Stat Regions
        stat_frame = ttk.LabelFrame(main_frame, text="Character Stat Regions", padding="10")
        stat_frame.pack(fill=tk.X)

        stat_info = [
            ("spd", "Speed", "Speed stat number (e.g., 1200)"),
            ("sta", "Stamina", "Stamina stat number (e.g., 800)"),
            ("pwr", "Power", "Power stat number (e.g., 950)"),
            ("guts", "Guts", "Guts stat number (e.g., 600)"),
            ("wit", "Wisdom", "Wisdom stat number (e.g., 750)"),
        ]

        for i, (stat_key, stat_name, desc) in enumerate(stat_info):
            self.create_stat_region_entry(stat_frame, i, stat_name, stat_key, desc)

    def setup_event_regions_tab(self, parent):
        """Setup event choice regions configuration tab"""
        main_frame = ttk.Frame(parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Instructions
        instructions = ttk.Label(main_frame,
                                 text="Configure event choice detection regions\n" +
                                      "These regions are used for automatic event handling",
                                 font=("Arial", 10), justify=tk.CENTER,
                                 foreground="blue")
        instructions.pack(pady=(0, 15))

        # Event Choice Regions
        event_frame = ttk.LabelFrame(main_frame, text="Event Choice Regions", padding="10")
        event_frame.pack(fill=tk.X)

        event_regions = [
            ("Event Region", "EVENT_REGION",
             "Area where event type icons appear (scenario/uma_musume/support_card)"),
            ("Event Name Region", "EVENT_NAME_REGION",
             "Area containing the event name text for OCR recognition"),
        ]

        for i, (label, key, desc) in enumerate(event_regions):
            self.create_region_entry(event_frame, i, label, key, desc)

    def setup_preview_tab(self, parent):
        """Setup preview and testing tab"""
        main_frame = ttk.Frame(parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Screenshot section
        screenshot_frame = ttk.LabelFrame(main_frame, text="Screenshot", padding="10")
        screenshot_frame.pack(fill=tk.X, pady=(0, 10))

        screenshot_info = ttk.Label(screenshot_frame,
                                    text="Take a screenshot first to enable region preview functionality",
                                    font=("Arial", 9))
        screenshot_info.pack(pady=(0, 10))

        screenshot_btn_frame = ttk.Frame(screenshot_frame)
        screenshot_btn_frame.pack()

        self.screenshot_btn = ttk.Button(screenshot_btn_frame, text="📷 Take Screenshot",
                                         command=self.take_screenshot)
        self.screenshot_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.screenshot_status = ttk.Label(screenshot_btn_frame, text="No screenshot taken",
                                           foreground="red")
        self.screenshot_status.pack(side=tk.LEFT)

        # Preview section
        preview_frame = ttk.LabelFrame(main_frame, text="Region Preview", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True)

        preview_info = ttk.Label(preview_frame,
                                 text="Click 'Preview' buttons next to each region to see what area will be captured",
                                 font=("Arial", 9))
        preview_info.pack(pady=(0, 10))

        # Quick preview buttons
        quick_preview_frame = ttk.Frame(preview_frame)
        quick_preview_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(quick_preview_frame, text="Quick Preview:", font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        ttk.Button(quick_preview_frame, text="Mood", width=8,
                   command=lambda: self.preview_specific_region("MOOD_REGION")).pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_preview_frame, text="Energy", width=8,
                   command=lambda: self.preview_specific_region("ENERGY_BAR")).pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_preview_frame, text="SPD Stat", width=8,
                   command=lambda: self.preview_stat_region("spd")).pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_preview_frame, text="Event", width=8,
                   command=lambda: self.preview_specific_region("EVENT_REGION")).pack(side=tk.LEFT, padx=5)

        # Test results area
        test_frame = ttk.LabelFrame(main_frame, text="Test Results", padding="10")
        test_frame.pack(fill=tk.X, pady=(10, 0))

        self.test_result_text = tk.Text(test_frame, height=8, wrap=tk.WORD, font=("Consolas", 9))
        test_scrollbar = ttk.Scrollbar(test_frame, orient="vertical", command=self.test_result_text.yview)
        self.test_result_text.configure(yscrollcommand=test_scrollbar.set)

        self.test_result_text.pack(side="left", fill="both", expand=True)
        test_scrollbar.pack(side="right", fill="y")

        # Insert initial text
        self.test_result_text.insert(tk.END, "Click 'Test All Regions' to verify your settings...\n")
        self.test_result_text.configure(state='disabled')

    def create_region_entry(self, parent, row, label, key, description):
        """Create input fields for a region configuration"""
        # Main container
        container = ttk.Frame(parent)
        container.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5, padx=5)
        parent.columnconfigure(0, weight=1)

        # Label section
        label_frame = ttk.Frame(container)
        label_frame.grid(row=0, column=0, sticky=(tk.W, tk.N), padx=(0, 10))

        ttk.Label(label_frame, text=label, font=("Arial", 9, "bold")).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(label_frame, text=description, font=("Arial", 8),
                  foreground="gray", wraplength=200).grid(row=1, column=0, sticky=tk.W)

        # Coordinate inputs
        coord_frame = ttk.Frame(container)
        coord_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        container.columnconfigure(1, weight=1)

        self.region_vars[key] = {}

        # Special handling for Energy Bar (x1, y1, x2, y2)
        if key == "ENERGY_BAR":
            coord_labels = ["X1:", "Y1:", "X2:", "Y2:"]
        else:
            coord_labels = ["X:", "Y:", "Width:", "Height:"]

        for i, coord_label in enumerate(coord_labels):
            ttk.Label(coord_frame, text=coord_label).grid(row=0, column=i*2, padx=(10 if i > 0 else 0, 2))
            var = tk.StringVar()
            entry = ttk.Entry(coord_frame, textvariable=var, width=8)
            entry.grid(row=0, column=i*2+1, padx=(0, 5))
            self.region_vars[key][i] = var

        # Preview button
        ttk.Button(container, text="Preview", width=10,
                   command=lambda k=key: self.preview_specific_region(k)).grid(row=0, column=2, padx=5)

    def create_stat_region_entry(self, parent, row, label, stat_key, description):
        """Create input fields for stat region configuration"""
        # Main container
        container = ttk.Frame(parent)
        container.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5, padx=5)
        parent.columnconfigure(0, weight=1)

        # Label section
        label_frame = ttk.Frame(container)
        label_frame.grid(row=0, column=0, sticky=(tk.W, tk.N), padx=(0, 10))

        ttk.Label(label_frame, text=f"{label} Stat", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(label_frame, text=description, font=("Arial", 8),
                  foreground="gray", wraplength=200).grid(row=1, column=0, sticky=tk.W)

        # Coordinate inputs
        coord_frame = ttk.Frame(container)
        coord_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        container.columnconfigure(1, weight=1)

        key = f"STAT_{stat_key.upper()}"
        self.region_vars[key] = {}
        coord_labels = ["X:", "Y:", "Width:", "Height:"]

        for i, coord_label in enumerate(coord_labels):
            ttk.Label(coord_frame, text=coord_label).grid(row=0, column=i*2, padx=(10 if i > 0 else 0, 2))
            var = tk.StringVar()
            entry = ttk.Entry(coord_frame, textvariable=var, width=8)
            entry.grid(row=0, column=i*2+1, padx=(0, 5))
            self.region_vars[key][i] = var

        # Preview button
        ttk.Button(container, text="Preview", width=10,
                   command=lambda s=stat_key: self.preview_stat_region(s)).grid(row=0, column=2, padx=5)

    def load_current_values(self):
        """Load current region values into input fields"""
        try:
            # Load main regions
            for key, coords in self.current_regions.items():
                if key == 'STAT_REGIONS':
                    continue
                if key == 'EVENT_REGIONS':
                    continue

                if key in self.region_vars:
                    for i, value in enumerate(coords):
                        self.region_vars[key][i].set(str(value))

            # Load stat regions
            stat_regions = self.current_regions.get('STAT_REGIONS', {})
            for stat, coords in stat_regions.items():
                key = f"STAT_{stat.upper()}"
                if key in self.region_vars:
                    for i, value in enumerate(coords):
                        self.region_vars[key][i].set(str(value))

            # Load event regions
            event_regions = self.current_regions.get('EVENT_REGIONS', {})
            for event_key, coords in event_regions.items():
                if event_key in self.region_vars:
                    for i, value in enumerate(coords):
                        self.region_vars[event_key][i].set(str(value))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load current values: {e}")

    def get_region_values(self):
        """Get current values from input fields"""
        try:
            regions = {}
            stat_regions = {}
            event_regions = {}

            for key, coord_vars in self.region_vars.items():
                if key.startswith('STAT_'):
                    stat_name = key[5:].lower()
                    coords = []
                    for i in range(4):
                        value = coord_vars[i].get().strip()
                        if not value:
                            raise ValueError(f"Empty value for {key} coordinate {i+1}")
                        coords.append(int(value))
                    stat_regions[stat_name] = tuple(coords)
                elif key in ['EVENT_REGION', 'EVENT_NAME_REGION']:
                    coords = []
                    for i in range(4):
                        value = coord_vars[i].get().strip()
                        if not value:
                            raise ValueError(f"Empty value for {key} coordinate {i+1}")
                        coords.append(int(value))
                    event_regions[key] = tuple(coords)
                else:
                    coords = []
                    for i in range(4):
                        value = coord_vars[i].get().strip()
                        if not value:
                            raise ValueError(f"Empty value for {key} coordinate {i+1}")
                        coords.append(int(value))
                    regions[key] = tuple(coords)

            regions['STAT_REGIONS'] = stat_regions
            regions['EVENT_REGIONS'] = event_regions
            return regions

        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid input: {e}")
            return None
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get region values: {e}")
            return None

    def take_screenshot(self):
        """Take a screenshot for preview"""
        try:
            # Minimize this window temporarily
            self.window.withdraw()
            self.window.after(1000, self._take_screenshot_delayed)
        except Exception as e:
            self.window.deiconify()
            messagebox.showerror("Error", f"Failed to take screenshot: {e}")

    def _take_screenshot_delayed(self):
        """Take screenshot after delay"""
        try:
            self.preview_image = pyautogui.screenshot()
            self.screenshot_taken = True
            self.window.deiconify()  # Restore window

            # Update status
            self.screenshot_status.config(text="Screenshot ready ✓", foreground="green")
            self.screenshot_btn.config(text="📷 Retake Screenshot")

            messagebox.showinfo("Success", "Screenshot captured successfully!\nYou can now use Preview buttons to check regions.")

        except Exception as e:
            self.window.deiconify()  # Restore window even on error
            messagebox.showerror("Error", f"Failed to capture screenshot: {e}")

    def preview_specific_region(self, region_key):
        """Preview a specific region"""
        if not self.screenshot_taken:
            messagebox.showwarning("Warning", "Please take a screenshot first.")
            return

        try:
            coords = []
            for i in range(4):
                value = self.region_vars[region_key][i].get().strip()
                if not value:
                    messagebox.showerror("Error", f"Please fill in all coordinates for {region_key}")
                    return
                coords.append(int(value))

            self.show_region_preview(coords, region_key)

        except ValueError:
            messagebox.showerror("Error", f"Invalid coordinates for {region_key}. Please enter numbers only.")
        except Exception as e:
            messagebox.showerror("Error", f"Error previewing {region_key}: {e}")

    def preview_stat_region(self, stat_key):
        """Preview a stat region"""
        if not self.screenshot_taken:
            messagebox.showwarning("Warning", "Please take a screenshot first.")
            return

        try:
            key = f"STAT_{stat_key.upper()}"
            coords = []
            for i in range(4):
                value = self.region_vars[key][i].get().strip()
                if not value:
                    messagebox.showerror("Error", f"Please fill in all coordinates for {stat_key} stat")
                    return
                coords.append(int(value))

            self.show_region_preview(coords, f"{stat_key.upper()} Stat")

        except ValueError:
            messagebox.showerror("Error", f"Invalid coordinates for {stat_key} stat. Please enter numbers only.")
        except Exception as e:
            messagebox.showerror("Error", f"Error previewing {stat_key} stat: {e}")

    def show_region_preview(self, coords, title):
        """Show preview of a region"""
        try:
            # Special handling for Energy Bar
            if title == "ENERGY_BAR":
                x1, y1, x2, y2 = coords
                # Convert to standard x, y, width, height format for preview
                # Add height padding for energy bar (default 13 pixels above and below)
                height_padding = 13
                x = min(x1, x2)
                y = min(y1, y2) - height_padding
                width = abs(x2 - x1)
                height = abs(y2 - y1) + (height_padding * 2)
                coords = (x, y, width, height)

            x, y, width, height = coords

            # Validate coordinates
            if x < 0 or y < 0 or width <= 0 or height <= 0:
                messagebox.showerror("Error", "Invalid coordinates. X, Y must be >= 0 and Width, Height must be > 0.")
                return

            # Check if coordinates are within screen bounds
            screen_width, screen_height = self.preview_image.size
            if x >= screen_width or y >= screen_height:
                messagebox.showerror("Error", f"Starting coordinates are outside screen bounds ({screen_width}x{screen_height})")
                return

            if x + width > screen_width or y + height > screen_height:
                response = messagebox.askyesno("Warning",
                                               f"Region extends beyond screen bounds ({screen_width}x{screen_height}).\n" +
                                               f"Region end: X={x+width}, Y={y+height}\n\n" +
                                               "Preview what's visible?")
                if not response:
                    return

                # Adjust to screen bounds
                width = min(width, screen_width - x)
                height = min(height, screen_height - y)

            # Crop the region from screenshot
            cropped = self.preview_image.crop((x, y, x + width, y + height))

            # Create preview window
            self.create_preview_window(cropped, title, coords)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to preview region: {e}")

    def create_preview_window(self, image, title, coords):
        """Create a preview window for the region"""
        if title == "ENERGY_BAR":
            # For energy bar, show original coordinates in title
            x1, y1, x2, y2 = coords[:4] if len(coords) >= 4 else coords
            coord_info = f"Energy Bar: ({x1}, {y1}) to ({x2}, {y2}) + padding"
        else:
            x, y, width, height = coords
            coord_info = f"Region: ({x}, {y}) Size: {width}×{height}"

        # Calculate display size (max 600x400)
        max_width, max_height = 600, 400
        display_width, display_height = image.size

        if display_width > max_width or display_height > max_height:
            ratio = min(max_width / display_width, max_height / display_height)
            new_width = int(display_width * ratio)
            new_height = int(display_height * ratio)
            display_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        else:
            display_image = image

        # Create preview window
        preview_window = tk.Toplevel(self.window)
        preview_window.title(f"Preview: {title}")
        preview_window.resizable(False, False)
        preview_window.attributes('-topmost', True)

        # Main frame
        main_frame = ttk.Frame(preview_window, padding="10")
        main_frame.pack()

        # Title and info
        title_label = ttk.Label(main_frame, text=title, font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 5))

        info_label = ttk.Label(main_frame, text=coord_info, font=("Arial", 9))
        info_label.pack(pady=(0, 10))

        # Image
        photo = ImageTk.PhotoImage(display_image)
        image_label = ttk.Label(main_frame, image=photo)
        image_label.pack(pady=(0, 10))
        image_label.image = photo  # Keep reference

        # Close button
        ttk.Button(main_frame, text="Close",
                   command=preview_window.destroy).pack()

        # Center preview window
        preview_window.update_idletasks()
        pw_width = preview_window.winfo_width()
        pw_height = preview_window.winfo_height()
        px = (preview_window.winfo_screenwidth() // 2) - (pw_width // 2)
        py = (preview_window.winfo_screenheight() // 2) - (pw_height // 2)
        preview_window.geometry(f"{pw_width}x{pw_height}+{px}+{py}")

    def test_regions(self):
        """Test all regions by attempting OCR"""
        regions = self.get_region_values()
        if not regions:
            return

        # Clear previous results
        self.test_result_text.configure(state='normal')
        self.test_result_text.delete(1.0, tk.END)
        self.test_result_text.insert(tk.END, "Testing regions...\n\n")
        self.test_result_text.update()

        try:
            # Update regions temporarily for testing
            from utils.constants import update_regions
            update_regions(regions)

            results = []

            # Test mood detection
            try:
                from core.state import check_mood
                mood = check_mood()
                results.append(f"✅ Mood Detection: {mood}")
            except Exception as e:
                results.append(f"❌ Mood Detection: Error - {str(e)[:50]}...")

            # Test energy detection
            try:
                from core.state import check_energy_percentage
                energy = check_energy_percentage()
                results.append(f"✅ Energy Detection: {energy}%")
            except Exception as e:
                results.append(f"❌ Energy Detection: Error - {str(e)[:50]}...")

            # Test stat detection
            try:
                from core.state import stat_state
                stats = stat_state()
                results.append(f"✅ Stat Detection: {stats}")
            except Exception as e:
                results.append(f"❌ Stat Detection: Error - {str(e)[:50]}...")

            # Test turn detection
            try:
                from core.state import check_turn
                turn = check_turn()
                results.append(f"✅ Turn Detection: {turn}")
            except Exception as e:
                results.append(f"❌ Turn Detection: Error - {str(e)[:50]}...")

            # Test year detection
            try:
                from core.state import check_current_year
                year = check_current_year()
                results.append(f"✅ Year Detection: {year}")
            except Exception as e:
                results.append(f"❌ Year Detection: Error - {str(e)[:50]}...")

            # Test event regions if they exist
            event_regions = regions.get('EVENT_REGIONS', {})
            if event_regions:
                try:
                    # Test event region detection
                    if 'EVENT_REGION' in event_regions:
                        results.append(f"✅ Event Region configured: {event_regions['EVENT_REGION']}")
                    if 'EVENT_NAME_REGION' in event_regions:
                        results.append(f"✅ Event Name Region configured: {event_regions['EVENT_NAME_REGION']}")
                except Exception as e:
                    results.append(f"❌ Event Region Test: Error - {str(e)[:50]}...")

            # Display results
            self.test_result_text.delete(1.0, tk.END)
            self.test_result_text.insert(tk.END, "Region Test Results:\n")
            self.test_result_text.insert(tk.END, "=" * 50 + "\n\n")

            for result in results:
                self.test_result_text.insert(tk.END, result + "\n")

            self.test_result_text.insert(tk.END, "\n" + "=" * 50 + "\n")

            # Count successes
            success_count = sum(1 for r in results if r.startswith("✅"))
            total_count = len(results)

            if success_count == total_count:
                self.test_result_text.insert(tk.END, f"🎉 All tests passed! ({success_count}/{total_count})\n")
            else:
                self.test_result_text.insert(tk.END, f"⚠️  {success_count}/{total_count} tests passed.\n")
                self.test_result_text.insert(tk.END, "Check failed regions and adjust coordinates.\n")

            self.test_result_text.configure(state='disabled')

        except Exception as e:
            self.test_result_text.delete(1.0, tk.END)
            self.test_result_text.insert(tk.END, f"Test failed with error: {e}\n")
            self.test_result_text.configure(state='disabled')
            messagebox.showerror("Error", f"Failed to test regions: {e}")

    def reset_to_defaults(self):
        """Reset all regions to default values"""
        if messagebox.askyesno("Confirm Reset",
                               "Reset all regions to default values?\n\nThis will overwrite all current settings."):
            try:
                # Load default values for main regions
                for key, coords in DEFAULT_REGIONS.items():
                    if key == 'STAT_REGIONS':
                        continue
                    if key == 'EVENT_REGIONS':
                        continue

                    if key in self.region_vars:
                        for i, value in enumerate(coords):
                            self.region_vars[key][i].set(str(value))

                # Load default stat regions
                default_stat_regions = DEFAULT_REGIONS.get('STAT_REGIONS', {})
                for stat, coords in default_stat_regions.items():
                    key = f"STAT_{stat.upper()}"
                    if key in self.region_vars:
                        for i, value in enumerate(coords):
                            self.region_vars[key][i].set(str(value))

                # Load default event regions (if they exist in defaults)
                default_event_regions = DEFAULT_REGIONS.get('EVENT_REGIONS', {
                    'EVENT_REGION': (160, 170, 300, 80),
                    'EVENT_NAME_REGION': (240, 200, 350, 45)
                })
                for event_key, coords in default_event_regions.items():
                    if event_key in self.region_vars:
                        for i, value in enumerate(coords):
                            self.region_vars[event_key][i].set(str(value))

                messagebox.showinfo("Success", "All regions have been reset to default values.")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to reset to defaults: {e}")

    def save_settings(self):
        """Save the current region settings"""
        regions = self.get_region_values()
        if not regions:
            return

        try:
            # Validate all regions have reasonable values
            for key, coords in regions.items():
                if key == 'STAT_REGIONS':
                    for stat, stat_coords in coords.items():
                        x, y, w, h = stat_coords
                        if w <= 0 or h <= 0:
                            raise ValueError(f"Invalid size for {stat} stat region: width and height must be positive")
                        if x < 0 or y < 0:
                            raise ValueError(f"Invalid position for {stat} stat region: coordinates must be non-negative")
                elif key == 'EVENT_REGIONS':
                    for event_key, event_coords in coords.items():
                        x, y, w, h = event_coords
                        if w <= 0 or h <= 0:
                            raise ValueError(f"Invalid size for {event_key}: width and height must be positive")
                        if x < 0 or y < 0:
                            raise ValueError(f"Invalid position for {event_key}: coordinates must be non-negative")
                else:
                    x, y, w, h = coords
                    if w <= 0 or h <= 0:
                        raise ValueError(f"Invalid size for {key}: width and height must be positive")
                    if x < 0 or y < 0:
                        raise ValueError(f"Invalid position for {key}: coordinates must be non-negative")

            # Save the regions
            from utils.constants import update_regions
            if update_regions(regions):
                messagebox.showinfo("Success",
                                    "Region settings saved successfully!\n\n" +
                                    "✅ Settings applied immediately\n" +
                                    "✅ Settings will persist on restart\n" +
                                    "✅ All OCR functions will use new regions")
                self.window.destroy()
            else:
                messagebox.showerror("Error", "Failed to save region settings to file.")

        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")

    def on_closing(self):
        """Handle window closing"""
        if messagebox.askyesno("Confirm Close", "Close without saving changes?"):
            self.window.destroy()