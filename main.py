import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
import pygetwindow as gw
from datetime import datetime
import keyboard
import sys
import os

from core.execute import set_log_callback, career_lobby

class UmaAutoGUI:
  def __init__(self):
    self.root = tk.Tk()
    self.root.title("Uma Musume Auto Train")
    self.root.geometry("600x500")

    # Keep window always on top
    self.root.attributes('-topmost', True)

    # Variables
    self.is_running = False
    self.is_paused = False
    self.bot_thread = None

    # Setup GUI
    self.setup_gui()

    # Setup keyboard shortcuts
    self.setup_keyboard_shortcuts()

    # Set log callback for execute module
    set_log_callback(self.log_message)

    # Bind window close event
    self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

  def setup_gui(self):
    # Main frame
    main_frame = ttk.Frame(self.root, padding="10")
    main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    # Configure grid weights
    self.root.columnconfigure(0, weight=1)
    self.root.rowconfigure(0, weight=1)
    main_frame.columnconfigure(1, weight=1)
    main_frame.rowconfigure(2, weight=1)

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

    # Control buttons frame
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
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
    log_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
    log_frame.columnconfigure(0, weight=1)
    log_frame.rowconfigure(0, weight=1)

    # Log text area
    self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=70)
    self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    # Clear log button
    clear_button = ttk.Button(log_frame, text="Clear Log", command=self.clear_log)
    clear_button.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))

    # Keyboard shortcuts info
    shortcuts_frame = ttk.LabelFrame(main_frame, text="Keyboard Shortcuts", padding="5")
    shortcuts_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))

    shortcuts_text = ("F1: Start Bot | F2: Pause/Resume | F3: Stop Bot | ESC: Emergency Stop")
    ttk.Label(shortcuts_frame, text=shortcuts_text, font=("Arial", 9)).grid(row=0, column=0)

  def setup_keyboard_shortcuts(self):
    """Setup global keyboard shortcuts"""
    try:
      keyboard.add_hotkey('f1', self.start_bot)
      keyboard.add_hotkey('f2', self.pause_bot)
      keyboard.add_hotkey('f3', self.stop_bot)
      keyboard.add_hotkey('esc', self.emergency_stop)
    except Exception as e:
      self.log_message(f"Warning: Could not setup keyboard shortcuts: {e}")

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
    self.log_message("Make sure the game window is active before starting the bot.")
    self.log_message("Use F1 to start, F2 to pause/resume, F3 to stop, ESC for emergency stop.")
    self.root.mainloop()

def main():
  """Main function - create and run GUI"""
  print("Uma Auto - GUI Version!")
  app = UmaAutoGUI()
  app.run()

if __name__ == "__main__":
  main()