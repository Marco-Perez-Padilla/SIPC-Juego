# Proyecto: Practica Juego

Este repositorio contiene los scripts del juego usando **MediaPipe**, **Pymunk** y **Pygame** en Windows. Asimismo, tiene scripts que muestran el desarrollo continuo del juego, así como del control por mano de forma independiente.
**Nota**: No se incluye el entorno virtual `env-sipc-11` en el repositorio. Cada colaborador debe crearlo localmente.

---

## Descripción del juego

El juego principal se encuentra implementado en el archivo:

- **`laberinth_game_with_hands.py`**

El objetivo del juego es **recolectar tres llaves dentro de un laberinto** sin tocar las paredes.  
Si el jugador entra en contacto con alguna pared del laberinto, **la partida se pierde automáticamente**.

---

## Sistema de control

El control del personaje se realiza mediante **seguimiento de la mano**, utilizando **MediaPipe**:

- Se detecta la posición del **dedo índice** de la mano.
- El movimiento del jugador dentro del laberinto depende directamente de la posición del dedo índice captada por la cámara.
- No se utilizan teclado ni ratón; todo el control es **por gestos de la mano**.

---

## Requisitos

- Windows 10 o superior
- Python 3.11.9 (64-bit)
- Git (opcional, para clonar el repo)

---

## Configuración del entorno

1. Instalar Python 3.11.9 (64-bit) 
   Descárgalo desde [Python oficial](https://www.python.org/downloads/release/python-3119/)  
   Asegúrate de marcar **Add Python to PATH** durante la instalación.

2. Abrir PowerShell y navegar a la carpeta del proyecto:

```powershell
cd C:\ruta\del\proyecto
```

3. Crear un entorno virtual
```powershell
py -3.11 -m venv env-sipc-11
```

4. Activar el entorno virtual
```powershell
env-sipc-11\Scripts\Activate.ps1
```

5. Actualizar pip
```powershell
python -m pip install --upgrade pip
```

6. Instalar las librerías necesarias
```powershell
pip install mediapipe pymunk pygame opencv-python
```

## Ejecución del juego

1. Con el entorno virtual activado, ejecutar el juego principal:
```powershell
python laberinth_game_with_hands.py
```

2. Asegúrate de tener la cámara encendida y visible.

3. Mueve el dedo índice frente a la cámara para controlar al jugador dentro del laberinto.
