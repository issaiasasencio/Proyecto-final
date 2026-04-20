import cv2
import time
import serial
import os
import threading
from collections import deque
from ultralytics import YOLO
import contextlib


class VideoGet:
    """Hilo dedicado a capturar frames de la cámara sin bloquear el procesamiento."""

    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False

    def start(self):
        threading.Thread(target=self.get, args=(), daemon=True).start()
        return self

    def get(self):
        while not self.stopped:
            if not self.grabbed:
                self.stop()
            else:
                (self.grabbed, self.frame) = self.stream.read()

    def stop(self):
        self.stopped = True
        self.stream.release()


class ScannerEngine:
    def __init__(self, model_path, arduino_port="/dev/ttyUSB0", baudrate=115200):
        # Configuracion de limites y parametros
        self.Y_LIMITE_SUP = 90
        self.Y_LIMITE_INF = 400
        self.X_CINTA_IZQ = 100
        self.X_CINTA_DER = 540
        self.DISTANCIAS = {"1": 0.20, "2": 0.20, "3": 0.45, "4": 0.45}
        self.VELOCIDAD_CINTA = 0.07  # Valor por defecto
        self.TIEMPO_ANTICIPACION = 2.5
        self.TIEMPO_COOLDOWN = 5.0

        self.model_path = model_path
        self.arduino_port = arduino_port
        self.baudrate = baudrate

        self.model = None
        self.arduino = None
        self.video_getter = None
        self.running = False

        self.cola_eventos = deque()
        self.ultimas_detecciones = {}
        self.status_msg = "Inicializando..."

        self.mapa_categorias = {}
        self.conf_threshold = 0.40
        self.arduino_ready = False

    def is_arduino_connected(self):
        """Verifica el estado real del puerto serial."""
        return self.arduino is not None and self.arduino.is_open

    def load_resources(self):
        try:
            if not os.path.exists(self.model_path):
                self.status_msg = "Error: No se ha detectado ningun modelo entrenado en la ruta especificada."
                return False
            
            # Optimizacion para Pi 5: Cargar modelo con task detect explícito
            self.model = YOLO(self.model_path, task="detect")
            self.status_msg = "Modelo cargado."
        except Exception as e:  # noqa: BLE001
            self.status_msg = f"Error Crítico del Modelo: {e}"
            return False

        try:
            self.arduino = serial.Serial(self.arduino_port, self.baudrate, timeout=1)
            time.sleep(2)
            self.status_msg = "Arduino conectado."
            self.arduino_ready = True
        except Exception:  # noqa: BLE001
            self.status_msg = "Arduino No detectado (Simulando)."
            self.arduino_ready = False

        return True

    def set_mapping(self, mapping_dict):
        self.mapa_categorias = {str(k).lower(): str(v) for k, v in mapping_dict.items()}

    def start(self, frame_callback):
        if self.running:
            return
        self.running = True
        self.video_getter = VideoGet(src=0).start()
        self.thread = threading.Thread(
            target=self._loop, args=(frame_callback,), daemon=True
        )
        self.thread.start()

    def stop(self):
        self.running = False
        if self.video_getter:
            self.video_getter.stop()
        if hasattr(self, "thread"):
            self.thread.join(timeout=2)
        if self.arduino:
            self.arduino.close()
            self.arduino_ready = False

    def send_manual_cmd(self, servo_id):
        """Envía un pulso manual a un servo específico para prueba."""
        if self.is_arduino_connected():
            try:
                self.arduino.write(f"{servo_id}\n".encode())
                return True
            except Exception:  # noqa: BLE001
                self.arduino_ready = False
                return False
        return False

    def _loop(self, frame_callback):
        # Esperar a que el primer frame este listo
        time.sleep(1)

        while self.running:
            if not self.video_getter.grabbed:
                break

            frame = self.video_getter.frame.copy()
            current_time = time.time()

            # Dibujar Guias
            cv2.line(
                frame, (0, self.Y_LIMITE_SUP), (640, self.Y_LIMITE_SUP), (0, 255, 0), 2
            )
            cv2.line(
                frame, (0, self.Y_LIMITE_INF), (640, self.Y_LIMITE_INF), (0, 255, 0), 1
            )

            # Inferencia Optimizada (No verbose para no saturar bus interno)
            results = self.model.predict(frame, verbose=False, conf=self.conf_threshold)

            for r in results:
                for box in r.boxes:
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    cls_id = int(box.cls[0])

                    # Conseguir nombre evitando crash si no hay names cargados
                    nombre = self.model.names.get(cls_id, str(cls_id)).lower()

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(
                        frame,
                        f"{nombre.upper()} {conf:.2f}",
                        (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2,
                    )

                    # Logica de Clasificacion en Zona de Cinta
                    if (cx > self.X_CINTA_IZQ and cx < self.X_CINTA_DER) and (
                        cy > self.Y_LIMITE_SUP and cy < self.Y_LIMITE_INF
                    ):
                        servo_id = self.mapa_categorias.get(str(cls_id), "")
                        if servo_id in ["1", "2", "3", "4"]:
                            ultimo = self.ultimas_detecciones.get(nombre, 0)
                            if (current_time - ultimo) > self.TIEMPO_COOLDOWN:
                                dist = self.DISTANCIAS.get(servo_id, 0.30)
                                t_viaje = dist / self.VELOCIDAD_CINTA
                                t_prog = (
                                    current_time + t_viaje - self.TIEMPO_ANTICIPACION
                                )
                                self.cola_eventos.append(
                                    {
                                        "letra": servo_id,
                                        "tiempo": max(t_prog, current_time),
                                    }
                                )
                                self.ultimas_detecciones[nombre] = current_time

            # Procesamiento de Servos
            while self.cola_eventos:
                evento = self.cola_eventos[0]
                if current_time >= evento["tiempo"]:
                    self.cola_eventos.popleft()
                    if self.arduino and self.arduino.is_open:
                        with contextlib.suppress(Exception):
                            self.arduino.write(f"{evento['letra']}\n".encode())
                else:
                    break

            if frame_callback:
                frame_callback(frame)


if __name__ == "__main__":
    print("Iniciando Motor Ultralytics (Optimizado para RPi 5)...")
    model_rpi = "/home/pi/Desktop/Flex-Sort/Modelos/best_ncnn_model"
    engine = ScannerEngine(model_rpi)
    if engine.load_resources():
        # Ejecucion headless (Sin ventana extra OpenCV) para ahorrar VRAM
        engine.start(lambda f: None)
        try:
            print("Motor en marcha (Modo Headless). Presione Ctrl+C para detener.")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        engine.stop()
