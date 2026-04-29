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
        print(f"[OK] CUDA detectado. Entrenamiento en: {torch.cuda.get_device_name(0)}")
        total_vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"VRAM disponible de GPU: {total_vram:.2f} GB")
        device = "0"  # Fuerza la GPU Nvidia
    else:
        print("[ATENCION] CUDA no detectado. Se entrenara por CPU.")
        device = "cpu"
    print("=====================================\n")

    base_dir = "Proyecto_FlexSort"
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
            f"[INFO] Modo aprendizaje continuo activado: "
            f"Optimizando modelo previo ({best_path})..."
        )
        model = YOLO(best_path)
    else:
        if modo == "finetune":
            print(
                "[INFO] No se encontro modelo previo para aprendizaje continuo. "
                "Iniciando nuevo entrenamiento."
            )
        print("[INFO] Modo desde cero: Iniciando modelo yolo26n...")
        model = YOLO("yolo26n.pt")

    config = load_config()
    epochs = config.get("epochs", 300)

    print("\n[INFO] Iniciando proceso de entrenamiento.")

    # Forzar rutas absolutas para evitar que YOLO use 'runs/detect/'
    project_abs = os.path.abspath(os.path.join(base_dir, "entrenamientos"))

    model.train(
        data=yaml_path,
        epochs=epochs,
        imgsz=640,
        batch=16,
        device=device,
        project=project_abs,
        name="modelo_produccion",
        exist_ok=True,
        patience=50,
        # --- DATA AUGMENTATION EXTREMO PARA CINTA TRANSPORTADORA ---
        degrees=180.0,   # Rota los objetos en todos los angulos posibles internamente
        flipud=0.5,      # Voltea imagenes de cabeza (50%)
        fliplr=0.5,      # Voltea imagenes en espejo lateral
        scale=0.3,       # +30% y -30% de tamano aleatorio al vuelo
        hsv_v=0.2,       # Aplica hasta 20% de diferencia de iluminacion ambiental
    )

    best_path = os.path.join(project_abs, "modelo_produccion", "weights", "best.pt")
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
        print(f"[INFO] Modelo archivado correctamente como: {versioned_name}")

        # --- GENERAR METADATOS ENRIQUECIDOS ---
        metadata = {
            "version": versioned_name,
            "fecha": time.strftime("%d/%m/%Y %H:%M:%S"), # Formato completo para ordenado
            "objetos": [],
            "servos": {}
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
            metadata["objetos"].append(name)
            metadata["servos"][name] = servo

        metadata_path_archive = archive_path.replace(".pt", ".json")
        metadata_path_best = best_path.replace(".pt", ".json")
        
        with open(metadata_path_archive, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)
        with open(metadata_path_best, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)
            
        print(f"[INFO] Metadatos sincronizados en: {os.path.basename(metadata_path_archive)}")

    print(f"Proceso MLOps completado. Modelo guardado en: {best_path}")


if __name__ == "__main__":
    train()
