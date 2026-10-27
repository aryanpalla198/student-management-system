"""
Application Entry Point for AcademiaSMS (Student Management System).
Initializes database schema, seeds default accounts if needed,
and orchestrates the lifecycle between Login and Main windows.
"""

import sys
from pathlib import Path

# Ensure application root is in python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.config import DATABASE_PATH, SCHEMA_PATH, SEED_PATH
from app.dao.db_connection import default_db_manager
from app.dao.student_dao import StudentDAO
from app.dao.user_dao import UserDAO
from app.gui.login_window import LoginWindow
from app.gui.main_window import MainWindow
from app.gui.widgets import ThemeManager
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.student_service import StudentService
from app.utils.logger import get_logger

logger = get_logger("sms.main")


def ensure_database_ready() -> None:
    """Ensure database schema is created and initial seeds are populated."""
    db_needs_init = not DATABASE_PATH.exists() or DATABASE_PATH.stat().st_size == 0

    if db_needs_init:
        logger.info("Database file not found or empty. Creating schema...")
        default_db_manager.init_db(SCHEMA_PATH)
        logger.info("Populating initial seed data...")
        default_db_manager.seed_db(SEED_PATH)
    else:
        # Check if users table exists, initialize if not
        with default_db_manager.connection() as conn:
            cursor = conn.execute(
                "SELECT count(*) as count FROM sqlite_master WHERE type='table' AND name='users'"
            )
            if cursor.fetchone()["count"] == 0:
                logger.info("Tables missing in existing database. Running schema creation...")
                default_db_manager.init_db(SCHEMA_PATH)
                default_db_manager.seed_db(SEED_PATH)


class ApplicationController:
    """Controls transitions between Login and Main dashboard."""

    def __init__(self):
        ensure_database_ready()
        self.user_dao = UserDAO(default_db_manager)
        self.student_dao = StudentDAO(default_db_manager)
        self.auth_service = AuthService(self.user_dao)
        self.student_service = StudentService(self.student_dao)
        self.theme_manager = ThemeManager(default_theme="light")

    def start(self) -> None:
        """Begin application lifecycle with login window."""
        self.show_login()

    def show_login(self) -> None:
        """Launch staff authentication dialog."""
        logger.info("Launching Login Window...")
        login_win = LoginWindow(
            auth_service=self.auth_service,
            on_login_success=self.on_login_success,
            theme_manager=self.theme_manager,
        )
        login_win.run()

    def on_login_success(self, user: User) -> None:
        """Transition from Login to Main Window upon successful authentication."""
        logger.info("Transitioning to Main Window for user: %s", user.username)
        main_win = MainWindow(
            student_service=self.student_service,
            current_user=user,
            on_logout_callback=self.on_logout,
            theme_manager=self.theme_manager,
        )
        main_win.run()

    def on_logout(self) -> None:
        """Handle logout by clearing auth state and returning to login dialog."""
        logger.info("User signed out. Returning to login screen.")
        self.auth_service.logout()
        self.show_login()


def main() -> None:
    """Main CLI / GUI invocation."""
    try:
        app = ApplicationController()
        app.start()
    except Exception as e:
        logger.critical("Unhandled application exception: %s", e, exc_info=True)
        print(f"Fatal error starting application: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
