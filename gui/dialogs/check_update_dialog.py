"""
Check Update Dialog for Uma Musume Auto Train.
Provides access to app update check, event map update check,
auto-check toggle, and donate link.
"""

import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import webbrowser

from version import APP_VERSION

KOFI_URL = "https://ko-fi.com/LittleKai"


class CheckUpdateDialog:
    """Dialog with update check options and auto-check toggle."""

    SETTINGS_FILE = "bot_settings.json"

    def __init__(self, parent, on_app_update_found, on_event_update_found):
        self.parent = parent
        self.on_app_update_found = on_app_update_found
        self.on_event_update_found = on_event_update_found
        self.checking = False

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Uma Auto Train")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)

        self._setup_ui()
        self._center_window()

    def _load_auto_check_setting(self):
        try:
            if os.path.exists(self.SETTINGS_FILE):
                with open(self.SETTINGS_FILE, "r") as f:
                    settings = json.load(f)
                return settings.get("auto_check_update", True)
        except (json.JSONDecodeError, OSError):
            pass
        return True

    def _save_auto_check_setting(self, enabled):
        try:
            settings = {}
            if os.path.exists(self.SETTINGS_FILE):
                with open(self.SETTINGS_FILE, "r") as f:
                    settings = json.load(f)
            settings["auto_check_update"] = enabled
            with open(self.SETTINGS_FILE, "w") as f:
                json.dump(settings, f, indent=2)
        except (json.JSONDecodeError, OSError):
            pass

    def _setup_ui(self):
        main_frame = ttk.Frame(self.dialog, padding=(24, 16, 24, 20))
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ── Header: App name + version ──
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(
            header_frame,
            text="Uma Musume Auto Train",
            font=("Arial", 13, "bold"),
        ).pack(side=tk.LEFT)

        ttk.Label(
            header_frame,
            text=f"v{APP_VERSION}",
            font=("Arial", 10),
            foreground="#888888",
        ).pack(side=tk.LEFT, padx=(8, 0), pady=(3, 0))

        # ── Separator ──
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 14))

        # ── Update section ──
        update_frame = ttk.LabelFrame(main_frame, text="Updates", padding=(12, 8, 12, 10))
        update_frame.pack(fill=tk.X, pady=(0, 10))
        update_frame.columnconfigure(1, weight=1)

        # App update row
        ttk.Label(
            update_frame,
            text="App version:",
            font=("Arial", 10),
        ).grid(row=0, column=0, sticky=tk.W, padx=(0, 10), pady=(0, 6))

        self.check_update_btn = ttk.Button(
            update_frame,
            text="Check Update",
            command=self._check_app_update,
            width=16,
        )
        self.check_update_btn.grid(row=0, column=1, sticky=tk.E, pady=(0, 6))

        # Event update row
        ttk.Label(
            update_frame,
            text="Event maps:",
            font=("Arial", 10),
        ).grid(row=1, column=0, sticky=tk.W, padx=(0, 10))

        self.check_event_btn = ttk.Button(
            update_frame,
            text="Check Events",
            command=self._check_event_updates,
            width=16,
        )
        self.check_event_btn.grid(row=1, column=1, sticky=tk.E)

        # Status label (shown when checking)
        self.status_label = ttk.Label(update_frame, text="", font=("Arial", 9), foreground="#666666")

        # ── Settings section ──
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding=(12, 6, 12, 8))
        settings_frame.pack(fill=tk.X, pady=(0, 10))

        self.auto_check_var = tk.BooleanVar(value=self._load_auto_check_setting())
        ttk.Checkbutton(
            settings_frame,
            text="Auto check update on startup",
            variable=self.auto_check_var,
            command=self._on_auto_check_toggle,
        ).pack(anchor=tk.W)

        # ── Support section ──
        support_frame = ttk.Frame(main_frame)
        support_frame.pack(fill=tk.X, pady=(4, 0))

        donate_btn = tk.Button(
            support_frame,
            text="Buy me a coffee",
            font=("Arial", 10, "bold"),
            fg="white",
            bg="#FF5E5B",
            activeforeground="white",
            activebackground="#E04440",
            cursor="hand2",
            relief=tk.FLAT,
            padx=14,
            pady=5,
            command=lambda: webbrowser.open(KOFI_URL),
        )
        donate_btn.pack(side=tk.LEFT)

        ttk.Label(
            support_frame,
            text="Support development",
            font=("Arial", 9),
            foreground="#999999",
        ).pack(side=tk.LEFT, padx=(8, 0))

    def _center_window(self):
        self.dialog.update_idletasks()
        w = self.dialog.winfo_width()
        h = self.dialog.winfo_height()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - w) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - h) // 2
        self.dialog.geometry(f"+{x}+{y}")

    def _on_auto_check_toggle(self):
        self._save_auto_check_setting(self.auto_check_var.get())

    def _set_checking(self, checking, status_text=""):
        self.checking = checking
        state = tk.DISABLED if checking else tk.NORMAL
        self.check_update_btn.config(state=state)
        self.check_event_btn.config(state=state)

        if status_text:
            self.status_label.config(text=status_text)
            self.status_label.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(8, 0))
        else:
            self.status_label.grid_forget()

    def _check_app_update(self):
        if self.checking:
            return
        self._set_checking(True, "Checking for app update...")

        def check_thread():
            from core.updater import check_for_update
            result = check_for_update()
            self.dialog.after(0, self._on_app_update_result, result)

        threading.Thread(target=check_thread, daemon=True).start()

    def _on_app_update_result(self, result):
        self._set_checking(False)
        if result.get("has_update"):
            self.dialog.destroy()
            self.on_app_update_found(result)
        else:
            messagebox.showinfo(
                "No Update",
                f"You are running the latest version (v{APP_VERSION}).",
                parent=self.dialog,
            )

    def _check_event_updates(self):
        if self.checking:
            return
        self._set_checking(True, "Checking for event updates...")

        def check_thread():
            from core.updater import check_event_updates
            result = check_event_updates()
            self.dialog.after(0, self._on_event_update_result, result)

        threading.Thread(target=check_thread, daemon=True).start()

    def _on_event_update_result(self, result):
        self._set_checking(False)
        if result.get("has_updates"):
            self.dialog.destroy()
            self.on_event_update_found(result)
        elif result.get("error"):
            messagebox.showwarning(
                "Event Update",
                f"Could not check for updates:\n{result['error']}",
                parent=self.dialog,
            )
        else:
            messagebox.showinfo(
                "Event Update",
                "All event maps are up to date.",
                parent=self.dialog,
            )
