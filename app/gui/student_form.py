"""
Student Form Modal (Add / Edit Student Dialog).
Implements field validation, optimistic concurrency handling,
department selection, and clear error presentation.
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Callable, Dict, List, Optional
from app.config import (
    FONT_FAMILY,
    FONT_SIZES,
    MIN_GPA,
    MAX_GPA,
    MIN_YEAR_LEVEL,
    MAX_YEAR_LEVEL,
)
from app.gui.widgets import ThemeManager
from app.models.student import Department, Student
from app.models.user import User
from app.services.student_service import StudentService
from app.utils.logger import get_logger

logger = get_logger("sms.student_form")


class StudentFormDialog(tk.Toplevel):
    """Modal dialog for creating and updating student records."""

    def __init__(
        self,
        parent: tk.Widget,
        student_service: StudentService,
        current_user: User,
        student: Optional[Student] = None,
        on_save_callback: Optional[Callable[[], None]] = None,
        theme_manager: Optional[ThemeManager] = None,
    ):
        super().__init__(parent)
        self.service = student_service
        self.current_user = current_user
        self.student = student  # If None, in "Add" mode; otherwise in "Edit" mode
        self.on_save_callback = on_save_callback
        self.tm = theme_manager or ThemeManager()

        self.is_edit = student is not None
        title_prefix = "Edit Student" if self.is_edit else "Add New Student"
        self.title(f"{title_prefix}")
        self.geometry("620x720")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()  # Make window modal

        # Load departments
        self.departments: List[Department] = self.service.get_departments()
        self.dept_name_to_id = {d.name: d.department_id for d in self.departments}
        self.dept_id_to_name = {d.department_id: d.name for d in self.departments}

        # Error tracking widgets {field_key: label_widget}
        self.field_entries: Dict[str, tk.Entry] = {}
        self.error_labels: Dict[str, tk.Label] = {}

        self._build_ui()
        if self.is_edit and self.student:
            self._populate_fields(self.student)

    def _build_ui(self) -> None:
        c = self.tm.colors
        self.configure(bg=c["app_bg"])

        # Main wrapper with padding
        container = tk.Frame(self, bg=c["app_bg"], padx=24, pady=20)
        container.pack(fill="both", expand=True)

        # Header Title Card
        header = tk.Frame(
            container,
            bg=c["surface"],
            highlightbackground=c["border"],
            highlightthickness=1,
            padx=18,
            pady=14,
        )
        header.pack(fill="x", pady=(0, 16))

        title_text = f"✏️ Edit Student Details" if self.is_edit else "➕ Add New Student Record"
        tk.Label(
            header,
            text=title_text,
            font=(FONT_FAMILY, FONT_SIZES["title"], "bold"),
            bg=c["surface"],
            fg=c["text_main"],
        ).pack(anchor="w")

        sub_text = (
            f"Editing record for Roll No: {self.student.roll_number}"
            if self.is_edit and self.student
            else "Fill in the required academic and personal information below."
        )
        tk.Label(
            header,
            text=sub_text,
            font=(FONT_FAMILY, FONT_SIZES["caption"]),
            bg=c["surface"],
            fg=c["text_sub"],
        ).pack(anchor="w", pady=(2, 0))

        # Scrollable / Form Card
        form_card = tk.Frame(
            container,
            bg=c["surface"],
            highlightbackground=c["border"],
            highlightthickness=1,
            padx=20,
            pady=16,
        )
        form_card.pack(fill="both", expand=True)

        # 2-Column Grid Layout
        form_card.columnconfigure(0, weight=1, uniform="col")
        form_card.columnconfigure(1, weight=1, uniform="col")

        # Row 0: Roll Number & Date of Birth
        self._add_field(form_card, "roll_number", "Roll Number *", "e.g. CS2025001", row=0, col=0)
        self._add_field(form_card, "date_of_birth", "Date of Birth * (YYYY-MM-DD)", "YYYY-MM-DD", row=0, col=1)

        # Row 2: First Name & Last Name
        self._add_field(form_card, "first_name", "First Name *", "Letters only", row=2, col=0)
        self._add_field(form_card, "last_name", "Last Name *", "Letters only", row=2, col=1)

        # Row 4: Email Address & Phone Number
        self._add_field(form_card, "email", "Email Address *", "student@university.edu", row=4, col=0)
        self._add_field(form_card, "phone", "Phone Number (Optional)", "+15550123", row=4, col=1)

        # Row 6: Department & Year Level
        self._add_department_field(form_card, row=6, col=0)
        self._add_year_level_field(form_card, row=6, col=1)

        # Row 8: GPA & Concurrency / Audit Note
        self._add_field(form_card, "gpa", "GPA (0.00 – 10.00, Optional)", "e.g. 8.75", row=8, col=0)

        # Status note for Edit mode
        if self.is_edit and self.student:
            status_box = tk.Frame(form_card, bg=c["surface_alt"], padx=10, pady=8)
            status_box.grid(row=8, column=1, sticky="nsew", padx=8, pady=(4, 0))
            status_str = "Archived" if self.student.is_archived else "Active"
            tk.Label(
                status_box,
                text=f"Record Status: {status_str}",
                font=(FONT_FAMILY, FONT_SIZES["caption"], "bold"),
                bg=c["surface_alt"],
                fg=c["danger" if self.student.is_archived else "success"],
            ).pack(anchor="w")
            tk.Label(
                status_box,
                text=f"Last Updated: {self.student.updated_at or 'N/A'}",
                font=(FONT_FAMILY, FONT_SIZES["caption"]),
                bg=c["surface_alt"],
                fg=c["text_muted"],
            ).pack(anchor="w")

        # Global Error Banner inside Form
        self.global_err_lbl = tk.Label(
            form_card,
            text="",
            font=(FONT_FAMILY, FONT_SIZES["caption"], "bold"),
            bg=c["danger_bg"],
            fg=c["danger_text"],
            wraplength=520,
            padx=8,
            pady=4,
        )
        self.global_err_lbl.grid(row=10, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self.global_err_lbl.grid_remove()

        # Action Buttons Container
        btn_bar = tk.Frame(container, bg=c["app_bg"])
        btn_bar.pack(fill="x", pady=(16, 0))

        cancel_btn = ttk.Button(
            btn_bar,
            text="Cancel",
            style="Secondary.TButton",
            command=self.destroy,
            cursor="hand2",
        )
        cancel_btn.pack(side="right", padx=(8, 0))

        save_label = "Update Record" if self.is_edit else "Create Student"
        self.save_btn = ttk.Button(
            btn_bar,
            text=save_label,
            style="Primary.TButton",
            command=self.handle_save,
            cursor="hand2",
        )
        self.save_btn.pack(side="right")

    def _add_field(self, parent: tk.Widget, key: str, label_text: str, placeholder: str, row: int, col: int) -> None:
        c = self.tm.colors
        cell = tk.Frame(parent, bg=c["surface"])
        cell.grid(row=row, column=col, sticky="nsew", padx=8, pady=4)

        tk.Label(
            cell,
            text=label_text,
            font=(FONT_FAMILY, FONT_SIZES["caption"], "bold"),
            bg=c["surface"],
            fg=c["text_main"],
            anchor="w",
        ).pack(fill="x", pady=(0, 2))

        entry = tk.Entry(
            cell,
            font=(FONT_FAMILY, FONT_SIZES["body"]),
            bg=c["input_bg"],
            fg=c["input_fg"],
            highlightbackground=c["input_border"],
            highlightcolor=c["primary"],
            highlightthickness=1,
            relief="flat",
        )
        entry.pack(fill="x", ipady=4)
        self.field_entries[key] = entry

        # Error label beneath entry
        err_lbl = tk.Label(
            cell,
            text="",
            font=(FONT_FAMILY, 8),
            bg=c["surface"],
            fg=c["danger"],
            anchor="w",
            wraplength=240,
            justify="left",
        )
        err_lbl.pack(fill="x", pady=(2, 0))
        self.error_labels[key] = err_lbl

    def _add_department_field(self, parent: tk.Widget, row: int, col: int) -> None:
        c = self.tm.colors
        cell = tk.Frame(parent, bg=c["surface"])
        cell.grid(row=row, column=col, sticky="nsew", padx=8, pady=4)

        tk.Label(
            cell,
            text="Department *",
            font=(FONT_FAMILY, FONT_SIZES["caption"], "bold"),
            bg=c["surface"],
            fg=c["text_main"],
            anchor="w",
        ).pack(fill="x", pady=(0, 2))

        dept_names = [d.name for d in self.departments]
        self.dept_var = tk.StringVar()
        self.dept_combo = ttk.Combobox(
            cell,
            textvariable=self.dept_var,
            values=dept_names,
            state="readonly",
        )
        self.dept_combo.pack(fill="x", ipady=3)
        if dept_names:
            self.dept_combo.current(0)

        err_lbl = tk.Label(
            cell,
            text="",
            font=(FONT_FAMILY, 8),
            bg=c["surface"],
            fg=c["danger"],
            anchor="w",
        )
        err_lbl.pack(fill="x", pady=(2, 0))
        self.error_labels["department_id"] = err_lbl

    def _add_year_level_field(self, parent: tk.Widget, row: int, col: int) -> None:
        c = self.tm.colors
        cell = tk.Frame(parent, bg=c["surface"])
        cell.grid(row=row, column=col, sticky="nsew", padx=8, pady=4)

        tk.Label(
            cell,
            text="Year Level *",
            font=(FONT_FAMILY, FONT_SIZES["caption"], "bold"),
            bg=c["surface"],
            fg=c["text_main"],
            anchor="w",
        ).pack(fill="x", pady=(0, 2))

        year_options = [f"Year {y}" for y in range(MIN_YEAR_LEVEL, MAX_YEAR_LEVEL + 1)]
        self.year_var = tk.StringVar(value="Year 1")
        self.year_combo = ttk.Combobox(
            cell,
            textvariable=self.year_var,
            values=year_options,
            state="readonly",
        )
        self.year_combo.pack(fill="x", ipady=3)

        err_lbl = tk.Label(
            cell,
            text="",
            font=(FONT_FAMILY, 8),
            bg=c["surface"],
            fg=c["danger"],
            anchor="w",
        )
        err_lbl.pack(fill="x", pady=(2, 0))
        self.error_labels["year_level"] = err_lbl

    def _populate_fields(self, student: Student) -> None:
        """Pre-populate existing student data."""
        self.field_entries["roll_number"].insert(0, student.roll_number)
        self.field_entries["first_name"].insert(0, student.first_name)
        self.field_entries["last_name"].insert(0, student.last_name)
        self.field_entries["date_of_birth"].insert(0, student.date_of_birth)
        self.field_entries["email"].insert(0, student.email)
        if student.phone:
            self.field_entries["phone"].insert(0, student.phone)
        if student.gpa is not None:
            self.field_entries["gpa"].insert(0, f"{student.gpa:.2f}")

        # Set Department
        dept_name = self.dept_id_to_name.get(student.department_id)
        if dept_name:
            self.dept_var.set(dept_name)

        # Set Year Level
        self.year_var.set(f"Year {student.year_level}")

    def clear_errors(self) -> None:
        """Clear all active validation and global error indicators."""
        c = self.tm.colors
        for key, lbl in self.error_labels.items():
            lbl.config(text="")
        for entry in self.field_entries.values():
            entry.config(highlightbackground=c["input_border"])
        self.global_err_lbl.grid_remove()

    def handle_save(self) -> None:
        """Collect form values, validate via service, and persist."""
        self.clear_errors()
        c = self.tm.colors

        # Collect data
        dept_name = self.dept_var.get()
        dept_id = self.dept_name_to_id.get(dept_name)

        year_str = self.year_var.get()
        year_num = int(year_str.replace("Year ", "")) if "Year" in year_str else 1

        payload = {
            "roll_number": self.field_entries["roll_number"].get().strip(),
            "first_name": self.field_entries["first_name"].get().strip(),
            "last_name": self.field_entries["last_name"].get().strip(),
            "date_of_birth": self.field_entries["date_of_birth"].get().strip(),
            "email": self.field_entries["email"].get().strip(),
            "phone": self.field_entries["phone"].get().strip() or None,
            "department_id": dept_id,
            "year_level": year_num,
            "gpa": self.field_entries["gpa"].get().strip() or None,
        }

        if self.is_edit and self.student and self.student.student_id:
            # Update Existing Student with Optimistic Locking
            success, updated_student, errors = self.service.update_student(
                student_id=self.student.student_id,
                data=payload,
                expected_updated_at=self.student.updated_at,
                current_user=self.current_user,
            )
            action_desc = "updated"
        else:
            # Create New Student
            success, created_student, errors = self.service.create_student(
                data=payload,
                current_user=self.current_user,
            )
            action_desc = "created"

        if success:
            messagebox.showinfo(
                "Success",
                f"Student record successfully {action_desc}!",
                parent=self,
            )
            if self.on_save_callback:
                self.on_save_callback()
            self.destroy()
        else:
            if errors:
                for field_key, err_msg in errors.items():
                    if field_key in self.error_labels:
                        self.error_labels[field_key].config(text=err_msg)
                        if field_key in self.field_entries:
                            self.field_entries[field_key].config(highlightbackground=c["danger"])
                    else:
                        # General error (concurrency conflict, etc.)
                        self.global_err_lbl.config(text=err_msg)
                        self.global_err_lbl.grid()
