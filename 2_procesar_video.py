import json
import os
import random
import shutil
import sys
import time

import cv2
import yaml


def limpiar_historial(base_dir):
    """Vacía las carpetas de train/val e inicializa data.yaml a 0."""
    print("Limpiando el historial del dataset. Esto borrará datos anteriores...")
    # 3. Rutas a borrar y recrear
    carpetas_a_limpiar = [
        os.path.join(base_dir, "dataset", "images", "train"),
        os.path.join(base_dir, "dataset", "images", "val"),
        os.path.join(base_dir, "dataset", "labels", "train"),
        os.path.join(base_dir, "dataset", "labels", "val"),
    ]

    # Borrar todo el contenido de cada carpeta
    for carpeta in carpetas_a_limpiar:
        if os.path.exists(carpeta):
            for filename in os.listdir(carpeta):
                file_path = os.path.join(carpeta, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Error al borrar {file_path}: {e}")
        else:
            # Crea de nuevo si por alguna razón no existía
            os.makedirs(carpeta, exist_ok=True)

    # Reiniciar data.yaml (vaciar historial de clases)
    yaml_path = os.path.join(base_dir, "dataset", "data.yaml")
    yaml_content = {
        'train': 'images/train',
        'val': 'images/val',
        'nc': 0,
        'names': [],
    }
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_content, f, default_flow_style=False, sort_keys=False)

    # Reiniciar mapeo de servos
    mapping_path = os.path.join(base_dir, "dataset", "servo_mapping.json")
    if os.path.exists(mapping_path):
        try:
            os.remove(mapping_path)
        except Exception:
            pass

    print("Historial borrado. Dataset y mapeo de servos limpios.")


def procesar_video():
    """Ingestor de datos. Procesa el video subido guardando frames redimensionados."""
    base_dir = "Proyecto_Cinta"
    yaml_path = os.path.join(base_dir, "dataset", "data.yaml")

    # 1. Checar si se pasaron argumentos (desde la GUI)
    # El panel envía 4 argumentos: video_path, categoria, opcion, servo_id
    if len(sys.argv) >= 4:
        video_path = sys.argv[1]
        categoria = sys.argv[2]
        opcion = sys.argv[3].lower()
        servo_id = sys.argv[4] if len(sys.argv) >= 5 else None
    else:
        # Pedir por consola si se ejecuta directo
        video_path = input("Ingresa la ruta del video .mp4 (ej: videos_crudos/mitest.mp4): ")
        if not os.path.exists(video_path):
            print("El archivo de video especificado no fue encontrado. Terminando programa.")
            return

        categoria = input("Ingresa el nombre de la categoría del objeto (ej: 'manzana'): ")

        # 2. Preguntar al usuario sobre la limpieza de la data (Opción A o B)
        while True:
            prompt = (
                "¿Deseás (A) sumar este video al dataset existente, "
                "o (B) borrar todo el historial? (a/b): "
            )
            opcion = input(prompt).strip().lower()
            if opcion in ['a', 'b']:
                break
            print("Opción no válida. Por favor, ingresá 'a' para anexar o 'b' para rehacer el dataset.")

        servo_id = input("Ingresá el ID del servo (1, 2, 3 o 4): ").strip()

    if video_path != "webcam" and not os.path.exists(video_path):
        print(f"Error: No se encontró el archivo de video: {video_path}")
        return

    # 3. Implementar función de limpieza si elige la opción B
    if opcion == 'b':
        limpiar_historial(base_dir)

    # 4. Leer data.yaml, agregar categoría si no existe y conseguir class_id
    with open(yaml_path, encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}

    names = data.get('names', [])
    if categoria not in names:
        names.append(categoria)
        data['names'] = names
        data['nc'] = len(names)

        # Guardar archivo actualizado
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        print(f"Categoría agregada. Total de clases ({data['nc']}).")

    # Obtener el class_id (índice en la lista de nombres)
    class_id = names.index(categoria)
    print(f"Se utilizará el ID (class_id) '{class_id}' para la categoría '{categoria}'")

    # 5. Guardar el mapeo de Servo si existe
    if servo_id:
        mapping_path = os.path.join(base_dir, "dataset", "servo_mapping.json")
        mapping = {}
        if os.path.exists(mapping_path):
            try:
                with open(mapping_path, encoding='utf-8') as f:
                    mapping = json.load(f)
            except Exception:
                pass

        # Mapeamos el string del class_id al servo_id
        mapping[str(class_id)] = str(servo_id)

        with open(mapping_path, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, indent=4)
        print(f"Mapeo Hardware: Clase {class_id} -> Servo {servo_id}")

    # 6. Procesar el video con OpenCV
    MIN_DURACION = 10  # Tiempo mínimo en segundos
    es_webcam = (video_path == "webcam")

    if es_webcam:
        print("Iniciando conexión con Cámara Web (Iriun Webcam)...")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            cap = cv2.VideoCapture(1)  # Intentar fallback si el index 0 no es la Iriun
        if not cap.isOpened():
            cap = cv2.VideoCapture(2)
        fps = 30.0
    else:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)

    if not cap.isOpened():
        print("Error al abrir la cámara en vivo o el archivo de video.")
        return

    if fps <= 0:
        fps = 30.0  # Valor seguro por defecto si no lo lee correctamente

    # --- VERIFICACIÓN DE DURACIÓN MÍNIMA (PARA ARCHIVOS) ---
    if not es_webcam:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duracion_video = total_frames / fps
        if duracion_video < MIN_DURACION:
            print(f"\n[ERROR] Video demasiado corto: {duracion_video:.1f}s.")
            print(f"[REQUERIDO] Mínimo {MIN_DURACION}s para asegurar calidad de entrenamiento.")
            return

    # Avanza ~300ms por iteración.
    frames_a_saltar = max(1, int(fps * 0.3))

    frame_count = 0
    guardados = 0

    template_obj = None
    bbox_w = 0
    bbox_h = 0

    if es_webcam:
        print(f"\n[AUTO-LABELLER] SISTEMA DE MÁXIMA PRECISIÓN - CATEGORÍA: {categoria}")
        print(">>>>> Vamos a calibrar tu objeto. Colocalo frente a la cámara.")
        print(">>>>> PRESIONÁ LA BARRA ESPACIADORA en la ventana cuando estés listo para congelar la imagen.")

        while True:
            ret, frame = cap.read()
            if not ret:
                return

            # NO redimensionar forzosamente para no distorsionar la imagen nativa (aspect ratio)
            cv2.imshow("CALIBRACIÓN (Presioná ESPACIO cuando se vea bien)", frame)
            if cv2.waitKey(1) & 0xFF == ord(' '):
                break
        cv2.destroyWindow("CALIBRACIÓN (Presioná ESPACIO cuando se vea bien)")

        print(">>>>> MUY IMPORTANTE: Usá el mouse para DIBUJAR un recuadro MUY AJUSTADO alrededor del objeto.")
        print(">>>>> Luego presioná 'ENTER' en tu teclado para disparar el Auto-Etiquetado Inteligente.")

        bbox_roi = cv2.selectROI("Dibujá un recuadro ajustado y pulsá ENTER",
                                 frame, fromCenter=False, showCrosshair=True)
        cv2.destroyWindow("Dibujá un recuadro ajustado y pulsá ENTER")

        if bbox_roi[2] > 0 and bbox_roi[3] > 0:
            x_r, y_r, w_r, h_r = bbox_roi
            template_obj = frame[y_r:y_r + h_r, x_r:x_r + w_r]
            bbox_w = w_r
            bbox_h = h_r
            print("\n✅ Molde capturado con ÉXITO. Ahora tu IA aprenderá la caja exacta matemática.")
            print("-> Mové el objeto muy lentamente frente a la cámara para generar el dataset hiperpreciso.")
        else:
            print("No dibujaste nada. Usando modo genérico.")
    else:
        print(f"Procesando video local a {fps:.2f} FPS. Extrayendo fotogramas...")

    # Tiempo de inicio para control de grabación
    start_time_live = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:  # Si no hay más frames, romper ciclo
            break

        real_h, real_w = frame.shape[:2]

        # Lógica de Rastreo Matemático (Template Matching) para etiquetado perfecto
        actual_x = 0.5
        actual_y = 0.5
        actual_w = 0.8
        actual_h = 0.8

        if template_obj is not None:
            # Buscar en la imagen nativa dónde se movió el objeto
            res = cv2.matchTemplate(frame, template_obj, cv2.TM_CCOEFF_NORMED)
            _, _, _, max_loc = cv2.minMaxLoc(res)
            x_top, y_top = max_loc

            # Transformar a formato normalizado de YOLO usando las dimensiones REALES de la cámara
            actual_x = (x_top + bbox_w / 2.0) / real_w
            actual_y = (y_top + bbox_h / 2.0) / real_h
            actual_w = bbox_w / real_w
            actual_h = bbox_h / real_h

        if es_webcam:
            vis_frame = frame.copy()

            # Dibujar la Bounding Box exacta rastreada en TIPO TIEMPO REAL
            x_vis = int((actual_x - actual_w / 2) * real_w)
            y_vis = int((actual_y - actual_h / 2) * real_h)
            w_vis = int(actual_w * real_w)
            h_vis = int(actual_h * real_h)

            cv2.rectangle(
                vis_frame, (x_vis, y_vis), (x_vis + w_vis, y_vis + h_vis), (0, 255, 0), 2
            )
            cv2.putText(vis_frame, "Auto-Etiquetado Inteligente", (x_vis, y_vis - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            if frame_count % frames_a_saltar <= 2:
                cv2.circle(vis_frame, (30, 30), 10, (0, 0, 255), -1)
                cv2.putText(vis_frame, "REC", (50, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            # --- FEEDBACK DE TIEMPO MÍNIMO ---
            tiempo_actual = time.time() - start_time_live
            if tiempo_actual < MIN_DURACION:
                color_msg = (0, 165, 255)  # Naranja
                txt_msg = f"TIEMPO RESTANTE: {int(MIN_DURACION - tiempo_actual)}s"
                cv2.rectangle(vis_frame, (10, real_h - 40), (400, real_h - 10), (0, 0, 0), -1)
                cv2.putText(vis_frame, txt_msg, (20, real_h - 15),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_msg, 2)
            else:
                cv2.rectangle(vis_frame, (10, real_h - 40), (250, real_h - 10), (0, 0, 0), -1)
                cv2.putText(vis_frame, "LISTO (Q para parar)", (20, real_h - 15),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            nombre_ventana = f"Grabando automáticamente - {categoria} (Presioná 'q' para salir)"
            cv2.imshow(nombre_ventana, vis_frame)
            tecla = cv2.waitKey(1) & 0xFF
            if tecla == ord('q'):
                if tiempo_actual >= MIN_DURACION:
                    break
                else:
                    print(f"\n[ATENCIÓN] Grabación muy corta ({int(tiempo_actual)}s). Falta llegar a {MIN_DURACION}s.")

            if frame_count == 0:
                cv2.setWindowProperty(nombre_ventana, cv2.WND_PROP_TOPMOST, 1)

        # Si el conteo coincide con nuestro paso de 300 ms, capturamos el frame
        if frame_count % frames_a_saltar == 0:

            # 6. Guardar usando proporción 80/20 (train/val)
            is_train = random.random() < 0.8
            split_folder = "train" if is_train else "val"

            # Generar Timestamp sumitido al nombre para prevenir que se sobrescriban
            timestamp = int(time.time() * 1000)
            filename_base = f"{categoria}_{timestamp}_{guardados}"
            img_filename = f"{filename_base}.jpg"
            txt_filename = f"{filename_base}.txt"

            img_path = os.path.join(base_dir, "dataset", "images", split_folder, img_filename)
            txt_path = os.path.join(base_dir, "dataset", "labels", split_folder, txt_filename)

            # Escribiendo el frame anatómico nativo en disco
            cv2.imwrite(img_path, frame)

            # 7. Guardar coordenadas Matemáticas ajustadas dinámicamente al movimiento
            with open(txt_path, 'w') as f:
                f.write(f"{class_id} {actual_x:.6f} {actual_y:.6f} {actual_w:.6f} {actual_h:.6f}\n")

            guardados += 1

        frame_count += 1

    cap.release()
    print(f"¡Proceso finalizado con éxito! Se guardaron {guardados} fotogramas pre-etiquetados para la IA.")


if __name__ == "__main__":
    procesar_video()
