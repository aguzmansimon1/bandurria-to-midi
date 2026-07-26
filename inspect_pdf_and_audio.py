import fitz
import os
import av
import librosa
import numpy as np

# 1. Renderizar la página del PDF
pdf_path = r'G:\Mi unidad\AYo\Tuna\Canciones Tuna\Las palmeras\las_palmeras_baritono_y_bandurria_1.pdf'
doc = fitz.open(pdf_path)
page = doc[0]
pix = page.get_pixmap(dpi=200)
out_png = r'c:\Users\Antonio\Documents\Desarrollo\Partituras\pdf_page_1.png'
pix.save(out_png)
print(f"Página PDF renderizada en: {out_png}")

# Extraer texto del PDF si existe
text = page.get_text()
with open(r'c:\Users\Antonio\Documents\Desarrollo\Partituras\pdf_text.txt', 'w', encoding='utf-8') as f:
    f.write(text if text else "[Sin texto legible - Partitura de imagen/vector]")

# 2. Analizar el audio de la bandurria grabada por el usuario
audio_path = r'G:\Mi unidad\AYo\Tuna\Canciones Tuna\Las palmeras\26-07-2026 12.14(2).m4a'
container = av.open(audio_path)
stream = container.streams.audio[0]
target_sr = 22050
resampler = av.AudioResampler(format='fltp', layout='mono', rate=target_sr)
audio_frames = []
for frame in container.decode(stream):
    resampled = resampler.resample(frame)
    for rf in resampled:
        audio_frames.append(rf.to_ndarray()[0])
y = np.concatenate(audio_frames)
duracion = len(y) / target_sr
print(f"Audio de Bandurria del usuario cargado. Duración: {duracion:.2f} segundos. SR: {target_sr}")

# Analizar la señal y espectro
rms = librosa.feature.rms(y=y)[0]
active_frames = np.sum(rms > 0.01)
print(f"Energía RMS media: {np.mean(rms):.4f}, Frames activos: {active_frames}")

# Guardar informe de análisis
with open(r'c:\Users\Antonio\Documents\Desarrollo\Partituras\audio_analysis.txt', 'w', encoding='utf-8') as f:
    f.write(f"Duración: {duracion:.2f}s\nRMS Medio: {np.mean(rms):.4f}\n")
