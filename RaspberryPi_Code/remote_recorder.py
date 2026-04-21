import cv2
import time
import os
import sys

def record_background(duration=10, output_name="fondo_maestro.mp4"):
    print(f"[RECODER] Iniciando capturador remoto (Logitech)...")
    
    # Intentar abrir la camara (usualmente index 0 en RPi)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] No se pudo abrir la camara Logitech.")
        sys.exit(1)

    # Configuracion de resolucion estandar para optimizar velocidad
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # Codec estandar compatible
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_name, fourcc, 20.0, (640, 480))

    print(f"[RECODER] Grabando {duration} segundos de fondo...")
    start_time = time.time()
    
    frames_count = 0
    while int(time.time() - start_time) < duration:
        ret, frame = cap.read()
        if ret:
            out.write(frame)
            frames_count += 1
            if frames_count % 30 == 0:
                print(f"[RECODER] Progreso: {int(time.time() - start_time)}s / {duration}s")
        else:
            break

    cap.release()
    out.release()
    print(f"[RECODER] Grabacion finalizada. Archivo guardado: {output_name}")

if __name__ == "__main__":
    record_background()
