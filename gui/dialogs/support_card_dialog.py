import tkinter as tk
from tkinter import ttk
import os
import glob


class SupportCardDialog:
    """Dialog for selecting support cards with tabbed interface and search"""

    def __init__(self, parent, current_selection="None", callback=None):
        self.parent = parent
        self.current_selection = current_selection
        self.callback = callback
        self.selected_card = None

        # Create dialog window
        self.window = tk.Toplevel(parent)
        self.window.title("Select Support Card")
        self.window.geometry("700x500")
        self.window.resizable(False, False)

        # Make modal
        self.window.transient(parent)
        self.window.grab_set()

        # Load support cards data
        self.support_cards_by_type = self._load_support_cards()

        # Setup UI
        self._setup_ui()

        # Center window
        self._center_window()

        # Bind close event
        self.window.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _load_support_cards(self):
        """Load support cards organized by type"""
        cards_by_type = {
            'all': [],
            'spd': [],
            'sta': [],
            'pow': [],
            'gut': [],
            'wit': [],
            'frd': []
        }

        try:
            support_folder = "assets/event_map/support_card"
            if not os.path.exists(support_folder):
                return cards_by_type

            # Define card types
            card_types = ["spd", "sta", "pow", "gut", "wit", "frd"]

            # Load cards by type
            for card_type in card_types:
                type_folder = os.path.join(support_folder, card_type)
                if os.path.exists(type_folder):
                    json_files = glob.glob(os.path.join(type_folder, "*.json"))

                    filenames = []
                    for file_path in json_files:
                        filename = os.path.basename(file_path).replace('.json', '')
                        filenames.append(filename)

                    # Sort alphabetically
                    filenames.sort(key=lambda x: x.lower())

                    for filename in filenames:
                        display_name = f"{card_type}: {filename}"
                        cards_by_type[card_type].append(display_name)
                        cards_by_type['all'].append(display_name)

            # Also check for direct JSON files
            direct_json_files = glob.glob(os.path.join(support_folder, "*.json"))
            direct_filenames = []
            for file_path in direct_json_files:
                filename = os.path.basename(file_path).replace('.json', '')
                direct_filenames.append(filename)

            direct_filenames.sort(key=lambda x: x.lower())
            for filename in direct_filenames:
                cards_by_type['all'].append(filename)

        except Exception as e:
            print(f"Error loading support cards: {e}")

        return cards_by_type

    def _setup_ui(self):
        """Setup dialog UI"""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Select Support Card",
            font=("Arial", 12, "bold")
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

        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create tabs
        self.tab_frames = {}
        self.tab_listboxes = {}

        tab_names = [
            ('All', 'all'),
            ('Speed', 'spd'),
            ('Stamina', 'sta'),
            ('Power', 'pow'),
            ('Guts', 'gut'),
            ('Wisdom', 'wit'),
            ('Friend', 'frd')
        ]

        for tab_label, tab_key in tab_names:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=tab_label)
            self.tab_frames[tab_key] = frame

            # Create scrolled listbox
            listbox_frame = ttk.Frame(frame)
            listbox_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            scrollbar = ttk.Scrollbar(listbox_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            listbox = tk.Listbox(
                listbox_frame,
                yscrollcommand=scrollbar.set,
                font=("Arial", 10),
                selectmode=tk.SINGLE
            )
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=listbox.yview)

            # Bind double-click
            listbox.bind('<Double-Button-1>', lambda e, key=tab_key: self._on_card_double_click(key))

            self.tab_listboxes[tab_key] = listbox

            # Populate listbox
            self._populate_listbox(tab_key)

        # Select current tab based on current selection
        self._select_appropriate_tab()

        # Bind tab change event
        self.notebook.bind('<<NotebookTabChanged>>', self._on_tab_change)

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

    def _populate_listbox(self, tab_key, filter_text=""):
        """Populate listbox with cards"""
        listbox = self.tab_listboxes[tab_key]
        listbox.delete(0, tk.END)

        cards = self.support_cards_by_type.get(tab_key, [])

        # Filter cards if search text provided
        if filter_text:
            filter_text = filter_text.lower()
            cards = [card for card in cards if filter_text in card.lower()]

        # Add cards to listbox
        for card in cards:
            listbox.insert(tk.END, card)

        # Highlight current selection if it exists in the list
        if self.current_selection != "None":
            try:
                index = cards.index(self.current_selection)
                listbox.selection_set(index)
                listbox.see(index)
            except ValueError:
                pass

    def _select_appropriate_tab(self):
        """Select appropriate tab based on current selection"""
        if self.current_selection == "None":
            return

        # Extract type from current selection
        if ":" in self.current_selection:
            card_type = self.current_selection.split(":")[0].strip().lower()
            
            # Map card type to tab index
            tab_mapping = {
                'spd': 1,
                'sta': 2,
                'pow': 3,
                'gut': 4,
                'wit': 5,
                'frd': 6
            }

            if card_type in tab_mapping:
                self.notebook.select(tab_mapping[card_type])

    def _on_search(self, *args):
        """Handle search text change"""
        search_text = self.search_var.get()
        current_tab = self.notebook.select()
        current_tab_text = self.notebook.tab(current_tab, "text").lower()

        # Map tab text to key
        tab_map = {
            'all': 'all',
            'speed': 'spd',
            'stamina': 'sta',
            'power': 'pow',
            'guts': 'gut',
            'wisdom': 'wit',
            'friend': 'frd'
        }

        tab_key = tab_map.get(current_tab_text, 'all')
        self._populate_listbox(tab_key, search_text)

    def _on_tab_change(self, event):
        """Handle tab change - refresh search"""
        # Clear and reapply search for new tab
        search_text = self.search_var.get()
        current_tab = self.notebook.select()
        current_tab_text = self.notebook.tab(current_tab, "text").lower()

        tab_map = {
            'all': 'all',
            'speed': 'spd',
            'stamina': 'sta',
            'power': 'pow',
            'guts': 'gut',
            'wisdom': 'wit',
            'friend': 'frd'
        }

        tab_key = tab_map.get(current_tab_text, 'all')
        self._populate_listbox(tab_key, search_text)

    def _on_card_double_click(self, tab_key):
        """Handle double-click on card"""
        self._on_select()

    def _on_select(self):
        """Handle select button"""
        current_tab = self.notebook.select()
        current_tab_text = self.notebook.tab(current_tab, "text").lower()

        tab_map = {
            'all': 'all',
            'speed': 'spd',
            'stamina': 'sta',
            'power': 'pow',
            'guts': 'gut',
            'wisdom': 'wit',
            'friend': 'frd'
        }

        tab_key = tab_map.get(current_tab_text, 'all')
        listbox = self.tab_listboxes[tab_key]

        selection = listbox.curselection()
        if selection:
            self.selected_card = listbox.get(selection[0])
            if self.callback:
                self.callback(self.selected_card)
            self.window.destroy()

    def _on_none(self):
        """Handle None button"""
        self.selected_card = "None"
        if self.callback:
            self.callback(self.selected_card)
        self.window.destroy()

    def _on_cancel(self):
        """Handle cancel"""
        self.window.destroy()

    def _center_window(self):
        """Center window on screen"""
        self.window.update_idletasks()

        width = self.window.winfo_width()
        height = self.window.winfo_height()

        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        self.window.geometry(f"{width}x{height}+{x}+{y}")
