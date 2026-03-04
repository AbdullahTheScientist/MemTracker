import datetime

class TrackManager:
    def __init__(self, fps):
        self.track_times = {}
        self.fps = fps

    def update(self, track_id, frame_no, activity):
        if track_id not in self.track_times:
            self.track_times[track_id] = {
                "first_seen_frame": frame_no,
                "last_seen_frame": frame_no,
                "first_activity": activity,
                "last_activity": activity
            }
        else:
            self.track_times[track_id]['last_seen_frame'] = frame_no
            self.track_times[track_id]['last_activity'] = activity

    def summarize(self):
        summary = {}
        if not self.track_times:
            return {
                "status": "No detections"
            }

        for track_id, data in self.track_times.items():
            first_sec = data['first_seen_frame'] / self.fps
            last_sec = data['last_seen_frame'] / self.fps
            duration = last_sec - first_sec

            summary[track_id] = {
                "first_time": str(datetime.timedelta(seconds=int(first_sec))),
                "last_time": str(datetime.timedelta(seconds=int(last_sec))),
                "duration": round(duration, 2),
                "first_activity": data["first_activity"],
                "last_activity": data["last_activity"]
            }

        return summary