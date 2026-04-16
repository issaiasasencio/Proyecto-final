import customtkinter as ctk
from tkinter import filedialog, simpledialog, messagebox
import subprocess
import threading
import sys
import os

# Configuración global de entorno Moderno
ctk.set_appearance_mode("Dark") # Opciones: "Dark", "Light"
ctk.set_default_color_theme("blue") # Opciones: "blue", "green", "dark-blue"

class MLOpsPanel(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MLOps Edge Dashboard - Clasificador Inteligente")
        self.geometry("900x650")
        
        # Grid Layout Base: Dividimos la pantalla en 2 columnas
        # Columna 0: Panel lateral (menú) | Columna 1: Consola principal
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ---------------- MENU LATERAL (SIDEBAR) ----------------
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1) # Espacio flexible abajo

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="IA Edge\nDashboard", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 0))
        
        self.lbl_subtitle = ctk.CTkLabel(self.sidebar_frame, text="Versión 1.0.0 (GPU Core)", font=ctk.CTkFont(size=12, slant="italic"))
        self.lbl_subtitle.grid(row=1, column=0, padx=20, pady=(5, 30))

        # Botones de Acción Estilizados
        self.btn_setup = ctk.CTkButton(self.sidebar_frame, text="1. Inicializar Variables", command=self.run_setup, fg_color="#333333", hover_color="#555555", font=ctk.CTkFont(size=14))
        self.btn_setup.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.btn_ingest = ctk.CTkButton(self.sidebar_frame, text="2. Ingesta Dinámica", command=self.run_ingest, fg_color="#1E88E5", hover_color="#1565C0", font=ctk.CTkFont(size=14, weight="bold"))
        self.btn_ingest.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        self.btn_train = ctk.CTkButton(self.sidebar_frame, text="3. Entrenamiento Lógico", command=self.run_train, fg_color="#F57C00", hover_color="#E65100", font=ctk.CTkFont(size=14, weight="bold"))
        self.btn_train.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        self.btn_test = ctk.CTkButton(self.sidebar_frame, text="4. Probar Modelo / Visión", command=self.run_infer, fg_color="#7B1FA2", hover_color="#4A148C", font=ctk.CTkFont(size=14, weight="bold"))
        self.btn_test.grid(row=5, column=0, padx=20, pady=10, sticky="ew")

        # Configuración inferior
        self.lbl_hardware = ctk.CTkLabel(self.sidebar_frame, text="Controlador Nvidia Activo", font=ctk.CTkFont(size=11), text_color="#A5D6A7")
        self.lbl_hardware.grid(row=7, column=0, padx=20, pady=(0, 20), sticky="s")


        # ---------------- PANEL PRINCIPAL (CONSOLA) ----------------
        self.main_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.console_label = ctk.CTkLabel(self.main_frame, text="Monitor de Eventos MLOps", font=ctk.CTkFont(size=16, weight="bold"))
        self.console_label.grid(row=0, column=0, padx=0, pady=(0, 10), sticky="w")

        # Textbox para los Logs estilo Terminal Avanzada
        self.console = ctk.CTkTextbox(self.main_frame, fg_color="#1A1A1A", text_color="#4CAF50", border_color="#333333", border_width=2, font=("Consolas", 13))
        self.console.grid(row=1, column=0, sticky="nsew")

        # Forzar el uso estricto del ejecutable local
        self.python_exe = ".\\venv\\Scripts\\python.exe"
        self.log(f"[SISTEMA INICIADO] Conectado al intérprete virtual: {self.python_exe}\nEsperando instrucciones...\n{'-'*60}")

    def log(self, text):
        self.console.insert(ctk.END, text + "\n")
        self.console.see(ctk.END)

    def run_subprocess(self, cmd):
        def task():
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
                self.after(0, self.log, line.strip()) # Evitar congelamiento usando after loop de CTK
            process.wait()
            self.after(0, self.log, f"\n[ CÓDIGO FINALIZADO ]\n{'-'*70}\n")
        
        # Ejecutar en segundo plano real
        threading.Thread(target=task, daemon=True).start()

    def run_setup(self):
        self.run_subprocess([self.python_exe, "1_setup_vacio.py"])

    def run_ingest(self):
        usar_webcam = messagebox.askyesno("Fuente de Ingreso", "¿Deseas habilitar la CÁMARA WEB LGT/Iriun para grabar el objeto en tiempo real?\n\n- SÍ = Modo Cámara en Vivo\n- NO = Cargar archivo manual (.mp4)")
        
        if usar_webcam:
            video_path = "webcam"
        else:
            video_path = filedialog.askopenfilename(title="Seleccionar Video RAW", filetypes=[("Archivos MP4", "*.mp4"), ("Todos", "*.*")])
            if not video_path:
                return
            
        fuente_display = "Cámara en Vivo" if usar_webcam else os.path.basename(video_path)
        categoria = simpledialog.askstring("Etiqueta IA", f"Modo de ingesta: {fuente_display}\n\nEscribe qué tipo de objeto es (ej: manzana, pieza_metal):")
        
        if not categoria:
            return
            
        es_limpio = messagebox.askyesno("Memoria IA", "El modelo tiene información anterior.\n\n¿Deseas FORMATEAR LA MEMORIA VIRTUAL y comenzar la IA 100% Desde Cero?\n\n- SÍ = Resetea Base de Datos\n- NO = Anexa conocimientos")
        opcion = "b" if es_limpio else "a"
        
        self.log("\n >>> Lanzando interfaz de mapeo... Si usas cámara, mira la ventana emergente.")
        self.run_subprocess([self.python_exe, "2_procesar_video.py", video_path, categoria, opcion])

    def run_train(self):
        respuesta = messagebox.askyesno(
            "Protocolo de Entrenamiento", 
            "Atención: Se transferirá todo el procesamiento lógico a tu GPU NVIDIA RTX 2060.\n\n"
            "¿Deseas aplicar Transfer Learning sobre tu modelo viejo?\n\n"
            "- SÍ: Evolución Continua (Actualiza el modelo).\n"
            "- NO: Red Neuronal limpia."
        )
        modo = "finetune" if respuesta else "scratch"
        self.run_subprocess([self.python_exe, "3_entrenar_modelo.py", modo])

    def run_infer(self):
        # Escanear agresivamente por cualquier cerebro de IA entrenado (.pt)
        pt_files = []
        for root_dir, dirs, files in os.walk(os.getcwd()):
            if "venv" in root_dir or ".git" in root_dir: continue
            for file in files:
                if file.endswith(".pt") and "yolo" not in file:
                    pt_files.append(os.path.join(root_dir, file))
                    
        modelo_path = ""
        if pt_files:
            # Ordenar por el más reciente
            pt_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            latest = pt_files[0]
            
            # Auto-Detectado
            respuesta = messagebox.askyesno(
                "Historial de Inteligencia Artificial", 
                f"El sistema ha localizado el último cerebro entrenado hace poco en:\n...{latest[-50:]}\n\n¿Quieres encender la cámara con este modelo?\n\n- SÍ = Extraer historial automático\n- NO = Cargar un modelo viejo manualmente."
            )
            if respuesta:
                modelo_path = latest

        if not modelo_path:
            modelo_path = filedialog.askopenfilename(title="Cargar Historial (Archivo .pt)", filetypes=[("Modelos Neuronales", "*.pt")])
            if not modelo_path:
                self.log("\n[ABORTADO] No se seleccionó ningún modelo base para la prueba.")
                return

        self.log(f"\n >>> Inyectando cerebro en memoria: {os.path.basename(modelo_path)}")
        self.log(" >>> Activando sensores de Inferencia Local... Posiciona el objeto frente a la cámara.")
        self.run_subprocess([self.python_exe, "4_probar_modelo_pc.py", modelo_path])


if __name__ == "__main__":
    app = MLOpsPanel()
    app.mainloop()
