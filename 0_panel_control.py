import customtkinter as ctk
from tkinter import filedialog, simpledialog, messagebox
import subprocess
import threading
import sys
import os
import shutil
from PIL import Image
# Configuración global de entorno Moderno
ctk.set_appearance_mode("Dark")  # Opciones: "Dark", "Light"
ctk.set_default_color_theme("blue")  # Opciones: "blue", "green", "dark-blue"


class ServoSelectorDialog(ctk.CTkToplevel):
    def __init__(self, parent, categoria):
        super().__init__(parent)
        self.title("Asignación de Hardware Físico")
        self.geometry("500x350")
        self.servo_id = None

        # Mantener ventana al frente y modal
        self.attributes('-topmost', True)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        lbl = ctk.CTkLabel(self, text=f"Objeto: {categoria.upper()}\n\nSeleccioná el brazo expulsor de destino\n(Vista superior de la cinta):", font=ctk.CTkFont(
            size=16, weight="bold"))
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


class MLOpsPanel(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FLEX-SORT - Adaptive AI Classification System")

        # Dimensiones y centrado de ventana
        window_width = 900
        window_height = 650
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_cordinate = int((screen_width/2) - (window_width/2))
        y_cordinate = int((screen_height/2) - (window_height/2))
        self.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")

        # Grid Layout Base: Dividimos la pantalla en 2 columnas
        # Columna 0: Panel lateral (menú) | Columna 1: Consola principal
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ---------------- MENU LATERAL (SIDEBAR) ----------------
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(9, weight=1)  # Espacio flexible abajo

        path_logo_texto = "logo_texto.png"
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
            self.sidebar_frame, text="Adaptive AI System\nv2.0.0 (FLEX Core)", font=ctk.CTkFont(size=12, slant="italic"))
        self.lbl_subtitle.grid(row=1, column=0, padx=20, pady=(5, 30))

        # Botones de Acción Estilizados
        self.init_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.init_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.init_frame.grid_columnconfigure(0, weight=1)
        self.init_frame.grid_columnconfigure(1, weight=1)

        self.btn_reset = ctk.CTkButton(self.init_frame, text="0. Borrar memoria", command=self.run_reset_all,
                                       fg_color="#D32F2F", hover_color="#C62828", font=ctk.CTkFont(size=13, weight="bold"))
        self.btn_reset.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.btn_setup = ctk.CTkButton(self.init_frame, text="1. Inicializar",
                                       command=self.run_setup, fg_color="#333333", hover_color="#555555", font=ctk.CTkFont(size=13))
        self.btn_setup.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        self.btn_ingest = ctk.CTkButton(self.sidebar_frame, text="2. Nuevo entrenamiento", command=self.run_ingest,
                                        fg_color="#1E88E5", hover_color="#1565C0", font=ctk.CTkFont(size=14, weight="bold"))
        self.btn_ingest.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        self.btn_train = ctk.CTkButton(self.sidebar_frame, text="3. Entrenar modelo", command=self.run_train,
                                       fg_color="#F57C00", hover_color="#E65100", font=ctk.CTkFont(size=14, weight="bold"))
        self.btn_train.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        self.btn_test = ctk.CTkButton(self.sidebar_frame, text="4. Probar modelo / visión", command=self.run_infer,
                                      fg_color="#7B1FA2", hover_color="#4A148C", font=ctk.CTkFont(size=14, weight="bold"))
        self.btn_test.grid(row=5, column=0, padx=20, pady=10, sticky="ew")

        self.btn_optimize = ctk.CTkButton(self.sidebar_frame, text="5. Optimizar (NCNN/TF)", command=self.run_optimize,
                                          fg_color="#E040FB", hover_color="#AA00FF", font=ctk.CTkFont(size=14, weight="bold"))
        self.btn_optimize.grid(row=6, column=0, padx=20, pady=10, sticky="ew")

        self.btn_deploy = ctk.CTkButton(self.sidebar_frame, text="6. Enviar a Raspberry Pi", command=self.run_deploy,
                                        fg_color="#00897B", hover_color="#00695C", font=ctk.CTkFont(size=14, weight="bold"))
        self.btn_deploy.grid(row=7, column=0, padx=20, pady=10, sticky="ew")

        path_icono_central = "icono_central.png"
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
        self.switch_theme = ctk.CTkSwitch(self.sidebar_frame, text="Modo Oscuro",
                                          command=self.toggle_appearance_mode, variable=self.switch_var, onvalue="on", offvalue="of")
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

        self.progressbar = ctk.CTkProgressBar(self.main_frame, mode="indeterminate",
                                              height=6, fg_color="#333333", progress_color="#1E88E5")
        self.progressbar.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.progressbar.set(0)

        # Textbox para los Logs estilo Terminal Avanzada
        self.console = ctk.CTkTextbox(self.main_frame, fg_color="#1A1A1A", text_color="#4CAF50",
                                      border_color="#333333", border_width=2, font=("Consolas", 13))
        self.console.grid(row=2, column=0, sticky="nsew")

        # Forzar el uso estricto del ejecutable local
        self.python_exe = ".\\venv\\Scripts\\python.exe"
        self.log(
            f"[SISTEMA INICIADO] Conectado al intérprete virtual: {self.python_exe}\nEsperando instrucciones...\n{'-'*60}")

    def toggle_appearance_mode(self):
        if self.switch_var.get() == "on":
            ctk.set_appearance_mode("Dark")
            self.console.configure(fg_color="#1A1A1A", text_color="#4CAF50", border_color="#333333")
            self.switch_theme.configure(text="Modo Oscuro")
        else:
            ctk.set_appearance_mode("Light")
            self.console.configure(fg_color="#FFFFFF", text_color="#006400", border_color="#CCCCCC")
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
                **kwargs
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
            "¿Deseás REINICIAR LA MEMORIA VIRTUAL para un proyecto nuevo?"
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
            "Fuente de ingreso", "¿Deseás habilitar la CÁMARA WEB para grabar el objeto en tiempo real?\n\n- SÍ = Modo cámara en vivo\n- NO = Cargar archivo manual (.mp4)")

        if usar_webcam is None:  # X o Cancel
            return

        if usar_webcam:
            video_path = "webcam"
        else:
            video_path = filedialog.askopenfilename(title="Seleccionar Video RAW", filetypes=[
                                                    ("Archivos MP4", "*.mp4"), ("Todos", "*.*")])
            if not video_path:
                return

        fuente_display = "Cámara en vivo" if usar_webcam else os.path.basename(video_path)
        categoria = simpledialog.askstring(
            "Etiqueta IA", f"Modo de ingesta: {fuente_display}\n\nIngresá el tipo de objeto (ej: manzana, pieza_metal):")

        if not categoria:
            return

        dialog = ServoSelectorDialog(self, categoria)
        self.wait_window(dialog)
        servo_id = dialog.servo_id

        if not servo_id:
            self.log("\n[ABORTADO] No se asignó un servo al objeto.")
            return

        es_limpio = messagebox.askyesnocancel(
            "Memoria IA", "El modelo tiene información anterior.\n\n¿Deseás REINICIAR LA MEMORIA VIRTUAL y comenzar la IA 100% desde cero?\n\n- SÍ = Resetear base de datos\n- NO = Anexar conocimientos")
        if es_limpio is None:
            return
        opcion = "b" if es_limpio else "a"

        self.log("\n >>> Lanzando interfaz de mapeo... Si usas cámara, mira la ventana emergente.")
        self.run_subprocess([self.python_exe, "2_procesar_video.py", video_path, categoria, opcion, servo_id])

    def run_train(self):
        respuesta = messagebox.askyesnocancel(
            "Protocolo de Entrenamiento",
            "Atención: Se transferirá todo el procesamiento lógico a tu GPU NVIDIA RTX 2060.\n\n"
            "¿Deseas aplicar Transfer Learning sobre tu modelo viejo?\n\n"
            "- SÍ: Evolución Continua (Actualiza el modelo).\n"
            "- NO: Red Neuronal limpia."
        )
        if respuesta is None:
            return
        modo = "finetune" if respuesta else "scratch"
        self.run_subprocess([self.python_exe, "3_entrenar_modelo.py", modo])

    def run_infer(self):
        # Escanear agresivamente por cualquier cerebro de IA entrenado (.pt)
        pt_files = []
        for root_dir, dirs, files in os.walk(os.getcwd()):
            if "venv" in root_dir or ".git" in root_dir:
                continue
            for file in files:
                if file.endswith(".pt") and "yolo" not in file:
                    pt_files.append(os.path.join(root_dir, file))

        modelo_path = ""
        if pt_files:
            # Ordenar por el más reciente
            pt_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            latest = pt_files[0]

            # Auto-Detectado
            respuesta = messagebox.askyesnocancel(
                "Historial de inteligencia artificial",
                f"El sistema ha localizado el último cerebro entrenado hace poco en:\n...{latest[-50:]}\n\n¿Querés encender la cámara con este modelo?\n\n- SÍ = Extraer historial automático\n- NO = Cargar un modelo viejo manualmente."
            )
            if respuesta is None:
                return
            if respuesta:
                modelo_path = latest

        if not modelo_path:
            modelo_path = filedialog.askopenfilename(title="Cargar Historial (Archivo .pt)", filetypes=[
                                                     ("Modelos Neuronales", "*.pt")])
            if not modelo_path:
                self.log("\n[ABORTADO] No se seleccionó ningún modelo base para la prueba.")
                return

        self.log(f"\n >>> Inyectando cerebro en memoria: {os.path.basename(modelo_path)}")
        self.log(" >>> Activando sensores de Inferencia Local... Posiciona el objeto frente a la cámara.")
        self.run_subprocess([self.python_exe, "4_probar_modelo_pc.py", modelo_path])

    def run_optimize(self):
        # Buscar modelo .pt
        pt_files = []
        for root_dir, dirs, files in os.walk(os.getcwd()):
            if "venv" in root_dir or ".git" in root_dir:
                continue
            for file in files:
                if file.endswith("best.pt"):
                    pt_files.append(os.path.join(root_dir, file))

        modelo_path = ""
        if pt_files:
            pt_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            latest = pt_files[0]

            respuesta = messagebox.askyesnocancel(
                "Optimizar Modelo", f"Se detectó tu último modelo PyTorch:\n...{latest[-50:]}\n\n¿Quieres usar este base?\n\n- SÍ = Autodetectado\n- NO = Seleccionar manualmente.")
            if respuesta is None:
                return
            if respuesta:
                modelo_path = latest

        if not modelo_path:
            modelo_path = filedialog.askopenfilename(title="Seleccionar Modelo (.pt) a Optimizar", filetypes=[
                                                     ("Modelos PyTorch", "*.pt")])
            if not modelo_path:
                return

        formato = simpledialog.askstring(
            "Formato de Exportación", "¿A qué formato ligero deseas exportar?\n\nOpciones principales:\n- 'ncnn' (Máximo rendimiento en Rasp Pi, exporta como CARPETA)\n- 'tflite' (Muy bueno en Rasp Pi, exporta ARCHIVO)\n\nEscribe ncnn o tflite:", initialvalue="ncnn")
        if not formato:
            return
        formato = formato.lower().strip()

        self.log(
            f"\n >>> Iniciando Optimización de GPU a ARM [{formato.upper()}] para: {os.path.basename(modelo_path)}")
        self.run_subprocess([self.python_exe, "5_optimizar_modelo.py", modelo_path, formato])

    def run_deploy(self):
        # Auto-detectar agresivamente el último modelo optimizado (o carpeta ncnn) generado
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
                if file.endswith(".tflite") or file.endswith("best.pt") or file.endswith(".onnx"):
                    modelos_candidatos.append(os.path.join(root_dir, file))

        if not modelos_candidatos:
            self.log("\n[ERROR] No se encontró ningún modelo (NCNN, TFLite, o PT) para enviar.")
            return

        # Seleccionar el archivo o carpeta que fue creado/modificado MÁS recientemente
        modelos_candidatos.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        modelo_path = modelos_candidatos[0]

        self.log(f"\n >>> Auto-Detectado último modelo: {os.path.basename(modelo_path)}")
        self.log(" >>> Iniciando envío directo al Edge (Raspberry Pi)...")
        self.run_subprocess([self.python_exe, "6_enviar_a_raspberry.py", modelo_path])


if __name__ == "__main__":
    app = MLOpsPanel()
    app.mainloop()
