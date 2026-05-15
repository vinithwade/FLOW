"""Capture a gesture template for handfn.

Usage:
    .venv/bin/python capture.py left     # left-hand pose for Fn hold
    .venv/bin/python capture.py enter    # right-hand pose for Enter tap
    .venv/bin/python capture.py delete   # right-hand pose for Delete tap
"""
from __future__ import annotations

import json
import sys
import time

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    HandLandmarker,
    HandLandmarkerOptions,
    RunningMode,
)

MODEL_PATH = "models/hand_landmarker.task"
CAM_INDEX = 0
COUNTDOWN_SEC = 5
CAPTURE_SEC = 7

ACTIONS = {
    "left":   {"hand": "Left",  "output": "left_gesture.json",   "label": "left-hand (Fn hold)"},
    "enter":  {"hand": "Right", "output": "enter_gesture.json",  "label": "right-hand (Enter tap)"},
    "delete": {"hand": "Right", "output": "delete_gesture.json", "label": "right-hand (Delete tap)"},
}


def normalize(landmarks) -> np.ndarray:
    pts = np.array([[lm.x, lm.y, lm.z] for lm in landmarks], dtype=np.float32)
    pts -= pts[0]
    scale = float(np.linalg.norm(pts[9]))
    if scale < 1e-6:
        scale = 1.0
    return pts / scale


def find_hand(result, label: str):
    for i, hand in enumerate(result.handedness):
        if hand and hand[0].category_name == label:
            return result.hand_landmarks[i]
    return None


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in ACTIONS:
        print(f"usage: capture.py <{'|'.join(ACTIONS)}>", file=sys.stderr)
        return 2
    cfg = ACTIONS[sys.argv[1]]
    hand_label = cfg["hand"]
    output = cfg["output"]

    detector = HandLandmarker.create_from_options(
        HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=MODEL_PATH),
            num_hands=2,
            running_mode=RunningMode.VIDEO,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
    )
    cap = cv2.VideoCapture(CAM_INDEX)
    if not cap.isOpened():
        print("error: cannot open camera", file=sys.stderr)
        return 1

    for _ in range(5):
        cap.read()

    print(f"Get your {cfg['label']} pose ready")
    for c in range(COUNTDOWN_SEC, 0, -1):
        print(f"{c}...")
        time.sleep(1)
    print(f"CAPTURING for {CAPTURE_SEC}s — hold the pose")

    samples = []
    t0 = time.time()
    t_end = t0 + CAPTURE_SEC
    last_progress = -1.0
    while time.time() < t_end:
        ok, frame = cap.read()
        if not ok:
            continue
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        elapsed = time.time() - t0
        ts_ms = int(elapsed * 1000)
        result = detector.detect_for_video(mp_image, ts_ms)
        hand = find_hand(result, hand_label)
        if hand is not None:
            samples.append(normalize(hand))
        if int(elapsed) != int(last_progress):
            print(f"  t={int(elapsed)+1}s  frames_with_{hand_label.lower()}={len(samples)}")
            last_progress = elapsed

    cap.release()
    detector.close()

    if len(samples) < 10:
        print(
            f"error: only {len(samples)} frames had a {hand_label} hand — try again, keep it clearly in view",
            file=sys.stderr,
        )
        return 1

    arr = np.stack(samples)
    template = arr.mean(axis=0)
    per_frame_dist = np.mean(np.linalg.norm(arr - template, axis=2), axis=1)
    self_mean = float(per_frame_dist.mean())
    self_std = float(per_frame_dist.std())
    threshold = max(0.10, self_mean + 1.2 * self_std)

    with open(output, "w") as f:
        json.dump({"landmarks": template.tolist(), "threshold": threshold}, f, indent=2)

    print(f"DONE — {len(samples)} frames, self_mean={self_mean:.3f}, threshold={threshold:.3f}")
    print(f"saved to {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
