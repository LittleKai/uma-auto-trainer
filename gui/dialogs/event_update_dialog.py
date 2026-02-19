"""
Event Update Dialog for Uma Musume Auto Train.
Shows new/updated event map files and handles downloading them from GitHub.
"""

import tkinter as tk
from tkinter import ttk
import threading

from core.updater import download_event_files


class EventUpdateDialog:
    """Dialog for displaying and downloading event map updates."""

    def __init__(self, parent, update_result):
        """
        Args:
            parent: Parent tkinter window
            update_result: dict from check_event_updates() with update details
        """
        self.parent = parent
        self.files_to_update = update_result["files_to_update"]
        self.downloading = False

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Event Update")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)

        self._setup_ui()
        self._center_window()

    def _setup_ui(self):
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        new_count = sum(1 for f in self.files_to_update if f["status"] == "New")
        updated_count = sum(1 for f in self.files_to_update if f["status"] == "Updated")

        ttk.Label(main_frame, text="Event Updates Available",
                  font=("Arial", 12, "bold")).pack(anchor=tk.W)

        summary_parts = []
        if new_count:
            summary_parts.append(f"{new_count} new")
        if updated_count:
            summary_parts.append(f"{updated_count} updated")
        summary_text = f"Found {', '.join(summary_parts)} event file(s)"

        ttk.Label(main_frame, text=summary_text,
                  font=("Arial", 10)).pack(anchor=tk.W, pady=(3, 10))

        # File list
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("file", "status")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings",
                                 height=min(len(self.files_to_update), 15))
        self.tree.heading("file", text="File")
        self.tree.heading("status", text="Status")
        self.tree.column("file", width=380)
        self.tree.column("status", width=70, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL,
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for file_info in self.files_to_update:
            # Show shortened path (remove "assets/event_map/" prefix)
            display_path = file_info["path"]
            if display_path.startswith("assets/event_map/"):
                display_path = display_path[len("assets/event_map/"):]
            self.tree.insert("", tk.END, values=(display_path, file_info["status"]))

        # Progress bar (hidden initially)
        self.progress_frame = ttk.Frame(main_frame)

        self.progress_label = ttk.Label(self.progress_frame, text="Downloading...",
                                        font=("Arial", 9))
        self.progress_label.pack(anchor=tk.W)

        self.progress_bar = ttk.Progressbar(self.progress_frame, mode="determinate",
                                            length=460)
        self.progress_bar.pack(fill=tk.X, pady=(3, 0))

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        self.update_btn = ttk.Button(btn_frame, text="Update All",
                                     command=self._start_download)
        self.update_btn.pack(side=tk.RIGHT, padx=(5, 0))

        self.close_btn = ttk.Button(btn_frame, text="Close",
                                    command=self._close)
        self.close_btn.pack(side=tk.RIGHT)

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

        self.progress_frame.pack(fill=tk.X, pady=(10, 0))
        self.update_btn.config(state=tk.DISABLED)
        self.close_btn.config(state=tk.DISABLED)

        thread = threading.Thread(target=self._download_thread, daemon=True)
        thread.start()

    def _download_thread(self):
        def on_progress(current, total, file_path):
            if total > 0:
                percent = int(current / total * 100)
            else:
                percent = 0
            if file_path:
                display = file_path
                if display.startswith("assets/event_map/"):
                    display = display[len("assets/event_map/"):]
                text = f"Downloading ({current}/{total}): {display}"
            else:
                text = "Download complete!"
            self.dialog.after(0, self._update_progress, percent, text)

        success_count = download_event_files(
            self.files_to_update, progress_callback=on_progress
        )

        self.dialog.after(0, self._download_complete, success_count)

    def _update_progress(self, percent, text):
        self.progress_bar["value"] = percent
        self.progress_label.config(text=text)

    def _download_complete(self, success_count):
        total = len(self.files_to_update)
        failed = total - success_count

        self.progress_bar["value"] = 100

        if failed == 0:
            self.progress_label.config(
                text=f"Successfully updated {success_count} file(s)!"
            )
        else:
            self.progress_label.config(
                text=f"Updated {success_count}/{total} file(s). {failed} failed."
            )

        self.update_btn.config(text="Done", state=tk.DISABLED)
        self.close_btn.config(state=tk.NORMAL)

    def _close(self):
        self.dialog.destroy()
