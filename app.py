from flask import Flask, render_template, request, send_file, jsonify
import os
import shutil
import json
from script import generate_certificates
from emailer import send_emails
from utils.fonts import get_font_path, download_font

app = Flask(__name__)

# Config
UPLOAD_FOLDER = 'uploads'
GENERATED_FOLDER = 'generated_certs'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['GENERATED_FOLDER'] = GENERATED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Ensure dirs exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/.well-known/appspecific/com.chrome.devtools.json')
def chrome_devtools_probe():
    # Chrome DevTools may probe this well-known URL; return an empty JSON
    # response so the request is handled cleanly instead of logging a 404.
    return jsonify({})

@app.route('/api/generate', methods=['POST'])
def generate():
    # 1. Handle Files
    if 'csvFile' not in request.files or 'templateFile' not in request.files:
        return jsonify({"error": "Missing CSV or Template file"}), 400
    
    csv_file = request.files['csvFile']
    template_file = request.files['templateFile']
    
    if csv_file.filename == '' or template_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Save uploaded files
    csv_path = os.path.join(app.config['UPLOAD_FOLDER'], 'participants.csv')
    template_path = os.path.join(app.config['UPLOAD_FOLDER'], 'template.png')
    
    csv_file.save(csv_path)
    template_file.save(template_path)

    # 2. Get Config (JSON string)
    configs_str = request.form.get('fieldConfigs', '[]')
    try:
        field_configs = json.loads(configs_str)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid field configuration"}), 400

    # 3. Handle Colors and Configs
    processed_configs = []
    for config in field_configs:
        # Convert hex color to RGB tuple
        hex_color = config.get('color', '#000000')
        rgb_color = tuple(int(hex_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        
        processed_configs.append({
            "column": config.get('column'),
            "font": config.get('font', 'Arial'),
            "size": int(config.get('size', 40)),
            "color": rgb_color,
            "x": int(config.get('x', 0)),
            "y": int(config.get('y', 0)),
            "alignment": config.get('alignment', 'center')
        })

    # 4. Generate
    if os.path.exists(app.config['GENERATED_FOLDER']):
        shutil.rmtree(app.config['GENERATED_FOLDER'])
    os.makedirs(app.config['GENERATED_FOLDER'])

    zip_path, error = generate_certificates(
        template_path, 
        csv_path, 
        app.config['GENERATED_FOLDER'],
        processed_configs
    )

    if error:
        return jsonify({"error": error}), 500

    return jsonify({"downloadUrl": "/api/download", "message": "Certificates generated successfully!"})

@app.route('/api/download')
def download():
    zip_path = os.path.join(app.config['GENERATED_FOLDER'], 'certificates.zip')
    if os.path.exists(zip_path):
        return send_file(zip_path, as_attachment=True)
    return "File not found", 404

@app.route('/api/email', methods=['POST'])
def email_participants():
    data = request.json
    sender_email = data.get('email')
    app_password = data.get('password')
    subject = data.get('subject')
    body = data.get('body')

    csv_path = os.path.join(app.config['UPLOAD_FOLDER'], 'participants.csv')
    cert_dir = app.config['GENERATED_FOLDER']

    if not sender_email or not app_password:
        return jsonify({"error": "Missing credentials"}), 400

    success, errors, logs = send_emails(csv_path, cert_dir, sender_email, app_password, subject, body)
    
    return jsonify({
        "success": True,
        "sent": success,
        "failed": errors,
        "logs": logs
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
