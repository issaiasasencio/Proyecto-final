import os
import json
import time
import threading
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image, ImageTk
import cv2
from main import ScannerEngine
import contextlib

# Configuración Estética (Clon del Dashboard de PC)
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class RPiOperatorPanel(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FLEX-SORT | Panel de Operacion (Raspberry Pi 5)")

        # Dimensiones para Raspberry Pi (VNC u Monitor HDMI)
        self.geometry("1024x720")

        # Rutas de Archivos en la Pi
        self.base_path = "/home/pi/Desktop/Flex-Sort/"
        self.modelos_dir = os.path.join(self.base_path, "Modelos")
        self.recursos_dir = os.path.join(self.base_path, "recursos")
        self.mapping_path = os.path.join(self.modelos_dir, "servo_mapping.json")
        self.sync_path = os.path.join(self.base_path, "last_sync.json")
        self.config_path = os.path.join(self.base_path, "pi_config.json")

        # Cargar Ajustes Persistentes
        self.config_data = self.load_config()

        # Inicializar Motor de IA
        default_model = self.config_data.get(
            "active_model", os.path.join(self.modelos_dir, "best_ncnn_model")
        )
        self.engine = ScannerEngine(default_model)
        self.engine.conf_threshold = self.config_data.get("confidence", 0.40)
        self.engine.VELOCIDAD_CINTA = self.config_data.get("belt_speed", 0.70 / 10.0)

        self.servo_labels = []
        self.assignment_labels = []

        # Layout principal
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)

        self.setup_ui()

        # Intentar conectar hardware desde el arranque
        threading.Thread(target=self.engine.load_resources, daemon=True).start()

        self.update_stats_loop()
        self.check_sync_loop()

    def setup_ui(self):
        # ---------------- HEADER ----------------
        self.header = ctk.CTkFrame(self, height=80, corner_radius=0, fg_color="#1A1A1A")
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew")

        # Logo (si existe)
        logo_path = os.path.join(self.recursos_dir, "logo_texto.png")
        if os.path.exists(logo_path):
            img = Image.open(logo_path)
            logo_img = ctk.CTkImage(img, size=(200, 45))
            self.logo = ctk.CTkLabel(self.header, image=logo_img, text="")
            self.logo.pack(side="left", padx=20, pady=10)
        else:
            self.logo = ctk.CTkLabel(
                self.header, text="FLEX-SORT", font=ctk.CTkFont(size=24, weight="bold")
            )
            self.logo.pack(side="left", padx=20)

        self.status_indicator = ctk.CTkLabel(
            self.header,
            text="SISTEMA LISTO",
            text_color="#4CAF50",
            font=ctk.CTkFont(weight="bold"),
        )
        self.status_indicator.pack(side="right", padx=20)

        # Botón Configuración (Engranaje)
        conf_path = os.path.join(self.recursos_dir, "config_icon.png")
        if os.path.exists(conf_path):
            img_c = ctk.CTkImage(Image.open(conf_path), size=(26, 26))
            self.btn_conf = ctk.CTkButton(
                self.header,
                text="",
                image=img_c,
                width=40,
                fg_color="transparent",
                hover_color="#333333",
                command=self.open_settings,
            )
            self.btn_conf.pack(side="right", padx=5)

        # Botón Historial (Reloj)
        hist_path = os.path.join(self.recursos_dir, "history_icon.png")
        if os.path.exists(hist_path):
            img_h = ctk.CTkImage(Image.open(hist_path), size=(26, 26))
            self.btn_hist = ctk.CTkButton(
                self.header,
                text="",
                image=img_h,
                width=40,
                fg_color="transparent",
                hover_color="#333333",
                command=self.open_history,
            )
            self.btn_hist.pack(side="right", padx=5)

        # Botón Factory Reset
        self.btn_reset = ctk.CTkButton(
            self.header,
            text="RESET",
            width=60,
            fg_color="#b71c1c",
            hover_color="#d32f2f",
            command=self.confirm_reset,
        )
        self.btn_reset.pack(side="right", padx=15)

        # ---------------- SIDEBAR (CONTROLES) ----------------
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)

        ctk.CTkLabel(
            self.sidebar,
            text="OPERACIÓN",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#1E88E5",
        ).pack(pady=(20, 10))

        self.btn_power = ctk.CTkButton(
            self.sidebar,
            text="ENCENDER SCANNER",
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            font=ctk.CTkFont(weight="bold"),
            height=50,
            command=self.toggle_scanner,
        )
        self.btn_power.pack(pady=10, padx=20, fill="x")

        # Sync Monitor
        self.sync_frame = ctk.CTkFrame(self.sidebar, fg_color="#222222")
        self.sync_frame.pack(pady=20, padx=20, fill="x")
        ctk.CTkLabel(
            self.sync_frame,
            text="ÚLTIMO RELEVAMIENTO (SSH)",
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(pady=5)
        self.lbl_sync_info = ctk.CTkLabel(
            self.sync_frame,
            text="Sincronizando...",
            font=ctk.CTkFont(size=10),
            text_color="#AAAAAA",
        )
        self.lbl_sync_info.pack(pady=5)

        # Monitor Hardware
        self.hw_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.hw_frame.pack(pady=(20, 5), padx=20, fill="x")
        ctk.CTkLabel(
            self.hw_frame,
            text="ESTADO HARDWARE",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#1E88E5",
        ).pack(anchor="center")

        self.lbl_arduino_status = ctk.CTkLabel(
            self.hw_frame,
            text="Arduino: DESCONECTADO",
            font=ctk.CTkFont(size=11),
            text_color="#F44336",
        )
        self.lbl_arduino_status.pack(anchor="center")

        self.lbl_temp = ctk.CTkLabel(self.sidebar, text="Temp: --°C")
        self.lbl_temp.pack(anchor="center")

        self.lbl_cpu = ctk.CTkLabel(self.sidebar, text="CPU: --%", text_color="#AAAAAA")
        self.lbl_cpu.pack(anchor="center")

        self.lbl_ram = ctk.CTkLabel(self.sidebar, text="RAM: --%", text_color="#AAAAAA")
        self.lbl_ram.pack(anchor="center")

        # ---------------- MAIN (VISIÓN) ----------------
        self.main_view = ctk.CTkFrame(self, corner_radius=10, fg_color="#000000")
        self.main_view.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

        self.video_label = tk.Label(self.main_view, bg="black")
        self.video_label.pack(expand=True, fill="both")

        # Portada Inactiva
        self.portada_img = None
        self.set_portada()

        # ---------------- FOOTER (SERVO HUB) ----------------
        self.footer = ctk.CTkFrame(self, height=140, fg_color="transparent")
        self.footer.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=5)

        self.servo_labels = []
        for i in range(1, 5):
            f = ctk.CTkFrame(
                self.footer, height=130, border_width=2, border_color="#333333"
            )
            f.pack(side="left", padx=10, expand=True, fill="x")
            f.pack_propagate(False)
            ctk.CTkLabel(
                f, text=f"SERVO {i}", font=ctk.CTkFont(size=12, weight="bold")
            ).pack(pady=(8, 2))

            lbl_asig = ctk.CTkLabel(
                f,
                text="(Sin asignar)",
                font=ctk.CTkFont(size=11, slant="italic"),
                text_color="#AAAAAA",
            )
            lbl_asig.pack()
            self.assignment_labels.append(lbl_asig)

            # Botón de Prueba Manual (Centrado y más ancho)
            btn_test = ctk.CTkButton(
                f,
                text="TEST",
                width=100,
                height=24,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="#333333",
                hover_color="#444444",
                command=lambda x=i: self.test_servo(x),
            )
            btn_test.pack(pady=(5, 0), anchor="center")

            lbl_status = ctk.CTkLabel(
                f,
                text="LIBRE",
                text_color="#666666",
                font=ctk.CTkFont(size=16, weight="bold"),
            )
            lbl_status.pack(pady=(5, 8), anchor="center")
            self.servo_labels.append(lbl_status)

    def toggle_scanner(self):
        if not self.engine.running:
            # Cargar mapeo antes de empezar
            if os.path.exists(self.mapping_path):
                with open(self.mapping_path) as f:
                    self.engine.set_mapping(json.load(f))

            if self.engine.load_resources():
                self.update_servo_assignments()
                self.btn_power.configure(
                    text="DETENER SCANNER", fg_color="#D32F2F", hover_color="#C62828"
                )
                self.engine.start(self.update_video_frame)
                self.status_indicator.configure(text="ESCANEANDO", text_color="#1E88E5")
            else:
                messagebox.showerror("Error", self.engine.status_msg)
        else:
            self.engine.stop()
            self.btn_power.configure(
                text="ENCENDER SCANNER", fg_color="#2E7D32", hover_color="#1B5E20"
            )
            self.status_indicator.configure(text="SISTEMA LISTO", text_color="#4CAF50")
            
            # Ejecucion redundante y retrasada para sobrevivir a hilos remanentes del modelo AI
            self.set_portada()
            self.after(200, self.set_portada)
            self.after(800, self.set_portada)

    def set_portada(self):
        portada_path = os.path.join(self.recursos_dir, "portada.png")
        if os.path.exists(portada_path):
            try:
                img = Image.open(portada_path)
                img = img.resize((740, 480))  # Quitamos LANCZOS para evitar errores de compatibilidad
                self.portada_img = ImageTk.PhotoImage(img)
                self.video_label.configure(image=self.portada_img)
            except Exception as e:
                print("Error portada:", e)
                self.portada_img = None
                self.video_label.configure(image="")
        else:
            self.portada_img = None
            self.video_label.configure(image="")

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path) as f:
                return json.load(f)
        return {"confidence": 0.40, "belt_speed": 0.07}

    def save_config(self):
        with open(self.config_path, "w") as f:
            json.dump(self.config_data, f, indent=4)

    def open_settings(self):
        SettingsDialog(self)

    def open_history(self):
        HistoryDialog(self)

    def confirm_reset(self):
        res = messagebox.askyesno(
            "Reset de Fabrica",
            (
                "ESTA SEGURO que desea ELIMINAR todos los entrenamientos, modelos "
                "y configuracion de servos?\n\nEsta accion dejara la placa "
                "como nueva y no se puede deshacer."
            ),
            parent=self,
        )
        if res:
            self.status_indicator.configure(text="FORMATEANDO...", text_color="#F44336")
            self.update()

            if self.engine.running:
                self.engine.stop()

            time.sleep(0.5)
            # Eliminar todos los modelos (*.pt y *_ncnn_model)
            if os.path.exists(self.modelos_dir):
                import shutil

                for f in os.listdir(self.modelos_dir):
                    if (
                        f.endswith(".pt")
                        or f.endswith("_ncnn_model")
                        or (f.endswith(".json") and f != "servo_mapping.json")
                    ):
                        path = os.path.join(self.modelos_dir, f)
                        try:
                            if os.path.isdir(path):
                                shutil.rmtree(path)
                            else:
                                os.remove(path)
                        except Exception:  # noqa: BLE001
                            pass

            # Eliminar mapeo
            if os.path.exists(self.mapping_path):
                with contextlib.suppress(Exception):
                    os.remove(self.mapping_path)

            self.engine.set_mapping({})  # Vaciar mapeo en RAM
            self.update_servo_assignments()

            messagebox.showinfo(
                "Reset Exitoso",
                "El sistema ha sido purgado correctamente.",
                parent=self,
            )
            self.status_indicator.configure(
                text="● SISTEMA LISTO", text_color="#4CAF50"
            )

    def test_servo(self, servo_id):
        """Envía un pulso de prueba al servo sin necesidad de que
        el scanner esté prendido."""
        # Intentar conectar si no lo está
        if not self.engine.arduino_ready:
            self.engine.load_resources()

        if self.engine.send_manual_cmd(str(servo_id)):
            # Feedback visual momentáneo
            idx = servo_id - 1
            self.servo_labels[idx].configure(text="TESTING", text_color="#F57C00")
            self.after(
                1000,
                lambda: self.servo_labels[idx].configure(
                    text="LIBRE", text_color="#666666"
                ),
            )
        else:
            messagebox.showwarning(
                "Hardware",
                (
                    f"No se pudo enviar comando al Servo {servo_id}. "
                    "Verifique la conexion del Arduino."
                ),
            )

    def update_video_frame(self, frame):
        # Abortar dibujado de frames retrasados en caso de apagado
        if not self.engine.running:
            return
            
        # Convertir a imagen de Tkinter
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        # Redimensionar para encajar perfectamente si es necesario
        img_tk = ImageTk.PhotoImage(image=img)
        self.video_label.configure(image=img_tk)
        self.video_label.image = img_tk

    def update_servo_assignments(self):
        # Reset labels
        for lbl in self.assignment_labels:
            lbl.configure(text="(Sin asignar)", text_color="#AAAAAA")

        if not self.engine.model:
            return

        # Revertir el mapa: Categoría -> Servo
        # self.engine.mapa_categorias es { "id_objeto": "id_servo" }
        # Necesitamos los nombres reales de ScannerEngine.model.names
        names = self.engine.model.names if hasattr(self.engine.model, "names") else {}

        for obj_id, servo_id in self.engine.mapa_categorias.items():
            try:
                name = names.get(int(obj_id), f"ID:{obj_id}").upper()
                s_idx = int(servo_id) - 1
                if 0 <= s_idx < 4:
                    self.assignment_labels[s_idx].configure(
                        text=name, text_color="#1E88E5"
                    )
            except Exception:  # noqa: BLE001
                pass

    def check_sync_loop(self):
        if os.path.exists(self.sync_path):
            try:
                with open(self.sync_path) as f:
                    data = json.load(f)
                    txt = f"Fecha: {data['fecha']}\nModelo: {data['modelo']}"
                    self.lbl_sync_info.configure(text=txt, text_color="#A5D6A7")
            except Exception:  # noqa: BLE001
                pass
        self.after(5000, self.check_sync_loop)

    def update_stats_loop(self):
        # Temp RPi
        try:
            with open("/sys/class/thermal/thermal_zone0/temp") as f:
                t = int(f.read()) / 1000
                self.lbl_temp.configure(
                    text=f"Temp: {t:.1f}°C",
                    text_color="#F44336" if t > 70 else "#AAAAAA",
                )
        except Exception:  # noqa: BLE001
            pass

        # CPU y RAM RPi
        try:
            # CPU
            load1, _, _ = os.getloadavg()
            cpu_cores = os.cpu_count() or 4
            cpu_pct = min(100.0, (load1 / cpu_cores) * 100)
            self.lbl_cpu.configure(text=f"CPU: {cpu_pct:.1f}%")

            # RAM
            with open("/proc/meminfo") as f:
                lines = f.readlines()
            total = int(lines[0].split()[1])
            free = int(lines[1].split()[1])
            buffers = int(lines[3].split()[1])
            cached = int(lines[4].split()[1])
            used = total - free - buffers - cached
            ram_pct = (used / total) * 100
            self.lbl_ram.configure(text=f"RAM: {ram_pct:.1f}%")
        except Exception:  # noqa: BLE001
            pass

        # Arduino Status
        if self.engine.is_arduino_connected():
            self.lbl_arduino_status.configure(
                text="Arduino: CONECTADO", text_color="#4CAF50"
            )
        else:
            self.lbl_arduino_status.configure(
                text="Arduino: DESCONECTADO", text_color="#F44336"
            )

        # Servo Status based on queue
        if self.engine.running:
            occupied = [False] * 4
            for e in self.engine.cola_eventos:
                idx = int(e["letra"]) - 1
                if 0 <= idx < 4:
                    occupied[idx] = True
                    self.servo_labels[idx].configure(
                        text="OCUPADO", text_color="#F57C00"
                    )

            for index, is_occ in enumerate(occupied):
                if not is_occ:
                    self.servo_labels[index].configure(
                        text="LIBRE", text_color="#666666"
                    )

        self.after(500, self.update_stats_loop)


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Ajustes de Operación")
        self.geometry("400x450")
        # Cambio fundamental: transient en vez de topmost evita bloqueos de clicks en Linux/Wayland
        self.transient(parent)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self, text="CONFIGURACION LOCAL", font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=20)

        # Umbral de Confianza
        self.lbl_conf_val = ctk.CTkLabel(
            self, text=f"Umbral de Confianza: {self.parent.engine.conf_threshold:.2f}"
        )
        self.lbl_conf_val.pack(pady=(10, 0))
        
        self.conf_slider = ctk.CTkSlider(
            self, from_=0.1, to=0.9, command=self.update_conf
        )
        self.conf_slider.set(self.parent.engine.conf_threshold)
        self.conf_slider.pack(pady=5, padx=20, fill="x")
        
        # Velocidad de la Cinta (Dinámica)
        self.lbl_speed_val = ctk.CTkLabel(
            self, text=f"Velocidad Transportadora: {self.parent.engine.VELOCIDAD_CINTA:.2f}"
        )
        self.lbl_speed_val.pack(pady=(20, 0))
        
        self.speed_slider = ctk.CTkSlider(
            self, from_=0.01, to=0.30, command=self.update_speed
        )
        self.speed_slider.set(self.parent.engine.VELOCIDAD_CINTA)
        self.speed_slider.pack(pady=5, padx=20, fill="x")

        ctk.CTkButton(
            self, text="Calibrar Servos de Arduino", fg_color="#1E88E5", command=self.open_calibration
        ).pack(pady=10)

        ctk.CTkButton(
            self, text="Cerrar Ajustes", fg_color="#2E7D32", command=self.apply
        ).pack(pady=10)

    def open_calibration(self):
        # Asegurar que el arduino esta inicializado por la app
        if not self.parent.engine.arduino_ready:
            messagebox.showwarning("Error Hardware", "El Arduino no esta conectado. Verifique la conexion USB y encienda el Scanner al menos una vez para inicializar los puertos.")
            return
        HardwareCalibrationDialog(self.parent)


    def update_speed(self, val):
        self.lbl_speed_val.configure(text=f"Velocidad Transportadora: {val:.2f}")
        self.parent.engine.VELOCIDAD_CINTA = val
        self.parent.config_data["belt_speed"] = val

    def update_conf(self, val):
        self.lbl_conf_val.configure(text=f"Umbral de Confianza: {val:.2f}")
        self.parent.engine.conf_threshold = val
        self.parent.config_data["confidence"] = val

    def apply(self):
        self.parent.save_config()
        self.destroy()

class HardwareCalibrationDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Calibrar Servos de Arduino")
        self.geometry("450x300")
        self.transient(parent)
        self.attributes('-topmost', True)
        
        ctk.CTkLabel(self, text="Ajuste de Límites Maximos (Golpe)", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        ctk.CTkLabel(self, text="Mueve los sliders. Se enviará la instruccion directa por Serial.", font=ctk.CTkFont(size=11), text_color="#FF9800").pack(pady=(0,10))
        
        self.sliders = []
        for i in range(1, 5):
            f = ctk.CTkFrame(self, fg_color="transparent")
            f.pack(fill="x", padx=20, pady=5)
            
            ctk.CTkLabel(f, text=f"Servo {i}", width=50).pack(side="left")
            
            val_lbl = ctk.CTkLabel(f, text="90°", width=40)
            val_lbl.pack(side="right")
            
            sl = ctk.CTkSlider(f, from_=0, to=180, command=lambda val, idx=i, lbl=val_lbl: self.update_and_send(idx, val, lbl))
            sl.set(90)
            sl.pack(side="left", fill="x", expand=True, padx=10)
            self.sliders.append(sl)

    def update_and_send(self, servo_id, angle, label):
        ang_int = int(angle)
        label.configure(text=f"{ang_int}°")
        # Enviar comando LOCALMENTE al puerto serial ya reservado por ScannerEngine
        try:
            # Mandamos la cadena M1:90\n
            packet = f"M{servo_id}:{ang_int}\n".encode()
            self.parent.engine.arduino.write(packet)
        except Exception as e:
            print(f"Error escribiendo al serial: {e}")

class HistoryDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Historial de Modelos")
        self.geometry("600x650")  # Mas ancho para los detalles
        self.attributes("-topmost", True)

        ctk.CTkLabel(
            self, text="HISTORIAL DE CEREBROS", font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=20)

        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=10)

        self.load_models()

    def load_models(self):
        base_dir = self.parent.modelos_dir
        items = [
            d
            for d in os.listdir(base_dir)
            if d.endswith("_ncnn_model") or d.endswith(".pt")
        ]

        # Recolectar datos y fechas para ordenar
        model_data_list = []
        for m in items:
            m_path = os.path.join(base_dir, m)
            # Metadatos
            meta_path = (
                m_path.replace(".pt", ".json")
                if m.endswith(".pt")
                else m_path.rstrip("/") + ".json"
            )

            meta_info = {}
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, encoding="utf-8") as f:
                        meta_info = json.load(f)
                except Exception:  # noqa: BLE001
                    pass

            # Timestamp para ordenar (prioridad al del JSON, sino fecha archivo)
            try:
                date_str = meta_info.get("fecha", "")
                if date_str:
                    ts = time.mktime(time.strptime(date_str, "%d/%m/%Y %H:%M:%S"))
                else:
                    ts = os.path.getmtime(m_path)
            except Exception:  # noqa: BLE001
                ts = os.path.getmtime(m_path)

            model_data_list.append(
                {"name": m, "path": m_path, "timestamp": ts, "meta": meta_info}
            )

        # Ordenar: Más nuevo primero
        model_data_list.sort(key=lambda x: x["timestamp"], reverse=True)

        if not model_data_list:
            ctk.CTkLabel(self.scroll, text="No hay modelos encontrados.").pack()
            return

        for data in model_data_list:
            m = data["name"]
            meta = data["meta"]

            # Tarjeta de Modelo
            f = ctk.CTkFrame(
                self.scroll, corner_radius=10, border_width=1, border_color="#333333"
            )
            f.pack(fill="x", pady=8, padx=5)

            # Fila Superior: Nombre y Botón
            top_row = ctk.CTkFrame(f, fg_color="transparent")
            top_row.pack(fill="x", padx=10, pady=(5, 0))

            ctk.CTkLabel(
                top_row,
                text=m,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#1E88E5",
            ).pack(side="left")
            btn = ctk.CTkButton(
                top_row,
                text="Activar",
                width=80,
                height=24,
                fg_color="#1E88E5",
                hover_color="#1565C0",
                command=lambda x=m: self.activate(x),
            )
            btn.pack(side="right")

            # Cuerpo: Detalles
            details = ctk.CTkFrame(f, fg_color="transparent")
            details.pack(fill="x", padx=15, pady=5)

            fecha = meta.get(
                "fecha",
                time.strftime("%d/%m/%y %H:%M", time.localtime(data["timestamp"])),
            )
            ctk.CTkLabel(
                details,
                text=f"Fecha: {fecha}",
                font=ctk.CTkFont(size=10),
                text_color="#888888",
            ).pack(anchor="w")

            objs = meta.get("objetos", [])
            mapping = meta.get("servos", {})

            # Resumen de entrenamiento
            if objs:
                resumen = " | ".join(
                    [f"{o.upper()} (S{mapping.get(o, '?')})" for o in objs]
                )
                ctk.CTkLabel(
                    details,
                    text=f"Objetos: {resumen}",
                    font=ctk.CTkFont(size=11),
                    wraplength=400,
                    justify="left",
                ).pack(anchor="w", pady=2)

            # Precisión
            acc = meta.get("precision", meta.get("mAP50", "N/A"))
            if acc != "N/A":
                try:
                    score = float(acc)
                    color = (
                        "#4CAF50"
                        if score > 0.8
                        else "#FFC107"
                        if score > 0.5
                        else "#F44336"
                    )
                    score_txt = (
                        f"{score * 100:.1f}%" if score <= 1.0 else f"{score:.1f}"
                    )
                    ctk.CTkLabel(
                        details,
                        text=f"Precision: {score_txt}",
                        font=ctk.CTkFont(size=11, weight="bold"),
                        text_color=color,
                    ).pack(anchor="w")
                except Exception:  # noqa: BLE001
                    ctk.CTkLabel(
                        details, text=f"Precision: {acc}", font=ctk.CTkFont(size=11)
                    ).pack(anchor="w")

    def activate(self, model_name):
        full_path = os.path.join(self.parent.modelos_dir, model_name)
        was_running = self.parent.engine.running
        if was_running:
            self.parent.engine.stop()

        self.parent.engine.model_path = full_path
        self.parent.config_data["active_model"] = full_path
        self.parent.save_config()

        if was_running:
            self.parent.toggle_scanner()  # Reiniciar
        self.destroy()
        messagebox.showinfo("Modelo Cambiado", f"Se ha activado: {model_name}")


if __name__ == "__main__":
    app = RPiOperatorPanel()
    app.mainloop()
