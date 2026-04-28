import json
import os
import shutil
import subprocess
import sys
import threading
import time
import socket
import csv
import psutil
import webbrowser
from tkinter import filedialog, messagebox, simpledialog
import tkinter as tk

import customtkinter as ctk
from PIL import Image
from capturar_maestro import capturar_y_procesar_fondo
import paramiko
import yaml

# Configuración global de entorno Moderno
ctk.set_appearance_mode("Dark")  # Opciones: "Dark", "Light"

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


class SourceSelectorDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Fuente de Ingreso")
        
        w, h = 450, 400
        x = int((self.winfo_screenwidth() / 2) - (w / 2))
        y = int((self.winfo_screenheight() / 2) - (h / 2))
        self.geometry(f"{w}x{h}+{x}+{y}")
        
        self.source_type = None
        
        self.attributes('-topmost', True)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        lbl = ctk.CTkLabel(
            self, text="Selecciona la camara o video a utilizar:\n(¿Desde donde ingresaremos el objeto?)",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        lbl.pack(pady=(20, 10))

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        def select(val):
            self.source_type = val
            self.destroy()

        btn_rpi = ctk.CTkButton(
            frame, text="1. Camara Inalambrica (Raspberry Pi)", font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#00897B", hover_color="#00695C", height=50,
            command=lambda: select("raspberry")
        )
        btn_rpi.pack(fill="x", pady=10)

        btn_pc = ctk.CTkButton(
            frame, text="2. Camara Local (PC o Iriun)", font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#1E88E5", hover_color="#1565C0", height=50,
            command=lambda: select("webcam")
        )
        btn_pc.pack(fill="x", pady=10)

        btn_manual = ctk.CTkButton(
            frame, text="3. Subir Video Manual (.mp4)", font=ctk.CTkFont(size=14),
            fg_color="#555555", hover_color="#333333", height=50,
            command=lambda: select("manual")
        )
        btn_manual.pack(fill="x", pady=10)

class HistoryDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Historial de Inteligencia Artificial")
        self.geometry("500x450")
        self.parent = parent
        self.archive_dir = os.path.join("Proyecto_FlexSort", "modelos_archivados")
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

        header = ctk.CTkLabel(self, text="Modelos Archivados", font=ctk.CTkFont(size=20, weight="bold"))
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
                        servos = meta_data.get("servos", {})
                        if objetos:
                            description = "Objetos: " + ", ".join(
                                [f"{o} (S{servos.get(o, '?')})" for o in objetos]
                            )
                except (json.JSONDecodeError, FileNotFoundError):
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
        except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
            messagebox.showerror("Error", f"No se pudo activar el modelo: {e}")


class ReportDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Calidad de Inteligencia Artificial")
        self.geometry("500x550")

        # Centrar
        w, h = 500, 550
        x = int((self.winfo_screenwidth() / 2) - (w / 2))
        y = int((self.winfo_screenheight() / 2) - (h / 2))
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.attributes('-topmost', True)
        self.transient(parent)
        self.grab_set()

        base_dir = "Proyecto_FlexSort"
        project_abs = os.path.abspath(os.path.join(base_dir, "entrenamientos"))
        self.results_path = os.path.join(project_abs, "modelo_produccion", "results.csv")
        self.image_path = os.path.join(project_abs, "modelo_produccion", "results.png")

        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Reporte de Desempeño", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=20)

        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.load_report()

    def load_report(self):
        map50 = 0.0
        if os.path.exists(self.results_path):
            try:
                with open(self.results_path, mode='r', encoding='utf-8') as f:
                    reader = list(csv.DictReader(f))
                    if reader:
                        last_row = reader[-1]
                        # Buscar la columna mAP50 ajustando por posibles espacios en nombres
                        val_key = next((k for k in last_row.keys() if "mAP50(B)" in k), None)
                        if val_key:
                            map50 = float(last_row[val_key])
            except (csv.Error, FileNotFoundError, ValueError, KeyError) as e:
                print(f"Error al leer reporte: {e}")

        # Lógica de Veredicto
        score_pct = map50 * 100
        if score_pct >= 90:
            status, color, msg = "EXCELENTE", "#4CAF50", "Precision optima. El sistema esta listo para produccion."
        elif score_pct >= 70:
            status, color, msg = "ACEPTABLE", "#FBC02D", "Funcionamiento estable. Podria presentar variaciones menores."
        else:
            status, color, msg = "INSUFICIENTE", "#F44336", "Se requiere mayor volumen de datos para entrenamiento."

        # UI del Score
        ctk.CTkLabel(self.content_frame, text=status, font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=color).pack(pady=(20, 5))

        # Score Gauge
        gauge = ctk.CTkProgressBar(self.content_frame, height=20, progress_color=color, fg_color="#333333")
        gauge.set(map50)
        gauge.pack(fill="x", padx=40, pady=10)

        ctk.CTkLabel(self.content_frame, text=f"Puntaje de Precisión: {score_pct:.1f}%",
                     font=ctk.CTkFont(size=14)).pack()

        # Recomendación
        msg_frame = ctk.CTkFrame(self.content_frame, fg_color="#222222")
        msg_frame.pack(pady=20, padx=20, fill="x")
        ctk.CTkLabel(msg_frame, text="RECOMENDACIÓN:", font=ctk.CTkFont(weight="bold", size=12),
                     text_color="#AAAAAA").pack(pady=(10, 0))
        ctk.CTkLabel(msg_frame, text=msg, wraplength=350, font=ctk.CTkFont(size=13)).pack(pady=10)

        # Imagen de resultados si existe
        if os.path.exists(self.image_path):
            try:
                img = Image.open(self.image_path)
                # Redimensionar para encajar
                img.thumbnail((400, 200))
                img_ctk = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                ctk.CTkLabel(self.content_frame, text="", image=img_ctk).pack(pady=10)
            except (IOError, AttributeError):
                pass

        ctk.CTkButton(self, text="Entendido", command=self.destroy).pack(pady=20)


class TrainingManagerDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Estación de Control de Entrenamiento")
        
        # Dimensiones y centrado
        w, h = 550, 700
        x = int((self.winfo_screenwidth() / 2) - (w / 2))
        y = int((self.winfo_screenheight() / 2) - (h / 2))
        self.geometry(f"{w}x{h}+{x}+{y}")
        
        self.parent = parent
        self.config_path = "config.json"
        self.base_dir = "Proyecto_FlexSort"
        self.yaml_path = os.path.join(self.base_dir, "dataset", "data.yaml")
        self.mapping_path = os.path.join(self.base_dir, "dataset", "servo_mapping.json")
        
        # Cargar datos actuales
        self.categorias = self.get_available_categories()
        self.mapping = self.load_mapping()
        
        # Variables de control
        self.selected_categories = {cat: tk.BooleanVar(value=True) for cat in self.categorias}
        self.servo_vars = {cat: tk.StringVar(value=self.mapping.get(str(i), "1")) for i, cat in enumerate(self.categorias)}
        self.train_mode = tk.StringVar(value="finetune")
        self.result = None 

        # Referencias de widgets para validacion
        self.checkboxes = {}
        self.option_menus = {}

        self.setup_ui()
        self.update_validation()

        # Modal y Propiedades de Ventana
        try:
            self.resizable(False, False)
            if parent is not None:
                self.transient(parent)
                self.grab_set()
        except Exception as e:
            print(f"Aviso: No se pudieron aplicar todas las propiedades modales: {e}")

    def get_available_categories(self):
        if os.path.exists(self.yaml_path):
            try:
                with open(self.yaml_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    return data.get('names', [])
            except Exception as e:
                print(f"Error al leer data.yaml: {e}")
        return []

    def load_mapping(self):
        if os.path.exists(self.mapping_path):
            try:
                with open(self.mapping_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception: pass
        return {}

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        
        header = ctk.CTkLabel(self, text="MODIFICAR ENTRENAMIENTO", font=ctk.CTkFont(size=22, weight="bold"))
        header.pack(pady=(25, 10))
        
        desc = ctk.CTkLabel(self, text="Seleccioná qué objetos incluir y asignales su brazo robótico:", 
                            font=ctk.CTkFont(size=13), text_color="#AAAAAA")
        desc.pack(pady=(0, 15))

        # Contenedor con scroll
        self.scroll = ctk.CTkScrollableFrame(self, label_text="Objetos en Base de Datos", height=280)
        self.scroll.pack(fill="both", expand=True, padx=30, pady=10)

        if not self.categorias:
            ctk.CTkLabel(self.scroll, text="No hay objetos registrados.\nAgregá uno en el Paso 1.", 
                         text_color="#F44336", font=ctk.CTkFont(weight="bold")).pack(pady=40)
        
        for i, cat in enumerate(self.categorias):
            f = ctk.CTkFrame(self.scroll, fg_color="transparent")
            f.pack(fill="x", pady=8, padx=5)
            
            # Botón de Borrar (Tacho)
            btn_del = ctk.CTkButton(f, text="🗑", width=30, height=30, fg_color="#D32F2F", 
                                     hover_color="#B71C1C", command=lambda c=cat: self.delete_category(c))
            btn_del.pack(side="left", padx=(0, 5))

            # Checkbox de inclusion
            cb = ctk.CTkCheckBox(f, text=cat.upper(), variable=self.selected_categories[cat], 
                                 font=ctk.CTkFont(size=14, weight="bold"), width=150,
                                 command=self.update_validation)
            cb.pack(side="left", padx=10)
            self.checkboxes[cat] = cb
            
            # Servo Selector
            ctk.CTkLabel(f, text="Brazo:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(10, 5))
            om = ctk.CTkOptionMenu(f, values=["1", "2", "3", "4"], variable=self.servo_vars[cat], width=80,
                                   fg_color="#333333", button_color="#444444", command=lambda _: self.update_validation())
            om.pack(side="left", padx=5)
            self.option_menus[cat] = om

        # SECCIÓN INFERIOR: Modo de Red
        mode_frame = ctk.CTkFrame(self, fg_color="#222222", corner_radius=10)
        mode_frame.pack(fill="x", padx=30, pady=15)
        
        ctk.CTkLabel(mode_frame, text="Protocolo de Red Neuronal:", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        
        r1 = ctk.CTkRadioButton(mode_frame, text="Evolución Continua (Usa experiencia previa)", 
                                variable=self.train_mode, value="finetune", text_color="#4CAF50")
        r1.pack(pady=5, padx=20, anchor="w")
        
        r2 = ctk.CTkRadioButton(mode_frame, text="Red Limpia (Olvida todo y aprende de cero)", 
                                variable=self.train_mode, value="scratch", text_color="#FF9800")
        r2.pack(pady=5, padx=20, anchor="w")

        # Botón de Inicio
        self.btn_start = ctk.CTkButton(self, text="CONTINUAR ENTRENAMIENTO", 
                                       font=ctk.CTkFont(size=16, weight="bold"),
                                       fg_color="#1E88E5", hover_color="#1565C0", height=55,
                                       command=self.confirm)
        self.btn_start.pack(pady=(10, 30), padx=30, fill="x")

    def update_validation(self):
        selected_cats = [cat for cat in self.categorias if self.selected_categories[cat].get()]
        count = len(selected_cats)
        
        # 1. Sin límite estricto, pero mantenemos la lógica por si acaso quieres limitar después
        for cb in self.checkboxes.values():
            cb.configure(state="normal")
        
        # 2. Estado del Boton (Sin restricción de duplicados)
        if count > 0:
            self.btn_start.configure(state="normal", fg_color="#1E88E5", text=f"CONTINUAR ENTRENAMIENTO ({count} objetos)")
        else:
            self.btn_start.configure(state="disabled", fg_color="#555555", text="SELECCIONÁ AL MENOS 1 OBJETO")

    def delete_category(self, category):
        if not messagebox.askyesno("Confirmar Borrado", f"¿Estás seguro de eliminar '{category.upper()}' de la base de datos?\n\nEsta acción es irreversible y borrará todas sus fotos.", parent=self):
            return
            
        try:
            idx_to_remove = self.categorias.index(category)
            
            # 1. Actualizar data.yaml
            self.categorias.remove(category)
            with open(self.yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            data['names'] = self.categorias
            data['nc'] = len(self.categorias)
            with open(self.yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f)
            
            # 2. Re-indexar archivos de etiquetas (labels)
            labels_path = os.path.join(self.base_dir, "dataset", "labels")
            for root, dirs, files in os.walk(labels_path):
                for file in files:
                    if file.endswith(".txt"):
                        f_path = os.path.join(root, file)
                        lines_to_keep = []
                        with open(f_path, 'r') as f:
                            lines = f.readlines()
                        
                        for line in lines:
                            parts = line.split()
                            if not parts: continue
                            cls_id = int(parts[0])
                            if cls_id == idx_to_remove:
                                continue # Eliminar linea de la clase borrada
                            elif cls_id > idx_to_remove:
                                parts[0] = str(cls_id - 1)
                            lines_to_keep.append(" ".join(parts) + "\n")
                        
                        if lines_to_keep:
                            with open(f_path, 'w') as f:
                                f.writelines(lines_to_keep)
                        else:
                            os.remove(f_path)
                            # Intentar borrar imagen correspondiente
                            img_path = f_path.replace("labels", "images").replace(".txt", ".jpg")
                            if os.path.exists(img_path): os.remove(img_path)

            messagebox.showinfo("Éxito", f"Objeto '{category}' eliminado correctamente.", parent=self)
            self.destroy() # Recargar ventana
            self.parent.run_train() # Reabrir
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar: {e}", parent=self)

    def confirm(self):
        # Guardar cambios de servos y seleccion
        new_mapping = {}
        for i, cat in enumerate(self.categorias):
            if self.selected_categories[cat].get():
                new_mapping[str(i)] = self.servo_vars[cat].get()
        
        if not new_mapping:
            messagebox.showwarning("Atención", "Debés seleccionar al menos un objeto para entrenar.", parent=self)
            return

        # Guardar en JSON
        with open(self.mapping_path, 'w', encoding='utf-8') as f:
            json.dump(new_mapping, f, indent=4)
            
        self.result = self.train_mode.get()
        self.destroy()


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

        header = ctk.CTkLabel(self, text="Configuracion Maestra", font=ctk.CTkFont(size=20, weight="bold"))
        header.pack(pady=(20, 10))

        # --- SECCIÓN: RED ---
        frame_red = ctk.CTkFrame(self)
        frame_red.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(frame_red, text="CONEXIÓN RASPBERRY PI", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#1E88E5").pack(pady=5)

        self.ip_entry = self.create_input(
            frame_red, "Dirección IP:", self.config_data.get("ip_raspberry", "192.168.1.10")
        )
        self.user_entry = self.create_input(
            frame_red, "Usuario SSH:", self.config_data.get("usuario", "pi")
        )
        self.pass_entry = self.create_input(
            frame_red, "Contraseña SSH:", self.config_data.get("contrasena", "12345678"), show="*"
        )

        # Botones de Red (Escanear y Ping)
        btn_network_frame = ctk.CTkFrame(frame_red, fg_color="transparent")
        btn_network_frame.pack(pady=10, padx=10, fill="x")
        
        self.btn_scan = ctk.CTkButton(btn_network_frame, text="Escanear Red", command=self.run_network_scan,
                                      fg_color="#00897B", hover_color="#00695C", width=120)
        self.btn_scan.pack(side="left", padx=5, expand=True)

        self.btn_ping = ctk.CTkButton(btn_network_frame, text="Probar Ping", command=self.run_ping_test,
                                      fg_color="#333333", hover_color="#444444", width=120)
        self.btn_ping.pack(side="right", padx=5, expand=True)

        self.lbl_ping_status = ctk.CTkLabel(frame_red, text="Estado: Desconocido", font=ctk.CTkFont(size=11))
        self.lbl_ping_status.pack(pady=(0, 5))

        # --- SECCIÓN: IA ---
        frame_ia = ctk.CTkFrame(self)
        frame_ia.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(frame_ia, text="PARÁMETROS DE INTELIGENCIA", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#F57C00").pack(pady=5)

        self.epochs_entry = self.create_input(
            frame_ia, "Épocas de Entrenamiento:", str(self.config_data.get("epochs", 300))
        )
        
        # SLIDER DE CONFIANZA
        self.conf_frame = ctk.CTkFrame(frame_ia, fg_color="transparent")
        self.conf_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # Label dinámico
        conf_inicial = float(self.config_data.get("confidence", 0.70))
        self.lbl_conf_val = ctk.CTkLabel(self.conf_frame, text=f"Confianza Mínima: {conf_inicial:.2f}")
        self.lbl_conf_val.pack(anchor="w")
        
        self.conf_slider = ctk.CTkSlider(
            self.conf_frame, from_=0.1, to=1.0, 
            command=lambda val: self.lbl_conf_val.configure(text=f"Confianza Mínima: {val:.2f}")
        )
        self.conf_slider.set(conf_inicial)
        self.conf_slider.pack(fill="x", expand=True, pady=(5, 5))

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
                "confidence": float(self.conf_slider.get())
            }
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(new_config, f, indent=4)
            messagebox.showinfo("Éxito", "Configuración guardada correctamente.")
            self.destroy()
        except ValueError:
            messagebox.showerror("Error", "Por favor ingresá valores numéricos válidos en Épocas y Confianza.")

    def run_network_scan(self):
        self.lbl_ping_status.configure(text="Estado: Buscando raspberrypi.local...", text_color="yellow")
        self.update_idletasks()
        
        def sc_thread():
            try:
                # Intento 1: mDNS stándar
                ip = socket.gethostbyname("raspberrypi.local")
                self.ip_entry.delete(0, 'end')
                self.ip_entry.insert(0, ip)
                self.lbl_ping_status.configure(text=f"Estado: Encontrada! IP: {ip}", text_color="#4CAF50")
            except socket.gaierror:
                self.lbl_ping_status.configure(text="Estado: No encontrada en la red local. Ingrese IP Manual.", text_color="#F44336")
        
        threading.Thread(target=sc_thread, daemon=True).start()

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
                    self.after(0, lambda: self.lbl_ping_status.configure(text="Estado: ONLINE",
                                                                         text_color="#4CAF50"))
                else:
                    self.after(0, lambda: self.lbl_ping_status.configure(text="Estado: OFFLINE",
                                                                         text_color="#F44336"))
            except (subprocess.SubprocessError, OSError) as e:
                err_msg = str(e)
                self.after(0, lambda m=err_msg: self.lbl_ping_status.configure(text=f"Error: {m}",
                                                                               text_color="#F44336"))

        threading.Thread(target=ping, daemon=True).start()


class MLOpsPanel(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FLEX-SORT - Sistema de Clasificacion por IA Adaptativa")

        # Dimensiones y centrado de ventana
        window_width = 900
        window_height = 650
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_cordinate = int((screen_width / 2) - (window_width / 2))
        y_cordinate = int((screen_height / 2) - (window_height / 2))
        self.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")

        # Grid Layout Base
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # MENU LATERAL
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")

        for i in range(3, 8):
            self.sidebar_frame.grid_rowconfigure(i, weight=1)
        self.sidebar_frame.grid_rowconfigure(9, weight=2)

        path_logo_texto = os.path.join("recursos", "logo_texto.png")
        if os.path.exists(path_logo_texto):
            try:
                img_pil = Image.open(path_logo_texto)
                img_ctk = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(200, 50))
                self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="", image=img_ctk)
            except (IOError, AttributeError):
                self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="FLEX-SORT", font=ctk.CTkFont(size=28, weight="bold"))
        else:
            self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="FLEX-SORT", font=ctk.CTkFont(size=28, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 0))

        self.lbl_subtitle = ctk.CTkLabel(self.sidebar_frame, text="Sistema de IA Adaptativa\nv2.0.0 (Nucleo FLEX)", font=ctk.CTkFont(size=12, slant="italic"))
        self.lbl_subtitle.grid(row=1, column=0, padx=20, pady=(2, 20))

        self.sidebar_frame.grid_rowconfigure(2, weight=1)

        self.btn_ingest = ctk.CTkButton(self.sidebar_frame, text="1. Nuevo entrenamiento", command=self.run_ingest, fg_color="#1E88E5", hover_color="#1565C0", font=ctk.CTkFont(size=14, weight="bold"), height=35)
        self.btn_ingest.grid(row=3, column=0, padx=20, pady=4, sticky="ew")

        self.btn_train = ctk.CTkButton(self.sidebar_frame, text="2. Entrenar Inteligencia", command=self.run_train, fg_color="#1E88E5", hover_color="#1565C0", font=ctk.CTkFont(size=14, weight="bold"), height=35)
        self.btn_train.grid(row=4, column=0, padx=20, pady=4, sticky="ew")

        self.btn_test = ctk.CTkButton(self.sidebar_frame, text="3. Probar modelo / visión", command=self.run_infer, fg_color="#7B1FA2", hover_color="#4A148C", font=ctk.CTkFont(size=14, weight="bold"), height=35)
        self.btn_test.grid(row=5, column=0, padx=20, pady=4, sticky="ew")

        self.btn_optimize = ctk.CTkButton(self.sidebar_frame, text="4. Optimizar (NCNN)", command=self.run_optimize, fg_color="#E040FB", hover_color="#AA00FF", font=ctk.CTkFont(size=14, weight="bold"), height=35)
        self.btn_optimize.grid(row=6, column=0, padx=20, pady=4, sticky="ew")

        self.btn_deploy = ctk.CTkButton(self.sidebar_frame, text="5. Enviar a Raspberry Pi", command=self.run_deploy, fg_color="#00897B", hover_color="#00695C", font=ctk.CTkFont(size=14, weight="bold"), height=35)
        self.btn_deploy.grid(row=7, column=0, padx=20, pady=4, sticky="ew")

        path_icono_central = os.path.join("recursos", "icono_central.png")
        if os.path.exists(path_icono_central):
            try:
                img_ic = Image.open(path_icono_central)
                img_ic_ctk = ctk.CTkImage(light_image=img_ic, dark_image=img_ic, size=(60, 60))
                self.icono_label = ctk.CTkLabel(self.sidebar_frame, text="", image=img_ic_ctk)
                self.icono_label.grid(row=8, column=0, padx=20, pady=(5, 5))
            except (IOError, AttributeError): pass

        self.switch_var = ctk.StringVar(value="on")
        self.switch_theme = ctk.CTkSwitch(self.sidebar_frame, text="Modo Oscuro", command=self.toggle_appearance_mode, variable=self.switch_var, onvalue="on", offvalue="off")
        self.switch_theme.grid(row=9, column=0, padx=20, pady=(0, 5))

        self.lbl_performance = ctk.CTkButton(self.sidebar_frame, text="Ver Rendimiento", font=ctk.CTkFont(size=11), fg_color="transparent", text_color="#A5D6A7", command=self.toggle_performance)
        self.lbl_performance.grid(row=10, column=0, padx=20, pady=(0, 5))

        self.perf_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="#222222", corner_radius=5)
        self.perf_frame.grid_remove()

        self.cpu_bar = self.create_perf_bar(self.perf_frame, "CPU:", "#4CAF50")
        self.ram_bar = self.create_perf_bar(self.perf_frame, "RAM:", "#1E88E5")
        self.gpu_bar = self.create_perf_bar(self.perf_frame, "GPU (RTX):", "#F57C00")

        self.update_performance_stats()

        # CONSOLA PRINCIPAL
        self.main_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.console_label = ctk.CTkLabel(self.main_frame, text="Monitor de eventos MLOps", font=ctk.CTkFont(size=16, weight="bold"))
        self.console_label.grid(row=0, column=0, padx=0, pady=(0, 5), sticky="w")

        self.btn_factory = ctk.CTkButton(self.main_frame, text="Resetear de Fabrica", command=self.run_reset_all, fg_color="#D32F2F", hover_color="#C62828", font=ctk.CTkFont(size=12, weight="bold"), width=130, height=30)
        self.btn_factory.grid(row=0, column=0, sticky="e", padx=(0, 80))

        path_history_icon = os.path.join("recursos", "history_icon.png")
        if os.path.exists(path_history_icon):
            try:
                img_hist = Image.open(path_history_icon)
                img_hist_ctk = ctk.CTkImage(light_image=img_hist, dark_image=img_hist, size=(24, 24))
                self.btn_history = ctk.CTkButton(self.main_frame, text="", image=img_hist_ctk, width=30, height=30, fg_color="transparent", hover_color=("#DBDBDB", "#2B2B2B"), command=self.open_history)
                self.btn_history.grid(row=0, column=0, sticky="e", padx=(0, 40))
            except (IOError, AttributeError): pass

        path_config_icon = os.path.join("recursos", "config_icon.png")
        if os.path.exists(path_config_icon):
            try:
                img_conf = Image.open(path_config_icon)
                img_conf_ctk = ctk.CTkImage(light_image=img_conf, dark_image=img_conf, size=(24, 24))
                self.btn_settings = ctk.CTkButton(self.main_frame, text="", image=img_conf_ctk, width=30, height=30, fg_color="transparent", hover_color=("#DBDBDB", "#2B2B2B"), command=self.open_settings)
                self.btn_settings.grid(row=0, column=0, sticky="e", padx=(0, 5))
            except (IOError, AttributeError): pass
        else:
            self.btn_settings = ctk.CTkButton(self.main_frame, text="Config", width=30, height=30, fg_color="transparent", command=self.open_settings)
            self.btn_settings.grid(row=0, column=0, sticky="e", padx=(0, 5))

        self.progressbar = ctk.CTkProgressBar(self.main_frame, mode="indeterminate", height=6, fg_color="#333333", progress_color="#1E88E5")
        self.progressbar.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.progressbar.set(0)

        self.console = ctk.CTkTextbox(self.main_frame, fg_color="#1A1A1A", text_color="#4CAF50", border_color="#333333", border_width=2, font=("Consolas", 13))
        self.console.grid(row=2, column=0, sticky="nsew")

        self.footer_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.footer_frame.grid(row=3, column=0, sticky="e", pady=(5, 0))

        ctk.CTkLabel(self.footer_frame, text="Creado por: Medina Albaro y Asencio Issaias | Contacto: ", font=ctk.CTkFont(size=11, slant="italic"), text_color="#AAAAAA").pack(side="left")
        lbl_email1 = ctk.CTkLabel(self.footer_frame, text="medinaferesalbaro@gmail.com", cursor="hand2", font=ctk.CTkFont(size=11, slant="italic", underline=True), text_color="#1E88E5")
        lbl_email1.pack(side="left")
        lbl_email1.bind("<Button-1>", lambda e: webbrowser.open("mailto:medinaferesalbaro@gmail.com"))
        ctk.CTkLabel(self.footer_frame, text=" - ", font=ctk.CTkFont(size=11, slant="italic"), text_color="#AAAAAA").pack(side="left")
        lbl_email2 = ctk.CTkLabel(self.footer_frame, text="issaiasasencio@gmail.com", cursor="hand2", font=ctk.CTkFont(size=11, slant="italic", underline=True), text_color="#1E88E5")
        lbl_email2.pack(side="left")
        lbl_email2.bind("<Button-1>", lambda e: webbrowser.open("mailto:issaiasasencio@gmail.com"))

        self.python_exe = ".\\venv\\Scripts\\python.exe"
        self.log(f"[SISTEMA INICIADO] Conectado al intérprete virtual: {self.python_exe}\nEsperando instrucciones...\n{'-' * 60}")

    def controlar_escaneo_remoto(self, accion):
        """Detiene o reinicia el escáner en la Raspberry Pi para liberar la cámara."""
        def task():
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(
                    self.config_data.get("ip_raspberry", "192.168.1.10"), 
                    username=self.config_data.get("usuario", "pi"), 
                    password=self.config_data.get("contrasena", "12345678"),
                    timeout=5
                )
                if accion == "detener":
                    self.after(0, lambda: self.log("[REMOTO] Solicitando liberación de cámara en Raspberry Pi..."))
                    ssh.exec_command("pkill -f main.py")
                elif accion == "iniciar":
                    self.after(0, lambda: self.log("[REMOTO] Reanudando servicios de escaneo en Raspberry Pi..."))
                    # Corregido a .venv según se ve en tu terminal
                    ssh.exec_command("nohup /home/pi/Desktop/Flex-Sort/.venv/bin/python /home/pi/Desktop/Flex-Sort/rpi_panel.py > /dev/null 2>&1 &")
                ssh.close()
            except Exception as e:
                self.after(0, lambda: self.log(f"[REMOTO] Aviso: No se pudo {accion} el escaneo. Error: {str(e)}"))
        threading.Thread(target=task, daemon=True).start()

    def open_settings(self):
        dialog = SettingsDialog(self)
        self.wait_window(dialog)

    def open_history(self):
        dialog = HistoryDialog(self)
        self.wait_window(dialog)

    def run_bg_calibration(self):
        confirm = messagebox.askyesno("Calibración de Fondo", "Asegúrate de que la cinta esté ENCENDIDA y COMPLETAMENTE VACÍA.\n¿Deseas iniciar la captura de 10 segundos?", parent=self)
        if confirm:
            self.log("\n[CALIBRACION] Iniciando captura remota de fondo maestro...")
            self.controlar_escaneo_remoto("detener")
            self.progressbar.start()
            def task():
                success = capturar_y_procesar_fondo()
                self.after(0, self.progressbar.stop)
                if success:
                    msg_exito = "Fondo maestro capturado y procesado correctamente.\n\nSISTEMA LISTO: Ya podés proceder al PASO 2 (Entrenar Inteligencia)."
                    self.after(0, lambda: messagebox.showinfo("Éxito", msg_exito, parent=self))
                    self.after(0, lambda: self.log("[CALIBRACION] Fondo maestro listo para futuros entrenamientos."))
                else:
                    self.after(0, lambda: messagebox.showerror("Error", "No se pudo realizar la calibracion remota. Chequea los logs.", parent=self))
                    self.after(0, lambda: self.log("[ERROR] Falla en la calibracion de fondo."))
                self.controlar_escaneo_remoto("iniciar")
            threading.Thread(target=task, daemon=True).start()

    def open_report(self):
        dialog = ReportDialog(self)
        self.wait_window(dialog)

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

    def run_subprocess(self, cmd, on_finish=None):
        def task():
            self.after(0, self.progressbar.start)
            self.log(f"> \n> EJECUTANDO: {' '.join(cmd)}\n")
            kwargs = {}
            if sys.platform == "win32":
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            custom_env = os.environ.copy()
            custom_env["PYTHONIOENCODING"] = "utf-8"
            kwargs["env"] = custom_env
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True, encoding='utf-8', errors='replace', **kwargs)
            for line in process.stdout:
                self.after(0, self.log, line.strip())
            process.wait()
            self.after(0, self.progressbar.stop)
            self.after(0, self.progressbar.set, 0)
            self.after(0, self.log, f"\n[ CÓDIGO FINALIZADO ]\n{'-'*70}\n")
            if on_finish: self.after(0, on_finish)
        threading.Thread(target=task, daemon=True).start()

    def create_perf_bar(self, parent, label, color):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=10)).pack(side="left")
        bar = ctk.CTkProgressBar(frame, height=8, progress_color=color, fg_color="#333333")
        bar.set(0)
        bar.pack(side="right", fill="x", expand=True, padx=(5, 0))
        return bar

    def toggle_performance(self):
        if self.perf_frame.winfo_viewable():
            self.perf_frame.grid_remove()
            self.lbl_performance.configure(text="📊 Ver Rendimiento")
        else:
            self.perf_frame.grid(row=11, column=0, padx=10, pady=(0, 20), sticky="ew")
            self.lbl_performance.configure(text="📊 Ocultar Rendimiento")

    def update_performance_stats(self):
        def get_gpu_usage():
            try:
                cmd = ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"]
                result = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if result.returncode == 0: return int(result.stdout.strip())
            except: pass
            return 0
        cpu = psutil.cpu_percent() / 100
        ram = psutil.virtual_memory().percent / 100
        gpu = get_gpu_usage() / 100
        self.cpu_bar.set(cpu)
        self.ram_bar.set(ram)
        self.gpu_bar.set(gpu)
        self.after(2000, self.update_performance_stats)

    def run_reset_all(self):
        respuesta = messagebox.askyesnocancel("PELIGRO: BORRADO MASIVO", "Estás a punto de ELIMINAR permanentemente:\n- Todas las fotos y videos capturados\n- Todas los modelos de IA entrenados en la historia\n- El archivo de configuración de servos\n\n¿Deseás REINICIAR LA MEMORIA VIRTUAL para un proyecto nuevo?")
        if not respuesta: return
        self.log("\n[FORMATEO] Eliminando archivos antiguos de la IA...")
        folders_to_delete = ["Proyecto_FlexSort/dataset/images", "Proyecto_FlexSort/dataset/labels", "Proyecto_FlexSort/entrenamientos", "Proyecto_FlexSort/modelos_archivados", "runs"]
        files_to_delete = ["Proyecto_FlexSort/dataset/data.yaml", "Proyecto_FlexSort/dataset/servo_mapping.json"]
        for folder in folders_to_delete:
            if os.path.exists(folder):
                try: shutil.rmtree(folder)
                except: pass
        for f in files_to_delete:
            if os.path.exists(f):
                try: os.remove(f)
                except: pass
        self.run_setup()

    def run_setup(self):
        self.run_subprocess([self.python_exe, "1_setup_vacio.py"])

    def run_ingest(self):
        dialog = SourceSelectorDialog(self)
        self.wait_window(dialog)
        opcion_fuente = dialog.source_type
        if not opcion_fuente: return
        if opcion_fuente == "webcam": video_path = "webcam"
        elif opcion_fuente == "raspberry": video_path = "raspberry"
        else:
            video_path = filedialog.askopenfilename(title="Seleccionar Video RAW", filetypes=[("Archivos MP4", "*.mp4"), ("Todos", "*.*")])
            if not video_path: return
        fuente_display = "Camara Raspberry Pi" if opcion_fuente == "raspberry" else ("Camara en vivo" if opcion_fuente == "webcam" else os.path.basename(video_path))
        categoria = simpledialog.askstring("Etiqueta IA", f"Modo de ingesta: {fuente_display}\n\nIngresá el tipo de objeto (ej: manzana, pieza_metal):", parent=self)
        if not categoria: return
        dialog = ServoSelectorDialog(self, categoria)
        self.wait_window(dialog)
        servo_id = dialog.servo_id
        if not servo_id: return
        es_limpio = messagebox.askyesnocancel("Memoria IA", "El modelo tiene información anterior.\n\n¿Deseás REINICIAR LA MEMORIA VIRTUAL y comenzar la IA 100% desde cero?\n\n- SÍ = Resetear base de datos\n- NO = Anexar conocimientos", parent=self)
        if es_limpio is None: return
        opcion = "b" if es_limpio else "a"
        if opcion_fuente == "raspberry": self.controlar_escaneo_remoto("detener")

        def on_finish_ingest():
            def check_bg_calibration():
                ruta_fondo = os.path.join("Proyecto_FlexSort", "recursos", "fondo_maestro")
                fondo_detectado = False
                if os.path.exists(ruta_fondo):
                    for f in os.listdir(ruta_fondo):
                        if f.endswith(".jpg"):
                            fondo_detectado = True
                            break
                if fondo_detectado: msg = "¡OBJETO GUARDADO! Además, se detectó tú último Fondo Maestro (cinta vacía) y se aplicó con éxito.\n\n¿Deseás grabar un fondo maestro NUEVO ahora?"
                else: msg = "¡OBJETO GUARDADO! Sin embargo...\n\nNo se detectó un Fondo Maestro de tu cinta vacía.\n¿Deseás grabar el fondo vacío ahora?"
                if messagebox.askyesno("Calibración del Fondo", msg, parent=self): self.run_bg_calibration()
            
            check_bg_calibration()
            if opcion_fuente == "raspberry": self.controlar_escaneo_remoto("iniciar")
            
        self.run_subprocess([self.python_exe, "2_procesar_video.py", video_path, categoria, opcion, servo_id], on_finish=on_finish_ingest)

    def run_train(self):
        dialog = TrainingManagerDialog(self)
        self.wait_window(dialog)
        if not dialog.result: return
        def suggest_report():
            if messagebox.askyesno("Entrenamiento Finalizado", "¿Deseás ver el Reporte de Calidad del nuevo modelo ahora?"): self.open_report()
        self.run_subprocess([self.python_exe, "3_entrenar_modelo.py", dialog.result], on_finish=suggest_report)

    def run_infer(self):
        modelo_path = ""
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
            active = config.get("active_model")
            if active and os.path.exists(active): modelo_path = active
        except: pass
        if not modelo_path:
            pt_files = []
            for root_dir, dirs, files in os.walk(os.getcwd()):
                if "venv" in root_dir or ".git" in root_dir: continue
                for file in files:
                    if file.endswith(".pt") and "yolo" not in file: pt_files.append(os.path.join(root_dir, file))
            if pt_files:
                pt_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                latest = pt_files[0]
                if messagebox.askyesno("Historial", f"¿Activar último modelo entrenado?\n{os.path.basename(latest)}"): modelo_path = latest
        if not modelo_path: modelo_path = filedialog.askopenfilename(title="Seleccionar Cerebro YOLO (.pt)", filetypes=[("Modelos YOLO", "*.pt")])
        if modelo_path: self.run_subprocess([self.python_exe, "4_probar_modelo_pc.py", modelo_path])

    def run_optimize(self):
        modelo_path = ""
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
            active = config.get("active_model")
            if active and os.path.exists(active): modelo_path = active
        except: pass

        if not modelo_path:
            pt_files = []
            for root_dir, dirs, files in os.walk(os.getcwd()):
                if "venv" in root_dir or ".git" in root_dir: continue
                for file in files:
                    if file.endswith(".pt") and "yolo" not in file: pt_files.append(os.path.join(root_dir, file))
            if pt_files:
                pt_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                latest = pt_files[0]
                if messagebox.askyesno("Optimización", f"¿Optimizar último modelo entrenado?\n{os.path.basename(latest)}"): 
                    modelo_path = latest

        if not modelo_path: 
            modelo_path = filedialog.askopenfilename(title="Seleccionar Modelo para Optimizar", filetypes=[("Modelos YOLO", "*.pt")])
        
        if modelo_path:
            self.run_subprocess([self.python_exe, "5_optimizar_modelo.py", modelo_path, "ncnn"])

    def run_deploy(self):
        modelos_ncnn = []
        for root, dirs, files in os.walk(os.getcwd()):
            # Evitar carpetas pesadas o irrelevantes
            if "venv" in root or ".git" in root: continue
            for d in dirs:
                if d.endswith("_ncnn_model"):
                    modelos_ncnn.append(os.path.join(root, d))
        
        if not modelos_ncnn:
            messagebox.showerror("Error", "No se encontró ningún modelo optimizado para Raspberry Pi.\n\nAseguráte de haber completado el Paso 4 (Optimizar NCNN) primero.")
            return
        
        # Ordenar por fecha de modificación (el más reciente primero)
        modelos_ncnn.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        # Enviar el modelo más reciente encontrado
        self.run_subprocess([self.python_exe, "6_enviar_a_raspberry.py", modelos_ncnn[0]])

if __name__ == "__main__":
    app = MLOpsPanel()
    app.mainloop()
