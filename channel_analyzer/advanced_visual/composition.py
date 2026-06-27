"""OpenCV-based composition and subject analysis."""

from __future__ import annotations

import cv2
import numpy as np

from channel_analyzer.advanced_visual.models import COMPOSITION_TYPES


def detect_faces(gray: np.ndarray) -> list[tuple[int, int, int, int]]:
    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    faces = cascade.detectMultiScale(gray, 1.1, 4, minSize=(24, 24))
    return [tuple(int(v) for v in f) for f in faces]


def subject_bbox(
    frame: np.ndarray, faces: list[tuple[int, int, int, int]]
) -> tuple[int, int, int, int] | None:
    """Estimate subject bounding box from faces or saliency fallback."""
    h, w = frame.shape[:2]
    if faces:
        xs = [f[0] for f in faces]
        ys = [f[1] for f in faces]
        x2 = [f[0] + f[2] for f in faces]
        y2 = [f[1] + f[3] for f in faces]
        pad_x = int(0.6 * max(f[2] for f in faces))
        pad_y = int(1.2 * max(f[3] for f in faces))
        x1 = max(0, min(xs) - pad_x)
        y1 = max(0, min(ys) - pad_y)
        x2v = min(w, max(x2) + pad_x)
        y2v = min(h, max(y2) + pad_y)
        return (x1, y1, x2v - x1, y2v - y1)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 40, 120)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    largest = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest)
    if area < (w * h * 0.005):
        return None
    return cv2.boundingRect(largest)


def negative_space_percent(frame: np.ndarray) -> float:
    """Estimate negative space via low-detail / dark uniform regions."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    # Low gradient + dark or mid-uniform areas
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    gradient = np.sqrt(gx**2 + gy**2)
    low_detail = gradient < 12
    dark = gray < 80
    neg = low_detail | dark
    return float(np.mean(neg) * 100)


def analyze_composition(
    frame: np.ndarray,
    faces: list[tuple[int, int, int, int]],
) -> tuple[str, float, float, float]:
    """
    Return (composition_type, confidence, negative_space_pct, subject_scale_pct).
    """
    h, w = frame.shape[:2]
    neg_pct = negative_space_percent(frame)
    bbox = subject_bbox(frame, faces)

    if bbox is None:
        if neg_pct > 55:
            return "tiny_human_large_world", 0.55, neg_pct, 0.0
        return "full_frame_subject", 0.4, neg_pct, 50.0

    x, y, bw, bh = bbox
    scale_pct = (bw * bh) / (w * h) * 100
    cx = x + bw / 2
    cy = y + bh / 2
    center_dist = np.sqrt((cx - w / 2) ** 2 + (cy - h / 2) ** 2)
    max_dist = np.sqrt((w / 2) ** 2 + (h / 2) ** 2)
    centrality = 1 - (center_dist / max_dist)

    edge_margin = min(x, y, w - (x + bw), h - (y + bh))
    edge_ratio = edge_margin / min(w, h)

    if scale_pct < 8 and neg_pct > 45:
        return "tiny_human_large_world", min(0.95, 0.6 + neg_pct / 200), neg_pct, scale_pct
    if edge_ratio < 0.08:
        return "edge_subject", 0.7, neg_pct, scale_pct
    if centrality > 0.65:
        return "centered_subject", 0.75, neg_pct, scale_pct
    return "full_frame_subject", 0.6, neg_pct, scale_pct


def infer_relationship_heuristic(
    faces: list[tuple[int, int, int, int]], frame_shape: tuple[int, int, int]
) -> tuple[str, float]:
    h, w = frame_shape[:2]
    n = len(faces)
    if n == 0:
        return "alone", 0.7
    if n == 1:
        return "alone", 0.85
    if n >= 2:
        f1, f2 = faces[0], faces[1]
        c1 = (f1[0] + f1[2] / 2, f1[1] + f1[3] / 2)
        c2 = (f2[0] + f2[2] / 2, f2[1] + f2[3] / 2)
        dist = np.sqrt((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2)
        if dist < w * 0.25:
            return "couple", 0.65
        if dist > w * 0.45:
            return "separated_couple", 0.6
        return "looking_at_each_other", 0.5
    return "ambiguous", 0.3
