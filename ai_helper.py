import sqlite3
import json
from dotenv import load_dotenv
import os

from groq import Groq



db_path = "tracking.db"

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# -------------------------------------------
# Database Schema (VERY IMPORTANT FOR LLM)
# -------------------------------------------
DB_SCHEMA = """
You are working with a SQLite database called tracking.db.

Tables:

1) tracks
- track_id INTEGER PRIMARY KEY
- first_seen TEXT
- last_seen TEXT
- attributes TEXT (JSON containing: duration_sec, first_activity, last_activity)


IMPORTANT:
Return ONLY a valid SQL query.
Do NOT explain anything.
Do NOT use markdown.
"""


# -------------------------------------------
# Step 1: Convert Question → SQL using GROQ
# -------------------------------------------
def generate_sql(question: str):

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": DB_SCHEMA},
            {"role": "user", "content": question}
        ],
        temperature=0
    )

    sql_query = response.choices[0].message.content.strip()
    return sql_query


# -------------------------------------------
# Step 2: Execute SQL
# -------------------------------------------
def execute_sql(sql_query: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []

        result = [dict(zip(columns, row)) for row in rows]

        return result

    except Exception as e:
        return {"error": str(e)}

    finally:
        conn.close()


# -------------------------------------------
# Step 3: Convert DB Result → Natural Answer
# -------------------------------------------
def generate_final_answer(question: str, db_result):

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "Answer the user's question using the database result provided. like if person one is holding the laptop in first sce and in second scene he is standing mean is that he put down the laptop. if one persone is standing in first frame and in last frame holding the laptop mean is that definatley he steal the laptop. if one person is not in first frame and in last frame he is holding the laptop mean is that he steal the laptop. if one person is holding the laptop in first frame and in last frame he is not holding the laptop mean is that he put down the laptop. if one person is not in first frame and in last frame he is not holding the laptop mean is that he dont have any relation with laptop."
            },
            {
                "role": "user",
                "content": f"""
                Question: {question}
                Database Result: {json.dumps(db_result)}
                """
            }
        ],
        temperature=0.3
    )

    return response.choices[0].message.content.strip()


# -------------------------------------------
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