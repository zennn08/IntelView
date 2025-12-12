import cv2
from ultralytics import YOLO
from motpy import Detection, MultiObjectTracker
import logging
import time

logger = logging.getLogger(__name__)

# -----------------------
# Load YOLOv12-Face
# -----------------------
det_model = YOLO("yolov12n-face.pt")
device = "cuda" if cv2.cuda.getCudaEnabledDeviceCount() > 0 else "cpu"
det_model.to(device)


def run_people_detector(
    video_path,
    detection_interval=4,      # Deteksi setiap N frame
    conf_threshold=0.4,
    resolution=(640, 360),     # Resolusi lebih kecil
    min_track_seconds=0.8,     # Validasi track (sedikit lebih cepat)
    max_staleness=8            # Track hilang setelah N frame tanpa deteksi
):
    """
    People detector.
    
    Args:
        video_path: Path ke file video
        detection_interval: Deteksi setiap N frame
        conf_threshold: YOLO confidence threshold
        resolution: Tuple (width, height) untuk resize frame
        min_track_seconds: Minimum detik untuk validasi track
        max_staleness: Frame sebelum track dianggap hilang
    
    Returns:
        dict dengan hasil deteksi dan confidence score
    """
    time_start = time.time()
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"error": "cannot_open_video"}

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    frame_count = 0
    detected_frames = 0

    # MotPY tracker dengan config lebih ringan
    tracker = MultiObjectTracker(
        dt=1.0 / fps * detection_interval,  # Sesuaikan dt dengan interval
        tracker_kwargs={
            "max_staleness": max_staleness
        }
    )

    # Track validation
    min_frames_alive = int(fps / detection_interval * min_track_seconds)
    track_lifetime = {}
    valid_tracks = set()

    # Stats untuk confidence score
    single_person_frames = 0
    
    cheating_events = []
    cheating_state = False

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # Skip frame
        if frame_count % detection_interval != 0:
            continue

        detected_frames += 1
        frame_resized = cv2.resize(frame, resolution)

        # YOLO detection
        results = det_model(frame_resized, conf=conf_threshold, verbose=False)
        det = results[0].boxes

        detections = []
        for box in det:
            cls = int(box.cls[0])
            if cls == 0:  # face
                xmin, ymin, xmax, ymax = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0].cpu().numpy())
                detections.append(
                    Detection(
                        box=[xmin, ymin, xmax, ymax],
                        score=conf
                    )
                )

        # Update tracker
        tracker.step(detections)
        active_tracks = tracker.active_tracks()

        # Track lifetime update
        current_ids = set()
        for t in active_tracks:
            tid = t.id
            current_ids.add(tid)

            track_lifetime[tid] = track_lifetime.get(tid, 0) + 1

            if track_lifetime[tid] >= min_frames_alive:
                valid_tracks.add(tid)

        # Cleanup inactive tracks
        track_lifetime = {tid: cnt for tid, cnt in track_lifetime.items() if tid in current_ids}

        # Hitung valid people
        valid_count = sum(1 for tid in current_ids if tid in valid_tracks)

        # Stats untuk confidence
        if valid_count == 1:
            single_person_frames += 1

        # Timestamp
        second = round(frame_count / fps, 2)
        minute = int(second // 60)
        sec_only = round(second % 60, 2)

        # Cheating detection
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

    # Confidence score
    confidence_score = 0.0
    if detected_frames > 0:
        confidence_score = round(single_person_frames / detected_frames, 4)

    time_end = time.time()
    execution_time = round(time_end - time_start, 3)

    print(f"Time execution people_detector: {execution_time}s")

    return {
        "cheating_detected": len(cheating_events) > 0,
        "total_events": len(cheating_events),
        "confidence_score": confidence_score,
        "valid_people": len(valid_tracks),
        "single_person_frames": single_person_frames,
        "total_detected_frames": detected_frames,
        "total_frames": frame_count,
        "execution_time": execution_time,
        "events": cheating_events
    }