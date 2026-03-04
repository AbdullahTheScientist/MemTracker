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
    uvicorn.run(app, host="127.0.0.1", port=8000)

















# from fastapi import FastAPI
# from fastapi import File, UploadFile
# import os
# # from detections import detect_and_track
# from ultralytics import YOLO
# import shutil

# from config import INPUT_VIDEO, OUTPUT_VIDEO
# from models import VideoProcessor

# if __name__ == "__main__":
#     processor = VideoProcessor(INPUT_VIDEO, OUTPUT_VIDEO)
#     processor.process()















# app = FastAPI()

# UPLOAD_FOLDER = "uploads"

# # Create folder if it doesn't exist
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# @app.post("/upload-video/")
# async def upload_video(file: UploadFile = File(...)):
    
#     file_path = os.path.join(UPLOAD_FOLDER, file.filename)

#     # Save file to disk
#     with open(file_path, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)

#     (file_path, "output_tracked.avi")

#     # return back back video file
#     output_video_path = os.path.join(UPLOAD_FOLDER, "output_tracked.avi")
#     if os.path.exists(output_video_path):
#         with open(output_video_path, "rb") as f:
#             return {
#                 "message": "Video processed successfully",
#                 "filename": file.filename,
#                 "saved_path": file_path,
#                 "output_video": f.read()
#             }
#     else:
#         return {
#             "message": "Video processing failed",
#             "filename": file.filename,
#             "saved_path": file_path
#         }

#     # return {
#     #     "message": "Video uploaded successfully",
#     #     "filename": file.filename,
#     #     "saved_path": file_path,
#     #     "content_type": file.content_type
#     # }


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8000)