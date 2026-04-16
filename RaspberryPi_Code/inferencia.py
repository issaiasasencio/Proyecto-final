# Paso 1: Importar las librerías necesarias
import cv2
from ultralytics import YOLO
from gpiozero import Servo
import time

# Configuración de 4 servos
servo0 = Servo(12)  # Categoría 0 (papel), GPIO12 (pin físico 32)
servo1 = Servo(13)  # Categoría 1 (plástico), GPIO13 (pin físico 33)
servo2 = Servo(18)  # Categoría 2 (vidrio), GPIO18 (pin físico 12)
servo3 = Servo(19)  # Categoría 3 (metal), GPIO19 (pin físico 35)
servos = [servo0, servo1, servo2, servo3]

# Mapeo de categorías a servos:
# 0: servo0 (Categoría 0 - papel)
# 1: servo1 (Categoría 1 - plástico)
# 2: servo2 (Categoría 2 - vidrio)
# 3: servo3 (Categoría 3 - metal)
class_to_servo = {0: servo0, 1: servo1, 2: servo2, 3: servo3}

def activate_servo(servo, open_position=0.25, close_position=0):  # 0.25 ~ 45°, 0 ~ 0°
    print(f"Abriendo servo a {open_position} (45°)...")
    servo.value = open_position
    time.sleep(2)  # Tiempo para que el residuo caiga/pase
    print(f"Cerrando servo a {close_position} (0°)...")
    servo.value = close_position
    time.sleep(1)  # Estabilizar

# Paso 2: Cargar el modelo entrenado
# Elige qué modelo quieres usar cambiando el nombre del archivo.
model_path = 'Modelos/bestn.mnn'  # O cambia a 'besth.pt' para usar el otro modelo
model = YOLO(model_path)

# Paso 3: Iniciar la captura de video desde la cámara web
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: No se pudo abrir la cámara.")
    exit()

print("Iniciando detección en tiempo real para categorías 0 y 1... Presiona 'q' para salir.")

# Paso 4: Bucle principal para leer y procesar cada fotograma
last_activation = {}  # Cooldown por categoría
cooldown_time = 3  # Segundos entre activaciones de la misma categoría
while True:
    # Leer un fotograma de la cámara
    success, frame = cap.read()
    if not success:
        print("Se terminó el stream de video.")
        break

    # Realizar la predicción de YOLO en el fotograma
    results = model(frame, stream=True, conf=0.45)
    current_time = time.time()

    # Dibujar las cajas y etiquetas en el fotograma
    for r in results:
        annotated_frame = r.plot()
        
        if r.boxes is not None:
            for box in r.boxes:
                cls = int(box.cls.item())
                if cls in class_to_servo and (cls not in last_activation or current_time - last_activation[cls] > cooldown_time):
                    print(f"Detectado categoría {cls}, activando servo...")
                    activate_servo(class_to_servo[cls])
                    last_activation[cls] = current_time

        # Mostrar el fotograma final en una ventana
        cv2.imshow("Deteccion en Tiempo Real", annotated_frame)

    # Romper el bucle y cerrar la ventana si se presiona la tecla 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Paso 5: Liberar recursos al finalizar
cap.release()
cv2.destroyAllWindows()
for servo in servos:
    servo.close()
print("Detección detenida.")