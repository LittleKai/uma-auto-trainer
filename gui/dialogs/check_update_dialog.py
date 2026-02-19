"""
Check Update Dialog for Uma Musume Auto Train.
Provides access to app update check, event map update check,
and auto-check toggle setting.
"""

import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading

from version import APP_VERSION


class CheckUpdateDialog:
    """Dialog with update check options and auto-check toggle."""

    SETTINGS_FILE = "bot_settings.json"

    def __init__(self, parent, on_app_update_found, on_event_update_found):
        """
        Args:
            parent: Parent tkinter window
            on_app_update_found: callback(update_info) when app update is found
            on_event_update_found: callback(update_result) when event updates are found
        """
        self.parent = parent
        self.on_app_update_found = on_app_update_found
        self.on_event_update_found = on_event_update_found
        self.checking = False

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Check Update")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)

        self._setup_ui()
        self._center_window()

    def _load_auto_check_setting(self):
        """Load auto-check setting from bot_settings.json."""
        try:
            if os.path.exists(self.SETTINGS_FILE):
                with open(self.SETTINGS_FILE, "r") as f:
                    settings = json.load(f)
                return settings.get("auto_check_update", True)
        except (json.JSONDecodeError, OSError):
            pass
        return True

    def _save_auto_check_setting(self, enabled):
        """Save auto-check setting to bot_settings.json."""
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
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Auto-check toggle
        self.auto_check_var = tk.BooleanVar(value=self._load_auto_check_setting())
        auto_check_cb = ttk.Checkbutton(
            main_frame,
            text="Auto check update on startup",
            variable=self.auto_check_var,
            command=self._on_auto_check_toggle,
        )
        auto_check_cb.pack(anchor=tk.W, pady=(0, 15))

        # Buttons frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)

        self.check_update_btn = ttk.Button(
            btn_frame,
            text="Check Update",
            command=self._check_app_update,
        )
        self.check_update_btn.grid(row=0, column=0, padx=(0, 5), sticky=tk.W + tk.E, ipady=4)

        self.check_event_btn = ttk.Button(
            btn_frame,
            text="Check Events",
            command=self._check_event_updates,
        )
        self.check_event_btn.grid(row=0, column=1, padx=(5, 0), sticky=tk.W + tk.E, ipady=4)

        # Status label (hidden initially)
        self.status_label = ttk.Label(main_frame, text="", font=("Arial", 9))

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
            self.status_label.pack(anchor=tk.W, pady=(10, 0))
        else:
            self.status_label.pack_forget()

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
