import cv2

# Abrir la cámara (0 = cámara por defecto)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("No se pudo abrir la cámara")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("No se pudo leer el frame")
        break

    # Mostrar la imagen en una ventana
    frame = cv2.flip(frame, 1) # 1 = horizontal, 0 = vertical, -1 = ambas
    
    cv2.imshow("Webcam", frame)

    # Salir si presionas 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
