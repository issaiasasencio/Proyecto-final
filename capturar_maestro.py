import json
import os
import time
import subprocess
import cv2
import paramiko
from scp import SCPClient

def load_config():
    config_path = "config.json"
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"ip_raspberry": "192.168.1.10", "usuario": "pi", "contrasena": "12345678"}

def capturar_y_procesar_fondo():
    config = load_config()
    ip = config["ip_raspberry"]
    user = config["usuario"]
    pwd = config["contrasena"]

    base_dir = "Proyecto_FlexSort"
    repo_fondo = os.path.join(base_dir, "recursos", "fondo_maestro")
    os.makedirs(repo_fondo, exist_ok=True)

    print("\n[CAPTURADOR MAESTRO] Conectando con Raspberry Pi...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(hostname=ip, username=user, password=pwd, timeout=10)
        print("Conexion establecida. Iniciando grabacion de 10s en el Edge...")

        # 1. Ejecutar el grabador remoto
        # Nos aseguramos de estar en el directorio correcto en la RPi
        cmd = "cd Desktop/Flex-Sort && python3 remote_recorder.py"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        # Esperar a que termine (bloqueante para asegurar el archivo)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status == 0:
            print("Grabacion exitosa en Raspberry. Descargando archivo...")
            
            # 2. Descargar el video
            with SCPClient(ssh.get_transport()) as scp:
                remoto = "/home/pi/Desktop/Flex-Sort/fondo_maestro.mp4"
                local = os.path.join(repo_fondo, "fondo_maestro.mp4")
                scp.get(remoto, local)
            
            # Eliminar archivo remoto para mantener limpia la Raspberry Pi
            ssh.exec_command(f"rm {remoto}")
            
            print(f"Video guardado localmente: {local}")

            # 3. Procesar el video para extraer fotos negativas
            print("Procesando video para generar muestras negativas...")
            cap = cv2.VideoCapture(local)
            count = 0
            guardados = 0
            
            # Limpiar fotos viejas del fondo maestro si existen
            for f in os.listdir(repo_fondo):
                if f.endswith(".jpg"):
                    os.remove(os.path.join(repo_fondo, f))

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Extraer 1 frame cada 5 para no tener 300 fotos identicas
                if count % 5 == 0:
                    img_name = f"negativo_{guardados}.jpg"
                    img_path = os.path.join(repo_fondo, img_name)
                    cv2.imwrite(img_path, frame)
                    guardados += 1
                count += 1
            
            cap.release()
            print(f"Finalizado. Se generaron {guardados} muestras negativas permanentes.")
            ssh.close()
            return True
        else:
            print(f"Error en la Raspberry Pi: {stderr.read().decode()}")
            ssh.close()
            return False

    except Exception as e:
        print(f"Error de conexion o proceso: {e}")
        return False

if __name__ == "__main__":
    capturar_y_procesar_fondo()
