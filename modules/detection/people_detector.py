import cv2
import torch
from motpy import Detection, MultiObjectTracker
import logging
import os

logger = logging.getLogger(__name__)

# -----------------------
# Load YOLO From Local File
# -----------------------
device = "cuda" if torch.cuda.is_available() else "cpu"

det_model = torch.hub.load("ultralytics/yolov5", "yolov5s", pretrained=True)
det_model.to(device)
det_model.conf = 0.4

# -----------------------
# People Detector Function
# -----------------------
def run_people_detector(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"error": "cannot_open_video"}

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    frame_count = 0

    tracker = MultiObjectTracker(dt=1.0/fps, tracker_kwargs={"max_staleness": 10})
    cheating_events = []
    cheating_state = False

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        frame = cv2.resize(frame, (640, 360))

        # detect setiap 3 frame
        if frame_count % 3 == 0:
            results = det_model(frame)
            df = results.pandas().xyxy[0]
            persons = df[df["name"] == "person"]

            detections = [
                Detection(
                    box=[int(p["xmin"]), int(p["ymin"]), int(p["xmax"]), int(p["ymax"])],
                    score=float(p["confidence"])
                )
                for _, p in persons.iterrows()
            ]

            tracker.step(detections)
        else:
            tracker.step([])

        active = tracker.active_tracks()
        count = len(active)

        # Hitung timestamp
        second = round(frame_count / fps, 2)
        minute = int(second // 60)
        sec_only = round(second % 60, 2)

        # Cheating event
        if count > 1 and not cheating_state:
            cheating_events.append({
                "timestamp_second": second,
                "timestamp_minute": minute,
                "timestamp_sec_only": sec_only,
                "people_detected": count
            })
            cheating_state = True
        elif count <= 1:
            cheating_state = False

    cap.release()

    return {
        "cheating_detected": len(cheating_events) > 0,
        "total_events": len(cheating_events),
        "events": cheating_events
    }
