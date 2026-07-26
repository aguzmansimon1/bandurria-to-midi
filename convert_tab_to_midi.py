import os
import pretty_midi

# Mapeo oficial de Tablatura de Bandurria a Notas MIDI
# Formato de tab: [Cuerda][Traste]
# 1ª cuerda = La4 (MIDI 69)
# 2ª cuerda = Mi4 (MIDI 64)
# 3ª cuerda = Si3 (MIDI 59)
# 4ª cuerda = Fa#3 (MIDI 54)
# 5ª cuerda = Do#3 (MIDI 49)
# 6ª cuerda = Sol#2 (MIDI 44)

TAB_TO_MIDI = {
    # 1ª Cuerda (La4 / A4)
    '10': 69, '11': 70, '12': 71, '13': 72, '14': 73, '15': 74, '16': 75, '17': 76, '18': 77, '19': 78,
    # 2ª Cuerda (Mi4 / E4)
    '20': 64, '21': 65, '22': 66, '23': 67, '24': 68, '25': 69,
    # 3ª Cuerda (Si3 / B3)
    '30': 59, '31': 60, '32': 61, '33': 62, '34': 63, '35': 64,
    # 4ª Cuerda (Fa#3 / F#3)
    '40': 54, '41': 55, '42': 56, '43': 57, '44': 58, '45': 59,
}

def parse_tab_string(tab_text):
    """
    Parsea una cadena de texto de tablatura (ej: '17-14-15-17-15...') 
    y devuelve la lista de tonos MIDI.
    """
    pitches = []
    # Limpiar saltos de línea y separar por guiones o espacios
    tokens = tab_text.replace('\n', '-').replace(' ', '-').split('-')
    for token in tokens:
        token = token.strip()
        if not token:
            continue
        if token in TAB_TO_MIDI:
            pitches.append(TAB_TO_MIDI[token])
    return pitches

def create_midi_from_tab(tab_text, output_midi_path, bpm=120, note_duration=0.4, silence=0.05):
    pitches = parse_tab_string(tab_text)
    pm = pretty_midi.PrettyMIDI(initial_tempo=bpm)
    
    # Usar Piano Acústico (Program 0)
    piano_program = pretty_midi.instrument_name_to_program('Acoustic Grand Piano')
    piano_inst = pretty_midi.Instrument(program=piano_program, name="Bandurria Tab (Piano)")
    
    current_time = 0.0
    step = note_duration + silence
    
    for p in pitches:
        note = pretty_midi.Note(
            velocity=90,
            pitch=p,
            start=current_time,
            end=current_time + note_duration
        )
        piano_inst.notes.append(note)
        current_time += step
        
    pm.instruments.append(piano_inst)
    pm.write(output_midi_path)
    print(f"MIDI desde tablatura generado con éxito: {output_midi_path} ({len(pitches)} notas)")
    return output_midi_path

if __name__ == "__main__":
    tab_noche_madrilena = """
    17-14-15-17-15-14-12-10-12-15-14-22
    10-21-23-10-12-14-17-14
    20-22-24-10-24-22-20
    20-22-24-10-24-22-20
    22-24-10-12-10
    20-10-24-23-22-21-23-21-20
    10-24-23-24-10-17-14-10-20-17-13
    10-24-23-22-21-21-21-21-23-10
    21-20
    """
    out_dir = r"G:\Mi unidad\AYo\Tuna\Canciones Tuna\Noche madrileña"
    out_file = os.path.join(out_dir, "Noche_madrileña_Tablatura_Piano.mid")
    create_midi_from_tab(tab_noche_madrilena, out_file)
