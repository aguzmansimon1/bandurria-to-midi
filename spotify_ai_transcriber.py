import os
import numpy as np
import pretty_midi
import scipy.signal
if not hasattr(scipy.signal, 'gaussian'):
    import scipy.signal.windows
    scipy.signal.gaussian = scipy.signal.windows.gaussian

from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH
import seed_tracking
from transcribe_melody import merge_tremolo_notes, quantize_notes, calculate_note_velocities, export_to_musicxml, load_audio_av

def clean_to_monophonic_melody(notes):
    """
    Convierte una lista de notas potencialmente polifónicas en una línea melódica
    estrictamente monofónica (una sola nota sonando en cada momento), eliminando
    armónicos fantasma y notas discordantes superpuestas.
    """
    if not notes:
        return []
        
    sorted_notes = sorted(notes, key=lambda x: (x['start'], -x.get('velocity', 80)))
    mono_notes = []
    
    for current in sorted_notes:
        if not mono_notes:
            mono_notes.append(current.copy())
            continue
            
        prev = mono_notes[-1]
        
        # Si la nota actual empieza después de que termine la anterior, no hay solapamiento
        if current['start'] >= prev['end'] - 0.03:
            mono_notes.append(current.copy())
        else:
            # Hay solapamiento simultáneo (polifonía no deseada)
            if current['pitch'] == prev['pitch']:
                prev['end'] = max(prev['end'], current['end'])
            else:
                dur_current = current['end'] - current['start']
                dur_prev = prev['end'] - prev['start']
                
                # Ignorar notas discordantes ultracortas (<80ms) que son chasquidos/armónicos
                if dur_current < 0.08 and dur_prev >= 0.12:
                    continue
                elif dur_prev < 0.08:
                    mono_notes[-1] = current.copy()
                else:
                    prev['end'] = current['start']
                    if prev['end'] > prev['start'] + 0.04:
                        mono_notes.append(current.copy())
                    else:
                        mono_notes[-1] = current.copy()
                        
    return mono_notes

def transcribe_with_spotify_ai(audio_path, midi_path, bpm=120, subdivision=16, 
                               fmin=220, fmax=1400, rms_threshold="auto", log_callback=None):
    """
    Transcribe audio de bandurria utilizando la Red Neuronal de Inteligencia Artificial 
    Basic Pitch desarrollada por el laboratorio de IA de Spotify.
    """
    def log(msg):
        try:
            print(msg)
        except Exception:
            print(msg.encode('ascii', errors='replace').decode('ascii'))
        if log_callback:
            log_callback(msg)

    log("🤖 Cargando modelo de Red Neuronal de Spotify (Basic Pitch)...")
    
    # Decodificar audio/vídeo con PyAV para garantizar compatibilidad total con .mp4, .m4a, .mp3, .wav
    import scipy.io.wavfile as wavfile

    y, sr = load_audio_av(audio_path)
    temp_dir = os.path.dirname(os.path.abspath(midi_path))
    os.makedirs(temp_dir, exist_ok=True)
    temp_wav = os.path.join(temp_dir, "_temp_basic_pitch_input.wav")
    
    # Escalar a int16 para wavfile
    audio_int16 = (y * 32767).astype(np.int16)
    wavfile.write(temp_wav, sr, audio_int16)

    # Usar el modelo ONNX nmp.onnx para ejecución ultrarrápida sin dependencias pesadas de TF
    onnx_model_path = os.path.join(os.path.dirname(ICASSP_2022_MODEL_PATH), "nmp.onnx")
    model_to_use = onnx_model_path if os.path.exists(onnx_model_path) else ICASSP_2022_MODEL_PATH

    try:
        # 1. Predicción mediante la Red Neuronal de Spotify
        model_output, midi_data, note_events = predict(
            temp_wav,
            model_or_model_path=model_to_use,
            minimum_frequency=float(fmin),
            maximum_frequency=float(fmax)
        )
    finally:
        if os.path.exists(temp_wav):
            try:
                os.remove(temp_wav)
            except Exception:
                pass
    
    log("🧠 Predicción neuronal completada. Procesando notas detectadas...")
    
    # 2. Extraer notas predichas por la red neuronal acotando a la tesitura real de melodía (MIDI 54 a 81)
    raw_notes = []
    for inst in midi_data.instruments:
        for n in inst.notes:
            # Rango melódico estricto de Bandurria: Fa#3 (MIDI 54 / ~185Hz) a La5 (MIDI 81 / ~880Hz)
            if 54 <= n.pitch <= 81:
                raw_notes.append({
                    'pitch': int(n.pitch),
                    'start': float(n.start),
                    'end': float(n.end),
                    'pitches': [float(n.pitch)],
                    'velocity': int(n.velocity)
                })
                
    # Ordenar por tiempo de inicio
    raw_notes = sorted(raw_notes, key=lambda x: (x['start'], -x['velocity']))
    log(f"Notas detectadas por la IA en tesitura de melodía: {len(raw_notes)}")
    
    # 3. Monofonización Estricta (Línea Melódica Única) para eliminar notas discordantes simultáneas ("pam-pam-pam")
    log("Aislando línea melódica monofónica pura (eliminando armónicos discordantes superpuestos)...")
    mono_notes = clean_to_monophonic_melody(raw_notes)
    log(f"Notas tras monofonización melódica: {len(mono_notes)}")

    # 4. Unificación de Trémolos de Bandurria
    log("Unificando trémolos de púa de la bandurria...")
    merged_notes = merge_tremolo_notes(mono_notes, max_gap=0.18, max_pitch_diff=1.0)
    log(f"Notas tras unificar trémolos: {len(merged_notes)}")
    
    # 5. Cuantización Rítmica
    if bpm == "auto" or bpm is None or bpm <= 0:
        log("Estimando tempo (BPM) automáticamente...")
        try:
            import librosa
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            bpm = int(round(float(np.atleast_1d(tempo)[0])))
            log(f"Tempo detectado automáticamente: {bpm} BPM")
        except Exception:
            bpm = 120
            log(f"Usando tempo por defecto: {bpm} BPM")
            
    log(f"Cuantizando ritmo a {bpm} BPM (Subdivisión: 1/{subdivision})...")
    final_notes = quantize_notes(merged_notes, bpm=bpm, subdivision=subdivision)
    
    # 6. Escribir MIDI con instrumento Piano Acústico
    pm = pretty_midi.PrettyMIDI(initial_tempo=float(bpm))
    piano_program = pretty_midi.instrument_name_to_program('Acoustic Grand Piano')
    piano_inst = pretty_midi.Instrument(program=piano_program, name="Melodia Piano (IA Spotify)")
    
    for n in final_notes:
        note_obj = pretty_midi.Note(
            velocity=n.get('velocity', 85),
            pitch=n['pitch'],
            start=n['start'],
            end=n['end']
        )
        piano_inst.notes.append(note_obj)
        
    pm.instruments.append(piano_inst)
    
    # Asegurar creación de directorio y guardar archivo MIDI
    os.makedirs(os.path.dirname(os.path.abspath(midi_path)), exist_ok=True)
    pm.write(midi_path)
    log(f"¡Éxito! MIDI generado por IA guardado en: {midi_path}")
    
    # 7. Generación MusicXML para MuseScore 4
    try:
        base_path, _ = os.path.splitext(midi_path)
        musicxml_path = base_path + ".musicxml"
        song_title = os.path.basename(base_path).replace("_", " ").title()
        export_to_musicxml(final_notes, musicxml_path, bpm=bpm, title=song_title)
        log(f"¡Éxito! MusicXML para MuseScore generado en: {musicxml_path}")
    except Exception as e:
        log(f"Aviso al exportar MusicXML: {str(e)}")

    # 8. Evaluación de coincidencia
    log("📊 Calculando porcentaje de acierto melódico...")
    accuracy_pct = seed_tracking.evaluate_midi_accuracy(audio_path, midi_path)
    log(f"🎯 ¡Evaluación Completada! Porcentaje de Acierto Melódico: {accuracy_pct}%")
    
    return accuracy_pct
