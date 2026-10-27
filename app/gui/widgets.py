"""
Reusable GUI Widgets and Theme Manager.
Implements Windows High-DPI scaling, modern ttk styling, stat cards,
debounced search bar, and paginated table navigation controls.
"""

import sys
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, Optional
from app.config import FONT_FAMILY, FONT_SIZES, PAGE_SIZE_OPTIONS, THEMES
from app.utils.logger import get_logger

logger = get_logger("sms.widgets")


def enable_high_dpi_awareness() -> None:
    """Enable Per-Monitor DPI awareness on Windows platforms for sharp typography."""
    if sys.platform == "win32":
        try:
            import ctypes
            # Per-monitor DPI awareness
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


class ThemeManager:
    """Maintains active UI theme (Light/Dark) and configures ttk styles."""

    _instance = None

    def __new__(cls, default_theme: str = "light"):
        if cls._instance is None:
            cls._instance = super(ThemeManager, cls).__new__(cls)
            cls._instance.current_theme_name = default_theme
            cls._instance.listeners = []
        return cls._instance

    @property
    def colors(self) -> Dict[str, str]:
        return THEMES.get(self.current_theme_name, THEMES["light"])

    @property
    def is_dark(self) -> bool:
        return self.current_theme_name == "dark"

    def toggle_theme(self) -> str:
        """Switch between Light and Dark mode."""
        self.current_theme_name = "dark" if self.current_theme_name == "light" else "light"
        for callback in self.listeners:
            try:
                callback(self.colors)
            except Exception as e:
                logger.error("Error in theme callback: %s", e)
        return self.current_theme_name

    def subscribe(self, callback: Callable[[Dict[str, str]], None]) -> None:
        """Register a callback for theme changes."""
        if callback not in self.listeners:
            self.listeners.append(callback)

    def unsubscribe(self, callback: Callable[[Dict[str, str]], None]) -> None:
        """Unregister callback."""
        if callback in self.listeners:
            self.listeners.remove(callback)

    def apply_styles(self, style: ttk.Style) -> None:
        """Configure ttk styles with current theme palette."""
        c = self.colors

        # Base theme
        style.theme_use("clam")

        # Global TFrame
        style.configure("TFrame", background=c["app_bg"])
        style.configure("Surface.TFrame", background=c["surface"])
        style.configure("SurfaceAlt.TFrame", background=c["surface_alt"])
        style.configure("BorderCard.TFrame", background=c["surface"], relief="solid", borderwidth=1)

        # Labels
        style.configure(
            "TLabel",
            background=c["app_bg"],
            foreground=c["text_main"],
            font=(FONT_FAMILY, FONT_SIZES["body"]),
        )
        style.configure(
            "Surface.TLabel",
            background=c["surface"],
            foreground=c["text_main"],
            font=(FONT_FAMILY, FONT_SIZES["body"]),
        )
        style.configure(
            "Sub.TLabel",
            background=c["surface"],
            foreground=c["text_sub"],
            font=(FONT_FAMILY, FONT_SIZES["caption"]),
        )
        style.configure(
            "Title.TLabel",
            background=c["surface"],
            foreground=c["text_main"],
            font=(FONT_FAMILY, FONT_SIZES["title"], "bold"),
        )
        style.configure(
            "Display.TLabel",
            background=c["surface"],
            foreground=c["text_main"],
            font=(FONT_FAMILY, FONT_SIZES["display"], "bold"),
        )
        style.configure(
            "NavTitle.TLabel",
            background=c["nav_bg"],
            foreground=c["nav_text"],
            font=(FONT_FAMILY, FONT_SIZES["title"], "bold"),
        )
        style.configure(
            "NavSub.TLabel",
            background=c["nav_bg"],
            foreground=c["nav_sub"],
            font=(FONT_FAMILY, FONT_SIZES["caption"]),
        )

        # Primary Button
        style.configure(
            "Primary.TButton",
            background=c["primary"],
            foreground=c["text_inverse"],
            borderwidth=0,
            focuscolor=c["primary_hover"],
            font=(FONT_FAMILY, FONT_SIZES["body"], "bold"),
            padding=(12, 6),
        )
        style.map(
            "Primary.TButton",
            background=[("active", c["primary_hover"]), ("disabled", c["border"])],
            foreground=[("disabled", c["text_muted"])],
        )

        # Secondary Button
        style.configure(
            "Secondary.TButton",
            background=c["button_secondary_bg"],
            foreground=c["button_secondary_fg"],
            borderwidth=0,
            font=(FONT_FAMILY, FONT_SIZES["body"]),
            padding=(10, 5),
        )
        style.map(
            "Secondary.TButton",
            background=[("active", c["border"]), ("disabled", c["surface"])],
            foreground=[("disabled", c["text_muted"])],
        )

        # Danger Button
        style.configure(
            "Danger.TButton",
            background=c["danger"],
            foreground=c["text_inverse"],
            borderwidth=0,
            font=(FONT_FAMILY, FONT_SIZES["body"], "bold"),
            padding=(10, 5),
        )
        style.map(
            "Danger.TButton",
            background=[("active", "#DC2626")],
        )

        # Success Button
        style.configure(
            "Success.TButton",
            background=c["success"],
            foreground=c["text_inverse"],
            borderwidth=0,
            font=(FONT_FAMILY, FONT_SIZES["body"], "bold"),
            padding=(10, 5),
        )
        style.map(
            "Success.TButton",
            background=[("active", "#059669")],
        )

        # Treeview (Modern Table)
        style.configure(
            "Treeview",
            background=c["tree_bg"],
            foreground=c["tree_fg"],
            fieldbackground=c["tree_bg"],
            font=(FONT_FAMILY, FONT_SIZES["body"]),
            rowheight=32,
            borderwidth=0,
        )
        style.map(
            "Treeview",
            background=[("selected", c["tree_selected_bg"])],
            foreground=[("selected", c["tree_selected_fg"])],
        )

        style.configure(
            "Treeview.Heading",
            background=c["tree_head_bg"],
            foreground=c["tree_head_fg"],
            font=(FONT_FAMILY, FONT_SIZES["body"], "bold"),
            relief="flat",
            padding=(8, 8),
        )
        style.map(
            "Treeview.Heading",
            background=[("active", c["border"])],
        )

        # Combobox
        style.configure(
            "TCombobox",
            background=c["surface"],
            foreground=c["text_main"],
            fieldbackground=c["surface"],
            selectbackground=c["primary_light"],
            selectforeground=c["primary_dark"],
            padding=4,
        )


class StatCard(tk.Frame):
    """
    A neat metric display card with color accent, title, large value,
    and descriptive subtitle.
    """

    def __init__(
        self,
        parent: tk.Widget,
        title: str,
        value: str,
        subtitle: str,
        accent_color: str,
        icon: str = "📊",
        theme_manager: Optional[ThemeManager] = None,
        **kwargs,
    ):
        self.tm = theme_manager or ThemeManager()
        c = self.tm.colors
        super().__init__(
            parent,
            bg=c["surface"],
            highlightbackground=c["border"],
            highlightthickness=1,
            padx=16,
            pady=14,
            **kwargs,
        )
        self.accent_color = accent_color
        self.icon = icon

        # Top Accent Strip
        self.strip = tk.Frame(self, bg=accent_color, height=4)
        self.strip.pack(fill="x", side="top", pady=(0, 10))

        # Header Row (Icon + Title)
        header_frame = tk.Frame(self, bg=c["surface"])
        header_frame.pack(fill="x", anchor="w")

        self.icon_label = tk.Label(
            header_frame,
            text=icon,
            font=(FONT_FAMILY, 14),
            bg=c["surface"],
            fg=accent_color,
        )
        self.icon_label.pack(side="left", padx=(0, 8))

        self.title_label = tk.Label(
            header_frame,
            text=title.upper(),
            font=(FONT_FAMILY, FONT_SIZES["badge"], "bold"),
            bg=c["surface"],
            fg=c["text_sub"],
        )
        self.title_label.pack(side="left")

        # Big Value
        self.val_label = tk.Label(
            self,
            text=value,
            font=(FONT_FAMILY, 20, "bold"),
            bg=c["surface"],
            fg=c["text_main"],
        )
        self.val_label.pack(anchor="w", pady=(6, 2))

        # Subtitle
        self.sub_label = tk.Label(
            self,
            text=subtitle,
            font=(FONT_FAMILY, FONT_SIZES["caption"]),
            bg=c["surface"],
            fg=c["text_muted"],
        )
        self.sub_label.pack(anchor="w")

        self.tm.subscribe(self.update_theme)

    def set_value(self, value: str, subtitle: Optional[str] = None) -> None:
        self.val_label.config(text=value)
        if subtitle is not None:
            self.sub_label.config(text=subtitle)

    def update_theme(self, colors: Dict[str, str]) -> None:
        self.config(bg=colors["surface"], highlightbackground=colors["border"])
        self.icon_label.config(bg=colors["surface"])
        self.title_label.config(bg=colors["surface"], fg=colors["text_sub"])
        self.val_label.config(bg=colors["surface"], fg=colors["text_main"])
        self.sub_label.config(bg=colors["surface"], fg=colors["text_muted"])


class DebouncedSearchBar(tk.Frame):
    """
    Search bar with a search icon, clear button, and 300ms debounce
    so typing feels responsive without spamming database queries.
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_search_callback: Callable[[str], None],
        placeholder: str = "Search by roll number, name, or email...",
        debounce_ms: int = 300,
        theme_manager: Optional[ThemeManager] = None,
        **kwargs,
    ):
        self.tm = theme_manager or ThemeManager()
        c = self.tm.colors
        super().__init__(parent, bg=c["surface"], highlightbackground=c["border"], highlightthickness=1, **kwargs)

        self.on_search = on_search_callback
        self.placeholder = placeholder
        self.debounce_ms = debounce_ms
        self._after_id = None

        # Search Icon Label
        self.icon_lbl = tk.Label(self, text="🔍", font=(FONT_FAMILY, 10), bg=c["surface"], fg=c["text_muted"])
        self.icon_lbl.pack(side="left", padx=(10, 4))

        # Entry
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_text_changed)
        self.entry = tk.Entry(
            self,
            textvariable=self.search_var,
            font=(FONT_FAMILY, FONT_SIZES["body"]),
            bg=c["surface"],
            fg=c["text_main"],
            relief="flat",
            borderwidth=0,
            insertbackground=c["text_main"],
        )
        self.entry.pack(side="left", fill="both", expand=True, padx=(0, 6), pady=6)

        # Clear Button
        self.clear_btn = tk.Button(
            self,
            text="✕",
            font=(FONT_FAMILY, 9),
            bg=c["surface"],
            fg=c["text_muted"],
            activebackground=c["surface"],
            activeforeground=c["text_main"],
            relief="flat",
            borderwidth=0,
            cursor="hand2",
            command=self.clear,
        )
        self.clear_btn.pack(side="right", padx=(0, 8))

        self.tm.subscribe(self.update_theme)

    def _on_text_changed(self, *args) -> None:
        if self._after_id:
            self.after_cancel(self._after_id)
        self._after_id = self.after(self.debounce_ms, self._trigger_callback)

    def _trigger_callback(self) -> None:
        query = self.search_var.get().strip()
        self.on_search(query)

    def clear(self) -> None:
        self.search_var.set("")
        self.entry.focus()

    def get_query(self) -> str:
        return self.search_var.get().strip()

    def update_theme(self, colors: Dict[str, str]) -> None:
        self.config(bg=colors["surface"], highlightbackground=colors["border"])
        self.icon_lbl.config(bg=colors["surface"], fg=colors["text_muted"])
        self.entry.config(bg=colors["surface"], fg=colors["text_main"], insertbackground=colors["text_main"])
        self.clear_btn.config(bg=colors["surface"], fg=colors["text_muted"])


class PaginationControl(tk.Frame):
    """
    Pagination bar with page size selection, page navigation buttons,
    and record count summary.
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_page_change_callback: Callable[[int, int], None],
        theme_manager: Optional[ThemeManager] = None,
        **kwargs,
    ):
        self.tm = theme_manager or ThemeManager()
        c = self.tm.colors
        super().__init__(parent, bg=c["surface"], highlightbackground=c["border"], highlightthickness=1, **kwargs)

        self.on_page_change = on_page_change_callback
        self.current_page = 1
        self.total_pages = 1
        self.total_records = 0

        # Left: Record summary label
        self.summary_lbl = tk.Label(
            self,
            text="Showing 0 of 0 records",
            font=(FONT_FAMILY, FONT_SIZES["caption"]),
            bg=c["surface"],
            fg=c["text_sub"],
        )
        self.summary_lbl.pack(side="left", padx=14, pady=8)

        # Right container: Page size + nav buttons
        right_frame = tk.Frame(self, bg=c["surface"])
        right_frame.pack(side="right", padx=12, pady=6)

        # Page Size Dropdown
        tk.Label(
            right_frame,
            text="Per page:",
            font=(FONT_FAMILY, FONT_SIZES["caption"]),
            bg=c["surface"],
            fg=c["text_sub"],
        ).pack(side="left", padx=(0, 4))

        self.page_size_var = tk.IntVar(value=10)
        self.size_combo = ttk.Combobox(
            right_frame,
            textvariable=self.page_size_var,
            values=PAGE_SIZE_OPTIONS,
            width=3,
            state="readonly",
        )
        self.size_combo.pack(side="left", padx=(0, 16))
        self.size_combo.bind("<<ComboboxSelected>>", self._on_size_change)

        # Navigation Buttons
        btn_kwargs = {"width": 3, "relief": "flat", "cursor": "hand2", "font": (FONT_FAMILY, 9)}

        self.btn_first = tk.Button(right_frame, text="⏮", command=self.go_first, **btn_kwargs)
        self.btn_first.pack(side="left", padx=2)

        self.btn_prev = tk.Button(right_frame, text="◀", command=self.go_prev, **btn_kwargs)
        self.btn_prev.pack(side="left", padx=2)

        self.page_lbl = tk.Label(
            right_frame,
            text="Page 1 of 1",
            font=(FONT_FAMILY, FONT_SIZES["body"], "bold"),
            bg=c["surface"],
            fg=c["text_main"],
            padx=8,
        )
        self.page_lbl.pack(side="left", padx=4)

        self.btn_next = tk.Button(right_frame, text="▶", command=self.go_next, **btn_kwargs)
        self.btn_next.pack(side="left", padx=2)

        self.btn_last = tk.Button(right_frame, text="⏭", command=self.go_last, **btn_kwargs)
        self.btn_last.pack(side="left", padx=2)

        self._style_buttons(c)
        self.tm.subscribe(self.update_theme)

    def _style_buttons(self, c: Dict[str, str]) -> None:
        for b in [self.btn_first, self.btn_prev, self.btn_next, self.btn_last]:
            b.config(bg=c["button_secondary_bg"], fg=c["button_secondary_fg"])

    def update_state(self, current_page: int, total_pages: int, total_records: int, page_size: int) -> None:
        self.current_page = current_page
        self.total_pages = max(1, total_pages)
        self.total_records = total_records
        self.page_size_var.set(page_size)

        # Update labels
        start = ((current_page - 1) * page_size) + 1 if total_records > 0 else 0
        end = min(current_page * page_size, total_records)
        self.summary_lbl.config(text=f"Showing {start}–{end} of {total_records} records")
        self.page_lbl.config(text=f"Page {current_page} of {self.total_pages}")

        # Update button enable/disable
        has_prev = current_page > 1
        has_next = current_page < self.total_pages

        self.btn_first.config(state="normal" if has_prev else "disabled")
        self.btn_prev.config(state="normal" if has_prev else "disabled")
        self.btn_next.config(state="normal" if has_next else "disabled")
        self.btn_last.config(state="normal" if has_next else "disabled")

    def _on_size_change(self, event=None) -> None:
        self.current_page = 1
        self.on_page_change(1, self.page_size_var.get())

    def go_first(self) -> None:
        if self.current_page > 1:
            self.on_page_change(1, self.page_size_var.get())

    def go_prev(self) -> None:
        if self.current_page > 1:
            self.on_page_change(self.current_page - 1, self.page_size_var.get())

    def go_next(self) -> None:
        if self.current_page < self.total_pages:
            self.on_page_change(self.current_page + 1, self.page_size_var.get())

    def go_last(self) -> None:
        if self.current_page < self.total_pages:
            self.on_page_change(self.total_pages, self.page_size_var.get())

    def update_theme(self, colors: Dict[str, str]) -> None:
        self.config(bg=colors["surface"], highlightbackground=colors["border"])
        self.summary_lbl.config(bg=colors["surface"], fg=colors["text_sub"])
        self.page_lbl.config(bg=colors["surface"], fg=colors["text_main"])
        self._style_buttons(colors)
