import cv2
import time
import serial
import json
import os
import numpy as np
from collections import deque
from ultralytics import YOLO

# ==========================================
# 1. CONFIGURACIÓN DEL SISTEMA
# ==========================================

Y_LIMITE_SUP = 90   
Y_LIMITE_INF = 400  
X_CINTA_IZQ = 100
X_CINTA_DER = 540

DISTANCIAS = {
    "1": 0.20,  "2": 0.20,  "3": 0.45,  "4": 0.45
}

VELOCIDAD_CINTA = 0.70 / 10.0   
TIEMPO_ANTICIPACION = 2.5
TIEMPO_COOLDOWN = 5.0    
ARDUINO_PORT = '/dev/ttyUSB0' 
BAUDRATE = 115200 

MODEL_PATH = "/home/pi/Desktop/Deteccion/Modelos/best_ncnn_model"

# ---> CARGAR MAPEO DE SERVOS <---
mapping_path = "/home/pi/Desktop/Deteccion/Modelos/servo_mapping.json"
mapa_categorias = {}
if os.path.exists(mapping_path):
    with open(mapping_path, "r") as f:
        raw_mapa = json.load(f)
        # Normalizar a minúsculas
        mapa_categorias = {k.lower(): str(v) for k, v in raw_mapa.items()}
    print(f"Mapeo de hardware cargado con exito: {mapa_categorias}")

# ==========================================
# 2. INICIALIZACIÓN
# ==========================================
print(f"--- CLASIFICADOR INICIADO ---")

try:
    model = YOLO(MODEL_PATH, task='detect') 
except Exception as e:
    print(f"ERROR: No se pudo cargar el modelo. {e}")
    exit()

cap = cv2.VideoCapture(0)
cap.set(3, 640) 
cap.set(4, 480)

arduino = None
try:
    arduino = serial.Serial(ARDUINO_PORT, BAUDRATE, timeout=1)
    time.sleep(7) 
    print(f"Arduino CONECTADO en {ARDUINO_PORT}")
except:
    print("AVISO: Arduino NO conectado. Modo SIMULACIÓN.")

cola_eventos = deque()
ultimas_detecciones = {} 

# ==========================================
# 3. BUCLE PRINCIPAL
# ==========================================
try:
    while True:
        ret, frame = cap.read()
        if not ret: break

        current_time = time.time()
        
        cv2.line(frame, (0, Y_LIMITE_SUP), (640, Y_LIMITE_SUP), (0, 255, 0), 2)
        cv2.line(frame, (0, Y_LIMITE_INF), (640, Y_LIMITE_INF), (0, 255, 0), 1)
        
        # Confianza relajada a 0.45 
        results = model(frame, verbose=False, conf=0.45)

        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2 
                
                cls_id = int(box.cls[0])
                if hasattr(model, 'names'):
                    nombre = model.names[cls_id].lower()
                else:
                    nombre = str(cls_id)

                # SIEMPRE DIBUJAR LA CAJA (incluso si no esta en la zona verde)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{nombre} {box.conf[0]:.2f}", (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

                en_cinta = (cx > X_CINTA_IZQ) and (cx < X_CINTA_DER)
                en_zona  = (cy > Y_LIMITE_SUP) and (cy < Y_LIMITE_INF)

                if en_cinta and en_zona:
                    servo_id_str = str(mapa_categorias.get(nombre, ""))
                    
                    if servo_id_str in ['1', '2', '3', '4']:
                        ultimo = ultimas_detecciones.get(nombre, 0)
                        
                        if (current_time - ultimo) > TIEMPO_COOLDOWN:
                            dist = DISTANCIAS.get(servo_id_str, 0.30)
                            t_viaje = dist / VELOCIDAD_CINTA
                            
                            t_programado = current_time + t_viaje - TIEMPO_ANTICIPACION
                            if t_programado < current_time:
                                t_programado = current_time
                            
                            cola_eventos.append({
                                "letra": servo_id_str,
                                "tiempo": t_programado,
                                "nombre": nombre
                            })
                            
                            ultimas_detecciones[nombre] = current_time
                            print(f">>> [ZONA] {nombre}. Activa Servo {servo_id_str}. Tiempo viaje restante: {t_viaje - TIEMPO_ANTICIPACION:.2f}s")
                            
        while cola_eventos:
            evento = cola_eventos[0]
            if current_time >= evento["tiempo"]:
                cola_eventos.popleft()
                if arduino and arduino.is_open:
                    try:
                        arduino.write(f"{evento['letra']}\n".encode('utf-8'))
                        print(f"Tx Arduino: {evento['letra']}")
                    except Exception as e:
                        print(f"Error Serial: {e}")
            else:
                break

        cv2.imshow("Clasificador Final", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    pass
finally:
    cap.release()
    cv2.destroyAllWindows()
    if arduino: arduino.close()
