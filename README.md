# Proyecto: Practica Juego

Este repositorio contiene los scripts del juego usando **MediaPipe**, **Pymunk** y **Pygame** en Windows.
**Nota**: No se incluye el entorno virtual `env-sipc-11` en el repositorio. Cada colaborador debe crearlo localmente.

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

## Ejecución de los scripts

1. Con el entorno virtual activado, ejecutar cualquier script con:
```powershell
python nombre_del_script.py
```
