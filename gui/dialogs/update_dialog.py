"""
Update Dialog for Uma Musume Auto Train.
Shows update information and handles downloading/applying updates.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading

from version import APP_VERSION
from core.updater import download_update, apply_update


class UpdateDialog:
    """Dialog for displaying update information and managing the update process."""

    def __init__(self, parent, update_info):
        """
        Args:
            parent: Parent tkinter window
            update_info: dict from check_for_update() with update details
        """
        self.parent = parent
        self.update_info = update_info
        self.downloading = False

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Update Available")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)

        self._setup_ui()
        self._center_window()

    def _setup_ui(self):
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Version info
        version_frame = ttk.Frame(main_frame)
        version_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(version_frame, text="A new version is available!",
                  font=("Arial", 12, "bold")).pack(anchor=tk.W)

        ttk.Label(version_frame,
                  text=f"Current version: v{APP_VERSION}",
                  font=("Arial", 10)).pack(anchor=tk.W, pady=(5, 0))

        ttk.Label(version_frame,
                  text=f"New version: v{self.update_info['latest_version']}",
                  font=("Arial", 10, "bold")).pack(anchor=tk.W)

        # Release notes
        notes = self.update_info.get("release_notes", "")
        if notes:
            ttk.Label(main_frame, text="Release Notes:",
                      font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(5, 3))

            notes_text = tk.Text(main_frame, wrap=tk.WORD, height=10, width=55,
                                 font=("Arial", 9), relief=tk.SOLID, borderwidth=1)
            notes_text.pack(fill=tk.X, pady=(0, 10))
            notes_text.insert("1.0", notes)
            notes_text.config(state=tk.DISABLED)

            # Scrollbar for notes
            scrollbar = ttk.Scrollbar(notes_text, orient=tk.VERTICAL,
                                      command=notes_text.yview)
            notes_text.configure(yscrollcommand=scrollbar.set)
            scrollbar.place(relx=1.0, rely=0, relheight=1.0, anchor=tk.NE)

        # Progress bar (hidden initially)
        self.progress_frame = ttk.Frame(main_frame)

        self.progress_label = ttk.Label(self.progress_frame, text="Downloading...",
                                        font=("Arial", 9))
        self.progress_label.pack(anchor=tk.W)

        self.progress_bar = ttk.Progressbar(self.progress_frame, mode="determinate",
                                            length=400)
        self.progress_bar.pack(fill=tk.X, pady=(3, 0))

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        self.update_btn = ttk.Button(btn_frame, text="Update Now",
                                     command=self._start_download)
        self.update_btn.pack(side=tk.RIGHT, padx=(5, 0))

        self.skip_btn = ttk.Button(btn_frame, text="Skip This Version",
                                   command=self._skip)
        self.skip_btn.pack(side=tk.RIGHT, padx=(5, 0))

        self.later_btn = ttk.Button(btn_frame, text="Remind Me Later",
                                    command=self._close)
        self.later_btn.pack(side=tk.RIGHT)

    def _center_window(self):
        self.dialog.update_idletasks()
        w = self.dialog.winfo_width()
        h = self.dialog.winfo_height()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - w) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - h) // 2
        self.dialog.geometry(f"+{x}+{y}")

    def _start_download(self):
        if self.downloading:
            return
        self.downloading = True

        # Show progress, disable buttons
        self.progress_frame.pack(fill=tk.X, pady=(0, 5))
        self.update_btn.config(state=tk.DISABLED)
        self.skip_btn.config(state=tk.DISABLED)
        self.later_btn.config(state=tk.DISABLED)

        url = self.update_info["download_url"]
        thread = threading.Thread(target=self._download_thread, args=(url,), daemon=True)
        thread.start()

    def _download_thread(self, url):
        def on_progress(downloaded, total):
            percent = int(downloaded / total * 100) if total > 0 else 0
            mb_down = downloaded / (1024 * 1024)
            mb_total = total / (1024 * 1024)
            self.dialog.after(0, self._update_progress, percent,
                              f"Downloading... {mb_down:.1f} / {mb_total:.1f} MB ({percent}%)")

        zip_path = download_update(url, progress_callback=on_progress)

        if zip_path:
            self.dialog.after(0, self._download_complete, zip_path)
        else:
            self.dialog.after(0, self._download_failed)

    def _update_progress(self, percent, text):
        self.progress_bar["value"] = percent
        self.progress_label.config(text=text)

    def _download_complete(self, zip_path):
        self.progress_label.config(text="Download complete. Applying update...")
        self.progress_bar["value"] = 100

        success = apply_update(zip_path)
        if success:
            messagebox.showinfo(
                "Update Ready",
                "Update has been downloaded. The application will now restart "
                "to apply the update.\n\nYour settings will be preserved.",
                parent=self.dialog
            )
            self.dialog.destroy()
            self.parent.destroy()
        else:
            messagebox.showerror(
                "Update Failed",
                "Failed to apply the update. Please try downloading manually "
                "from GitHub.",
                parent=self.dialog
            )
            self._reset_buttons()

    def _download_failed(self):
        messagebox.showerror(
            "Download Failed",
            "Failed to download the update. Please check your internet "
            "connection and try again.",
            parent=self.dialog
        )
        self._reset_buttons()

    def _reset_buttons(self):
        self.downloading = False
        self.progress_frame.pack_forget()
        self.update_btn.config(state=tk.NORMAL)
        self.skip_btn.config(state=tk.NORMAL)
        self.later_btn.config(state=tk.NORMAL)

    def _skip(self):
        self.dialog.destroy()

    def _close(self):
        self.dialog.destroy()
