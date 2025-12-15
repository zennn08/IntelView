"""
Eye Tracking Visualization Utilities

Module ini berisi utility functions untuk visualisasi eye tracking results.
Functions ini digunakan untuk menggambar annotations pada video frames,
termasuk eye landmarks, gaze indicators, dan text overlays.

Note: Module ini tidak digunakan dalam production pipeline saat ini,
tetapi berguna untuk debugging dan development visualization.
"""

import cv2 as cv
import numpy as np

# ================= COLOR CONSTANTS (BGR FORMAT) =================
# OpenCV menggunakan BGR format, bukan RGB
# Format: (Blue, Green, Red)

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (255, 0, 0)
RED = (0, 0, 255)
CYAN = (255, 255, 0)
YELLOW = (0, 255, 255)
MAGENTA = (255, 0, 255)
GRAY = (128, 128, 128)
GREEN = (0, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (0, 165, 255)
PINK = (147, 20, 255)

# ================= DRAWING UTILITY FUNCTIONS =================


def drawColor(img, colors, start=(10, 10)):
    """
    Draw color palette/legend pada image.

    Menggambar serangkaian kotak berwarna secara horizontal,
    berguna untuk menampilkan legend atau color reference pada frame.

    Args:
        img (np.ndarray): Input image untuk menggambar
        colors (list): List of color tuples (BGR format)
        start (tuple): Starting position (x, y) untuk color palette

    Returns:
        np.ndarray: Image dengan color palette yang digambar

    Example:
        >>> img = drawColor(img, [RED, GREEN, BLUE], start=(10, 10))
    """
    x, y = start
    w, h = 20, 30  # Width dan height untuk setiap color box

    for color in colors:
        # Gambar outer border (dark green)
        cv.rectangle(img, (x - 6, y - 5), (x + w + 5, y + h + 5), (10, 50, 10), -1)
        # Gambar color box
        cv.rectangle(img, (x, y), (x + w, y + h), color, -1)
        x += w + 8  # Move ke posisi next color box

    return img


def textWithBackground(img, text, font, fontScale, textPos,
                       textThickness=1, textColor=(0, 255, 0),
                       bgColor=(0, 0, 0), pad_x=3, pad_y=3, bgOpacity=0.5):
    """
    Render text dengan semi-transparent background untuk better readability.

    Menggambar text dengan background box yang semi-transparent,
    membuat text lebih mudah dibaca di atas background yang kompleks.

    Args:
        img (np.ndarray): Input image
        text (str): Text yang akan digambar
        font: OpenCV font type (e.g., cv.FONT_HERSHEY_SIMPLEX)
        fontScale (float): Font scale factor
        textPos (tuple): Text position (x, y)
        textThickness (int): Thickness dari text
        textColor (tuple): Color untuk text (BGR)
        bgColor (tuple): Color untuk background box (BGR)
        pad_x (int): Horizontal padding untuk background box
        pad_y (int): Vertical padding untuk background box
        bgOpacity (float): Opacity dari background (0-1)

    Returns:
        np.ndarray: Image dengan text dan background yang digambar

    Example:
        >>> img = textWithBackground(img, "Hello", cv.FONT_HERSHEY_SIMPLEX,
        ...                          1.0, (50, 50), textColor=WHITE)
    """
    # Hitung ukuran text untuk menentukan ukuran background box
    (t_w, t_h), _ = cv.getTextSize(text, font, fontScale, textThickness)
    x, y = textPos

    # Buat overlay untuk semi-transparent background
    overlay = img.copy()

    # Gambar background rectangle pada overlay
    cv.rectangle(
        overlay,
        (x - pad_x, y + pad_y),
        (x + t_w + pad_x, y - t_h - pad_y),
        bgColor, -1
    )

    # Blend overlay dengan original image untuk transparency effect
    img = cv.addWeighted(overlay, bgOpacity, img, 1 - bgOpacity, 0)

    # Gambar text di atas background
    cv.putText(img, text, textPos, font, fontScale, textColor, textThickness)

    return img


def textBlurBackground(img, text, font, fontScale, textPos,
                       textThickness=1, textColor=(0, 255, 0),
                       kernel=(33, 33), pad_x=3, pad_y=3):
    """
    Render text dengan blurred background untuk aesthetic effect.

    Menggambar text dengan background yang di-blur, memberikan
    depth-of-field effect yang menarik secara visual.

    Args:
        img (np.ndarray): Input image
        text (str): Text yang akan digambar
        font: OpenCV font type
        fontScale (float): Font scale factor
        textPos (tuple): Text position (x, y)
        textThickness (int): Thickness dari text
        textColor (tuple): Color untuk text (BGR)
        kernel (tuple): Blur kernel size (width, height) - harus odd numbers
        pad_x (int): Horizontal padding untuk blur region
        pad_y (int): Vertical padding untuk blur region

    Returns:
        np.ndarray: Image dengan text dan blurred background

    Example:
        >>> img = textBlurBackground(img, "Gaze: Center",
        ...                          cv.FONT_HERSHEY_SIMPLEX,
        ...                          1.0, (50, 50))
    """
    # Hitung ukuran text
    (t_w, t_h), _ = cv.getTextSize(text, font, fontScale, textThickness)
    x, y = textPos
    h, w = img.shape[:2]

    # Calculate ROI (Region of Interest) bounds dengan boundary check
    x1 = max(0, x - pad_x)
    y1 = max(0, y - t_h - pad_y)
    x2 = min(w, x + t_w + pad_x)
    y2 = min(h, y + pad_y)

    # Extract ROI dan apply blur
    roi = img[y1:y2, x1:x2]
    img[y1:y2, x1:x2] = cv.blur(roi, kernel)

    # Gambar text di atas blurred region
    cv.putText(img, text, textPos, font, fontScale, textColor, textThickness)

    return img


def fillPolyTrans(img, points, color, opacity):
    """
    Fill polygon dengan transparency dan outline.

    Menggambar filled polygon dengan semi-transparent fill dan
    solid outline, berguna untuk highlight regions seperti eye boundaries.

    Args:
        img (np.ndarray): Input image
        points (list): List of (x, y) points untuk polygon vertices
        color (tuple): Color untuk fill dan outline (BGR)
        opacity (float): Opacity dari fill (0-1)

    Returns:
        np.ndarray: Image dengan polygon yang digambar

    Example:
        >>> eye_points = [(100, 100), (120, 90), (140, 100), (120, 110)]
        >>> img = fillPolyTrans(img, eye_points, GREEN, 0.3)
    """
    # Buat overlay untuk transparency effect
    overlay = img.copy()

    # Convert points ke numpy array dengan proper dtype
    pts = np.array(points, dtype=np.int32)

    # Fill polygon pada overlay
    cv.fillPoly(overlay, [pts], color)

    # Blend overlay dengan original image
    img = cv.addWeighted(overlay, opacity, img, 1 - opacity, 0)

    # Gambar polygon outline dengan anti-aliasing
    cv.polylines(img, [pts], True, color, 1, cv.LINE_AA)

    return img


def rectTrans(img, pt1, pt2, color, thickness, opacity):
    """
    Draw rectangle dengan transparency.

    Menggambar rectangle dengan semi-transparent fill/stroke,
    berguna untuk bounding boxes atau region highlights.

    Args:
        img (np.ndarray): Input image
        pt1 (tuple): Top-left corner (x, y)
        pt2 (tuple): Bottom-right corner (x, y)
        color (tuple): Color untuk rectangle (BGR)
        thickness (int): Line thickness (-1 untuk filled)
        opacity (float): Opacity dari rectangle (0-1)

    Returns:
        np.ndarray: Image dengan rectangle yang digambar

    Example:
        >>> img = rectTrans(img, (50, 50), (200, 150), RED, 2, 0.5)
    """
    # Buat overlay untuk transparency effect
    overlay = img.copy()

    # Gambar rectangle pada overlay
    cv.rectangle(overlay, pt1, pt2, color, thickness)

    # Blend overlay dengan original image untuk transparency
    img = cv.addWeighted(overlay, opacity, img, 1 - opacity, 0)

    return img
