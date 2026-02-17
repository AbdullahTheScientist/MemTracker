import os
import cv2
import torch
import numpy as np
import datetime
from datetime import datetime as dt
from ultralytics import YOLO
import supervision as sv
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
from database import store_event_into_db, store_track_into_db

# ==============================
# Paths
# ==============================
input_video = "uploads/input_video.mp4"
output_video = "output_tracked.avi"

prompts = [
    "The person is walking",
    "The person is standing",
    "The person placed the laptop down",
    "The person picked the laptop",
    "The man is holding a laptop"
]

if not os.path.exists(input_video):
    print("❌ Input video not found")
    exit()


def detect_and_track(input_video, output_video):

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    # ==============================
    # Load Models
    # ==============================
    model = YOLO("yolov8n.pt")
    clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
    clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

    # ==============================
    # Open Video
    # ==============================
    cap = cv2.VideoCapture(input_video)

    if not cap.isOpened():
        print("❌ Could not open video")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        fps = 25

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

    # ==============================
    # Annotators
    # ==============================
    box_annotator = sv.BoxAnnotator()
    label_annotator = sv.LabelAnnotator()

    # ==============================
    # Track dictionary
    # ==============================
    track_times = {}

    # ==============================
    # Process Frames
    # ==============================
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            conf=0.5,
            verbose=False
        )

        result = results[0]
        detections = sv.Detections.from_ultralytics(result)

        if detections.tracker_id is None:
            out.write(frame)
            continue

        # Keep only PERSON class (COCO class 0)
        mask = detections.class_id == 0
        detections = detections[mask]

        if len(detections) == 0:
            out.write(frame)
            continue

        labels = []

        for i in range(len(detections)):

            track_id = int(detections.tracker_id[i])

            x1, y1, x2, y2 = detections.xyxy[i].astype(int)
            person_crop = frame[y1:y2, x1:x2]

            if person_crop.size == 0:
                labels.append("Unknown")
                continue

            # -----------------------------
            # CLIP Activity Classification
            # -----------------------------
            person_crop_pil = Image.fromarray(
                cv2.cvtColor(person_crop, cv2.COLOR_BGR2RGB)
            )

            inputs = clip_processor(
                text=prompts,
                images=person_crop_pil,
                return_tensors="pt",
                padding=True
            ).to(device)

            with torch.no_grad():
                outputs = clip_model(**inputs)
                probs = outputs.logits_per_image.softmax(dim=1).cpu().numpy()[0]

            activity = prompts[np.argmax(probs)]
            labels.append(activity)

            # -----------------------------
            # Frame Time Calculation
            # -----------------------------
            track_id = int(detections.tracker_id[i])

            frame_no = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            time_sec = frame_no / fps

            # If first time seeing this track
            if track_id not in track_times:
                track_times[track_id] = {
                    "first_seen_frame": frame_no,
                    "last_seen_frame": frame_no,
                    "first_activity": activity,
                    "last_activity": activity
                }
            else:
                track_times[track_id]["last_seen_frame"] = frame_no
                track_times[track_id]["last_activity"] = activity


            # -----------------------------
            # Store Event
            # -----------------------------
            store_event_into_db(
                timestamp=dt.now().strftime("%Y-%m-%d %H:%M:%S"),
                track_id=track_id,
                activity=activity,
                created_at=dt.now().strftime("%Y-%m-%d %H:%M:%S")
            )

        # -----------------------------
        # Draw Boxes & Labels
        # -----------------------------
        frame = box_annotator.annotate(
            scene=frame,
            detections=detections
        )

        display_labels = [
            f"ID {int(detections.tracker_id[i])} | {labels[i]}"
            for i in range(len(detections))
        ]

        frame = label_annotator.annotate(
            scene=frame,
            detections=detections,
            labels=display_labels
        )

        out.write(frame)

    # ==============================
    # After Video Ends
    # ==============================
    cap.release()
    out.release()

    print("\n📊 Person Appearance Summary:\n")

    print("\n📊 Person Appearance Summary:\n")

    for track_id, data in track_times.items():

        first_sec = data["first_seen_frame"] / fps
        last_sec = data["last_seen_frame"] / fps
        duration = last_sec - first_sec

        first_time = str(datetime.timedelta(seconds=int(first_sec)))
        last_time = str(datetime.timedelta(seconds=int(last_sec)))

        first_activity = data["first_activity"]
        last_activity = data["last_activity"]

        print(f"Person ID: {track_id}")
        print(f"   First Seen: {first_time}")
        print(f"   First Activity: {first_activity}")
        print(f"   Last Seen: {last_time}")
        print(f"   Last Activity: {last_activity}")
        print(f"   Duration: {round(duration,2)} sec\n")

        # Store into DB
        store_track_into_db(
            track_id=track_id,
            first_seen=first_time,
            last_seen=last_time,
            is_active=False,
            attributes={
                "duration_sec": round(duration, 2),
                "first_activity": first_activity,
                "last_activity": last_activity
            }
        )


    print("✅ Tracking complete.")
    print("📁 Output saved at:", output_video)


if __name__ == "__main__":
    detect_and_track(input_video, output_video)
