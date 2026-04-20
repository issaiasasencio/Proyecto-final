import json
import os
import shutil
import time

import torch
import yaml
from ultralytics import YOLO


def load_config():
    config_path = "config.json"
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"epochs": 300}


def train():
    print("=== Configuración del Motor ===")
    if torch.cuda.is_available():
        print(f"[OK] ¡CUDA detectado! Entrenamiento en: {torch.cuda.get_device_name(0)}")
        total_vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"VRAM disponible de GPU: {total_vram:.2f} GB")
        device = "0"  # Fuerza la GPU Nvidia
    else:
        print("[ATENCIÓN] CUDA NO DETECTADO. Se entrenará por CPU (lento).")
        device = "cpu"
    print("=====================================\n")

    base_dir = "Proyecto_Cinta"
    yaml_path = os.path.abspath(os.path.join(base_dir, "dataset", "data.yaml"))

    if not os.path.exists(yaml_path):
        print(
            "Error: El archivo data.yaml no existe. "
            "Ejecuta primero 1_setup_vacio.py y alimenta datos con procesar_video."
        )
        return

    import sys
    best_path = os.path.join(base_dir, "entrenamientos", "modelo_produccion", "weights", "best.pt")

    # Determinar si hacemos Fine-Tuning (Continuo) o Desde Cero (Scratch) guiado por el panel
    modo = sys.argv[1] if len(sys.argv) > 1 else "scratch"

    if modo == "finetune" and os.path.exists(best_path):
        print(
            f"[RECICLAJE] Modo APRENDIZAJE CONTINUO activado: "
            f"Sumando conocimiento a tu último cerebro ({best_path})..."
        )
        model = YOLO(best_path)
    else:
        if modo == "finetune":
            print(
                "[ATENCIÓN] Querías sumar a tu modelo anterior pero aún no existe. "
                "¡No te preocupes! Arrancaremos creando el primero."
            )
        print("[NUEVO] Modo DESDE CERO: Iniciando modelo YOLO (yolo11n.pt)...")
        model = YOLO("yolo11n.pt")

    config = load_config()
    epochs = config.get("epochs", 300)

    print("\n[INICIANDO] ¡Iniciando el entrenamiento profundo!")
    # model.train ejecuta la estructura completa de PyTorch por debajo.
    model.train(
        data=yaml_path,
        epochs=epochs,      # Industrial Level: Cargado dinámicamente.
        imgsz=640,       # Tamaño de red a 640x640 pixeles.
        batch=16,        # Tamaño de lote optimizado para exprimir al 100% tu Nvidia.
        device=device,   # Dispositivo seleccionado arriba.
        project=os.path.join(base_dir, "entrenamientos"),  # Directorio principal de resultados.
        name="modelo_produccion",  # Nombre de la corrida.
        exist_ok=True,   # Puesto en True actualiza la misma carpeta sin crear redundancias.
        # Parada anticipada permisiva: si tras 50 vueltas la pérdida no mejora, asume que llegó a la perfección y frena.
        patience=50,
    )

    best_path = os.path.join(base_dir, "entrenamientos", "modelo_produccion", "weights", "best.pt")
    print("\n[FIN] ENTRENAMIENTO FINALIZADO [FIN]")

    archive_dir = os.path.join(base_dir, "modelos_archivados")
    os.makedirs(archive_dir, exist_ok=True)

    # Encontrar la última versión para autoincrementar
    existing_versions = [
        f for f in os.listdir(archive_dir)
        if f.startswith("modelo_v") and f.endswith(".pt")
    ]
    next_v = 1
    if existing_versions:
        try:
            # Extraer números de 'modelo_v1.pt', 'modelo_v2.pt', etc.
            version_nums = [
                int(f.replace("modelo_v", "").replace(".pt", ""))
                for f in existing_versions
            ]
            next_v = max(version_nums) + 1
        except ValueError:
            pass

    versioned_name = f"modelo_v{next_v}.pt"
    archive_path = os.path.join(archive_dir, versioned_name)

    if os.path.exists(best_path):
        shutil.copy2(best_path, archive_path)
        print(f"📦 ¡Cerebro archivado automáticamente como: {versioned_name}!")

        # --- GENERAR METADATOS ENRIQUECIDOS ---
        metadata = {
            "version": versioned_name,
            "fecha": time.strftime("%d/%m/%Y %H:%M"),
            "objetos": []
        }

        # Leer clases y servos
        mapping_path = os.path.join(base_dir, "dataset", "servo_mapping.json")
        yaml_path = os.path.join(base_dir, "dataset", "data.yaml")

        names = []
        if os.path.exists(yaml_path):
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                names = data.get("names", [])

        mapping = {}
        if os.path.exists(mapping_path):
            with open(mapping_path, "r", encoding="utf-8") as f:
                mapping = json.load(f)

        for i, name in enumerate(names):
            servo = mapping.get(str(i), "N/A")
            metadata["objetos"].append({"nombre": name, "servo": servo})

        metadata_path = archive_path.replace(".pt", ".json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)
        print(f"📝 Metadatos guardados en: {os.path.basename(metadata_path)}")

    print(f"Olla MLOps completada. Tu modelo central ha sido guardado en: {best_path}")


if __name__ == "__main__":
    train()
