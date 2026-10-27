"""
Main Application Window for AcademiaSMS.
Combines Students Registry, Analytics Dashboard, and Audit Trail
into a cohesive, modern desktop interface.
"""

import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Dict, List, Optional
from pathlib import Path

from app.config import (
    APP_NAME,
    APP_SUBTITLE,
    APP_VERSION,
    FONT_FAMILY,
    FONT_SIZES,
)
from app.gui.dashboard_view import DashboardView
from app.gui.student_form import StudentFormDialog
from app.gui.widgets import (
    DebouncedSearchBar,
    PaginationControl,
    ThemeManager,
    enable_high_dpi_awareness,
)
from app.models.student import Department, Student
from app.models.user import User
from app.services.student_service import StudentService
from app.utils.importer import (
    export_students_to_csv,
    export_students_to_pdf,
    import_students_from_file,
)
from app.utils.logger import get_logger

logger = get_logger("sms.main_window")


class MainWindow:
    """The primary application window for staff and administrators."""

    def __init__(
        self,
        student_service: StudentService,
        current_user: User,
        on_logout_callback: Optional[Callable[[], None]] = None,
        theme_manager: Optional[ThemeManager] = None,
    ):
        enable_high_dpi_awareness()
        self.service = student_service
        self.current_user = current_user
        self.on_logout = on_logout_callback
        self.tm = theme_manager or ThemeManager()

        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} - Enterprise Academic Portal")
        self.root.geometry("1200x780")
        self.root.minsize(1000, 650)

        # Center on screen
        self.root.eval("tk::PlaceWindow . center")

        self.style = ttk.Style()
        self.tm.apply_styles(self.style)

        # State variables
        self.current_page = 1
        self.page_size = 10
        self.total_pages = 1
        self.total_records = 0
        self.sort_by = "last_name"
        self.sort_dir = "ASC"
        self.selected_student_id: Optional[int] = None
        self.students_cache: List[Student] = []

        # Load departments
        self.departments: List[Department] = self.service.get_departments()
        self.dept_name_to_id = {d.name: d.department_id for d in self.departments}

        self._build_ui()
        self._load_students()
        self.tm.subscribe(self.update_theme)

    # -------------------------------------------------------------------------
    # UI Construction
    # -------------------------------------------------------------------------
    def _build_ui(self) -> None:
        c = self.tm.colors
        self.root.configure(bg=c["app_bg"])

        # 1. Top Navigation Bar (Brand, Tabs, User Info, Theme, Logout)
        self._build_top_navbar()

        # 2. Main Content Container
        self.content_container = tk.Frame(self.root, bg=c["app_bg"])
        self.content_container.pack(fill="both", expand=True)

        # View Tabs: Students Registry, Dashboard, Audit Logs
        self.views: Dict[str, tk.Frame] = {}

        self.views["students"] = self._build_students_view()
        self.views["dashboard"] = DashboardView(
            self.content_container,
            self.service,
            theme_manager=self.tm,
        )
        self.views["audit"] = self._build_audit_view()

        # Default active view
        self.switch_view("students")

        # 3. Bottom Status Bar
        self._build_status_bar()

    def _build_top_navbar(self) -> None:
        c = self.tm.colors
        self.nav_frame = tk.Frame(self.root, bg=c["nav_bg"], height=62, padx=16, pady=8)
        self.nav_frame.pack(fill="x", side="top")

        # Brand / Logo
        brand_frame = tk.Frame(self.nav_frame, bg=c["nav_bg"])
        brand_frame.pack(side="left", padx=(4, 24))

        tk.Label(
            brand_frame,
            text="🎓",
            font=(FONT_FAMILY, 20),
            bg=c["nav_bg"],
            fg=c["primary"],
        ).pack(side="left", padx=(0, 8))

        brand_text_frame = tk.Frame(brand_frame, bg=c["nav_bg"])
        brand_text_frame.pack(side="left")

        tk.Label(
            brand_text_frame,
            text=APP_NAME,
            font=(FONT_FAMILY, FONT_SIZES["title"], "bold"),
            bg=c["nav_bg"],
            fg=c["nav_text"],
        ).pack(anchor="w")

        tk.Label(
            brand_text_frame,
            text=APP_SUBTITLE,
            font=(FONT_FAMILY, 8),
            bg=c["nav_bg"],
            fg=c["nav_sub"],
        ).pack(anchor="w")

        # View Navigation Buttons
        self.nav_btn_frame = tk.Frame(self.nav_frame, bg=c["nav_bg"])
        self.nav_btn_frame.pack(side="left", padx=10)

        self.nav_btns: Dict[str, tk.Button] = {}
        for view_key, label in [
            ("students", "🎓 Students"),
            ("dashboard", "📊 Analytics"),
            ("audit", "📜 Audit Logs"),
        ]:
            btn = tk.Button(
                self.nav_btn_frame,
                text=label,
                font=(FONT_FAMILY, FONT_SIZES["body"], "bold"),
                bg=c["nav_bg"],
                fg=c["nav_text"],
                activebackground=c["primary"],
                activeforeground="#FFFFFF",
                relief="flat",
                padx=12,
                pady=6,
                cursor="hand2",
                command=lambda k=view_key: self.switch_view(k),
            )
            btn.pack(side="left", padx=4)
            self.nav_btns[view_key] = btn

        # Right Controls: User Profile Badge, Theme Toggle, Logout
        right_frame = tk.Frame(self.nav_frame, bg=c["nav_bg"])
        right_frame.pack(side="right")

        # User Profile Pill
        user_badge_frame = tk.Frame(right_frame, bg="#1E293B", padx=10, pady=4)
        user_badge_frame.pack(side="left", padx=8)

        role_color = c["success"] if self.current_user.is_admin else c["info"]
        tk.Label(
            user_badge_frame,
            text=f"👤 {self.current_user.username}",
            font=(FONT_FAMILY, FONT_SIZES["caption"], "bold"),
            bg="#1E293B",
            fg="#F8FAFC",
        ).pack(side="left")

        tk.Label(
            user_badge_frame,
            text=f"[{self.current_user.role}]",
            font=(FONT_FAMILY, 8, "bold"),
            bg="#1E293B",
            fg=role_color,
        ).pack(side="left", padx=(4, 0))

        # Theme Toggle Button
        theme_icon = "☀️ Light" if self.tm.is_dark else "🌙 Dark"
        self.theme_btn = tk.Button(
            right_frame,
            text=theme_icon,
            font=(FONT_FAMILY, FONT_SIZES["caption"]),
            bg="#334155",
            fg="#F8FAFC",
            activebackground="#475569",
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._handle_theme_toggle,
        )
        self.theme_btn.pack(side="left", padx=4)

        # Sign Out Button
        logout_btn = tk.Button(
            right_frame,
            text="🚪 Sign Out",
            font=(FONT_FAMILY, FONT_SIZES["caption"]),
            bg="#DC2626",
            fg="#FFFFFF",
            activebackground="#B91C1C",
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._handle_logout,
        )
        logout_btn.pack(side="left", padx=(4, 0))

    def _build_students_view(self) -> tk.Frame:
        """Construct the Students Registry tab."""
        c = self.tm.colors
        view = tk.Frame(self.content_container, bg=c["app_bg"])

        # 1. Action Toolbar
        toolbar = tk.Frame(view, bg=c["app_bg"], padx=16, pady=12)
        toolbar.pack(fill="x")

        # Action Buttons (Left)
        left_actions = tk.Frame(toolbar, bg=c["app_bg"])
        left_actions.pack(side="left")

        ttk.Button(
            left_actions,
            text="➕ Add Student",
            style="Primary.TButton",
            command=self._open_add_student_dialog,
            cursor="hand2",
        ).pack(side="left", padx=(0, 6))

        ttk.Button(
            left_actions,
            text="✏️ Edit",
            style="Secondary.TButton",
            command=self._open_edit_student_dialog,
            cursor="hand2",
        ).pack(side="left", padx=4)

        ttk.Button(
            left_actions,
            text="🗑️ Delete / Archive",
            style="Secondary.TButton",
            command=self._handle_delete_action,
            cursor="hand2",
        ).pack(side="left", padx=4)

        # Right Action Utilities: Import, Export CSV, Export PDF, Backup
        right_actions = tk.Frame(toolbar, bg=c["app_bg"])
        right_actions.pack(side="right")

        ttk.Button(
            right_actions,
            text="📥 Import",
            style="Secondary.TButton",
            command=self._handle_import_file,
            cursor="hand2",
        ).pack(side="left", padx=4)

        ttk.Button(
            right_actions,
            text="📄 Export CSV",
            style="Secondary.TButton",
            command=self._handle_export_csv,
            cursor="hand2",
        ).pack(side="left", padx=4)

        ttk.Button(
            right_actions,
            text="📑 Export PDF",
            style="Secondary.TButton",
            command=self._handle_export_pdf,
            cursor="hand2",
        ).pack(side="left", padx=4)

        ttk.Button(
            right_actions,
            text="💾 Backup DB",
            style="Secondary.TButton",
            command=self._handle_backup_db,
            cursor="hand2",
        ).pack(side="left", padx=(4, 0))

        # 2. Filter Bar
        filter_card = tk.Frame(
            view,
            bg=c["surface"],
            highlightbackground=c["border"],
            highlightthickness=1,
            padx=14,
            pady=10,
        )
        filter_card.pack(fill="x", padx=16, pady=(0, 10))

        # Debounced Search Bar
        self.search_bar = DebouncedSearchBar(
            filter_card,
            on_search_callback=self._on_search_triggered,
            theme_manager=self.tm,
        )
        self.search_bar.pack(side="left", fill="x", expand=True, padx=(0, 12))

        # Department Filter Dropdown
        tk.Label(
            filter_card,
            text="Dept:",
            font=(FONT_FAMILY, FONT_SIZES["caption"], "bold"),
            bg=c["surface"],
            fg=c["text_sub"],
        ).pack(side="left", padx=(0, 4))

        dept_options = ["All Departments"] + [d.name for d in self.departments]
        self.filter_dept_var = tk.StringVar(value="All Departments")
        self.filter_dept_combo = ttk.Combobox(
            filter_card,
            textvariable=self.filter_dept_var,
            values=dept_options,
            state="readonly",
            width=20,
        )
        self.filter_dept_combo.pack(side="left", padx=(0, 12))
        self.filter_dept_combo.bind("<<ComboboxSelected>>", lambda e: self._on_filter_changed())

        # Year Level Filter Dropdown
        tk.Label(
            filter_card,
            text="Year:",
            font=(FONT_FAMILY, FONT_SIZES["caption"], "bold"),
            bg=c["surface"],
            fg=c["text_sub"],
        ).pack(side="left", padx=(0, 4))

        year_options = ["All Years", "Year 1", "Year 2", "Year 3", "Year 4", "Year 5", "Year 6"]
        self.filter_year_var = tk.StringVar(value="All Years")
        self.filter_year_combo = ttk.Combobox(
            filter_card,
            textvariable=self.filter_year_var,
            values=year_options,
            state="readonly",
            width=10,
        )
        self.filter_year_combo.pack(side="left", padx=(0, 12))
        self.filter_year_combo.bind("<<ComboboxSelected>>", lambda e: self._on_filter_changed())

        # Show Archived Records Checkbox
        self.show_archived_var = tk.BooleanVar(value=False)
        self.archived_cb = tk.Checkbutton(
            filter_card,
            text="Show Archived",
            variable=self.show_archived_var,
            font=(FONT_FAMILY, FONT_SIZES["caption"]),
            bg=c["surface"],
            fg=c["text_sub"],
            activebackground=c["surface"],
            command=self._on_filter_changed,
        )
        self.archived_cb.pack(side="left", padx=(0, 8))

        # Reset Filter Button
        reset_btn = tk.Button(
            filter_card,
            text="↺ Reset",
            font=(FONT_FAMILY, FONT_SIZES["caption"]),
            bg=c["button_secondary_bg"],
            fg=c["button_secondary_fg"],
            relief="flat",
            padx=8,
            pady=2,
            cursor="hand2",
            command=self._reset_filters,
        )
        reset_btn.pack(side="left")

        # 3. Students Table (Treeview inside Surface Card)
        table_card = tk.Frame(
            view,
            bg=c["surface"],
            highlightbackground=c["border"],
            highlightthickness=1,
        )
        table_card.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        columns = (
            "roll_number",
            "name",
            "department",
            "year",
            "gpa",
            "email",
            "phone",
            "status",
            "updated_at",
        )
        self.tree = ttk.Treeview(table_card, columns=columns, show="headings", selectmode="browse")

        # Configure columns with clickable sort headers
        col_headers = {
            "roll_number": ("Roll Number", 100, "center"),
            "name": ("Student Name", 160, "w"),
            "department": ("Department", 180, "w"),
            "year": ("Year", 70, "center"),
            "gpa": ("GPA", 65, "center"),
            "email": ("Email Address", 190, "w"),
            "phone": ("Phone", 100, "center"),
            "status": ("Status", 80, "center"),
            "updated_at": ("Last Modified", 130, "center"),
        }

        for col_id, (header_text, width, anchor) in col_headers.items():
            self.tree.heading(
                col_id,
                text=header_text,
                command=lambda c_id=col_id: self._on_column_header_click(c_id),
            )
            self.tree.column(col_id, width=width, anchor=anchor)

        # Scrollbars
        v_scroll = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scroll.set)
        v_scroll.pack(side="right", fill="y")

        h_scroll = ttk.Scrollbar(table_card, orient="horizontal", command=self.tree.xview)
        self.tree.configure(xscrollcommand=h_scroll.set)
        h_scroll.pack(side="bottom", fill="x")

        self.tree.pack(fill="both", expand=True)

        # Bind events
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", lambda e: self._open_edit_student_dialog())

        # Context Menu
        self._build_context_menu()

        # 4. Pagination Controls Bar
        self.pagination = PaginationControl(
            view,
            on_page_change_callback=self._on_page_changed,
            theme_manager=self.tm,
        )
        self.pagination.pack(fill="x", padx=16, pady=(0, 10))

        return view

    def _build_audit_view(self) -> tk.Frame:
        """Construct the Audit Logs tab."""
        c = self.tm.colors
        view = tk.Frame(self.content_container, bg=c["app_bg"])

        # Toolbar
        bar = tk.Frame(view, bg=c["app_bg"], padx=16, pady=12)
        bar.pack(fill="x")

        tk.Label(
            bar,
            text="📜 System Audit Trail (Database Write History)",
            font=(FONT_FAMILY, FONT_SIZES["title"], "bold"),
            bg=c["app_bg"],
            fg=c["text_main"],
        ).pack(side="left")

        ttk.Button(
            bar,
            text="↺ Refresh Audit Trail",
            style="Secondary.TButton",
            command=self._load_audit_logs,
            cursor="hand2",
        ).pack(side="right")

        # Table Container
        card = tk.Frame(
            view,
            bg=c["surface"],
            highlightbackground=c["border"],
            highlightthickness=1,
        )
        card.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        cols = ("id", "user", "action", "table", "record_id", "details", "timestamp")
        self.audit_tree = ttk.Treeview(card, columns=cols, show="headings")

        audit_headers = {
            "id": ("Log ID", 60, "center"),
            "user": ("Staff User", 100, "w"),
            "action": ("Action", 90, "center"),
            "table": ("Target Table", 90, "center"),
            "record_id": ("Record ID", 80, "center"),
            "details": ("Change Details", 340, "w"),
            "timestamp": ("Timestamp", 140, "center"),
        }

        for cid, (txt, w, a) in audit_headers.items():
            self.audit_tree.heading(cid, text=txt)
            self.audit_tree.column(cid, width=w, anchor=a)

        audit_v_scroll = ttk.Scrollbar(card, orient="vertical", command=self.audit_tree.yview)
        self.audit_tree.configure(yscrollcommand=audit_v_scroll.set)
        audit_v_scroll.pack(side="right", fill="y")

        self.audit_tree.pack(fill="both", expand=True)
        return view

    def _build_context_menu(self) -> None:
        """Build right-click context menu for rows."""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="✏️ Edit Student", command=self._open_edit_student_dialog)
        self.context_menu.add_command(label="🗑️ Delete / Archive", command=self._handle_delete_action)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="📋 Copy Roll Number", command=self._copy_selected_roll_number)

        self.tree.bind("<Button-3>", self._show_context_menu)

    def _show_context_menu(self, event) -> None:
        row_id = self.tree.identify_row(event.y)
        if row_id:
            self.tree.selection_set(row_id)
            self._on_tree_select()
            self.context_menu.post(event.x_root, event.y_root)

    def _copy_selected_roll_number(self) -> None:
        student = self._get_selected_student()
        if student:
            self.root.clipboard_clear()
            self.root.clipboard_append(student.roll_number)

    def _build_status_bar(self) -> None:
        c = self.tm.colors
        self.status_bar = tk.Frame(self.root, bg=c["surface_alt"], height=28, padx=16, pady=4)
        self.status_bar.pack(fill="x", side="bottom")

        # Database indicator
        self.db_status_lbl = tk.Label(
            self.status_bar,
            text="● SQLite Database: Connected (WAL Mode)",
            font=(FONT_FAMILY, 8),
            bg=c["surface_alt"],
            fg=c["success"],
        )
        self.db_status_lbl.pack(side="left")

        # Version & Role
        self.version_lbl = tk.Label(
            self.status_bar,
            text=f"{APP_NAME} v{APP_VERSION} | Logged in as: {self.current_user.username} ({self.current_user.role})",
            font=(FONT_FAMILY, 8),
            bg=c["surface_alt"],
            fg=c["text_muted"],
        )
        self.version_lbl.pack(side="right")

    # -------------------------------------------------------------------------
    # View Switching
    # -------------------------------------------------------------------------
    def switch_view(self, view_name: str) -> None:
        """Switch between Students, Dashboard, and Audit views."""
        c = self.tm.colors
        for name, frame in self.views.items():
            if name == view_name:
                frame.pack(fill="both", expand=True)
                # Highlight active button
                if name in self.nav_btns:
                    self.nav_btns[name].config(bg=c["primary"], fg="#FFFFFF")
            else:
                frame.pack_forget()
                if name in self.nav_btns:
                    self.nav_btns[name].config(bg=c["nav_bg"], fg=c["nav_text"])

        # Auto-refresh data when switching
        if view_name == "dashboard":
            self.views["dashboard"].refresh()
        elif view_name == "audit":
            self._load_audit_logs()
        elif view_name == "students":
            self._load_students()

    # -------------------------------------------------------------------------
    # Data Loading & Pagination
    # -------------------------------------------------------------------------
    def _load_students(self) -> None:
        """Fetch filtered and paginated students from service layer."""
        # Query filter
        query = self.search_bar.get_query() if hasattr(self, "search_bar") else ""

        # Dept filter
        dept_str = self.filter_dept_var.get() if hasattr(self, "filter_dept_var") else "All Departments"
        dept_id = self.dept_name_to_id.get(dept_str)

        # Year filter
        year_str = self.filter_year_var.get() if hasattr(self, "filter_year_var") else "All Years"
        year_num = int(year_str.replace("Year ", "")) if "Year" in year_str else None

        include_archived = self.show_archived_var.get() if hasattr(self, "show_archived_var") else False

        students, total_records, total_pages = self.service.search_students(
            query=query,
            department_id=dept_id,
            year_level=year_num,
            include_archived=include_archived,
            sort_by=self.sort_by,
            sort_dir=self.sort_dir,
            page=self.current_page,
            page_size=self.page_size,
        )

        self.students_cache = students
        self.total_records = total_records
        self.total_pages = total_pages

        # Populate tree
        for item in self.tree.get_children():
            self.tree.delete(item)

        for s in students:
            status_text = "Archived" if s.is_archived else "Active"
            gpa_display = f"{s.gpa:.2f}" if s.gpa is not None else "-"
            updated_display = (s.updated_at or "")[:19]

            self.tree.insert(
                "",
                "end",
                iid=str(s.student_id),
                values=(
                    s.roll_number,
                    s.full_name,
                    s.department_name or "N/A",
                    f"Year {s.year_level}",
                    gpa_display,
                    s.email,
                    s.phone or "-",
                    status_text,
                    updated_display,
                ),
            )

        # Update pagination control
        if hasattr(self, "pagination"):
            self.pagination.update_state(
                current_page=self.current_page,
                total_pages=self.total_pages,
                total_records=self.total_records,
                page_size=self.page_size,
            )

    def _load_audit_logs(self) -> None:
        """Fetch and populate audit logs."""
        try:
            logs = self.service.get_audit_logs(limit=150)
            for item in self.audit_tree.get_children():
                self.audit_tree.delete(item)

            for log in logs:
                self.audit_tree.insert(
                    "",
                    "end",
                    values=(
                        log["log_id"],
                        log.get("username") or "System",
                        log["action"],
                        log["table_name"],
                        log["record_id"],
                        log["details"] or "-",
                        str(log["changed_at"])[:19],
                    ),
                )
        except Exception as e:
            logger.error("Error loading audit logs: %s", e)

    # -------------------------------------------------------------------------
    # Filter & Search Handlers
    # -------------------------------------------------------------------------
    def _on_search_triggered(self, query: str) -> None:
        self.current_page = 1
        self._load_students()

    def _on_filter_changed(self) -> None:
        self.current_page = 1
        self._load_students()

    def _reset_filters(self) -> None:
        self.search_bar.clear()
        self.filter_dept_var.set("All Departments")
        self.filter_year_var.set("All Years")
        self.show_archived_var.set(False)
        self.sort_by = "last_name"
        self.sort_dir = "ASC"
        self.current_page = 1
        self._load_students()

    def _on_page_changed(self, new_page: int, new_page_size: int) -> None:
        self.current_page = new_page
        self.page_size = new_page_size
        self._load_students()

    def _on_column_header_click(self, col_id: str) -> None:
        """Toggle sort column and direction when table header is clicked."""
        if self.sort_by == col_id:
            self.sort_dir = "DESC" if self.sort_dir == "ASC" else "ASC"
        else:
            self.sort_by = col_id
            self.sort_dir = "ASC"

        self.current_page = 1
        self._load_students()

    def _on_tree_select(self, event=None) -> None:
        selection = self.tree.selection()
        if selection:
            try:
                self.selected_student_id = int(selection[0])
            except ValueError:
                self.selected_student_id = None
        else:
            self.selected_student_id = None

    def _get_selected_student(self) -> Optional[Student]:
        if not self.selected_student_id:
            return None
        for s in self.students_cache:
            if s.student_id == self.selected_student_id:
                return s
        return self.service.get_student(self.selected_student_id)

    # -------------------------------------------------------------------------
    # Dialogs & Action Handlers
    # -------------------------------------------------------------------------
    def _open_add_student_dialog(self) -> None:
        StudentFormDialog(
            self.root,
            self.service,
            self.current_user,
            student=None,
            on_save_callback=self._load_students,
            theme_manager=self.tm,
        )

    def _open_edit_student_dialog(self) -> None:
        student = self._get_selected_student()
        if not student:
            messagebox.showwarning(
                "Selection Required",
                "Please select a student from the table to edit.",
                parent=self.root,
            )
            return

        StudentFormDialog(
            self.root,
            self.service,
            self.current_user,
            student=student,
            on_save_callback=self._load_students,
            theme_manager=self.tm,
        )

    def _handle_delete_action(self) -> None:
        """
        Delete action handler.
        Allows Soft Delete (Archive) for all staff, or Hard Delete for Admin.
        """
        student = self._get_selected_student()
        if not student:
            messagebox.showwarning(
                "Selection Required",
                "Please select a student record to delete or archive.",
                parent=self.root,
            )
            return

        # Modal dialog for confirmation
        dialog = tk.Toplevel(self.root)
        dialog.title("Confirm Record Deletion")
        dialog.geometry("480x320")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        c = self.tm.colors
        dialog.configure(bg=c["surface"])

        pad_frame = tk.Frame(dialog, bg=c["surface"], padx=20, pady=20)
        pad_frame.pack(fill="both", expand=True)

        tk.Label(
            pad_frame,
            text=f"Student: {student.full_name} ({student.roll_number})",
            font=(FONT_FAMILY, FONT_SIZES["title"], "bold"),
            bg=c["surface"],
            fg=c["text_main"],
        ).pack(anchor="w", pady=(0, 6))

        tk.Label(
            pad_frame,
            text="Choose an action to proceed with this student record:",
            font=(FONT_FAMILY, FONT_SIZES["body"]),
            bg=c["surface"],
            fg=c["text_sub"],
        ).pack(anchor="w", pady=(0, 14))

        # Radio options
        action_var = tk.StringVar(value="archive")

        rb_archive = tk.Radiobutton(
            pad_frame,
            text="📦 Archive Record (Soft Delete - Reversible)",
            variable=action_var,
            value="archive",
            font=(FONT_FAMILY, FONT_SIZES["body"]),
            bg=c["surface"],
            fg=c["text_main"],
            activebackground=c["surface"],
        )
        rb_archive.pack(anchor="w", pady=4)

        if student.is_archived:
            rb_restore = tk.Radiobutton(
                pad_frame,
                text="♻️ Restore Record (Make Active)",
                variable=action_var,
                value="restore",
                font=(FONT_FAMILY, FONT_SIZES["body"]),
                bg=c["surface"],
                fg=c["text_main"],
                activebackground=c["surface"],
            )
            rb_restore.pack(anchor="w", pady=4)
            action_var.set("restore")

        # Admin Hard Delete Option
        is_admin = self.current_user.is_admin
        rb_hard = tk.Radiobutton(
            pad_frame,
            text="🔥 Permanently Delete (Admin Only - Irreversible)",
            variable=action_var,
            value="permanent",
            font=(FONT_FAMILY, FONT_SIZES["body"]),
            bg=c["surface"],
            fg=c["danger"] if is_admin else c["text_muted"],
            activebackground=c["surface"],
            state="normal" if is_admin else "disabled",
        )
        rb_hard.pack(anchor="w", pady=4)

        if not is_admin:
            tk.Label(
                pad_frame,
                text="* Permanent deletion is restricted to Administrators.",
                font=(FONT_FAMILY, 8),
                bg=c["surface"],
                fg=c["text_muted"],
            ).pack(anchor="w", padx=24)

        btn_row = tk.Frame(pad_frame, bg=c["surface"])
        btn_row.pack(fill="x", side="bottom", pady=(16, 0))

        def execute_action():
            selected_choice = action_var.get()
            dialog.destroy()

            if selected_choice == "archive":
                ok, err = self.service.delete_student(
                    student.student_id,
                    permanent=False,
                    current_user=self.current_user,
                )
                if ok:
                    messagebox.showinfo("Archived", f"Student {student.roll_number} has been archived.", parent=self.root)
                    self._load_students()
                else:
                    messagebox.showerror("Error", err or "Failed to archive student.", parent=self.root)

            elif selected_choice == "restore":
                ok, err = self.service.restore_student(student.student_id, current_user=self.current_user)
                if ok:
                    messagebox.showinfo("Restored", f"Student {student.roll_number} has been restored.", parent=self.root)
                    self._load_students()
                else:
                    messagebox.showerror("Error", err or "Failed to restore student.", parent=self.root)

            elif selected_choice == "permanent":
                confirm = messagebox.askyesno(
                    "Confirm Permanent Deletion",
                    f"Are you ABSOLUTELY SURE you want to permanently erase record for '{student.full_name}'?\nThis cannot be undone.",
                    icon="warning",
                    parent=self.root,
                )
                if confirm:
                    ok, err = self.service.delete_student(
                        student.student_id,
                        permanent=True,
                        current_user=self.current_user,
                    )
                    if ok:
                        messagebox.showinfo("Deleted", "Student permanently removed.", parent=self.root)
                        self._load_students()
                    else:
                        messagebox.showerror("Error", err or "Failed to delete student.", parent=self.root)

        ttk.Button(
            btn_row,
            text="Cancel",
            style="Secondary.TButton",
            command=dialog.destroy,
            cursor="hand2",
        ).pack(side="right", padx=(8, 0))

        ttk.Button(
            btn_row,
            text="Confirm Action",
            style="Danger.TButton",
            command=execute_action,
            cursor="hand2",
        ).pack(side="right")

    # -------------------------------------------------------------------------
    # Import / Export / Backup
    # -------------------------------------------------------------------------
    def _handle_import_file(self) -> None:
        """Import students from CSV or Excel file."""
        file_path = filedialog.askopenfilename(
            title="Select Student Import File",
            filetypes=[
                ("Supported Formats (*.csv, *.xlsx, *.xls)", "*.csv;*.xlsx;*.xls"),
                ("CSV Files (*.csv)", "*.csv"),
                ("Excel Files (*.xlsx, *.xls)", "*.xlsx;*.xls"),
            ],
            parent=self.root,
        )
        if not file_path:
            return

        success, imported_count, errors = import_students_from_file(
            Path(file_path),
            current_user=self.current_user,
            student_dao=self.service.student_dao,
        )

        if success:
            messagebox.showinfo(
                "Import Successful",
                f"Successfully imported {imported_count} student records!",
                parent=self.root,
            )
            self._load_students()
        else:
            err_summary = "\n".join(errors[:10])
            if len(errors) > 10:
                err_summary += f"\n...and {len(errors) - 10} more errors."
            messagebox.showerror(
                "Import Failed (Rolled Back)",
                f"The file contained validation errors and was NOT imported:\n\n{err_summary}",
                parent=self.root,
            )

    def _get_all_matching_students(self) -> List[Student]:
        """Fetch all matching students across all pages for complete export."""
        query = self.search_bar.get_query()
        dept_str = self.filter_dept_var.get()
        dept_id = self.dept_name_to_id.get(dept_str)
        year_str = self.filter_year_var.get()
        year_num = int(year_str.replace("Year ", "")) if "Year" in year_str else None
        include_archived = self.show_archived_var.get()

        students, _ = self.service.student_dao.search_students(
            search_query=query,
            department_id=dept_id,
            year_level=year_num,
            include_archived=include_archived,
            sort_by=self.sort_by,
            sort_dir=self.sort_dir,
            limit=100000,
            offset=0,
        )
        return students

    def _handle_export_csv(self) -> None:
        """Export current filtered records to CSV."""
        students = self._get_all_matching_students()
        if not students:
            messagebox.showinfo("Export", "No student records to export.", parent=self.root)
            return

        file_path = filedialog.asksaveasfilename(
            title="Save Student Records CSV",
            defaultextension=".csv",
            filetypes=[("CSV Files (*.csv)", "*.csv")],
            initialfile=f"students_export_{len(students)}.csv",
            parent=self.root,
        )
        if not file_path:
            return

        try:
            export_students_to_csv(students, Path(file_path))
            messagebox.showinfo("Export Complete", f"Exported {len(students)} records to:\n{file_path}", parent=self.root)
        except Exception as e:
            messagebox.showerror("Export Failed", str(e), parent=self.root)

    def _handle_export_pdf(self) -> None:
        """Export current filtered records to a styled PDF report."""
        students = self._get_all_matching_students()
        if not students:
            messagebox.showinfo("Export", "No student records to export.", parent=self.root)
            return

        file_path = filedialog.asksaveasfilename(
            title="Save Student Records PDF",
            defaultextension=".pdf",
            filetypes=[("PDF Documents (*.pdf)", "*.pdf")],
            initialfile=f"students_report_{len(students)}.pdf",
            parent=self.root,
        )
        if not file_path:
            return

        try:
            export_students_to_pdf(students, Path(file_path))
            messagebox.showinfo("Export Complete", f"Generated PDF report for {len(students)} students:\n{file_path}", parent=self.root)
        except Exception as e:
            messagebox.showerror("Export Failed", str(e), parent=self.root)

    def _handle_backup_db(self) -> None:
        """Trigger an instant database backup."""
        try:
            backup_path = self.service.create_database_backup()
            messagebox.showinfo(
                "Database Backup Successful",
                f"A complete backup of the database was safely created at:\n{backup_path}",
                parent=self.root,
            )
        except Exception as e:
            messagebox.showerror("Backup Failed", f"Database backup encountered an error:\n{e}", parent=self.root)

    # -------------------------------------------------------------------------
    # Theme & Logout
    # -------------------------------------------------------------------------
    def _handle_theme_toggle(self) -> None:
        """Toggle between light and dark themes."""
        self.tm.toggle_theme()
        theme_icon = "☀️ Light" if self.tm.is_dark else "🌙 Dark"
        self.theme_btn.config(text=theme_icon)

    def update_theme(self, colors: Dict[str, str]) -> None:
        """Apply theme updates across root window and top navbar."""
        self.style = ttk.Style()
        self.tm.apply_styles(self.style)
        self.root.configure(bg=colors["app_bg"])
        self.nav_frame.configure(bg=colors["nav_bg"])
        self.content_container.configure(bg=colors["app_bg"])
        self.status_bar.configure(bg=colors["surface_alt"])
        self.db_status_lbl.configure(bg=colors["surface_alt"])
        self.version_lbl.configure(bg=colors["surface_alt"], fg=colors["text_muted"])

    def _handle_logout(self) -> None:
        """Confirm and execute staff logout."""
        confirm = messagebox.askyesno("Confirm Sign Out", "Are you sure you want to sign out?", parent=self.root)
        if confirm:
            self.root.destroy()
            if self.on_logout:
                self.on_logout()

    def run(self) -> None:
        self.root.mainloop()
