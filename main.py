from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
import os
import shutil
from detections import detect_and_track
from ai_helper import answer_question_with_groq, generate_sql, execute_sql

app = FastAPI(title="MemTracker API")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ----------------------------------------
# Request model for chat endpoint
# ----------------------------------------
class ChatRequest(BaseModel):
    question: str


# ----------------------------------------
# Wasiq's existing endpoint (unchanged)
# ----------------------------------------
@app.post("/upload-video/")
async def upload_video(file: UploadFile = File(...)):

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    detect_and_track(file_path, "output_tracked.avi")

    output_video_path = os.path.join(UPLOAD_FOLDER, "output_tracked.avi")
    if os.path.exists(output_video_path):
        with open(output_video_path, "rb") as f:
            return {
                "message": "Video processed successfully",
                "filename": file.filename,
                "saved_path": file_path,
                "output_video": f.read()
            }
    else:
        return {
            "message": "Video processing failed",
            "filename": file.filename,
            "saved_path": file_path
        }


# ----------------------------------------
# MANAHIL'S ENDPOINT 1: AI Summary
# GET /ai/summary
# Returns a summary of ALL activity in the DB
# ----------------------------------------
@app.get("/ai/summary")
async def get_summary():
    try:
        # Ask the LLM to summarize everything in the tracks table
        summary = answer_question_with_groq(
            "Give me a full summary of all persons tracked, "
            "their first and last activities, and how long they were present."
        )
        return {
            "status": "success",
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------
# MANAHIL'S ENDPOINT 2: AI Chat / Q&A
# POST /ai/chat
# Body: { "question": "Who stole the laptop?" }
# Returns: { "answer": "..." }
# ----------------------------------------
@app.post("/ai/chat")
async def chat(request: ChatRequest):
    try:
        answer = answer_question_with_groq(request.question)
        return {
            "status": "success",
            "question": request.question,
            "answer": answer
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------
# Health check
# ----------------------------------------
@app.get("/")
async def root():
    return {"message": "MemTracker API is running ✅ — Manahil's AI endpoints active"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)