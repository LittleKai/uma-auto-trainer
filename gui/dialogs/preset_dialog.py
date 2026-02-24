import copy
import tkinter as tk
from tkinter import ttk, messagebox


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
        self._swaps_performed = False
        self._drag_source = None
        self._drag_hover = None

        # Create dialog window
        self.window = tk.Toplevel(parent)
        self.window.title("Select Preset")
        self.window.geometry("650x700")
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

        # Scroll to current preset after layout is ready
        self.window.after(50, self._scroll_to_current_preset)

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
        self.preset_card_frames = {}
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

            # Create preset row (outer container returned)
            row = self._create_preset_frame(preset_num, preset_name, preset_data)
            row.pack(fill=tk.X, pady=2, padx=5)
            self.preset_frames[preset_num] = row

        # "+" button to create a new empty preset at the bottom
        add_frame = tk.Frame(self.scrollable_frame, bg="#f0f0f0")
        add_frame.pack(fill=tk.X, pady=(6, 2), padx=5)

        add_btn = tk.Label(
            add_frame,
            text="＋  New Preset",
            font=("Arial", 9, "bold"),
            fg="#0066CC",
            bg="#f0f0f0",
            cursor="hand2",
            pady=6,
            relief=tk.GROOVE,
            borderwidth=1
        )
        add_btn.pack(fill=tk.X)
        add_btn.bind('<Button-1>', lambda e: self._create_new_preset())
        add_btn.bind('<Enter>', lambda e: e.widget.configure(bg="#ddeeff"))
        add_btn.bind('<Leave>', lambda e: e.widget.configure(bg="#f0f0f0"))

    def _create_preset_frame(self, preset_num, preset_name, preset_data):
        """Create a row containing the preset card and action buttons side by side."""
        is_current = preset_num == self.current_set

        # ── Outer row: card (left) + buttons (right, outside card) ──
        row_frame = ttk.Frame(self.scrollable_frame)

        # Card frame with border
        frame = tk.Frame(
            row_frame,
            relief=tk.RAISED if is_current else tk.GROOVE,
            borderwidth=2,
            bg="#e6f0ff" if is_current else "#f8f8f8",
            cursor="hand2"
        )
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.preset_card_frames[preset_num] = frame

        # Content area fills the card
        content_frame = tk.Frame(frame, bg=frame.cget('bg'))
        content_frame.pack(fill=tk.BOTH, expand=True)

        # ── Action buttons (outside the card, right of row) ──
        move_frame = ttk.Frame(row_frame)
        move_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(4, 0))

        # Drag handle (replaces ▲▼ buttons)
        drag_handle = tk.Label(
            move_frame,
            text="\u28bf",
            font=("Segoe UI", 13),
            fg="#bbbbbb",
            cursor="fleur",
            padx=4, pady=4
        )
        drag_handle.pack(side=tk.TOP)
        drag_handle.bind('<ButtonPress-1>',   lambda e, pn=preset_num: self._start_drag(e, pn))
        drag_handle.bind('<B1-Motion>',       lambda e, pn=preset_num: self._on_drag_motion(e, pn))
        drag_handle.bind('<ButtonRelease-1>', lambda e, pn=preset_num: self._end_drag(e, pn))
        drag_handle.bind('<Enter>', lambda e: e.widget.configure(fg="#555555"))
        drag_handle.bind('<Leave>', lambda e: e.widget.configure(fg="#bbbbbb"))

        # Copy button (green)
        copy_btn = tk.Label(
            move_frame,
            text="\u29c9",
            font=("Arial", 11),
            fg="#28A745",
            cursor="hand2",
            padx=4, pady=2
        )
        copy_btn.pack(side=tk.TOP, pady=(4, 0))
        copy_btn.bind('<Button-1>', lambda e, pn=preset_num: self._copy_preset(pn))
        copy_btn.bind('<Enter>', lambda e: e.widget.configure(fg="#1a6e2e"))
        copy_btn.bind('<Leave>', lambda e: e.widget.configure(fg="#28A745"))

        # Delete button (red)
        del_btn = tk.Label(
            move_frame,
            text="\u2715",
            font=("Arial", 10),
            fg="#CC2222",
            cursor="hand2",
            padx=4, pady=2
        )
        del_btn.pack(side=tk.TOP, pady=(4, 0))
        del_btn.bind('<Button-1>', lambda e, pn=preset_num: self._delete_preset(pn))
        del_btn.bind('<Enter>', lambda e: e.widget.configure(fg="#ff0000"))
        del_btn.bind('<Leave>', lambda e: e.widget.configure(fg="#CC2222"))

        # Header row: preset number + name entry + edit indicator
        header_frame = tk.Frame(content_frame, bg=frame.cget('bg'))
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
        info_frame = tk.Frame(content_frame, bg=frame.cget('bg'))
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
        caps_frame = tk.Frame(content_frame, bg=frame.cget('bg'))
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
        clickable_widgets = [frame, content_frame, header_frame, info_frame,
                             caps_frame, num_label, uma_label]
        for widget in clickable_widgets:
            widget.bind('<Button-1>', lambda e, pn=preset_num: self._select_preset(pn))
            widget.bind('<Double-Button-1>', lambda e, pn=preset_num: self._double_click_preset(pn))

        if card_summary:
            cards_label.bind('<Button-1>', lambda e, pn=preset_num: self._select_preset(pn))
            cards_label.bind('<Double-Button-1>', lambda e, pn=preset_num: self._double_click_preset(pn))

        caps_label.bind('<Button-1>', lambda e, pn=preset_num: self._select_preset(pn))
        caps_label.bind('<Double-Button-1>', lambda e, pn=preset_num: self._double_click_preset(pn))

        return row_frame

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

    def _set_frame_bg(self, widget, bg):
        """Recursively set background color for a widget and its children"""
        if isinstance(widget, (tk.Frame, tk.Label)):
            try:
                widget.configure(bg=bg)
            except tk.TclError:
                pass
        for child in widget.winfo_children():
            self._set_frame_bg(child, bg)

    def _select_preset(self, preset_num):
        """Handle preset selection (single click)"""
        self.selected_preset = preset_num

        # Update visual selection (only the card frame, not the outer row)
        for pn, card in self.preset_card_frames.items():
            if pn == preset_num:
                card.configure(bg="#d0e0ff", relief=tk.RAISED)
                self._set_frame_bg(card, "#d0e0ff")
            else:
                is_current = pn == self.current_set
                bg = "#e6f0ff" if is_current else "#f8f8f8"
                card.configure(bg=bg, relief=tk.RAISED if is_current else tk.GROOVE)
                self._set_frame_bg(card, bg)

    def _double_click_preset(self, preset_num):
        """Handle preset double-click (select and close)"""
        self.selected_preset = preset_num
        self._on_select()

    def _on_search(self, *args):
        """Handle search text change"""
        search_text = self.search_var.get()
        self._populate_presets(search_text)

    def _swap_presets(self, num_a, num_b):
        """Swap all data between two preset positions"""
        self._swaps_performed = True

        # Swap preset names
        name_a = self.preset_names[num_a].get()
        name_b = self.preset_names[num_b].get()
        self.preset_names[num_a].set(name_b)
        self.preset_names[num_b].set(name_a)

        # Swap preset data (uma_musume, support_cards, stat_caps, debut_style, stop_conditions)
        preset_a = self.preset_sets[num_a]
        preset_b = self.preset_sets[num_b]

        # Swap uma_musume
        uma_a = preset_a['uma_musume'].get()
        uma_b = preset_b['uma_musume'].get()
        preset_a['uma_musume'].set(uma_b)
        preset_b['uma_musume'].set(uma_a)

        # Swap support_cards
        for i in range(len(preset_a['support_cards'])):
            card_a = preset_a['support_cards'][i].get()
            card_b = preset_b['support_cards'][i].get()
            preset_a['support_cards'][i].set(card_b)
            preset_b['support_cards'][i].set(card_a)

        # Swap stat_caps
        for stat_key in preset_a['stat_caps']:
            cap_a = preset_a['stat_caps'][stat_key].get()
            cap_b = preset_b['stat_caps'][stat_key].get()
            preset_a['stat_caps'][stat_key].set(cap_b)
            preset_b['stat_caps'][stat_key].set(cap_a)

        # Swap debut_style
        style_a = preset_a.get('debut_style', 'none')
        style_b = preset_b.get('debut_style', 'none')
        preset_a['debut_style'] = style_b
        preset_b['debut_style'] = style_a

        # Swap stop_conditions
        sc_a = dict(preset_a.get('stop_conditions', {}))
        sc_b = dict(preset_b.get('stop_conditions', {}))
        preset_a['stop_conditions'] = sc_b
        preset_b['stop_conditions'] = sc_a

        # Swap race_schedule
        rs_a = preset_a.get('race_schedule', [])
        rs_b = preset_b.get('race_schedule', [])
        preset_a['race_schedule'] = rs_b
        preset_b['race_schedule'] = rs_a

    # ── Drag-to-reorder ────────────────────────────────────────────────────

    def _start_drag(self, event, preset_num):
        """Begin dragging a preset row."""
        self._drag_source = preset_num
        self._drag_hover = None
        card = self.preset_card_frames.get(preset_num)
        if card:
            card.configure(bg="#c8d8f0", relief=tk.FLAT)
            self._set_frame_bg(card, "#c8d8f0")

    def _on_drag_motion(self, event, preset_num):
        """Update drag-over highlight while mouse moves."""
        if self._drag_source is None:
            return

        abs_y = event.widget.winfo_rooty() + event.y
        new_hover = self._find_row_at_y(abs_y)

        if new_hover == self._drag_hover:
            return

        # Restore previous hover target
        if self._drag_hover is not None and self._drag_hover != self._drag_source:
            self._restore_card_bg(self._drag_hover)

        self._drag_hover = new_hover

        # Highlight new hover target
        if new_hover is not None and new_hover != self._drag_source:
            card = self.preset_card_frames.get(new_hover)
            if card:
                card.configure(bg="#ffe0a0", relief=tk.RAISED)
                self._set_frame_bg(card, "#ffe0a0")

    def _end_drag(self, event, preset_num):
        """Finish drag: move preset to target position."""
        if self._drag_source is None:
            return

        source = self._drag_source
        target = self._drag_hover
        self._drag_source = None
        self._drag_hover = None

        if target is not None and target != source:
            self._move_preset_to(source, target)
        else:
            # Restore visuals without any move
            self._populate_presets(self.search_var.get())
            if self.selected_preset:
                self._select_preset(self.selected_preset)

    def _find_row_at_y(self, abs_y):
        """Return the preset_num whose row contains the given absolute screen Y."""
        for pn, row in self.preset_frames.items():
            top = row.winfo_rooty()
            if top <= abs_y <= top + row.winfo_height():
                return pn
        return None

    def _restore_card_bg(self, preset_num):
        """Restore a card to its default background/relief."""
        card = self.preset_card_frames.get(preset_num)
        if not card:
            return
        if preset_num == self.selected_preset:
            bg, relief = "#d0e0ff", tk.RAISED
        elif preset_num == self.current_set:
            bg, relief = "#e6f0ff", tk.RAISED
        else:
            bg, relief = "#f8f8f8", tk.GROOVE
        card.configure(bg=bg, relief=relief)
        self._set_frame_bg(card, bg)

    def _move_preset_to(self, source_num, target_num):
        """Move preset from source_num to target_num, shifting everything in between."""
        if source_num == target_num:
            return

        old_current = self.current_set

        if source_num < target_num:
            for i in range(source_num, target_num):
                self._swap_presets(i, i + 1)
            if old_current == source_num:
                self.current_set = target_num
            elif source_num < old_current <= target_num:
                self.current_set = old_current - 1
        else:
            for i in range(source_num, target_num, -1):
                self._swap_presets(i, i - 1)
            if old_current == source_num:
                self.current_set = target_num
            elif target_num <= old_current < source_num:
                self.current_set = old_current + 1

        self.selected_preset = target_num
        self._populate_presets(self.search_var.get())
        self._select_preset(target_num)
        self._scroll_to_preset(target_num)

    def _find_next_available_slot(self):
        """Find the first preset slot with no uma_musume configured."""
        for slot in range(1, 21):
            uma = self.preset_sets[slot]['uma_musume'].get()
            if not uma or uma == "None":
                return slot
        return None  # All 20 slots are occupied

    def _copy_preset(self, source_num):
        """Copy preset data from source_num to the next available slot."""
        target = self._find_next_available_slot()
        if target is None:
            messagebox.showwarning(
                "No Empty Slot",
                "All 20 preset slots are in use.",
                parent=self.window
            )
            return

        preset_name = self.preset_names[source_num].get()
        if not messagebox.askyesno(
            "Copy Preset",
            f"Copy \"{preset_name}\" to slot #{target}?",
            parent=self.window
        ):
            return

        src = self.preset_sets[source_num]
        dst = self.preset_sets[target]

        # Copy name
        self.preset_names[target].set(self.preset_names[source_num].get() + " (Copy)")

        # Copy uma_musume
        dst['uma_musume'].set(src['uma_musume'].get())

        # Copy support_cards
        for i in range(len(src['support_cards'])):
            dst['support_cards'][i].set(src['support_cards'][i].get())

        # Copy stat_caps
        for stat_key in src['stat_caps']:
            dst['stat_caps'][stat_key].set(src['stat_caps'][stat_key].get())

        # Copy plain-value fields
        dst['debut_style'] = src.get('debut_style', 'none')
        dst['stop_conditions'] = copy.deepcopy(src.get('stop_conditions', {}))
        if 'race_schedule' in src:
            dst['race_schedule'] = copy.deepcopy(src['race_schedule'])

        self._swaps_performed = True

        # Refresh list and navigate to the new preset
        self._populate_presets(self.search_var.get())
        self._select_preset(target)
        self._scroll_to_preset(target)

    def _create_new_preset(self):
        """Navigate to the next available (empty) preset slot."""
        target = self._find_next_available_slot()
        if target is None:
            return

        self._populate_presets(self.search_var.get())
        self._select_preset(target)
        self._scroll_to_preset(target)

    def _delete_preset(self, preset_num):
        """Clear all data from a preset slot after confirmation."""
        preset_name = self.preset_names[preset_num].get()
        msg = f"Clear preset #{preset_num} \"{preset_name}\"?\n\nAll settings will be reset."
        if preset_num == self.current_set:
            msg += "\n\nWarning: this is the currently active preset."

        if not messagebox.askyesno("Clear Preset", msg, parent=self.window):
            return

        data = self.preset_sets[preset_num]

        self.preset_names[preset_num].set(f"Preset {preset_num}")
        data['uma_musume'].set("None")
        for card_var in data['support_cards']:
            card_var.set("None")
        data['debut_style'] = 'none'
        data['race_schedule'] = []
        data['stop_conditions'] = {}

        self._swaps_performed = True
        if self.selected_preset == preset_num:
            self.selected_preset = None

        self._populate_presets(self.search_var.get())

    def _scroll_to_preset(self, preset_num):
        """Scroll to make a specific preset visible"""
        if preset_num not in self.preset_frames:
            return

        self.canvas.update_idletasks()
        frame = self.preset_frames[preset_num]
        frame_y = frame.winfo_y()
        frame_height = frame.winfo_height()
        canvas_height = self.canvas.winfo_height()
        scroll_height = self.scrollable_frame.winfo_height()

        if scroll_height <= canvas_height:
            return

        target_y = frame_y - (canvas_height - frame_height) // 2
        target_y = max(0, min(target_y, scroll_height - canvas_height))
        self.canvas.yview_moveto(target_y / scroll_height)

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
        # If presets were reordered, notify parent to save and refresh
        if self._swaps_performed and self.callback:
            self.callback(self.current_set)

        # Unbind mousewheel before destroying
        self.canvas.unbind_all("<MouseWheel>")
        self.window.destroy()

    def _scroll_to_current_preset(self):
        """Scroll to make the current preset visible"""
        if self.current_set not in self.preset_frames:
            return

        frame = self.preset_frames[self.current_set]
        self.canvas.update_idletasks()

        # Get frame position relative to scrollable area
        frame_y = frame.winfo_y()
        frame_height = frame.winfo_height()
        canvas_height = self.canvas.winfo_height()
        scroll_height = self.scrollable_frame.winfo_height()

        if scroll_height <= canvas_height:
            return

        # Center the current preset in the visible area
        target_y = frame_y - (canvas_height - frame_height) // 2
        target_y = max(0, min(target_y, scroll_height - canvas_height))
        self.canvas.yview_moveto(target_y / scroll_height)

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
