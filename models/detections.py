from ultralytics import YOLO
import cv2
import supervision as sv
from  config import YOLO_MODEL, PERSON_CLASS_ID


class PersonDetector:
    def __init__(self):
        self.model = YOLO(YOLO_MODEL)

    def detect(self, frame):
        results = self.model.track(
            frame,
            persist = True,
            tracker = "bytetrack.yaml",
            conf = 0.5,
            verbose = True
        )

        result = results[0]
        detections = sv.Detections.from_ultralytics(result)

        if detections.tracker_id is None:
            return None
        
        mask = detections.class_id == PERSON_CLASS_ID

        return detections[mask]