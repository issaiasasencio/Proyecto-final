import json
import os
import shutil
import subprocess
import sys
import threading
import time
from tkinter import filedialog, messagebox, simpledialog

import customtkinter as ctk
from PIL import Image

# Configuración global de entorno Moderno
ctk.set_appearance_mode("Dark")  # Opciones: "Dark", "Light"
ctk.set_default_color_theme("blue")  # Opciones: "blue", "green", "dark-blue"


class ServoSelectorDialog(ctk.CTkToplevel):
    def __init__(self, parent, categoria):
        super().__init__(parent)
        self.title("Asignación de Hardware Físico")
        
        # Dimensiones y centrado
        w, h = 500, 350
        x = int((self.winfo_screenwidth() / 2) - (w / 2))
        y = int((self.winfo_screenheight() / 2) - (h / 2))
        self.geometry(f"{w}x{h}+{x}+{y}")
        
        self.servo_id = None

        # Mantener ventana al frente y modal
        self.attributes('-topmost', True)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        lbl = ctk.CTkLabel(
            self,
            text=(
                f"Objeto: {categoria.upper()}\n\n"
                "Seleccioná el brazo expulsor de destino\n"
                "(Vista superior de la cinta):"
            ),
            font=ctk.CTkFont(size=16, weight="bold")
        )
        lbl.pack(pady=(20, 10))

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(pady=10, padx=20, fill="both", expand=True)

        # Grid layout (2x2)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        def select(val):
            self.servo_id = val
            self.destroy()

        btn_font = ctk.CTkFont(size=18, weight="bold")

        btn1 = ctk.CTkButton(frame, text="1\n(Izquierdo cerca)", font=btn_font, corner_radius=15,
                             fg_color="#1E88E5", hover_color="#1565C0", command=lambda: select('1'))
        btn1.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        btn2 = ctk.CTkButton(frame, text="2\n(Derecho cerca)", font=btn_font, corner_radius=15,
                             fg_color="#1E88E5", hover_color="#1565C0", command=lambda: select('2'))
        btn2.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        btn3 = ctk.CTkButton(frame, text="3\n(Izquierdo lejos)", font=btn_font, corner_radius=15,
                             fg_color="#F57C00", hover_color="#E65100", command=lambda: select('3'))
        btn3.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        btn4 = ctk.CTkButton(frame, text="4\n(Derecho lejos)", font=btn_font, corner_radius=15,
                             fg_color="#F57C00", hover_color="#E65100", command=lambda: select('4'))
        btn4.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")


class HistoryDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Historial de Inteligencia Artificial")
        self.geometry("500x450")
        self.parent = parent
        self.archive_dir = os.path.join("Proyecto_Cinta", "modelos_archivados")
        self.config_path = "config.json"

        # Centrar
        w, h = 500, 450
        x = int((self.winfo_screenwidth() / 2) - (w / 2))
        y = int((self.winfo_screenheight() / 2) - (h / 2))
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.attributes('-topmost', True)
        self.transient(parent)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkLabel(self, text="📚 Modelos Archivados", font=ctk.CTkFont(size=20, weight="bold"))
        header.grid(row=0, column=0, pady=20)

        # Scrollable list
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Versiones Guardadas")
        self.scroll_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

        self.load_history()

    def load_history(self):
        if not os.path.exists(self.archive_dir):
            os.makedirs(self.archive_dir, exist_ok=True)

        files = [f for f in os.listdir(self.archive_dir) if f.endswith(".pt")]
        # Ordenar por fecha de modificación (Más nuevo arriba)
        files.sort(key=lambda x: os.path.getmtime(os.path.join(self.archive_dir, x)), reverse=True)

        if not files:
            ctk.CTkLabel(self.scroll_frame, text="No hay modelos guardados aún.").pack(pady=20)
            return

        for f in files:
            f_path = os.path.join(self.archive_dir, f)
            metadata_path = f_path.replace(".pt", ".json")
            
            # Datos básicos por defecto
            mtime = time.strftime("%d/%m/%Y %H:%M", time.localtime(os.path.getmtime(f_path)))
            description = "Sin metadatos detallados"
            
            # Cargar metadatos si existen
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, "r", encoding="utf-8") as meta_f:
                        meta_data = json.load(meta_f)
                        mtime = meta_data.get("fecha", mtime)
                        objetos = meta_data.get("objetos", [])
                        if objetos:
                            description = "📦 Objetos: " + ", ".join(
                                [f"{o['nombre']} (S{o['servo']})" for o in objetos]
                            )
                except Exception:
                    pass

            item_frame = ctk.CTkFrame(self.scroll_frame)
            item_frame.pack(fill="x", pady=8, padx=5)

            # Contenedor de texto
            text_container = ctk.CTkFrame(item_frame, fg_color="transparent")
            text_container.pack(side="left", padx=10, pady=5, fill="both", expand=True)

            ctk.CTkLabel(text_container, text=f, font=ctk.CTkFont(size=13, weight="bold"),
                        anchor="w").pack(fill="x")
            ctk.CTkLabel(text_container, text=f"Fecha: {mtime}", font=ctk.CTkFont(size=11),
                        text_color="#AAAAAA", anchor="w").pack(fill="x")
            
            # Color distintivo para la lista de objetos
            lbl_desc = ctk.CTkLabel(text_container, text=description, font=ctk.CTkFont(size=11),
                                    text_color="#4CAF50", anchor="w", wraplength=300, justify="left")
            lbl_desc.pack(fill="x")

            btn_activate = ctk.CTkButton(item_frame, text="Activar", width=80,
                                         fg_color="#1E88E5", hover_color="#1565C0",
                                         command=lambda p=f_path: self.activate_model(p))
            btn_activate.pack(side="right", padx=10)

    def activate_model(self, path):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            config["active_model"] = path
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
            
            messagebox.showinfo("Éxito", f"Modelo activo cambiado a:\n{os.path.basename(path)}")
            self.parent.log(f"\n[HISTORIAL] Modelo activo seleccionado: {os.path.basename(path)}")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo activar el modelo: {e}")


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Ajustes del Sistema FLEX-SORT")
        
        # Dimensiones y centrado
        w, h = 450, 550
        x = int((self.winfo_screenwidth() / 2) - (w / 2))
        y = int((self.winfo_screenheight() / 2) - (h / 2))
        self.geometry(f"{w}x{h}+{x}+{y}")
        
        self.config_path = "config.json"

        # Cargar configuración actual
        self.config_data = self.load_config()

        # Modal
        self.attributes('-topmost', True)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Layout
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(self, text="⚙️ Configuración Maestra", font=ctk.CTkFont(size=20, weight="bold"))
        header.pack(pady=(20, 10))

        # --- SECCIÓN: RED ---
        frame_red = ctk.CTkFrame(self)
        frame_red.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(frame_red, text="CONEXIÓN RASPBERRY PI", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#1E88E5").pack(pady=5)

        self.pass_entry = self.create_input(
            frame_red, "Contraseña SSH:", self.config_data.get("contrasena", "12345678"), show="*"
        )

        # Botón de Ping
        self.btn_ping = ctk.CTkButton(frame_red, text="📡 Probar Conexión (Ping)", command=self.run_ping_test,
                                      fg_color="#333333", hover_color="#444444")
        self.btn_ping.pack(pady=10, padx=10, fill="x")

        self.lbl_ping_status = ctk.CTkLabel(frame_red, text="Estado: Desconocido", font=ctk.CTkFont(size=11))
        self.lbl_ping_status.pack(pady=(0, 5))

        # --- SECCIÓN: IA ---
        frame_ia = ctk.CTkFrame(self)
        frame_ia.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(frame_ia, text="PARÁMETROS DE INTELIGENCIA", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#F57C00").pack(pady=5)

        self.epochs_entry = self.create_input(frame_ia, "Épocas de Entrenamiento:", str(self.config_data.get("epochs", 300)))
        self.conf_entry = self.create_input(
            frame_ia, "Confianza Mínima (0.1 a 1.0):", str(self.config_data.get("confidence", 0.60))
        )

        # Botón Guardar
        btn_save = ctk.CTkButton(self, text="Guardar Cambios", command=self.save_config,
                                 fg_color="#2E7D32", hover_color="#1B5E20", font=ctk.CTkFont(weight="bold"))
        btn_save.pack(pady=20, padx=20, fill="x")

    def create_input(self, parent, label, default_val, show=None):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(frame, text=label).pack(side="left")
        entry = ctk.CTkEntry(frame, width=150, show=show)
        entry.insert(0, default_val)
        entry.pack(side="right")
        return entry

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_config(self):
        try:
            new_config = {
                "ip_raspberry": self.ip_entry.get(),
                "usuario": self.user_entry.get(),
                "contrasena": self.pass_entry.get(),
                "epochs": int(self.epochs_entry.get()),
                "confidence": float(self.conf_entry.get())
            }
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(new_config, f, indent=4)
            messagebox.showinfo("Éxito", "Configuración guardada correctamente.")
            self.destroy()
        except ValueError:
            messagebox.showerror("Error", "Por favor ingresá valores numéricos válidos en Épocas y Confianza.")

    def run_ping_test(self):
        ip = self.ip_entry.get()
        self.lbl_ping_status.configure(text="Estado: Verificando...", text_color="white")
        self.update_idletasks()

        def ping():
            try:
                # -n 1 para Windows (1 paquete), -w 2000 (timeout 2s)
                result = subprocess.run(["ping", "-n", "1", "-w", "2000", ip],
                                        capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if result.returncode == 0:
                    self.after(0, lambda: self.lbl_ping_status.configure(text="Estado: ONLINE ✅", text_color="#4CAF50"))
                else:
                    self.after(0, lambda: self.lbl_ping_status.configure(text="Estado: OFFLINE ❌", text_color="#F44336"))
            except Exception as e:
                self.after(0, lambda: self.lbl_ping_status.configure(text=f"Error: {str(e)}", text_color="#F44336"))

        threading.Thread(target=ping, daemon=True).start()


class MLOpsPanel(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FLEX-SORT - Adaptive AI Classification System")

        # Dimensiones y centrado de ventana
        window_width = 900
        window_height = 650
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_cordinate = int((screen_width / 2) - (window_width / 2))
        y_cordinate = int((screen_height / 2) - (window_height / 2))
        self.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")

        # Grid Layout Base: Dividimos la pantalla en 2 columnas
        # Columna 0: Panel lateral (menú) | Columna 1: Consola principal
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ---------------- MENU LATERAL (SIDEBAR) ----------------
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(9, weight=1)  # Espacio flexible abajo

        path_logo_texto = os.path.join("recursos", "logo_texto.png")
        if os.path.exists(path_logo_texto):
            try:
                img_pil = Image.open(path_logo_texto)
                img_ctk = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(200, 50))
                self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="", image=img_ctk)
            except Exception:
                self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="FLEX-SORT",
                                               font=ctk.CTkFont(size=28, weight="bold"))
        else:
            self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="FLEX-SORT",
                                           font=ctk.CTkFont(size=28, weight="bold"))

        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 0))

        self.lbl_subtitle = ctk.CTkLabel(
            self.sidebar_frame,
            text="Adaptive AI System\nv2.0.0 (FLEX Core)",
            font=ctk.CTkFont(size=12, slant="italic")
        )
        self.lbl_subtitle.grid(row=1, column=0, padx=20, pady=(5, 30))

        # Botones de Acción Estilizados
        self.init_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.init_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.init_frame.grid_columnconfigure(0, weight=1)
        self.init_frame.grid_columnconfigure(1, weight=1)

        self.btn_reset = ctk.CTkButton(
            self.init_frame, text="0. Borrar memoria", command=self.run_reset_all,
            fg_color="#D32F2F", hover_color="#C62828", font=ctk.CTkFont(size=13, weight="bold")
        )
        self.btn_reset.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.btn_setup = ctk.CTkButton(
            self.init_frame, text="1. Inicializar", command=self.run_setup,
            fg_color="#333333", hover_color="#555555", font=ctk.CTkFont(size=13)
        )
        self.btn_setup.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        self.btn_ingest = ctk.CTkButton(
            self.sidebar_frame, text="2. Nuevo entrenamiento", command=self.run_ingest,
            fg_color="#1E88E5", hover_color="#1565C0", font=ctk.CTkFont(size=14, weight="bold")
        )
        self.btn_ingest.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        self.btn_train = ctk.CTkButton(
            self.sidebar_frame, text="3. Entrenar modelo", command=self.run_train,
            fg_color="#F57C00", hover_color="#E65100", font=ctk.CTkFont(size=14, weight="bold")
        )
        self.btn_train.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        self.btn_test = ctk.CTkButton(
            self.sidebar_frame, text="4. Probar modelo / visión", command=self.run_infer,
            fg_color="#7B1FA2", hover_color="#4A148C", font=ctk.CTkFont(size=14, weight="bold")
        )
        self.btn_test.grid(row=5, column=0, padx=20, pady=10, sticky="ew")

        self.btn_optimize = ctk.CTkButton(
            self.sidebar_frame, text="5. Optimizar (NCNN/TF)", command=self.run_optimize,
            fg_color="#E040FB", hover_color="#AA00FF", font=ctk.CTkFont(size=14, weight="bold")
        )
        self.btn_optimize.grid(row=6, column=0, padx=20, pady=10, sticky="ew")

        self.btn_deploy = ctk.CTkButton(
            self.sidebar_frame, text="6. Enviar a Raspberry Pi", command=self.run_deploy,
            fg_color="#00897B", hover_color="#00695C", font=ctk.CTkFont(size=14, weight="bold")
        )
        self.btn_deploy.grid(row=7, column=0, padx=20, pady=10, sticky="ew")

        path_icono_central = os.path.join("recursos", "icono_central.png")
        if os.path.exists(path_icono_central):
            try:
                img_ic = Image.open(path_icono_central)
                img_ic_ctk = ctk.CTkImage(light_image=img_ic, dark_image=img_ic, size=(100, 100))
                self.icono_label = ctk.CTkLabel(self.sidebar_frame, text="", image=img_ic_ctk)
                self.icono_label.grid(row=8, column=0, padx=20, pady=(10, 10), sticky="s")
            except Exception:
                pass

        # Configuración inferior
        self.switch_var = ctk.StringVar(value="on")
        self.switch_theme = ctk.CTkSwitch(
            self.sidebar_frame, text="Modo Oscuro", command=self.toggle_appearance_mode,
            variable=self.switch_var, onvalue="on", offvalue="of"
        )
        self.switch_theme.grid(row=9, column=0, padx=20, pady=(0, 10), sticky="s")

        self.lbl_hardware = ctk.CTkLabel(self.sidebar_frame, text="Controlador NVIDIA activo",
                                         font=ctk.CTkFont(size=11), text_color="#A5D6A7")
        self.lbl_hardware.grid(row=10, column=0, padx=20, pady=(0, 20), sticky="s")

        # ---------------- PANEL PRINCIPAL (CONSOLA) ----------------
        self.main_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.console_label = ctk.CTkLabel(self.main_frame, text="Monitor de eventos MLOps",
                                          font=ctk.CTkFont(size=16, weight="bold"))
        self.console_label.grid(row=0, column=0, padx=0, pady=(0, 5), sticky="w")

        # Botón de Historial (Reloj) al lado del engranaje
        path_history_icon = os.path.join("recursos", "history_icon.png")
        if os.path.exists(path_history_icon):
            try:
                img_hist = Image.open(path_history_icon)
                img_hist_ctk = ctk.CTkImage(light_image=img_hist, dark_image=img_hist, size=(24, 24))
                self.btn_history = ctk.CTkButton(self.main_frame, text="", image=img_hist_ctk, width=30, height=30,
                                                 fg_color="transparent", hover_color=("#DBDBDB", "#2B2B2B"),
                                                 command=self.open_history)
                self.btn_history.grid(row=0, column=0, sticky="e", padx=(0, 40))
            except Exception:
                pass

        # Botón de Ajustes (Engranaje) en la parte superior derecha
        path_config_icon = os.path.join("recursos", "config_icon.png")
        if os.path.exists(path_config_icon):
            try:
                img_conf = Image.open(path_config_icon)
                img_conf_ctk = ctk.CTkImage(light_image=img_conf, dark_image=img_conf, size=(24, 24))
                self.btn_settings = ctk.CTkButton(self.main_frame, text="", image=img_conf_ctk, width=30, height=30,
                                                  fg_color="transparent", hover_color=("#DBDBDB", "#2B2B2B"),
                                                  command=self.open_settings)
                self.btn_settings.grid(row=0, column=0, sticky="e", padx=(0, 5))
            except Exception:
                self.btn_settings = ctk.CTkButton(self.main_frame, text="⚙️", width=30, height=30,
                                                  fg_color="transparent", command=self.open_settings)
                self.btn_settings.grid(row=0, column=0, sticky="e", padx=(0, 5))
        else:
            self.btn_settings = ctk.CTkButton(self.main_frame, text="⚙️", width=30, height=30,
                                              fg_color="transparent", command=self.open_settings)
            self.btn_settings.grid(row=0, column=0, sticky="e", padx=(0, 5))

        self.progressbar = ctk.CTkProgressBar(self.main_frame, mode="indeterminate",
                                              height=6, fg_color="#333333", progress_color="#1E88E5")
        self.progressbar.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.progressbar.set(0)

        # Textbox para los Logs estilo Terminal Avanzada
        self.console = ctk.CTkTextbox(
            self.main_frame, fg_color="#1A1A1A", text_color="#4CAF50",
            border_color="#333333", border_width=2, font=("Consolas", 13)
        )
        self.console.grid(row=2, column=0, sticky="nsew")

        # Forzar el uso estricto del ejecutable local
        self.python_exe = ".\\venv\\Scripts\\python.exe"
        self.log(
            f"[SISTEMA INICIADO] Conectado al intérprete virtual: "
            f"{self.python_exe}\nEsperando instrucciones...\n{'-' * 60}"
        )

    def open_settings(self):
        dialog = SettingsDialog(self)
        self.wait_window(dialog)

    def open_history(self):
        dialog = HistoryDialog(self)
        self.wait_window(dialog)

    def toggle_appearance_mode(self):
        if self.switch_var.get() == "on":
            ctk.set_appearance_mode("Dark")
            self.console.configure(
                fg_color="#1A1A1A", text_color="#4CAF50", border_color="#333333"
            )
            self.switch_theme.configure(text="Modo Oscuro")
        else:
            ctk.set_appearance_mode("Light")
            self.console.configure(
                fg_color="#FFFFFF", text_color="#006400", border_color="#CCCCCC"
            )
            self.switch_theme.configure(text="Modo Claro  ")

    def log(self, text):
        self.console.insert(ctk.END, text + "\n")
        self.console.see(ctk.END)

    def run_subprocess(self, cmd):
        def task():
            self.after(0, self.progressbar.start)
            self.log(f"> \n> EJECUTANDO: {' '.join(cmd)}\n")
            kwargs = {}
            if sys.platform == "win32":
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

            # Forzar entorno a UTF-8 para evitar errores de decodificación en Windows
            custom_env = os.environ.copy()
            custom_env["PYTHONIOENCODING"] = "utf-8"
            kwargs["env"] = custom_env

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace',
                **kwargs,
            )
            for line in process.stdout:
                self.after(0, self.log, line.strip())  # Evitar congelamiento usando after loop de CTK
            process.wait()
            self.after(0, self.progressbar.stop)
            self.after(0, self.progressbar.set, 0)
            self.after(0, self.log, f"\n[ CÓDIGO FINALIZADO ]\n{'-'*70}\n")

        # Ejecutar en segundo plano real
        threading.Thread(target=task, daemon=True).start()

    def run_reset_all(self):
        respuesta = messagebox.askyesnocancel(
            "PELIGRO: BORRADO MASIVO",
            "Estás a punto de ELIMINAR permanentemente:\n"
            "- Todas las fotos y videos capturados\n"
            "- Todas los modelos de IA entrenados en la historia\n"
            "- El archivo de configuración de servos\n\n"
            "¿Deseás REINICIAR LA MEMORIA VIRTUAL para un proyecto nuevo?",
        )
        if not respuesta or respuesta is None:
            return

        self.log("\n[FORMATEO] Eliminando archivos antiguos de la IA...")

        # Eliminar carpetas problemáticas enteras
        folders_to_delete = ["Proyecto_Cinta/dataset/images", "Proyecto_Cinta/dataset/labels", "runs"]
        files_to_delete = ["Proyecto_Cinta/dataset/data.yaml", "Proyecto_Cinta/dataset/servo_mapping.json"]

        for folder in folders_to_delete:
            if os.path.exists(folder):
                try:
                    shutil.rmtree(folder)
                    self.log(f"  [-] Carpeta purgada: {folder}")
                except Exception as e:
                    self.log(f"  [x] Error al borrar {folder}: {e}")

        for f in files_to_delete:
            if os.path.exists(f):
                try:
                    os.remove(f)
                    self.log(f"  [-] Archivo reseteado: {f}")
                except Exception:
                    pass

        # Barrer todos los modelos basura optimizados
        for r, ds, fs in os.walk(os.getcwd()):
            if "venv" in r or ".git" in r:
                continue

            # Borrar carpetas de exportacion como _ncnn_model
            for d in list(ds):
                if d.endswith("_ncnn_model"):
                    try:
                        shutil.rmtree(os.path.join(r, d))
                    except Exception:
                        pass

            for file in fs:
                if file.endswith(".tflite") or file.endswith(".onnx") or (file.endswith(".pt") and "yolo" not in file):
                    try:
                        os.remove(os.path.join(r, file))
                    except Exception:
                        pass

        self.log("\n[SISTEMA LIMPIO] Memoria totalmente limpia.\n>>> AHORA PRESIONÁ EN: '1. Inicializar'.")

    def run_setup(self):
        self.run_subprocess([self.python_exe, "1_setup_vacio.py"])

    def run_ingest(self):
        usar_webcam = messagebox.askyesnocancel(
            "Fuente de ingreso",
            "¿Deseás habilitar la CÁMARA WEB para grabar el objeto en tiempo real?\n\n"
            "- SÍ = Modo cámara en vivo\n- NO = Cargar archivo manual (.mp4)"
        )

        if usar_webcam is None:  # X o Cancel
            return

        if usar_webcam:
            video_path = "webcam"
        else:
            video_path = filedialog.askopenfilename(
                title="Seleccionar Video RAW",
                filetypes=[("Archivos MP4", "*.mp4"), ("Todos", "*.*")]
            )
            if not video_path:
                return

        fuente_display = "Cámara en vivo" if usar_webcam else os.path.basename(video_path)
        categoria = simpledialog.askstring(
            "Etiqueta IA",
            f"Modo de ingesta: {fuente_display}\n\nIngresá el tipo de objeto (ej: manzana, pieza_metal):"
        )

        if not categoria:
            return

        dialog = ServoSelectorDialog(self, categoria)
        self.wait_window(dialog)
        servo_id = dialog.servo_id

        if not servo_id:
            self.log("\n[ABORTADO] No se asignó un servo al objeto.")
            return

        es_limpio = messagebox.askyesnocancel(
            "Memoria IA",
            "El modelo tiene información anterior.\n\n"
            "¿Deseás REINICIAR LA MEMORIA VIRTUAL y comenzar la IA 100% desde cero?\n\n"
            "- SÍ = Resetear base de datos\n- NO = Anexar conocimientos"
        )
        if es_limpio is None:
            return
        opcion = "b" if es_limpio else "a"

        self.log(
            "\n >>> Lanzando interfaz de mapeo... "
            "Si usas cámara, mira la ventana emergente."
        )
        self.run_subprocess(
            [self.python_exe, "2_procesar_video.py", video_path,
             categoria, opcion, servo_id]
        )

    def run_train(self):
        respuesta = messagebox.askyesnocancel(
            "Protocolo de Entrenamiento",
            "Atención: Se transferirá todo el procesamiento lógico a tu GPU NVIDIA RTX 2060.\n\n"
            "¿Deseas aplicar Transfer Learning sobre tu modelo viejo?\n\n"
            "- SÍ: Evolución Continua (Actualiza el modelo).\n"
            "- NO: Red Neuronal limpia.",
        )
        if respuesta is None:
            return
        modo = "finetune" if respuesta else "scratch"
        self.run_subprocess([
            self.python_exe, "3_entrenar_modelo.py", modo
        ])

    def run_infer(self):
        # 0. Intentar cargar el modelo activo desde config.json
        modelo_path = ""
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
            active = config.get("active_model")
            if active and os.path.exists(active):
                modelo_path = active
                self.log(f"\n[AUTO] Usando modelo ACTIVO del historial: {os.path.basename(active)}")
        except Exception:
            pass

        if not modelo_path:
            # Escanear agresivamente por cualquier cerebro de IA entrenado (.pt)
            pt_files = []
            for root_dir, dirs, files in os.walk(os.getcwd()):
                if "venv" in root_dir or ".git" in root_dir:
                    continue
                for file in files:
                    if file.endswith(".pt") and "yolo" not in file:
                        pt_files.append(os.path.join(root_dir, file))

            if pt_files:
                # Ordenar por el más reciente
                pt_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                latest = pt_files[0]

                # Auto-Detectado
                respuesta = messagebox.askyesnocancel(
                    "Historial de inteligencia artificial",
                    f"El sistema ha localizado el último cerebro entrenado hace poco en:\n"
                    f"...{latest[-50:]}\n\n¿Querés encender la cámara con este modelo?\n\n"
                    f"- SÍ = Extraer historial automático\n- NO = Cargar un modelo viejo manualmente.",
                )
                if respuesta is None:
                    return
                if respuesta:
                    modelo_path = latest

        if not modelo_path:
            modelo_path = filedialog.askopenfilename(
                title="Cargar Historial (Archivo .pt)",
                filetypes=[("Modelos Neuronales", "*.pt")]
            )
            if not modelo_path:
                self.log("\n[ABORTADO] No se seleccionó ningún modelo base para la prueba.")
                return

        self.log(f"\n >>> Inyectando cerebro en memoria: {os.path.basename(modelo_path)}")
        self.log(" >>> Activando sensores de Inferencia Local... Posiciona el objeto frente a la cámara.")
        self.run_subprocess([self.python_exe, "4_probar_modelo_pc.py", modelo_path])

    def run_optimize(self):
        # 0. Intentar cargar el modelo activo desde config.json
        modelo_path = ""
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
            active = config.get("active_model")
            if active and os.path.exists(active) and active.endswith(".pt"):
                modelo_path = active
                self.log(f"\n[AUTO] Usando modelo ACTIVO para optimizar: {os.path.basename(active)}")
        except Exception:
            pass

        if not modelo_path:
            # Buscar modelo .pt
            pt_files = []
            for root_dir, dirs, files in os.walk(os.getcwd()):
                if "venv" in root_dir or ".git" in root_dir:
                    continue
                for file in files:
                    if file.endswith("best.pt"):
                        pt_files.append(os.path.join(root_dir, file))

            if pt_files:
                pt_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                latest = pt_files[0]

                respuesta = messagebox.askyesnocancel(
                    "Optimizar Modelo",
                    f"Se detectó tu último modelo PyTorch:\n...{latest[-50:]}\n\n"
                    "¿Quieres usar este base?\n\n- SÍ = Autodetectado\n- NO = Seleccionar manualmente."
                )
                if respuesta is None:
                    return
                if respuesta:
                    modelo_path = latest

        if not modelo_path:
            modelo_path = filedialog.askopenfilename(
                title="Seleccionar Modelo (.pt) a Optimizar",
                filetypes=[("Modelos PyTorch", "*.pt")]
            )
            if not modelo_path:
                return

        formato = simpledialog.askstring(
            "Formato de Exportación",
            "¿A qué formato ligero deseas exportar?\n\nOpciones principales:\n"
            "- 'ncnn' (Máximo rendimiento en Rasp Pi, exporta como CARPETA)\n"
            "- 'tflite' (Muy bueno en Rasp Pi, exporta ARCHIVO)\n\n"
            "Escribe ncnn o tflite:",
            initialvalue="ncnn"
        )
        if not formato:
            return
        formato = formato.lower().strip()

        self.log(
            f"\n >>> Iniciando Optimización de GPU a ARM [{formato.upper()}] "
            f"para: {os.path.basename(modelo_path)}"
        )
        self.run_subprocess(
            [self.python_exe, "5_optimizar_modelo.py", modelo_path, formato]
        )

    def run_deploy(self):
        # 0. Detectar candidatos (Priorizando el último optimizado)
        modelos_candidatos = []
        for root_dir, dirs, files in os.walk(os.getcwd()):
            if "venv" in root_dir or ".git" in root_dir:
                continue

            # Buscar carpetas de modelo NCNN
            for dir_name in dirs:
                if dir_name.endswith("_ncnn_model"):
                    modelos_candidatos.append(os.path.join(root_dir, dir_name))

            # Buscar archivos TFLite, ONNX, o el best base
            for file in files:
                if (file.endswith(".tflite") or file.endswith("best.pt") or
                   file.endswith(".onnx") or (file.startswith("modelo_") and file.endswith(".pt"))):
                    modelos_candidatos.append(os.path.join(root_dir, file))

        if not modelos_candidatos:
            self.log("\n[ERROR] No se encontró ningún modelo (NCNN, TFLite, o PT) para enviar.")
            return

        # Seleccionar el archivo o carpeta que fue creado/modificado MÁS recientemente
        modelos_candidatos.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        modelo_path = modelos_candidatos[0]

        self.log(
            f"\n >>> Auto-Detectado último modelo/optimizado: {os.path.basename(modelo_path)}"
        )
        self.log(" >>> Iniciando envío directo al Edge (Raspberry Pi)...")
        self.run_subprocess(
            [self.python_exe, "6_enviar_a_raspberry.py", modelo_path]
        )


if __name__ == "__main__":
    app = MLOpsPanel()
    app.mainloop()
