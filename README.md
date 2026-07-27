# 🪕 Transcriptor de Melodías de Bandurria a MIDI y MusicXML (MuseScore)

<p align="center">
  <img src="logo.png" alt="Bandurria to MIDI Logo" width="220">
</p>

Aplicación de escritorio en Python para transcribir grabaciones de audio, vídeo y tablaturas de **Bandurria Española (6 cuerdas dobles / 12 cuerdas en 6 pares)** a archivos **MIDI (.mid)** y **MusicXML (.musicxml)** formateados para **MuseScore 4** en sonido de **Piano Acústico**.

---

## 📌 Estado Actual del Proyecto y Sincronización

| Componente | Estado | Descripción |
| :--- | :---: | :--- |
| **Interfaz Gráfica (GUI)** | **COMPLETO** | Interfaz limpia en tema claro (`gui.py`) con memoria persistente (`config.json`), icono oficial `logo.ico` y numeración anti-sobrescritura `(1).mid`. |
| **Transcriptor Audio/Vídeo** | **COMPLETO** | Decodificación PyAV, filtrado armónico HPSS, acotado frecuencial (220-1400 Hz), unificador de trémolos de púa y estimación automática de tempo. |
| **Filtro de Ruidos Graves** | **COMPLETO** | Filtro de desviación tonal (Melodic Outlier Filter) que elimina ruidos de manejo pre-interpretación (roces/púa a t=0s). |
| **Exportación MusicXML** | **COMPLETO** | Generación nativa de `.musicxml` con Clave de Sol (`<clef><sign>G</sign><line>2</line></clef>`), compás de 4/4 y figuras rítmicas. |
| **Control de Dinámicas (RMS)** | **COMPLETO** | Análisis de volumen por nota (Velocity 45-118), matices (*p*, *mp*, *mf*, *f*) y acentos de púa (`<accent/>`). |
| **Convertidor de Tablatura** | **COMPLETO** | Pestaña `📝 Desde Tablatura (Texto)` para convertir secuencias de cifras (`17-14-15...`) en MIDI y MusicXML. |
| **Integración MuseScore 4** | **COMPLETO** | Botón `🎼 Abrir en MuseScore` que busca automáticamente MuseScore 4 (`C:\Program Files\MuseScore 4\bin\MuseScore4.exe`) y abre la partitura `.musicxml`. |

---

## ⚙️ Especificaciones Técnicas y Tesitura de Bandurria

- **Instrumento objetivo**: Bandurria Española (6 pares de cuerdas dobles):
  - 1ª cuerda = La4 (A4 = 440 Hz = MIDI 69)
  - 2ª cuerda = Mi4 (E4 = 329.6 Hz = MIDI 64)
  - 3ª cuerda = Si3 (B3 = 246.9 Hz = MIDI 59)
  - 4ª cuerda = Fa#3 (F#3 = 185.0 Hz = MIDI 54)
  - 5ª cuerda = Do#3 (C#3 = 138.6 Hz = MIDI 49)
  - 6ª cuerda = Sol#3 (G#3 = 207.7 Hz = MIDI 56)
- **Timbre MIDI**: **Piano Acústico** (`Acoustic Grand Piano`, General MIDI Program 0) por requerimiento del usuario para lograr máxima claridad en notación y audición.
- **Rango de Frecuencia del Transcriptor**: `220 Hz` (La3) a `1400 Hz` (Fa6) para cubrir el registro melódico solista ignorando ruidos de baja frecuencia.

---

## 📂 Archivos Principales del Código

- **`gui.py`**: Código fuente de la interfaz gráfica de usuario en Tkinter.
- **`transcribe_melody.py`**: Algoritmo principal de transcripción de audio/vídeo (HPSS, PyIN, unificación de trémolos, cuantización rítmica, dinámicas RMS y exportador nativo MusicXML).
- **`convert_tab_to_midi.py`**: Convertidor de notación de tablatura (texto) a MIDI y MusicXML.
- **`Abrir_Transcriptor.bat`**: Script ejecutable directo para abrir la interfaz en el escritorio de Windows.
- **`config.json`**: Archivo local de persistencia que almacena automáticamente la ruta del último archivo cargado y del MIDI de salida.
- **`logo.png` / `logo.ico`**: Logotipo e icono oficial basados en la anatomía real de la bandurria de 12 clavijas del usuario.

---

## 💻 Instalación y Sincronización en un Nuevo Ordenador

Si clonas este repositorio en otro equipo, sigue estos pasos:

1. **Requisitos de Sistema**:
   - Windows 10/11
   - Python 3.10 o superior (ej: Python 3.13)
   - MuseScore 4 instalado en `C:\Program Files\MuseScore 4\bin\MuseScore4.exe` (opcional para visualización)

2. **Crear entorno virtual e instalar dependencias**:
   ```powershell
   # Clonar repositorio
   git clone https://github.com/aguzmansimon1/bandurria-to-midi.git
   cd bandurria-to-midi

   # Crear entorno virtual .venv
   python -m venv .venv
   .\.venv\Scripts\activate

   # Instalar paquetes requeridos
   pip install librosa pretty_midi pyav scipy pillow
   ```

3. **Ejecutar la Aplicación**:
   - Haciendo doble clic en **`Abrir_Transcriptor.bat`**.
   - O desde PowerShell:
     ```powershell
     .\.venv\Scripts\python.exe gui.py
     ```

---

## 🗺️ Hoja de Ruta / Próximos Pasos (Roadmap)

Al continuar el trabajo en el nuevo equipo, el plan acordado es:

- [ ] **Paso 1 (Próximo)**: Probar la transcripción con más grabaciones solistas de la Tuna (*Noche Madrileña*, *Las Palmeras*, *Fonseca*, etc.) y verificar la fidelidad de las partituras `.musicxml` en MuseScore 4.
- [ ] **Paso 4 (Futuro)**: Extender la herramienta para detectar e identificar acompañamientos de **Laúd** y **Guitarra** una vez que el núcleo de Bandurria esté afinado al 100%.

---

*Repositorio oficial en GitHub: [github.com/aguzmansimon1/bandurria-to-midi](https://github.com/aguzmansimon1/bandurria-to-midi)*

