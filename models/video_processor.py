import cv2
import supervision as sv
from datetime import datetime as dt
# from .video_processor import VideoProcessor
from .detections import PersonDetector
from .activity import ActivityClassifier
from .tracker import TrackManager
from database import store_event_into_db, store_track_into_db

class VideoProcessor:
    def __init__(self, input_path, output_path):
        self.input_path = input_path
        self.output_path = output_path

        self.detector = PersonDetector()
        self.classifier = ActivityClassifier()

    def process(self):
        cap = cv2.VideoCapture(self.input_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        out = cv2.VideoWriter(
            self.output_path,
            cv2.VideoWriter_fourcc(*"XVID"),
            fps,
            (width, height)
        )
        tracker_manager = TrackManager(fps)

        box_annotator = sv.BoxAnnotator()
        label_annotator = sv.LabelAnnotator()

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            detections = self.detector.detect(frame)

            if detections is None or len(detections)==0:
                out.write(frame)
                continue
            labels =[]
            frame_no = int(cap.get(cv2.CAP_PROP_POS_FRAMES))

            for i in range(len(detections)):
                track_id = int(detections.tracker_id[i])
                bbox = detections.xyxy[i]

                activity = self.classifier.classify(frame, bbox)
                labels.append(f"ID {track_id} | {activity}")


                tracker_manager.update(track_id, frame_no, activity)

                store_event_into_db(
                    timestamp=dt.now().strftime("%Y-%m-%d %H:%M:%S"),
                    track_id=track_id,
                    activity=activity,
                    created_at=dt.now().strftime("%Y-%m-%d %H:%M:%S")
                )

            frame = box_annotator.annotate(frame, detections)
            frame = label_annotator.annotate(frame, detections, labels)

            out.write(frame)

        cap.release()
        out.release()

        summary = tracker_manager.summarize()

        for track_id, data in summary.items():
            store_track_into_db(
                track_id=track_id,
                first_seen=data["first_time"],
                last_seen=data["last_time"],
                is_active=False,
                attributes=data
            )

        print("✅ Tracking complete.")