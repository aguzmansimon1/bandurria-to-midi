import os
import sys
import time
import threading
import webbrowser
from flask import Flask, render_template_string, request, jsonify, send_file
from werkzeug.utils import secure_filename
from transcribe_melody import transcribe_audio_to_midi

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200 MB max limit

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Transcriptor de Bandurria a MIDI (MuseScore)</title>
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-gradient: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            --card-bg: rgba(30, 41, 59, 0.75);
            --card-border: rgba(255, 255, 255, 0.12);
            --accent-purple: #818cf8;
            --accent-pink: #c084fc;
            --accent-glow: rgba(129, 140, 248, 0.35);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --success: #34d399;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', sans-serif;
            background: var(--bg-gradient);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }

        .container {
            width: 100%;
            max-width: 760px;
            background: var(--card-bg);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--card-border);
            border-radius: 24px;
            padding: 36px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 30px var(--accent-glow);
        }

        .header {
            text-align: center;
            margin-bottom: 28px;
        }

        .header h1 {
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(to right, #a5b4fc, #e879f9);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }

        .header p {
            color: var(--text-muted);
            font-size: 0.95rem;
            line-height: 1.5;
        }

        /* Tabs Selection */
        .tab-buttons {
            display: flex;
            gap: 10px;
            margin-bottom: 16px;
            background: rgba(15, 23, 42, 0.5);
            padding: 5px;
            border-radius: 14px;
        }

        .tab-btn {
            flex: 1;
            padding: 10px;
            border: none;
            background: transparent;
            color: var(--text-muted);
            font-weight: 600;
            font-size: 0.9rem;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .tab-btn.active {
            background: var(--accent-purple);
            color: white;
            box-shadow: 0 4px 12px var(--accent-glow);
        }

        /* Dropzone */
        .dropzone {
            border: 2px dashed rgba(129, 140, 248, 0.4);
            border-radius: 16px;
            padding: 32px 20px;
            text-align: center;
            background: rgba(15, 23, 42, 0.4);
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            margin-bottom: 20px;
        }

        .dropzone:hover, .dropzone.dragover, .dropzone.has-file {
            border-color: var(--accent-purple);
            background: rgba(129, 140, 248, 0.1);
            box-shadow: 0 0 20px var(--accent-glow);
        }

        .dropzone input[type="file"] {
            display: none;
        }

        .dropzone-icon {
            font-size: 2.8rem;
            margin-bottom: 12px;
            display: block;
        }

        .btn-browse {
            display: inline-block;
            margin-top: 10px;
            padding: 8px 18px;
            background: rgba(129, 140, 248, 0.2);
            border: 1px solid var(--accent-purple);
            color: var(--text-main);
            border-radius: 10px;
            font-weight: 600;
            font-size: 0.88rem;
            pointer-events: none;
        }

        .file-info-badge {
            display: none;
            background: rgba(52, 211, 153, 0.15);
            border: 1px solid rgba(52, 211, 153, 0.4);
            color: var(--success);
            padding: 12px 16px;
            border-radius: 12px;
            font-weight: 600;
            font-size: 0.95rem;
            margin-top: 10px;
            word-break: break-all;
        }

        /* Local Path Input Box */
        .local-path-box {
            display: none;
            margin-bottom: 20px;
        }

        .local-path-box input {
            width: 100%;
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 12px 14px;
            color: var(--text-main);
            font-size: 0.95rem;
            font-family: inherit;
            outline: none;
        }

        .local-path-box input:focus {
            border-color: var(--accent-purple);
        }

        /* Form Grid */
        .form-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 24px;
        }

        .form-group {
            display: flex;
            flex-direction: column;
        }

        .form-group label {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-muted);
            margin-bottom: 6px;
        }

        .form-group input, .form-group select {
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 12px 14px;
            color: var(--text-main);
            font-size: 0.95rem;
            font-family: inherit;
            outline: none;
            transition: border-color 0.2s;
        }

        .form-group input:focus, .form-group select:focus {
            border-color: var(--accent-purple);
        }

        /* Action Button */
        .btn-submit {
            width: 100%;
            padding: 16px;
            border: none;
            border-radius: 14px;
            background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
            color: white;
            font-size: 1.05rem;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 10px 25px -5px var(--accent-glow);
            transition: transform 0.2s, box-shadow 0.2s;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
        }

        .btn-submit:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 15px 30px -5px var(--accent-glow);
        }

        .btn-submit:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        /* Progress & Logs */
        .status-card {
            display: none;
            margin-top: 24px;
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 20px;
        }

        .progress-bar-bg {
            width: 100%;
            height: 8px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 12px;
        }

        .progress-bar-fill {
            height: 100%;
            width: 0%;
            background: linear-gradient(to right, #6366f1, #34d399);
            transition: width 0.4s ease;
        }

        .log-box {
            font-family: monospace;
            font-size: 0.82rem;
            color: #cbd5e1;
            max-height: 120px;
            overflow-y: auto;
            white-space: pre-wrap;
            line-height: 1.4;
            padding-right: 5px;
        }

        /* Result Section */
        .result-card {
            display: none;
            margin-top: 24px;
            background: rgba(52, 211, 153, 0.1);
            border: 1px solid rgba(52, 211, 153, 0.3);
            border-radius: 16px;
            padding: 20px;
            text-align: center;
        }

        .result-card h3 {
            color: var(--success);
            margin-bottom: 8px;
            font-size: 1.2rem;
        }

        .btn-download {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-top: 14px;
            padding: 12px 24px;
            background: var(--success);
            color: #064e3b;
            font-weight: 700;
            text-decoration: none;
            border-radius: 12px;
            transition: transform 0.2s;
        }

        .btn-download:hover {
            transform: scale(1.03);
        }

        .spinner {
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 0.8s linear infinite;
            display: none;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>

<div class="container">
    <div class="header">
        <h1>🪕 Transcriptor de Bandurria a MIDI</h1>
        <p>Convierte el audio o vídeo de tu bandurria en un archivo MIDI listo para exportar a partitura en <strong>MuseScore</strong>.</p>
    </div>

    <!-- Mode Selector -->
    <div class="tab-buttons">
        <button type="button" class="tab-btn active" id="tabUploadBtn" onclick="setMode('upload')">📁 Seleccionar / Arrastrar Archivo</button>
        <button type="button" class="tab-btn" id="tabPathBtn" onclick="setMode('path')">💻 Ruta Local en Disco</button>
    </div>

    <form id="transcribeForm">
        <input type="file" id="audioFile" accept="audio/*,video/*">

        <!-- Mode 1: Drag & Drop Dropzone -->
        <div class="dropzone" id="dropzone" onclick="document.getElementById('audioFile').click()">
            <span class="dropzone-icon">🎼</span>
            <div id="dropzoneText">
                <strong>Arrastra tu archivo de audio/vídeo de bandurria aquí</strong>
                <div style="font-size: 0.85rem; color: var(--text-muted); margin-top: 4px;">formatos compatibles: MP4, MP3, WAV, M4A, AVI</div>
                <div class="btn-browse">Examinar Archivo...</div>
            </div>
            <div class="file-info-badge" id="fileInfoBadge"></div>
        </div>

        <!-- Mode 2: Local Path Input -->
        <div class="local-path-box" id="localPathBox">
            <label style="font-size: 0.85rem; font-weight: 600; color: var(--text-muted); display: block; margin-bottom: 6px;">Escribe o pega la ruta del archivo en tu PC:</label>
            <input type="text" id="localPathInput" placeholder="Ej: G:\Mi unidad\AYo\Tuna\Canciones Tuna\Noche madrileña\Noche madrileña bandurria.mp4">
        </div>

        <!-- Form Options -->
        <div class="form-grid">
            <div class="form-group">
                <label for="bpm">Tempo Estimado (BPM):</label>
                <input type="number" id="bpm" value="120" min="40" max="240" required>
            </div>
            <div class="form-group">
                <label for="subdivision">Subdivisión Rítmica (MuseScore):</label>
                <select id="subdivision">
                    <option value="16">1/16 (Semicorcheas)</option>
                    <option value="8">1/8 (Corcheas)</option>
                    <option value="4">1/4 (Negras)</option>
                </select>
            </div>
        </div>

        <!-- Submit Button -->
        <button type="submit" class="btn-submit" id="btnSubmit">
            <span class="spinner" id="btnSpinner"></span>
            <span id="btnText">🎵 Convertir y Transcribir a MIDI</span>
        </button>
    </form>

    <!-- Status & Progress -->
    <div class="status-card" id="statusCard">
        <div class="progress-bar-bg">
            <div class="progress-bar-fill" id="progressFill"></div>
        </div>
        <div class="log-box" id="logBox">Iniciando procesamiento...</div>
    </div>

    <!-- Result Box -->
    <div class="result-card" id="resultCard">
        <h3>¡Transcripción Completada!</h3>
        <p style="font-size: 0.9rem; color: #cbd5e1; margin-top: 4px;">Tu archivo MIDI de bandurria ha sido generado con trémolos unificados y ritmo cuantizado.</p>
        <a href="#" class="btn-download" id="downloadBtn" download>
            <span>📥 Descargar Archivo MIDI</span>
        </a>
    </div>
</div>

<script>
    let currentMode = 'upload';
    const fileInput = document.getElementById('audioFile');
    const dropzone = document.getElementById('dropzone');
    const dropzoneText = document.getElementById('dropzoneText');
    const fileInfoBadge = document.getElementById('fileInfoBadge');
    const localPathBox = document.getElementById('localPathBox');
    const localPathInput = document.getElementById('localPathInput');
    const form = document.getElementById('transcribeForm');
    const btnSubmit = document.getElementById('btnSubmit');
    const btnSpinner = document.getElementById('btnSpinner');
    const btnText = document.getElementById('btnText');
    const statusCard = document.getElementById('statusCard');
    const progressFill = document.getElementById('progressFill');
    const logBox = document.getElementById('logBox');
    const resultCard = document.getElementById('resultCard');
    const downloadBtn = document.getElementById('downloadBtn');

    function setMode(mode) {
        currentMode = mode;
        if (mode === 'upload') {
            document.getElementById('tabUploadBtn').classList.add('active');
            document.getElementById('tabPathBtn').classList.remove('active');
            dropzone.style.display = 'block';
            localPathBox.style.display = 'none';
        } else {
            document.getElementById('tabPathBtn').classList.add('active');
            document.getElementById('tabUploadBtn').classList.remove('active');
            dropzone.style.display = 'none';
            localPathBox.style.display = 'block';
            if (!localPathInput.value) {
                localPathInput.value = `G:\\Mi unidad\\AYo\\Tuna\\Canciones Tuna\\Noche madrileña\\Noche madrileña bandurria.mp4`;
            }
        }
    }

    // Drag & Drop Handling
    ['dragenter', 'dragover'].forEach(name => {
        dropzone.addEventListener(name, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(name => {
        dropzone.addEventListener(name, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dragover');
        });
    });

    dropzone.addEventListener('drop', (e) => {
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            try {
                const dt = new DataTransfer();
                dt.items.add(e.dataTransfer.files[0]);
                fileInput.files = dt.files;
            } catch(err) {
                fileInput.files = e.dataTransfer.files;
            }
            updateFileInfo();
        }
    });

    fileInput.addEventListener('change', updateFileInfo);

    function updateFileInfo() {
        if (fileInput.files && fileInput.files.length > 0) {
            const file = fileInput.files[0];
            const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
            fileInfoBadge.innerHTML = `✅ Archivo Seleccionado:<br><strong>${file.name}</strong> (${sizeMB} MB)`;
            fileInfoBadge.style.display = 'block';
            dropzoneText.style.display = 'none';
            dropzone.classList.add('has-file');
        }
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData();
        formData.append('bpm', document.getElementById('bpm').value);
        formData.append('subdivision', document.getElementById('subdivision').value);

        if (currentMode === 'upload') {
            if (!fileInput.files || !fileInput.files.length) {
                alert('Por favor selecciona o arrastra un archivo de audio/vídeo de bandurria.');
                return;
            }
            formData.append('audio', fileInput.files[0]);
        } else {
            const pathVal = localPathInput.value.trim();
            if (!pathVal) {
                alert('Por favor escribe la ruta local de tu archivo.');
                return;
            }
            formData.append('local_path', pathVal);
        }

        // UI Reset
        btnSubmit.disabled = true;
        btnSpinner.style.display = 'inline-block';
        btnText.textContent = 'Procesando Bandurria...';
        statusCard.style.display = 'block';
        resultCard.style.display = 'none';
        progressFill.style.width = '20%';
        logBox.textContent = 'Iniciando transcripción de la bandurria...\n';

        try {
            progressFill.style.width = '40%';
            logBox.textContent += 'Cargando audio y ejecutando detección de pitch pYIN...\n';

            const response = await fetch('/api/transcribe', {
                method: 'POST',
                body: formData
            });

            progressFill.style.width = '80%';
            logBox.textContent += 'Unificando notas de trémolo y aplicando cuantización para MuseScore...\n';

            const data = await response.json();

            if (data.success) {
                progressFill.style.width = '100%';
                logBox.textContent += '¡Éxito! Transcripción de Bandurria completada.\n';

                downloadBtn.href = data.download_url;
                downloadBtn.setAttribute('download', data.filename);
                resultCard.style.display = 'block';
            } else {
                alert('Error: ' + data.error);
                logBox.textContent += `❌ Error: ${data.error}\n`;
            }
        } catch (err) {
            alert('Error de procesamiento: ' + err.message);
            logBox.textContent += `❌ Error: ${err.message}\n`;
        } finally {
            btnSubmit.disabled = false;
            btnSpinner.style.display = 'none';
            btnText.textContent = '🎵 Convertir y Transcribir a MIDI';
        }
    });
</script>

</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/transcribe', methods=['POST'])
def api_transcribe():
    bpm = int(request.form.get('bpm', 120))
    subdivision = int(request.form.get('subdivision', 16))
    
    local_path = request.form.get('local_path', '').strip()
    
    if local_path:
        if not os.path.exists(local_path):
            return jsonify({'success': False, 'error': f"El archivo local '{local_path}' no existe en el disco"}), 400
        input_path = local_path
        filename = os.path.basename(local_path)
    else:
        if 'audio' not in request.files or request.files['audio'].filename == '':
            return jsonify({'success': False, 'error': 'No se adjuntó o seleccionó ningún archivo de audio'}), 400
            
        file = request.files['audio']
        filename = file.filename
        safe_name = f"upload_{int(time.time())}_{secure_filename(filename)}"
        if not safe_name.endswith(os.path.splitext(filename)[1]):
            safe_name += os.path.splitext(filename)[1]
            
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
        file.save(input_path)
    
    base_name, _ = os.path.splitext(filename)
    output_midi_name = f"{base_name}_bandurria.mid"
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_midi_name)
    
    try:
        transcribe_audio_to_midi(
            audio_path=input_path,
            midi_path=output_path,
            bpm=bpm,
            subdivision=subdivision
        )
        return jsonify({
            'success': True,
            'filename': output_midi_name,
            'download_url': f'/download/{output_midi_name}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "Archivo no encontrado", 404

def open_browser():
    time.sleep(1.2)
    webbrowser.open("http://127.0.0.1:5000")

def main():
    print("=========================================================")
    print("  Servidor Web de Transcripcion de Bandurria a MIDI")
    print("  Abriendo la interfaz en tu navegador por defecto...")
    print("  Direccion local: http://127.0.0.1:5000")
    print("=========================================================")
    
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host='127.0.0.1', port=5000, debug=False)

if __name__ == '__main__':
    main()
