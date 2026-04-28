import os
import json
import time
import threading
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw, ImageFont
import cv2
from main import ScannerEngine
import contextlib

# Configuración Estética (Clon del Dashboard de PC)
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class RPiOperatorPanel(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FLEX-SORT | Industrial Dashboard")

        # Dimensiones para Raspberry Pi (Optimizado para visualización amplia)
        self.geometry("1200x850")
        self.configure(fg_color="#0A0A0A")

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
        self.engine.VELOCIDAD_CINTA_NEAR = self.config_data.get("belt_speed_near", 0.07)
        self.engine.VELOCIDAD_CINTA_FAR = self.config_data.get("belt_speed_far", 0.07)

        self.servo_labels = []
        self.assignment_labels = []


        self.setup_ui()

        # Intentar conectar hardware desde el arranque
        threading.Thread(target=self.engine.load_resources, daemon=True).start()

        self.update_stats_loop()
        self.check_sync_loop()

    def setup_ui(self):
        # ---------------- HEADER ----------------
        self.header = ctk.CTkFrame(self, height=70, corner_radius=0, fg_color="#111111")
        self.header.pack(side="top", fill="x")

        # Contenedor Título
        self.title_frame = ctk.CTkFrame(self.header, fg_color="#111111")
        self.title_frame.pack(side="left", padx=20, pady=10)

        self.lbl_brand = ctk.CTkLabel(
            self.title_frame, 
            text="FLEX-SORT", 
            font=ctk.CTkFont(family="Orbitron", size=24, weight="bold"),
            text_color="#1E88E5"
        )
        self.lbl_brand.pack(side="left")

        self.lbl_subtitle = ctk.CTkLabel(
            self.title_frame,
            text=" Panel de Operación · Raspberry Pi 5",
            font=ctk.CTkFont(size=12),
            text_color="#555555"
        )
        self.lbl_subtitle.pack(side="left", padx=(10, 0), pady=(5, 0))

        # Botones Derecha (Orden: RESET | HISTORIAL | AJUSTES)
        self.btn_conf = ctk.CTkButton(
            self.header, text="⚙ AJUSTES", width=100, height=35, fg_color="#1A1A1A", 
            hover_color="#333333", font=ctk.CTkFont(size=11, weight="bold"), cursor="hand2",
            command=lambda: [print("Ajustes"), self.open_settings()]
        )
        self.btn_conf.pack(side="right", padx=(5, 15))

        self.btn_hist = ctk.CTkButton(
            self.header, text="🕒 HISTORIAL", width=110, height=35, fg_color="#1A1A1A", 
            hover_color="#333333", font=ctk.CTkFont(size=11, weight="bold"), cursor="hand2",
            command=lambda: [print("Historial"), self.open_history()]
        )
        self.btn_hist.pack(side="right", padx=5)

        self.btn_reset = ctk.CTkButton(
            self.header, text="↺ RESET", width=90, height=35, fg_color="#b71c1c", 
            hover_color="#d32f2f", font=ctk.CTkFont(size=11, weight="bold"), cursor="hand2",
            command=lambda: [print("Reset"), self.confirm_reset()]
        )
        self.btn_reset.pack(side="right", padx=5)

        self.status_indicator = ctk.CTkLabel(
            self.header,
            text="● SISTEMA LISTO",
            text_color="#4CAF50",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.status_indicator.pack(side="right", padx=20)
        
        self.header.lift()

        # ---------------- BODY (Sidebar + Main) ----------------
        self.body_container = ctk.CTkFrame(self, fg_color="#0A0A0A")
        self.body_container.pack(side="top", fill="both", expand=True)

        # SIDEBAR
        self.sidebar = ctk.CTkFrame(self.body_container, width=280, corner_radius=0, fg_color="#0F0F0F")
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # MAIN AREA (Vision + Footer)
        self.main_area = ctk.CTkFrame(self.body_container, fg_color="#0A0A0A")
        self.main_area.pack(side="right", fill="both", expand=True)

        # Sección OPERACIÓN
        ctk.CTkLabel(
            self.sidebar, text="OPERACIÓN", font=ctk.CTkFont(size=11, weight="bold"), text_color="#333333"
        ).pack(anchor="w", padx=20, pady=(20, 5))

        self.btn_power = ctk.CTkButton(
            self.sidebar,
            text="▶ ENCENDER SCANNER",
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            corner_radius=8,
            cursor="hand2",
            command=lambda: [print("Click Power Scanner"), self.toggle_scanner()],
        )
        self.btn_power.pack(pady=10, padx=20, fill="x")

        # Sección CINTA
        self.cinta_frame = ctk.CTkFrame(self.sidebar, fg_color="#161616", corner_radius=10)
        self.cinta_frame.pack(pady=10, padx=20, fill="x")
        
        cinta_header = ctk.CTkFrame(self.cinta_frame, fg_color="transparent")
        cinta_header.pack(fill="x", padx=10, pady=(10, 0))
        
        ctk.CTkLabel(cinta_header, text="CINTA", font=ctk.CTkFont(size=11, weight="bold"), text_color="#555555").pack(side="left")
        self.btn_cinta_toggle = ctk.CTkButton(
            cinta_header, text="ON", fg_color="#2E7D32", text_color="white", 
            font=ctk.CTkFont(size=9, weight="bold"), corner_radius=4, width=40, height=20,
            cursor="hand2",
            command=self.toggle_cinta
        )
        self.btn_cinta_toggle.pack(side="right")

        self.cinta_on = False
        self.btn_cinta_toggle.configure(text="OFF", fg_color="#333333")

        val_row = ctk.CTkFrame(self.cinta_frame, fg_color="transparent")
        val_row.pack(fill="x", padx=10, pady=(5, 0))
        ctk.CTkLabel(val_row, text="Velocidad", font=ctk.CTkFont(size=11), text_color="#555555").pack(side="left")
        self.lbl_vel_val = ctk.CTkLabel(val_row, text="1200 p/s", font=ctk.CTkFont(size=11, weight="bold"), text_color="white")
        self.lbl_vel_val.pack(side="right")

        # Cargar velocidad guardada
        saved_speed = self.config_data.get("belt_speed_steps", 1200)
        self.cinta_slider = ctk.CTkSlider(self.cinta_frame, from_=200, to=1600, height=15, button_length=15, command=self.update_cinta_vel)
        self.cinta_slider.set(saved_speed)
        self.cinta_slider.pack(padx=10, pady=(5, 5), fill="x")
        self.lbl_vel_val.configure(text=f"{saved_speed} p/s")

        limits_row = ctk.CTkFrame(self.cinta_frame, fg_color="transparent")
        limits_row.pack(fill="x", padx=10, pady=(0, 5))
        ctk.CTkLabel(limits_row, text="200", font=ctk.CTkFont(size=9), text_color="#333333").pack(side="left")
        ctk.CTkLabel(limits_row, text="1600 p/s", font=ctk.CTkFont(size=9), text_color="#333333").pack(side="right")

        self.lbl_cinta_activa = ctk.CTkLabel(
            self.cinta_frame, text="○ APAGADA", font=ctk.CTkFont(size=10, weight="bold"), text_color="#555555"
        )
        self.lbl_cinta_activa.pack(anchor="w", padx=10, pady=(0, 5))

        # Switch para Modo Manual (Potenciómetro)
        self.sw_manual = ctk.CTkSwitch(
            self.cinta_frame, text="MODO MANUAL", font=ctk.CTkFont(size=10),
            command=self.toggle_manual, progress_color="#1E88E5"
        )
        self.sw_manual.pack(anchor="w", padx=10, pady=(0, 10))

        # Sección ÚLTIMO SYNC
        self.sync_frame = ctk.CTkFrame(self.sidebar, fg_color="#161616", corner_radius=10)
        self.sync_frame.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(
            self.sync_frame, text="ÚLTIMO SYNC SSH", font=ctk.CTkFont(size=11, weight="bold"), text_color="#555555"
        ).pack(anchor="w", padx=10, pady=(10, 5))
        self.lbl_sync_info = ctk.CTkLabel(
            self.sync_frame,
            text="Fecha: --/--/---- --:--\nModelo: --",
            font=ctk.CTkFont(size=10),
            text_color="#888888",
            justify="left"
        )
        self.lbl_sync_info.pack(anchor="w", padx=10, pady=(0, 10))

        # Sección HARDWARE
        ctk.CTkLabel(
            self.sidebar, text="HARDWARE", font=ctk.CTkFont(size=11, weight="bold"), text_color="#333333"
        ).pack(anchor="w", padx=20, pady=(15, 5))

        self.lbl_arduino_status = ctk.CTkLabel(
            self.sidebar,
            text="● microcontrolador: DESCONECTADO",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#F44336",
        )
        self.lbl_arduino_status.pack(anchor="w", padx=20)

        # Telemetría con Barras
        self.telemetry_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.telemetry_frame.pack(fill="x", padx=20, pady=10)

        # TEMP
        temp_row = ctk.CTkFrame(self.telemetry_frame, fg_color="transparent")
        temp_row.pack(fill="x", pady=2)
        ctk.CTkLabel(temp_row, text="TEMP", font=ctk.CTkFont(size=10), text_color="#555555").pack(side="left")
        self.lbl_temp_val = ctk.CTkLabel(temp_row, text="--°C", font=ctk.CTkFont(size=10), text_color="white")
        self.lbl_temp_val.pack(side="right")
        self.bar_temp = ctk.CTkProgressBar(self.telemetry_frame, height=6, progress_color="#1E88E5", fg_color="#1A1A1A")
        self.bar_temp.set(0)
        self.bar_temp.pack(fill="x", pady=(0, 5))

        # CPU
        cpu_row = ctk.CTkFrame(self.telemetry_frame, fg_color="transparent")
        cpu_row.pack(fill="x", pady=2)
        ctk.CTkLabel(cpu_row, text="CPU", font=ctk.CTkFont(size=10), text_color="#555555").pack(side="left")
        self.lbl_cpu_val = ctk.CTkLabel(cpu_row, text="--%", font=ctk.CTkFont(size=10), text_color="white")
        self.lbl_cpu_val.pack(side="right")
        self.bar_cpu = ctk.CTkProgressBar(self.telemetry_frame, height=6, progress_color="#1E88E5", fg_color="#1A1A1A")
        self.bar_cpu.set(0)
        self.bar_cpu.pack(fill="x", pady=(0, 5))

        # RAM
        ram_row = ctk.CTkFrame(self.telemetry_frame, fg_color="transparent")
        ram_row.pack(fill="x", pady=2)
        ctk.CTkLabel(ram_row, text="RAM", font=ctk.CTkFont(size=10), text_color="#555555").pack(side="left")
        self.lbl_ram_val = ctk.CTkLabel(ram_row, text="--%", font=ctk.CTkFont(size=10), text_color="white")
        self.lbl_ram_val.pack(side="right")
        self.bar_ram = ctk.CTkProgressBar(self.telemetry_frame, height=6, progress_color="#1E88E5", fg_color="#1A1A1A")
        self.bar_ram.set(0)
        self.bar_ram.pack(fill="x", pady=(0, 5))

        self.lbl_fps = ctk.CTkLabel(self.sidebar, text="-- FPS", font=ctk.CTkFont(size=14, weight="bold"), text_color="#333333")
        self.lbl_fps.pack(pady=5)

        # Consola (Simplificada para evitar problemas de eventos)
        ctk.CTkLabel(
            self.sidebar, text="CONSOLA DE EVENTOS", font=ctk.CTkFont(size=11, weight="bold"), text_color="#333333"
        ).pack(anchor="w", padx=20, pady=(10, 0))
        self.console_frame = ctk.CTkFrame(self.sidebar, fg_color="#080808", height=150)
        self.console_frame.pack(fill="x", padx=15, pady=5)
        self.console_frame.pack_propagate(False)
        
        self.lbl_console = ctk.CTkLabel(
            self.console_frame, text="> Sistema iniciado...\n> Esperando instrucciones.",
            font=("Consolas", 10), text_color="#4CAF50", justify="left", anchor="nw",
            padx=10, pady=10
        )
        self.lbl_console.pack(fill="both", expand=True)

        # ---------------- MAIN (VISIÓN) ----------------
        self.main_view = ctk.CTkFrame(self.main_area, corner_radius=10, fg_color="#000000")
        self.main_view.pack(fill="both", expand=True, padx=10, pady=10)

        # Canvas fijo para el video - NO usa fill/expand para no invadir el sidebar
        self.video_canvas = tk.Canvas(
            self.main_view, bg="black",
            highlightthickness=0,
            cursor="none"  # Sin cursor encima del video
        )
        self.video_canvas.pack(fill="both", expand=True)
        # Bloquear propagación de clics al contenedor padre
        self.video_canvas.bind("<Button-1>", lambda e: "break")
        self.video_canvas.bind("<Button-3>", lambda e: "break")
        # Recentrar imagen si el canvas cambia de tamaño
        self.video_canvas.bind("<Configure>", self._on_canvas_resize)
        self._canvas_img_id = None

        # Portada Inactiva: esperar a que el canvas tenga tamaño real
        self.portada_img = None
        self.after(200, self.set_portada)

        # ---------------- FOOTER (SERVO HUB) ----------------
        self.footer = ctk.CTkFrame(self.main_area, height=150, fg_color="#0A0A0A")
        self.footer.pack(fill="x", side="bottom", padx=10, pady=10)

        self.assignment_labels = []
        self.servo_labels = []
        for i in range(1, 5):
            f = ctk.CTkFrame(
                self.footer, width=180, height=140, corner_radius=10, fg_color="#161616"
            )
            f.pack(side="left", padx=5, expand=True, fill="both")
            f.pack_propagate(False)
            
            ctk.CTkLabel(
                f, text=f"SERVO {i}", font=ctk.CTkFont(size=10, weight="bold"), text_color="#555555"
            ).pack(pady=(10, 2))

            cmb_asig = ctk.CTkOptionMenu(
                f,
                values=["LIBRE"],
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#161616",
                button_color="#222222",
                button_hover_color="#333333",
                dropdown_font=ctk.CTkFont(size=12),
                text_color="#1E88E5",
                width=140,
                command=lambda val, servo_idx=i: self.change_servo_assignment(servo_idx, val)
            )
            cmb_asig.pack(pady=(0, 5))
            self.assignment_labels.append(cmb_asig)

            # Botón de Prueba Manual
            btn_test = ctk.CTkButton(
                f,
                text="TEST",
                width=80,
                height=28,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="#222222",
                hover_color="#333333",
                corner_radius=6,
                command=lambda x=i: self.test_servo(x),
            )
            btn_test.pack(pady=10)

            lbl_status = ctk.CTkLabel(
                f,
                text="LIBRE",
                text_color="#333333",
                font=ctk.CTkFont(size=12, weight="bold"),
            )
            lbl_status.pack(pady=(0, 5))
            self.servo_labels.append(lbl_status)

    def _on_canvas_resize(self, event):
        """Recentra la imagen en el canvas cuando cambia de tamaño."""
        if self._canvas_img_id is not None:
            self.video_canvas.coords(
                self._canvas_img_id,
                event.width // 2,
                event.height // 2
            )

    def toggle_scanner(self):
        if not self.engine.running:
            # Cargar mapeo antes de empezar
            if os.path.exists(self.mapping_path):
                with open(self.mapping_path) as f:
                    self.engine.set_mapping(json.load(f))

            if self.engine.load_resources():
                self.update_servo_assignments()
                self.btn_power.configure(
                    text="■ DETENER SCANNER", fg_color="#D32F2F", hover_color="#C62828"
                )
                self.engine.start(self.update_video_frame)
                self.status_indicator.configure(text="● ESCANEANDO", text_color="#1E88E5")
                # Al iniciar el scanner, forzar la velocidad actual de la cinta si está ON
                if self.cinta_on:
                    self.engine.set_belt_speed(int(self.cinta_slider.get()))
            else:
                messagebox.showerror("Error", self.engine.status_msg)
        else:
            self.engine.stop()
            self.btn_power.configure(
                text="▶ ENCENDER SCANNER", fg_color="#2E7D32", hover_color="#1B5E20"
            )
            self.status_indicator.configure(text="● SISTEMA LISTO", text_color="#4CAF50")
            # No forzamos el badge de cinta aquí, ya tiene su propio botón
            
            # Ejecucion redundante y retrasada para sobrevivir a hilos remanentes del modelo AI
            self.set_portada()
            self.after(200, self.set_portada)
            self.after(800, self.set_portada)

    def set_portada(self):
        # Crear una imagen negra dinámica de 740x480 (o tamaño del video_label)
        w, h = 800, 520 # Ajustado al nuevo tamaño de ventana
        img = Image.new("RGB", (w, h), color="#0F0F0F")
        draw = ImageDraw.Draw(img)
        
        # Dibujar guías verdes (Escaladas de 640x480 a 800x520)
        y_sup = int(90 * (h / 480))
        y_inf = int(400 * (h / 480))
        draw.line([(0, y_sup), (w, y_sup)], fill="#2E7D32", width=2)
        draw.line([(0, y_inf), (w, y_inf)], fill="#2E7D32", width=1)
        
        # Icono Pausa (Dos rectángulos)
        cx, cy = w // 2, h // 2
        draw.rectangle([cx - 10, cy - 60, cx - 4, cy - 30], fill="#333333")
        draw.rectangle([cx + 4, cy - 60, cx + 10, cy - 30], fill="#333333")
        
        # Texto Principal
        txt_main = "SCANNER INACTIVO"
        txt_sub = "Presiona ENCENDER SCANNER para iniciar"
        
        # Intentar cargar fuente, si falla usar default
        try:
            font_main = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except:
            font_main = ImageFont.load_default()
            font_sub = ImageFont.load_default()
            
        # Centrar texto
        draw.text((cx, cy), txt_main, fill="#555555", anchor="mm", font=font_main)
        draw.text((cx, cy + 35), txt_sub, fill="#333333", anchor="mm", font=font_sub)
        
        self.portada_img = ImageTk.PhotoImage(img)
        # Dibujar portada en el canvas
        cw = self.video_canvas.winfo_width() or w
        ch = self.video_canvas.winfo_height() or h
        if self._canvas_img_id is None:
            self._canvas_img_id = self.video_canvas.create_image(
                cw // 2, ch // 2, image=self.portada_img, anchor="center"
            )
        else:
            self.video_canvas.coords(self._canvas_img_id, cw // 2, ch // 2)
            self.video_canvas.itemconfig(self._canvas_img_id, image=self.portada_img)
        self.video_canvas.image = self.portada_img

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path) as f:
                return json.load(f)
        return {"confidence": 0.40, "belt_speed_near": 0.07, "belt_speed_far": 0.07}

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
        img_tk = ImageTk.PhotoImage(image=img)
        
        # Dibujar en el canvas en lugar de usar .configure(image=...)
        w = self.video_canvas.winfo_width()
        h = self.video_canvas.winfo_height()
        if w > 1 and h > 1:
            if self._canvas_img_id is None:
                self._canvas_img_id = self.video_canvas.create_image(
                    w // 2, h // 2, image=img_tk, anchor="center"
                )
            else:
                self.video_canvas.coords(self._canvas_img_id, w // 2, h // 2)
                self.video_canvas.itemconfig(self._canvas_img_id, image=img_tk)
        self.video_canvas.image = img_tk

    def update_servo_assignments(self):
        if not self.engine.model:
            return

        names = self.engine.model.names if hasattr(self.engine.model, "names") else {}
        
        # Obtener todas las clases disponibles
        all_classes = [name.upper() for name in names.values()]
        all_classes.insert(0, "LIBRE")
        
        # Reset labels / comboboxes
        for cmb in self.assignment_labels:
            cmb.configure(values=all_classes)
            cmb.set("LIBRE")

        # Configurar qué muestra cada combobox actualmente
        for obj_id, servo_id in self.engine.mapa_categorias.items():
            try:
                name = names.get(int(obj_id), f"ID:{obj_id}").upper()
                s_idx = int(servo_id) - 1
                if 0 <= s_idx < 4:
                    self.assignment_labels[s_idx].set(name)
            except Exception:  # noqa: BLE001
                pass

    def change_servo_assignment(self, servo_idx, object_name):
        if not self.engine.model:
            return
        
        names = self.engine.model.names if hasattr(self.engine.model, "names") else {}
        name_to_id = {v.upper(): str(k) for k, v in names.items()}
        
        # Si elige LIBRE, eliminamos cualquier objeto asignado a este servo
        if object_name == "LIBRE":
            to_delete = [k for k, v in self.engine.mapa_categorias.items() if str(v) == str(servo_idx)]
            for k in to_delete:
                del self.engine.mapa_categorias[k]
        elif object_name in name_to_id:
            # Reasignamos el objeto seleccionado a este servo
            obj_id = name_to_id[object_name]
            self.engine.mapa_categorias[obj_id] = str(servo_idx)
            
        # Guardar configuración permanentemente
        try:
            with open(self.mapping_path, "w") as f:
                json.dump(self.engine.mapa_categorias, f, indent=4)
            # Refrescar la UI por si hubo conflictos
            self.update_servo_assignments()
        except Exception as e:
            print(f"Error al guardar asignación: {e}")

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
                self.lbl_temp_val.configure(text=f"{t:.1f}°C")
                self.bar_temp.set(min(1.0, t / 100.0))
                if t > 75:
                    self.bar_temp.configure(progress_color="#F44336")
                else:
                    self.bar_temp.configure(progress_color="#1E88E5")
        except Exception:  # noqa: BLE001
            pass

        # CPU y RAM RPi
        try:
            # CPU
            load1, _, _ = os.getloadavg()
            cpu_cores = os.cpu_count() or 4
            cpu_pct = min(100.0, (load1 / cpu_cores) * 100)
            self.lbl_cpu_val.configure(text=f"{cpu_pct:.1f}%")
            self.bar_cpu.set(cpu_pct / 100.0)

            # RAM
            with open("/proc/meminfo") as f:
                lines = f.readlines()
            total = int(lines[0].split()[1])
            free = int(lines[1].split()[1])
            buffers = int(lines[3].split()[1])
            cached = int(lines[4].split()[1])
            used = total - free - buffers - cached
            ram_pct = (used / total) * 100
            self.lbl_ram_val.configure(text=f"{ram_pct:.1f}%")
            self.bar_ram.set(ram_pct / 100.0)
        except Exception:  # noqa: BLE001
            pass

        # FPS
        if hasattr(self.engine, "current_fps") and self.engine.running:
            self.lbl_fps.configure(text=f"FPS: {self.engine.current_fps:.1f}")
        else:
            self.lbl_fps.configure(text="FPS: --")

        # Arduino Status
        if self.engine.is_arduino_connected():
            self.lbl_arduino_status.configure(
                text="● microcontrolador: CONECTADO", text_color="#4CAF50"
            )
        else:
            self.lbl_arduino_status.configure(
                text="● microcontrolador: DESCONECTADO", text_color="#F44336"
            )

        # Servo Status based on queue
        if self.engine.running:
            occupied = [False] * 4
            for e in list(self.engine.cola_eventos):
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

    def confirm_shutdown(self):
        res = messagebox.askyesno(
            "Apagar Sistema",
            "¿Desea cerrar la aplicación y apagar la Raspberry Pi?",
            parent=self
        )
        if res:
            if self.engine.running:
                self.engine.stop()
            self.destroy()
            os.system("sudo shutdown -h now")

    def update_cinta_vel(self, val):
        speed = int(val)
        self.lbl_vel_val.configure(text=f"{speed} p/s")
        if self.cinta_on:
            self.engine.set_belt_speed(speed)
        # Persistir la velocidad
        self.config_data["belt_speed_steps"] = speed
        self.save_config()

    def toggle_cinta(self):
        self.cinta_on = not self.cinta_on
        if self.cinta_on:
            self.btn_cinta_toggle.configure(text="ON", fg_color="#2E7D32")
            self.lbl_cinta_activa.configure(text="● ACTIVA", text_color="#4CAF50")
            self.engine.set_belt_speed(int(self.cinta_slider.get()))
        else:
            self.btn_cinta_toggle.configure(text="OFF", fg_color="#333333")
            self.lbl_cinta_activa.configure(text="○ APAGADA", text_color="#555555")
            self.engine.set_belt_speed(0)


    def toggle_manual(self):
        is_manual = self.sw_manual.get()
        if is_manual:
            self.cinta_slider.configure(state="disabled")
            self.lbl_vel_val.configure(text="CONTROL FÍSICO", text_color="#1E88E5")
            self.engine.set_manual_mode(True)
        else:
            self.cinta_slider.configure(state="normal")
            self.lbl_vel_val.configure(text=f"{int(self.cinta_slider.get())} p/s", text_color="white")
            self.engine.set_manual_mode(False)
            if self.cinta_on:
                self.engine.set_belt_speed(int(self.cinta_slider.get()))

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
        
        # Velocidad de la Cinta (Cerca: 1 y 2)
        self.lbl_speed_near = ctk.CTkLabel(
            self, text=f"Velocidad (1 y 2) - Cerca: {self.parent.engine.VELOCIDAD_CINTA_NEAR:.2f}"
        )
        self.lbl_speed_near.pack(pady=(20, 0))
        
        self.speed_near_slider = ctk.CTkSlider(
            self, from_=0.01, to=0.30, command=self.update_speed_near
        )
        self.speed_near_slider.set(self.parent.engine.VELOCIDAD_CINTA_NEAR)
        self.speed_near_slider.pack(pady=5, padx=20, fill="x")

        # Velocidad de la Cinta (Lejos: 3 y 4)
        self.lbl_speed_far = ctk.CTkLabel(
            self, text=f"Velocidad (3 y 4) - Lejos: {self.parent.engine.VELOCIDAD_CINTA_FAR:.2f}"
        )
        self.lbl_speed_far.pack(pady=(15, 0))
        
        self.speed_far_slider = ctk.CTkSlider(
            self, from_=0.01, to=0.30, command=self.update_speed_far
        )
        self.speed_far_slider.set(self.parent.engine.VELOCIDAD_CINTA_FAR)
        self.speed_far_slider.pack(pady=5, padx=20, fill="x")

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


    def update_speed_near(self, val):
        self.lbl_speed_near.configure(text=f"Velocidad (1 y 2) - Cerca: {val:.2f}")
        self.parent.engine.VELOCIDAD_CINTA_NEAR = val
        self.parent.config_data["belt_speed_near"] = val

    def update_speed_far(self, val):
        self.lbl_speed_far.configure(text=f"Velocidad (3 y 4) - Lejos: {val:.2f}")
        self.parent.engine.VELOCIDAD_CINTA_FAR = val
        self.parent.config_data["belt_speed_far"] = val

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
