import sqlite3
import re
from datetime import datetime
from dotenv import load_dotenv
import os
from groq import Groq

db_path = "tracking.db"

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Groq llama-3.3-70b has a large context window but we keep our payload
# tight so the model reasons well and never hits rate-limit token caps.
MAX_CONTEXT_CHARS = 10_000

# ─────────────────────────────────────────────────────────────────────────────
# SQL generation
# ─────────────────────────────────────────────────────────────────────────────
DB_SCHEMA = """You are a SQLite query generator for a surveillance tracking system.

Database: tracking.db
Table: events
Columns:
  - id        INTEGER  (primary key, auto-increment)
  - track_id  INTEGER  (unique ID per tracked person)
  - activity  TEXT     (e.g. "The person is walking", "The person is standing")
  - timestamp TEXT     (time string HH:MM:SS)

RULES — follow strictly:
1. Output ONLY a single raw SQL SELECT statement. No markdown, no backticks, no explanation, no semicolons.
2. Never use columns that don't exist.
3. Always ORDER BY timestamp ASC so events are in chronological order.
4. For general summaries / "what happened" → SELECT * FROM events ORDER BY timestamp ASC
5. For a specific person → SELECT * FROM events WHERE track_id = <id> ORDER BY timestamp ASC
6. For activity queries → SELECT * FROM events WHERE activity LIKE '%keyword%' ORDER BY timestamp ASC
7. For time range queries → SELECT * FROM events WHERE timestamp BETWEEN 'HH:MM:SS' AND 'HH:MM:SS' ORDER BY timestamp ASC
8. For "how many people" → SELECT COUNT(DISTINCT track_id) as total_persons FROM events
9. For "last seen" or "latest" → SELECT * FROM events ORDER BY timestamp DESC LIMIT 30
10. Never add a LIMIT unless the question specifically asks for a small number of results.
"""

FALLBACK_SQL = "SELECT * FROM events ORDER BY timestamp ASC"


def generate_sql(question: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": DB_SCHEMA},
            {"role": "user", "content": f"Generate a SQL query for: {question}\nOutput ONLY raw SQL."},
        ],
        temperature=0,
        max_tokens=200,
    )
    return _extract_sql(response.choices[0].message.content.strip())


def _extract_sql(raw: str) -> str:
    raw = re.sub(r"```(?:sql)?", "", raw, flags=re.IGNORECASE).replace("```", "").strip()
    match = re.search(r"(SELECT\s.+?)(?:;|$)", raw, re.IGNORECASE | re.DOTALL)
    if match:
        sql = match.group(1).strip().rstrip(";")
        if re.match(r"^\s*SELECT\s", sql, re.IGNORECASE):
            return sql
    print(f"⚠️  Bad SQL from LLM: {repr(raw)} — using fallback")
    return FALLBACK_SQL


# ─────────────────────────────────────────────────────────────────────────────
# Execute SQL
# ─────────────────────────────────────────────────────────────────────────────
def execute_sql(sql_query: str) -> list:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        columns = [d[0] for d in cursor.description] if cursor.description else []
        return [dict(zip(columns, r)) for r in rows]
    except Exception as e:
        print(f"❌ SQL error: {e} — retrying with fallback")
        try:
            cursor.execute(FALLBACK_SQL)
            rows = cursor.fetchall()
            columns = [d[0] for d in cursor.description] if cursor.description else []
            return [dict(zip(columns, r)) for r in rows]
        except Exception:
            return []
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Time helpers
# ─────────────────────────────────────────────────────────────────────────────
def _parse_ts(ts: str):
    try:
        return datetime.strptime(ts, "%H:%M:%S")
    except Exception:
        return None


def _duration_str(start_ts: str, end_ts: str) -> str:
    s, e = _parse_ts(start_ts), _parse_ts(end_ts)
    if s and e and e >= s:
        secs = int((e - s).total_seconds())
        if secs < 60:
            return f"{secs}s"
        return f"{secs // 60}m {secs % 60}s"
    return "?"


# ─────────────────────────────────────────────────────────────────────────────
# Context builder — compresses ANY number of rows to under MAX_CONTEXT_CHARS
#
# KEY INSIGHT: 1,610 raw rows → maybe only 20-30 unique activity transitions.
# We never send raw rows. We send segments (compressed runs of the same
# activity) and a transition log (one line per change, not per detection).
# This turns 72,907 chars into ~2,000-4,000 chars regardless of video length.
# ─────────────────────────────────────────────────────────────────────────────
def build_context(db_result: list) -> str:
    if not db_result:
        return "No tracking events found in the database."

    # Aggregate result (e.g. COUNT DISTINCT query)
    if "track_id" not in db_result[0]:
        return "Aggregate result: " + ", ".join(
            f"{k}={v}" for row in db_result for k, v in row.items()
        )

    # Sort chronologically
    rows = sorted(db_result, key=lambda r: r.get("timestamp") or "")

    # ── Compress each person's events into activity segments ──
    # A "segment" = a consecutive run of the same activity.
    # 800 frames of "walking" → 1 segment with start/end/count.
    persons: dict = {}
    for row in rows:
        tid = row.get("track_id", "unknown")
        act = row.get("activity", "unknown")
        ts  = row.get("timestamp", "?")
        if tid not in persons:
            persons[tid] = []
        segs = persons[tid]
        if not segs or segs[-1]["activity"] != act:
            segs.append({"activity": act, "start": ts, "end": ts, "count": 1})
        else:
            segs[-1]["end"] = ts
            segs[-1]["count"] += 1

    # ── Build compact context string ──
    lines = [
        "=== SURVEILLANCE SESSION ===",
        f"Total detections : {len(rows)}",
        f"Unique persons   : {len(persons)}",
        f"Session start    : {rows[0].get('timestamp', '?')}",
        f"Session end      : {rows[-1].get('timestamp', '?')}",
        "",
    ]

    for tid, segs in persons.items():
        first_ts  = segs[0]["start"]
        last_ts   = segs[-1]["end"]
        total_det = sum(s["count"] for s in segs)
        session_dur = _duration_str(first_ts, last_ts)

        lines.append(f"--- Person {tid} ---")
        lines.append(
            f"  Present: {first_ts} → {last_ts}  "
            f"(total duration: {session_dur}, {total_det} detections, {len(segs)} activity segments)"
        )
        lines.append("  Activity timeline:")
        for i, seg in enumerate(segs, 1):
            dur = _duration_str(seg["start"], seg["end"])
            lines.append(
                f"    {i}. [{seg['start']} → {seg['end']}] {dur} | "
                f"{seg['count']} frames | {seg['activity']}"
            )
        lines.append("")

    # ── Transition log: one line per activity change across all persons ──
    # This is the most information-dense part for the LLM —
    # it shows the exact moment each person changed behaviour.
    lines.append("=== ACTIVITY CHANGE LOG ===")
    prev: dict = {}
    for row in rows:
        tid = row.get("track_id", "?")
        act = row.get("activity", "?")
        ts  = row.get("timestamp", "?")
        if prev.get(tid) != act:
            lines.append(f"  [{ts}] Person {tid}: {act}")
            prev[tid] = act

    context = "\n".join(lines)

    # ── Hard trim if somehow still over the limit ──
    if len(context) > MAX_CONTEXT_CHARS:
        context = _trim_to_limit(context, len(rows))

    return context


def _trim_to_limit(context: str, total_rows: int) -> str:
    """Last-resort trim — cuts the bottom of the change log and adds a note."""
    cut = MAX_CONTEXT_CHARS - 300
    trimmed = context[:cut]
    trimmed = trimmed[: trimmed.rfind("\n")]
    trimmed += (
        f"\n  ... [change log truncated — {total_rows} total detections] ...\n"
        "  [The per-person summary above is complete and accurate]"
    )
    return trimmed


# ─────────────────────────────────────────────────────────────────────────────
# Final answer generation
# ─────────────────────────────────────────────────────────────────────────────
ANALYST_SYSTEM_PROMPT = """You are an expert AI security analyst for MemTracker, a real-time person tracking and surveillance system.

You receive a user question and a structured tracking data block.

YOUR JOB:
- Answer precisely using only the tracking data provided.
- Describe what happened chronologically: who did what, when, in what order, for how long.
- Use exact timestamps (e.g. "At 10:04:12, Person 2 picked up the laptop").
- Describe activity transitions (e.g. "Person 1 stood still from 10:01 to 10:03, then began walking").
- Compute durations when asked — each segment has a start time, end time, and duration already calculated.
- If multiple persons are tracked, describe each one separately then note any overlapping events.
- If the data is empty, say so clearly.

STRICT RULES:
- Never mention SQL, databases, errors, or technical internals.
- Never say "based on the data" — state facts directly as a security analyst would.
- Never invent events not present in the data.
- Refer to persons by their ID: Person 1, Person 2, etc.
- Be concise and professional. Write like a trained analyst producing an incident report.
"""


def generate_final_answer(question: str, context: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": ANALYST_SYSTEM_PROMPT},
            {"role": "user", "content": f"Question: {question}\n\nTracking Data:\n{context}"},
        ],
        temperature=0.1,
        max_tokens=900,
    )
    return response.choices[0].message.content.strip()


# ─────────────────────────────────────────────────────────────────────────────
# Main pipeline
# ─────────────────────────────────────────────────────────────────────────────
def answer_question_with_groq(question: str) -> str:
    print(f"\n🔎 Question: {question}")

    print("⚙️  Generating SQL...")
    sql = generate_sql(question)
    print(f"✅ SQL: {sql}")

    print("📊 Executing SQL...")
    rows = execute_sql(sql)
    print(f"📦 Rows returned: {len(rows)}")

    print("🧠 Building context...")
    context = build_context(rows)
    print(f"📝 Context length: {len(context)} chars  (limit: {MAX_CONTEXT_CHARS})")

    print("💬 Generating answer...")
    answer = generate_final_answer(question, context)

    return answer








