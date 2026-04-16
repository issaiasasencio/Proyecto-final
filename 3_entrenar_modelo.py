import os
from ultralytics import YOLO
import torch

def train():
    print("=== Configuración del Motor ===")
    if torch.cuda.is_available():
        print(f"[OK] ¡CUDA detectado! Entrenamiento Acelerado en: {torch.cuda.get_device_name(0)}")
        total_vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"VRAM disponible de GPU: {total_vram:.2f} GB")
        device = "0" # Fuerza la GPU Nvidia
    else:
        print("[ATENCION] CUDA NO DETECTADO. Se entrenará por CPU (Esto será extremadamente lento).")
        device = "cpu"
    print("=====================================\n")

    base_dir = "Proyecto_Cinta"
    yaml_path = os.path.abspath(os.path.join(base_dir, "dataset", "data.yaml"))

    if not os.path.exists(yaml_path):
        print("Error: El archivo data.yaml no existe. Ejecuta primero 1_setup_vacio.py y alimenta datos con procesar_video.")
        return

    import sys
    best_path = os.path.join(base_dir, "entrenamientos", "modelo_produccion", "weights", "best.pt")
    
    # Determinar si hacemos Fine-Tuning (Continuo) o Desde Cero (Scratch) guiado por el panel
    modo = sys.argv[1] if len(sys.argv) > 1 else "scratch"
    
    if modo == "finetune" and os.path.exists(best_path):
        print(f"[RECICLAJE] Modo APRENDIZAJE CONTINUO Activado: Sumando conocimiento a tu último cerebro ({best_path})...")
        model = YOLO(best_path)
    else:
        if modo == "finetune":
            print("[ATENCION] Quisiste sumar a tu modelo anterior pero aún no existe. ¡No te preocupes! Arrancaremos creando el primero.")
        print("[NUEVO] Modo DESDE CERO Activado: Iniciando Modelo Pre-Entrenado general (yolo11n.pt)...")
        model = YOLO("yolo11n.pt")

    print("\n[INICIANDO] ¡Iniciando el entrenamiento profundo!")
    # model.train ejecuta la estructura completa de PyTorch por debajo. 
    results = model.train(
        data=yaml_path,
        epochs=300,      # Industrial Level: 300 Iteraciones para máxima absorción matemática.
        imgsz=640,       # Tamaño de red a 640x640 pixeles.
        batch=16,        # Tamaño de lote optimizado para exprimir al 100% tu Nvidia.
        device=device,   # Dispositivo seleccionado arriba.
        project=os.path.join(base_dir, "entrenamientos"), # Directorio principal de resultados.
        name="modelo_produccion", # Nombre de la corrida.
        exist_ok=True,   # Puesto en True actualiza la misma carpeta sin crear redundancias.
        patience=50      # Parada anticipada permisiva: si tras 50 vueltas la pérdida no mejora, asume que llegó a la perfección y frena.
    )

    best_path = os.path.join(base_dir, "entrenamientos", "modelo_produccion", "weights", "best.pt")
    print("\n[FIN] ENTRENAMIENTO FINALIZADO [FIN]")
    print(f"Olla MLOps completada. Tu modelo central ha sido guardado en: {best_path}")

if __name__ == "__main__":
    train()
