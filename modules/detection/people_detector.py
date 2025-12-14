"""
People Detection & Tracking Module untuk Cheating Detection

Module ini menggunakan YOLO12n-Face untuk mendeteksi wajah dalam video dan
MotPy (Multi-Object Tracking library) untuk tracking konsisten antar frame.

Tujuan utama: Mendeteksi kehadiran lebih dari satu orang dalam frame video
sebagai indikator kecurangan potensial dalam wawancara.

Optimasi Performa:
- Frame skipping: Proses setiap N frame (default: 4)
- Resolution downscaling: 640x360 untuk inference lebih cepat
- Track validation: Hanya count track yang valid (>=0.8 detik)
- GPU acceleration: Otomatis gunakan CUDA jika tersedia
"""

import cv2
from ultralytics import YOLO
from motpy import Detection, MultiObjectTracker
import logging
import time

logger = logging.getLogger(__name__)

# Load YOLO12n-Face model (lightweight face detection model)
# Model file: yolov12n-face.pt harus ada di root directory
det_model = YOLO("yolov12n-face.pt")

# Deteksi GPU availability dan pilih device otomatis
device = "cuda" if cv2.cuda.getCudaEnabledDeviceCount() > 0 else "cpu"
det_model.to(device)


def run_people_detector(
    video_path,
    detection_interval=4,      # Proses setiap 4 frame untuk efisiensi
    conf_threshold=0.4,        # YOLO confidence threshold untuk face detection
    resolution=(640, 360),     # Resolusi rendah untuk inference cepat
    min_track_seconds=0.8,     # Track dianggap valid setelah 0.8 detik
    max_staleness=8            # Track dianggap hilang setelah 8 frame tanpa deteksi
):
    """
    Deteksi dan track multiple people dalam video untuk cheating detection.

    Workflow:
    1. Baca video frame-by-frame
    2. Skip frame sesuai detection_interval untuk efisiensi
    3. Resize frame ke resolusi lebih rendah
    4. Jalankan YOLO face detection
    5. Update MotPy tracker dengan detections
    6. Validasi tracks (filter tracks yang terlalu singkat)
    7. Hitung jumlah valid people per frame
    8. Deteksi cheating jika valid_people > 1
    9. Hitung confidence score berdasarkan proportion single-person frames

    Args:
        video_path (str): Path absolut ke file video
        detection_interval (int): Proses setiap N frame (4 = 25% frames)
        conf_threshold (float): YOLO confidence threshold (0.0-1.0)
        resolution (tuple): Target resolution (width, height) untuk resize
        min_track_seconds (float): Minimum durasi track agar dianggap valid
        max_staleness (int): Max frames tanpa detection sebelum track dihapus

    Returns:
        dict: Hasil deteksi dengan struktur:
            {
                "cheating_detected": bool,          # Ada >1 orang terdeteksi?
                "total_events": int,                # Jumlah cheating events
                "confidence_score": float,          # 0-1, portion single person frames
                "valid_people": int,                # Jumlah unique valid people
                "single_person_frames": int,        # Frames dengan hanya 1 orang
                "total_detected_frames": int,       # Total frames yang diproses
                "total_frames": int,                # Total frames dalam video
                "execution_time": float,            # Waktu eksekusi (detik)
                "events": list[dict]                # Detail setiap cheating event
            }

    Example:
        >>> result = run_people_detector("/tmp/interview.mp4")
        >>> print(result["cheating_detected"])
        True
        >>> print(result["confidence_score"])
        0.73
    """
    # Mulai tracking waktu eksekusi
    time_start = time.time()

    # Buka video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"error": "cannot_open_video"}

    # Ambil metadata video
    fps = cap.get(cv2.CAP_PROP_FPS) or 25  # Default 25 FPS jika tidak terdeteksi
    frame_count = 0
    detected_frames = 0  # Counter frames yang benar-benar diproses

    # Inisialisasi MotPy Multi-Object Tracker
    # dt (delta time) disesuaikan dengan detection interval
    # max_staleness: berapa frame tanpa deteksi sebelum track dihapus
    tracker = MultiObjectTracker(
        dt=1.0 / fps * detection_interval,  # Time step antar deteksi
        tracker_kwargs={
            "max_staleness": max_staleness
        }
    )

    # Track Validation System
    # Hanya count track yang "valid" (muncul cukup lama)
    # Ini mengurangi false positive dari deteksi sesaat
    min_frames_alive = int(fps / detection_interval * min_track_seconds)
    track_lifetime = {}  # {track_id: frame_count}
    valid_tracks = set()  # Set of track IDs yang sudah valid

    # Statistics untuk confidence score calculation
    single_person_frames = 0

    # Cheating detection state
    cheating_events = []
    cheating_state = False  # Flag untuk menghindari duplicate event

    # Main video processing loop
    while True:
        ret, frame = cap.read()
        if not ret:
            break  # End of video

        frame_count += 1

        # Frame Skipping untuk efisiensi
        # Hanya proses setiap N frame (detection_interval)
        if frame_count % detection_interval != 0:
            continue

        detected_frames += 1

        # Resize frame untuk inference lebih cepat
        # Trade-off: Slightly lower detection accuracy tapi 4-5x lebih cepat
        frame_resized = cv2.resize(frame, resolution)

        # YOLO Face Detection
        # verbose=False untuk mematikan logging per-inference
        results = det_model(frame_resized, conf=conf_threshold, verbose=False)
        det = results[0].boxes

        # Convert YOLO detections ke format MotPy
        detections = []
        for box in det:
            cls = int(box.cls[0])
            if cls == 0:  # Class 0 = face
                # Extract bounding box coordinates
                xmin, ymin, xmax, ymax = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0].cpu().numpy())

                # Buat MotPy Detection object
                detections.append(
                    Detection(
                        box=[xmin, ymin, xmax, ymax],
                        score=conf
                    )
                )

        # Update Tracker dengan detections frame ini
        # Tracker akan associate detections dengan existing tracks
        # atau create new tracks jika perlu
        tracker.step(detections)
        active_tracks = tracker.active_tracks()

        # Update Track Lifetime & Validation
        current_ids = set()
        for t in active_tracks:
            tid = t.id
            current_ids.add(tid)

            # Increment lifetime counter untuk track ini
            track_lifetime[tid] = track_lifetime.get(tid, 0) + 1

            # Validasi: jika track sudah cukup lama, tandai sebagai valid
            if track_lifetime[tid] >= min_frames_alive:
                valid_tracks.add(tid)

        # Cleanup: Hapus lifetime data untuk tracks yang sudah tidak aktif
        track_lifetime = {tid: cnt for tid, cnt in track_lifetime.items() if tid in current_ids}

        # Hitung jumlah valid people di frame ini
        # Hanya count tracks yang sudah tervalidasi
        valid_count = sum(1 for tid in current_ids if tid in valid_tracks)

        # Update statistics untuk confidence score
        if valid_count == 1:
            single_person_frames += 1

        # Calculate timestamp untuk event logging
        second = round(frame_count / fps, 2)
        minute = int(second // 60)
        sec_only = round(second % 60, 2)

        # Cheating Detection Logic
        # Flag cheating jika ada lebih dari 1 valid person
        # State machine untuk menghindari duplicate events
        if valid_count > 1 and not cheating_state:
            # Cheating terdeteksi pertama kali
            cheating_events.append({
                "timestamp_second": second,
                "timestamp_minute": minute,
                "timestamp_sec_only": sec_only,
                "valid_people_detected": valid_count
            })
            cheating_state = True
        elif valid_count <= 1:
            # Kembali ke state normal (hanya 1 atau 0 orang)
            cheating_state = False

    # Cleanup
    cap.release()

    # Calculate Confidence Score
    # Confidence = proportion of frames dengan hanya 1 orang
    # Score tinggi (mendekati 1.0) = hampir selalu single person
    # Score rendah = sering ada multiple people atau tidak ada orang
    confidence_score = 0.0
    if detected_frames > 0:
        confidence_score = round(single_person_frames / detected_frames, 2)

    # Hitung waktu eksekusi total
    time_end = time.time()
    execution_time = round(time_end - time_start, 3)

    print(f"Time execution people_detector: {execution_time}s")

    # Return comprehensive results
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
