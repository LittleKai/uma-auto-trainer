import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import threading
import time


class WindowManager:
    """Manages window settings, positioning, and region configuration"""

    def __init__(self, root):
        self.root = root

        # Default window settings
        self.window_settings = {
            'width': 700,
            'height': 900,
            'x': 100,
            'y': 20
        }

        # Load initial window settings
        self.load_window_settings()

        # Region settings variables
        self.region_vars = {}
        self.region_thread = None
        self.region_monitoring = False

    def load_window_settings(self):
        """Load window settings from file"""
        try:
            if os.path.exists('bot_settings.json'):
                with open('bot_settings.json', 'r') as f:
                    settings = json.load(f)

                if 'window' in settings:
                    self.window_settings.update(settings['window'])

        except Exception as e:
            print(f"Warning: Could not load window settings: {e}")

    def setup_window(self):
        """Setup window size, position and properties"""
        # Configure window
        self.root.geometry(f"{self.window_settings['width']}x{self.window_settings['height']}+"
                           f"{self.window_settings['x']}+{self.window_settings['y']}")

        # Set minimum size
        self.root.minsize(600, 700)

        # Configure styles
        self.setup_styles()

        # Set icon if available
        self.set_window_icon()

    def setup_styles(self):
        """Setup custom styles for the GUI"""
        style = ttk.Style()

        # Configure accent button style
        style.configure(
            "Accent.TButton",
            font=("Arial", 10, "bold")
        )

    def set_window_icon(self):
        """Set window icon if available"""
        try:
            if os.path.exists("assets/icon.ico"):
                self.root.iconbitmap("assets/icon.ico")
        except Exception:
            pass

    def on_window_configure(self, event):
        """Handle window resize/move events"""
        # Only save if it's the root window being configured
        if event.widget == self.root:
            # Debounce the saving by using after_idle
            self.root.after_idle(self.save_window_position)

    def save_window_position(self):
        """Save current window position and size"""
        try:
            # Update window settings
            self.window_settings['width'] = self.root.winfo_width()
            self.window_settings['height'] = self.root.winfo_height()
            self.window_settings['x'] = self.root.winfo_x()
            self.window_settings['y'] = self.root.winfo_y()

        except Exception as e:
            print(f"Warning: Could not save window position: {e}")

    def get_window_settings(self):
        """Get current window settings"""
        # Update with current position/size before returning
        try:
            self.window_settings['width'] = self.root.winfo_width()
            self.window_settings['height'] = self.root.winfo_height()
            self.window_settings['x'] = self.root.winfo_x()
            self.window_settings['y'] = self.root.winfo_y()
        except Exception:
            pass

        return self.window_settings.copy()

    def create_region_tab(self, notebook, main_window):
        """Create region settings tab"""
        region_frame = ttk.Frame(notebook)
        region_frame.columnconfigure(0, weight=1)

        # Load region settings
        self.load_region_settings()

        # Create region UI
        self.create_region_ui(region_frame, main_window)

        return region_frame

    def load_region_settings(self):
        """Load region settings from file"""
        self.region_vars = {}

        try:
            if os.path.exists('region_settings.json'):
                with open('region_settings.json', 'r') as f:
                    settings = json.load(f)

                # Initialize StringVar for each region
                for region_name, coords in settings.items():
                    self.region_vars[region_name] = {
                        'x': tk.StringVar(value=str(coords.get('x', 0))),
                        'y': tk.StringVar(value=str(coords.get('y', 0))),
                        'width': tk.StringVar(value=str(coords.get('width', 100))),
                        'height': tk.StringVar(value=str(coords.get('height', 50)))
                    }
        except Exception as e:
            print(f"Warning: Could not load region settings: {e}")

        # Ensure we have default regions
        self.ensure_default_regions()

    def ensure_default_regions(self):
        """Ensure default regions exist"""
        default_regions = {
            'date_region': {'x': 100, 'y': 100, 'width': 200, 'height': 50},
            'mood_region': {'x': 300, 'y': 100, 'width': 150, 'height': 40},
            'energy_region': {'x': 500, 'y': 100, 'width': 100, 'height': 30},
            'training_region': {'x': 200, 'y': 200, 'width': 400, 'height': 300},
            'race_region': {'x': 150, 'y': 150, 'width': 350, 'height': 200}
        }

        for region_name, default_coords in default_regions.items():
            if region_name not in self.region_vars:
                self.region_vars[region_name] = {
                    'x': tk.StringVar(value=str(default_coords['x'])),
                    'y': tk.StringVar(value=str(default_coords['y'])),
                    'width': tk.StringVar(value=str(default_coords['width'])),
                    'height': tk.StringVar(value=str(default_coords['height']))
                }

    def create_region_ui(self, parent, main_window):
        """Create region settings UI"""
        # Instructions
        instruction_frame = ttk.LabelFrame(parent, text="Instructions", padding="10")
        instruction_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        instruction_frame.columnconfigure(0, weight=1)

        instructions = (
            "Configure OCR detection regions for accurate game state recognition.\n"
            "Use 'Start Position Monitor' to automatically detect regions by moving your mouse.\n"
            "Manually adjust coordinates if automatic detection fails."
        )

        ttk.Label(
            instruction_frame,
            text=instructions,
            wraplength=600,
            justify=tk.LEFT
        ).grid(row=0, column=0, sticky=(tk.W, tk.E))

        # Region configuration
        config_frame = ttk.LabelFrame(parent, text="Region Configuration", padding="10")
        config_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        config_frame.columnconfigure(0, weight=1)

        # Create region entries
        self.create_region_entries(config_frame)

        # Control buttons
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)

        # Position monitor button
        self.monitor_button = ttk.Button(
            button_frame,
            text="Start Position Monitor",
            command=self.toggle_position_monitor
        )
        self.monitor_button.grid(row=0, column=0, padx=(0, 5), sticky=(tk.W, tk.E))

        # Save button
        ttk.Button(
            button_frame,
            text="Save Regions",
            command=self.save_region_settings
        ).grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))

        # Reset button
        ttk.Button(
            button_frame,
            text="Reset to Defaults",
            command=self.reset_to_defaults
        ).grid(row=0, column=2, padx=(5, 0), sticky=(tk.W, tk.E))

        # Status label
        self.region_status_label = ttk.Label(parent, text="Ready", foreground="blue")
        self.region_status_label.grid(row=3, column=0, pady=(10, 0))

    def create_region_entries(self, parent):
        """Create input fields for region coordinates"""
        # Headers
        headers = ["Region", "X", "Y", "Width", "Height"]
        for i, header in enumerate(headers):
            ttk.Label(parent, text=header, font=("Arial", 10, "bold")).grid(
                row=0, column=i, padx=5, pady=5, sticky=tk.W
            )

        row = 1
        for region_name, vars_dict in self.region_vars.items():
            # Region name
            display_name = region_name.replace('_', ' ').title()
            ttk.Label(parent, text=display_name).grid(
                row=row, column=0, padx=5, pady=2, sticky=tk.W
            )

            # Coordinate entries
            for i, coord in enumerate(['x', 'y', 'width', 'height']):
                entry = ttk.Entry(parent, textvariable=vars_dict[coord], width=8)
                entry.grid(row=row, column=i+1, padx=5, pady=2)

            row += 1

    def toggle_position_monitor(self):
        """Toggle position monitoring for region detection"""
        if not self.region_monitoring:
            self.start_position_monitor()
        else:
            self.stop_position_monitor()

    def start_position_monitor(self):
        """Start position monitoring thread"""
        self.region_monitoring = True
        self.monitor_button.config(text="Stop Position Monitor")
        self.region_status_label.config(text="Monitoring mouse position...", foreground="green")

        self.region_thread = threading.Thread(target=self.position_monitor_worker, daemon=True)
        self.region_thread.start()

    def stop_position_monitor(self):
        """Stop position monitoring"""
        self.region_monitoring = False
        self.monitor_button.config(text="Start Position Monitor")
        self.region_status_label.config(text="Monitoring stopped", foreground="blue")

    def position_monitor_worker(self):
        """Worker thread for position monitoring"""
        try:
            import pyautogui

            while self.region_monitoring:
                try:
                    x, y = pyautogui.position()

                    # Update status in main thread
                    self.root.after(0, lambda: self.region_status_label.config(
                        text=f"Mouse position: X={x}, Y={y}",
                        foreground="green"
                    ))

                    time.sleep(0.1)

                except Exception as e:
                    self.root.after(0, lambda: self.region_status_label.config(
                        text=f"Monitor error: {e}",
                        foreground="red"
                    ))
                    break

        except ImportError:
            self.root.after(0, lambda: self.region_status_label.config(
                text="PyAutoGUI not available for position monitoring",
                foreground="red"
            ))
        except Exception as e:
            self.root.after(0, lambda: self.region_status_label.config(
                text=f"Position monitor error: {e}",
                foreground="red"
            ))

    def save_region_settings(self):
        """Save current region settings to file"""
        try:
            settings = {}

            for region_name, vars_dict in self.region_vars.items():
                settings[region_name] = {
                    'x': int(vars_dict['x'].get()),
                    'y': int(vars_dict['y'].get()),
                    'width': int(vars_dict['width'].get()),
                    'height': int(vars_dict['height'].get())
                }

            with open('region_settings.json', 'w') as f:
                json.dump(settings, f, indent=2)

            self.region_status_label.config(text="Region settings saved!", foreground="green")

            # Auto-clear status after 3 seconds
            self.root.after(3000, lambda: self.region_status_label.config(
                text="Ready", foreground="blue"
            ))

        except ValueError as e:
            messagebox.showerror("Invalid Input", "Please enter valid numeric values for coordinates.")
            self.region_status_label.config(text="Save failed - invalid input", foreground="red")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save region settings: {e}")
            self.region_status_label.config(text="Save failed", foreground="red")

    def reset_to_defaults(self):
        """Reset all regions to default values"""
        if messagebox.askyesno("Confirm Reset", "Reset all regions to default values?"):
            default_regions = {
                'date_region': {'x': 100, 'y': 100, 'width': 200, 'height': 50},
                'mood_region': {'x': 300, 'y': 100, 'width': 150, 'height': 40},
                'energy_region': {'x': 500, 'y': 100, 'width': 100, 'height': 30},
                'training_region': {'x': 200, 'y': 200, 'width': 400, 'height': 300},
                'race_region': {'x': 150, 'y': 150, 'width': 350, 'height': 200}
            }

            for region_name, coords in default_regions.items():
                if region_name in self.region_vars:
                    self.region_vars[region_name]['x'].set(str(coords['x']))
                    self.region_vars[region_name]['y'].set(str(coords['y']))
                    self.region_vars[region_name]['width'].set(str(coords['width']))
                    self.region_vars[region_name]['height'].set(str(coords['height']))

            self.region_status_label.config(text="Reset to defaults", foreground="green")

    def get_region_settings(self):
        """Get current region settings as dictionary"""
        settings = {}

        try:
            for region_name, vars_dict in self.region_vars.items():
                settings[region_name] = {
                    'x': int(vars_dict['x'].get()),
                    'y': int(vars_dict['y'].get()),
                    'width': int(vars_dict['width'].get()),
                    'height': int(vars_dict['height'].get())
                }
        except ValueError:
            # Return empty dict if invalid values
            return {}

        return settings

    def validate_region_settings(self):
        """Validate that all region settings have valid numeric values"""
        try:
            for region_name, vars_dict in self.region_vars.items():
                for coord in ['x', 'y', 'width', 'height']:
                    int(vars_dict[coord].get())
            return True
        except ValueError:
            return False

    def cleanup(self):
        """Cleanup resources when window manager is destroyed"""
        if self.region_monitoring:
            self.stop_position_monitor()

        if self.region_thread and self.region_thread.is_alive():
            self.region_monitoring = False
            self.region_thread.join(timeout=1.0)