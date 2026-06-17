# ======================================================
# ================= COMPANION DATABASE ==================
# ======================================================
# This is 0.01 (Task Manager) + 0.02 (Profile & Memory) — the
# foundation everything else in AI Companion builds on top of.
#
# Key design rule: ONE companion.db PER INSTALLATION.
# Every machine that runs this creates its own fresh local file.
# We (Aahil/Himanshu) never see or touch this data — it never
# leaves the user's machine, there's no server, no sync.

import sqlite3
import os
from datetime import datetime, timezone

# ------------------------------------------------------
# WHERE THE DATABASE LIVES
# ------------------------------------------------------
# Don't put it next to the script — that breaks if the app gets
# reinstalled, updated, or packaged into an exe later. Use the
# OS's proper "app data" folder instead, same place real desktop
# apps store their local config/data.

def get_db_path():
    """
    Returns the correct local app-data path for companion.db,
    creating the folder if it doesn't exist yet. Works cross-platform.
    """
    if os.name == "nt":  # Windows
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:  # macOS / Linux
        base = os.path.join(os.path.expanduser("~"), ".local", "share")

    app_folder = os.path.join(base, "AICompanion")
    os.makedirs(app_folder, exist_ok=True)
    return os.path.join(app_folder, "companion.db")


DB_PATH = get_db_path()


# ------------------------------------------------------
# CONNECTION HELPER
# ------------------------------------------------------

def get_connection():
    """
    Opens a connection to companion.db. If the file doesn't exist yet,
    SQLite creates it automatically on first connect — that's the
    "first run" moment for a brand new install.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us access columns by name
    return conn


# ------------------------------------------------------
# SCHEMA SETUP — runs once, safe to call every startup
# ------------------------------------------------------

def init_db():
    """
    Creates all tables if they don't already exist. Safe to call on
    every app startup — CREATE TABLE IF NOT EXISTS means this never
    wipes existing data on a returning user's machine.
    """
    conn = get_connection()
    cur = conn.cursor()

    # ---- Profile: one row, basic identity info ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            name TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # ---- Tasks: 0.01 Task Manager ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            due_date TEXT,
            priority TEXT CHECK (priority IN ('low', 'medium', 'high')) DEFAULT 'medium',
            tags TEXT,
            is_done INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            completed_at TEXT
        )
    """)

    # ---- Memory: 0.02 long-term facts the companion remembers ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            category TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # ---- Conversation log: short-term context, recent turns ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS conversation_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT CHECK (role IN ('user', 'assistant')) NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def is_first_run():
    """
    True if companion.db didn't exist before this process started.
    Useful for triggering a one-time setup/welcome flow.
    """
    return not os.path.exists(DB_PATH)


# ------------------------------------------------------
# PROFILE — CRUD
# ------------------------------------------------------

def set_profile_name(name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO profile (id, name, created_at)
        VALUES (1, ?, ?)
        ON CONFLICT(id) DO UPDATE SET name = excluded.name
    """, (name, datetime.now(timezone.utc).isoformat()))
    conn.commit()
    conn.close()


def get_profile():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM profile WHERE id = 1")
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


# ------------------------------------------------------
# TASKS — CRUD (0.01)
# ------------------------------------------------------

def create_task(title, description=None, due_date=None, priority="medium", tags=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO tasks (title, description, due_date, priority, tags, is_done, created_at)
        VALUES (?, ?, ?, ?, ?, 0, ?)
    """, (title, description, due_date, priority, tags, datetime.now(timezone.utc).isoformat()))
    conn.commit()
    task_id = cur.lastrowid
    conn.close()
    return task_id


def get_tasks(include_done=False):
    conn = get_connection()
    cur = conn.cursor()
    if include_done:
        cur.execute("SELECT * FROM tasks ORDER BY created_at DESC")
    else:
        cur.execute("SELECT * FROM tasks WHERE is_done = 0 ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def complete_task(task_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE tasks SET is_done = 1, completed_at = ? WHERE id = ?
    """, (datetime.now(timezone.utc).isoformat(), task_id))
    conn.commit()
    changed = cur.rowcount
    conn.close()
    return changed > 0


def delete_task(task_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    changed = cur.rowcount
    conn.close()
    return changed > 0


# ------------------------------------------------------
# MEMORY — CRUD (0.02 long-term)
# ------------------------------------------------------

def save_memory(content, category=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO memory (content, category, created_at)
        VALUES (?, ?, ?)
    """, (content, category, datetime.now(timezone.utc).isoformat()))
    conn.commit()
    mem_id = cur.lastrowid
    conn.close()
    return mem_id


def get_all_memory():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM memory ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_memory(keyword):
    """Simple substring search — fine for now, replaced by smarter
    recall logic once the Memory Engine (0.03) is built."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM memory WHERE content LIKE ? ORDER BY created_at DESC
    """, (f"%{keyword}%",))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ------------------------------------------------------
# CONVERSATION LOG — short-term context (0.02 supporting piece)
# ------------------------------------------------------

def log_message(role, content):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO conversation_log (role, content, created_at)
        VALUES (?, ?, ?)
    """, (role, content, datetime.now(timezone.utc).isoformat()))
    conn.commit()
    conn.close()


def get_recent_messages(limit=10):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM conversation_log ORDER BY created_at DESC LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in reversed(rows)]  # oldest first, reads naturally
