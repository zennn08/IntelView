import cv2 as cv
import numpy as np

# ================= COLORS (BGR) =================
BLACK = (0,0,0)
WHITE = (255,255,255)
BLUE = (255,0,0)
RED = (0,0,255)
CYAN = (255,255,0)
YELLOW = (0,255,255)
MAGENTA = (255,0,255)
GRAY = (128,128,128)
GREEN = (0,255,0)
PURPLE = (128,0,128)
ORANGE = (0,165,255)
PINK = (147,20,255)

# ================= DRAW UTILS =================

def drawColor(img, colors, start=(10,10)):
    x, y = start
    w, h = 20, 30
    for color in colors:
        cv.rectangle(img, (x-6, y-5), (x+w+5, y+h+5), (10,50,10), -1)
        cv.rectangle(img, (x, y), (x+w, y+h), color, -1)
        x += w + 8
    return img

def textWithBackground(img, text, font, fontScale, textPos,
                       textThickness=1, textColor=(0,255,0),
                       bgColor=(0,0,0), pad_x=3, pad_y=3, bgOpacity=0.5):

    (t_w, t_h), _ = cv.getTextSize(text, font, fontScale, textThickness)
    x, y = textPos
    overlay = img.copy()
    cv.rectangle(
        overlay,
        (x-pad_x, y+pad_y),
        (x+t_w+pad_x, y-t_h-pad_y),
        bgColor, -1
    )
    img = cv.addWeighted(overlay, bgOpacity, img, 1-bgOpacity, 0)
    cv.putText(img, text, textPos, font, fontScale, textColor, textThickness)
    return img

def textBlurBackground(img, text, font, fontScale, textPos,
                       textThickness=1, textColor=(0,255,0),
                       kernel=(33,33), pad_x=3, pad_y=3):

    (t_w, t_h), _ = cv.getTextSize(text, font, fontScale, textThickness)
    x, y = textPos
    h, w = img.shape[:2]

    x1 = max(0, x - pad_x)
    y1 = max(0, y - t_h - pad_y)
    x2 = min(w, x + t_w + pad_x)
    y2 = min(h, y + pad_y)

    roi = img[y1:y2, x1:x2]
    img[y1:y2, x1:x2] = cv.blur(roi, kernel)
    cv.putText(img, text, textPos, font, fontScale, textColor, textThickness)
    return img

def fillPolyTrans(img, points, color, opacity):
    overlay = img.copy()
    pts = np.array(points, dtype=np.int32)
    cv.fillPoly(overlay, [pts], color)
    img = cv.addWeighted(overlay, opacity, img, 1-opacity, 0)
    cv.polylines(img, [pts], True, color, 1, cv.LINE_AA)
    return img

def rectTrans(img, pt1, pt2, color, thickness, opacity):
    overlay = img.copy()
    cv.rectangle(overlay, pt1, pt2, color, thickness)
    img = cv.addWeighted(overlay, opacity, img, 1-opacity, 0)
    return img
