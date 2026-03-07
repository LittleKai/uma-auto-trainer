import tkinter as tk
from tkinter import ttk


class FriendEventsWindow:
    """Window for configuring Friend Events automation settings"""

    def __init__(self, strategy_tab):
        self.strategy_tab = strategy_tab
        self.main_window = strategy_tab.main_window
        self.window = tk.Toplevel(self.main_window.root)
        self.window.title("Friend Events Configuration")
        self.window.resizable(False, False)

        self.window.attributes('-topmost', True)
        self.window.transient(self.main_window.root)
        self.window.grab_set()

        self.setup_ui()

        self.window.protocol("WM_DELETE_WINDOW", self.window.destroy)
        self.center_window()

    def setup_ui(self):
        main_frame = ttk.Frame(self.window, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Friend Events Configuration",
                  font=("Arial", 12, "bold")).pack(pady=(0, 10))

        ttk.Label(
            main_frame,
            text="Settings for Friend support card events.",
            font=("Arial", 9),
            justify=tk.CENTER,
            foreground="blue"
        ).pack(pady=(0, 15))

        # Placeholder - to be extended
        ttk.Label(
            main_frame,
            text="(No additional settings yet)",
            foreground="gray"
        ).pack(pady=10)

        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=15)

        ttk.Button(main_frame, text="Close", command=self.window.destroy).pack(side=tk.RIGHT)

    def center_window(self):
        self.window.update_idletasks()
        width = max(320, self.window.winfo_reqwidth() + 40)
        height = max(200, self.window.winfo_reqheight() + 40)
        parent_x = self.main_window.root.winfo_x()
        parent_y = self.main_window.root.winfo_y()
        parent_width = self.main_window.root.winfo_width()
        parent_height = self.main_window.root.winfo_height()
        x = parent_x + (parent_width // 2) - (width // 2)
        y = parent_y + (parent_height // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
