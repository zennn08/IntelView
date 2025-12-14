import cv2 as cv
import mediapipe as mp
import time
import math
import numpy as np
from collections import deque
from modules.utils import eye_utils

# =========================
# GLOBAL ADJUST CONFIG
# =========================

LEFT_GAZE_THRESH = 0.25      # ADJUST DI SINI (semakin kecil = makin toleran)
RIGHT_GAZE_THRESH = 0.75     # ADJUST DI SINI (semakin besar = makin toleran)

SMOOTHING_WINDOW = 7         # ADJUST DI SINI
BLINK_RATIO_THRESH = 5.5     # ADJUST DI SINI (blink detector)
MIN_CHEAT_SECONDS = 0.5      # ADJUST DI SINI (durasi minimal cheating)

# =========================
# MEDIAPIPE
# =========================

map_face_mesh = mp.solutions.face_mesh

LEFT_EYE =[362,382,381,380,374,373,390,249,263,466,388,387,386,385,384,398]
RIGHT_EYE=[33,7,163,144,145,153,154,155,133,173,157,158,159,160,161,246]

LEFT_IRIS = [474,475,476,477]
RIGHT_IRIS = [469,470,471,472]

# =========================
# UTILS
# =========================

def landmarksDetection(img, results):
    h, w = img.shape[:2]
    return [(int(p.x * w), int(p.y * h))
            for p in results.multi_face_landmarks[0].landmark]

def euclaideanDistance(p1, p2):
    return math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)

def blinkRatio(img, landmarks, right_eye, left_eye):
    rh = euclaideanDistance(landmarks[right_eye[0]], landmarks[right_eye[8]])
    rv = euclaideanDistance(landmarks[right_eye[12]], landmarks[right_eye[4]])

    lh = euclaideanDistance(landmarks[left_eye[0]], landmarks[left_eye[8]])
    lv = euclaideanDistance(landmarks[left_eye[12]], landmarks[left_eye[4]])

    if rv == 0 or lv == 0:
        return 0

    return ((rh / rv) + (lh / lv)) / 2


# =========================
# GAZE ESTIMATION
# =========================

def gaze_ratio_from_mesh(mesh_coords):

    def iris_center(indices):
        xs = [mesh_coords[i][0] for i in indices]
        ys = [mesh_coords[i][1] for i in indices]
        return (int(sum(xs)/len(xs)), int(sum(ys)/len(ys)))

    def norm_x(center, eye_coords):
        xs = [p[0] for p in eye_coords]
        min_x, max_x = min(xs), max(xs)
        return 0.5 if max_x == min_x else (center[0] - min_x) / (max_x - min_x)

    right_eye = [mesh_coords[i] for i in RIGHT_EYE]
    left_eye = [mesh_coords[i] for i in LEFT_EYE]

    right_ratio = norm_x(iris_center(RIGHT_IRIS), right_eye)
    left_ratio = norm_x(iris_center(LEFT_IRIS), left_eye)

    return (right_ratio + left_ratio) / 2

# =========================
# MAIN FUNCTION
# =========================

def run_eye_tracking(video_path):

    cap = cv.VideoCapture(video_path)
    if not cap.isOpened():
        return {"error": "cannot_open_video"}

    fps = cap.get(cv.CAP_PROP_FPS) or 25
    MIN_CONSEC_FRAMES = int(fps * MIN_CHEAT_SECONDS)  # 🔧 AUTO-CONVERT

    ratio_buffer = deque(maxlen=SMOOTHING_WINDOW)

    cheating_events = []
    cheat_streak = 0
    cheating_state = False
    frame_count = 0

    frames_total = 0
    frames_with_face = 0
    frames_flagged = 0

    with map_face_mesh.FaceMesh(
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as face_mesh:

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frames_total += 1
            frame_count += 1

            # 🔧 ADJUST DI SINI (jangan terlalu besar)
            frame = cv.resize(frame, None, fx=1.2, fy=1.2)

            results = face_mesh.process(cv.cvtColor(frame, cv.COLOR_BGR2RGB))

            if not results.multi_face_landmarks:
                cheat_streak = 0
                continue

            frames_with_face += 1
            mesh_coords = landmarksDetection(frame, results)

            # ========== BLINK FILTER ==========
            blink = blinkRatio(frame, mesh_coords, RIGHT_EYE, LEFT_EYE)
            if blink > BLINK_RATIO_THRESH:
                cheat_streak = 0
                continue

            # ========== GAZE ==========
            ratio = gaze_ratio_from_mesh(mesh_coords)
            ratio_buffer.append(ratio)
            smooth_ratio = sum(ratio_buffer) / len(ratio_buffer)

            is_cheating = (
                smooth_ratio < LEFT_GAZE_THRESH or
                smooth_ratio > RIGHT_GAZE_THRESH
            )

            if is_cheating:
                frames_flagged += 1
                cheat_streak += 1
            else:
                cheat_streak = 0

            # ========== EVENT ==========
            if cheat_streak >= MIN_CONSEC_FRAMES and not cheating_state:
                second = round(frame_count / fps, 2)
                cheating_events.append({"timestamp_second": second})
                cheating_state = True

            if cheat_streak == 0:
                cheating_state = False

    cap.release()

    return {
        "cheating_detected": len(cheating_events) >= 3,
        "total_events": len(cheating_events),
        "events": cheating_events,
        "confidence_score": (
            0.0 if frames_with_face == 0
            else round(1 - frames_flagged / frames_with_face, 2)
        ),
        "frames_total": frames_total,
        "frames_with_face": frames_with_face,
        "frames_flagged": frames_flagged,
    }
