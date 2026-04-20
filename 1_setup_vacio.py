import os

import yaml


def setup_project():
    """Inicializa la estructura de carpetas y crea el data.yaml base."""
    # Definir la estructura base de carpetas
    base_dir = "Proyecto_FlexSort"
    carpetas = [
        os.path.join(base_dir, "dataset", "images", "train"),
        os.path.join(base_dir, "dataset", "images", "val"),
        os.path.join(base_dir, "dataset", "labels", "train"),
        os.path.join(base_dir, "dataset", "labels", "val"),
        os.path.join(base_dir, "videos_crudos"),
    ]

    # Crear las carpetas
    print(f"--- INICIALIZANDO ENTORNO PARA YOLO26 ---")
    print("Iniciando la creación de la estructura de directorios...")
    for carpeta in carpetas:
        os.makedirs(carpeta, exist_ok=True)
        print(f"Directorio creado o ya existente: {carpeta}")

    # Pre-descarga de la arquitectura YOLO26 para evitar esperas en el primer entrenamiento
    model_base = "yolo26n.pt"
    if not os.path.exists(model_base):
        print(f"\n[AI-SYNC] Detectado entorno YOLO26. Pre-descargando arquitectura base...")
        try:
            from ultralytics import YOLO
            # Esto dispara la descarga automática si no existe
            YOLO(model_base)
            print(f"✅ Arquitectura {model_base} sincronizada localmente.")
        except Exception as e:
            print(f"⚠️ Aviso: No se pudo pre-cargar el modelo base: {e}")

    # Configuración inicial para el archivo data.yaml
    yaml_path = os.path.join(base_dir, "dataset", "data.yaml")

    # Este será nuestro archivo "pelado"
    yaml_content = {
        'train': 'images/train',
        'val': 'images/val',
        'nc': 0,
        'names': [],
    }

    # Crear y guardar el archivo data.yaml
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_content, f, default_flow_style=False, sort_keys=False)

    # Confirmación final en consola
    print(f"\nArchivo de configuración generado: {yaml_path}")
    print("🚀 Estructura YOLO26 finalizada. ¡El sistema está listo para el futuro!")



if __name__ == "__main__":
    setup_project()
