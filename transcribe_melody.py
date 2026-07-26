import sys
import os
import argparse
import av
import numpy as np
import librosa
import pretty_midi

def load_audio_av(path):
    print(f"Decodificando audio desde: {path}...")
    container = av.open(path)
    stream = container.streams.audio[0]
    
    target_sr = 22050
    resampler = av.AudioResampler(
        format='fltp',
        layout='mono',
        rate=target_sr,
    )
    
    audio_frames = []
    for frame in container.decode(stream):
        resampled_frames = resampler.resample(frame)
        for rf in resampled_frames:
            array = rf.to_ndarray()[0]
            audio_frames.append(array)
            
    if not audio_frames:
        raise ValueError("No se pudieron decodificar frames de audio.")
        
    y = np.concatenate(audio_frames)
    return y, target_sr

def merge_tremolo_notes(notes, max_gap=0.15, max_pitch_diff=1.0):
    """
    Fusiona notas consecutivas del mismo tono o tono casi idéntico separadas por 
    micro-pausas producidas por el plectro/trémolo de la bandurria.
    """
    if not notes:
        return []
        
    merged = [notes[0].copy()]
    for current in notes[1:]:
        previous = merged[-1]
        gap = current['start'] - previous['end']
        pitch_diff = abs(current['pitch'] - previous['pitch'])
        
        # Si el espacio entre notas es pequeño (típico golpe de púa) y el tono es el mismo
        if gap <= max_gap and pitch_diff <= max_pitch_diff:
            previous['end'] = current['end']
            previous['pitches'].extend(current['pitches'])
            previous['pitch'] = int(round(np.median(previous['pitches'])))
        else:
            merged.append(current.copy())
            
    return merged

def quantize_notes(notes, bpm=120, subdivision=16):
    """
    Cuantiza el inicio y fin de cada nota a la rejilla rítmica (p. ej. semicorcheas = 16),
    para generar partituras limpias e inteligibles en MuseScore.
    """
    if bpm <= 0 or not notes:
        return notes
        
    beat_duration = 60.0 / bpm
    grid_step = beat_duration / (subdivision / 4.0) # Duración de 1 paso de la rejilla (en segundos)
    
    quantized = []
    for n in notes:
        q_start = round(n['start'] / grid_step) * grid_step
        q_end = round(n['end'] / grid_step) * grid_step
        
        # Asegurar que la nota dure al menos 1 paso de rejilla
        if q_end <= q_start:
            q_end = q_start + grid_step
            
        note_copy = n.copy()
        note_copy['start'] = q_start
        note_copy['end'] = q_end
        quantized.append(note_copy)
        
    # Limpiar posibles notas solapadas tras la cuantización
    cleaned = []
    for n in quantized:
        if cleaned:
            prev = cleaned[-1]
            if n['start'] < prev['end']:
                if n['pitch'] == prev['pitch']:
                    prev['end'] = max(prev['end'], n['end'])
                    continue
                else:
                    n['start'] = prev['end']
            if n['start'] >= n['end']:
                continue
        cleaned.append(n)
        
    return cleaned

def calculate_note_velocities(notes, y, sr):
    """
    Calcula la intensidad (velocity MIDI 0-127) según la energía RMS del audio en cada nota.
    """
    if not notes:
        return notes
        
    for n in notes:
        start_sample = int(max(0, n['start'] * sr))
        end_sample = int(min(len(y), n['end'] * sr))
        
        if end_sample > start_sample:
            segment = y[start_sample:end_sample]
            rms = np.sqrt(np.mean(segment**2)) if len(segment) > 0 else 0.01
        else:
            rms = 0.01
            
        # Mapear RMS a rango MIDI (p. ej. entre 55 y 115)
        # Asumiendo un nivel RMS típico entre 0.005 y 0.2
        velocity = int(np.clip(55 + (rms / 0.15) * 60, 50, 120))
        n['velocity'] = velocity
        
    return notes

def transcribe_audio_to_midi(audio_path, midi_path, bpm=120, subdivision=16, fmin=300, fmax=1100, log_callback=None):
    def log(msg):
        print(msg)
        if log_callback:
            log_callback(msg)

    if not os.path.exists(audio_path):
        err_msg = f"Error: El archivo de entrada '{audio_path}' no existe."
        log(err_msg)
        if not log_callback:
            sys.exit(1)
        return
        
    # Cargar audio
    log("Cargando y decodificando audio...")
    y, sr = load_audio_av(audio_path)
    duracion = len(y) / sr
    log(f"Audio cargado. Duración: {duracion:.2f} segundos. Detectando afinación exacta para Bandurria...")
    
    # Detección de pitch pYIN acotada al registro real de la Bandurria (300 Hz a 1100 Hz)
    hop_length = 512
    f0, voiced_flag, voiced_probs = librosa.pyin(
        y, 
        fmin=fmin, 
        fmax=fmax, 
        sr=sr,
        hop_length=hop_length,
        fill_na=0.0
    )
    
    # Aplicar filtrado medfilt para eliminar saltos de armónicos
    import scipy.signal
    f0 = scipy.signal.medfilt(f0, kernel_size=5)
    
    times = librosa.frames_to_time(range(len(f0)), sr=sr, hop_length=hop_length)
    frame_duration = hop_length / sr
    
    log("Segmentando notas iniciales de la melodía...")
    notes = []
    current_note = None
    
    for i in range(len(f0)):
        freq = f0[i]
        t = times[i]
        
        if freq > 0:
            midi_pitch = librosa.hz_to_midi(freq)
            rounded_pitch = int(round(midi_pitch))
            
            if current_note is None:
                current_note = {
                    'pitch': rounded_pitch,
                    'start': t,
                    'end': t + frame_duration,
                    'pitches': [midi_pitch]
                }
            else:
                avg_pitch = np.median(current_note['pitches'])
                if abs(midi_pitch - avg_pitch) < 1.2:
                    current_note['end'] = t + frame_duration
                    current_note['pitches'].append(midi_pitch)
                else:
                    notes.append(current_note)
                    current_note = {
                        'pitch': rounded_pitch,
                        'start': t,
                        'end': t + frame_duration,
                        'pitches': [midi_pitch]
                    }
        else:
            if current_note is not None:
                notes.append(current_note)
                current_note = None
                
    if current_note is not None:
        notes.append(current_note)

    # Filtrar notas ruidosas ultra cortas (<60ms)
    min_note_duration = 0.06
    filtered_notes = [n for n in notes if (n['end'] - n['start']) >= min_note_duration]
    log(f"Notas iniciales detectadas: {len(filtered_notes)}")
    
    # 1. Unificación de Trémolos de Bandurria
    log("Unificando trémolos de púa de la bandurria...")
    merged_notes = merge_tremolo_notes(filtered_notes, max_gap=0.15, max_pitch_diff=1.0)
    log(f"Notas tras unificar trémolo: {len(merged_notes)}")
    
    # 2. Cuantización rítmica para MuseScore
    if bpm == "auto" or bpm == 0 or bpm is None:
        log("Estimando tempo (BPM) automáticamente del audio de la canción...")
        try:
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            detected_bpm = int(round(float(np.atleast_1d(tempo)[0])))
            if detected_bpm < 50 or detected_bpm > 200:
                detected_bpm = 120
            bpm = detected_bpm
            log(f"Tempo detectado automáticamente: {bpm} BPM")
        except Exception as e:
            bpm = 120
            log(f"No se pudo estimar el tempo automáticamente. Usando {bpm} BPM por defecto.")
    else:
        try:
            bpm = int(bpm)
        except ValueError:
            bpm = 120

    if bpm > 0:
        log(f"Cuantizando ritmo a {bpm} BPM (Subdivisión: 1/{subdivision})...")
        final_notes = quantize_notes(merged_notes, bpm=bpm, subdivision=subdivision)
    else:
        final_notes = merged_notes
        
    # 3. Dinámicas y Velocity por nota
    final_notes = calculate_note_velocities(final_notes, y, sr)
    
    log(f"Escribiendo archivo MIDI en sonido de Piano ({len(final_notes)} notas finalizadas)...")
    
    # Crear objeto MIDI asignando Acoustic Grand Piano (Program 0) para sonido limpio
    pm = pretty_midi.PrettyMIDI(initial_tempo=bpm if bpm > 0 else 120.0)
    piano_program = pretty_midi.instrument_name_to_program('Acoustic Grand Piano')
    piano_inst = pretty_midi.Instrument(program=piano_program, name="Melodia Piano")
    
    for n in final_notes:
        note_obj = pretty_midi.Note(
            velocity=n.get('velocity', 80),
            pitch=n['pitch'],
            start=n['start'],
            end=n['end']
        )
        piano_inst.notes.append(note_obj)
        
    pm.instruments.append(piano_inst)
    pm.write(midi_path)
    log(f"¡Éxito! MIDI guardado en: {midi_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transcriptor de Melodías de Bandurria a MIDI (MuseScore)")
    parser.add_argument("input", nargs="?", help="Ruta al archivo de audio o vídeo de entrada (mp4, mp3, wav)")
    parser.add_argument("output", nargs="?", help="Ruta de salida para el archivo MIDI (.mid)")
    parser.add_argument("--bpm", type=int, default=120, help="Tempo estimado en BPM para cuantización (por defecto 120, 0 para desactivar)")
    parser.add_argument("--subdivision", type=int, default=16, help="Subdivisión para la rejilla rítmica (16 = semicorcheas, 8 = corcheas)")
    parser.add_argument("--gui", action="store_true", help="Abrir la Interfaz Gráfica de Usuario")
    
    args = parser.parse_args()
    
    if args.gui or len(sys.argv) == 1:
        from gui import launch_gui
        launch_gui()
    elif args.input and args.output:
        transcribe_audio_to_midi(args.input, args.output, bpm=args.bpm, subdivision=args.subdivision)
    else:
        # Valores por defecto en consola
        audio_file = r"G:\Mi unidad\AYo\Tuna\Canciones Tuna\Noche madrileña\Noche madrileña bandurria.mp4"
        output_midi = r"G:\Mi unidad\AYo\Tuna\Canciones Tuna\Noche madrileña\Noche madrileña bandurria.mid"
        print(f"No se proporcionaron argumentos completos. Ejecutando con valores por defecto:")
        print(f"Entrada: {audio_file}")
        print(f"Salida: {output_midi}\n")
        transcribe_audio_to_midi(audio_file, output_midi, bpm=args.bpm, subdivision=args.subdivision)

