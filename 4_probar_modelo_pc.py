import json
import os

import cv2
from ultralytics import YOLO


def load_config():
    config_path = "config.json"
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"confidence": 0.60}


def probar_en_pc():
    """Lanza la inferencia local usando la cámara web de tu PC para que puedas validar físicamente el modelo."""
    import sys
    if len(sys.argv) > 1:
        best_path = sys.argv[1]
    else:
        best_path = os.path.join("Proyecto_FlexSort", "entrenamientos", "modelo_produccion", "weights", "best.pt")

    if not os.path.exists(best_path):
        print(f"Error Crítico: No se encontró el cerebro de IA en -> {best_path}")
        return

    print("Cargando el cerebro de IA (weights best.pt)...")
    model = YOLO(best_path)

    # 0 = Cámara por defecto en Windows (usualmente la web frontal).
    # Si Windows la pone secundaria, cambia el 0 por un 1 o un 2.
    print("Iniciando captura de cámara local. Presiona la tecla 'q' para salir.")
    cap = cv2.VideoCapture(0)

    # Reducimos resolución sólo para la ventana a fin de que sea fluida
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("Error: OpenCV no pudo acceder a la cámara local de esta PC.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 1. Aplicar la red neuronal en el frame actual
        # ('verbose=False' elimina el spam a consola)
        # Modo Producción: Confianza cargada dinámicamente desde Ajustes
        config = load_config()
        conf_val = config.get("confidence", 0.60)
        results = model.predict(source=frame, conf=conf_val, verbose=False)
        result = results[0]

        frame_anotado = frame.copy()

        # 2. Dibujo iterativo Manual para control exacto del UI de detección
        for box in result.boxes:
            # Obtener Coordenadas
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            # Obtener Clase y Categoria
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])

            # Evitar error si el modelo cargado no tiene la misma cantidad de clases
            # (ej si usó el yolo base accidentalmente)
            nombre_etiqueta = result.names.get(cls_id, f"Clase_{cls_id}")

            # Dibujar el Recuadro Verde del objeto
            cv2.rectangle(frame_anotado, (x1, y1), (x2, y2), (0, 255, 0), 3)

            # Crear un fondo negro para el texto para que sea súper legible
            label = f"{nombre_etiqueta.upper()} ({conf*100:.0f}%)"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            # Fondo verde brillante para el texto
            cv2.rectangle(
                frame_anotado, (x1, y1 - th - 10), (x1 + tw, y1), (0, 255, 0), -1
            )

            # Dibujar el nombre que el usuario escribió
            cv2.putText(frame_anotado, label, (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)  # Letras negras

        # Dibujar Stats de Motor
        stats_text = f"Detecciones: {len(result.boxes)} | Conf. Limite: {int(conf_val*100)}%"
        cv2.putText(
            frame_anotado, stats_text, (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2
        )

        # 3. Mostrar la ventana visual interactiva
        cv2.imshow("Scanner AI - Deteccion en vivo", frame_anotado)

        # 4. Romper el bucle si detecta la tecla 'q' en el teclado de tu computadora.
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Liberación de recursos
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    probar_en_pc()
