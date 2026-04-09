from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse
from pydantic import BaseModel
import os
import shutil
from uuid import uuid4
import threading
import time

from ai_helper import answer_question_with_groq
from models.video_processor import RTSPVideoProcessor, FileVideoProcessor
from models.detections import PersonDetector
from models.activity import ActivityClassifier
from database import create_db, get_all_events

# ─────────────────────────────────────────────
# Startup — DB + pre-load models ONCE
# ─────────────────────────────────────────────
create_db()

print("⏳ Loading YOLOv8 model...")
shared_detector = PersonDetector()
print("✅ YOLOv8 ready.")

print("⏳ Loading CLIP model (downloading if first run, ~600 MB)...")
shared_classifier = ActivityClassifier()
print("✅ CLIP ready.")

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
RTSP_URL   = os.environ.get("RTSP_URL", "rtsp://localhost:8554/mystream")
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ─────────────────────────────────────────────
# Global state — RTSP stream
# ─────────────────────────────────────────────
stream_processor: RTSPVideoProcessor | None = None
stream_thread:    threading.Thread    | None = None
stream_lock = threading.Lock()

# ─────────────────────────────────────────────
# Global state — file upload jobs
# ─────────────────────────────────────────────
file_jobs: dict[str, FileVideoProcessor] = {}
file_jobs_lock = threading.Lock()

# ─────────────────────────────────────────────
# Request models
# ─────────────────────────────────────────────
class ChatRequest(BaseModel):
    question: str

# ─────────────────────────────────────────────
# App
# ─────────────────────────────────────────────
app = FastAPI(title="MemTracker API")


@app.get("/", response_class=HTMLResponse)
def frontend():
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        return f.read()


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — RTSP live stream
# ══════════════════════════════════════════════════════════════════════════════

def _run_stream(processor: RTSPVideoProcessor):
    processor.process()


@app.post("/stream/start")
def start_stream():
    global stream_processor, stream_thread
    with stream_lock:
        if stream_processor and stream_processor.running:
            return {"status": "already_running", "rtsp_url": RTSP_URL}

        # Pass the already-loaded shared models — no reload
        stream_processor = RTSPVideoProcessor(
            rtsp_url=RTSP_URL,
            detector=shared_detector,
            classifier=shared_classifier,
        )
        stream_thread = threading.Thread(
            target=_run_stream,
            args=(stream_processor,),
            daemon=True,
            name="rtsp-processor",
        )
        stream_thread.start()

    return {"status": "started", "rtsp_url": RTSP_URL}


@app.post("/stream/stop")
def stop_stream():
    global stream_processor
    with stream_lock:
        if not stream_processor or not stream_processor.running:
            raise HTTPException(status_code=400, detail="Stream is not running")
        stream_processor.stop()
    return {"status": "stopped"}


@app.get("/stream/status")
def stream_status():
    with stream_lock:
        if stream_processor is None:
            return {"status": "idle"}
        return {
            "status":           "running" if stream_processor.running else "stopped",
            "rtsp_url":         RTSP_URL,
            "frames_processed": stream_processor.frames_processed,
        }


@app.get("/stream/summary")
def stream_summary():
    with stream_lock:
        if stream_processor is None:
            raise HTTPException(status_code=400, detail="No stream has been started yet")
        return {"status": "success", "summary": stream_processor.get_summary()}


def _mjpeg_gen_rtsp():
    while True:
        with stream_lock:
            processor = stream_processor
        if processor is None or not processor.running:
            time.sleep(0.1)
            continue
        frame_bytes = processor.get_latest_frame_bytes()
        if frame_bytes is None:
            time.sleep(0.03)
            continue
        yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        time.sleep(0.03)


@app.get("/stream/feed")
def stream_feed():
    return StreamingResponse(
        _mjpeg_gen_rtsp(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Upload a video file
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/video/upload")
async def upload_video(file: UploadFile = File(...)):
    allowed = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
    ext = os.path.splitext(file.filename or "")[-1].lower()
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {allowed}",
        )

    job_id    = str(uuid4())
    save_path = os.path.join(UPLOAD_DIR, f"{job_id}{ext}")

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Pass the already-loaded shared models — no reload, no 600 MB download
    processor = FileVideoProcessor(
        video_path=save_path,
        detector=shared_detector,
        classifier=shared_classifier,
        process_every_n=3,
    )
    processor.start()

    with file_jobs_lock:
        file_jobs[job_id] = processor

    return {
        "status":        "processing_started",
        "job_id":        job_id,
        "filename":      file.filename,
        "live_feed_url": f"/video/{job_id}/feed",
        "status_url":    f"/video/{job_id}/status",
        "summary_url":   f"/video/{job_id}/summary",
    }


def _mjpeg_gen_file(job_id: str):
    while True:
        with file_jobs_lock:
            processor = file_jobs.get(job_id)
        if processor is None:
            break
        frame_bytes = processor.get_latest_frame_bytes()
        if frame_bytes:
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        if processor.finished and frame_bytes is None:
            break
        time.sleep(0.04)


@app.get("/video/{job_id}/feed")
def video_feed(job_id: str):
    with file_jobs_lock:
        if job_id not in file_jobs:
            raise HTTPException(status_code=404, detail="Job not found")
    return StreamingResponse(
        _mjpeg_gen_file(job_id),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.get("/video/{job_id}/status")
def video_status(job_id: str):
    with file_jobs_lock:
        processor = file_jobs.get(job_id)
    if processor is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id":           job_id,
        "running":          processor.running,
        "finished":         processor.finished,
        "frames_processed": processor.frames_processed,
    }


@app.get("/video/{job_id}/summary")
def video_summary(job_id: str):
    with file_jobs_lock:
        processor = file_jobs.get(job_id)
    if processor is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id":   job_id,
        "finished": processor.finished,
        "summary":  processor.get_summary(),
    }


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Database
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/events")
def list_events(limit: int = 100):
    events = get_all_events()
    return {"count": len(events), "events": events[:limit]}


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — AI endpoints
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/ai/summary")
async def get_ai_summary():
    try:
        summary = answer_question_with_groq(
            "Give me a full summary of all persons tracked, "
            "their first and last activities, and how long they were present."
        )
        return {"status": "success", "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai/chat")
async def chat(request: ChatRequest):
    try:
        answer = answer_question_with_groq(request.question)
        return {"status": "success", "question": request.question, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)






