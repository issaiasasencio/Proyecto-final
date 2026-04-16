import os
import yaml

def setup_project():
    """Inicializa la estructura de carpetas y crea el data.yaml base."""
    # Definir la estructura base de carpetas
    base_dir = "Proyecto_Cinta"
    carpetas = [
        os.path.join(base_dir, "dataset", "images", "train"),
        os.path.join(base_dir, "dataset", "images", "val"),
        os.path.join(base_dir, "dataset", "labels", "train"),
        os.path.join(base_dir, "dataset", "labels", "val"),
        os.path.join(base_dir, "videos_crudos")
    ]

    # Crear las carpetas
    print("Iniciando la creación de la estructura de carpetas...")
    for carpeta in carpetas:
        os.makedirs(carpeta, exist_ok=True)
        print(f"Directorio creado o ya existente: {carpeta}")

    # Configuración inicial para el archivo data.yaml
    yaml_path = os.path.join(base_dir, "dataset", "data.yaml")
    
    # Este será nuestro archivo "pelado"
    yaml_content = {
        'train': 'images/train',
        'val': 'images/val',
        'nc': 0,
        'names': []
    }

    # Crear y guardar el archivo data.yaml
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_content, f, default_flow_style=False, sort_keys=False)
    
    # Confirmación final en consola
    print(f"Archivo generado exitosamente: {yaml_path}")
    print("Estructura inicializada correctamente. ¡El sistema empieza en blanco!")

if __name__ == "__main__":
    setup_project()
