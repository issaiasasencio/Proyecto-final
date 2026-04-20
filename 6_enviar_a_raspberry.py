import sys
import os
import time
import paramiko
from scp import SCPClient

# Forzar salida en UTF-8 para evitar errores con los emojis en la consola de Windows
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def enviar_modelo_a_raspberry(ruta_modelo_pc, ruta_destino_pi):
    # =========================================================================
    # ¡IMPORTANTE! EDITA ESTAS CREDENCIALES CON LOS DATOS DE TU RASPBERRY PI
    # =========================================================================
    ip_raspberry = '192.168.1.10'  # <-- Modifica esta IP
    usuario = 'pi'                  # <-- Modifica si no usas 'pi'
    contrasena = '12345678'        # <-- Modifica con tu contraseña real
    # =========================================================================
    
    print(f"\n[TRANSFERENCIA EDGE]")
    print(f"📡 Intentando conectar con {ip_raspberry}...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) 

    try:
        # Timeout de 5 segundos para que te des cuenta rápido si la IP está mal
        ssh.connect(hostname=ip_raspberry, username=usuario, password=contrasena, timeout=5)
        print("✅ Conexión P2P (SSH) establecida...")

        # Nos aseguramos de que el directorio remoto exista
        ssh.exec_command(f"mkdir -p {ruta_destino_pi}")
        
        nombre_archivo = os.path.basename(ruta_modelo_pc)
        print(f"📤 Inicializando protocolo de transferencia para [{nombre_archivo}]")
        print("⏳ Subiendo el cerebro a la Raspberry Pi... Por favor esperá.")
        
        # Iniciar cronómetro simple
        inicio = time.time()
        
        with SCPClient(ssh.get_transport()) as scp:
            # recursive=True permite enviar carpetas enteras (ej. formato NCNN) o archivos
            scp.put(ruta_modelo_pc, remote_path=ruta_destino_pi, recursive=True)
            
            # NUEVO: Enviar archivo de configuración JSON para los Servos
            mapping_local = os.path.join(os.getcwd(), "Proyecto_Cinta", "dataset", "servo_mapping.json")
            if os.path.exists(mapping_local):
                print("⚙️ Detectado mapeo de servos local. Transfiriendo configuración...")
                scp.put(mapping_local, remote_path=ruta_destino_pi)
            else:
                print("⚠️ Aviso: No se encontró servo_mapping.json para enviar.")
            
        duracion = round(time.time() - inicio, 1)
        print(f"📦 ¡Carga exitosa! Archivo subido en {duracion} segundos.")
        print(f"Ruta remota: {ruta_destino_pi}{nombre_archivo}")

    except paramiko.ssh_exception.AuthenticationException:
        print("❌ FALLO: Contraseña o usuario incorrecto. Verificá las variables en el script.")
    except Exception as e:
        print(f"❌ ERROR DE RED: {e}")
        print("Sugerencias:")
        print(" 1. ¿Modificaste la IP_RASPBERRY en el script '6_enviar_a_raspberry.py'?")
        print(" 2. ¿La Raspberry Pi está encendida y conectada al mismo WiFi/Red?")
        print(" 3. ¿Habilitaste 'SSH' en la configuración de la Raspberry?")
    finally:
        ssh.close()
        print("🔌 Canal de comunicación cerrado de forma segura.")

if __name__ == "__main__":
    # Obtenemos la ruta del modelo seleccionada en el Panel de Control
    if len(sys.argv) < 2:
        print("FATAL: No se proporcionó la ruta del modelo.")
        sys.exit(1)
        
    modelo_generado = sys.argv[1]
    
    # La carpeta dentro de tu Raspberry donde van a vivir los modelos
    # Debe terminar con / para asegurar que entra en el directorio
    carpeta_en_pi = "/home/pi/Desktop/Deteccion/Modelos/"
    
    enviar_modelo_a_raspberry(modelo_generado, carpeta_en_pi)
