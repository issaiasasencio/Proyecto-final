import cv2
import time
import serial
import json
import os
import threading
from collections import deque
from ultralytics import YOLO

class ScannerEngine:
    def __init__(self, model_path, arduino_port='/dev/ttyUSB0', baudrate=115200):
        # Configuración de límites y parámetros
        self.Y_LIMITE_SUP = 90
        self.Y_LIMITE_INF = 400
        self.X_CINTA_IZQ = 100
        self.X_CINTA_DER = 540
        self.DISTANCIAS = {"1": 0.20, "2": 0.20, "3": 0.45, "4": 0.45}
        self.VELOCIDAD_CINTA = 0.70 / 10.0
        self.TIEMPO_ANTICIPACION = 2.5
        self.TIEMPO_COOLDOWN = 5.0
        
        self.model_path = model_path
        self.arduino_port = arduino_port
        self.baudrate = baudrate
        
        self.model = None
        self.arduino = None
        self.cap = None
        self.running = False
        
        self.cola_eventos = deque()
        self.ultimas_detecciones = {}
        self.status_msg = "Inicializando..."
        
        # Mapeo de categorías
        self.mapa_categorias = {}
        self.conf_threshold = 0.40

    def load_resources(self):
        try:
            self.model = YOLO(self.model_path, task='detect')
            self.status_msg = "Modelo cargado."
        except Exception as e:
            self.status_msg = f"Error Modelo: {e}"
            return False

        try:
            self.arduino = serial.Serial(self.arduino_port, self.baudrate, timeout=1)
            time.sleep(2) # Espera conexión
            self.status_msg = "Arduino conectado."
        except Exception:
            self.status_msg = "Arduino No detectado (Simulando)."
            
        return True

    def set_mapping(self, mapping_dict):
        self.mapa_categorias = {str(k).lower(): str(v) for k, v in mapping_dict.items()}

    def start(self, frame_callback):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._loop, args=(frame_callback,), daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=2)
        if self.cap:
            self.cap.release()
        if self.arduino:
            self.arduino.close()

    def _loop(self, frame_callback):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, 640)
        self.cap.set(4, 480)
        
        while self.running:
            ret, frame = self.cap.read()
            if not ret: break
            
            current_time = time.time()
            
            # Dibujar Guías
            cv2.line(frame, (0, self.Y_LIMITE_SUP), (640, self.Y_LIMITE_SUP), (0, 255, 0), 2)
            cv2.line(frame, (0, self.Y_LIMITE_INF), (640, self.Y_LIMITE_INF), (0, 255, 0), 1)

            results = self.model(frame, verbose=False, conf=self.conf_threshold)

            for r in results:
                for box in r.boxes:
                    conf = float(box.conf[0])
                    if conf < self.conf_threshold: continue
                    
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    cls_id = int(box.cls[0])
                    nombre = self.model.names[cls_id].lower() if hasattr(self.model, 'names') else str(cls_id)

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"{nombre} {conf:.2f}", (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                    if (cx > self.X_CINTA_IZQ and cx < self.X_CINTA_DER) and (cy > self.Y_LIMITE_SUP and cy < self.Y_LIMITE_INF):
                        servo_id = self.mapa_categorias.get(str(cls_id), "")
                        if servo_id in ['1', '2', '3', '4']:
                            ultimo = self.ultimas_detecciones.get(nombre, 0)
                            if (current_time - ultimo) > self.TIEMPO_COOLDOWN:
                                dist = self.DISTANCIAS.get(servo_id, 0.30)
                                t_viaje = dist / self.VELOCIDAD_CINTA
                                t_prog = current_time + t_viaje - self.TIEMPO_ANTICIPACION
                                self.cola_eventos.append({"letra": servo_id, "tiempo": max(t_prog, current_time), "nombre": nombre})
                                self.ultimas_detecciones[nombre] = current_time

            # Procesar cola de servos
            while self.cola_eventos:
                evento = self.cola_eventos[0]
                if current_time >= evento["tiempo"]:
                    self.cola_eventos.popleft()
                    if self.arduino and self.arduino.is_open:
                        try:
                            self.arduino.write(f"{evento['letra']}\n".encode('utf-8'))
                        except: pass
                else:
                    break

            # Enviar frame a la UI
            if frame_callback:
                frame_callback(frame)

# Mantenemos compatibilidad para ejecución directa
if __name__ == "__main__":
    print("Ejecutando en modo consola clásico...")
    engine = ScannerEngine("/home/pi/Desktop/Flex-Sort/Modelos/best_ncnn_model")
    if engine.load_resources():
        engine.start(lambda f: cv2.imshow("Debug", f))
        try:
            while True: 
                if cv2.waitKey(1) & 0xFF == ord('q'): break
                time.sleep(0.01)
        except KeyboardInterrupt: pass
        engine.stop()
