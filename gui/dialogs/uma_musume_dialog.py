import tkinter as tk
from tkinter import ttk
import os
import glob


class UmaMusumeDialog:
    """Dialog for selecting Uma Musume with search functionality"""

    def __init__(self, parent, current_selection="None", callback=None):
        self.parent = parent
        self.current_selection = current_selection
        self.callback = callback
        self.selected_uma = None

        # Create dialog window
        self.window = tk.Toplevel(parent)
        self.window.title("Select Uma Musume")
        self.window.geometry("500x450")
        self.window.resizable(False, False)

        # Make modal
        self.window.transient(parent)
        self.window.grab_set()

        # Load uma musume list
        self.uma_musume_list = self._load_uma_musume_list()

        # Setup UI
        self._setup_ui()

        # Center window
        self._center_window()

        # Bind close event
        self.window.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _load_uma_musume_list(self):
        """Load Uma Musume list from event_map folder"""
        uma_list = []

        try:
            # Load from assets/event_map/uma_musume
            uma_folder = "assets/event_map/uma_musume"
            if os.path.exists(uma_folder):
                json_files = glob.glob(os.path.join(uma_folder, "*.json"))
                for file_path in json_files:
                    filename = os.path.basename(file_path).replace('.json', '')
                    uma_list.append(filename)

            # Also load from assets/uma_musume if exists
            other_uma_folder = "assets/uma_musume"
            if os.path.exists(other_uma_folder):
                json_files = glob.glob(os.path.join(other_uma_folder, "*.json"))
                for file_path in json_files:
                    filename = os.path.basename(file_path).replace('.json', '')
                    if filename not in uma_list:
                        uma_list.append(filename)

            # Sort alphabetically
            uma_list.sort(key=lambda x: x.lower())

        except Exception as e:
            print(f"Error loading Uma Musume list: {e}")

        return uma_list

    def _setup_ui(self):
        """Setup dialog UI"""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Select Uma Musume",
            font=("Arial", 12, "bold"),
            foreground="#CC0066"
        )
        title_label.pack(pady=(0, 10))

        # Search frame
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))

        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._on_search)

        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        search_entry.focus_set()

        # Listbox with scrollbar
        listbox_frame = ttk.Frame(main_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(
            listbox_frame,
            yscrollcommand=scrollbar.set,
            font=("Arial", 11),
            selectmode=tk.SINGLE,
            activestyle='dotbox'
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)

        # Bind double-click and Enter key
        self.listbox.bind('<Double-Button-1>', lambda e: self._on_select())
        self.listbox.bind('<Return>', lambda e: self._on_select())
        search_entry.bind('<Return>', lambda e: self._on_select())

        # Populate listbox
        self._populate_listbox()

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        # None button
        none_button = ttk.Button(
            button_frame,
            text="None",
            command=self._on_none
        )
        none_button.pack(side=tk.LEFT, padx=(0, 5))

        # Spacer
        ttk.Frame(button_frame).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Cancel button
        cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel
        )
        cancel_button.pack(side=tk.RIGHT, padx=(5, 0))

        # Select button
        select_button = ttk.Button(
            button_frame,
            text="Select",
            command=self._on_select
        )
        select_button.pack(side=tk.RIGHT)

    def _populate_listbox(self, filter_text=""):
        """Populate listbox with Uma Musume names"""
        self.listbox.delete(0, tk.END)

        uma_list = self.uma_musume_list

        # Filter if search text provided
        if filter_text:
            filter_text = filter_text.lower()
            uma_list = [uma for uma in uma_list if filter_text in uma.lower()]

        # Add to listbox
        for uma in uma_list:
            self.listbox.insert(tk.END, uma)

        # Highlight current selection if it exists
        if self.current_selection and self.current_selection != "None":
            try:
                index = uma_list.index(self.current_selection)
                self.listbox.selection_set(index)
                self.listbox.see(index)
            except ValueError:
                pass

    def _on_search(self, *args):
        """Handle search text change"""
        search_text = self.search_var.get()
        self._populate_listbox(search_text)

    def _on_select(self):
        """Handle select button"""
        selection = self.listbox.curselection()
        if selection:
            self.selected_uma = self.listbox.get(selection[0])
            if self.callback:
                self.callback(self.selected_uma)
            self.window.destroy()

    def _on_none(self):
        """Handle None button"""
        self.selected_uma = "None"
        if self.callback:
            self.callback(self.selected_uma)
        self.window.destroy()

    def _on_cancel(self):
        """Handle cancel"""
        self.window.destroy()

    def _center_window(self):
        """Center window on parent"""
        self.window.update_idletasks()

        width = self.window.winfo_width()
        height = self.window.winfo_height()

        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2

        self.window.geometry(f"{width}x{height}+{x}+{y}")
