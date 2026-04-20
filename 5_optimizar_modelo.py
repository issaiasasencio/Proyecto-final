import os
import sys

from ultralytics import YOLO

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("ERROR: Faltan argumentos.")
        print(
            "Uso: python 5_optimizar_modelo.py "
            "<ruta_modelo.pt> <formato: ncnn o tflite>"
        )
        sys.exit(1)

    modelo_path = sys.argv[1]
    formato = sys.argv[2]

    print("\n[OPTIMIZACIÓN EDGE]")
    print(f"⚙️ Cargando modelo base de PyTorch: {os.path.basename(modelo_path)}")
    model = YOLO(modelo_path)

    print(
        f"🚀 Iniciando exportación a formato '{formato.upper()}' para Raspberry Pi..."
    )
    print(
        "Nota: La primera vez que exportes a un formato estructurado como NCNN "
        "puede tardar un poco mientras configura ONNX."
    )

    try:
        # Exportar el modelo. Ultralytics manejará todo el backend pesado
        # Forzar el tipo Float32 quitando half=True, ya que NCNN en esta Rasp causa NaNs ciegos.
        path_exportado = model.export(format=formato)
        print(f"\n✅ ¡Exportación exitosa a {formato.upper()}!")
        print(f"📁 Modelo optimizado guardado en: {path_exportado}")
    except Exception as e:
        print(f"\n❌ ERROR durante la exportación: {e}")
        print(
            "Aseguráte de estar conectado a internet si es la primera vez "
            "que exportás a este formato."
        )
