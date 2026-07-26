import sys
import os
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from transcribe_melody import transcribe_audio_to_midi

class BandurriaTranscriberGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Transcriptor de Melodías de Bandurria a MIDI (MuseScore)")
        self.root.geometry("720x640")
        self.root.minsize(650, 580)
        
        # Paleta de colores Dark Premium (Acorde a la interfaz web)
        self.BG_COLOR = "#0f172a"        # Slate 900
        self.CARD_BG = "#1e293b"         # Slate 800
        self.TEXT_MAIN = "#f8fafc"       # Slate 50
        self.TEXT_MUTED = "#94a3b8"      # Slate 400
        self.ACCENT_PURPLE = "#818cf8"  # Indigo 400
        self.SUCCESS_GREEN = "#34d399"   # Emerald 400
        
        self.root.configure(bg=self.BG_COLOR)
        
        # Configurar estilos de TTK
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.style.configure(".", background=self.BG_COLOR, foreground=self.TEXT_MAIN, font=("Segoe UI", 10))
        self.style.configure("TFrame", background=self.BG_COLOR)
        self.style.configure("Card.TFrame", background=self.CARD_BG, relief="flat")
        self.style.configure("TLabel", background=self.BG_COLOR, foreground=self.TEXT_MAIN)
        self.style.configure("Card.TLabel", background=self.CARD_BG, foreground=self.TEXT_MAIN)
        self.style.configure("Muted.TLabel", background=self.CARD_BG, foreground=self.TEXT_MUTED, font=("Segoe UI", 9))
        self.style.configure("Header.TLabel", font=("Segoe UI", 15, "bold"), foreground="#a5b4fc", background=self.BG_COLOR)
        
        # Estilo para Pestañas (Notebook)
        self.style.configure("TNotebook", background=self.BG_COLOR, borderwidth=0)
        self.style.configure("TNotebook.Tab", background="#1e293b", foreground=self.TEXT_MUTED, padding=[16, 8], font=("Segoe UI", 10, "bold"))
        self.style.map("TNotebook.Tab", background=[("selected", self.ACCENT_PURPLE)], foreground=[("selected", "#ffffff")])
        
        # Estilo de botones
        self.style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"), background="#6366f1", foreground="#ffffff")
        self.style.map("Primary.TButton", background=[("active", "#4f46e5")])
        self.style.configure("Secondary.TButton", font=("Segoe UI", 9, "bold"), background="#334155", foreground="#ffffff")
        self.style.map("Secondary.TButton", background=[("active", "#475569")])

        # Header Title
        header_frame = ttk.Frame(root, padding=(20, 15, 20, 10))
        header_frame.pack(fill="x")
        
        lbl_title = ttk.Label(header_frame, text="🪕 Transcriptor de Bandurria a MIDI", style="Header.TLabel")
        lbl_title.pack(anchor="w")
        lbl_subtitle = ttk.Label(header_frame, text="Extrae la melodía de tu bandurria, unifica el trémolo de púa y genera un MIDI cuantizado para MuseScore.")
        lbl_subtitle.pack(anchor="w", pady=(2, 0))

        # Main Container
        main_container = ttk.Frame(root, padding=(20, 0, 20, 15))
        main_container.pack(fill="both", expand=True)

        # Tabs (Notebook): Modo 1 (Selección por Explorador) / Modo 2 (Ruta Local Directa)
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill="x", pady=(0, 12))

        # Tab 1: Seleccionar con Explorador de Archivos
        self.tab_explorer = ttk.Frame(self.notebook, style="Card.TFrame", padding=15)
        self.notebook.add(self.tab_explorer, text=" 📁 Explorar Archivo ")

        lbl_input = ttk.Label(self.tab_explorer, text="Archivo de Audio o Vídeo (.mp4, .mp3, .wav):", style="Card.TLabel", font=("Segoe UI", 10, "bold"))
        lbl_input.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
        
        self.entry_input = tk.Entry(self.tab_explorer, font=("Segoe UI", 10), bg="#0f172a", fg="#ffffff", insertbackground="#ffffff", relief="flat", highlightthickness=1, highlightbackground="#334155", highlightcolor="#818cf8")
        self.entry_input.grid(row=1, column=0, sticky="ew", padx=(0, 8), ipady=4)
        
        btn_browse_in = ttk.Button(self.tab_explorer, text="Examinar...", style="Secondary.TButton", command=self.browse_input)
        btn_browse_in.grid(row=1, column=1, sticky="e")
        
        lbl_output = ttk.Label(self.tab_explorer, text="Archivo MIDI de Salida (.mid):", style="Card.TLabel", font=("Segoe UI", 10, "bold"))
        lbl_output.grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 4))
        
        self.entry_output = tk.Entry(self.tab_explorer, font=("Segoe UI", 10), bg="#0f172a", fg="#ffffff", insertbackground="#ffffff", relief="flat", highlightthickness=1, highlightbackground="#334155", highlightcolor="#818cf8")
        self.entry_output.grid(row=3, column=0, sticky="ew", padx=(0, 8), ipady=4)
        
        btn_browse_out = ttk.Button(self.tab_explorer, text="Guardar en...", style="Secondary.TButton", command=self.browse_output)
        btn_browse_out.grid(row=3, column=1, sticky="e")
        
        self.tab_explorer.columnconfigure(0, weight=1)

        # Tab 2: Ruta Local Directa
        self.tab_direct = ttk.Frame(self.notebook, style="Card.TFrame", padding=15)
        self.notebook.add(self.tab_direct, text=" 💻 Ruta Local en Disco ")

        lbl_direct = ttk.Label(self.tab_direct, text="Pega la ruta completa del archivo de tu PC:", style="Card.TLabel", font=("Segoe UI", 10, "bold"))
        lbl_direct.pack(anchor="w", pady=(0, 4))
        
        self.entry_direct_path = tk.Entry(self.tab_direct, font=("Segoe UI", 10), bg="#0f172a", fg="#ffffff", insertbackground="#ffffff", relief="flat", highlightthickness=1, highlightbackground="#334155", highlightcolor="#818cf8")
        self.entry_direct_path.pack(fill="x", pady=(0, 8), ipady=4)
        
        default_direct = r"G:\Mi unidad\AYo\Tuna\Canciones Tuna\Noche madrileña\Noche madrileña bandurria2.mp4"
        self.entry_direct_path.insert(0, default_direct)
        
        lbl_direct_help = ttk.Label(self.tab_direct, text="Abre directamente el archivo sin necesidad de seleccionarlo manualmente.", style="Muted.TLabel")
        lbl_direct_help.pack(anchor="w")

        # Cargar valores por defecto en Tab 1 si existen
        default_in = r"G:\Mi unidad\AYo\Tuna\Canciones Tuna\Noche madrileña\Noche madrileña bandurria.mp4"
        if os.path.exists(default_in):
            self.entry_input.insert(0, default_in)
        default_out = r"G:\Mi unidad\AYo\Tuna\Canciones Tuna\Noche madrileña\Noche madrileña bandurria.mid"
        self.entry_output.insert(0, default_out)

        # Card de Opciones de Cuantización
        card_opts = ttk.Frame(main_container, style="Card.TFrame", padding=15)
        card_opts.pack(fill="x", pady=(0, 12))
        
        lbl_opts = ttk.Label(card_opts, text="Ajustes de Cuantización Rítmica (MuseScore):", style="Card.TLabel", font=("Segoe UI", 10, "bold"))
        lbl_opts.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))
        
        lbl_bpm = ttk.Label(card_opts, text="Tempo Estimado (BPM):", style="Card.TLabel")
        lbl_bpm.grid(row=1, column=0, sticky="w", padx=(0, 8))
        
        self.spin_bpm = ttk.Spinbox(card_opts, from_=40, to=240, width=8, font=("Segoe UI", 10))
        self.spin_bpm.set(120)
        self.spin_bpm.grid(row=1, column=1, sticky="w", padx=(0, 24))
        
        lbl_subdiv = ttk.Label(card_opts, text="Subdivisión Rítmica:", style="Card.TLabel")
        lbl_subdiv.grid(row=1, column=2, sticky="w", padx=(0, 8))
        
        self.combo_subdiv = ttk.Combobox(card_opts, values=["1/16 (Semicorcheas)", "1/8 (Corcheas)", "1/4 (Negras)"], state="readonly", width=22, font=("Segoe UI", 9))
        self.combo_subdiv.current(0)
        self.combo_subdiv.grid(row=1, column=3, sticky="w")

        # Barra de Progreso y Consola de Log
        self.progress_var = tk.DoubleVar()
        self.progressbar = ttk.Progressbar(main_container, variable=self.progress_var, maximum=100)
        self.progressbar.pack(fill="x", pady=(0, 8))
        
        # Log Console Box
        log_frame = ttk.Frame(main_container)
        log_frame.pack(fill="both", expand=True, pady=(0, 12))
        
        self.txt_log = tk.Text(log_frame, height=8, bg="#0f172a", fg="#cbd5e1", font=("Consolas", 9), relief="flat", wrap="word", insertbackground="#ffffff")
        self.txt_log.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, command=self.txt_log.yview)
        scrollbar.pack(side="right", fill="y")
        self.txt_log.config(yscrollcommand=scrollbar.set)
        
        # Frame de Acción
        action_frame = ttk.Frame(main_container)
        action_frame.pack(fill="x")

        self.btn_convert = ttk.Button(action_frame, text="🎵 CONVERTIR Y TRANSCRIBIR A MIDI", style="Primary.TButton", command=self.start_transcription_thread)
        self.btn_convert.pack(fill="x", ipady=8)

        # Botón secundario para abrir carpeta contenedora al finalizar
        self.btn_open_folder = ttk.Button(action_frame, text="📂 Abrir Carpeta del Archivo MIDI", style="Secondary.TButton", command=self.open_output_folder)
        self.last_midi_output = None

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
            
            base, _ = os.path.splitext(filename)
            out_path = base + ".mid"
            self.entry_output.delete(0, tk.END)
            self.entry_output.insert(0, out_path)

    def browse_output(self):
        filename = filedialog.asksaveasfilename(
            title="Guardar archivo MIDI como",
            defaultextension=".mid",
            filetypes=[("Archivo MIDI", "*.mid"), ("Todos los archivos", "*.*")]
        )
        if filename:
            self.entry_output.delete(0, tk.END)
            self.entry_output.insert(0, filename)

    def start_transcription_thread(self):
        # Determinar pestaña activa
        selected_tab = self.notebook.index(self.notebook.select())
        
        if selected_tab == 0:
            # Tab Explorador
            audio_path = self.entry_input.get().strip()
            midi_path = self.entry_output.get().strip()
        else:
            # Tab Ruta Local Directa
            audio_path = self.entry_direct_path.get().strip()
            if audio_path:
                base, _ = os.path.splitext(audio_path)
                midi_path = base + ".mid"
            else:
                midi_path = ""
                
        if not audio_path or not os.path.exists(audio_path):
            messagebox.showerror("Error de Archivo", f"El archivo de entrada no existe o no es válido:\n'{audio_path}'")
            return
            
        if not midi_path:
            messagebox.showerror("Error de Salida", "Por favor especifica una ruta válida para el archivo MIDI de salida.")
            return
            
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
            
        self.btn_convert.config(state="disabled")
        self.btn_open_folder.pack_forget()
        self.progress_var.set(10)
        self.txt_log.delete(1.0, tk.END)
        self.log("▶ Iniciando transcripción de Bandurria...")
        
        self.last_midi_output = midi_path
        
        thread = threading.Thread(target=self.run_transcription, args=(audio_path, midi_path, bpm, subdiv), daemon=True)
        thread.start()

    def run_transcription(self, audio_path, midi_path, bpm, subdiv):
        try:
            def callback(msg):
                self.log(msg)
                if "Audio cargado" in msg:
                    self.root.after(0, lambda: self.progress_var.set(30))
                elif "Segmentando" in msg:
                    self.root.after(0, lambda: self.progress_var.set(50))
                elif "Unificando" in msg:
                    self.root.after(0, lambda: self.progress_var.set(70))
                elif "Cuantizando" in msg:
                    self.root.after(0, lambda: self.progress_var.set(90))
                elif "Éxito" in msg:
                    self.root.after(0, lambda: self.progress_var.set(100))

            transcribe_audio_to_midi(
                audio_path=audio_path,
                midi_path=midi_path,
                bpm=bpm,
                subdivision=subdiv,
                log_callback=callback
            )
            
            self.root.after(0, lambda: self.on_transcription_success(midi_path))
        except Exception as e:
            self.log(f"\n❌ Error durante la transcripción: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Error de Transcripción", f"Ocurrió un error:\n{str(e)}"))
        finally:
            self.root.after(0, lambda: self.btn_convert.config(state="normal"))

    def on_transcription_success(self, midi_path):
        self.btn_open_folder.pack(fill="x", pady=(8, 0))
        messagebox.showinfo("¡Transcripción Completada!", f"¡Archivo MIDI generado con éxito!\n\nRuta: {midi_path}\n\nYa puedes abrirlo directamente en MuseScore.")

    def open_output_folder(self):
        if self.last_midi_output and os.path.exists(os.path.dirname(self.last_midi_output)):
            folder = os.path.dirname(self.last_midi_output)
            subprocess.run(["explorer", folder])

def launch_gui():
    root = tk.Tk()
    app = BandurriaTranscriberGUI(root)
    root.mainloop()

if __name__ == "__main__":
    launch_gui()
