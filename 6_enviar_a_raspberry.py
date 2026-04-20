import contextlib
import json
import os
import sys
import time

import paramiko
from scp import SCPClient

# Forzar salida en UTF-8 para evitar errores con los emojis en la consola de Windows
if sys.stdout.encoding.lower() != 'utf-8':
    with contextlib.suppress(AttributeError):
        sys.stdout.reconfigure(encoding='utf-8')


def load_config():
    config_path = "config.json"
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "ip_raspberry": "192.168.1.10",
        "usuario": "pi",
        "contrasena": "12345678"
    }


def enviar_modelo_a_raspberry(ruta_modelo_pc, ruta_destino_pi):
    # =========================================================================
    # ¡IMPORTANTE! EDITA ESTAS CREDENCIALES EN EL PANEL DE AJUSTES (ENGRANAJE)
    # =========================================================================
    config = load_config()
    ip_raspberry = config.get("ip_raspberry", "192.168.1.10")
    usuario = config.get("usuario", "pi")
    contrasena = config.get("contrasena", "12345678")
    # =========================================================================

    print("\n[TRANSFERENCIA EDGE]")
    print(f"Intentando conectar con {ip_raspberry}...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Timeout de 5 segundos para que te des cuenta rápido si la IP está mal
        ssh.connect(hostname=ip_raspberry, username=usuario, password=contrasena, timeout=5)
        print("Conexion P2P (SSH) establecida.")

        # Nos aseguramos de que el directorio remoto exista
        ssh.exec_command(f"mkdir -p {ruta_destino_pi}")

        nombre_archivo = os.path.basename(ruta_modelo_pc)
        print(f"Inicializando protocolo de transferencia para [{nombre_archivo}]")
        print("Cargando modelo en Raspberry Pi. Por favor, espere.")

        # Iniciar cronómetro simple
        inicio = time.time()

        with SCPClient(ssh.get_transport()) as scp:
            # 1. Enviar modelo NCNN completo o archivo .pt
            scp.put(ruta_modelo_pc, remote_path=ruta_destino_pi, recursive=True)

            # --- NUEVO: ENVIAR METADATOS DEL MODELO ---
            # Si enviamos un .pt, buscamos el .json con el mismo nombre
            # Si enviamos una carpeta NCNN, buscamos el .json que la PC suele crear paralelo a ella
            metadata_local = ""
            if ruta_modelo_pc.endswith(".pt"):
                metadata_local = ruta_modelo_pc.replace(".pt", ".json")
            else:
                # Caso carpeta NCNN: buscamos un .json con el mismo nombre base en la carpeta padre
                ext = ".json"
                metadata_local = ruta_modelo_pc.rstrip("/") + ext
            
            if os.path.exists(metadata_local):
                print(f"Metadatos detectados: {os.path.basename(metadata_local)}. Sincronizando.")
                scp.put(metadata_local, remote_path=ruta_destino_pi)
            # ------------------------------------------

            # 2. Enviar archivo de configuración JSON para los Servos
            mapping_local = os.path.join(
                os.getcwd(), "Proyecto_FlexSort", "dataset", "servo_mapping.json"
            )
            if os.path.exists(mapping_local):
                print("Mapeo de servos detectado. Transfiriendo.")
                scp.put(mapping_local, remote_path=ruta_destino_pi)
            else:
                print("Aviso: No se encontro servo_mapping.json para enviar.")

            # 3. Transferir los scripts lógicos asegurando que la Pi tenga lo último
            # Vamos a mandar todo el contenido de la carpeta RaspberryPi_Code a la raíz de la app en la Pi
            ruta_scripts_locales = os.path.join(os.getcwd(), "RaspberryPi_Code")
            ruta_scripts_remota = "/home/pi/Desktop/Flex-Sort/" # Raíz del proyecto en Pi
            
            if os.path.exists(ruta_scripts_locales):
                print("Sincronizando codigo fuente con Raspberry Pi.")
                for item in os.listdir(ruta_scripts_locales):
                    item_path = os.path.join(ruta_scripts_locales, item)
                    if os.path.isfile(item_path):
                        scp.put(item_path, remote_path=ruta_scripts_remota)
                print("Codigo fuente Python sincronizado.")

            # 4. NUEVO: Transferir todo el firmware de Arduino para flasheo directo
            ruta_arduino_local = os.path.join(os.getcwd(), "Arduino_Code")
            if os.path.exists(ruta_arduino_local):
                print("Sincronizando codigo firmware para Arduino.")
                scp.put(ruta_arduino_local, remote_path=ruta_scripts_remota, recursive=True)
                print("Codigo C++ Firmware sincronizado.")

            duracion = round(time.time() - inicio, 1)

            # --- NUEVO: CREAR SELLO DE SINCRONIZACIÓN ---
            sync_data = {
                "fecha": time.strftime("%d/%m/%Y %H:%M:%S"),
                "modelo": nombre_archivo,
                "duracion_seg": duracion
            }
            sync_path_local = os.path.join(os.getcwd(), "last_sync.json")
            with open(sync_path_local, "w", encoding="utf-8") as fsync:
                json.dump(sync_data, fsync, indent=4)
            
            scp.put(sync_path_local, remote_path=ruta_scripts_remota)
            print("Sello de sincronizacion enviado correctamente.")
            # -------------------------------------------

            print(f"Carga exitosa. Archivo subido en {duracion} segundos.")

        print(f"Ruta remota: {ruta_destino_pi}{nombre_archivo}")

    except paramiko.ssh_exception.AuthenticationException:
        print("FALLO: Credenciales incorrectas. Verifique la configuracion.")
    except Exception as e:
        print(f"ERROR DE RED: {e}")
        print("Sugerencias:")
        print(" 1. ¿Modificaste la IP_RASPBERRY en '6_enviar_a_raspberry.py'?")
        print(" 2. ¿La Raspberry Pi está encendida y conectada al mismo WiFi/Red?")
        print(" 3. ¿Habilitaste 'SSH' en la configuración de la Raspberry?")
    finally:
        ssh.close()
        print("🔌 Canal de comunicación cerrado de forma segura.")


if __name__ == "__main__":
    # Obtenemos la ruta del modelo seleccionada en el Panel de Control
    if len(sys.argv) < 2:
        print("ERROR: No se proporciono la ruta del modelo.")
        sys.exit(1)

    modelo_generado = sys.argv[1]

    # La carpeta dentro de tu Raspberry donde van a vivir los modelos
    # Debe terminar con / para asegurar que entra en el directorio
    carpeta_en_pi = "/home/pi/Desktop/Flex-Sort/Modelos/"

    enviar_modelo_a_raspberry(modelo_generado, carpeta_en_pi)
