from fastapi import FastAPI
from fastapi import File, UploadFile
import os
from detections import detect_and_track
from ultralytics import YOLO
import shutil


app = FastAPI()

UPLOAD_FOLDER = "uploads"

# Create folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.post("/upload-video/")
async def upload_video(file: UploadFile = File(...)):
    
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    # Save file to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    detect_and_track(file_path, "output_tracked.avi")

    # return back back video file
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

    # return {
    #     "message": "Video uploaded successfully",
    #     "filename": file.filename,
    #     "saved_path": file_path,
    #     "content_type": file.content_type
    # }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)