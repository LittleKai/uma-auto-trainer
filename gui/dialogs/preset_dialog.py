import tkinter as tk
from tkinter import ttk


class PresetDialog:
    """Dialog for selecting presets with summary information"""

    # Card type display info
    CARD_TYPE_INFO = {
        'spd': ('SPD', '#0066CC'),
        'sta': ('STA', '#CC0066'),
        'pow': ('PWR', '#CC6600'),
        'gut': ('GUT', '#CC8800'),
        'wit': ('WIT', '#007733'),
        'frd': ('FRD', '#AA8800')
    }

    def __init__(self, parent, preset_names, preset_sets, current_set, callback=None):
        """
        Initialize preset dialog

        Args:
            parent: Parent window
            preset_names: Dict of preset number -> StringVar for names
            preset_sets: Dict of preset number -> preset data dict
            current_set: Currently selected preset number
            callback: Function to call when preset is selected (receives preset_num, new_name)
        """
        self.parent = parent
        self.preset_names = preset_names
        self.preset_sets = preset_sets
        self.current_set = current_set
        self.callback = callback
        self.selected_preset = None

        # Create dialog window
        self.window = tk.Toplevel(parent)
        self.window.title("Select Preset")
        self.window.geometry("650x500")
        self.window.resizable(False, False)

        # Make modal
        self.window.transient(parent)
        self.window.grab_set()

        # Setup UI
        self._setup_ui()

        # Center window
        self._center_window()

        # Bind close event
        self.window.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _setup_ui(self):
        """Setup dialog UI"""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Select Preset",
            font=("Arial", 12, "bold"),
            foreground="#0066CC"
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

        # Create scrollable frame for presets
        list_container = ttk.Frame(main_frame)
        list_container.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Canvas with scrollbar
        canvas = tk.Canvas(list_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=canvas.yview)

        self.scrollable_frame = ttk.Frame(canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas = canvas

        # Populate presets
        self._populate_presets()

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

        # Select button
        select_button = ttk.Button(
            button_frame,
            text="Select",
            command=self._on_select
        )
        select_button.pack(side=tk.RIGHT)

    def _populate_presets(self, filter_text=""):
        """Populate preset list"""
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.preset_frames = {}
        self.name_entries = {}

        filter_text = filter_text.lower()

        for preset_num in range(1, 21):
            preset_name = self.preset_names[preset_num].get()
            preset_data = self.preset_sets[preset_num]

            # Filter by name or Uma Musume
            uma_musume = preset_data['uma_musume'].get()
            if filter_text:
                if filter_text not in preset_name.lower() and filter_text not in uma_musume.lower():
                    continue

            # Create preset frame
            frame = self._create_preset_frame(preset_num, preset_name, preset_data)
            frame.pack(fill=tk.X, pady=2, padx=5)
            self.preset_frames[preset_num] = frame

    def _create_preset_frame(self, preset_num, preset_name, preset_data):
        """Create a frame for a single preset"""
        # Determine if this is the current preset
        is_current = preset_num == self.current_set

        # Frame with border
        frame = tk.Frame(
            self.scrollable_frame,
            relief=tk.RAISED if is_current else tk.GROOVE,
            borderwidth=2,
            bg="#e6f0ff" if is_current else "#f8f8f8",
            cursor="hand2"
        )

        # Header row: preset number + name entry + edit indicator
        header_frame = tk.Frame(frame, bg=frame.cget('bg'))
        header_frame.pack(fill=tk.X, padx=8, pady=(8, 4))

        # Preset number label
        num_label = tk.Label(
            header_frame,
            text=f"#{preset_num}",
            font=("Arial", 10, "bold"),
            fg="#0066CC" if is_current else "#666666",
            bg=frame.cget('bg'),
            width=3
        )
        num_label.pack(side=tk.LEFT, padx=(0, 5))

        # Name entry (editable)
        name_var = tk.StringVar(value=preset_name)
        name_entry = ttk.Entry(
            header_frame,
            textvariable=name_var,
            font=("Arial", 10, "bold"),
            width=20
        )
        name_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.name_entries[preset_num] = name_var

        # Current indicator
        if is_current:
            current_label = tk.Label(
                header_frame,
                text="(Current)",
                font=("Arial", 9, "italic"),
                fg="#0066CC",
                bg=frame.cget('bg')
            )
            current_label.pack(side=tk.LEFT)

        # Info row: Uma Musume + Support Cards summary
        info_frame = tk.Frame(frame, bg=frame.cget('bg'))
        info_frame.pack(fill=tk.X, padx=8, pady=(0, 4))

        # Uma Musume
        uma_musume = preset_data['uma_musume'].get()
        uma_text = uma_musume if uma_musume and uma_musume != "None" else "No Uma"
        uma_label = tk.Label(
            info_frame,
            text=f"Uma: {uma_text}",
            font=("Arial", 9),
            fg="#CC0066",
            bg=frame.cget('bg')
        )
        uma_label.pack(side=tk.LEFT, padx=(0, 15))

        # Support cards summary (count by type)
        card_summary = self._get_card_summary(preset_data['support_cards'])
        if card_summary:
            cards_label = tk.Label(
                info_frame,
                text=f"Cards: {card_summary}",
                font=("Arial", 9),
                fg="#666666",
                bg=frame.cget('bg')
            )
            cards_label.pack(side=tk.LEFT)

        # Stat caps row
        caps_frame = tk.Frame(frame, bg=frame.cget('bg'))
        caps_frame.pack(fill=tk.X, padx=8, pady=(0, 8))

        caps_text = self._get_stat_caps_summary(preset_data['stat_caps'])
        caps_label = tk.Label(
            caps_frame,
            text=f"Caps: {caps_text}",
            font=("Arial", 8),
            fg="#888888",
            bg=frame.cget('bg')
        )
        caps_label.pack(side=tk.LEFT)

        # Bind click events to select this preset
        for widget in [frame, header_frame, info_frame, caps_frame, num_label, uma_label]:
            widget.bind('<Button-1>', lambda e, pn=preset_num: self._select_preset(pn))
            widget.bind('<Double-Button-1>', lambda e, pn=preset_num: self._double_click_preset(pn))

        if card_summary:
            cards_label.bind('<Button-1>', lambda e, pn=preset_num: self._select_preset(pn))
            cards_label.bind('<Double-Button-1>', lambda e, pn=preset_num: self._double_click_preset(pn))

        caps_label.bind('<Button-1>', lambda e, pn=preset_num: self._select_preset(pn))
        caps_label.bind('<Double-Button-1>', lambda e, pn=preset_num: self._double_click_preset(pn))

        return frame

    def _get_card_summary(self, support_cards):
        """Get summary of support cards by type"""
        type_counts = {}

        for card_var in support_cards:
            card_value = card_var.get()
            if card_value and card_value != "None" and ":" in card_value:
                card_type = card_value.split(":")[0].strip().lower()
                type_counts[card_type] = type_counts.get(card_type, 0) + 1

        if not type_counts:
            return ""

        # Format: "2 SPD, 1 STA, 1 PWR"
        parts = []
        for card_type, count in sorted(type_counts.items()):
            if card_type in self.CARD_TYPE_INFO:
                name, _ = self.CARD_TYPE_INFO[card_type]
                parts.append(f"{count}{name}")

        return ", ".join(parts)

    def _get_stat_caps_summary(self, stat_caps):
        """Get summary of stat caps"""
        parts = []
        stat_order = ['spd', 'sta', 'pwr', 'guts', 'wit']
        stat_names = {'spd': 'S', 'sta': 'T', 'pwr': 'P', 'guts': 'G', 'wit': 'W'}

        for stat_key in stat_order:
            value = stat_caps[stat_key].get()
            parts.append(f"{stat_names[stat_key]}:{value}")

        return " | ".join(parts)

    def _select_preset(self, preset_num):
        """Handle preset selection (single click)"""
        self.selected_preset = preset_num

        # Update visual selection
        for pn, frame in self.preset_frames.items():
            if pn == preset_num:
                frame.configure(bg="#d0e0ff", relief=tk.RAISED)
                for child in frame.winfo_children():
                    if isinstance(child, tk.Frame):
                        child.configure(bg="#d0e0ff")
                        for subchild in child.winfo_children():
                            if isinstance(subchild, tk.Label):
                                subchild.configure(bg="#d0e0ff")
            else:
                is_current = pn == self.current_set
                bg = "#e6f0ff" if is_current else "#f8f8f8"
                frame.configure(bg=bg, relief=tk.RAISED if is_current else tk.GROOVE)
                for child in frame.winfo_children():
                    if isinstance(child, tk.Frame):
                        child.configure(bg=bg)
                        for subchild in child.winfo_children():
                            if isinstance(subchild, tk.Label):
                                subchild.configure(bg=bg)

    def _double_click_preset(self, preset_num):
        """Handle preset double-click (select and close)"""
        self.selected_preset = preset_num
        self._on_select()

    def _on_search(self, *args):
        """Handle search text change"""
        search_text = self.search_var.get()
        self._populate_presets(search_text)

    def _on_select(self):
        """Handle select button"""
        if self.selected_preset is None:
            self.selected_preset = self.current_set

        # Save any name changes
        for preset_num, name_var in self.name_entries.items():
            new_name = name_var.get()
            if new_name != self.preset_names[preset_num].get():
                self.preset_names[preset_num].set(new_name)

        if self.callback:
            self.callback(self.selected_preset)

        # Unbind mousewheel before destroying
        self.canvas.unbind_all("<MouseWheel>")
        self.window.destroy()

    def _on_cancel(self):
        """Handle cancel"""
        # Unbind mousewheel before destroying
        self.canvas.unbind_all("<MouseWheel>")
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
