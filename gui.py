import sys
import os
import shutil
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
from PIL import Image, ImageTk
from transcribe_melody import transcribe_audio_to_midi
from convert_tab_to_midi import create_midi_from_tab
import seed_tracking

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_config(data):
    try:
        current = load_config()
        current.update(data)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

import re

def get_unique_midi_path(path):
    directory, filename = os.path.split(path)
    name, ext = os.path.splitext(filename)
    
    # Limpiar cualquier sufijo numerado previo como (1), (2), (1)(1)...
    match = re.search(r'^(.*?)(?:\(\d+\))+$', name)
    if match:
        clean_name = match.group(1).rstrip()
    else:
        clean_name = name.rstrip()
        
    candidate = os.path.join(directory, f"{clean_name}{ext}")
    if not os.path.exists(candidate):
        return candidate
        
    counter = 1
    candidate = os.path.join(directory, f"{clean_name}({counter}){ext}")
    while os.path.exists(candidate):
        counter += 1
        candidate = os.path.join(directory, f"{clean_name}({counter}){ext}")
    return candidate

class BandurriaTranscriberGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Transcriptor de Melodías de Bandurria a MIDI (MuseScore)")
        self.root.geometry("780x820")
        self.root.minsize(700, 720)
        
        # Paleta de colores Light Warm & Cheerful Premium
        self.BG_COLOR = "#f8fafc"
        self.CARD_BG = "#ffffff"
        self.TEXT_MAIN = "#0f172a"
        self.TEXT_MUTED = "#64748b"
        self.ACCENT_PRIMARY = "#4f46e5"
        self.ACCENT_WARM = "#d97706"
        self.BORDER_COLOR = "#e2e8f0"
        
        self.root.configure(bg=self.BG_COLOR)
        
        # Estilos TTK
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.style.configure(".", background=self.BG_COLOR, foreground=self.TEXT_MAIN, font=("Segoe UI", 10))
        self.style.configure("TFrame", background=self.BG_COLOR)
        self.style.configure("Card.TFrame", background=self.CARD_BG, relief="flat")
        self.style.configure("TLabel", background=self.BG_COLOR, foreground=self.TEXT_MAIN)
        self.style.configure("Card.TLabel", background=self.CARD_BG, foreground=self.TEXT_MAIN)
        self.style.configure("Muted.TLabel", background=self.CARD_BG, foreground=self.TEXT_MUTED, font=("Segoe UI", 9))
        self.style.configure("Header.TLabel", font=("Segoe UI", 15, "bold"), foreground=self.ACCENT_PRIMARY, background=self.BG_COLOR)
        
        self.style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"), background=self.ACCENT_PRIMARY, foreground="#ffffff")
        self.style.map("Primary.TButton", background=[("active", "#4338ca")])
        self.style.configure("Secondary.TButton", font=("Segoe UI", 9, "bold"), background="#e2e8f0", foreground="#1e293b")
        self.style.map("Secondary.TButton", background=[("active", "#cbd5e1")])
        self.style.configure("Danger.TButton", font=("Segoe UI", 10, "bold"), background="#ef4444", foreground="#ffffff")
        self.style.map("Danger.TButton", background=[("active", "#dc2626"), ("disabled", "#e2e8f0")], foreground=[("disabled", "#94a3b8")])
        
        self.cancel_event = threading.Event()
        
        self.style.configure("TCombobox", fieldbackground="#ffffff", background="#e2e8f0", foreground=self.TEXT_MAIN, arrowcolor=self.TEXT_MAIN, selectbackground=self.ACCENT_PRIMARY, selectforeground="#ffffff")
        self.style.map("TCombobox", fieldbackground=[("readonly", "#ffffff")], foreground=[("readonly", self.TEXT_MAIN)])
        self.style.configure("TCheckbutton", background=self.CARD_BG, foreground=self.TEXT_MAIN, font=("Segoe UI", 9))
        self.style.map("TCheckbutton", background=[("active", self.CARD_BG)])

        # Icono
        ico_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.ico")
        if os.path.exists(ico_path):
            try:
                self.root.iconbitmap(ico_path)
            except Exception:
                pass

        # Header Title con Logo
        header_frame = ttk.Frame(root, padding=(20, 15, 20, 10))
        header_frame.pack(fill="x")
        
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path)
                img = img.resize((55, 55), Image.Resampling.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(img)
                lbl_logo = ttk.Label(header_frame, image=self.logo_img)
                lbl_logo.pack(side="left", padx=(0, 12))
                self.root.iconphoto(True, self.logo_img)
            except Exception:
                pass
                
        text_frame = ttk.Frame(header_frame)
        text_frame.pack(side="left", fill="both", expand=True)

        lbl_title = ttk.Label(text_frame, text="🪕 Transcriptor de Melodías de Bandurria a MIDI", style="Header.TLabel")
        lbl_title.pack(anchor="w")
        lbl_subtitle = ttk.Label(text_frame, text="Convierte tu audio, vídeo o tablatura a partitura limpia en sonido Piano para MuseScore.")
        lbl_subtitle.pack(anchor="w", pady=(2, 0))

        # Main Container (Un Solo Cuerpo Sin Pestañas)
        main_container = ttk.Frame(root, padding=(20, 0, 20, 15))
        main_container.pack(fill="both", expand=True)

        # Card Principal: Selección de Modo y Parámetros
        card_main = ttk.Frame(main_container, style="Card.TFrame", padding=15)
        card_main.pack(fill="x", pady=(0, 10))

        # Desplegable Único de Modo / Algoritmo
        lbl_mode = ttk.Label(card_main, text="Modo / Algoritmo de Transcripción:", style="Card.TLabel", font=("Segoe UI", 10, "bold"))
        lbl_mode.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        self.mode_options = [
            "🤖 IA de Spotify (Basic Pitch - Red Neuronal Recomendada)",
            "🌱 Con Nota Semilla (Seguimiento de Melodía por Intervalos)",
            "📝 Desde Tablatura (Texto)",
            "🎯 Análisis por Síntesis (Cotejo Espectral Armónico)",
            "⚡ PyIN (Estándar)"
        ]
        
        self.combo_mode = ttk.Combobox(card_main, values=self.mode_options, state="readonly", width=52, font=("Segoe UI", 9), style="TCombobox")
        self.combo_mode.current(0)
        self.combo_mode.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 10))
        self.combo_mode.bind("<<ComboboxSelected>>", self.on_mode_changed)

        # -------------------------------------------------------------
        # Panel Dinámico 1: Archivo de Entrada Audio / Vídeo
        # -------------------------------------------------------------
        self.frame_audio_file = ttk.Frame(card_main, style="Card.TFrame")
        self.frame_audio_file.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 6))

        lbl_input = ttk.Label(self.frame_audio_file, text="Archivo de Audio o Vídeo (.mp4, .mp3, .wav, .m4a):", style="Card.TLabel", font=("Segoe UI", 9, "bold"))
        lbl_input.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        self.entry_input = tk.Entry(self.frame_audio_file, font=("Segoe UI", 10), bg="#ffffff", fg="#0f172a", insertbackground="#0f172a", relief="flat", highlightthickness=1, highlightbackground="#cbd5e1", highlightcolor="#4f46e5")
        self.entry_input.grid(row=1, column=0, sticky="ew", padx=(0, 8), ipady=3)

        btn_browse_in = ttk.Button(self.frame_audio_file, text="Examinar...", style="Secondary.TButton", command=self.browse_input)
        btn_browse_in.grid(row=1, column=1, sticky="e")
        self.frame_audio_file.columnconfigure(0, weight=1)

        # -------------------------------------------------------------
        # Panel Dinámico 2: Selección de Nota Semilla (Único Combo)
        # -------------------------------------------------------------
        self.frame_seed = ttk.Frame(card_main, style="Card.TFrame")
        self.frame_seed.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 6))

        lbl_seed = ttk.Label(self.frame_seed, text="Nota Semilla Inicial (Cifrado + Nota):", style="Card.TLabel", font=("Segoe UI", 9, "bold"))
        lbl_seed.grid(row=0, column=0, sticky="w", padx=(0, 8))

        self.seed_options = [f"Cifrado {item['cifrado']}  —  {item['note_es']} ({item['description']})" for item in seed_tracking.BANDURRIA_TAB_MAP]
        self.combo_seed_cifrado = ttk.Combobox(self.frame_seed, values=self.seed_options, state="readonly", width=46, font=("Segoe UI", 9), style="TCombobox")
        
        default_idx = next((i for i, item in enumerate(seed_tracking.BANDURRIA_TAB_MAP) if item['cifrado'] == '17'), 7)
        self.combo_seed_cifrado.current(default_idx)
        self.combo_seed_cifrado.grid(row=0, column=1, sticky="w")

        # -------------------------------------------------------------
        # Panel Dinámico 3: Secuencia de Tablatura (Texto)
        # -------------------------------------------------------------
        self.frame_tab_text = ttk.Frame(card_main, style="Card.TFrame")
        self.frame_tab_text.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 6))

        lbl_tab_text = ttk.Label(self.frame_tab_text, text="Pega la secuencia de tablatura (ej: 17-14-15-17-15-14-12-10...):", style="Card.TLabel", font=("Segoe UI", 9, "bold"))
        lbl_tab_text.pack(anchor="w", pady=(0, 4))

        self.txt_tab_input = tk.Text(self.frame_tab_text, height=4, bg="#ffffff", fg="#0f172a", font=("Consolas", 10), relief="flat", insertbackground="#0f172a", highlightthickness=1, highlightbackground="#cbd5e1", highlightcolor="#4f46e5")
        self.txt_tab_input.pack(fill="x", pady=(0, 4))

        default_tab_text = """17-14-15-17-15-14-12-10-12-15-14-22
10-21-23-10-12-14-17-14
20-22-24-10-24-22-20
20-22-24-10-24-22-20
22-24-10-12-10
20-10-24-23-22-21-23-21-20"""
        self.txt_tab_input.insert(tk.END, default_tab_text.strip())

        # -------------------------------------------------------------
        # Archivo MIDI de Salida
        # -------------------------------------------------------------
        lbl_output = ttk.Label(card_main, text="Archivo MIDI de Salida (.mid):", style="Card.TLabel", font=("Segoe UI", 9, "bold"))
        lbl_output.grid(row=5, column=0, columnspan=2, sticky="w", pady=(4, 4))

        frame_out_row = ttk.Frame(card_main, style="Card.TFrame")
        frame_out_row.grid(row=6, column=0, columnspan=2, sticky="ew")

        self.entry_output = tk.Entry(frame_out_row, font=("Segoe UI", 10), bg="#ffffff", fg="#0f172a", insertbackground="#0f172a", relief="flat", highlightthickness=1, highlightbackground="#cbd5e1", highlightcolor="#4f46e5")
        self.entry_output.pack(side="left", fill="x", expand=True, padx=(0, 8), ipady=3)

        btn_browse_out = ttk.Button(frame_out_row, text="Guardar en...", style="Secondary.TButton", command=self.browse_output)
        btn_browse_out.pack(side="right")

        # Cargar última ruta en config.json
        cfg = load_config()
        last_in = cfg.get("last_input_path")
        last_out = cfg.get("last_output_path")

        local_outputs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
        os.makedirs(local_outputs_dir, exist_ok=True)

        if last_in and os.path.exists(last_in):
            default_in = last_in
        else:
            default_in = r"G:\Mi unidad\AYo\Tuna\Canciones Tuna\Noche madrileña\Noche madrileña bandurria2.mp4"
            
        self.entry_input.insert(0, default_in)

        base_name = os.path.basename(os.path.splitext(default_in)[0])
        default_out = os.path.join(local_outputs_dir, f"{base_name}.mid")

        if last_out and os.path.exists(os.path.dirname(last_out)):
            # Si la ruta guardada es válida la usamos, si era una ruta problemática a Google Drive redirigimos a outputs local
            if "G:" in last_out or not os.path.exists(os.path.dirname(last_out)):
                default_out = os.path.join(local_outputs_dir, f"{base_name}.mid")
            else:
                default_out = last_out

        self.entry_output.insert(0, default_out)

        # -------------------------------------------------------------
        # Card de Opciones de Cuantización Rítmica y Puerta de Ruido
        # -------------------------------------------------------------
        card_opts = ttk.Frame(main_container, style="Card.TFrame", padding=12)
        card_opts.pack(fill="x", pady=(0, 10))

        lbl_opts = ttk.Label(card_opts, text="Ajustes Rítmicos y Puerta de Ruido:", style="Card.TLabel", font=("Segoe UI", 10, "bold"))
        lbl_opts.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 6))

        self.var_auto_bpm = tk.BooleanVar(value=True)
        chk_auto = ttk.Checkbutton(card_opts, text="⚡ Estimar Tempo (BPM) automáticamente", variable=self.var_auto_bpm, style="TCheckbutton", command=self.toggle_bpm_state)
        chk_auto.grid(row=1, column=0, columnspan=4, sticky="w", pady=(0, 6))

        lbl_bpm = ttk.Label(card_opts, text="Tempo (BPM):", style="Card.TLabel")
        lbl_bpm.grid(row=2, column=0, sticky="w", padx=(0, 6))

        self.spin_bpm = tk.Spinbox(card_opts, from_=40, to=240, width=6, font=("Segoe UI", 9), bg="#f1f5f9", fg="#94a3b8", insertbackground="#0f172a", buttonbackground="#e2e8f0", relief="flat", highlightthickness=1, highlightbackground="#cbd5e1", highlightcolor="#4f46e5", state="disabled")
        self.spin_bpm.delete(0, tk.END)
        self.spin_bpm.insert(0, "120")
        self.spin_bpm.grid(row=2, column=1, sticky="w", padx=(0, 16))

        lbl_subdiv = ttk.Label(card_opts, text="Subdivisión:", style="Card.TLabel")
        lbl_subdiv.grid(row=2, column=2, sticky="w", padx=(0, 6))

        self.combo_subdiv = ttk.Combobox(card_opts, values=["1/16 (Semicorcheas)", "1/8 (Corcheas)", "1/4 (Negras)"], state="readonly", width=20, font=("Segoe UI", 9), style="TCombobox")
        self.combo_subdiv.current(0)
        self.combo_subdiv.grid(row=2, column=3, sticky="w")

        # Puerta de Ruido
        self.var_auto_gate = tk.BooleanVar(value=True)
        self.chk_auto_gate = ttk.Checkbutton(card_opts, text="⚙️ Puerta de ruido automática", variable=self.var_auto_gate, style="TCheckbutton", command=self.toggle_gate_state)
        self.chk_auto_gate.grid(row=3, column=0, columnspan=4, sticky="w", pady=(6, 4))

        lbl_gate_val = ttk.Label(card_opts, text="Umbral (RMS):", style="Card.TLabel")
        lbl_gate_val.grid(row=4, column=0, sticky="w", padx=(0, 6))

        self.scale_gate = tk.Scale(card_opts, from_=0.005, to=0.050, resolution=0.001, orient="horizontal", bg=self.CARD_BG, fg=self.TEXT_MUTED, troughcolor=self.BG_COLOR, activebackground=self.ACCENT_PRIMARY, highlightthickness=0, showvalue=True, state="disabled", length=180)
        self.scale_gate.set(0.015)
        self.scale_gate.grid(row=4, column=1, columnspan=3, sticky="w")

        # -------------------------------------------------------------
        # Barra de Progreso (%) y Consola de Log
        # -------------------------------------------------------------
        progress_frame = ttk.Frame(main_container)
        progress_frame.pack(fill="x", pady=(0, 6))

        self.progress_var = tk.DoubleVar(value=0.0)
        self.progressbar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progressbar.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.lbl_progress_pct = ttk.Label(progress_frame, text="0%", font=("Segoe UI", 10, "bold"), foreground=self.ACCENT_PRIMARY)
        self.lbl_progress_pct.pack(side="right")

        log_frame = ttk.Frame(main_container)
        log_frame.pack(fill="both", expand=True, pady=(0, 10))

        self.txt_log = tk.Text(log_frame, height=4, bg="#1e293b", fg="#f8fafc", font=("Consolas", 9), relief="flat", wrap="word", insertbackground="#ffffff")
        self.txt_log.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(log_frame, command=self.txt_log.yview)
        scrollbar.pack(side="right", fill="y")
        self.txt_log.config(yscrollcommand=scrollbar.set)

        # -------------------------------------------------------------
        # Línea 1: Controles de Ejecución (Convertir / Detener)
        # -------------------------------------------------------------
        top_action_frame = ttk.Frame(main_container)
        top_action_frame.pack(fill="x", pady=(0, 8))

        top_action_frame.columnconfigure(0, weight=3)
        top_action_frame.columnconfigure(1, weight=1)

        self.btn_convert = ttk.Button(top_action_frame, text="🎵 CONVERTIR Y TRANSCRIBIR A MIDI", style="Primary.TButton", command=self.start_transcription_thread)
        self.btn_convert.grid(row=0, column=0, sticky="ew", padx=(0, 4), ipady=7)

        self.btn_cancel = ttk.Button(top_action_frame, text="🛑 DETENER", style="Danger.TButton", command=self.cancel_transcription, state="disabled")
        self.btn_cancel.grid(row=0, column=1, sticky="ew", padx=(4, 0), ipady=7)

        # -------------------------------------------------------------
        # Línea 2: Acciones del Resultado (Abrir Carpeta, Cifrado, MIDI, MuseScore)
        # -------------------------------------------------------------
        self.post_frame = ttk.Frame(main_container)
        self.post_frame.pack(fill="x")

        self.post_frame.columnconfigure(0, weight=1, uniform="post_btn")
        self.post_frame.columnconfigure(1, weight=1, uniform="post_btn")
        self.post_frame.columnconfigure(2, weight=1, uniform="post_btn")
        self.post_frame.columnconfigure(3, weight=1, uniform="post_btn")

        self.btn_open_folder = ttk.Button(self.post_frame, text="📂 Abrir Carpeta", style="Secondary.TButton", command=self.open_output_folder)
        self.btn_open_folder.grid(row=0, column=0, sticky="ew", padx=(0, 3), ipady=5)

        self.btn_open_txt = ttk.Button(self.post_frame, text="📜 Cifrado TXT", style="Secondary.TButton", command=self.open_cifrado_txt)
        self.btn_open_txt.grid(row=0, column=1, sticky="ew", padx=3, ipady=5)

        self.btn_open_midi = ttk.Button(self.post_frame, text="🎹 Abrir MIDI", style="Secondary.TButton", command=self.open_midi_file)
        self.btn_open_midi.grid(row=0, column=2, sticky="ew", padx=3, ipady=5)

        self.btn_open_musescore = ttk.Button(self.post_frame, text="🎼 MuseScore 4", style="Secondary.TButton", command=self.open_in_musescore)
        self.btn_open_musescore.grid(row=0, column=3, sticky="ew", padx=(3, 0), ipady=5)

        self.last_midi_output = default_out
        
        # Inicializar visibilidad contextual según el modo por defecto
        self.on_mode_changed()

    def on_mode_changed(self, event=None):
        mode_text = self.combo_mode.get()
        
        if "Tablatura" in mode_text:
            self.frame_audio_file.grid_remove()
            self.frame_seed.grid_remove()
            self.frame_tab_text.grid()
        elif "Semilla" in mode_text:
            self.frame_audio_file.grid()
            self.frame_seed.grid()
            self.frame_tab_text.grid_remove()
        else:
            # Modos Audio/Vídeo estándar (Spotify AI, PyIN, Spectral)
            self.frame_audio_file.grid()
            self.frame_seed.grid_remove()
            self.frame_tab_text.grid_remove()

    def set_progress(self, val):
        self.progress_var.set(val)
        if hasattr(self, 'lbl_progress_pct'):
            self.lbl_progress_pct.config(text=f"{int(round(val))}%")

    def cancel_transcription(self):
        if hasattr(self, 'cancel_event'):
            self.cancel_event.set()
            self.log("⚠️ Solicitando cancelación del proceso...")
            self.btn_cancel.config(state="disabled")

    def log(self, message):
        def _update():
            self.txt_log.insert(tk.END, message + "\n")
            self.txt_log.see(tk.END)
        self.root.after(0, _update)

    def browse_input(self):
        filename = filedialog.askopenfilename(
            title="Seleccionar archivo de audio/vídeo de Bandurria",
            filetypes=[("Archivos multimedia", "*.mp4 *.mp3 *.wav *.m4a *.avi *.flac"), ("Todos los archivos", "*.*")]
        )
        if filename:
            self.entry_input.delete(0, tk.END)
            self.entry_input.insert(0, filename)
            
            base_name = os.path.basename(os.path.splitext(filename)[0])
            orig_dir = os.path.dirname(os.path.abspath(filename))
            
            raw_out = os.path.join(orig_dir, f"{base_name}.mid")
            out_path = get_unique_midi_path(raw_out)
            
            self.entry_output.delete(0, tk.END)
            self.entry_output.insert(0, out_path)
            self.last_midi_output = out_path
            save_config({"last_input_path": filename, "last_output_path": out_path})

    def browse_output(self):
        filename = filedialog.asksaveasfilename(
            title="Guardar archivo MIDI como",
            defaultextension=".mid",
            filetypes=[("Archivo MIDI", "*.mid"), ("Todos los archivos", "*.*")]
        )
        if filename:
            self.entry_output.delete(0, tk.END)
            self.entry_output.insert(0, filename)
            self.last_midi_output = filename
            save_config({"last_output_path": filename})

    def toggle_bpm_state(self):
        if self.var_auto_bpm.get():
            self.spin_bpm.config(state="disabled", fg=self.TEXT_MUTED)
        else:
            self.spin_bpm.config(state="normal", fg=self.TEXT_MAIN)

    def toggle_gate_state(self):
        if self.var_auto_gate.get():
            self.scale_gate.config(state="disabled", fg=self.TEXT_MUTED)
        else:
            self.scale_gate.config(state="normal", fg=self.TEXT_MAIN)

    def start_transcription_thread(self):
        mode_text = self.combo_mode.get()

        if "Tablatura" in mode_text:
            tab_text = self.txt_tab_input.get(1.0, tk.END).strip()
            if not tab_text:
                messagebox.showerror("Error de Tablatura", "Por favor pega la secuencia de tablatura de la canción.")
                return
            
            midi_path = self.entry_output.get().strip()
            if not midi_path:
                midi_path = r"G:\Mi unidad\AYo\Tuna\Canciones Tuna\Noche madrileña\Noche_madrileña_Tablatura_Piano.mid"
            
            midi_path = get_unique_midi_path(midi_path)
            self.entry_output.delete(0, tk.END)
            self.entry_output.insert(0, midi_path)
                
            try:
                bpm = 120 if self.var_auto_bpm.get() else int(self.spin_bpm.get())
            except ValueError:
                bpm = 120
                
            self.txt_log.delete(1.0, tk.END)
            self.log("▶ Generando partitura MIDI en sonido de Piano desde la tablatura...")
            self.set_progress(50)
            
            try:
                create_midi_from_tab(tab_text, midi_path, bpm=bpm)
                self.set_progress(100)
                self.last_midi_output = midi_path
                self.log(f"¡Éxito! MIDI desde tablatura guardado en: {midi_path}")
                self.on_transcription_success(midi_path)
            except Exception as e:
                self.log(f"❌ Error al convertir tablatura: {str(e)}")
                messagebox.showerror("Error", f"No se pudo procesar la tablatura:\n{str(e)}")
            return

        # Modos de Audio / Vídeo
        audio_path = self.entry_input.get().strip()
        midi_path = self.entry_output.get().strip()
                
        if not audio_path or not os.path.exists(audio_path):
            messagebox.showerror("Error de Archivo", f"El archivo de entrada no existe o no es válido:\n'{audio_path}'")
            return
            
        if not midi_path:
            messagebox.showerror("Error de Salida", "Por favor especifica una ruta válida para el archivo MIDI de salida.")
            return
            
        midi_path = get_unique_midi_path(midi_path)
        midi_path = os.path.abspath(os.path.normpath(midi_path))
        os.makedirs(os.path.dirname(midi_path), exist_ok=True)
        
        self.entry_output.delete(0, tk.END)
        self.entry_output.insert(0, midi_path)
        self.last_midi_output = midi_path

        save_config({"last_input_path": audio_path, "last_output_path": midi_path})

        if self.var_auto_bpm.get():
            bpm = "auto"
        else:
            try:
                bpm = int(self.spin_bpm.get())
            except ValueError:
                bpm = 120
            
        subdiv_text = self.combo_subdiv.get()
        if "1/8" in subdiv_text:
            subdiv = 8
        elif "1/4" in subdiv_text:
            subdiv = 4
        else:
            subdiv = 16

        if self.var_auto_gate.get():
            gate_val = "auto"
        else:
            try:
                gate_val = float(self.scale_gate.get())
            except ValueError:
                gate_val = 0.015

        # Seleccionar Algoritmo
        if "Spotify" in mode_text or "Basic Pitch" in mode_text:
            algo = "spotify_ai"
        elif "Semilla" in mode_text:
            algo = "seed"
        elif "Síntesis" in mode_text or "Cotejo" in mode_text:
            algo = "spectral"
        else:
            algo = "pyin"

        # Obtener seed_midi
        seed_idx = self.combo_seed_cifrado.current()
        if seed_idx < 0 or seed_idx >= len(seed_tracking.BANDURRIA_TAB_MAP):
            seed_idx = 7
        seed_midi = seed_tracking.BANDURRIA_TAB_MAP[seed_idx]['midi']

        self.cancel_event.clear()
        self.btn_convert.config(state="disabled")
        self.btn_cancel.config(state="normal")
        self.set_progress(10)
        self.txt_log.delete(1.0, tk.END)
        self.log(f"▶ Iniciando transcripción de Bandurria con el algoritmo: {mode_text}...")

        thread = threading.Thread(target=self.run_transcription, args=(audio_path, midi_path, bpm, subdiv, gate_val, algo, seed_midi), daemon=True)
        thread.start()

    def run_transcription(self, audio_path, midi_path, bpm, subdiv, gate_val, algorithm="spotify_ai", seed_midi=76):
        try:
            def callback(msg):
                if self.cancel_event.is_set():
                    raise InterruptedError("Transcripción cancelada por el usuario.")
                self.log(msg)
                if "Cargando" in msg or "Audio cargado" in msg:
                    self.root.after(0, lambda: self.set_progress(30))
                elif "Predicción" in msg or "Calculando" in msg:
                    self.root.after(0, lambda: self.set_progress(50))
                elif "Unificando" in msg:
                    self.root.after(0, lambda: self.set_progress(70))
                elif "Cuantizando" in msg:
                    self.root.after(0, lambda: self.set_progress(90))
                elif "Éxito" in msg or "Evaluación Completada" in msg:
                    self.root.after(0, lambda: self.set_progress(100))

            accuracy_pct = transcribe_audio_to_midi(
                audio_path=audio_path,
                midi_path=midi_path,
                bpm=bpm,
                subdivision=subdiv,
                rms_threshold=gate_val,
                algorithm=algorithm,
                seed_midi=seed_midi,
                log_callback=callback,
                check_cancel=lambda: self.cancel_event.is_set()
            )
            
            if not self.cancel_event.is_set():
                self.root.after(0, lambda: self.on_transcription_success(midi_path, accuracy_pct))
        except Exception as e:
            if isinstance(e, InterruptedError) or self.cancel_event.is_set():
                self.log("\n🛑 Transcripción cancelada por el usuario.")
                self.root.after(0, lambda: self.set_progress(0))
                self.root.after(0, lambda: messagebox.showwarning("Proceso Detenido", "La conversión ha sido cancelada por el usuario."))
            else:
                self.log(f"\n❌ Error durante la transcripción: {str(e)}")
                self.root.after(0, lambda: messagebox.showerror("Error de Transcripción", f"Ocurrió un error:\n{str(e)}"))
        finally:
            self.root.after(0, lambda: self.btn_convert.config(state="normal"))
            self.root.after(0, lambda: self.btn_cancel.config(state="disabled"))

    def move_files_to_original_dir(self, midi_path, audio_path):
        if not audio_path or not os.path.exists(audio_path):
            return midi_path
            
        orig_dir = os.path.dirname(os.path.abspath(audio_path))
        if not os.path.exists(orig_dir):
            return midi_path

        current_midi_abs = os.path.abspath(os.path.normpath(midi_path))
        current_xml_abs = os.path.splitext(current_midi_abs)[0] + ".musicxml"
        
        filename = os.path.basename(current_midi_abs)
        target_midi_raw = os.path.join(orig_dir, filename)
        
        # Si ya está en orig_dir y no hay colisión salvo consigo mismo
        if os.path.dirname(current_midi_abs).lower() == orig_dir.lower():
            target_midi_final = current_midi_abs
        else:
            target_midi_final = get_unique_midi_path(target_midi_raw)

        target_xml_final = os.path.splitext(target_midi_final)[0] + ".musicxml"

        # Mover archivo MIDI si el destino difiere
        if current_midi_abs != target_midi_final and os.path.exists(current_midi_abs):
            try:
                shutil.move(current_midi_abs, target_midi_final)
            except Exception as e:
                self.log(f"Aviso al mover MIDI a carpeta original: {str(e)}")

        # Mover archivo MusicXML si existe
        if os.path.exists(current_xml_abs):
            if current_xml_abs != target_xml_final:
                try:
                    shutil.move(current_xml_abs, target_xml_final)
                except Exception as e:
                    self.log(f"Aviso al mover MusicXML a carpeta original: {str(e)}")

        # Mover archivo Cifrado TXT si existe
        current_txt_abs = os.path.splitext(current_midi_abs)[0] + "_cifrado.txt"
        target_txt_final = os.path.splitext(target_midi_final)[0] + "_cifrado.txt"
        if os.path.exists(current_txt_abs):
            if current_txt_abs != target_txt_final:
                try:
                    shutil.move(current_txt_abs, target_txt_final)
                except Exception as e:
                    self.log(f"Aviso al mover Cifrado TXT a carpeta original: {str(e)}")

        return target_midi_final

    def on_transcription_success(self, midi_path, accuracy_pct=None):
        audio_path = self.entry_input.get().strip()
        final_midi = self.move_files_to_original_dir(midi_path, audio_path)
        final_midi = os.path.abspath(os.path.normpath(final_midi))
        final_xml = os.path.splitext(final_midi)[0] + ".musicxml"
        
        self.last_midi_output = final_midi
        self.entry_output.delete(0, tk.END)
        self.entry_output.insert(0, final_midi)
        
        save_config({
            "last_input_path": audio_path,
            "last_output_path": final_midi
        })
        
        self.log(f"📦 Archivos movidos a la carpeta original del audio:\n - MIDI: {final_midi}\n - MusicXML: {final_xml}")
        
        acc_text = f"\n🎯 Porcentaje de Acierto Melódico: {accuracy_pct}%\n" if accuracy_pct is not None else ""
        messagebox.showinfo(
            "¡Transcripción Completada!", 
            f"¡Archivo MIDI y MusicXML generados y movidos con éxito a la carpeta original!{acc_text}\nRuta: {final_midi}\n\nPuedes hacer clic en 'Abrir Carpeta', 'Abrir MIDI' o 'Abrir en MuseScore'."
        )

    def open_output_folder(self):
        midi_path = self.last_midi_output or self.entry_output.get().strip()
        if midi_path:
            abs_path = os.path.abspath(os.path.normpath(midi_path))
            folder = os.path.dirname(abs_path)
            if os.path.exists(abs_path):
                subprocess.Popen(f'explorer /select,"{abs_path}"')
            elif os.path.exists(folder):
                subprocess.Popen(f'explorer "{folder}"')
            else:
                messagebox.showerror("Error", f"La carpeta de destino no existe:\n{folder}")
        else:
            messagebox.showerror("Error", "No hay ningún archivo seleccionado.")

    def open_cifrado_txt(self):
        midi_path = self.last_midi_output or self.entry_output.get().strip()
        if midi_path:
            abs_midi = os.path.abspath(os.path.normpath(midi_path))
            base_path, _ = os.path.splitext(abs_midi)
            txt_path = base_path + "_cifrado.txt"
            if os.path.exists(txt_path):
                os.startfile(txt_path)
                return
            elif os.path.exists(abs_midi):
                import seed_tracking, pretty_midi
                try:
                    pm = pretty_midi.PrettyMIDI(abs_midi)
                    notes = []
                    for inst in pm.instruments:
                        for n in inst.notes:
                            notes.append({'pitch': n.pitch, 'start': n.start})
                    notes = sorted(notes, key=lambda x: x['start'])
                    song_title = os.path.basename(base_path).replace("_", " ").title()
                    report_content = seed_tracking.format_cifrado_txt_report(notes, title=song_title)
                    with open(txt_path, "w", encoding="utf-8") as f:
                        f.write(report_content)
                    os.startfile(txt_path)
                    return
                except Exception:
                    pass
        messagebox.showerror("Error", f"El archivo de Cifrado TXT no se encuentra en el disco:\n{midi_path}")

    def open_midi_file(self):
        midi_path = self.last_midi_output or self.entry_output.get().strip()
        if midi_path:
            abs_path = os.path.abspath(os.path.normpath(midi_path))
            if os.path.exists(abs_path):
                os.startfile(abs_path)
                return
        messagebox.showerror("Error", f"El archivo MIDI no existe en el disco:\n{midi_path}")

    def open_in_musescore(self):
        midi_path = self.last_midi_output or self.entry_output.get().strip()
        if not midi_path:
            messagebox.showerror("Error", "No hay ningún archivo generado disponible.")
            return

        abs_midi = os.path.abspath(os.path.normpath(midi_path))
        base_path, _ = os.path.splitext(abs_midi)
        musicxml_path = base_path + ".musicxml"

        target_file = musicxml_path if os.path.exists(musicxml_path) else abs_midi
        if not os.path.exists(target_file):
            messagebox.showerror("Error", f"El archivo no existe en el disco:\n{target_file}")
            return

        musescore_path = r"C:\Program Files\MuseScore 4\bin\MuseScore4.exe"
        if not os.path.exists(musescore_path):
            musescore_path = r"C:\Program Files\MuseScore 3\bin\MuseScore3.exe"

        if os.path.exists(musescore_path):
            self.log(f"🎼 Abriendo '{os.path.basename(target_file)}' en MuseScore...")
            subprocess.Popen([musescore_path, target_file])
        else:
            self.log("Aviso: MuseScore 4 no se encontró en la ruta estándar. Abriendo con la aplicación por defecto de Windows...")
            os.startfile(target_file)

def launch_gui():
    root = tk.Tk()
    app = BandurriaTranscriberGUI(root)
    root.mainloop()

if __name__ == "__main__":
    launch_gui()
