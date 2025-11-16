import cv2
from ultralytics import YOLO
from motpy import Detection, MultiObjectTracker
import logging
import os

logger = logging.getLogger(__name__)

# -----------------------
# Load YOLOv12-Face
# -----------------------
det_model = YOLO("yolov12n-face.pt")  # Ganti dengan model kamu
device = "cuda" if cv2.cuda.getCudaEnabledDeviceCount() > 0 else "cpu"
det_model.to(device)

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

    # --- Track Validation (min 1 second)
    min_frames_alive = int(fps * 1)   # 1 second validation
    track_lifetime = {}               # track_id → count_frames
    valid_tracks = set()              # track_id yg sudah valid
    
    cheating_events = []
    cheating_state = False

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        frame = cv2.resize(frame, (640, 360))

        # YOLO detect setiap 3 frame
        persons = []
        if frame_count % 3 == 0:
            results = det_model(frame, conf=0.4, verbose=False)
            det = results[0].boxes

            for box in det:
                cls = int(box.cls[0])

                # Untuk YOLO-Face, class biasanya 0 = face
                if cls == 0:
                    xmin, ymin, xmax, ymax = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0].cpu().numpy())

                    persons.append({
                        "xmin": int(xmin),
                        "ymin": int(ymin),
                        "xmax": int(xmax),
                        "ymax": int(ymax),
                        "confidence": conf
                    })

            detections = [
                Detection(
                    box=[p["xmin"], p["ymin"], p["xmax"], p["ymax"]],
                    score=p["confidence"]
                )
                for p in persons
            ]

            tracker.step(detections)
        else:
            tracker.step([])

        active_tracks = tracker.active_tracks()

        # --- Track Lifetime Update ---
        current_ids = set()
        for t in active_tracks:
            tid = t.id
            current_ids.add(tid)

            # Tambah waktu hidup track
            if tid not in track_lifetime:
                track_lifetime[tid] = 1
            else:
                track_lifetime[tid] += 1

            # Track valid jika sudah hidup >= 1 detik
            if track_lifetime[tid] >= min_frames_alive:
                valid_tracks.add(tid)

        # Hapus ID yg tidak lagi aktif dari track_lifetime
        to_delete = []
        for tid in track_lifetime:
            if tid not in current_ids:
                to_delete.append(tid)
        for tid in to_delete:
            del track_lifetime[tid]

        # Hitung berapa orang valid dalam frame ini
        valid_count = len([tid for tid in current_ids if tid in valid_tracks])

        # Waktu
        second = round(frame_count / fps, 2)
        minute = int(second // 60)
        sec_only = round(second % 60, 2)

        # --- Cheating detection ---
        if valid_count > 1 and not cheating_state:
            cheating_events.append({
                "timestamp_second": second,
                "timestamp_minute": minute,
                "timestamp_sec_only": sec_only,
                "valid_people_detected": valid_count
            })
            cheating_state = True
        elif valid_count <= 1:
            cheating_state = False

    cap.release()

    return {
        "cheating_detected": len(cheating_events) > 0,
        "total_events": len(cheating_events),
        "valid_people": len(valid_tracks),
        "events": cheating_events
    }