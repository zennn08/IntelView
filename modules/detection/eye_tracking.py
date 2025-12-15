"""
Eye Tracking & Gaze Detection Module untuk Cheating Detection

Module ini menggunakan MediaPipe Face Mesh untuk:
1. Deteksi facial landmarks (478 points)
2. Tracking iris position dalam eye boundaries
3. Estimasi gaze direction (left/center/right)
4. Deteksi ketika kandidat melihat keluar layar (cheating indicator)

Teknik yang digunakan:
- Face Mesh: 478 facial landmarks dengan iris refinement
- Gaze Ratio: Normalized iris position (0 = kiri, 0.5 = tengah, 1 = kanan)
- Smoothing: Moving average untuk mengurangi noise
- Blink Filtering: Ignore detections saat mata sedang berkedip
- Streak Counting: Hanya flag jika sustained looking away (>0.5 detik)

Konfigurasi dapat disesuaikan melalui konstanta di bagian atas file.
"""

import cv2 as cv
import mediapipe as mp
import time
import math
import numpy as np
from collections import deque
from modules.utils import eye_utils

# =========================
# GLOBAL CONFIGURATION
# =========================
# Parameter-parameter ini dapat disesuaikan untuk tuning sensitivity

# Threshold untuk gaze direction detection
# Nilai lebih rendah = lebih toleran untuk left gaze
# Nilai lebih tinggi = lebih toleran untuk right gaze
LEFT_GAZE_THRESH = 0.25      # Default: 0.25 (gaze ratio < 0.25 = looking left)
RIGHT_GAZE_THRESH = 0.75     # Default: 0.75 (gaze ratio > 0.75 = looking right)

# Smoothing window size untuk moving average
# Nilai lebih besar = smoother tapi less responsive
SMOOTHING_WINDOW = 7         # Default: 7 frames

# Blink detection threshold (aspect ratio)
# Nilai lebih tinggi = hanya detect blink yang lebih obvious
BLINK_RATIO_THRESH = 5.5     # Default: 5.5

# Minimum durasi untuk flag cheating (dalam detik)
# Nilai lebih tinggi = reduce false positives
MIN_CHEAT_SECONDS = 0.5      # Default: 0.5 detik

# =========================
# MEDIAPIPE SETUP
# =========================

map_face_mesh = mp.solutions.face_mesh

# MediaPipe Face Mesh Landmark Indices
# Face mesh memiliki 478 landmarks, index untuk mata dan iris:

# Landmark indices untuk left eye boundary (16 points)
LEFT_EYE = [362,382,381,380,374,373,390,249,263,466,388,387,386,385,384,398]

# Landmark indices untuk right eye boundary (16 points)
RIGHT_EYE = [33,7,163,144,145,153,154,155,133,173,157,158,159,160,161,246]

# Landmark indices untuk left iris (4 points)
LEFT_IRIS = [474,475,476,477]

# Landmark indices untuk right iris (4 points)
RIGHT_IRIS = [469,470,471,472]

# =========================
# UTILITY FUNCTIONS
# =========================

def landmarksDetection(img, results):
    """
    Convert MediaPipe normalized landmarks ke pixel coordinates.

    Args:
        img: Input frame (untuk mendapat height & width)
        results: MediaPipe FaceMesh detection results

    Returns:
        list: List of (x, y) tuples dalam pixel coordinates
    """
    h, w = img.shape[:2]
    return [(int(p.x * w), int(p.y * h))
            for p in results.multi_face_landmarks[0].landmark]

def euclaideanDistance(p1, p2):
    """
    Hitung Euclidean distance antara dua point.

    Args:
        p1: Tuple (x, y) untuk point pertama
        p2: Tuple (x, y) untuk point kedua

    Returns:
        float: Euclidean distance
    """
    return math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)

def blinkRatio(img, landmarks, right_eye, left_eye):
    """
    Hitung blink ratio untuk deteksi mata berkedip.

    Blink ratio = horizontal_distance / vertical_distance
    - Ratio tinggi (>5.5) = mata tertutup (blink)
    - Ratio rendah (<5.5) = mata terbuka

    Args:
        img: Input frame
        landmarks: List of facial landmarks
        right_eye: List of right eye landmark indices
        left_eye: List of left eye landmark indices

    Returns:
        float: Average blink ratio untuk kedua mata
    """
    # Right eye ratio
    rh = euclaideanDistance(landmarks[right_eye[0]], landmarks[right_eye[8]])
    rv = euclaideanDistance(landmarks[right_eye[12]], landmarks[right_eye[4]])

    # Left eye ratio
    lh = euclaideanDistance(landmarks[left_eye[0]], landmarks[left_eye[8]])
    lv = euclaideanDistance(landmarks[left_eye[12]], landmarks[left_eye[4]])

    # Avoid division by zero
    if rv == 0 or lv == 0:
        return 0

    # Return average ratio
    return ((rh / rv) + (lh / lv)) / 2


# =========================
# GAZE ESTIMATION
# =========================

def gaze_ratio_from_mesh(mesh_coords):
    """
    Estimasi gaze direction berdasarkan posisi iris dalam eye boundaries.

    Algoritma:
    1. Hitung center point dari iris (rata-rata 4 iris landmarks)
    2. Dapatkan eye boundaries (min/max x dari eye landmarks)
    3. Normalize posisi iris: (iris_x - min_x) / (max_x - min_x)
    4. Return average dari kedua mata

    Gaze Ratio Output:
    - 0.0 - 0.25: Looking LEFT (flagged)
    - 0.25 - 0.75: Looking CENTER (normal)
    - 0.75 - 1.0: Looking RIGHT (flagged)

    Args:
        mesh_coords: List of (x, y) coordinates untuk semua 478 landmarks

    Returns:
        float: Gaze ratio 0-1, dimana 0.5 = center gaze
    """
    def iris_center(indices):
        """Hitung center point dari iris landmarks."""
        xs = [mesh_coords[i][0] for i in indices]
        ys = [mesh_coords[i][1] for i in indices]
        return (int(sum(xs)/len(xs)), int(sum(ys)/len(ys)))

    def norm_x(center, eye_coords):
        """Normalize iris x position relatif terhadap eye boundaries."""
        xs = [p[0] for p in eye_coords]
        min_x, max_x = min(xs), max(xs)
        # Avoid division by zero
        return 0.5 if max_x == min_x else (center[0] - min_x) / (max_x - min_x)

    # Get eye coordinates
    right_eye = [mesh_coords[i] for i in RIGHT_EYE]
    left_eye = [mesh_coords[i] for i in LEFT_EYE]

    # Calculate gaze ratio untuk setiap mata
    right_ratio = norm_x(iris_center(RIGHT_IRIS), right_eye)
    left_ratio = norm_x(iris_center(LEFT_IRIS), left_eye)

    # Return average dari kedua mata
    return (right_ratio + left_ratio) / 2

# =========================
# MAIN FUNCTION
# =========================

def run_eye_tracking(video_path):
    """
    Jalankan eye tracking analysis pada video untuk deteksi cheating.

    Workflow:
    1. Baca video frame-by-frame
    2. Deteksi face mesh dengan MediaPipe
    3. Extract eye & iris landmarks
    4. Filter out blinks
    5. Hitung gaze ratio dengan smoothing
    6. Deteksi jika gaze outside threshold untuk sustained period
    7. Log cheating events dengan timestamps
    8. Hitung confidence score

    Cheating Detection Logic:
    - Cheating flagged jika gaze ratio < 0.25 (left) atau > 0.75 (right)
    - Harus sustained selama MIN_CHEAT_SECONDS (default 0.5 detik)
    - Cheating detected jika total events >= 3

    Confidence Score:
    - Formula: 1 - (frames_flagged / frames_with_face)
    - 1.0 = tidak pernah looking away (ideal)
    - 0.0 = selalu looking away (worst case)

    Args:
        video_path (str): Path absolut ke file video

    Returns:
        dict: Hasil eye tracking dengan struktur:
            {
                "cheating_detected": bool,      # True jika >= 3 events
                "total_events": int,            # Jumlah cheating events
                "events": list[dict],           # Detail setiap event
                "confidence_score": float,      # 0-1 score
                "frames_total": int,            # Total frames dalam video
                "frames_with_face": int,        # Frames dengan face terdeteksi
                "frames_flagged": int           # Frames yang flagged cheating
            }

    Example:
        >>> result = run_eye_tracking("/tmp/interview.mp4")
        >>> print(result["cheating_detected"])
        False
        >>> print(result["confidence_score"])
        0.92
    """
    # Buka video file
    cap = cv.VideoCapture(video_path)
    if not cap.isOpened():
        return {"error": "cannot_open_video"}

    # Ambil FPS dan hitung minimum consecutive frames untuk cheating flag
    fps = cap.get(cv.CAP_PROP_FPS) or 25
    MIN_CONSEC_FRAMES = int(fps * MIN_CHEAT_SECONDS)  # Auto-convert detik ke frames

    # Smoothing buffer menggunakan deque (efficient FIFO)
    ratio_buffer = deque(maxlen=SMOOTHING_WINDOW)

    # Cheating detection state
    cheating_events = []      # List of cheating events dengan timestamps
    cheat_streak = 0          # Counter consecutive frames looking away
    cheating_state = False    # Flag untuk avoid duplicate events
    frame_count = 0

    # Statistics untuk confidence score
    frames_total = 0          # Total frames processed
    frames_with_face = 0      # Frames dengan face terdeteksi
    frames_flagged = 0        # Frames yang flagged sebagai looking away

    # Initialize MediaPipe Face Mesh
    # refine_landmarks=True: Enable iris tracking
    # min_detection_confidence=0.5: Threshold untuk initial detection
    # min_tracking_confidence=0.5: Threshold untuk tracking antar frame
    with map_face_mesh.FaceMesh(
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as face_mesh:

        # Main video processing loop
        while True:
            ret, frame = cap.read()
            if not ret:
                break  # End of video

            frames_total += 1
            frame_count += 1

            # Resize frame sedikit untuk better visibility
            # Faktor 1.2x memberikan sedikit zoom tanpa terlalu mempengaruhi performa
            frame = cv.resize(frame, None, fx=1.2, fy=1.2)

            # Process dengan MediaPipe (perlu RGB format)
            results = face_mesh.process(cv.cvtColor(frame, cv.COLOR_BGR2RGB))

            # Check jika face terdeteksi
            if not results.multi_face_landmarks:
                # No face detected - reset streak
                cheat_streak = 0
                continue

            # Face detected - update counter dan extract landmarks
            frames_with_face += 1
            mesh_coords = landmarksDetection(frame, results)

            # ========== BLINK FILTER ==========
            # Ignore detection jika mata sedang berkedip
            # Ini mengurangi false positives dari deteksi saat blink
            blink = blinkRatio(frame, mesh_coords, RIGHT_EYE, LEFT_EYE)
            if blink > BLINK_RATIO_THRESH:
                cheat_streak = 0
                continue

            # ========== GAZE ESTIMATION ==========
            # Hitung gaze ratio dan apply smoothing
            ratio = gaze_ratio_from_mesh(mesh_coords)
            ratio_buffer.append(ratio)
            smooth_ratio = sum(ratio_buffer) / len(ratio_buffer)

            # Check jika gaze outside threshold (looking away)
            is_cheating = (
                smooth_ratio < LEFT_GAZE_THRESH or
                smooth_ratio > RIGHT_GAZE_THRESH
            )

            # Update streak dan statistics
            if is_cheating:
                frames_flagged += 1
                cheat_streak += 1
            else:
                cheat_streak = 0

            # ========== EVENT LOGGING ==========
            # Log cheating event jika streak mencapai threshold
            # dan belum dalam cheating state (avoid duplicate)
            if cheat_streak >= MIN_CONSEC_FRAMES and not cheating_state:
                second = round(frame_count / fps, 2)
                cheating_events.append({"timestamp_second": second})
                cheating_state = True

            # Reset state ketika streak kembali ke 0
            if cheat_streak == 0:
                cheating_state = False

    # Cleanup
    cap.release()

    # Calculate confidence score
    # Score tinggi = jarang looking away (good)
    # Score rendah = sering looking away (suspicious)
    confidence_score = (
        0.0 if frames_with_face == 0
        else round(1 - frames_flagged / frames_with_face, 2)
    )

    # Return comprehensive results
    # cheating_detected = True jika ada >= 3 events (threshold untuk reduce false positives)
    return {
        "cheating_detected": len(cheating_events) >= 3,
        "total_events": len(cheating_events),
        "events": cheating_events,
        "confidence_score": confidence_score,
        "frames_total": frames_total,
        "frames_with_face": frames_with_face,
        "frames_flagged": frames_flagged,
    }
