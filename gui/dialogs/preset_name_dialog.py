import tkinter as tk
from tkinter import ttk, messagebox


class PresetNameDialog:
    """Dialog for editing preset names"""

    def __init__(self, parent, current_name, callback=None):
        self.parent = parent
        self.current_name = current_name
        self.callback = callback
        self.new_name = None

        # Create dialog window
        self.window = tk.Toplevel(parent)
        self.window.title("Edit Preset Name")
        self.window.geometry("400x150")
        self.window.resizable(False, False)

        # Make modal
        self.window.transient(parent)
        self.window.grab_set()

        # Setup UI
        self._setup_ui()

        # Center window
        self._center_window()

        # Bind events
        self.window.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.name_entry.bind('<Return>', lambda e: self._on_save())

        # Focus on entry
        self.name_entry.focus_set()
        self.name_entry.select_range(0, tk.END)

    def _setup_ui(self):
        """Setup dialog UI"""
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Edit Preset Name",
            font=("Arial", 12, "bold")
        )
        title_label.pack(pady=(0, 15))

        # Name entry frame
        entry_frame = ttk.Frame(main_frame)
        entry_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(entry_frame, text="Name:").pack(side=tk.LEFT, padx=(0, 10))

        self.name_var = tk.StringVar(value=self.current_name)
        self.name_entry = ttk.Entry(entry_frame, textvariable=self.name_var, width=30)
        self.name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        # Cancel button
        cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel
        )
        cancel_button.pack(side=tk.RIGHT, padx=(5, 0))

        # Save button
        save_button = ttk.Button(
            button_frame,
            text="Save",
            command=self._on_save
        )
        save_button.pack(side=tk.RIGHT)

    def _on_save(self):
        """Handle save button"""
        new_name = self.name_var.get().strip()

        if not new_name:
            messagebox.showerror("Error", "Preset name cannot be empty", parent=self.window)
            return

        if len(new_name) > 50:
            messagebox.showerror("Error", "Preset name is too long (max 50 characters)", parent=self.window)
            return

        self.new_name = new_name

        if self.callback:
            self.callback(self.new_name)

        self.window.destroy()

    def _on_cancel(self):
        """Handle cancel"""
        self.window.destroy()

    def _center_window(self):
        """Center window on screen"""
        self.window.update_idletasks()

        width = self.window.winfo_width()
        height = self.window.winfo_height()

        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2

        self.window.geometry(f"{width}x{height}+{x}+{y}")
