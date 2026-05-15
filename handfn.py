"""All three triggers use captured-pose templates: left=Fn hold, right=Enter tap, right=Delete tap."""
from __future__ import annotations

import json
import os
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
from Quartz import (
    CGEventCreateKeyboardEvent,
    CGEventPost,
    CGEventSetFlags,
    kCGEventFlagMaskSecondaryFn,
    kCGHIDEventTap,
)

KEY_FN = 0x3F      # kVK_Function
KEY_RETURN = 0x24  # kVK_Return
KEY_DELETE = 0x33  # kVK_Delete (backspace)
MODEL_PATH = "models/hand_landmarker.task"
LEFT_TEMPLATE_PATH = "left_gesture.json"
ENTER_TEMPLATE_PATH = "enter_gesture.json"
DELETE_TEMPLATE_PATH = "delete_gesture.json"
CAM_INDEX = 0
PRESS_FRAMES = 2
RELEASE_FRAMES = 5


def press_fn() -> None:
    e = CGEventCreateKeyboardEvent(None, KEY_FN, True)
    CGEventSetFlags(e, kCGEventFlagMaskSecondaryFn)
    CGEventPost(kCGHIDEventTap, e)


def release_fn() -> None:
    e = CGEventCreateKeyboardEvent(None, KEY_FN, False)
    CGEventPost(kCGHIDEventTap, e)


def _tap(keycode: int) -> None:
    CGEventPost(kCGHIDEventTap, CGEventCreateKeyboardEvent(None, keycode, True))
    CGEventPost(kCGHIDEventTap, CGEventCreateKeyboardEvent(None, keycode, False))


def tap_enter() -> None:
    _tap(KEY_RETURN)


def tap_delete() -> None:
    _tap(KEY_DELETE)


def _normalize(landmarks) -> np.ndarray:
    pts = np.array([[lm.x, lm.y, lm.z] for lm in landmarks], dtype=np.float32)
    pts -= pts[0]
    scale = float(np.linalg.norm(pts[9]))
    if scale < 1e-6:
        scale = 1.0
    return pts / scale


def _load_template(path: str):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        data = json.load(f)
    return np.array(data["landmarks"], dtype=np.float32), float(data["threshold"])


def matches_template(landmarks, template_pts: np.ndarray, threshold: float) -> bool:
    norm = _normalize(landmarks)
    dist = float(np.mean(np.linalg.norm(norm - template_pts, axis=1)))
    return dist < threshold


def _find_hand(result, label: str):
    for i, hand in enumerate(result.handedness):
        if hand and hand[0].category_name == label:
            return result.hand_landmarks[i]
    return None


def main() -> int:
    detector = HandLandmarker.create_from_options(
        HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=MODEL_PATH),
            num_hands=2,
            running_mode=RunningMode.VIDEO,
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.7,
            min_tracking_confidence=0.6,
        )
    )
    cap = cv2.VideoCapture(CAM_INDEX)
    if not cap.isOpened():
        print("error: cannot open camera", file=sys.stderr)
        return 1

    left_tpl = _load_template(LEFT_TEMPLATE_PATH)
    enter_tpl = _load_template(ENTER_TEMPLATE_PATH)
    delete_tpl = _load_template(DELETE_TEMPLATE_PATH)
    missing = []
    if left_tpl is None:
        missing.append("left_gesture.json (run: .venv/bin/python capture.py left)")
    if enter_tpl is None:
        missing.append("enter_gesture.json (run: .venv/bin/python capture.py enter)")
    if delete_tpl is None:
        missing.append("delete_gesture.json (run: .venv/bin/python capture.py delete)")
    if missing:
        for m in missing:
            print(f"error: missing {m}", file=sys.stderr)
        cap.release()
        detector.close()
        return 1

    fn_seen = fn_missed = 0
    fn_held = False
    thumb_seen = thumb_missed = 0
    thumb_armed = True  # ready to fire next Enter tap
    ropen_seen = ropen_missed = 0
    ropen_armed = True  # ready to fire next Delete tap

    t0 = time.time()
    print("running — left captured=Fn hold | right enter-pose=Enter | right delete-pose=Delete (Ctrl-C to quit)")

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                continue
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            ts_ms = int((time.time() - t0) * 1000)
            result = detector.detect_for_video(mp_image, ts_ms)

            left = _find_hand(result, "Left")
            right = _find_hand(result, "Right")

            # left hand → Fn hold (captured template only)
            left_active = left is not None and matches_template(left, *left_tpl)
            if left_active:
                fn_seen += 1
                fn_missed = 0
                if not fn_held and fn_seen >= PRESS_FRAMES:
                    press_fn()
                    fn_held = True
                    print("Fn down")
            else:
                fn_missed += 1
                fn_seen = 0
                if fn_held and fn_missed >= RELEASE_FRAMES:
                    release_fn()
                    fn_held = False
                    print("Fn up")

            # right hand → Enter tap on rising edge of captured pose
            if right is not None and matches_template(right, *enter_tpl):
                thumb_seen += 1
                thumb_missed = 0
                if thumb_armed and thumb_seen >= PRESS_FRAMES:
                    tap_enter()
                    thumb_armed = False
                    print("Enter tap")
            else:
                thumb_missed += 1
                thumb_seen = 0
                if not thumb_armed and thumb_missed >= RELEASE_FRAMES:
                    thumb_armed = True

            # right hand → Delete tap on rising edge of captured Delete pose
            if right is not None and matches_template(right, *delete_tpl):
                ropen_seen += 1
                ropen_missed = 0
                if ropen_armed and ropen_seen >= PRESS_FRAMES:
                    tap_delete()
                    ropen_armed = False
                    print("Delete tap")
            else:
                ropen_missed += 1
                ropen_seen = 0
                if not ropen_armed and ropen_missed >= RELEASE_FRAMES:
                    ropen_armed = True
    except KeyboardInterrupt:
        pass
    finally:
        if fn_held:
            release_fn()
        cap.release()
        detector.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
