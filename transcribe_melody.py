import sys
import os
import argparse
import av
import numpy as np
import librosa
import pretty_midi
import xml.etree.ElementTree as ET
from xml.dom import minidom

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

def midi_to_musicxml_pitch(midi_num):
    steps = ['C', 'C', 'D', 'D', 'E', 'F', 'F', 'G', 'G', 'A', 'A', 'B']
    alters = [0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0]
    idx = midi_num % 12
    octave = (midi_num // 12) - 1
    return steps[idx], alters[idx], octave

def calculate_note_velocities(notes, y, sr):
    """
    Calcula la intensidad (velocity MIDI 0-127) y matices dinámicos según la energía RMS del audio en cada nota.
    """
    if not notes:
        return notes
        
    rms_values = []
    peak_values = []
    
    for n in notes:
        start_sample = int(max(0, n['start'] * sr))
        end_sample = int(min(len(y), n['end'] * sr))
        
        if end_sample > start_sample:
            segment = y[start_sample:end_sample]
            rms = float(np.sqrt(np.mean(segment**2))) if len(segment) > 0 else 0.01
            peak = float(np.max(np.abs(segment))) if len(segment) > 0 else 0.01
        else:
            rms = 0.01
            peak = 0.01
            
        n['rms'] = rms
        n['peak'] = peak
        rms_values.append(rms)
        peak_values.append(peak)
        
    rms_p10 = float(np.percentile(rms_values, 10)) if rms_values else 0.01
    rms_p90 = float(np.percentile(rms_values, 90)) if rms_values else 0.15
    rms_range = max(1e-4, rms_p90 - rms_p10)
    
    for n in notes:
        rel_energy = (n['rms'] - rms_p10) / rms_range
        velocity = int(np.clip(52 + rel_energy * 60, 45, 118))
        
        # Detección de acento de púa (si el pico del ataque es > 1.35x el RMS medio del segmento)
        is_accent = (n['peak'] > 1.35 * n['rms'])
        if is_accent:
            velocity = min(127, velocity + 10)
            
        n['velocity'] = velocity
        n['is_accent'] = is_accent
        
        if velocity >= 98:
            n['dynamic'] = 'f'
        elif velocity >= 82:
            n['dynamic'] = 'mf'
        elif velocity >= 68:
            n['dynamic'] = 'mp'
        else:
            n['dynamic'] = 'p'
            
    return notes

def export_to_musicxml(notes, xml_path, bpm=120, title="Partitura de Bandurria"):
    """
    Genera un archivo nativo de MusicXML (.musicxml) maquetado con Clave de Sol, 
    compás de 4/4, acentos de púa y matices dinámicos para MuseScore 4.
    """
    if not notes:
        return
        
    score = ET.Element('score-partwise', version='4.0')
    work = ET.SubElement(score, 'work')
    ET.SubElement(work, 'work-title').text = title

    part_list = ET.SubElement(score, 'part-list')
    score_part = ET.SubElement(part_list, 'score-part', id='P1')
    ET.SubElement(score_part, 'part-name').text = 'Bandurria / Piano'

    part = ET.SubElement(score, 'part', id='P1')

    divisions = 4 # Ticks por negra
    beat_sec = 60.0 / (bpm if bpm > 0 else 120.0)
    measure_dur_sec = 4.0 * beat_sec

    measures = {}
    sorted_notes = sorted(notes, key=lambda n: n['start'])

    for n in sorted_notes:
        start_sec = n['start']
        dur_sec = max(0.125 * beat_sec, n['end'] - n['start'])
        pitch = n['pitch']
        is_accent = n.get('is_accent', False)
        dynamic = n.get('dynamic', None)

        m_num = int(start_sec // measure_dur_sec) + 1
        if m_num not in measures:
            m_elt = ET.SubElement(part, 'measure', number=str(m_num))
            measures[m_num] = m_elt
            if m_num == 1:
                attr = ET.SubElement(m_elt, 'attributes')
                ET.SubElement(attr, 'divisions').text = str(divisions)
                key = ET.SubElement(attr, 'key')
                ET.SubElement(key, 'fifths').text = '0'
                time_elt = ET.SubElement(attr, 'time')
                ET.SubElement(time_elt, 'beats').text = '4'
                ET.SubElement(time_elt, 'beat-type').text = '4'
                clef = ET.SubElement(attr, 'clef')
                ET.SubElement(clef, 'sign').text = 'G'
                ET.SubElement(clef, 'line').text = '2'

                direction = ET.SubElement(m_elt, 'direction', placement='above')
                dir_type = ET.SubElement(direction, 'direction-type')
                metro = ET.SubElement(dir_type, 'metronome')
                ET.SubElement(metro, 'beat-unit').text = 'quarter'
                ET.SubElement(metro, 'per-minute').text = str(int(bpm if bpm > 0 else 120))

        current_measure = measures[m_num]

        if dynamic:
            dir_dyn = ET.SubElement(current_measure, 'direction', placement='below')
            dt = ET.SubElement(dir_dyn, 'direction-type')
            dyn = ET.SubElement(dt, 'dynamics')
            ET.SubElement(dyn, dynamic)

        note_elt = ET.SubElement(current_measure, 'note')

        step, alter, octave = midi_to_musicxml_pitch(pitch)
        p_elt = ET.SubElement(note_elt, 'pitch')
        ET.SubElement(p_elt, 'step').text = step
        if alter != 0:
            ET.SubElement(p_elt, 'alter').text = str(alter)
        ET.SubElement(p_elt, 'octave').text = str(octave)

        duration_divs = max(1, int(round((dur_sec / beat_sec) * divisions)))
        ET.SubElement(note_elt, 'duration').text = str(duration_divs)

        if duration_divs >= 4:
            note_type = 'quarter'
        elif duration_divs >= 2:
            note_type = 'eighth'
        else:
            note_type = 'sixteenth'
        ET.SubElement(note_elt, 'type').text = note_type

        if is_accent:
            notations = ET.SubElement(note_elt, 'notations')
            articulations = ET.SubElement(notations, 'articulations')
            ET.SubElement(articulations, 'accent')

    xml_str = minidom.parseString(ET.tostring(score)).toprettyxml(indent='  ')
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml_str)

def transcribe_audio_to_midi(audio_path, midi_path, bpm=120, subdivision=16, fmin=220, fmax=1400, rms_threshold="auto", log_callback=None):
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
    log(f"Audio cargado. Duración: {duracion:.2f} segundos.")
    
    # 1. Separación Armónico-Percusiva (HPSS) para aislar las notas de la bandurria
    log("Aislando melodía armónica de la bandurria con filtrado HPSS...")
    y_harmonic, y_percussive = librosa.effects.hpss(y)
    
    # 2. RMS de energía para filtrado de silencios y ruidos
    hop_length = 512
    rms = librosa.feature.rms(y=y_harmonic, hop_length=hop_length)[0]
    
    if rms_threshold == "auto" or rms_threshold is None:
        # Estimar según el ruido de fondo (percentil 10)
        base_noise = np.percentile(rms, 10)
        rms_threshold = float(np.clip(base_noise * 2.0, 0.008, 0.025))
        log(f"Umbral de puerta de ruido estimado automáticamente: {rms_threshold:.4f}")
    else:
        try:
            rms_threshold = float(rms_threshold)
            log(f"Usando umbral de puerta de ruido manual: {rms_threshold:.4f}")
        except ValueError:
            rms_threshold = 0.015
            log(f"Valor de umbral inválido. Usando por defecto: {rms_threshold:.4f}")
            
    # 3. Detección de pitch pYIN acotada a la tesitura melódica de la bandurria (220 Hz a 1400 Hz)
    log(f"Calculando afinación de notas ({fmin} Hz a {fmax} Hz)...")
    f0, voiced_flag, voiced_probs = librosa.pyin(
        y_harmonic, 
        fmin=fmin, 
        fmax=fmax, 
        sr=sr,
        hop_length=hop_length,
        fill_na=0.0
    )
    
    # Suavizado medfilt para eliminar saltos rápidos
    import scipy.signal
    f0 = scipy.signal.medfilt(f0, kernel_size=5)
    
    times = librosa.frames_to_time(np.arange(len(f0)), sr=sr, hop_length=hop_length)
    notes = []
    current_note = None
    for i in range(len(f0)):
        f = f0[i]
        r = rms[min(i, len(rms)-1)]
        
        # Filtro de silencio por energía RMS
        if r < rms_threshold:
            f = 0.0
            
        if f > 0:
            midi_pitch = librosa.hz_to_midi(f)
            rounded_pitch = int(round(midi_pitch))
            
            if current_note is None:
                current_note = {
                    'pitch': rounded_pitch,
                    'start': times[i],
                    'end': times[i] + hop_length/sr,
                    'pitches': [midi_pitch]
                }
            else:
                pitch_diff = abs(midi_pitch - np.median(current_note['pitches']))
                if pitch_diff <= 1.2:
                    current_note['end'] = times[i] + hop_length/sr
                    current_note['pitches'].append(midi_pitch)
                else:
                    notes.append(current_note)
                    current_note = {
                        'pitch': rounded_pitch,
                        'start': times[i],
                        'end': times[i] + hop_length/sr,
                        'pitches': [midi_pitch]
                    }
        else:
            if current_note is not None:
                notes.append(current_note)
                current_note = None
                
    if current_note is not None:
        notes.append(current_note)

    # Filtrar notas ruidosas ultra cortas (<100ms)
    min_note_duration = 0.10
    filtered_notes = [n for n in notes if (n['end'] - n['start']) >= min_note_duration]
    log(f"Notas iniciales detectadas: {len(filtered_notes)}")
    
    # 1. Unificación de Trémolos de Bandurria
    log("Unificando trémolos de púa de la bandurria...")
    merged_notes = merge_tremolo_notes(filtered_notes, max_gap=0.18, max_pitch_diff=1.0)
    
    # 2. Filtrado de notas espurias/graves de entrada (ruido de manejo pre-interpretación)
    if merged_notes:
        all_pitches = [n['pitch'] for n in merged_notes]
        median_pitch = float(np.median(all_pitches))
        cleaned_notes = [n for n in merged_notes if (median_pitch - n['pitch']) <= 12]
        if len(cleaned_notes) > 0:
            merged_notes = cleaned_notes
            
    log(f"Notas tras unificar trémolo y limpiar ruidos graves: {len(merged_notes)}")
    
    # 3. Cuantización rítmica para MuseScore
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
        
    # 4. Dinámicas e Intensidad RMS por nota
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
    
    # 5. Generación nativa de MusicXML (.musicxml) para MuseScore
    try:
        base_path, _ = os.path.splitext(midi_path)
        musicxml_path = base_path + ".musicxml"
        song_title = os.path.basename(base_path).replace("_", " ").title()
        export_to_musicxml(final_notes, musicxml_path, bpm=bpm, title=song_title)
        log(f"¡Éxito! MusicXML generado para MuseScore en: {musicxml_path}")
    except Exception as e:
        log(f"Aviso al exportar MusicXML: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transcriptor de Melodías de Bandurria a MIDI (MuseScore)")
    parser.add_argument("input", nargs="?", help="Ruta al archivo de audio o vídeo de entrada (mp4, mp3, wav)")
    parser.add_argument("output", nargs="?", help="Ruta de salida para el archivo MIDI (.mid)")
    parser.add_argument("--bpm", type=int, default=120, help="Tempo estimado en BPM para cuantización (por defecto 120, 0 para desactivar)")
    parser.add_argument("--subdivision", type=int, default=16, help="Subdivisión para la rejilla rítmica (16 = semicorcheas, 8 = corcheas)")
    parser.add_argument("--rms-threshold", default="auto", help="Umbral de energía RMS para puerta de ruido (ej: 0.015, o 'auto')")
    parser.add_argument("--gui", action="store_true", help="Abrir la Interfaz Gráfica de Usuario")
    
    args = parser.parse_args()
    
    if args.gui or len(sys.argv) == 1:
        from gui import launch_gui
        launch_gui()
    elif args.input and args.output:
        transcribe_audio_to_midi(args.input, args.output, bpm=args.bpm, subdivision=args.subdivision, rms_threshold=args.rms_threshold)
    else:
        # Valores por defecto en consola
        audio_file = r"G:\Mi unidad\AYo\Tuna\Canciones Tuna\Noche madrileña\Noche madrileña bandurria.mp4"
        output_midi = r"G:\Mi unidad\AYo\Tuna\Canciones Tuna\Noche madrileña\Noche madrileña bandurria.mid"
        print(f"No se proporcionaron argumentos completos. Ejecutando con valores por defecto:")
        print(f"Entrada: {audio_file}")
        print(f"Salida: {output_midi}\n")
        transcribe_audio_to_midi(audio_file, output_midi, bpm=args.bpm, subdivision=args.subdivision, rms_threshold=args.rms_threshold)

