import cv2 as cv
import mediapipe as mp
import time
from modules.utils import eye_utils  # atau: from . import utils
import math

import numpy as np
#import pygame 
#from pygame import mixer 

# variables 
frame_counter =0
CEF_COUNTER =0
TOTAL_BLINKS =0
start_voice= False
counter_right=0
counter_left =0
counter_center =0 
# constants
CLOSED_EYES_FRAME =3
FONTS =cv.FONT_HERSHEY_COMPLEX

# initialize mixer 
#mixer.init()
# loading in the voices/sounds 
#voice_left = mixer.Sound('Voice/left.wav')
#voice_right = mixer.Sound('Voice/Right.wav')
#voice_center = mixer.Sound('Voice/center.wav')

# face bounder indices 
FACE_OVAL=[ 10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103,67, 109]

# lips indices for Landmarks
LIPS=[ 61, 146, 91, 181, 84, 17, 314, 405, 321, 375,291, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95,185, 40, 39, 37,0 ,267 ,269 ,270 ,409, 415, 310, 311, 312, 13, 82, 81, 42, 183, 78 ]
LOWER_LIPS =[61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95]
UPPER_LIPS=[ 185, 40, 39, 37,0 ,267 ,269 ,270 ,409, 415, 310, 311, 312, 13, 82, 81, 42, 183, 78] 
# Left eyes indices 
LEFT_EYE =[ 362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385,384, 398 ]
LEFT_EYEBROW =[ 336, 296, 334, 293, 300, 276, 283, 282, 295, 285 ]

# right eyes indices
RIGHT_EYE=[ 33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161 , 246 ]  
RIGHT_EYEBROW=[ 70, 63, 105, 66, 107, 55, 65, 52, 53, 46 ]

# iris landmarks (available when refine_landmarks=True)
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]

map_face_mesh = mp.solutions.face_mesh

# landmark detection function 

def landmarksDetection(img, results, draw=False):
    img_height, img_width= img.shape[:2]
    # list[(x,y), (x,y)....]
    mesh_coord = [(int(point.x * img_width), int(point.y * img_height)) for point in results.multi_face_landmarks[0].landmark]
    if draw :
        [cv.circle(img, p, 2, (0,255,0), -1) for p in mesh_coord]

    # returning the list of tuples for each landmarks 
    return mesh_coord

# Euclaidean distance 
def euclaideanDistance(point, point1):
    x, y = point
    x1, y1 = point1
    distance = math.sqrt((x1 - x)*2 + (y1 - y)*2)
    return distance

# Blinking Ratio
def blinkRatio(img, landmarks, right_indices, left_indices):
    # Right eyes 
    # horizontal line 
    rh_right = landmarks[right_indices[0]]
    rh_left = landmarks[right_indices[8]]
    # vertical line 
    rv_top = landmarks[right_indices[12]]
    rv_bottom = landmarks[right_indices[4]]
    # draw lines on right eyes 
    cv.line(img, rh_right, rh_left, eye_utils.GREEN, 2)
    cv.line(img, rv_top, rv_bottom, eye_utils.WHITE, 2)

    # LEFT_EYE 
    # horizontal line 
    lh_right = landmarks[left_indices[0]]
    lh_left = landmarks[left_indices[8]]

    # vertical line 
    lv_top = landmarks[left_indices[12]]
    lv_bottom = landmarks[left_indices[4]]

    rhDistance = euclaideanDistance(rh_right, rh_left)
    rvDistance = euclaideanDistance(rv_top, rv_bottom)

    lvDistance = euclaideanDistance(lv_top, lv_bottom)
    lhDistance = euclaideanDistance(lh_right, lh_left)

    reRatio = rhDistance/rvDistance
    leRatio = lhDistance/lvDistance

    ratio = (reRatio+leRatio)/2
    return ratio 

# Eyes Extrctor function,
def eyesExtractor(img, right_eye_coords, left_eye_coords):
    # converting color image to  scale image 
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    
    # getting the dimension of image 
    dim = gray.shape

    # creating mask from gray scale dim
    mask = np.zeros(dim, dtype=np.uint8)

    # drawing Eyes Shape on mask with white color 
    cv.fillPoly(mask, [np.array(right_eye_coords, dtype=np.int32)], 255)
    cv.fillPoly(mask, [np.array(left_eye_coords, dtype=np.int32)], 255)

    # showing the mask 
    # cv.imshow('mask', mask)
    
    # draw eyes image on mask, where white shape is 
    eyes = cv.bitwise_and(gray, gray, mask=mask)
    # change black color to gray other than eys 
    # cv.imshow('eyes draw', eyes)
    eyes[mask==0]=155
    
    # getting minium and maximum x and y  for right and left eyes 
    # For Right Eye 
    r_max_x = (max(right_eye_coords, key=lambda item: item[0]))[0]
    r_min_x = (min(right_eye_coords, key=lambda item: item[0]))[0]
    r_max_y = (max(right_eye_coords, key=lambda item : item[1]))[1]
    r_min_y = (min(right_eye_coords, key=lambda item: item[1]))[1]

    # For LEFT Eye
    l_max_x = (max(left_eye_coords, key=lambda item: item[0]))[0]
    l_min_x = (min(left_eye_coords, key=lambda item: item[0]))[0]
    l_max_y = (max(left_eye_coords, key=lambda item : item[1]))[1]
    l_min_y = (min(left_eye_coords, key=lambda item: item[1]))[1]

    # croping the eyes from mask 
    cropped_right = eyes[r_min_y: r_max_y, r_min_x: r_max_x]
    cropped_left = eyes[l_min_y: l_max_y, l_min_x: l_max_x]

    # returning the cropped eyes 
    return cropped_right, cropped_left

# Eyes Postion Estimator 
def positionEstimator(cropped_eye):
    # getting height and width of eye 
    h, w =cropped_eye.shape
    
    # remove the noise from images
    gaussain_blur = cv.GaussianBlur(cropped_eye, (9,9),0)
    median_blur = cv.medianBlur(gaussain_blur, 3)

    # applying thrsholding to convert binary_image
    ret, threshed_eye = cv.threshold(median_blur, 130, 255, cv.THRESH_BINARY)

    # create fixd part for eye with 
    piece = int(w/3) 
    
    # slicing the eyes into three parts 
    # left, center, right slices (was reversed before)
    left_piece = threshed_eye[0:h, 0:piece]
    center_piece = threshed_eye[0:h, piece: piece+piece]
    right_piece = threshed_eye[0:h, piece +piece:w]
    
    # calling pixel counter function
    eye_position, color = pixelCounter(left_piece, center_piece, right_piece)

    return eye_position, color 

# creating pixel counter function 
def pixelCounter(first_piece, second_piece, third_piece):
    # counting black pixel in each part (left, center, right)
    left_part = np.sum(first_piece == 0)
    center_part = np.sum(second_piece == 0)
    right_part = np.sum(third_piece == 0)
    eye_parts = [left_part, center_part, right_part]

    max_index = eye_parts.index(max(eye_parts))
    if max_index == 0:
        pos_eye = "Cheating"
        color = [eye_utils.GRAY, eye_utils.YELLOW]
    elif max_index == 1:
        pos_eye = ""
        color = [eye_utils.YELLOW, eye_utils.PINK]
    else:
        pos_eye = "Cheating"
        color = [eye_utils.BLACK, eye_utils.GREEN]
    return pos_eye, color


def run_eye_tracking(video_path, min_consecutive_cheat_frames=10, left_thresh=0.35, right_thresh=0.65):
    """
    Deteksi gaze berbasis video input (bukan kamera live).
    Mengembalikan dict berisi status cheating dan daftar event (timestamp).
    left_thresh/right_thresh dipakai sebagai ambang kiri/kanan; tengah diabaikan (tidak dihitung cheating).
    """
    time_start = time.time()
    cap = cv.VideoCapture(video_path)
    if not cap.isOpened():
        return {"error": "cannot_open_video"}

    fps = cap.get(cv.CAP_PROP_FPS) or 25
    frame_count = 0
    cheating_events = []
    cheating_state = False
    cheat_streak = 0

    def gaze_ratio_from_mesh(mesh_coords):
        right_coords = [mesh_coords[p] for p in RIGHT_EYE]
        left_coords = [mesh_coords[p] for p in LEFT_EYE]

        def iris_center(indices):
            pts = [mesh_coords[i] for i in indices]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            return (int(sum(xs) / len(xs)), int(sum(ys) / len(ys)))

        def norm_x(center, coords):
            xs = [p[0] for p in coords]
            min_x, max_x = min(xs), max(xs)
            if max_x == min_x:
                return 0.5
            return (center[0] - min_x) / (max_x - min_x)

        right_iris_c = iris_center(RIGHT_IRIS)
        left_iris_c = iris_center(LEFT_IRIS)
        right_ratio = norm_x(right_iris_c, right_coords)
        left_ratio = norm_x(left_iris_c, left_coords)
        return (right_ratio + left_ratio) / 2

    with map_face_mesh.FaceMesh(
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as face_mesh:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            frame = cv.resize(frame, None, fx=1.5, fy=1.5, interpolation=cv.INTER_CUBIC)
            results = face_mesh.process(cv.cvtColor(frame, cv.COLOR_BGR2RGB))
            if results.multi_face_landmarks:
                mesh_coords = landmarksDetection(frame, results, False)
                ratio = gaze_ratio_from_mesh(mesh_coords)
                is_cheating = ratio < left_thresh or ratio > right_thresh
            else:
                is_cheating = False

            cheat_streak = cheat_streak + 1 if is_cheating else 0

            if cheat_streak >= min_consecutive_cheat_frames and not cheating_state:
                second = round(frame_count / fps, 2)
                minute = int(second // 60)
                sec_only = round(second % 60, 2)
                cheating_events.append(
                    {
                        "timestamp_second": second,
                        "timestamp_minute": minute,
                        "timestamp_sec_only": sec_only,
                    }
                )
                cheating_state = True
            elif cheat_streak == 0:
                cheating_state = False

    cap.release()

    time_end = time.time()
    execution_time = round(time_end - time_start, 3)
    print("Time execution eye_tracking : " , execution_time)

    return {
        "cheating_detected": len(cheating_events) >= 2,
        "total_events": len(cheating_events),
        "events": cheating_events,
    }