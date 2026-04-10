<div align="center">

<a href="https://www.youtube.com/watch?v=O3zD5Zgin-Q" target="_blank">
  <img src="https://img.youtube.com/vi/O3zD5Zgin-Q/maxresdefault.jpg"
       alt="Watch MemTracker Demo"
       style="width:100%;max-width:720px;border-radius:12px;border:1px solid #30363d;display:block;margin:0 auto 24px;"/>
</a>

<img src="https://img.shields.io/badge/MemTracker-AI%20Surveillance-7F77DD?style=for-the-badge&logo=eye&logoColor=white" alt="MemTracker" height="32"/>

<h1>MemTracker</h1>

<p><em>Real-time AI-powered person tracking, activity recognition, and intelligent surveillance analysis</em></p>

<p>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/YOLOv8-Ultralytics-FF6B35?style=flat-square"/>
  <img src="https://img.shields.io/badge/CLIP-OpenAI-412991?style=flat-square"/>
  <img src="https://img.shields.io/badge/Groq-LLaMA%203.3-F55036?style=flat-square"/>
  <img src="https://img.shields.io/badge/RunPod-RTX%203090-7B2FBE?style=flat-square"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square"/>
</p>

</div>

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the App](#running-the-app)
- [API Reference](#api-reference)
- [AI Chat System](#ai-chat-system)
- [Deploying on RunPod](#deploying-on-runpod)
- [Database Schema](#database-schema)
- [Troubleshooting](#troubleshooting)

---

## Overview

<table>
<tr>
<td width="60%">

**MemTracker** is a full-stack AI surveillance system that:

- **Detects and tracks** every person in a video using YOLOv8 + ByteTrack
- **Classifies activities** in real-time using OpenAI CLIP (walking, standing, picking up objects, etc.)
- **Stores every event** chronologically in a SQLite database with timestamps
- **Streams annotated video** live over HTTP (MJPEG) — watch detections happen in real time
- **Answers natural language questions** about what happened using a 3-stage AI pipeline (SQL → DB → LLaMA 3.3)

You can point it at a **live RTSP camera stream** or **upload any video file**. Ask it anything: *"What was Person 2 doing at 10:04?"* or *"Did anyone pick up the laptop?"* and it gives you a precise, timestamped answer.

</td>
<td width="40%" align="center">

```
Video / RTSP
     │
     ▼
 YOLOv8 Detection
     │
     ▼
 ByteTrack ID Assignment
     │
     ▼
 CLIP Activity Classification
     │
     ▼
 SQLite Event Storage
     │
     ▼
 LLaMA 3.3 Q&A
```

</td>
</tr>
</table>

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         MemTracker System                           │
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │  Video Input  │    │  AI Models   │    │    FastAPI Server    │  │
│  │              │    │              │    │                      │  │
│  │  • RTSP Live  │───▶│  YOLOv8n    │    │  POST /stream/start  │  │
│  │  • File Upload│    │  ByteTrack  │    │  POST /video/upload  │  │
│  │  (.mp4/.avi/ │    │  CLIP ViT   │    │  GET  /stream/feed   │  │
│  │   .mov/.mkv) │    │  B/32       │    │  POST /ai/chat       │  │
│  └──────────────┘    └──────┬───────┘    │  GET  /events        │  │
│                             │            └──────────────────────┘  │
│                             ▼                                       │
│                    ┌──────────────┐    ┌──────────────────────┐    │
│                    │  SQLite DB   │    │   AI Chat Pipeline   │    │
│                    │              │    │                      │    │
│                    │  events      │───▶│  1. Question → SQL   │    │
│                    │  • track_id  │    │  2. SQL → DB rows    │    │
│                    │  • activity  │    │  3. Compress context │    │
│                    │  • timestamp │    │  4. LLaMA 3.3 answer │    │
│                    └──────────────┘    └──────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Features

<table>
<tr>
<th>Feature</th>
<th>Details</th>
<th>Technology</th>
</tr>
<tr>
<td>🎯 <strong>Person Detection</strong></td>
<td>Detects every person in each frame with bounding boxes</td>
<td>YOLOv8n (Ultralytics)</td>
</tr>
<tr>
<td>🔢 <strong>Person Tracking</strong></td>
<td>Assigns consistent IDs across frames so Person 1 stays Person 1</td>
<td>ByteTrack algorithm</td>
</tr>
<tr>
<td>🏃 <strong>Activity Classification</strong></td>
<td>Classifies what each person is doing every frame</td>
<td>OpenAI CLIP ViT-B/32</td>
</tr>
<tr>
<td>📹 <strong>Live RTSP Stream</strong></td>
<td>Connect any IP camera or RTSP source and process live</td>
<td>OpenCV + FFMPEG</td>
</tr>
<tr>
<td>📁 <strong>Video File Upload</strong></td>
<td>Upload MP4/AVI/MOV/MKV/WebM, process and stream results live</td>
<td>FastAPI async upload</td>
</tr>
<tr>
<td>📺 <strong>Live Annotated Feed</strong></td>
<td>Watch the annotated video with bounding boxes and labels in real-time</td>
<td>MJPEG streaming</td>
</tr>
<tr>
<td>🗄️ <strong>Event Database</strong></td>
<td>Every detection stored with person ID, activity, and exact timestamp</td>
<td>SQLite</td>
</tr>
<tr>
<td>🧠 <strong>AI Q&A</strong></td>
<td>Ask natural language questions, get analyst-grade answers with timestamps</td>
<td>Groq + LLaMA 3.3 70B</td>
</tr>
<tr>
<td>⚡ <strong>GPU Accelerated</strong></td>
<td>CUDA acceleration for both YOLO and CLIP on RTX 3090</td>
<td>PyTorch CUDA</td>
</tr>
</table>

---

## Project Structure

```
memtracker/
│
├── app.py                  # FastAPI server — all HTTP endpoints
├── ai_helper.py            # 3-stage AI pipeline (SQL → DB → LLaMA answer)
├── config.py               # Global settings (model names, paths, prompts)
│
├── database/
│   ├── __init__.py         # Exports: store_event_into_db, create_db, get_all_events
│   └── database.py         # SQLite helpers — create tables, insert, fetch
│
├── models/
│   ├── __init__.py         # Exports: ActivityClassifier, PersonDetector, processors
│   ├── activity.py         # CLIP-based activity classifier
│   ├── detections.py       # YOLOv8 person detector wrapper
│   ├── tracker.py          # TrackManager — per-person timeline builder
│   └── video_processor.py  # RTSPVideoProcessor + FileVideoProcessor
│
├── db.py                   # Standalone CLI tool to inspect the database
├── index.html              # Frontend UI served at GET /
│
├── input/                  # (optional) Place input videos here
├── output/                 # (optional) Processed video output
└── uploads/                # Auto-created — stores uploaded video files
```

---

## How It Works

### Stage 1 — Detection & Tracking

Each video frame is passed through **YOLOv8n** with `persist=True` and the **ByteTrack** tracker. This gives every detected person a stable `track_id` that stays consistent across frames — so if Person 3 walks out of frame and back in, they keep the same ID.

```python
# detections.py — simplified
results = self.model.track(frame, persist=True, tracker="bytetrack.yaml", conf=0.5)
detections = sv.Detections.from_ultralytics(result)
person_detections = detections[detections.class_id == 0]  # class 0 = person
```

### Stage 2 — Activity Classification

For each detected person, their bounding box is cropped and passed to **OpenAI CLIP** (`ViT-B/32`). CLIP compares the crop against all activity prompts defined in `config.py` and picks the highest probability match.

```python
# activity.py — simplified
inputs = self.processor(text=PROMPTS, images=crop_pil, return_tensors='pt', padding=True)
outputs = self.model(**inputs)
probs = outputs.logits_per_image.softmax(dim=1).cpu().numpy()[0]
activity = PROMPTS[np.argmax(probs)]
```

**Default activity prompts** (configurable in `config.py`):

| Prompt | Description |
|--------|-------------|
| `"The person is walking"` | Person in motion |
| `"The person is standing"` | Stationary person |
| `"The person placed the laptop down"` | Object interaction |
| `"The person picked the laptop"` | Object interaction |
| `"The man is holding a laptop"` | Object hold |

> You can add any prompt to `config.py` — CLIP understands natural language descriptions.

### Stage 3 — Event Storage

Every detected activity change is written to SQLite immediately:

```python
store_event_into_db(
    track_id=track_id,
    activity=activity,
    timestamp=dt.now().strftime("%H:%M:%S")
)
```

### Stage 4 — AI Q&A Pipeline

When you ask a question, `ai_helper.py` runs a 3-step pipeline:

```
Question: "What was Person 2 doing between 10:02 and 10:05?"
    │
    ▼
Step 1 — LLaMA generates SQL
    │     SELECT * FROM events WHERE track_id = 2
    │     AND timestamp BETWEEN '10:02:00' AND '10:05:00'
    │     ORDER BY timestamp ASC
    ▼
Step 2 — Execute SQL on SQLite → raw rows
    │
    ▼
Step 3 — Compress rows into segments
    │     1,600 rows → ~20 activity-change lines (never hits token limits)
    ▼
Step 4 — LLaMA generates analyst answer
    │     "Person 2 was standing from 10:02:00 to 10:03:14,
    │      then picked up the laptop at 10:03:15 and was
    │      observed holding it until 10:04:58."
```

---

## Installation

### Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.10 or higher |
| CUDA | 11.8+ (for GPU) |
| pip | Latest |
| Groq API key | Free at [console.groq.com](https://console.groq.com) |

### 1. Clone the repository

```bash
git clone https://github.com/yourname/memtracker.git
cd memtracker
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Linux / Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
# Core API server
pip install fastapi uvicorn python-multipart

# AI / ML models
pip install ultralytics          # YOLOv8
pip install supervision          # ByteTrack + annotation
pip install transformers         # CLIP
pip install torch torchvision    # PyTorch (CUDA build recommended)
pip install opencv-python-headless

# AI chat
pip install groq python-dotenv
```

> **GPU note:** For CUDA-accelerated PyTorch, install from [pytorch.org](https://pytorch.org) with your specific CUDA version:
> ```bash
> pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
> ```

### 4. Create environment file

```bash
cp .env.example .env
# Then edit .env with your keys
```

Or create `.env` manually:

```env
GROQ_API_KEY=your_groq_api_key_here
RTSP_URL=rtsp://192.168.1.100:554/stream    # optional — only for live camera
```

### 5. Create required directories

```bash
mkdir -p uploads output input
```

### 6. Fix the import (important)

In `app.py` line 16, change:
```python
# Wrong — "models" package needs the submodule path
from models import RTSPVideoProcessor, FileVideoProcessor

# Correct
from models.video_processor import RTSPVideoProcessor, FileVideoProcessor
```

---

## Configuration

All model settings and activity prompts are controlled in `config.py`:

```python
# config.py

INPUT_VIDEO  = "input/input_video.mp4"   # default input path (not used by API)
OUTPUT_VIDEO = "output/output_tracked.avi"
DEVICE       = "cpu"                      # change to "cuda" for GPU

YOLO_MODEL      = "yolov8n.pt"           # nano=fast, yolov8s/m/l=more accurate
CLIP_MODEL_NAME = "openai/clip-vit-base-patch32"

PERSON_CLASS_ID = 0                      # COCO class 0 = person

# ── Customize these prompts to match your surveillance scenario ──
PROMPTS = [
    "The person is walking",
    "The person is standing",
    "The person placed the laptop down",
    "The person picked the laptop",
    "The man is holding a laptop"
]
```

### Customizing Activity Prompts

CLIP understands any natural language description. Customize for your use case:

<table>
<tr><th>Use Case</th><th>Example Prompts</th></tr>
<tr>
<td>Retail / Shop</td>
<td><code>"The person is browsing shelves"</code>, <code>"The person is at the checkout"</code>, <code>"The person is shoplifting"</code></td>
</tr>
<tr>
<td>Office Security</td>
<td><code>"The person is at their desk"</code>, <code>"The person is using a computer"</code>, <code>"The person entered a restricted area"</code></td>
</tr>
<tr>
<td>Warehouse</td>
<td><code>"The person is carrying a box"</code>, <code>"The person is operating a forklift"</code>, <code>"The person fell down"</code></td>
</tr>
</table>

---

## Running the App

### Start the server

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser at `http://localhost:8000` to see the frontend UI.

Interactive API docs are at `http://localhost:8000/docs`.

### Inspect the database (CLI)

```bash
python db.py
```

This prints a formatted table of all events directly in your terminal.

---

## API Reference

### 🔴 RTSP Live Stream

<table>
<tr><th>Method</th><th>Endpoint</th><th>Description</th></tr>
<tr>
<td><img src="https://img.shields.io/badge/POST-009688?style=flat-square" alt="POST"/></td>
<td><code>/stream/start</code></td>
<td>Start processing the RTSP camera stream</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/POST-009688?style=flat-square" alt="POST"/></td>
<td><code>/stream/stop</code></td>
<td>Stop the RTSP stream processor</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/GET-0277BD?style=flat-square" alt="GET"/></td>
<td><code>/stream/status</code></td>
<td>Check if stream is running, frames processed</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/GET-0277BD?style=flat-square" alt="GET"/></td>
<td><code>/stream/feed</code></td>
<td>Live MJPEG video feed — open in browser or <code>&lt;img&gt;</code> tag</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/GET-0277BD?style=flat-square" alt="GET"/></td>
<td><code>/stream/summary</code></td>
<td>Per-person tracking summary for current session</td>
</tr>
</table>

**Example — start stream:**
```bash
curl -X POST http://localhost:8000/stream/start
```
```json
{
  "status": "started",
  "rtsp_url": "rtsp://192.168.1.100:554/stream"
}
```

**Example — stream status:**
```bash
curl http://localhost:8000/stream/status
```
```json
{
  "status": "running",
  "rtsp_url": "rtsp://192.168.1.100:554/stream",
  "frames_processed": 1482
}
```

---

### 📁 Video File Upload

<table>
<tr><th>Method</th><th>Endpoint</th><th>Description</th></tr>
<tr>
<td><img src="https://img.shields.io/badge/POST-009688?style=flat-square" alt="POST"/></td>
<td><code>/video/upload</code></td>
<td>Upload a video file — returns a <code>job_id</code> immediately</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/GET-0277BD?style=flat-square" alt="GET"/></td>
<td><code>/video/{job_id}/feed</code></td>
<td>Live MJPEG feed of the video being processed</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/GET-0277BD?style=flat-square" alt="GET"/></td>
<td><code>/video/{job_id}/status</code></td>
<td>Check processing progress (running / finished / frames done)</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/GET-0277BD?style=flat-square" alt="GET"/></td>
<td><code>/video/{job_id}/summary</code></td>
<td>Get tracking summary after processing completes</td>
</tr>
</table>

**Supported formats:** `.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`

**Example — upload a video:**
```bash
curl -X POST http://localhost:8000/video/upload \
  -F "file=@/path/to/video.mp4"
```
```json
{
  "status": "processing_started",
  "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "filename": "video.mp4",
  "live_feed_url": "/video/f47ac10b-58cc-4372-a567-0e02b2c3d479/feed",
  "status_url":    "/video/f47ac10b-58cc-4372-a567-0e02b2c3d479/status",
  "summary_url":   "/video/f47ac10b-58cc-4372-a567-0e02b2c3d479/summary"
}
```

**Example — check status:**
```bash
curl http://localhost:8000/video/f47ac10b.../status
```
```json
{
  "job_id": "f47ac10b-...",
  "running": true,
  "finished": false,
  "frames_processed": 342
}
```

**Example — get summary after processing:**
```bash
curl http://localhost:8000/video/f47ac10b.../summary
```
```json
{
  "job_id": "f47ac10b-...",
  "finished": true,
  "summary": {
    "1": {
      "first_time": "0:00:02",
      "last_time": "0:01:14",
      "duration": 72.4,
      "first_activity": "The person is walking",
      "last_activity": "The person is standing"
    }
  }
}
```

**Watch the live feed while processing:**
```html
<!-- Open this in any browser while the video processes -->
<img src="http://localhost:8000/video/YOUR_JOB_ID/feed" />
```

---

### 🗄️ Events Database

<table>
<tr><th>Method</th><th>Endpoint</th><th>Params</th><th>Description</th></tr>
<tr>
<td><img src="https://img.shields.io/badge/GET-0277BD?style=flat-square" alt="GET"/></td>
<td><code>/events</code></td>
<td><code>?limit=100</code></td>
<td>Return latest tracking events from the database</td>
</tr>
</table>

```bash
curl http://localhost:8000/events?limit=50
```
```json
{
  "count": 50,
  "events": [
    {
      "id": 1,
      "track_id": 1,
      "activity": "The person is walking",
      "timestamp": "10:01:03"
    },
    {
      "id": 2,
      "track_id": 1,
      "activity": "The person picked the laptop",
      "timestamp": "10:01:47"
    }
  ]
}
```

---

### 🧠 AI Chat & Analysis

<table>
<tr><th>Method</th><th>Endpoint</th><th>Description</th></tr>
<tr>
<td><img src="https://img.shields.io/badge/GET-0277BD?style=flat-square" alt="GET"/></td>
<td><code>/ai/summary</code></td>
<td>Auto-generate a full surveillance session report</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/POST-009688?style=flat-square" alt="POST"/></td>
<td><code>/ai/chat</code></td>
<td>Ask any natural language question about the footage</td>
</tr>
</table>

**Example — AI chat:**
```bash
curl -X POST http://localhost:8000/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Who picked up the laptop and when?"}'
```
```json
{
  "status": "success",
  "question": "Who picked up the laptop and when?",
  "answer": "Person 1 picked up the laptop at 10:01:47. They had been standing stationary from 10:01:03 before the action. Person 3 was also observed picking up the laptop at 10:08:22, after walking across the room from 10:07:55."
}
```

**Example questions you can ask:**

| Question | What it answers |
|----------|----------------|
| `"What happened?"` | Full chronological narrative of the entire session |
| `"How many people were tracked?"` | Total unique persons detected |
| `"What was Person 2 doing at 10:05?"` | Specific person + time lookup |
| `"Did anyone pick up the laptop?"` | Activity-specific search |
| `"How long was Person 1 in the frame?"` | Duration calculation |
| `"Who was walking the most?"` | Comparative activity analysis |
| `"What happened between 10:00 and 10:10?"` | Time-range query |
| `"When did Person 3 first appear?"` | First detection lookup |

---

## AI Chat System

The AI pipeline in `ai_helper.py` has three components working together:

### 1. SQL Generator

A LLaMA 3.3 70B call that converts your natural language question into a precise SQLite query:

```
"Did anyone pick up the laptop?"
        ↓
SELECT * FROM events
WHERE activity LIKE '%laptop%'
ORDER BY timestamp ASC
```

### 2. Context Compressor

The most important part — instead of sending thousands of raw database rows to the LLM (which would exceed token limits and cost more), it **compresses consecutive identical activities into segments**:

```
Before compression (1,610 raw rows → 72,907 chars — would crash):
  10:01:00 | Person 1 | The person is walking
  10:01:00 | Person 1 | The person is walking
  10:01:01 | Person 1 | The person is walking
  ... (750 more identical rows)

After compression (20 segments → ~3,000 chars — fits perfectly):
  Person 1 — [10:01:00 → 10:01:30] 30s | 750 frames | The person is walking
  Person 1 — [10:01:31 → 10:02:05] 34s | 850 frames | The person is standing
  Person 1 — [10:02:06 → 10:02:06]  0s |   1 frame  | The person picked the laptop
```

This means **no matter how long your video is** — 5 minutes or 5 hours — the context sent to the LLM stays small and accurate.

### 3. Analyst Answer Generator

LLaMA 3.3 70B with a security analyst persona that reads the compressed timeline and generates a precise, timestamped, professional answer.

```
Temperature: 0.1  (near-zero = factual, not creative)
Max tokens:  900  (enough for detailed incident reports)
```

---

## Database Schema

```sql
-- Main events table — one row per detection
CREATE TABLE events (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id  INTEGER,              -- consistent person ID (ByteTrack)
    activity  TEXT NOT NULL,        -- CLIP classification result
    timestamp TEXT                  -- HH:MM:SS when detected
);

-- Chat history (stored for future conversation memory)
CREATE TABLE chat_history (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    role             TEXT NOT NULL,         -- 'user' or 'assistant'
    message          TEXT NOT NULL,
    timestamp        DATETIME DEFAULT CURRENT_TIMESTAMP,
    event_references TEXT                   -- linked event IDs
);
```

**Inspect the database from CLI:**

```bash
python db.py
```

Output example:
```
📦 Database: tracking.db
📋 Tables found: events, chat_history

============================================================
  TABLE: events
============================================================
  Total records: 1610

id  | track_id | activity                        | timestamp
----+----------+---------------------------------+----------
1   | 1        | The person is walking           | 10:01:03
2   | 1        | The person is walking           | 10:01:04
3   | 2        | The person is standing          | 10:01:05
4   | 1        | The person picked the laptop    | 10:01:47
...
```

---

## Deploying on RunPod

### Step 1 — Create your pod

Go to [runpod.io](https://runpod.io) → GPU Cloud → Deploy a pod with:

| Setting | Value |
|---------|-------|
| GPU | RTX 3090 (24 GB VRAM) |
| Template | RunPod PyTorch 2.x |
| Container disk | 40 GB |
| Volume disk | 20 GB at `/workspace` |
| Expose HTTP port | `8000` |

### Step 2 — SSH into the pod

```bash
ssh root@ssh.runpod.io -p YOUR_PORT -i ~/.ssh/id_rsa
```

### Step 3 — Upload your project

From your local machine:
```bash
rsync -avz --progress ./memtracker/ \
  root@ssh.runpod.io:/workspace/memtracker/ \
  -e "ssh -p YOUR_PORT"
```

Or clone from GitHub:
```bash
cd /workspace
git clone https://github.com/yourname/memtracker.git
cd memtracker
```

### Step 4 — Install dependencies

```bash
cd /workspace/memtracker

pip install fastapi uvicorn python-multipart
pip install groq python-dotenv
pip install ultralytics supervision
pip install transformers accelerate
pip install opencv-python-headless
# torch is pre-installed in the PyTorch template — do not reinstall
```

### Step 5 — Set environment variables

```bash
cat > /workspace/memtracker/.env << 'EOF'
GROQ_API_KEY=your_groq_api_key_here
RTSP_URL=rtsp://your_camera_ip/stream
EOF
```

### Step 6 — Create directories

```bash
mkdir -p /workspace/memtracker/uploads \
         /workspace/memtracker/output \
         /workspace/memtracker/input
```

### Step 7 — Start with screen (keeps running after SSH disconnect)

```bash
cd /workspace/memtracker
screen -S memtracker
uvicorn app:app --host 0.0.0.0 --port 8000

# Detach:   Ctrl+A  then  D
# Reattach: screen -r memtracker
```

### Step 8 — Access your deployment

Your public URL from RunPod:
```
https://YOUR_POD_ID-8000.proxy.runpod.net/          ← Frontend UI
https://YOUR_POD_ID-8000.proxy.runpod.net/docs      ← API Explorer
https://YOUR_POD_ID-8000.proxy.runpod.net/events    ← Live events
```

### Auto-restart on pod reboot

In RunPod pod settings → Docker Command, set:
```bash
cd /workspace/memtracker && uvicorn app:app --host 0.0.0.0 --port 8000
```

> **Cost tip:** An RTX 3090 on RunPod costs ~$0.44/hr. Use **Stop** (not Delete) when not in use — your `/workspace` volume is preserved and not charged at GPU rate.

---

## Troubleshooting

<table>
<tr>
<th>Problem</th>
<th>Cause</th>
<th>Fix</th>
</tr>
<tr>
<td><code>POST /stream/start</code> returns 500</td>
<td>Wrong import in <code>app.py</code></td>
<td>Change line 16 to <code>from models.video_processor import ...</code></td>
</tr>
<tr>
<td><code>POST /ai/chat</code> returns 500</td>
<td>Context too large for Groq API</td>
<td>Use the updated <code>ai_helper.py</code> with context compression</td>
</tr>
<tr>
<td>RTSP stream won't connect</td>
<td>Wrong URL or camera offline</td>
<td>Test URL with <code>ffplay rtsp://your_url</code> first</td>
</tr>
<tr>
<td>YOLO model not found</td>
<td><code>yolov8n.pt</code> not downloaded yet</td>
<td>Runs once automatically on first use — needs internet access</td>
</tr>
<tr>
<td>CLIP slow on CPU</td>
<td><code>DEVICE = "cpu"</code> in config</td>
<td>Set <code>DEVICE = "cuda"</code> if you have a GPU</td>
</tr>
<tr>
<td>Database not found</td>
<td>App not started yet</td>
<td><code>create_db()</code> runs on startup — just start the server once</td>
</tr>
<tr>
<td>Video upload fails with 400</td>
<td>Unsupported file format</td>
<td>Use <code>.mp4</code>, <code>.avi</code>, <code>.mov</code>, <code>.mkv</code>, or <code>.webm</code></td>
</tr>
<tr>
<td><code>tracker_id is None</code> warning</td>
<td>No persons detected in frame</td>
<td>Normal — means frame had no people. Check confidence threshold in <code>detections.py</code></td>
</tr>
<tr>
<td>Screen session lost after restart</td>
<td>Pod container restarted</td>
<td>SSH back in, re-run <code>screen -S memtracker</code> + <code>uvicorn</code></td>
</tr>
</table>

---

## Performance Notes

| Hardware | Detection FPS | CLIP FPS | Notes |
|----------|--------------|----------|-------|
| RTX 3090 | ~60 fps | ~30 fps | CUDA, production |
| RTX 3080 | ~50 fps | ~25 fps | CUDA |
| CPU only | ~3-5 fps | ~2-3 fps | Not recommended for live |

The `FileVideoProcessor` processes every 3rd frame by default (`process_every_n=3`) to balance speed and accuracy. Adjust in `app.py`:

```python
processor = FileVideoProcessor(video_path=save_path, process_every_n=3)
#                                                           ↑ lower = more accurate, slower
#                                                             higher = faster, less accurate
```

---

<div align="center">

<br/>

Built with YOLOv8 · CLIP · LLaMA 3.3 · FastAPI · RunPod

<br/>

<img src="https://img.shields.io/badge/Made%20with-Python-3776AB?style=flat-square&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/Powered%20by-Groq-F55036?style=flat-square"/>
<img src="https://img.shields.io/badge/GPU-RTX%203090-76B900?style=flat-square"/>

<br/><br/>

</div>
