# AcademiaSMS: User & Operator Manual

## 1. Introduction

**AcademiaSMS** is a high-performance, enterprise-grade desktop Student Management System built using Python, Tkinter (ttk), and an ACID-compliant SQLite backend. It follows a strict 3-tier layered architecture separating Presentation, Business/Service Rules, and Data Access (DAO).

---

## 2. Default Access Credentials

Upon initial launch, the system automatically creates the database and seeds the following default accounts:

| Username | Password | Role | Permissions |
|---|---|---|---|
| `admin` | `Admin@123` | **ADMIN** | Full system CRUD, permanent hard delete, backup, user audits |
| `staff` | `Staff@123` | **STAFF** | Student record creation, search, edit, and soft delete (archive) |

> [!IMPORTANT]
> The login system incorporates an automatic rate limiter. After **3 consecutive failed login attempts**, the account form is temporarily locked for **60 seconds** to safeguard against brute-force intrusion.

---

## 3. Core Features & User Workflows

### 3.1 Authentication & Theme Switching
1. Launch the application via `py app/main.py`.
2. Enter your username and password. Click **"Show"** to toggle password visibility.
3. Click **"Sign In to System"** (or press `Enter`).
4. You can toggle between **Light Mode** and **Dark Mode** anytime using the **☀️ Light / 🌙 Dark** button on the top right navigation bar.

### 3.2 Students Registry & Navigation
The **Students** tab displays a comprehensive tabular view of all student records:
- **Real-Time Debounced Search:** Type into the search bar (`🔍`). Search triggers automatically 300ms after you stop typing to prevent lag. You can search by Roll Number, First Name, Last Name, or Email.
- **Department & Year Filtering:** Select specific departments or academic years from the dropdown menus to narrow results.
- **Show Archived:** Toggle the *"Show Archived"* checkbox to inspect soft-deleted or inactive student records.
- **Sorting:** Click on any column header (e.g., Roll Number, Student Name, GPA, Last Modified) to sort Ascending (`▲`) or Descending (`▼`).
- **Pagination:** Navigate through records using the bottom pagination bar (`⏮`, `◀`, `▶`, `⏭`). You can change the page density (5, 10, 20, or 50 records per page).

### 3.3 Adding a New Student
1. Click the **"➕ Add Student"** button.
2. Complete the required fields marked with an asterisk (`*`):
   - **Roll Number:** 5 to 20 alphanumeric characters (unique).
   - **First & Last Name:** Letters and spaces only, max 50 characters.
   - **Date of Birth:** `YYYY-MM-DD` format. Validated for ages 15 to 60.
   - **Email:** Valid RFC-compliant address (unique).
   - **Phone:** Optional 7 to 15 digit telephone number.
   - **Department:** Select from registered academic departments.
   - **Year Level:** Choose Year 1 through Year 6.
   - **GPA:** Optional decimal between `0.00` and `10.00`.
3. Click **"Create Student"**. Inline validation will highlight any mistakes in red.

### 3.4 Editing & Optimistic Concurrency Control
1. Double-click any row in the student table, or select it and click **"✏️ Edit"**.
2. Modify the student's attributes.
3. Click **"Update Record"**.
4. **Concurrency Conflict Protection:** If another user or process modified this student record while your edit window was open, the system detects a timestamp mismatch via `updated_at`, blocks overwrites, and prompts you to refresh the latest data.

### 3.5 Archiving (Soft Delete) vs Permanent Deletion
1. Select a student and click **"🗑️ Delete / Archive"**.
2. A confirmation dialog will appear:
   - **Archive Record (Default):** Soft-deletes the record by marking `is_archived = 1`. This is reversible and retains all academic history.
   - **Restore Record:** If the student was already archived, you can restore them back to active status with one click.
   - **Permanently Delete (Admin Only):** Irreversibly purges the record from the database. This option is disabled for Staff users.

### 3.6 Bulk Import & Export
- **Bulk Import (CSV / Excel):** Click **"📥 Import"** and select a `.csv`, `.xlsx`, or `.xls` file. The system validates every row. If even a single row has an error or duplicate, the **entire batch is rolled back** in a transaction to protect database integrity, and a detailed line-by-line error report is shown.
- **CSV Export:** Click **"📄 Export CSV"** to save all current filtered records into a comma-separated spreadsheet.
- **PDF Report Generation:** Click **"📑 Export PDF"** to generate an executive, print-ready document formatted with custom university headers and color-coded table rows using ReportLab.

### 3.7 Database Backups & Audit Trail
- **Online Hot Backup:** Click **"💾 Backup DB"** at any time. The application utilizes SQLite's online backup engine to snapshot the active database without interrupting reads or writes.
- **Audit Logs:** Switch to the **"📜 Audit Logs"** tab in the navigation bar to inspect who created, updated, archived, or deleted records, along with exact timestamps and change descriptions.
