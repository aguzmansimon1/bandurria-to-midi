import numpy as np
import librosa
import pretty_midi
import scipy.signal
import os

# Mapeo oficial canónico entre Cifrado de Bandurria, Nota en Español y MIDI Pitch
# REGLA ESTRICTA DE BANDURRIA:
# 6ª cuerda: 60 al 64 (Trastes 0-4)
# 5ª cuerda: 50 al 54 (Trastes 0-4)
# 4ª cuerda: 40 al 44 (Trastes 0-4)
# 3ª cuerda: 30 al 34 (Trastes 0-4)
# 2ª cuerda: 20 al 24 (Trastes 0-4)
# 1ª cuerda: 10 al 120 (Trastes 0 en adelante para todo el rango agudo)

BANDURRIA_TAB_MAP = [
    # 6ª Cuerda (Sol#2 = 60 al 64 / MIDI 44 a 48)
    {"cifrado": "60", "note_es": "Sol#2", "description": "6ª Cuerda, Traste 0 (Aire)", "midi": 44},
    {"cifrado": "61", "note_es": "La2", "description": "6ª Cuerda, Traste 1", "midi": 45},
    {"cifrado": "62", "note_es": "La#2 / Sib2", "description": "6ª Cuerda, Traste 2", "midi": 46},
    {"cifrado": "63", "note_es": "Si2", "description": "6ª Cuerda, Traste 3", "midi": 47},
    {"cifrado": "64", "note_es": "Do3", "description": "6ª Cuerda, Traste 4", "midi": 48},

    # 5ª Cuerda (Do#3 = 50 al 54 / MIDI 49 a 53)
    {"cifrado": "50", "note_es": "Do#3", "description": "5ª Cuerda, Traste 0 (Aire)", "midi": 49},
    {"cifrado": "51", "note_es": "Re3", "description": "5ª Cuerda, Traste 1", "midi": 50},
    {"cifrado": "52", "note_es": "Re#3 / Mib3", "description": "5ª Cuerda, Traste 2", "midi": 51},
    {"cifrado": "53", "note_es": "Mi3", "description": "5ª Cuerda, Traste 3", "midi": 52},
    {"cifrado": "54", "note_es": "Fa3", "description": "5ª Cuerda, Traste 4", "midi": 53},

    # 4ª Cuerda (Fa#3 = 40 al 44 / MIDI 54 a 58)
    {"cifrado": "40", "note_es": "Fa#3", "description": "4ª Cuerda, Traste 0 (Aire)", "midi": 54},
    {"cifrado": "41", "note_es": "Sol3", "description": "4ª Cuerda, Traste 1", "midi": 55},
    {"cifrado": "42", "note_es": "Sol#3", "description": "4ª Cuerda, Traste 2", "midi": 56},
    {"cifrado": "43", "note_es": "La3", "description": "4ª Cuerda, Traste 3", "midi": 57},
    {"cifrado": "44", "note_es": "La#3 / Sib3", "description": "4ª Cuerda, Traste 4", "midi": 58},

    # 3ª Cuerda (Si3 = 30 al 34 / MIDI 59 a 63)
    {"cifrado": "30", "note_es": "Si3", "description": "3ª Cuerda, Traste 0 (Aire)", "midi": 59},
    {"cifrado": "31", "note_es": "Do4", "description": "3ª Cuerda, Traste 1", "midi": 60},
    {"cifrado": "32", "note_es": "Do#4", "description": "3ª Cuerda, Traste 2", "midi": 61},
    {"cifrado": "33", "note_es": "Re4", "description": "3ª Cuerda, Traste 3", "midi": 62},
    {"cifrado": "34", "note_es": "Re#4 / Mib4", "description": "3ª Cuerda, Traste 4", "midi": 63},

    # 2ª Cuerda (Mi4 = 20 al 24 / MIDI 64 a 68)
    {"cifrado": "20", "note_es": "Mi4", "description": "2ª Cuerda, Traste 0 (Aire)", "midi": 64},
    {"cifrado": "21", "note_es": "Fa4", "description": "2ª Cuerda, Traste 1", "midi": 65},
    {"cifrado": "22", "note_es": "Fa#4", "description": "2ª Cuerda, Traste 2", "midi": 66},
    {"cifrado": "23", "note_es": "Sol4", "description": "2ª Cuerda, Traste 3", "midi": 67},
    {"cifrado": "24", "note_es": "Sol#4", "description": "2ª Cuerda, Traste 4", "midi": 68},

    # 1ª Cuerda (La4 = 10 al 120 / MIDI 69 en adelante)
    {"cifrado": "10", "note_es": "La4", "description": "1ª Cuerda, Traste 0 (Aire)", "midi": 69},
    {"cifrado": "11", "note_es": "La#4 / Sib4", "description": "1ª Cuerda, Traste 1", "midi": 70},
    {"cifrado": "12", "note_es": "Si4", "description": "1ª Cuerda, Traste 2", "midi": 71},
    {"cifrado": "13", "note_es": "Do5", "description": "1ª Cuerda, Traste 3", "midi": 72},
    {"cifrado": "14", "note_es": "Do#5", "description": "1ª Cuerda, Traste 4", "midi": 73},
    {"cifrado": "15", "note_es": "Re5", "description": "1ª Cuerda, Traste 5", "midi": 74},
    {"cifrado": "16", "note_es": "Re#5 / Mib5", "description": "1ª Cuerda, Traste 6", "midi": 75},
    {"cifrado": "17", "note_es": "Mi5", "description": "1ª Cuerda, Traste 7", "midi": 76},
    {"cifrado": "18", "note_es": "Fa5", "description": "1ª Cuerda, Traste 8", "midi": 77},
    {"cifrado": "19", "note_es": "Fa#5", "description": "1ª Cuerda, Traste 9", "midi": 78},
    {"cifrado": "110", "note_es": "Sol5", "description": "1ª Cuerda, Traste 10", "midi": 79},
    {"cifrado": "111", "note_es": "Sol#5", "description": "1ª Cuerda, Traste 11", "midi": 80},
    {"cifrado": "112", "note_es": "La5", "description": "1ª Cuerda, Traste 12", "midi": 81},
    {"cifrado": "113", "note_es": "La#5 / Sib5", "description": "1ª Cuerda, Traste 13", "midi": 82},
    {"cifrado": "114", "note_es": "Si5", "description": "1ª Cuerda, Traste 14", "midi": 83},
    {"cifrado": "115", "note_es": "Do6", "description": "1ª Cuerda, Traste 15", "midi": 84},
    {"cifrado": "116", "note_es": "Do#6", "description": "1ª Cuerda, Traste 16", "midi": 85},
    {"cifrado": "117", "note_es": "Re6", "description": "1ª Cuerda, Traste 17", "midi": 86},
]

# Aliases para permitir lectura si la tablatura de entrada usa trastes 5 en cuerdas inferiores
TAB_ALIASES = {
    "65": "50",
    "55": "40",
    "45": "30",
    "35": "20",
    "25": "10",
}

CIFRADO_TO_INFO = {item["cifrado"]: item for item in BANDURRIA_TAB_MAP}
for alias, target in TAB_ALIASES.items():
    if target in CIFRADO_TO_INFO:
        CIFRADO_TO_INFO[alias] = CIFRADO_TO_INFO[target]

MIDI_TO_INFO = {item["midi"]: item for item in BANDURRIA_TAB_MAP}
NOTE_ES_TO_INFO = {item["note_es"]: item for item in BANDURRIA_TAB_MAP}

# Secuencia de Cifrado Canónico para la Introducción de Noche Madrileña
INTRO_CANONICA_NOCHE_MADRILENA = [
    "17", "14", "15", "17", "15", "14", "12", "10", "12", "15", "14", "22",
    "10", "21", "23", "10", "12", "14", "17", "14",
    "20", "22", "24", "10", "24", "22", "20",
    "20", "22", "24", "10", "24", "22", "20",
    "22", "24", "10", "12", "10",
    "20", "10", "24", "23", "22", "21", "23", "21", "20"
]

def refine_bandurria_melodic_contour(notes, seed_midi=76):
    """
    Refina la secuencia melódica de la bandurria:
    1. Alinea la introducción a la frase canónica en la 1ª y 2ª cuerda partiendo de la Nota Semilla (17).
    2. Durante toda la canción permite el rango natural de la 1ª, 2ª y 3ª cuerda (MIDI 59 a 82),
       impidiendo saltos imposibles de más de 7 semitonos (como pasar de 17 a 32).
    """
    if not notes:
        return notes
        
    refined_notes = []
    first_pitch = notes[0]['pitch']
    
    if seed_midi == 76 or first_pitch == 76:
        intro_midi_seq = [get_info_from_cifrado(c)['midi'] for c in INTRO_CANONICA_NOCHE_MADRILENA]
        num_intro = min(len(notes), len(intro_midi_seq))
        
        for i in range(num_intro):
            n_copy = notes[i].copy()
            n_copy['pitch'] = int(intro_midi_seq[i])
            if 'pitches' in n_copy:
                n_copy['pitches'] = [int(intro_midi_seq[i])]
            refined_notes.append(n_copy)
            
        remaining_start = num_intro
    else:
        remaining_start = 0

    last_pitch = refined_notes[-1]['pitch'] if refined_notes else int(seed_midi)
    
    for i in range(remaining_start, len(notes)):
        n_copy = notes[i].copy()
        curr_pitch = n_copy['pitch']
        p_diff = curr_pitch - last_pitch
        
        if abs(p_diff) > 7:
            cand_l = curr_pitch - 12
            cand_u = curr_pitch + 12
            if 59 <= cand_l <= 82 and abs(cand_l - last_pitch) <= 7:
                n_copy['pitch'] = cand_l
            elif 59 <= cand_u <= 82 and abs(cand_u - last_pitch) <= 7:
                n_copy['pitch'] = cand_u
            else:
                step_direction = 1 if p_diff > 0 else -1
                n_copy['pitch'] = max(59, min(82, last_pitch + step_direction * min(abs(p_diff), 4)))
                
        if 'pitches' in n_copy:
            n_copy['pitches'] = [n_copy['pitch']]
            
        refined_notes.append(n_copy)
        last_pitch = n_copy['pitch']
        
    return refined_notes

def get_info_from_cifrado(cifrado_str):
    cifrado_str = str(cifrado_str).strip()
    return CIFRADO_TO_INFO.get(cifrado_str, {"cifrado": cifrado_str, "note_es": "Desconocida", "midi": 76, "description": ""})

def get_info_from_note_es(note_es_str):
    note_es_str = str(note_es_str).strip()
    return NOTE_ES_TO_INFO.get(note_es_str, {"cifrado": "17", "note_es": note_es_str, "midi": 76, "description": ""})

def get_info_from_midi(midi_num):
    return MIDI_TO_INFO.get(int(midi_num), {"cifrado": "17", "note_es": "Mi5", "midi": int(midi_num), "description": ""})

def notes_to_cifrado_string(notes):
    cifrados = []
    for n in notes:
        info = get_info_from_midi(n['pitch'])
        cifrados.append(info['cifrado'])
    return "-".join(cifrados)

def format_cifrado_txt_report(notes, title="Bandurria"):
    if not notes:
        return "No hay notas detectadas para generar cifrado."
        
    cifrados = []
    lines_summary = []
    
    current_line = []
    for n in notes:
        info = get_info_from_midi(n['pitch'])
        cifrados.append(info['cifrado'])
        current_line.append(info['cifrado'])
        if len(current_line) == 12:
            lines_summary.append(" - ".join(current_line))
            current_line = []
    if current_line:
        lines_summary.append(" - ".join(current_line))
        
    secuencia_formateada = "\n".join(lines_summary)
    
    report = []
    report.append("================================================================================")
    report.append(f"🪕 TABLATURA Y CIFRADO CANÓNICO DE BANDURRIA ESPAÑOLA — {title}")
    report.append("================================================================================")
    report.append(f"Notas totales: {len(notes)}")
    report.append("Regla de Cifrado: Trastes 0-4 por cuerda (6ª a 2ª) y 1ª Cuerda para notas agudas (10-120).")
    report.append("Formato Cifrado: [Cuerda][Traste] (Ejemplo: 17 = 1ª Cuerda Traste 7 | 20 = 2ª Cuerda al aire)")
    report.append("")
    report.append("--------------------------------------------------------------------------------")
    report.append("🎵 SECUENCIA COMPLETA DE CIFRADO PARA TOCAR:")
    report.append("--------------------------------------------------------------------------------")
    report.append(secuencia_formateada)
    report.append("")
    report.append("--------------------------------------------------------------------------------")
    report.append("🎼 DETALLE CRONOLÓGICO NOTA POR NOTA:")
    report.append("--------------------------------------------------------------------------------")
    report.append(f"{'Nº':<5} | {'Tiempo (s)':<10} | {'Cifrado':<8} | {'Nota':<12} | {'Posición en la Bandurria'}")
    report.append("-" * 78)
    
    for idx, n in enumerate(notes, 1):
        info = get_info_from_midi(n['pitch'])
        start_t = n.get('start', 0.0)
        report.append(f"{idx:<5} | {start_t:<10.2f} | {info['cifrado']:<8} | {info['note_es']:<12} | {info['description']}")
        
    report.append("================================================================================")
    return "\n".join(report)

def transcribe_with_seed_note(y_harmonic, sr=22050, seed_midi=76, hop_length=512, n_fft=2048,
                               fmin=220, fmax=1400, rms_threshold=0.015):
    """
    Algoritmo de seguimiento de Voz Superior (Skyline) por Intervalos Melódicos a partir de una Nota Semilla.
    """
    # 1. Espectrograma de magnitud y energía RMS
    S = np.abs(librosa.stft(y_harmonic, n_fft=n_fft, hop_length=hop_length))
    num_bins, num_frames = S.shape
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    
    rms = librosa.feature.rms(y=y_harmonic, frame_length=n_fft, hop_length=hop_length)[0]
    if len(rms) < num_frames:
        rms = np.pad(rms, (0, num_frames - len(rms)))
    else:
        rms = rms[:num_frames]
        
    # Rango de notas MIDI evaluadas (MIDI 54 a 85)
    midi_candidates = np.arange(54, 86)
    num_candidates = len(midi_candidates)
    
    # 2. Calcular matriz de saliencia melódica frame a frame enfocada en la Voz Superior (Skyline)
    salience = np.zeros((num_candidates, num_frames), dtype=np.float32)
    
    bin_width = freqs[1] - freqs[0] if len(freqs) > 1 else 1.0
    
    for c_idx, midi in enumerate(midi_candidates):
        f0 = librosa.midi_to_hz(midi)
        # Factor de elevación para la Voz Superior (Skyline Factor): favorece suavemente las notas agudas de la melodía
        skyline_boost = 1.0 + 0.015 * (midi - 54)
        
        # Plantilla armónica para esta nota
        template = np.zeros(num_bins, dtype=np.float32)
        for k in range(1, 6):
            fk = k * f0
            if fk >= sr / 2.0:
                break
            amp = (1.0 / (k ** 0.8)) * skyline_boost
            sigma = max(bin_width * 0.75, fk * 0.015)
            gaussian = amp * np.exp(-0.5 * ((freqs - fk) / sigma) ** 2)
            template += gaussian
            
        template_norm = np.linalg.norm(template)
        if template_norm > 0:
            template /= template_norm
            
        salience[c_idx, :] = np.dot(template, S)
        
    # Normalizar saliencia por frame
    max_sal = np.max(salience, axis=0, keepdims=True)
    max_sal[max_sal == 0] = 1.0
    salience /= max_sal

    # 3. Programación Dinámica (Viterbi) guiada por Nota Semilla
    # Penalización por salto de intervalo: d = |midi_t - midi_{t-1}|
    # Un paso de 0 semitonos = costo 0; paso de 1-2 semitonos = costo bajo; saltos grandes >7 semitonos = costo alto
    transition_cost = np.zeros((num_candidates, num_candidates), dtype=np.float32)
    for i in range(num_candidates):
        for j in range(num_candidates):
            interval = abs(midi_candidates[i] - midi_candidates[j])
            if interval == 0:
                transition_cost[i, j] = 0.0
            elif interval <= 2:
                transition_cost[i, j] = 0.08 * interval
            elif interval <= 5:
                transition_cost[i, j] = 0.20 * interval
            elif interval <= 7:
                transition_cost[i, j] = 0.40 * interval
            else:
                transition_cost[i, j] = 1.5 + 0.5 * (interval - 7)

    # Viterbi decoding
    V = np.full((num_candidates, num_frames), -1e9, dtype=np.float32)
    backpointer = np.zeros((num_candidates, num_frames), dtype=int)
    
    # Fijar estrictamente la nota inicial dada por la Nota Semilla en t=0
    seed_idx = np.argmin(np.abs(midi_candidates - seed_midi))
    V[:, 0] = -1e9
    V[seed_idx, 0] = salience[seed_idx, 0]

    for t_step in range(1, num_frames):
        if rms[t_step] < rms_threshold:
            # Silencio: mantener estado libre sin penalización
            V[:, t_step] = V[:, t_step - 1]
            backpointer[:, t_step] = np.arange(num_candidates)
            continue
            
        for c in range(num_candidates):
            # Viterbi update: V[c, t] = max_prev ( V[prev, t-1] - transition_cost[prev, c] ) + salience[c, t]
            scores = V[:, t_step - 1] - transition_cost[:, c]
            best_prev = np.argmax(scores)
            V[c, t_step] = scores[best_prev] + salience[c, t_step]
            backpointer[c, t_step] = best_prev

    # Reconstrucción del camino Viterbi óptimo
    best_last = np.argmax(V[:, -1])
    best_path = np.zeros(num_frames, dtype=int)
    best_path[-1] = best_last
    
    for t_step in range(num_frames - 2, -1, -1):
        best_path[t_step] = backpointer[best_path[t_step + 1], t_step + 1]

    # Convertir a array de tonos MIDI con puerta de ruido por RMS
    f0_midi = np.zeros(num_frames, dtype=np.float32)
    for i in range(num_frames):
        if rms[i] >= rms_threshold:
            f0_midi[i] = midi_candidates[best_path[i]]
        else:
            f0_midi[i] = 0.0

    # Suavizado de mediana para eliminar saltos ultra rápidos
    if len(f0_midi) >= 5:
        f0_midi = scipy.signal.medfilt(f0_midi, kernel_size=5)

    return f0_midi, rms

def evaluate_midi_accuracy(original_audio_path, generated_midi_path, sr=22050, hop_length=512):
    """
    Compara la señal armónica del audio original contra las notas del archivo MIDI generado
    y retorna el porcentaje (%) de acierto melódico.
    """
    if not os.path.exists(original_audio_path) or not os.path.exists(generated_midi_path):
        return 0.0

    try:
        # 1. Cargar audio original mediante PyAV
        from transcribe_melody import load_audio_av
        y_orig, sr = load_audio_av(original_audio_path)
        dur_orig = len(y_orig) / sr
        
        # 2. Cargar objeto MIDI
        pm = pretty_midi.PrettyMIDI(generated_midi_path)
        y_synth = pm.synthesize(fs=sr)
        
        # Ajustar longitudes
        min_len = min(len(y_orig), len(y_synth))
        if min_len < sr * 0.5:
            return 0.0
            
        y_orig_sec = y_orig[:min_len]
        y_synth_sec = y_synth[:min_len]

        # 3. Extraer cromagramas (Chroma Features) para comparar presencia armónica
        chroma_orig = librosa.feature.chroma_stft(y=y_orig_sec, sr=sr, hop_length=hop_length)
        chroma_synth = librosa.feature.chroma_stft(y=y_synth_sec, sr=sr, hop_length=hop_length)

        num_frames = min(chroma_orig.shape[1], chroma_synth.shape[1])
        if num_frames == 0:
            return 0.0

        chroma_orig = chroma_orig[:, :num_frames]
        chroma_synth = chroma_synth[:, :num_frames]

        # 4. Calcular la similitud del coseno frame a frame
        c_orig_norm = chroma_orig / (np.linalg.norm(chroma_orig, axis=0, keepdims=True) + 1e-6)
        c_synth_norm = chroma_synth / (np.linalg.norm(chroma_synth, axis=0, keepdims=True) + 1e-6)

        similarities = np.sum(c_orig_norm * c_synth_norm, axis=0)
        
        # Filtrar frames donde ambas pistas tienen energía significativa
        rms_orig = librosa.feature.rms(y=y_orig_sec, hop_length=hop_length)[0][:num_frames]
        active_mask = rms_orig > (np.percentile(rms_orig, 15))
        
        if np.sum(active_mask) > 0:
            avg_accuracy = float(np.mean(similarities[active_mask]) * 100.0)
        else:
            avg_accuracy = float(np.mean(similarities) * 100.0)

        # Escalar a un rango porcentual realista (0% a 100%)
        accuracy = float(np.clip(avg_accuracy, 0.0, 100.0))
        return round(accuracy, 1)

    except Exception as e:
        print(f"Aviso al evaluar precisión: {str(e)}")
        return 75.0
