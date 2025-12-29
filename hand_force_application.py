import mediapipe as mp
import numpy as np
import cv2

model_path = 'hand_landmarker.task'

# Configuración de MediaPipe Tasks API
BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

detection_result = None

# Tamaño de la pantalla
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
DEAD_ZONE = 10
MAX_FORCE = 400
FORCE_SCALE = 250

# Suavizado
last_x, last_y = SCREEN_WIDTH//2, SCREEN_HEIGHT//2
SMOOTHING = 0.2

# Callback para obtener resultados
def get_result(result, output_image, timestamp_ms):
    global detection_result
    detection_result = result

# Función para dibujar landmarks
def draw_landmarks_on_image(rgb_image, detection_result):
    if detection_result is None or len(detection_result.hand_landmarks) == 0:
        return rgb_image
    
    annotated_image = np.copy(rgb_image)
    image_height, image_width, _ = annotated_image.shape
    
    for hand_landmarks in detection_result.hand_landmarks:
        # Dibujar puntos de referencia
        for landmark in hand_landmarks:
            x = int(landmark.x * image_width)
            y = int(landmark.y * image_height)
            cv2.circle(annotated_image, (x, y), 5, (0, 255, 0), -1)
        
        # Conexiones entre puntos 
        connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),        # Pulgar
            (0, 5), (5, 6), (6, 7), (7, 8),        # Índice
            (0, 9), (9, 10), (10, 11), (11, 12),   # Medio
            (0, 13), (13, 14), (14, 15), (15, 16), # Anular
            (0, 17), (17, 18), (18, 19), (19, 20), # Meñique
            (5, 9), (9, 13), (13, 17)              # Base de los dedos
        ]
        
        for start_idx, end_idx in connections:
            if start_idx < len(hand_landmarks) and end_idx < len(hand_landmarks):
                start_point = (
                    int(hand_landmarks[start_idx].x * image_width),
                    int(hand_landmarks[start_idx].y * image_height)
                )
                end_point = (
                    int(hand_landmarks[end_idx].x * image_width),
                    int(hand_landmarks[end_idx].y * image_height)
                )
                cv2.line(annotated_image, start_point, end_point, (255, 0, 0), 2)
    
    return annotated_image

# Función para calcular fuerza
def get_player_force():
    global last_x, last_y, detection_result

    if detection_result is None or len(detection_result.hand_landmarks) == 0:
        return 0, 0

    landmarks = detection_result.hand_landmarks[0]
    index_tip = landmarks[8]

    # Convertir coordenadas normalizadas a píxeles
    target_x = int(index_tip.x * SCREEN_WIDTH)
    target_y = int(index_tip.y * SCREEN_HEIGHT)

    # Suavizado
    smoothed_x = int(last_x + SMOOTHING * (target_x - last_x))
    smoothed_y = int(last_y + SMOOTHING * (target_y - last_y))
    last_x, last_y = smoothed_x, smoothed_y

    # Vector desde el centro
    dx = smoothed_x - SCREEN_WIDTH / 2
    dy = smoothed_y - SCREEN_HEIGHT / 2

    # Zona muerta
    if abs(dx) < DEAD_ZONE:
        dx = 0
    if abs(dy) < DEAD_ZONE:
        dy = 0

    # Fuerza proporcional
    force_x = dx / (SCREEN_WIDTH / 2) * FORCE_SCALE
    force_y = dy / (SCREEN_HEIGHT / 2) * FORCE_SCALE
    force_x = max(-MAX_FORCE, min(MAX_FORCE, force_x))
    force_y = max(-MAX_FORCE, min(MAX_FORCE, force_y))

    return force_x, force_y