import numpy as np
import librosa
import scipy.signal

def generate_bandurria_harmonic_templates(sr=22050, n_fft=2048, midi_min=54, midi_max=90, num_harmonics=8, alpha=0.85):
    """
    Genera una matriz de plantillas espectrales teóricas para cada nota MIDI en la tesitura de la bandurria.
    
    Cada plantilla representa la distribución ideal de energía armónica (f0, 2f0, 3f0...)
    esperada para una nota tocada en la bandurria.
    """
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    num_bins = len(freqs)
    num_notes = midi_max - midi_min + 1
    
    templates = np.zeros((num_notes, num_bins), dtype=np.float32)
    midi_notes = np.arange(midi_min, midi_max + 1)
    
    bin_width = freqs[1] - freqs[0] if len(freqs) > 1 else 1.0
    
    for idx, midi in enumerate(midi_notes):
        f0 = librosa.midi_to_hz(midi)
        template = np.zeros(num_bins, dtype=np.float32)
        
        for k in range(1, num_harmonics + 1):
            fk = k * f0
            if fk >= sr / 2.0:
                break
                
            # Amplitud del armónico k (decaimiento característico de cuerdas de metal)
            amp = 1.0 / (k ** alpha)
            
            # Repartir energía con una campana gaussiana en torno a la frecuencia exacta fk
            # para dar tolerancia a pequeñas desviaciones de afinación
            sigma = max(bin_width * 0.75, fk * 0.015) # ~1.5% de tolerancia en Hz
            gaussian = amp * np.exp(-0.5 * ((freqs - fk) / sigma) ** 2)
            template += gaussian
            
        # Normalizar la plantilla a norma L2 unitaria
        norm = np.linalg.norm(template)
        if norm > 0:
            template /= norm
            
        templates[idx] = template
        
    return midi_notes, templates

def analyze_audio_spectral_matching(y_harmonic, sr=22050, hop_length=512, n_fft=2048, 
                                    fmin=220, fmax=1400, rms_threshold=0.015):
    """
    Analiza una señal de audio aislada mediante cotejo espectral (Análisis por Síntesis).
    
    Retorna arrays con la estimación de nota MIDI frame a frame y su nivel de confianza (similitud).
    """
    # 1. Espectrograma de Magnitud STFT
    S = np.abs(librosa.stft(y_harmonic, n_fft=n_fft, hop_length=hop_length))
    num_bins, num_frames = S.shape
    
    # 2. RMS por frame
    rms = librosa.feature.rms(y=y_harmonic, frame_length=n_fft, hop_length=hop_length)[0]
    if len(rms) < num_frames:
        rms = np.pad(rms, (0, num_frames - len(rms)))
    elif len(rms) > num_frames:
        rms = rms[:num_frames]
        
    # 3. Generar plantillas armónicas para el rango de la bandurria
    midi_min = int(round(librosa.hz_to_midi(fmin)))
    midi_max = int(round(librosa.hz_to_midi(fmax)))
    midi_notes, templates = generate_bandurria_harmonic_templates(
        sr=sr, n_fft=n_fft, midi_min=midi_min, midi_max=midi_max
    )
    
    # 4. Normalizar cada frame del espectrograma a norma L2 unitaria
    S_norm = S.copy()
    norms = np.linalg.norm(S_norm, axis=0, keepdims=True)
    norms[norms == 0] = 1.0
    S_norm /= norms
    
    # 5. Producto matricial: Similitud del coseno entre cada frame y cada plantilla de nota
    # Coincidencia: (num_notes, num_frames)
    matching_matrix = np.dot(templates, S_norm)
    
    # 6. Seleccionar la nota MIDI de máxima similitud frame a frame
    best_template_idx = np.argmax(matching_matrix, axis=0)
    best_similarity = np.max(matching_matrix, axis=0)
    
    # Estimación de notas MIDI por frame
    f0_midi = np.zeros(num_frames, dtype=np.float32)
    
    for i in range(num_frames):
        # Puerta de silencio por RMS o baja similitud armónica
        if rms[i] >= rms_threshold and best_similarity[i] >= 0.25:
            f0_midi[i] = midi_notes[best_template_idx[i]]
        else:
            f0_midi[i] = 0.0
            
    # Suavizado de filtrado mediano para eliminar micro-conmutaciones ruidosas
    if len(f0_midi) >= 5:
        f0_midi = scipy.signal.medfilt(f0_midi, kernel_size=5)
        
    return f0_midi, best_similarity, rms
