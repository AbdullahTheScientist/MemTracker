import sqlite3
from datetime import datetime
import json

db_path = "tracking.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# -------------------------
# CREATE TABLES
# -------------------------
def create_db():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            activity TEXT NOT NULL,
            track_id INTEGER,
            details TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tracks (
            track_id INTEGER PRIMARY KEY,
            first_seen DATETIME NOT NULL,
            last_seen DATETIME NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            attributes TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            event_references TEXT
        )
    """)

def store_event_into_db(timestamp, track_id=None, activity=None, created_at=None):
    create_db()
    cursor.execute("""
        INSERT INTO events (timestamp, activity, track_id, created_at)
        VALUES (?, ?, ?, ?)
    """, (
        timestamp,
        activity,
        track_id,
        created_at
    ))
    conn.commit()

def store_track_into_db(track_id, first_seen, last_seen, is_active=True, attributes=None):
    create_db()
    cursor.execute("""
        INSERT OR REPLACE INTO tracks (track_id, first_seen, last_seen, is_active, attributes)
        VALUES (?, ?, ?, ?, ?)
    """, (
        track_id,
        first_seen,
        last_seen,
        is_active,
        json.dumps(attributes) if attributes else None
    ))
    conn.commit()

# -------------------------

# if __name__ == "__main__":
    # # Example usage
    # store_event_into_db(
    #     timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    #     track_id=1,
    #     activity="Walking",
    #     created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # )
    # store_track_into_db(
    #     track_id=1,
    #     first_seen=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    #     last_seen=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    #     is_active=True,
    #     attributes={"age": "30-40", "gender": "male"}
    # )

    # cursor.execute("SELECT * FROM events")
    # print("\n---- EVENTS ----")
    # for row in cursor.fetchall():
    #     print(row)

    # cursor.execute("SELECT * FROM tracks")
    # print("\n---- TRACKS ----")
    # for row in cursor.fetchall():
    #     print(row)