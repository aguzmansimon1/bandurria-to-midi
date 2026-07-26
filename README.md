# Transcriptor de Melodías de Bandurria a MIDI (MuseScore)

Este proyecto extrae automáticamente la melodía de archivos de audio y vídeo de **bandurria** (u otros instrumentos de púa solistas) y genera un archivo MIDI optimizado para ser importado en programas de notación como **MuseScore**.

---

## 🎯 Características Principales para Bandurria

1. **Unificación de Trémolos de Púa**: El algoritmo detecta las pulsaciones rápidas consecutivas características del trémolo de la bandurria y las convierte en una **nota musical continua y sostenida**, evitando notas cortas fragmentadas en la partitura.
2. **Cuantización Rítmica para MuseScore**: Ajusta los tiempos de inicio y fin de las notas a una rejilla musical limpia (semicorcheas/corcheas en un BPM determinado) para evitar garabatos rítmicos al abrir el MIDI en MuseScore.
3. **Dinámicas de Amplitud (Velocity)**: Calcula la intensidad sonora real de cada nota para reflejar los acentos de la ejecución en la bandurria.
4. **Instrumento MIDI Bandurria**: Asigna el timbre de *Mandolina/Cuerda pulsada* (GM Program 105) en la pista MIDI.
5. **Rango de Frecuencias de Bandurria**: Filtro pYIN configurado entre `150 Hz` (Sol3) y `1800 Hz` (La6).

---

## 🚀 Cómo Usar el Transcriptor

### Opción 1: Interfaz Gráfica de Usuario (GUI - Recomendada)
Puedes abrir la ventana interactiva haciendo doble clic o ejecutando:
```powershell
.\.venv\Scripts\python.exe gui.py
```
o simplemente:
```powershell
.\.venv\Scripts\python.exe transcribe_melody.py
```
#### Ventajas de la Interfaz Gráfica:
- **Botón Examinar**: Selecciona cualquier archivo de vídeo o audio (`.mp4`, `.mp3`, `.wav`) sin necesidad de escribir la ruta a mano.
- **Ajustes sencillos**: Define el tempo (BPM) y la subdivisión rítmica con selectores visuales.
- **Consola de Progreso integrada**: Observa en tiempo real los pasos de la decodificación, agrupamiento de trémolo y generación del MIDI.

---

### Opción 2: Ejecución por Línea de Comandos (CLI)
```powershell
.\.venv\Scripts\python.exe transcribe_melody.py "Ruta\Al\Video_o_Audio.mp4" "Ruta\De\Salida.mid" --bpm 120 --subdivision 16
```

---

## 📂 Archivos del Proyecto
* [transcribe_melody.py](file:///c:/Users/Antonio/Documents/Desarrollo/Partituras/transcribe_melody.py): Código fuente del transcriptor con algoritmo de trémolo y cuantización.
* [implementation_plan.md](file:///C:/Users/Antonio/.gemini/antigravity-ide/brain/4ea02090-f127-4a7e-84b5-2efebbcc7288/implementation_plan.md): Plan de desarrollo y arquitectura.

