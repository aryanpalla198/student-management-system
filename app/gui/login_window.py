"""
Login Window with failed attempt rate limiting, lockout countdown,
and clean, modern card styling.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional
from app.config import (
    APP_NAME,
    APP_SUBTITLE,
    FONT_FAMILY,
    FONT_SIZES,
)
from app.gui.widgets import ThemeManager, enable_high_dpi_awareness
from app.models.user import User
from app.services.auth_service import AuthService
from app.utils.logger import get_logger

logger = get_logger("sms.login_window")


class LoginWindow:
    """Authentication dialog presented upon application launch."""

    def __init__(
        self,
        auth_service: AuthService,
        on_login_success: Callable[[User], None],
        theme_manager: Optional[ThemeManager] = None,
    ):
        enable_high_dpi_awareness()
        self.auth_service = auth_service
        self.on_login_success = on_login_success
        self.tm = theme_manager or ThemeManager()

        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} - Staff Login")
        self.root.geometry("460x560")
        self.root.resizable(False, False)

        # Center on screen
        self.root.eval("tk::PlaceWindow . center")

        self.style = ttk.Style()
        self.tm.apply_styles(self.style)

        self._lockout_timer_id = None
        self._build_ui()
        self._bind_events()

    def _build_ui(self) -> None:
        c = self.tm.colors
        self.root.configure(bg=c["app_bg"])

        # Main Centered Container
        outer_frame = tk.Frame(self.root, bg=c["app_bg"], padx=24, pady=24)
        outer_frame.pack(fill="both", expand=True)

        # Card Frame
        card = tk.Frame(
            outer_frame,
            bg=c["surface"],
            highlightbackground=c["border"],
            highlightthickness=1,
            padx=28,
            pady=28,
        )
        card.pack(fill="both", expand=True)

        # App Icon & Brand Title
        tk.Label(
            card,
            text="🎓",
            font=(FONT_FAMILY, 32),
            bg=c["surface"],
            fg=c["primary"],
        ).pack(pady=(4, 0))

        tk.Label(
            card,
            text=APP_NAME,
            font=(FONT_FAMILY, FONT_SIZES["display"], "bold"),
            bg=c["surface"],
            fg=c["text_main"],
        ).pack(pady=(2, 0))

        tk.Label(
            card,
            text=APP_SUBTITLE,
            font=(FONT_FAMILY, FONT_SIZES["caption"]),
            bg=c["surface"],
            fg=c["text_sub"],
        ).pack(pady=(0, 16))

        # Error / Lockout Banner
        self.banner_frame = tk.Frame(card, bg=c["danger_bg"], padx=10, pady=8)
        self.banner_lbl = tk.Label(
            self.banner_frame,
            text="",
            font=(FONT_FAMILY, FONT_SIZES["caption"], "bold"),
            bg=c["danger_bg"],
            fg=c["danger_text"],
            wraplength=340,
            justify="center",
        )
        self.banner_lbl.pack(fill="x")
        # Hidden by default

        # Form Fields Container
        form_frame = tk.Frame(card, bg=c["surface"])
        form_frame.pack(fill="x", pady=10)

        # Username
        tk.Label(
            form_frame,
            text="Username",
            font=(FONT_FAMILY, FONT_SIZES["body"], "bold"),
            bg=c["surface"],
            fg=c["text_main"],
            anchor="w",
        ).pack(fill="x", pady=(4, 2))

        self.user_entry = tk.Entry(
            form_frame,
            font=(FONT_FAMILY, FONT_SIZES["body"]),
            bg=c["input_bg"],
            fg=c["input_fg"],
            highlightbackground=c["input_border"],
            highlightcolor=c["primary"],
            highlightthickness=1,
            relief="flat",
        )
        self.user_entry.pack(fill="x", ipady=6, pady=(0, 12))
        self.user_entry.focus()

        # Password
        pwd_hdr_frame = tk.Frame(form_frame, bg=c["surface"])
        pwd_hdr_frame.pack(fill="x", pady=(4, 2))

        tk.Label(
            pwd_hdr_frame,
            text="Password",
            font=(FONT_FAMILY, FONT_SIZES["body"], "bold"),
            bg=c["surface"],
            fg=c["text_main"],
            anchor="w",
        ).pack(side="left")

        # Show/Hide Password Checkbox
        self.show_pwd_var = tk.BooleanVar(value=False)
        self.show_pwd_cb = tk.Checkbutton(
            pwd_hdr_frame,
            text="Show",
            variable=self.show_pwd_var,
            font=(FONT_FAMILY, FONT_SIZES["caption"]),
            bg=c["surface"],
            fg=c["text_sub"],
            activebackground=c["surface"],
            command=self._toggle_pwd_visibility,
        )
        self.show_pwd_cb.pack(side="right")

        self.pwd_entry = tk.Entry(
            form_frame,
            show="●",
            font=(FONT_FAMILY, FONT_SIZES["body"]),
            bg=c["input_bg"],
            fg=c["input_fg"],
            highlightbackground=c["input_border"],
            highlightcolor=c["primary"],
            highlightthickness=1,
            relief="flat",
        )
        self.pwd_entry.pack(fill="x", ipady=6, pady=(0, 16))

        # Sign In Button
        self.login_btn = ttk.Button(
            card,
            text="Sign In to System",
            style="Primary.TButton",
            command=self.handle_login,
            cursor="hand2",
        )
        self.login_btn.pack(fill="x", ipady=4, pady=(4, 12))

        # Default Demo Credentials Helper
        helper_frame = tk.Frame(card, bg=c["surface_alt"], padx=10, pady=8)
        helper_frame.pack(fill="x", side="bottom")

        tk.Label(
            helper_frame,
            text="Default System Accounts:",
            font=(FONT_FAMILY, FONT_SIZES["caption"], "bold"),
            bg=c["surface_alt"],
            fg=c["text_sub"],
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            helper_frame,
            text="• Admin: admin / Admin@123\n• Staff: staff / Staff@123",
            font=(FONT_FAMILY, FONT_SIZES["caption"]),
            bg=c["surface_alt"],
            fg=c["text_muted"],
            justify="left",
            anchor="w",
        ).pack(fill="x", pady=(2, 0))

    def _bind_events(self) -> None:
        self.root.bind("<Return>", lambda e: self.handle_login())

    def _toggle_pwd_visibility(self) -> None:
        if self.show_pwd_var.get():
            self.pwd_entry.config(show="")
        else:
            self.pwd_entry.config(show="●")

    def show_error(self, message: str) -> None:
        """Display error alert banner."""
        self.banner_lbl.config(text=message)
        self.banner_frame.pack(fill="x", pady=(0, 10), before=self.user_entry.master)

    def clear_error(self) -> None:
        self.banner_frame.pack_forget()

    def handle_login(self) -> None:
        """Attempt credentials verification and handle rate-limiting."""
        self.clear_error()
        username = self.user_entry.get().strip()
        password = self.pwd_entry.get()

        if not username:
            self.show_error("Please enter your username.")
            self.user_entry.focus()
            return

        if not password:
            self.show_error("Please enter your password.")
            self.pwd_entry.focus()
            return

        success, user, error_msg = self.auth_service.login(username, password)
        if success and user:
            logger.info("Authentication successful for %s", user.username)
            self.root.destroy()
            self.on_login_success(user)
        else:
            self.show_error(error_msg or "Invalid username or password.")
            # Check if locked out
            remaining = self.auth_service.get_lockout_remaining(username)
            if remaining > 0:
                self._start_lockout_countdown(username, remaining)

    def _start_lockout_countdown(self, username: str, seconds: int) -> None:
        """Disable inputs and show dynamic countdown."""
        self.login_btn.config(state="disabled")
        self.user_entry.config(state="disabled")
        self.pwd_entry.config(state="disabled")

        def tick(sec_left: int) -> None:
            if sec_left <= 0:
                self.login_btn.config(state="normal")
                self.user_entry.config(state="normal")
                self.pwd_entry.config(state="normal")
                self.clear_error()
                self.pwd_entry.delete(0, tk.END)
                self.pwd_entry.focus()
            else:
                self.show_error(f"Account locked due to failed attempts. Try again in {sec_left}s...")
                self._lockout_timer_id = self.root.after(1000, tick, sec_left - 1)

        tick(seconds)

    def run(self) -> None:
        self.root.mainloop()
