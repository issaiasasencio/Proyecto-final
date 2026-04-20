# FLEX-SORT: Clasificador Inteligente de Residuos mediante Visión Artificial

Este repositorio contiene el código fuente desarrollado para el proyecto de tesis de ingeniería enfocado en la clasificación automatizada de residuos sólidos utilizando modelos de aprendizaje profundo (YOLO) y sistemas embebidos en el borde.

## Arquitectura del Sistema

El proyecto se divide en tres capas principales que garantizan la robustez, el entrenamiento iterativo y el control operativo en tiempo real:

1. **Capa de Entrenamiento y Control (Local PC)**:
   - Contiene la interfaz principal del sistema (`0_panel_control.py`).
   - Módulo de preparación, etiquetado y entrenamiento iterativo de modelos supervisados (YOLOv11/YOLOv26).
   - Scripts de transferencia automatizada de modelos vía SSH hacia el nodo de inferencia.

2. **Capa de Inferencia en el Borde (Raspberry Pi Edge Node)**:
   - Localizada en la carpeta `/RaspberryPi_Code`.
   - Contiene el pipeline de visión artificial en tiempo real.
   - Encargada de leer y enviar matrices de predicción serializadas hacia la capa de hardware de bajo nivel.
   - Entorno reproducible configurado a través de `requirements.txt`.

3. **Capa de Actuación y Control (Microcontrolador Arduino)**:
   - Localizada en la carpeta `/Arduino_Code/Main_Integrado`.
   - Firmware en C/C++ que recibe señales seriales asíncronas para la ejecución del movimiento de los servomotores deflectores de la cinta.
   - Arquitectura orientada a objetos (clases `Clasificador` y `Cinta`) para mantener un bajo acoplamiento y alta cohesión a nivel de hardware.

## Tecnologías Implementadas

- **Machine Learning**: Ultralytics (YOLO), OpenCV, NumPy
- **Control Hardware**: Nivel bajo en C++ (Wiring), PySerial, lgpio, gpiozero
- **Networking**: Paramiko/SCP para despliegues automatizados OTA (Over-The-Air)

## Configuración del Entorno de Inferencia

Para desplegar el nodo de inferencia en la Raspberry Pi de forma aislada y determinista, debe ejecutarse la recolección de dependencias desde el directorio raíz del nodo:

```bash
pip install -r RaspberryPi_Code/requirements.txt
```

---
*Este repositorio recopila la ingeniería de software y hardware como soporte verificable y reproducible para el trabajo final de grado.*
