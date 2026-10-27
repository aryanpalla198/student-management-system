"""
Database connection manager and utilities for SQLite.
Supports connection pooling, context management, schema initialization,
and safe atomic backups using SQLite's online backup API.
"""

import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
from typing import Generator, Optional
from app.config import (
    DATABASE_PATH,
    SCHEMA_PATH,
    SEED_PATH,
    BACKUP_DIR,
    DATABASE_DIR,
)
from app.utils.logger import get_logger

logger = get_logger("sms.db_connection")


class DatabaseManager:
    """Manages SQLite database connections, lifecycle, and transactions."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else DATABASE_PATH
        # Ensure parent directory exists if using a file path
        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """Create and configure a new SQLite connection with foreign keys enabled."""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=10.0,
            check_same_thread=False,
        )
        # Use sqlite3.Row for name-based column indexing
        conn.row_factory = sqlite3.Row
        # Enforce foreign key constraints in SQLite
        conn.execute("PRAGMA foreign_keys = ON;")
        # Enable Write-Ahead Logging for improved concurrency and performance
        if str(self.db_path) != ":memory:":
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager yielding a managed connection."""
        conn = self.get_connection()
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self, conn: Optional[sqlite3.Connection] = None) -> Generator[sqlite3.Connection, None, None]:
        """
        Context manager for an atomic database transaction.
        Automatically commits on successful exit or rolls back on exception.
        """
        own_connection = False
        if conn is None:
            conn = self.get_connection()
            own_connection = True

        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error("Transaction rolled back due to error: %s", e)
            raise
        finally:
            if own_connection:
                conn.close()

    def init_db(self, schema_file: Optional[Path] = None) -> None:
        """Initialize database schema from SQL file."""
        target_schema = schema_file or SCHEMA_PATH
        if not target_schema.exists():
            raise FileNotFoundError(f"Schema file not found at {target_schema}")

        logger.info("Initializing database schema from %s", target_schema)
        with open(target_schema, "r", encoding="utf-8") as f:
            sql_script = f.read()

        with self.transaction() as conn:
            conn.executescript(sql_script)
        logger.info("Database schema initialized successfully.")

    def seed_db(self, seed_file: Optional[Path] = None) -> None:
        """Populate database with initial seed data."""
        target_seed = seed_file or SEED_PATH
        if not target_seed.exists():
            raise FileNotFoundError(f"Seed file not found at {target_seed}")

        logger.info("Seeding database from %s", target_seed)
        with open(target_seed, "r", encoding="utf-8") as f:
            sql_script = f.read()

        with self.transaction() as conn:
            conn.executescript(sql_script)
        logger.info("Database seeded successfully.")

    def backup_db(self, destination_dir: Optional[Path] = None) -> Path:
        """
        Create a live, atomic backup of the database file.
        Uses SQLite's online backup API to ensure safety even during reads/writes.
        """
        dest_dir = destination_dir or BACKUP_DIR
        dest_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"sms_backup_{timestamp}.db"
        backup_filepath = dest_dir / backup_filename

        logger.info("Starting online backup to %s", backup_filepath)
        source_conn = self.get_connection()
        try:
            dest_conn = sqlite3.connect(str(backup_filepath))
            try:
                # Online backup API
                source_conn.backup(dest_conn, pages=100)
            finally:
                dest_conn.close()
        finally:
            source_conn.close()

        logger.info("Backup successfully completed: %s", backup_filepath)
        return backup_filepath


# Default global instance
default_db_manager = DatabaseManager()
