import cv2
import time
import mediapipe as mp
import hand_force_application as hf

cap = cv2.VideoCapture(0)

options = hf.HandLandmarkerOptions(
    base_options=hf.BaseOptions(model_asset_path=hf.model_path),
    running_mode=hf.VisionRunningMode.LIVE_STREAM,
    result_callback=hf.get_result
)

with hf.HandLandmarker.create_from_options(options) as landmarker:
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            continue

        frame = cv2.flip(frame, 1)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame 
        )

        landmarker.detect_async(
            mp_image,
            int(time.time() * 1000)
        )

        center = (hf.SCREEN_WIDTH // 2, hf.SCREEN_HEIGHT // 2)

        # Centro
        cv2.circle(frame, center, 5, (0, 255, 0), -1)

        # Fuerza
        fx, fy = hf.get_player_force()
        end = (
            int(center[0] + fx * 0.1),
            int(center[1] + fy * 0.1)
        )

        cv2.arrowedLine(frame, center, end, (0, 0, 255), 4)

        cv2.putText(
            frame,
            f"Force: ({int(fx)}, {int(fy)})",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 0),
            2
        )

        if hf.detection_result:
            frame = hf.draw_landmarks_on_image(frame, hf.detection_result)

        cv2.imshow("Hand Control Test", frame)

        if cv2.waitKey(5) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()