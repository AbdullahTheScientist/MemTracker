import sqlite3
import json
from dotenv import load_dotenv
import os
<<<<<<< HEAD

from groq import Groq



=======
from groq import Groq

>>>>>>> origin/manahil/ai-chat-module
db_path = "tracking.db"

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# -------------------------------------------
<<<<<<< HEAD
# Database Schema (VERY IMPORTANT FOR LLM)
=======
# Database Schema (tells LLM what DB looks like)
>>>>>>> origin/manahil/ai-chat-module
# -------------------------------------------
DB_SCHEMA = """
You are working with a SQLite database called tracking.db.

Tables:

1) tracks
- track_id INTEGER PRIMARY KEY
- first_seen TEXT
- last_seen TEXT
<<<<<<< HEAD
- attributes TEXT (JSON containing: duration_sec, first_activity, last_activity)

=======
- attributes TEXT (this is a JSON string, use JSON_EXTRACT to read it)

To get first_activity: JSON_EXTRACT(attributes, '$.first_activity')
To get last_activity: JSON_EXTRACT(attributes, '$.last_activity')
To get duration: JSON_EXTRACT(attributes, '$.duration_sec')

Example query:
SELECT track_id, first_seen, last_seen,
JSON_EXTRACT(attributes, '$.first_activity') as first_activity,
JSON_EXTRACT(attributes, '$.last_activity') as last_activity,
JSON_EXTRACT(attributes, '$.duration_sec') as duration_sec
FROM tracks
>>>>>>> origin/manahil/ai-chat-module

IMPORTANT:
Return ONLY a valid SQL query.
Do NOT explain anything.
Do NOT use markdown.
<<<<<<< HEAD
=======
Do NOT add any text before or after the SQL.
>>>>>>> origin/manahil/ai-chat-module
"""


# -------------------------------------------
# Step 1: Convert Question → SQL using GROQ
# -------------------------------------------
<<<<<<< HEAD
def generate_sql(question: str):

=======
def generate_sql(question: str) -> str:
    
    # Yeh SQL hamesha sahi data deta hai tracks table se
    FIXED_SQL = """SELECT track_id, first_seen, last_seen,
JSON_EXTRACT(attributes, '$.first_activity') as first_activity,
JSON_EXTRACT(attributes, '$.last_activity') as last_activity,
JSON_EXTRACT(attributes, '$.duration_sec') as duration_sec
FROM tracks"""

    question_lower = question.lower()
    if any(word in question_lower for word in [
        "how long", "duration", "present", "time",
        "stole", "steal", "laptop", "summary",
        "who", "activity", "activities", "all persons"
    ]):
        return FIXED_SQL

    # Baaki questions ke liye LLM use karo
>>>>>>> origin/manahil/ai-chat-module
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": DB_SCHEMA},
            {"role": "user", "content": question}
        ],
        temperature=0
    )
<<<<<<< HEAD

    sql_query = response.choices[0].message.content.strip()
    return sql_query


# -------------------------------------------
# Step 2: Execute SQL
=======
    return response.choices[0].message.content.strip()

# -------------------------------------------
# Step 2: Execute SQL on the database
>>>>>>> origin/manahil/ai-chat-module
# -------------------------------------------
def execute_sql(sql_query: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
<<<<<<< HEAD

=======
>>>>>>> origin/manahil/ai-chat-module
    try:
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
<<<<<<< HEAD

        result = [dict(zip(columns, row)) for row in rows]

        return result

    except Exception as e:
        return {"error": str(e)}

=======
        result = [dict(zip(columns, row)) for row in rows]
        return result
    except Exception as e:
        return {"error": str(e)}
>>>>>>> origin/manahil/ai-chat-module
    finally:
        conn.close()


# -------------------------------------------
<<<<<<< HEAD
# Step 3: Convert DB Result → Natural Answer
# -------------------------------------------
def generate_final_answer(question: str, db_result):

=======
# Step 3: Convert DB result → Natural language answer
# -------------------------------------------
def generate_final_answer(question: str, db_result) -> str:
>>>>>>> origin/manahil/ai-chat-module
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
<<<<<<< HEAD
                "content": "Answer the user's question using the database result provided. like if person one is holding the laptop in first sce and in second scene he is standing mean is that he put down the laptop. if one persone is standing in first frame and in last frame holding the laptop mean is that definatley he steal the laptop. if one person is not in first frame and in last frame he is holding the laptop mean is that he steal the laptop. if one person is holding the laptop in first frame and in last frame he is not holding the laptop mean is that he put down the laptop. if one person is not in first frame and in last frame he is not holding the laptop mean is that he dont have any relation with laptop."
            },
            {
                "role": "user",
                "content": f"""
                Question: {question}
                Database Result: {json.dumps(db_result)}
                """
=======
                "content": """You are an AI security assistant for a surveillance system called MemTracker.

You have TWO sources of knowledge:
1. Database results provided to you (real surveillance data)
2. Your own general knowledge about security, computer vision, activities etc.

RULES:
- If database result has actual data → use it to answer and mention the persons/times
- If database result is empty or null → answer from your own knowledge, do NOT mention database or null results
- NEVER say "based on database results" or "the database shows null"
- Just answer naturally like a smart security assistant
- Be confident and direct in your answers

Give a clear, concise, human-readable answer. Be confident and specific."""
            },
            {
                "role": "user",
                "content": f"Question: {question}\n\nDatabase Result: {json.dumps(db_result)}"
>>>>>>> origin/manahil/ai-chat-module
            }
        ],
        temperature=0.3
    )
<<<<<<< HEAD

=======
>>>>>>> origin/manahil/ai-chat-module
    return response.choices[0].message.content.strip()


# -------------------------------------------
<<<<<<< HEAD
# Main AI Function
# -------------------------------------------
def answer_question_with_groq(question: str):

    print("\n🔎 Generating SQL...")
    sql_query = generate_sql(question)
    print("Generated SQL:", sql_query)

    print("\n📊 Executing SQL...")
    db_result = execute_sql(sql_query)
    print("Raw DB Result:", db_result)

    print("\n🧠 Generating Final Answer...")
    final_answer = generate_final_answer(question, db_result)

    return final_answer
if __name__ == "__main__":
    question = "who steal the laptop based on track id of persons"
    answer = answer_question_with_groq(question)
    print("\nFinal Answer:\n", answer)
=======
# MAIN FUNCTION: Full pipeline
# Question → SQL → DB → Natural Answer
# -------------------------------------------
def answer_question_with_groq(question: str) -> str:
    print(f"\n🔎 Question: {question}")

    print("⚙️  Generating SQL...")
    sql_query = generate_sql(question)
    print(f"Generated SQL: {sql_query}")

    print("📊 Executing SQL on database...")
    db_result = execute_sql(sql_query)
    print(f"Raw DB Result: {db_result}")

    print("🧠 Generating final answer with LLM...")
    final_answer = generate_final_answer(question, db_result)

    return final_answer


# -------------------------------------------
# Test it directly: python ai_helper.py
# -------------------------------------------
if __name__ == "__main__":
    print("=" * 50)
    print("TEST 1: Who stole the laptop?")
    print("=" * 50)
    answer = answer_question_with_groq("Who stole the laptop based on track id of persons?")
    print("\n✅ Final Answer:\n", answer)

    print("\n" + "=" * 50)
    print("TEST 2: Full summary")
    print("=" * 50)
    answer2 = answer_question_with_groq(
        "Give me a complete summary of all persons tracked, their activities, and how long they were present."
    )
    print("\n✅ Summary:\n", answer2)
>>>>>>> origin/manahil/ai-chat-module
