from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import os
import shutil
from uuid import uuid4
from ai_helper import answer_question_with_groq, generate_sql, execute_sql
from pydantic import BaseModel
from models import VideoProcessor

class ChatRequest(BaseModel):
    question: str



app = FastAPI(title="MemTracker API")

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@app.post("/upload-video/")
async def upload_video(file: UploadFile = File(...)):
    """
    Upload a video → Process it → Return processed video
    """

    # Generate unique filename (important for Railway)
    unique_id = str(uuid4())
    input_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}_{file.filename}")
    output_path = os.path.join(OUTPUT_FOLDER, f"{unique_id}_tracked.avi")

    # Save uploaded file
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Process video
    processor = VideoProcessor(input_path, output_path)
    processor.process()

    # Return processed file
    if os.path.exists(output_path):
        return FileResponse(
            output_path,
            media_type="video/x-msvideo",
            filename="tracked_video.avi"
        )

    return {"error": "Video processing failed"}


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




if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))

    uvicorn.run(
        # "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )














# from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
# from fastapi.responses import FileResponse
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# import os
# import shutil
# from uuid import uuid4

# from ai_helper import answer_question_with_groq
# from models import VideoProcessor


# # -------------------------------
# # Request Model
# # -------------------------------
# class ChatRequest(BaseModel):
#     question: str


# # -------------------------------
# # App Initialization
# # -------------------------------
# app = FastAPI(
#     title="MemTracker API",
#     version="1.0"
# )

# # -------------------------------
# # Enable CORS
# # -------------------------------
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # -------------------------------
# # Folder Setup
# # -------------------------------
# UPLOAD_FOLDER = "uploads"
# OUTPUT_FOLDER = "outputs"

# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# # Track job status
# job_status = {}


# # -------------------------------
# # Background Processing Function
# # -------------------------------
# def process_video_background(job_id, input_path, output_path):
#     try:
#         processor = VideoProcessor(input_path, output_path)
#         processor.process()

#         job_status[job_id] = "completed"

#     except Exception as e:
#         job_status[job_id] = f"failed: {str(e)}"


# # -------------------------------
# # Root Endpoint
# # -------------------------------
# @app.get("/")
# def home():
#     return {"message": "MemTracker API running", "docs": "/docs"}


# # -------------------------------
# # Upload Video
# # -------------------------------
# @app.post("/upload-video")
# async def upload_video(
#     background_tasks: BackgroundTasks,
#     file: UploadFile = File(...)
# ):

#     if not file.filename:
#         raise HTTPException(status_code=400, detail="No file uploaded")

#     job_id = str(uuid4())

#     input_path = os.path.join(
#         UPLOAD_FOLDER,
#         f"{job_id}_{file.filename}"
#     )

#     output_path = os.path.join(
#         OUTPUT_FOLDER,
#         f"{job_id}_tracked.avi"
#     )

#     # Save uploaded file
#     with open(input_path, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)

#     # Mark job as processing
#     job_status[job_id] = "processing"

#     # Run processing in background
#     background_tasks.add_task(
#         process_video_background,
#         job_id,
#         input_path,
#         output_path
#     )

#     return {
#         "job_id": job_id,
#         "status": "processing"
#     }


# # -------------------------------
# # Check Video Status
# # -------------------------------
# @app.get("/video-status/{job_id}")
# def video_status(job_id: str):

#     if job_id not in job_status:
#         raise HTTPException(status_code=404, detail="Job not found")

#     return {
#         "job_id": job_id,
#         "status": job_status[job_id]
#     }


# # -------------------------------
# # Download Processed Video
# # -------------------------------
# @app.get("/download/{job_id}")
# def download_video(job_id: str):

#     output_path = os.path.join(
#         OUTPUT_FOLDER,
#         f"{job_id}_tracked.avi"
#     )

#     if not os.path.exists(output_path):
#         raise HTTPException(
#             status_code=404,
#             detail="Video not ready yet"
#         )

#     return FileResponse(
#         output_path,
#         media_type="video/x-msvideo",
#         filename="tracked_video.avi"
#     )


# # -------------------------------
# # AI Summary
# # -------------------------------
# @app.get("/ai/summary")
# async def get_summary():

#     try:
#         summary = answer_question_with_groq(
#             "Give a summary of all tracked persons and activities."
#         )

#         return {
#             "status": "success",
#             "summary": summary
#         }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# # -------------------------------
# # AI Chat
# # -------------------------------
# @app.post("/ai/chat")
# async def chat(request: ChatRequest):

#     try:
#         answer = answer_question_with_groq(request.question)

#         return {
#             "status": "success",
#             "answer": answer
#         }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# # -------------------------------
# # Run Server
# # -------------------------------
# if __name__ == "__main__":
#     import uvicorn

#     port = int(os.environ.get("PORT", 8000))

#     uvicorn.run(
#         "main:app",
#         host="0.0.0.0",
#         port=port,
#         reload=True
#     )
