<!-- Auto-generated guidance for AI coding agents working on InstrumentTracker -->
# InstrumentTracker — Copilot instructions

Brief, actionable notes to help AI coding agents be productive in this repository.

## Big picture
- UI: A PyQt6 desktop application. `main.py` builds the main window and tabs and imports dialogs from `views/*.py`.
- Persistence: SQLite database file `inventory.db` at project root. Database access is centralized in `database/db_manager.py` (singleton `DatabaseManager`). A legacy helper `database/db_core.py` is used by `reset_db.py` to recreate the DB.
- Views: Dialogs and UI logic live in `views/` (examples: `asset_dialog.py`, `issue_dialog.py`, `return_dialog.py`, `edit_asset_dialog.py`). Business logic is thin and operates via SQL through `DatabaseManager`.

## Running & developer workflows
- Run the app: with Python 3 and PyQt6 installed, run `python main.py` from the project root.
- Check DB: `python check_db.py` will print tables and sample rows.
- Reset DB (drops and recreates `inventory.db`): `python reset_db.py` (this uses `database/db_core.py` and repopulates sample data).
- Note: `requirements.txt` is currently empty; the code requires at least `PyQt6` (install with `pip install PyQt6`).

## Key patterns & conventions (project-specific)
- Database access:
  - Use the singleton `DatabaseManager()` from `database/db_manager.py`.
  - Read queries: `execute_query(query, params=())` — returns `list[tuple]` (rows).
  - Write/update queries: `execute_update(query, params=())` — commits and returns `cursor.lastrowid`.
  - Concurrency: DB connection is opened with `check_same_thread=False` and protected by a `QMutex` / `QMutexLocker` around calls.
  - The DB uses `PRAGMA journal_mode=WAL` for WAL journaling.

- Domain strings (literal values used across UI and SQL):
  - Asset statuses: `'Доступен'`, `'Выдан'` (used directly in WHERE / UPDATE clauses).
  - Operation types: `'выдача'`, `'возврат'`, `'списание'` (used in `Usage_History.operation_type`).
  - When adding user-supplied `Locations`, code appends a trailing ` *` (star) to mark custom locations — e.g. `"{name} *"`.

- Queries and UI data flow:
  - Many UI dialogs load dropdowns with `SELECT ... FROM <table>` and then use `.addItem(display, id)` storing the DB id in the widget.
  - Example: `asset_dialog.load_dropdown_data()` loads `Asset_Types` and `Locations` with `type_id/type_name` and `location_id/location_name`.

- Error / confirmation handling: UI uses `QMessageBox` for validation errors and confirmations (e.g. issuing an asset shows a confirmation dialog before updating DB).

## Files to reference when coding
- `main.py` — app entry, high-level UI wiring and calls to `DatabaseManager`.
- `database/db_manager.py` — central DB singleton and helper methods (`execute_query`, `execute_update`).
- `database/db_core.py` — DB schema builder and test-data seeding (used by `reset_db.py`).
- `views/*.py` — all UI dialogs. Follow the pattern: load dropdowns via DB queries, validate fields, then `execute_update` to persist.
- `notification_manager.py` — deadline checking and Mac-style popup notifications. `NotificationManager` singleton runs periodic deadline checks; `NotificationWidget` renders top-right popups.
- `reset_db.py`, `check_db.py` — scripts for resetting and validating DB state.
- `test_notifications.py` — test script for deadline/notification functionality.

## Notifications & deadline checking (notification_manager.py)
- **Automatic deadline checker**: `NotificationManager` runs every 60 seconds (configurable).
  - Checks `Usage_History` records where `operation_type='выдача'` and `actual_return_date IS NULL`.
  - Triggers visual notifications for upcoming/overdue returns: tomorrow, today, or past the deadline.
- **Visual indicators**: `NotificationWidget` (Mac-style popup):
  - Appears in top-right corner with fade-in/fade-out animations.
  - Types: `'info'` (gray), `'warning'` (yellow), `'error'` (red), `'success'` (green).
  - Auto-closes after 4 seconds; can stack multiple notifications.
- **Automatic status annotations**: When loading history (`load_history_data()`):
  - Queries check if `actual_return_date > planned_return_date` or still null but overdue.
  - Appends `[Просрочено]` or `[Возвращено с опозданием]` to `notes` column in display.
  - Uses `_mark_as_overdue()` and `_update_overdue_notes()` helpers to persist annotations.

## Files to reference when coding

## Important implementation notes for AI edits
- Avoid deleting or reinitializing the DB silently. Code comments explicitly say "НЕ удаляем базу данных" in `DatabaseManager._init_db()` — follow existing DB preservation behaviour.
- String literals are significant (Russian UI and DB values); prefer using the same literals when modifying SQL or UI text to remain consistent.
- Keep `check_same_thread=False` + mutex approach when touching concurrency; changing DB threading must be deliberate and tested manually.
- When adding a new DB column or table, update both `db_manager._create_tables()` and `db_core.init_db()` (they both describe the schema). Also update `reset_db.py` expectations if schema changes.

## Quick examples (copyable)
- Query rows:
  - `rows = DatabaseManager().execute_query("SELECT type_id, type_name FROM Asset_Types")`
  - iterate: `for type_id, type_name in rows: ...`
- Insert and get id:
  - `new_id = DatabaseManager().execute_update("INSERT INTO Locations (location_name) VALUES (?)", (name,))`

## When to ask the human
- Any change that mutates the DB schema (add/remove columns or tables).
- Any change to domain literal values (statuses, operation_type strings) that could break existing data.

If anything here is unclear or you'd like a different level of detail (examples, more file links, or a checklist for schema changes), tell me which parts to expand and I'll iterate.
