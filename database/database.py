import sqlite3
from datetime import datetime

DB_PATH = "tracking.db"


def get_conn():
    """Always open a fresh connection — safe to call from any thread."""
    return sqlite3.connect(DB_PATH, check_same_thread=False)


# -------------------------
# CREATE TABLES
# -------------------------
def create_db():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id  INTEGER,
            activity  TEXT NOT NULL,
            timestamp TEXT DEFAULT (strftime('%H:%M:%S', 'now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            role             TEXT NOT NULL,
            message          TEXT NOT NULL,
            timestamp        DATETIME DEFAULT CURRENT_TIMESTAMP,
            event_references TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database tables ensured.")


def store_event_into_db(timestamp, activity, track_id=None):
    """Insert one tracking event. Auto-creates tables if they don't exist yet."""
    conn = get_conn()
    cursor = conn.cursor()

    # Safety: make sure the table exists (idempotent, cheap)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id  INTEGER,
            activity  TEXT NOT NULL,
            timestamp TEXT DEFAULT (strftime('%H:%M:%S', 'now'))
        )
    """)

    cursor.execute(
        "INSERT INTO events (track_id, activity, timestamp) VALUES (?, ?, ?)",
        (track_id, activity, timestamp),
    )

    conn.commit()
    conn.close()


def get_all_events():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events ORDER BY id DESC")
    rows = cursor.fetchall()
    columns = [d[0] for d in cursor.description]
    conn.close()
    return [dict(zip(columns, row)) for row in rows]


# Auto-create on import so the tables always exist when the app starts
create_db()