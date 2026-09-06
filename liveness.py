"""
liveness.py
------------
Lightweight "liveness" check for SmartBus's face scanner.

DESIGN DECISION (documented honestly for the project write-up):
Real anti-spoofing (detecting a printed photo or a phone/video held up
to the camera) is a genuinely hard problem that production biometric
systems solve with dedicated INFRARED (IR) cameras — IR can tell live
skin apart from paper/screens by how it reflects/absorbs infrared
light, which a regular RGB webcam physically cannot do.

For SmartBus's use case (a bus fare system, not a bank vault) and its
hardware (a standard webcam, no IR sensor), attempting strict photo/
video spoof detection with only Haar cascades produces an unreliable,
frustrating experience without real security to show for it — Haar
eye-box geometry does not vary meaningfully between "real eye" and
"photo of an eye" at webcam resolution. It just makes the demo fragile.

So this module intentionally does a SIMPLE, PRACTICAL check instead:
confirms a face is actually present and trackable for a brief moment
before accepting a scan, mainly to filter out false triggers (motion
blur, partial faces, empty frames) — not to defeat a determined spoof
attempt. That's an honest, correctly-scoped feature for this project.

FOR A REAL DEPLOYMENT: swap this module for one that reads frames from
an IR/depth camera (e.g. Intel RealSense, or a dedicated IR liveness
module) and checks the IR reflectance signature of live skin. That is
the practical, industry-standard way to solve this — not more Haar
cascade tuning on a regular webcam.

Usage:
    from liveness import run_liveness_check

    is_live, reason = run_liveness_check(camera, face_detector)
    if not is_live:
        # reject the scan, show `reason` to the user
"""

import cv2
import time

# ---------------- Tunable settings ----------------

REQUIRED_STABLE_FRAMES = 8        # consecutive frames a face must be visible
MAX_CONSECUTIVE_MISSES = 4
LIVENESS_TIMEOUT_SECONDS = 12      # generous, but won't hang a presentation


def run_liveness_check(camera, face_detector, eye_cascade=None, status_callback=None):
    """
    Confirms a real, trackable face is present in front of the camera
    for a short, continuous stretch of frames before accepting a scan.

    `eye_cascade` is accepted for backward compatibility with older
    call sites but is not required/used — kept as an optional param so
    existing calls in mainGUI.py don't need to change.

    Returns (is_live: bool, reason: str).
    """

    def report(msg):
        if status_callback:
            status_callback(msg)

    start_time = time.time()
    stable_frames = 0
    consecutive_misses = 0

    while True:
        elapsed = time.time() - start_time
        if elapsed > LIVENESS_TIMEOUT_SECONDS:
            cv2.destroyWindow("SmartBus - Liveness Check")
            return False, "No face detected in time. Please position your face in the camera and try again."

        success, frame = camera.read()
        if not success:
            cv2.destroyWindow("SmartBus - Liveness Check")
            return False, "Camera read failed during liveness check."

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(70, 70))

        display_frame = frame.copy()

        if len(faces) > 0:
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 200, 255), 2)
            stable_frames += 1
            consecutive_misses = 0
        else:
            consecutive_misses += 1
            if consecutive_misses > MAX_CONSECUTIVE_MISSES:
                stable_frames = 0
                consecutive_misses = 0

        instruction = f"Hold still... ({stable_frames}/{REQUIRED_STABLE_FRAMES})"
        cv2.putText(display_frame, instruction, (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)

        cv2.imshow("SmartBus - Liveness Check", display_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            cv2.destroyWindow("SmartBus - Liveness Check")
            return False, "Liveness check cancelled."

        if stable_frames >= REQUIRED_STABLE_FRAMES:
            break

    cv2.destroyWindow("SmartBus - Liveness Check")
    report("Face presence confirmed.")
    return True, "Face detected and confirmed."