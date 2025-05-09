import os
import threading
from flask import Flask, request, send_file, render_template, jsonify
from license_detector import detect_licenses

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
progress = {'current': 0, 'total': 0}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if not file.filename.endswith('.xlsx'):
        return 'Only .xlsx files are supported.', 400
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    result_path = os.path.join(RESULT_FOLDER, 'result_' + file.filename)
    def run_detection():
        detect_licenses(filepath, result_path, progress)
    threading.Thread(target=run_detection).start()
    return jsonify({'status': 'processing'})

@app.route('/progress')
def get_progress():
    return jsonify(progress)

@app.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join(RESULT_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
