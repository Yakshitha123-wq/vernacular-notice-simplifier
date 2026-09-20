import io

import numpy as np
from PIL import Image, ImageOps

MAX_DIMENSION = 2400
MIN_DIMENSION = 1000
THRESHOLD_BLOCK = 32
THRESHOLD_K = 0.15


def preprocess_image(image_bytes):
    image = Image.open(io.BytesIO(image_bytes))
    original_format = image.format
    image = _normalize_and_scale(image)
    image = _deskew(image)
    binary = _adaptive_threshold(image)
    output = io.BytesIO()
    binary.save(output, format="PNG")
    return output.getvalue(), original_format


def _normalize_and_scale(image):
    if image.mode != "L":
        image = image.convert("L")
    width, height = image.size
    scale = 1.0
    if max(width, height) > MAX_DIMENSION:
        scale = MAX_DIMENSION / max(width, height)
    elif min(width, height) < MIN_DIMENSION:
        scale = MIN_DIMENSION / min(width, height)
    if scale != 1.0:
        image = image.resize((int(width * scale), int(height * scale)), Image.LANCZOS)
    return ImageOps.autocontrast(image, cutoff=1)


def _deskew(image):
    try:
        import cv2

        array = np.array(image)
        edges = cv2.Canny(array, 50, 150)
        lines = cv2.HoughLinesP(
            edges, 1, np.pi / 180, threshold=120, minLineLength=image.width, maxLineGap=20
        )
        if lines is None:
            return image
        angles = []
        for line in lines[:, 0]:
            x1, y1, x2, y2 = line
            if abs(x2 - x1) < 1e-6:
                continue
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            if angle < -45:
                angle += 90
            elif angle > 45:
                angle -= 90
            if abs(angle) > 5:
                continue
            angles.append(angle)
        if not angles:
            return image
        median_angle = float(np.median(angles))
        if abs(median_angle) < 0.3:
            return image
        height, width = array.shape
        center = (width / 2, height / 2)
        matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        rotated = cv2.warpAffine(
            array,
            matrix,
            (width, height),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )
        return Image.fromarray(rotated)
    except ImportError:
        return image


def _integral_table(array):
    table = np.zeros((array.shape[0] + 1, array.shape[1] + 1), dtype=np.float64)
    np.cumsum(array, axis=0, out=table[1:, 1:])
    np.cumsum(table[1:, 1:], axis=1, out=table[1:, 1:])
    return table


def _adaptive_threshold(image):
    array = np.array(image, dtype=np.float64)
    height, width = array.shape
    int_img = _integral_table(array)
    int_sq = _integral_table(array * array)

    binary = np.zeros_like(array, dtype=np.uint8)
    block = THRESHOLD_BLOCK
    for top in range(0, height, block):
        bottom = min(top + block, height)
        for left in range(0, width, block):
            right = min(left + block, width)
            area = (bottom - top) * (right - left)
            if area == 0:
                continue
            total = (
                int_img[bottom, right]
                - int_img[top, right]
                - int_img[bottom, left]
                + int_img[top, left]
            )
            sq_total = (
                int_sq[bottom, right]
                - int_sq[top, right]
                - int_sq[bottom, left]
                + int_sq[top, left]
            )
            mean = total / area
            variance = max(sq_total / area - mean * mean, 0.0)
            stddev = variance ** 0.5
            threshold = mean * (1 - THRESHOLD_K) + 0.15 * stddev
            block_img = array[top:bottom, left:right]
            binary[top:bottom, left:right][block_img >= threshold] = 255
    return Image.fromarray(binary)