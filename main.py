import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import pygetwindow as gw
from datetime import datetime
import keyboard
import sys
import os
import json

from core.execute import set_log_callback, career_lobby
from core.race_manager import RaceManager, DateManager

class UmaAutoGUI:
  def __init__(self):
    self.root = tk.Tk()
    self.root.title("Uma Musume Auto Train")

    # Position window on the right half of screen
    screen_width = self.root.winfo_screenwidth()
    screen_height = self.root.winfo_screenheight()
    window_width = 600
    window_height = 750  # Increased height for energy display
    x = screen_width // 2
    y = (screen_height - window_height) // 2

    self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # Keep window always on top
    self.root.attributes('-topmost', True)

    # Variables
    self.is_running = False
    self.is_paused = False
    self.bot_thread = None

    # Race manager
    self.race_manager = RaceManager()

    # Race filter variables
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
      'g3': tk.BooleanVar(value=True),
      'op': tk.BooleanVar(value=False),
      'unknown': tk.BooleanVar(value=False)
    }

    # Setup GUI
    self.setup_gui()

    # Setup keyboard shortcuts
    self.setup_keyboard_shortcuts()

    # Set log callback for execute module
    set_log_callback(self.log_message)

    # Bind window close event
    self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # Load race filters from memory if exists
    self.load_race_filters()

  def setup_gui(self):
    # Main frame with scrollbar
    canvas = tk.Canvas(self.root)
    scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
      "<Configure>",
      lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    main_frame = ttk.Frame(scrollable_frame, padding="10")
    main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    # Configure grid weights
    main_frame.columnconfigure(1, weight=1)

    # Title
    title_label = ttk.Label(main_frame, text="Uma Musume Auto Train",
                            font=("Arial", 16, "bold"))
    title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))

    # Status frame
    status_frame = ttk.LabelFrame(main_frame, text="Status", padding="5")
    status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
    status_frame.columnconfigure(1, weight=1)

    # Status labels
    ttk.Label(status_frame, text="Bot Status:").grid(row=0, column=0, sticky=tk.W)
    self.status_label = ttk.Label(status_frame, text="Stopped", foreground="red")
    self.status_label.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))

    ttk.Label(status_frame, text="Game Window:").grid(row=1, column=0, sticky=tk.W)
    self.game_status_label = ttk.Label(status_frame, text="Not Found", foreground="red")
    self.game_status_label.grid(row=1, column=1, sticky=tk.W, padx=(5, 0))

    ttk.Label(status_frame, text="Current Date:").grid(row=2, column=0, sticky=tk.W)
    self.date_label = ttk.Label(status_frame, text="Unknown", foreground="blue")
    self.date_label.grid(row=2, column=1, sticky=tk.W, padx=(5, 0))

    # Energy status
    ttk.Label(status_frame, text="Energy:").grid(row=3, column=0, sticky=tk.W)
    self.energy_label = ttk.Label(status_frame, text="Unknown", foreground="blue")
    self.energy_label.grid(row=3, column=1, sticky=tk.W, padx=(5, 0))

    # Race Filter Frame
    filter_frame = ttk.LabelFrame(main_frame, text="Race Filters", padding="5")
    filter_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

    # Track filters
    track_frame = ttk.LabelFrame(filter_frame, text="Track Type", padding="5")
    track_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

    ttk.Checkbutton(track_frame, text="Turf", variable=self.track_filters['turf'],
                    command=self.save_race_filters).grid(row=0, column=0, sticky=tk.W)
    ttk.Checkbutton(track_frame, text="Dirt", variable=self.track_filters['dirt'],
                    command=self.save_race_filters).grid(row=1, column=0, sticky=tk.W)

    # Distance filters
    distance_frame = ttk.LabelFrame(filter_frame, text="Distance", padding="5")
    distance_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)

    ttk.Checkbutton(distance_frame, text="Sprint", variable=self.distance_filters['sprint'],
                    command=self.save_race_filters).grid(row=0, column=0, sticky=tk.W)
    ttk.Checkbutton(distance_frame, text="Mile", variable=self.distance_filters['mile'],
                    command=self.save_race_filters).grid(row=1, column=0, sticky=tk.W)
    ttk.Checkbutton(distance_frame, text="Medium", variable=self.distance_filters['medium'],
                    command=self.save_race_filters).grid(row=0, column=1, sticky=tk.W)
    ttk.Checkbutton(distance_frame, text="Long", variable=self.distance_filters['long'],
                    command=self.save_race_filters).grid(row=1, column=1, sticky=tk.W)

    # Grade filters
    grade_frame = ttk.LabelFrame(filter_frame, text="Grade", padding="5")
    grade_frame.grid(row=0, column=2, sticky=(tk.W, tk.E), padx=(5, 0))

    ttk.Checkbutton(grade_frame, text="G1", variable=self.grade_filters['g1'],
                    command=self.save_race_filters).grid(row=0, column=0, sticky=tk.W)
    ttk.Checkbutton(grade_frame, text="G2", variable=self.grade_filters['g2'],
                    command=self.save_race_filters).grid(row=1, column=0, sticky=tk.W)
    ttk.Checkbutton(grade_frame, text="G3", variable=self.grade_filters['g3'],
                    command=self.save_race_filters).grid(row=0, column=1, sticky=tk.W)
    ttk.Checkbutton(grade_frame, text="OP", variable=self.grade_filters['op'],
                    command=self.save_race_filters).grid(row=1, column=1, sticky=tk.W)
    ttk.Checkbutton(grade_frame, text="Unknown", variable=self.grade_filters['unknown'],
                    command=self.save_race_filters).grid(row=0, column=2, sticky=tk.W)

    # Control buttons frame
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
    button_frame.columnconfigure(0, weight=1)
    button_frame.columnconfigure(1, weight=1)
    button_frame.columnconfigure(2, weight=1)

    # Buttons
    self.start_button = ttk.Button(button_frame, text="Start (F1)",
                                   command=self.start_bot)
    self.start_button.grid(row=0, column=0, padx=(0, 5), sticky=(tk.W, tk.E))

    self.pause_button = ttk.Button(button_frame, text="Pause (F2)",
                                   command=self.pause_bot, state="disabled")
    self.pause_button.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))

    self.stop_button = ttk.Button(button_frame, text="Stop (F3)",
                                  command=self.stop_bot, state="disabled")
    self.stop_button.grid(row=0, column=2, padx=(5, 0), sticky=(tk.W, tk.E))

    # Log frame
    log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding="5")
    log_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
    log_frame.columnconfigure(0, weight=1)
    log_frame.rowconfigure(0, weight=1)

    # Log text area
    self.log_text = scrolledtext.ScrolledText(log_frame, height=12, width=70)
    self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    # Clear log button
    clear_button = ttk.Button(log_frame, text="Clear Log", command=self.clear_log)
    clear_button.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))

    # Keyboard shortcuts info
    shortcuts_frame = ttk.LabelFrame(main_frame, text="Keyboard Shortcuts", padding="5")
    shortcuts_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))

    shortcuts_text = ("F1: Start Bot | F2: Pause/Resume | F3: Stop Bot | ESC: Emergency Stop")
    ttk.Label(shortcuts_frame, text=shortcuts_text, font=("Arial", 9)).grid(row=0, column=0)

    # Pack canvas and scrollbar
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

  def setup_keyboard_shortcuts(self):
    """Setup global keyboard shortcuts"""
    try:
      keyboard.add_hotkey('f1', self.start_bot)
      keyboard.add_hotkey('f2', self.pause_bot)
      keyboard.add_hotkey('f3', self.stop_bot)
      keyboard.add_hotkey('esc', self.emergency_stop)
    except Exception as e:
      self.log_message(f"Warning: Could not setup keyboard shortcuts: {e}")

  def save_race_filters(self):
    """Save race filter settings to memory"""
    filters = {
      'track': {k: v.get() for k, v in self.track_filters.items()},
      'distance': {k: v.get() for k, v in self.distance_filters.items()},
      'grade': {k: v.get() for k, v in self.grade_filters.items()}
    }

    try:
      with open('race_filters.json', 'w') as f:
        json.dump(filters, f)

      # Update race manager with new filters
      self.race_manager.update_filters(filters)

    except Exception as e:
      self.log_message(f"Warning: Could not save race filters: {e}")

  def load_race_filters(self):
    """Load race filter settings from memory"""
    try:
      if os.path.exists('race_filters.json'):
        with open('race_filters.json', 'r') as f:
          filters = json.load(f)

        # Apply loaded filters
        for k, v in filters.get('track', {}).items():
          if k in self.track_filters:
            self.track_filters[k].set(v)

        for k, v in filters.get('distance', {}).items():
          if k in self.distance_filters:
            self.distance_filters[k].set(v)

        for k, v in filters.get('grade', {}).items():
          if k in self.grade_filters:
            self.grade_filters[k].set(v)

        # Update race manager
        self.race_manager.update_filters(filters)

    except Exception as e:
      self.log_message(f"Warning: Could not load race filters: {e}")

  def log_message(self, message):
    """Add message to log with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    formatted_message = f"[{timestamp}] {message}\n"

    # Update GUI in main thread
    self.root.after(0, self._update_log, formatted_message)

  def _update_log(self, message):
    """Update log text widget (must be called from main thread)"""
    self.log_text.insert(tk.END, message)
    self.log_text.see(tk.END)

  def clear_log(self):
    """Clear the log text"""
    self.log_text.delete(1.0, tk.END)

  def update_current_date(self, date_info):
    """Update current date display"""
    if date_info:
      if date_info.get('is_pre_debut', False):
        date_str = f"{date_info['year']} Year Pre-Debut (Day {date_info['absolute_day']}/72)"
      else:
        date_str = f"{date_info['year']} {date_info['month']} {date_info['period']} (Day {date_info['absolute_day']}/72)"
      self.root.after(0, lambda: self.date_label.config(text=date_str, foreground="blue"))
    else:
      self.root.after(0, lambda: self.date_label.config(text="Unknown", foreground="red"))

  def update_energy_display(self, energy_percentage):
    """Update energy display"""
    try:
      # Load energy thresholds from config
      with open('config.json', 'r') as f:
        config = json.load(f)
      minimum_energy = config.get('minimum_energy_percentage', 40)
      critical_energy = config.get('critical_energy_percentage', 15)

      # Determine color based on energy level
      if energy_percentage >= minimum_energy:
        color = "green"
      elif energy_percentage >= critical_energy:
        color = "orange"  # Low energy (15-40%)
      else:
        color = "red"     # Critical energy (<15%)

      energy_str = f"{energy_percentage}%"
      self.root.after(0, lambda: self.energy_label.config(text=energy_str, foreground=color))
    except Exception as e:
      self.root.after(0, lambda: self.energy_label.config(text="Error", foreground="red"))

  def check_game_window(self):
    """Check if Umamusume window is active"""
    try:
      windows = gw.getWindowsWithTitle("Umamusume")
      if windows:
        win = windows[0]
        is_active = win.isActive
        if is_active:
          self.root.after(0, self._update_game_status, "Active", "green")
          return True
        else:
          self.root.after(0, self._update_game_status, "Inactive", "orange")
          return False
      else:
        self.root.after(0, self._update_game_status, "Not Found", "red")
        return False
    except Exception as e:
      self.root.after(0, self._update_game_status, f"Error: {e}", "red")
      return False

  def _update_game_status(self, status, color):
    """Update game status label"""
    self.game_status_label.config(text=status, foreground=color)

  def focus_umamusume(self):
    """Focus Umamusume window"""
    try:
      windows = gw.getWindowsWithTitle("Umamusume")
      if not windows:
        raise Exception("Umamusume window not found.")

      win = windows[0]
      if win.isMinimized:
        win.restore()
      win.activate()
      win.maximize()
      time.sleep(0.5)
      return True
    except Exception as e:
      self.log_message(f"Error focusing game window: {e}")
      return False

  def start_bot(self):
    """Start the bot"""
    if self.is_running:
      return

    if not self.focus_umamusume():
      self.log_message("Cannot start bot: Game window not found or cannot be focused")
      return

    self.is_running = True
    self.is_paused = False

    # Update UI
    self.start_button.config(state="disabled")
    self.pause_button.config(state="normal")
    self.stop_button.config(state="normal")
    self.status_label.config(text="Running", foreground="green")

    # Start bot thread
    self.bot_thread = threading.Thread(target=self.bot_loop, daemon=True)
    self.bot_thread.start()

    self.log_message("Bot started successfully!")

  def pause_bot(self):
    """Pause/Resume the bot"""
    if not self.is_running:
      return

    self.is_paused = not self.is_paused

    if self.is_paused:
      self.pause_button.config(text="Resume (F2)")
      self.status_label.config(text="Paused", foreground="orange")
      self.log_message("Bot paused")
    else:
      self.pause_button.config(text="Pause (F2)")
      self.status_label.config(text="Running", foreground="green")
      self.log_message("Bot resumed")

  def stop_bot(self):
    """Stop the bot"""
    if not self.is_running:
      return

    self.is_running = False
    self.is_paused = False

    # Update UI
    self.start_button.config(state="normal")
    self.pause_button.config(state="disabled", text="Pause (F2)")
    self.stop_button.config(state="disabled")
    self.status_label.config(text="Stopped", foreground="red")

    self.log_message("Bot stopped")

  def emergency_stop(self):
    """Emergency stop - can be called from anywhere"""
    self.root.after(0, self.stop_bot)
    self.root.after(0, lambda: self.log_message("EMERGENCY STOP ACTIVATED!"))

  def bot_loop(self):
    """Main bot loop running in separate thread"""
    try:
      # Use the modified career_lobby with pause/stop support
      self.modified_career_lobby()
    except Exception as e:
      self.log_message(f"Bot error: {e}")
    finally:
      # Ensure UI is updated when bot stops
      self.root.after(0, self.stop_bot)

  def modified_career_lobby(self):
    """Modified career_lobby that respects GUI controls"""
    # Simply call the career_lobby function with GUI instance
    career_lobby(self)

  def on_closing(self):
    """Handle window close event"""
    self.stop_bot()
    try:
      keyboard.unhook_all()
    except:
      pass
    self.root.destroy()

  def run(self):
    """Start the GUI"""
    self.log_message("Uma Musume Auto Train started!")
    self.log_message("Configure race filters and make sure the game window is active before starting.")
    self.log_message("Use F1 to start, F2 to pause/resume, F3 to stop, ESC for emergency stop.")
    self.root.mainloop()

def main():
  """Main function - create and run GUI"""
  print("Uma Auto - Enhanced GUI Version!")
  app = UmaAutoGUI()
  app.run()

if __name__ == "__main__":
  main()