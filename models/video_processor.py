import cv2
import threading
import supervision as sv
from datetime import datetime as dt

from .detections import PersonDetector
from .activity import ActivityClassifier
from .tracker import TrackManager
from database import store_event_into_db, create_db


# ──────────────────────────────────────────────────────────────────────────────
# RTSP live-stream processor (existing)
# ──────────────────────────────────────────────────────────────────────────────

class RTSPVideoProcessor:
    def __init__(self, rtsp_url: str):
        self.rtsp_url = rtsp_url

        self.detector = PersonDetector()
        self.classifier = ActivityClassifier()

        self.running = False
        self.frames_processed = 0
        self._stop_event = threading.Event()
        self._tracker_manager: TrackManager | None = None

        # Latest annotated JPEG bytes — read by the MJPEG endpoint
        self.latest_frame_bytes: bytes | None = None
        self._frame_lock = threading.Lock()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def stop(self):
        self._stop_event.set()
        self.running = False

    def get_summary(self) -> dict:
        if self._tracker_manager is None:
            return {}
        return self._tracker_manager.summarize()

    def get_latest_frame_bytes(self) -> bytes | None:
        with self._frame_lock:
            return self.latest_frame_bytes

    # ------------------------------------------------------------------ #
    # Main loop
    # ------------------------------------------------------------------ #

    def process(self):
        cap = self._open_stream()
        if cap is None:
            return

        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        self._tracker_manager = TrackManager(fps)

        box_annotator = sv.BoxAnnotator()
        label_annotator = sv.LabelAnnotator()

        self.running = True
        self._stop_event.clear()
        print(f"▶  RTSP stream started: {self.rtsp_url}  (FPS={fps})")

        try:
            while not self._stop_event.is_set():
                ret, frame = cap.read()

                if not ret:
                    print("⚠  Stream interrupted — attempting reconnect …")
                    cap.release()
                    cap = self._open_stream(retries=5)
                    if cap is None:
                        print("✖  Could not reconnect. Stopping.")
                        break
                    continue

                self.frames_processed += 1
                frame_no = self.frames_processed

                detections = self.detector.detect(frame)

                if detections is not None and len(detections) > 0:
                    labels = []

                    for i in range(len(detections)):
                        track_id = int(detections.tracker_id[i])
                        bbox = detections.xyxy[i]

                        activity = self.classifier.classify(frame, bbox)
                        labels.append(f"ID {track_id} | {activity}")

                        self._tracker_manager.update(track_id, frame_no, activity)

                        # ✅ Fixed: store every event in DB
                        store_event_into_db(
                            track_id=track_id,
                            activity=activity,
                            timestamp=dt.now().strftime("%H:%M:%S"),
                        )

                    frame = box_annotator.annotate(frame, detections)
                    frame = label_annotator.annotate(frame, detections, labels)

                # Encode annotated frame as JPEG and store for MJPEG endpoint
                _, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                with self._frame_lock:
                    self.latest_frame_bytes = jpeg.tobytes()

        finally:
            cap.release()
            self.running = False
            print("✅  RTSP processing stopped.")

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _open_stream(self, retries: int = 3) -> cv2.VideoCapture | None:
        for attempt in range(1, retries + 1):
            cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            if cap.isOpened():
                return cap

            print(f"  Attempt {attempt}/{retries}: cannot open {self.rtsp_url}")
            cap.release()

        print(f"✖  Failed to open RTSP stream after {retries} attempts.")
        return None


# ──────────────────────────────────────────────────────────────────────────────
# NEW: File-based video processor (for uploaded videos)
# ──────────────────────────────────────────────────────────────────────────────

class FileVideoProcessor:
    """
    Process an uploaded video file frame-by-frame.

    Usage
    -----
    proc = FileVideoProcessor(video_path)
    proc.start()                        # runs in background thread
    while proc.running or proc.latest_frame_bytes:
        jpeg = proc.get_latest_frame_bytes()
        ...                             # serve via MJPEG
    summary = proc.get_summary()
    """

    def __init__(self, video_path: str, process_every_n: int = 3):
        self.video_path = video_path
        self.process_every_n = process_every_n   # skip frames for speed

        self.detector = PersonDetector()
        self.classifier = ActivityClassifier()

        self.running = False
        self.finished = False
        self.frames_processed = 0
        self._stop_event = threading.Event()
        self._tracker_manager: TrackManager | None = None

        self.latest_frame_bytes: bytes | None = None
        self._frame_lock = threading.Lock()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def start(self):
        """Launch processing in a background thread."""
        t = threading.Thread(target=self.process, daemon=True, name="file-processor")
        t.start()

    def stop(self):
        self._stop_event.set()

    def get_summary(self) -> dict:
        if self._tracker_manager is None:
            return {}
        return self._tracker_manager.summarize()

    def get_latest_frame_bytes(self) -> bytes | None:
        with self._frame_lock:
            return self.latest_frame_bytes

    # ------------------------------------------------------------------ #
    # Main processing loop
    # ------------------------------------------------------------------ #

    def process(self):
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            print(f"✖  Cannot open video file: {self.video_path}")
            self.finished = True
            return

        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        self._tracker_manager = TrackManager(fps)

        box_annotator = sv.BoxAnnotator()
        label_annotator = sv.LabelAnnotator()

        self.running = True
        self._stop_event.clear()
        print(f"▶  File video processing started: {self.video_path}  (FPS={fps})")

        frame_index = 0

        try:
            while not self._stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    break   # end of file

                frame_index += 1

                # Skip frames for performance (classify every N frames)
                if frame_index % self.process_every_n != 0:
                    _, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
                    with self._frame_lock:
                        self.latest_frame_bytes = jpeg.tobytes()
                    continue

                self.frames_processed += 1

                detections = self.detector.detect(frame)

                if detections is not None and len(detections) > 0:
                    labels = []

                    for i in range(len(detections)):
                        track_id = int(detections.tracker_id[i])
                        bbox = detections.xyxy[i]

                        activity = self.classifier.classify(frame, bbox)
                        labels.append(f"ID {track_id} | {activity}")

                        self._tracker_manager.update(track_id, frame_index, activity)

                        # ✅ Store every detection event in the database
                        store_event_into_db(
                            track_id=track_id,
                            activity=activity,
                            timestamp=dt.now().strftime("%H:%M:%S"),
                        )

                    frame = box_annotator.annotate(frame, detections)
                    frame = label_annotator.annotate(frame, detections, labels)

                _, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                with self._frame_lock:
                    self.latest_frame_bytes = jpeg.tobytes()

        finally:
            cap.release()
            self.running = False
            self.finished = True
            print("✅  File video processing finished.")