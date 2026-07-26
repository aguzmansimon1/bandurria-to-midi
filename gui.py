import sys
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from transcribe_melody import transcribe_audio_to_midi

class BandurriaTranscriberGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Transcriptor de Melodías de Bandurria a MIDI (MuseScore)")
        self.root.geometry("680x560")
        self.root.minsize(600, 500)
        
        # Aplicar estilo oscuro moderno
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Paleta de colores
        BG_COLOR = "#1e1e2e"
        CARD_BG = "#282a36"
        TEXT_COLOR = "#f8f8f2"
        ACCENT_COLOR = "#6272a4"
        BTN_COLOR = "#50fa7b"
        
        self.root.configure(bg=BG_COLOR)
        
        self.style.configure(".", background=BG_COLOR, foreground=TEXT_COLOR, font=("Segoe UI", 10))
        self.style.configure("TFrame", background=BG_COLOR)
        self.style.configure("Card.TFrame", background=CARD_BG, relief="flat")
        self.style.configure("TLabel", background=BG_COLOR, foreground=TEXT_COLOR)
        self.style.configure("Card.TLabel", background=CARD_BG, foreground=TEXT_COLOR)
        self.style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), foreground="#8be9fd", background=BG_COLOR)
        self.style.configure("TCheckbutton", background=CARD_BG, foreground=TEXT_COLOR)
        
        # Botón estilo primario
        self.style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"), background="#6272a4", foreground="#ffffff")
        self.style.map("Primary.TButton", background=[("active", "#bd93f9")])

        # Header Frame
        header_frame = ttk.Frame(root, padding=15)
        header_frame.pack(fill="x")
        
        lbl_title = ttk.Label(header_frame, text="🪕 Transcriptor de Bandurria a MIDI", style="Header.TLabel")
        lbl_title.pack(anchor="w")
        lbl_subtitle = ttk.Label(header_frame, text="Extrae la melodía de tu bandurria, unifica el trémolo de púa y genera un MIDI listo para MuseScore.")
        lbl_subtitle.pack(anchor="w", pady=(2, 0))

        # Main Container
        main_container = ttk.Frame(root, padding=15)
        main_container.pack(fill="both", expand=True)

        # Card 1: Selección de archivos
        card_files = ttk.Frame(main_container, style="Card.TFrame", padding=15)
        card_files.pack(fill="x", pady=(0, 10))
        
        # Input file
        lbl_input = ttk.Label(card_files, text="1. Archivo de Audio o Vídeo de Bandurria (.mp4, .mp3, .wav):", style="Card.TLabel", font=("Segoe UI", 10, "bold"))
        lbl_input.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
        
        self.entry_input = ttk.Entry(card_files, width=50)
        self.entry_input.grid(row=1, column=0, sticky="ew", padx=(0, 5))
        
        btn_browse_in = ttk.Button(card_files, text="Examinar...", command=self.browse_input)
        btn_browse_in.grid(row=1, column=1, sticky="e")
        
        # Default path
        default_in = r"G:\Mi unidad\AYo\Tuna\Canciones Tuna\Noche madrileña\Noche madrileña bandurria.mp4"
        if os.path.exists(default_in):
            self.entry_input.insert(0, default_in)
            
        # Output file
        lbl_output = ttk.Label(card_files, text="2. Archivo MIDI de Salida (.mid):", style="Card.TLabel", font=("Segoe UI", 10, "bold"))
        lbl_output.grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 5))
        
        self.entry_output = ttk.Entry(card_files, width=50)
        self.entry_output.grid(row=3, column=0, sticky="ew", padx=(0, 5))
        
        btn_browse_out = ttk.Button(card_files, text="Guardar en...", command=self.browse_output)
        btn_browse_out.grid(row=3, column=1, sticky="e")
        
        default_out = r"G:\Mi unidad\AYo\Tuna\Canciones Tuna\Noche madrileña\Noche madrileña bandurria.mid"
        self.entry_output.insert(0, default_out)

        card_files.columnconfigure(0, weight=1)

        # Card 2: Opciones de Cuantización y MuseScore
        card_opts = ttk.Frame(main_container, style="Card.TFrame", padding=15)
        card_opts.pack(fill="x", pady=(0, 10))
        
        lbl_opts = ttk.Label(card_opts, text="Ajustes de Cuantización (MuseScore):", style="Card.TLabel", font=("Segoe UI", 10, "bold"))
        lbl_opts.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))
        
        lbl_bpm = ttk.Label(card_opts, text="Tempo (BPM):", style="Card.TLabel")
        lbl_bpm.grid(row=1, column=0, sticky="w", padx=(0, 5))
        
        self.spin_bpm = ttk.Spinbox(card_opts, from_=40, to=240, width=8)
        self.spin_bpm.set(120)
        self.spin_bpm.grid(row=1, column=1, sticky="w", padx=(0, 20))
        
        lbl_subdiv = ttk.Label(card_opts, text="Subdivisión Rítmica:", style="Card.TLabel")
        lbl_subdiv.grid(row=1, column=2, sticky="w", padx=(0, 5))
        
        self.combo_subdiv = ttk.Combobox(card_opts, values=["1/16 (Semicorcheas)", "1/8 (Corcheas)", "1/4 (Negras)"], state="readonly", width=20)
        self.combo_subdiv.current(0)
        self.combo_subdiv.grid(row=1, column=3, sticky="w")

        # Progress & Log Area
        self.progress_var = tk.DoubleVar()
        self.progressbar = ttk.Progressbar(main_container, variable=self.progress_var, maximum=100)
        self.progressbar.pack(fill="x", pady=(0, 8))
        
        # Log Text area
        log_frame = ttk.Frame(main_container)
        log_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        self.txt_log = tk.Text(log_frame, height=8, bg="#181825", fg="#a6adc8", font=("Consolas", 9), relief="flat", wrap="word")
        self.txt_log.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, command=self.txt_log.yview)
        scrollbar.pack(side="right", fill="y")
        self.txt_log.config(yscrollcommand=scrollbar.set)
        
        # Start Button
        self.btn_convert = ttk.Button(main_container, text="🎵 CONVERTIR Y TRANSCRIBIR A MIDI", style="Primary.TButton", command=self.start_transcription_thread)
        self.btn_convert.pack(fill="x", ipady=8)

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
            
            # Auto-generate default output path
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
        audio_path = self.entry_input.get().strip()
        midi_path = self.entry_output.get().strip()
        
        if not audio_path or not os.path.exists(audio_path):
            messagebox.showerror("Error", "Por favor selecciona un archivo de audio/vídeo válido de entrada.")
            return
            
        if not midi_path:
            messagebox.showerror("Error", "Por favor especifica una ruta de salida para el archivo MIDI.")
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
        self.progress_var.set(10)
        self.txt_log.delete(1.0, tk.END)
        self.log("▶ Iniciando transcripción de Bandurria...")
        
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
                    self.root.after(0, lambda: self.progress_var.set(85))
                elif "Éxito" in msg:
                    self.root.after(0, lambda: self.progress_var.set(100))

            transcribe_audio_to_midi(
                audio_path=audio_path,
                midi_path=midi_path,
                bpm=bpm,
                subdivision=subdiv,
                log_callback=callback
            )
            
            self.root.after(0, lambda: messagebox.showinfo("Transcripción Completada", f"¡Archivo MIDI generado con éxito!\n\nRuta: {midi_path}\n\nYa puedes abrirlo directamente en MuseScore."))
        except Exception as e:
            self.log(f"\n❌ Error durante la transcripción: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Ocurrió un error inesperado:\n{str(e)}"))
        finally:
            self.root.after(0, lambda: self.btn_convert.config(state="normal"))

def launch_gui():
    root = tk.Tk()
    app = BandurriaTranscriberGUI(root)
    root.mainloop()

if __name__ == "__main__":
    launch_gui()
