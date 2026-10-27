"""
Dashboard and Institutional Analytics View.
Displays overview metric cards, department enrollment statistics,
and year-level distributions.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, Optional
from app.config import FONT_FAMILY, FONT_SIZES
from app.gui.widgets import StatCard, ThemeManager
from app.services.student_service import StudentService
from app.utils.logger import get_logger

logger = get_logger("sms.dashboard_view")


class DashboardView(tk.Frame):
    """Analytics and executive dashboard panel."""

    def __init__(
        self,
        parent: tk.Widget,
        student_service: StudentService,
        on_navigate_students: Optional[Callable[[], None]] = None,
        theme_manager: Optional[ThemeManager] = None,
        **kwargs,
    ):
        self.tm = theme_manager or ThemeManager()
        c = self.tm.colors
        super().__init__(parent, bg=c["app_bg"], **kwargs)

        self.service = student_service
        self.on_navigate_students = on_navigate_students

        self._build_ui()
        self.refresh()
        self.tm.subscribe(self.update_theme)

    def _build_ui(self) -> None:
        c = self.tm.colors

        # Top Metric Cards Row (4 cards in a grid)
        self.cards_frame = tk.Frame(self, bg=c["app_bg"])
        self.cards_frame.pack(fill="x", padx=16, pady=(16, 12))

        for i in range(4):
            self.cards_frame.columnconfigure(i, weight=1, uniform="stat_cards")

        self.card_total = StatCard(
            self.cards_frame,
            title="Total Students",
            value="0",
            subtitle="Registered in database",
            accent_color=c["primary"],
            icon="👥",
            theme_manager=self.tm,
        )
        self.card_total.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self.card_active = StatCard(
            self.cards_frame,
            title="Active Records",
            value="0",
            subtitle="Currently enrolled",
            accent_color=c["success"],
            icon="🎓",
            theme_manager=self.tm,
        )
        self.card_active.grid(row=0, column=1, sticky="nsew", padx=4)

        self.card_archived = StatCard(
            self.cards_frame,
            title="Archived Records",
            value="0",
            subtitle="Soft-deleted students",
            accent_color=c["warning"],
            icon="📁",
            theme_manager=self.tm,
        )
        self.card_archived.grid(row=0, column=2, sticky="nsew", padx=4)

        self.card_gpa = StatCard(
            self.cards_frame,
            title="Average GPA",
            value="0.00",
            subtitle="Campus-wide average (0-10)",
            accent_color=c["info"],
            icon="⭐",
            theme_manager=self.tm,
        )
        self.card_gpa.grid(row=0, column=3, sticky="nsew", padx=(8, 0))

        # Bottom Analytics Content (Two Panels)
        content_frame = tk.Frame(self, bg=c["app_bg"])
        content_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        content_frame.columnconfigure(0, weight=3, uniform="analytics_cols")
        content_frame.columnconfigure(1, weight=2, uniform="analytics_cols")
        content_frame.rowconfigure(0, weight=1)

        # Panel 1: Department Breakdown Table
        dept_panel = tk.Frame(
            content_frame,
            bg=c["surface"],
            highlightbackground=c["border"],
            highlightthickness=1,
            padx=16,
            pady=14,
        )
        dept_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        tk.Label(
            dept_panel,
            text="🏢 Department Breakdown & Performance",
            font=(FONT_FAMILY, FONT_SIZES["subtitle"], "bold"),
            bg=c["surface"],
            fg=c["text_main"],
        ).pack(anchor="w", pady=(0, 10))

        # Department Treeview
        columns = ("dept", "students", "avg_gpa")
        self.dept_tree = ttk.Treeview(dept_panel, columns=columns, show="headings", height=8)
        self.dept_tree.heading("dept", text="Department Name")
        self.dept_tree.heading("students", text="Enrolled")
        self.dept_tree.heading("avg_gpa", text="Avg GPA")

        self.dept_tree.column("dept", width=240, anchor="w")
        self.dept_tree.column("students", width=80, anchor="center")
        self.dept_tree.column("avg_gpa", width=80, anchor="center")
        self.dept_tree.pack(fill="both", expand=True)

        # Panel 2: Year Level Distribution
        year_panel = tk.Frame(
            content_frame,
            bg=c["surface"],
            highlightbackground=c["border"],
            highlightthickness=1,
            padx=16,
            pady=14,
        )
        year_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        tk.Label(
            year_panel,
            text="📅 Enrollment by Academic Year",
            font=(FONT_FAMILY, FONT_SIZES["subtitle"], "bold"),
            bg=c["surface"],
            fg=c["text_main"],
        ).pack(anchor="w", pady=(0, 10))

        # Year Level Treeview
        year_cols = ("year", "count")
        self.year_tree = ttk.Treeview(year_panel, columns=year_cols, show="headings", height=8)
        self.year_tree.heading("year", text="Academic Year")
        self.year_tree.heading("count", text="Students Enrolled")
        self.year_tree.column("year", width=140, anchor="w")
        self.year_tree.column("count", width=100, anchor="center")
        self.year_tree.pack(fill="both", expand=True)

    def refresh(self) -> None:
        """Fetch latest statistics and refresh dashboard views."""
        try:
            stats = self.service.get_dashboard_stats()

            # Update Stat Cards
            self.card_total.set_value(str(stats["total_count"]))
            self.card_active.set_value(str(stats["active_count"]))
            self.card_archived.set_value(str(stats["archived_count"]))
            self.card_gpa.set_value(f"{stats['avg_gpa']:.2f}")

            # Populate Department Treeview
            for item in self.dept_tree.get_children():
                self.dept_tree.delete(item)

            for d in stats["department_breakdown"]:
                gpa_disp = f"{d['avg_gpa']:.2f}" if d["avg_gpa"] is not None else "N/A"
                self.dept_tree.insert("", "end", values=(d["department"], d["student_count"], gpa_disp))

            # Populate Year Level Treeview
            for item in self.year_tree.get_children():
                self.year_tree.delete(item)

            for y in stats["year_breakdown"]:
                self.year_tree.insert("", "end", values=(f"Year {y['year_level']}", y["student_count"]))

        except Exception as e:
            logger.error("Error refreshing dashboard stats: %s", e)

    def update_theme(self, colors: Dict[str, str]) -> None:
        self.config(bg=colors["app_bg"])
        self.cards_frame.config(bg=colors["app_bg"])
