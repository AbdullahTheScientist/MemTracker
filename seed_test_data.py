import sqlite3
import json

conn = sqlite3.connect("tracking.db")
cursor = conn.cursor()

# Create tables
cursor.execute("""
    CREATE TABLE IF NOT EXISTS tracks (
        track_id INTEGER PRIMARY KEY,
        first_seen TEXT,
        last_seen TEXT,
        is_active BOOLEAN DEFAULT 1,
        attributes TEXT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME,
        activity TEXT,
        track_id INTEGER,
        created_at DATETIME
    )
""")

# Insert fake persons
cursor.execute("INSERT OR REPLACE INTO tracks VALUES (?, ?, ?, ?, ?)", (
    1, "0:00:03", "0:01:45", False,
    json.dumps({"duration_sec": 102, "first_activity": "The person is standing", "last_activity": "The man is holding a laptop"})
))

cursor.execute("INSERT OR REPLACE INTO tracks VALUES (?, ?, ?, ?, ?)", (
    2, "0:00:10", "0:02:30", False,
    json.dumps({"duration_sec": 140, "first_activity": "The person is walking", "last_activity": "The person is standing"})
))

cursor.execute("INSERT OR REPLACE INTO tracks VALUES (?, ?, ?, ?, ?)", (
    3, "0:01:00", "0:02:50", False,
    json.dumps({"duration_sec": 110, "first_activity": "The person picked the laptop", "last_activity": "The person is walking"})
))

conn.commit()
conn.close()

print("✅ Test data inserted successfully!")
print("Now run: python ai_helper.py")