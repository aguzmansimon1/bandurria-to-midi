import sys
import os
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from transcribe_melody import transcribe_audio_to_midi
from convert_tab_to_midi import create_midi_from_tab

class BandurriaTranscriberGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Transcriptor de Melodías de Bandurria a MIDI (MuseScore)")
        self.root.geometry("740x680")
        self.root.minsize(680, 600)
        
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
        
        # Estilo de botones y controles
        self.style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"), background="#6366f1", foreground="#ffffff")
        self.style.map("Primary.TButton", background=[("active", "#4f46e5")])
        self.style.configure("Secondary.TButton", font=("Segoe UI", 9, "bold"), background="#334155", foreground="#ffffff")
        self.style.map("Secondary.TButton", background=[("active", "#475569")])
        
        self.style.configure("TCombobox", fieldbackground="#0f172a", background="#1e293b", foreground="#ffffff", arrowcolor="#ffffff", selectbackground="#818cf8")
        self.style.map("TCombobox", fieldbackground=[("readonly", "#0f172a")], foreground=[("readonly", "#ffffff")])
        self.style.configure("TCheckbutton", background=self.CARD_BG, foreground=self.TEXT_MAIN, font=("Segoe UI", 9))
        self.style.map("TCheckbutton", background=[("active", self.CARD_BG)])

        # Establecer icono oficial de la ventana
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
                img = img.resize((56, 56), Image.Resampling.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(img)
                lbl_logo = ttk.Label(header_frame, image=self.logo_img)
                lbl_logo.pack(side="left", padx=(0, 14))
                self.root.iconphoto(True, self.logo_img)
            except Exception:
                pass
                
        text_frame = ttk.Frame(header_frame)
        text_frame.pack(side="left", fill="both", expand=True)

        lbl_title = ttk.Label(text_frame, text="Transcriptor de Bandurria a MIDI (Piano)", style="Header.TLabel")
        lbl_title.pack(anchor="w")
        lbl_subtitle = ttk.Label(text_frame, text="Genera partituras limpias en sonido Piano Acústico desde tu audio/vídeo o pegando tu tablatura.")
        lbl_subtitle.pack(anchor="w", pady=(2, 0))

        # Main Container
        main_container = ttk.Frame(root, padding=(20, 0, 20, 15))
        main_container.pack(fill="both", expand=True)

        # Tabs (Notebook): Modo 1 (Audio / Vídeo) | Modo 2 (Tablatura Directa)
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill="x", pady=(0, 10))

        # Tab 1: Transcripción de Audio / Vídeo
        self.tab_audio = ttk.Frame(self.notebook, style="Card.TFrame", padding=15)
        self.notebook.add(self.tab_audio, text=" 🎙️ Desde Audio / Vídeo ")

        lbl_input = ttk.Label(self.tab_audio, text="Archivo de Audio o Vídeo (.mp4, .mp3, .wav):", style="Card.TLabel", font=("Segoe UI", 10, "bold"))
        lbl_input.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
        
        self.entry_input = tk.Entry(self.tab_audio, font=("Segoe UI", 10), bg="#0f172a", fg="#ffffff", insertbackground="#ffffff", relief="flat", highlightthickness=1, highlightbackground="#334155", highlightcolor="#818cf8")
        self.entry_input.grid(row=1, column=0, sticky="ew", padx=(0, 8), ipady=4)
        
        btn_browse_in = ttk.Button(self.tab_audio, text="Examinar...", style="Secondary.TButton", command=self.browse_input)
        btn_browse_in.grid(row=1, column=1, sticky="e")
        
        lbl_output = ttk.Label(self.tab_audio, text="Archivo MIDI de Salida (.mid):", style="Card.TLabel", font=("Segoe UI", 10, "bold"))
        lbl_output.grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 4))
        
        self.entry_output = tk.Entry(self.tab_audio, font=("Segoe UI", 10), bg="#0f172a", fg="#ffffff", insertbackground="#ffffff", relief="flat", highlightthickness=1, highlightbackground="#334155", highlightcolor="#818cf8")
        self.entry_output.grid(row=3, column=0, sticky="ew", padx=(0, 8), ipady=4)
        
        btn_browse_out = ttk.Button(self.tab_audio, text="Guardar en...", style="Secondary.TButton", command=self.browse_output)
        btn_browse_out.grid(row=3, column=1, sticky="e")
        
        self.tab_audio.columnconfigure(0, weight=1)

        # Cargar ruta por defecto (Noche madrileña bandurria2.mp4)
        default_in = r"G:\Mi unidad\AYo\Tuna\Canciones Tuna\Noche madrileña\Noche madrileña bandurria2.mp4"
        if not os.path.exists(default_in):
            default_in = r"G:\Mi unidad\AYo\Tuna\Canciones Tuna\Noche madrileña\Noche madrileña bandurria.mp4"
        self.entry_input.insert(0, default_in)
        
        base, _ = os.path.splitext(default_in)
        default_out = base + ".mid"
        self.entry_output.insert(0, default_out)

        # Tab 2: Convertidor de Tablatura Directa
        self.tab_text = ttk.Frame(self.notebook, style="Card.TFrame", padding=15)
        self.notebook.add(self.tab_text, text=" 📝 Desde Tablatura (Texto) ")

        lbl_tab_text = ttk.Label(self.tab_text, text="Pega la secuencia de tablatura (ej: 17-14-15-17-15-14-12-10-12-15-14-22...):", style="Card.TLabel", font=("Segoe UI", 10, "bold"))
        lbl_tab_text.pack(anchor="w", pady=(0, 4))

        self.txt_tab_input = tk.Text(self.tab_text, height=5, bg="#0f172a", fg="#ffffff", font=("Consolas", 10), relief="flat", insertbackground="#ffffff")
        self.txt_tab_input.pack(fill="x", pady=(0, 6))

        default_tab_text = """17-14-15-17-15-14-12-10-12-15-14-22
10-21-23-10-12-14-17-14
20-22-24-10-24-22-20
20-22-24-10-24-22-20
22-24-10-12-10
20-10-24-23-22-21-23-21-20
10-24-23-24-10-17-14-10-20-17-13
10-24-23-22-21-21-21-21-23-10-
21-20-"""
        self.txt_tab_input.insert(tk.END, default_tab_text.strip())

        # Card de Opciones de Cuantización
        card_opts = ttk.Frame(main_container, style="Card.TFrame", padding=15)
        card_opts.pack(fill="x", pady=(0, 12))
        
        lbl_opts = ttk.Label(card_opts, text="Ajustes de Cuantización Rítmica (MuseScore):", style="Card.TLabel", font=("Segoe UI", 10, "bold"))
        lbl_opts.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))
        
        self.var_auto_bpm = tk.BooleanVar(value=True)
        chk_auto = ttk.Checkbutton(card_opts, text="⚡ Estimar Tempo (BPM) automáticamente de la canción", variable=self.var_auto_bpm, style="TCheckbutton", command=self.toggle_bpm_state)
        chk_auto.grid(row=1, column=0, columnspan=4, sticky="w", pady=(0, 8))
        
        lbl_bpm = ttk.Label(card_opts, text="Tempo Manual (BPM):", style="Card.TLabel")
        lbl_bpm.grid(row=2, column=0, sticky="w", padx=(0, 8))
        
        self.spin_bpm = tk.Spinbox(card_opts, from_=40, to=240, width=8, font=("Segoe UI", 10), bg="#0f172a", fg="#64748b", insertbackground="#ffffff", buttonbackground="#1e293b", relief="flat", highlightthickness=1, highlightbackground="#334155", highlightcolor="#818cf8", state="disabled")
        self.spin_bpm.delete(0, tk.END)
        self.spin_bpm.insert(0, "120")
        self.spin_bpm.grid(row=2, column=1, sticky="w", padx=(0, 24))
        
        lbl_subdiv = ttk.Label(card_opts, text="Subdivisión Rítmica:", style="Card.TLabel")
        lbl_subdiv.grid(row=2, column=2, sticky="w", padx=(0, 8))
        
        self.combo_subdiv = ttk.Combobox(card_opts, values=["1/16 (Semicorcheas)", "1/8 (Corcheas)", "1/4 (Negras)"], state="readonly", width=22, font=("Segoe UI", 9), style="TCombobox")
        self.combo_subdiv.current(0)
        self.combo_subdiv.grid(row=2, column=3, sticky="w")

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

        # Frame de botones visibles en todo momento
        self.post_frame = ttk.Frame(action_frame)
        self.post_frame.pack(fill="x", pady=(10, 0))
        
        self.btn_open_folder = ttk.Button(self.post_frame, text="📂 Abrir Carpeta", style="Secondary.TButton", command=self.open_output_folder)
        self.btn_open_folder.pack(side="left", fill="x", expand=True, padx=(0, 6))
        
        self.btn_open_musescore = ttk.Button(self.post_frame, text="🎼 Abrir en MuseScore", style="Secondary.TButton", command=self.open_in_musescore)
        self.btn_open_musescore.pack(side="right", fill="x", expand=True, padx=(6, 0))
        
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

    def toggle_bpm_state(self):
        if self.var_auto_bpm.get():
            self.spin_bpm.config(state="disabled", fg="#64748b")
        else:
            self.spin_bpm.config(state="normal", fg="#ffffff")

    def start_transcription_thread(self):
        selected_tab = self.notebook.index(self.notebook.select())
        
        if selected_tab == 1:
            # Modo 2: Convertir desde Tablatura (Texto)
            tab_text = self.txt_tab_input.get(1.0, tk.END).strip()
            if not tab_text:
                messagebox.showerror("Error de Tablatura", "Por favor pega la secuencia de tablatura de la canción.")
                return
            
            midi_path = self.entry_output.get().strip()
            if not midi_path:
                midi_path = r"G:\Mi unidad\AYo\Tuna\Canciones Tuna\Noche madrileña\Noche_madrileña_Tablatura_Piano.mid"
                
            try:
                bpm = 120 if self.var_auto_bpm.get() else int(self.spin_bpm.get())
            except ValueError:
                bpm = 120
                
            self.txt_log.delete(1.0, tk.END)
            self.log("▶ Generando partitura MIDI en sonido de Piano desde la tablatura...")
            self.progress_var.set(50)
            
            try:
                create_midi_from_tab(tab_text, midi_path, bpm=bpm)
                self.progress_var.set(100)
                self.last_midi_output = midi_path
                self.log(f"¡Éxito! MIDI desde tablatura guardado en: {midi_path}")
                self.on_transcription_success(midi_path)
            except Exception as e:
                self.log(f"❌ Error al convertir tablatura: {str(e)}")
                messagebox.showerror("Error", f"No se pudo procesar la tablatura:\n{str(e)}")
            return

        # Modo 1: Transcripción desde Audio / Vídeo
        audio_path = self.entry_input.get().strip()
        midi_path = self.entry_output.get().strip()
                
        if not audio_path or not os.path.exists(audio_path):
            messagebox.showerror("Error de Archivo", f"El archivo de entrada no existe o no es válido:\n'{audio_path}'")
            return
            
        if not midi_path:
            messagebox.showerror("Error de Salida", "Por favor especifica una ruta válida para el archivo MIDI de salida.")
            return
            
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
            
        self.btn_convert.config(state="disabled")
        self.progress_var.set(10)
        self.txt_log.delete(1.0, tk.END)
        self.log("▶ Iniciando transcripción de Bandurria (Sonido Piano)...")
        
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
        messagebox.showinfo("¡Transcripción Completada!", f"¡Archivo MIDI generado con éxito!\n\nRuta: {midi_path}\n\nPuedes hacer clic en 'Abrir en MuseScore' para ver tu partitura.")

    def open_output_folder(self):
        midi_path = self.last_midi_output or self.entry_output.get().strip()
        if midi_path and os.path.exists(os.path.dirname(midi_path)):
            folder = os.path.dirname(midi_path)
            subprocess.run(["explorer", folder])
        else:
            messagebox.showwarning("Aviso", "No se encontró la carpeta del archivo MIDI.")

    def open_in_musescore(self):
        midi_path = self.last_midi_output or self.entry_output.get().strip()
        if not midi_path or not os.path.exists(midi_path):
            messagebox.showwarning("Aviso", f"El archivo MIDI no existe aún en el disco:\n'{midi_path}'\n\nPor favor, ejecuta primero la conversión.")
            return
            
        possible_paths = [
            r"C:\Program Files\MuseScore 4\bin\MuseScore4.exe",
            r"C:\Program Files\MuseScore 3\bin\MuseScore3.exe",
            r"C:\Program Files (x86)\MuseScore 3\bin\MuseScore3.exe",
        ]
        musescore_exe = None
        for path in possible_paths:
            if os.path.exists(path):
                musescore_exe = path
                break
                
        try:
            if musescore_exe:
                subprocess.Popen([musescore_exe, midi_path])
            else:
                os.startfile(midi_path)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir MuseScore automáticamente:\n{str(e)}")

def launch_gui():
    root = tk.Tk()
    app = BandurriaTranscriberGUI(root)
    root.lift()
    root.attributes('-topmost', True)
    root.after(100, lambda: root.attributes('-topmost', False))
    root.focus_force()
    root.mainloop()

if __name__ == "__main__":
    launch_gui()
