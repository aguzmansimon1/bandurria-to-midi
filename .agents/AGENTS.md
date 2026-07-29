# Rules y Protocolo de Inicio Rápido para Agentes AI

## Protocolo de Inicio / Sincronización ("Buenos días, sincroniza" / "Sincroniza y prepara todo")

Cuando el usuario se conecte desde un nuevo ordenador o pida "sincroniza", "buenos días" o similar:

1. **Sincronizar código desde GitHub**:
   - `git pull origin master`
2. **Comprobar / Crear entorno virtual**:
   - Si no existe `.venv`:
     - `python -m venv .venv`
     - `.\.venv\Scripts\pip.exe install -r requirements.txt`
3. **Verificar estado**:
   - Comprobar que `.venv` e importaciones (`basic_pitch`, `onnxruntime`, `librosa`, `pretty_midi`, `av`) funcionan.
4. **Informar al usuario**:
   - Confirmar que la aplicación está sincronizada, probada y lista para ejecutar con `.\Abrir_Transcriptor.bat`.

---

## Estado del Proyecto

- **IA de Spotify**: Motor convolucional `basic-pitch` sobre **ONNX Runtime (`nmp.onnx`)**.
- **Monofonización**: Filtro `clean_to_monophonic_melody` (acotado Fa#3 a La5).
- **GUI**: Interfaz gráfica de un solo cuerpo (`gui.py`) sin pestañas.
- **Rutas**: Guardado por defecto en `outputs/` local de C: con orden `explorer /select`.
