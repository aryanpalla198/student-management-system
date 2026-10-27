"""
Application Configuration and Constants.
Provides file paths, database connection configurations, authentication rules,
and a premium, modern color palette for Light and Dark themes.
"""

from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "student_management.db"
SCHEMA_PATH = DATABASE_DIR / "schema.sql"
SEED_PATH = DATABASE_DIR / "seed.sql"
BACKUP_DIR = BASE_DIR / "backups"
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "app.log"

# App Metadata
APP_NAME = "AcademiaSMS"
APP_SUBTITLE = "Enterprise Student Management System"
APP_VERSION = "1.0.0"

# Pagination defaults
DEFAULT_PAGE_SIZE = 10
PAGE_SIZE_OPTIONS = [5, 10, 20, 50]

# Security & Authentication
MAX_LOGIN_ATTEMPTS = 3
LOCKOUT_DURATION_SECONDS = 60

# Student Validation Constraints
MIN_STUDENT_AGE = 15
MAX_STUDENT_AGE = 60
MIN_YEAR_LEVEL = 1
MAX_YEAR_LEVEL = 6
MIN_GPA = 0.00
MAX_GPA = 10.00

# Roles
ROLE_ADMIN = "ADMIN"
ROLE_STAFF = "STAFF"

# Typography
FONT_FAMILY = "Segoe UI"
FONT_SIZES = {
    "display": 18,
    "title": 14,
    "subtitle": 12,
    "body": 10,
    "caption": 9,
    "badge": 8,
}

# Premium Neat Color Palettes
THEMES = {
    "light": {
        "name": "light",
        "app_bg": "#F8FAFC",          # Crisp light slate background
        "surface": "#FFFFFF",         # Pure white cards and panels
        "surface_alt": "#F1F5F9",     # Light card header / row alternate
        "border": "#E2E8F0",          # Subtle border
        "border_focus": "#3B82F6",    # Focused input ring
        
        # Typography
        "text_main": "#0F172A",       # Deep slate 900
        "text_sub": "#475569",        # Slate 600
        "text_muted": "#94A3B8",      # Slate 400
        "text_inverse": "#FFFFFF",
        
        # Primary Brand & Accents
        "primary": "#2563EB",         # Royal Blue
        "primary_hover": "#1D4ED8",
        "primary_light": "#EFF6FF",   # Soft blue badge background
        "primary_dark": "#1E40AF",
        
        # Functional Colors
        "success": "#10B981",         # Emerald 500
        "success_bg": "#ECFDF5",
        "success_text": "#065F46",
        "danger": "#EF4444",          # Rose/Red 500
        "danger_bg": "#FEF2F2",
        "danger_text": "#991B1B",
        "warning": "#F59E0B",         # Amber 500
        "warning_bg": "#FFFBEB",
        "warning_text": "#92400E",
        "info": "#06B6D4",            # Cyan 500
        "info_bg": "#ECFEFF",
        "info_text": "#155E75",

        # Navigation & Headers
        "nav_bg": "#0F172A",          # Deep midnight navy
        "nav_text": "#F8FAFC",
        "nav_active": "#3B82F6",
        "nav_sub": "#94A3B8",

        # Treeview (Data Tables)
        "tree_bg": "#FFFFFF",
        "tree_alt_bg": "#F8FAFC",
        "tree_fg": "#0F172A",
        "tree_selected_bg": "#DBEAFE", # Soft blue selection
        "tree_selected_fg": "#1E3A8A",
        "tree_head_bg": "#E2E8F0",
        "tree_head_fg": "#1E293B",
        
        # Form Controls
        "input_bg": "#FFFFFF",
        "input_fg": "#0F172A",
        "input_border": "#CBD5E1",
        "button_secondary_bg": "#E2E8F0",
        "button_secondary_fg": "#1E293B",
    },
    "dark": {
        "name": "dark",
        "app_bg": "#090D16",          # Deep obsidian navy
        "surface": "#131C2E",         # Dark slate card
        "surface_alt": "#1A253B",     # Alternate card background
        "border": "#24324D",          # Refined dark border
        "border_focus": "#60A5FA",
        
        # Typography
        "text_main": "#F8FAFC",       # Crisp white
        "text_sub": "#94A3B8",        # Slate 400
        "text_muted": "#64748B",      # Slate 500
        "text_inverse": "#0F172A",
        
        # Primary Brand & Accents
        "primary": "#3B82F6",         # Bright Blue
        "primary_hover": "#60A5FA",
        "primary_light": "#1E3A8A",
        "primary_dark": "#1D4ED8",
        
        # Functional Colors
        "success": "#34D399",
        "success_bg": "#064E3B",
        "success_text": "#A7F3D0",
        "danger": "#F87171",
        "danger_bg": "#7F1D1D",
        "danger_text": "#FECACA",
        "warning": "#FBBF24",
        "warning_bg": "#78350F",
        "warning_text": "#FDE68A",
        "info": "#38BDF8",
        "info_bg": "#164E63",
        "info_text": "#BAE6FD",

        # Navigation & Headers
        "nav_bg": "#0B1120",
        "nav_text": "#F8FAFC",
        "nav_active": "#60A5FA",
        "nav_sub": "#64748B",

        # Treeview (Data Tables)
        "tree_bg": "#131C2E",
        "tree_alt_bg": "#17233A",
        "tree_fg": "#F8FAFC",
        "tree_selected_bg": "#1E3A8A",
        "tree_selected_fg": "#FFFFFF",
        "tree_head_bg": "#0B1120",
        "tree_head_fg": "#CBD5E1",
        
        # Form Controls
        "input_bg": "#1A253B",
        "input_fg": "#F8FAFC",
        "input_border": "#2E4166",
        "button_secondary_bg": "#24324D",
        "button_secondary_fg": "#F8FAFC",
    }
}
