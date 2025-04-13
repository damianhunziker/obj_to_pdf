#!/usr/bin/env python3
"""
OBJ to PDF Converter Server
This script provides a web API for the OBJ to PDF converter
"""

import os
import sys
import uuid
import re
import threading
import shutil
from pathlib import Path
from flask import Flask, request, jsonify, send_file, render_template_string, make_response
from flask_cors import CORS
import logging
import socket
from werkzeug.utils import secure_filename
from obj_to_pdf import ObjToPdfConverter

# Neue Imports hinzufügen
from flask import Response
import json
import time

# Progress-Tracking Dictionary anpassen
conversion_status = {}

def progress_handler(job_id):
    """Callback-Funktion für Fortschrittsupdates"""
    def handle_progress(progress, message):
        conversion_status[job_id] = {
            'progress': progress,
            'message': message,
            'timestamp': time.time()
        }
        logger.info(f"Job {job_id}: {progress}% - {message}")
    return handle_progress



# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('server.log')
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = os.path.expanduser('~/public_html/uploads')
OUTPUT_FOLDER = os.path.expanduser('~/public_html/output')
WORDPRESS_PDF_FOLDER = os.path.expanduser('~/public_html/wp-content/uploads/3d-pdfs')
WORDPRESS_URL_BASE = 'http://91.99.59.46/3dpdf-converter/wordpress/wp-content/uploads/3d-pdfs'
ALLOWED_EXTENSIONS = {'obj'}

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(WORDPRESS_PDF_FOLDER, exist_ok=True)

# Progress tracking
conversion_progress = {}

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        logger.error(f"Could not determine local IP: {e}")
        return "0.0.0.0"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def update_progress(job_id, progress):
    conversion_progress[job_id] = progress
    logger.info(f"Progress updated for job {job_id}: {progress}%")

def convert_using_script(obj_path, output_pdf, job_id):
    """Wrapper function to call obj_to_pdf conversion"""
    try:
        update_progress(job_id, 10)
        
        # Debug logging for paths
        logger.info("=== Path Debug Info ===")
        logger.info(f"obj_path: {obj_path}")
        logger.info(f"output_pdf: {output_pdf}")
        logger.info(f"Current working directory: {os.getcwd()}")
        
        # Create converter instance and ensure we're in the right directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        converter = ObjToPdfConverter()
        
        # Convert the file
        update_progress(job_id, 30)
        logger.info("Starting conversion...")
        pdf_file = converter.convert(obj_path, output_pdf)
        logger.info(f"Conversion result: {pdf_file}")
        
        if pdf_file and os.path.exists(pdf_file):
            # Generate download URL
            server_ip = get_local_ip()
            download_url = f"http://{server_ip}:5000/download/{job_id}"
            logger.info(f"PDF ready for download at: {download_url}")
            
            update_progress(job_id, 100)
            return download_url
        else:
            error_msg = "Conversion failed - PDF file not created"
            logger.error(error_msg)
            update_progress(job_id, -1)
            raise Exception(error_msg)
            
    except Exception as e:
        error_msg = f"Conversion error: {str(e)}"
        logger.error(error_msg)
        logger.exception("Full stack trace:")
        update_progress(job_id, -1)
        raise Exception(error_msg)

def sanitize_filename(filename):
    """Sanitize filename to contain only alphanumeric chars but keep extension"""
    # Split filename into name and extension
    name, ext = os.path.splitext(filename)
    # Replace all non-alphanumeric chars with empty string
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', name)
    # Combine clean name with original extension
    return f"{clean_name}{ext}"

@app.before_request
def log_request_info():
    logger.info(f"Request: {request.method} {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Body: {request.get_data()}")

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Accept,Access-Control-Allow-Origin')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

@app.route('/')
def index():
    logger.info("Serving index page")
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>OBJ to PDF Converter</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .upload-form { margin: 20px 0; }
            .progress-container { margin: 20px 0; display: none; }
            .progress-bar { width: 100%; height: 20px; background-color: #f0f0f0; border-radius: 10px; overflow: hidden; }
            .progress { width: 0%; height: 100%; background-color: #4CAF50; transition: width 0.3s; }
            .status { margin-top: 10px; }
            #download-link { display: none; margin-top: 20px; text-decoration: none; padding: 10px 20px; background-color: #4CAF50; color: white; border-radius: 5px; }
            #download-link:hover { background-color: #45a049; }
            .error { color: red; }
        </style>
    </head>
    <body>
        <h1>OBJ to PDF Converter</h1>
        <p>Server is running and ready to accept requests</p>
        <form class="upload-form" id="uploadForm">
            <input type="file" name="file" accept=".obj" required>
            <button type="submit">Convert</button>
        </form>
        <div class="progress-container" id="progressContainer">
            <div class="progress-bar">
                <div class="progress" id="progressBar"></div>
            </div>
            <div class="status" id="status"></div>
        </div>
        <a id="download-link" href="#" target="_blank">Download PDF</a>
        <script>
            document.getElementById('uploadForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData();
                formData.append('file', e.target.file.files[0]);
                
                const progressContainer = document.getElementById('progressContainer');
                const progressBar = document.getElementById('progressBar');
                const status = document.getElementById('status');
                const downloadLink = document.getElementById('download-link');
                
                progressContainer.style.display = 'block';
                status.textContent = 'Converting...';
                status.className = '';
                downloadLink.style.display = 'none';
                progressBar.style.width = '50%';
                
                try {
                    // Upload and convert
                    const response = await fetch('/convert', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    
                    const data = await response.json();
                    console.log('Conversion response:', data);
                    
                    if (data.error) {
                        throw new Error(data.error);
                    }
                    
                    if (data.download_url) {
                        // Conversion successful
                        progressBar.style.width = '100%';
                        status.textContent = 'Conversion complete! Click the link below to download.';
                        downloadLink.href = data.download_url;
                        downloadLink.style.display = 'block';
                        // Automatically open in new tab
                        window.open(data.download_url, '_blank');
                    } else {
                        throw new Error('No download URL received');
                    }
                    
                } catch (error) {
                    console.error('Conversion error:', error);
                    status.textContent = 'Error: ' + error.message;
                    status.className = 'error';
                    progressBar.style.width = '0%';
                }
            });
        </script>
    </body>
    </html>
    ''')

@app.route('/health')
def health_check():
    logger.info("Health check requested")
    return jsonify({
        'status': 'ok',
        'server_ip': get_local_ip(),
        'upload_folder': UPLOAD_FOLDER,
        'output_folder': OUTPUT_FOLDER
    })

@app.route('/convert', methods=['POST'])
def convert():
    try:
        if 'file' not in request.files:
            logger.error("No file part in request")
            return jsonify({'success': False, 'message': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            logger.error("No selected file")
            return jsonify({'success': False, 'message': 'No selected file'}), 400
        
        if not allowed_file(file.filename):
            logger.error(f"Invalid file type: {file.filename}")
            return jsonify({'success': False, 'message': 'Invalid file type'}), 400
        
        try:
            # Generate unique job ID
            job_id = str(uuid.uuid4())
            logger.info(f"Starting new conversion job: {job_id}")
            
            # Save uploaded file with sanitized name
            filename = secure_filename(file.filename)
            sanitized_filename = sanitize_filename(f"{job_id}_{filename}")
            obj_path = os.path.join(UPLOAD_FOLDER, sanitized_filename)
            
            # Ensure upload directory exists
            os.makedirs(os.path.dirname(obj_path), exist_ok=True)
            
            # Save file
            logger.info(f"Saving file to: {obj_path}")
            file.save(obj_path)
            
            if not os.path.exists(obj_path):
                raise Exception(f"Failed to save file at: {obj_path}")
            
            # Set output PDF path
            base_name = os.path.splitext(sanitized_filename)[0]
            output_pdf = os.path.join(OUTPUT_FOLDER, f"{base_name}.pdf")
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_pdf), exist_ok=True)
            
            logger.info(f"Output PDF will be: {output_pdf}")
            
            # Initialize converter with progress handler
            converter = ObjToPdfConverter(progress_callback=progress_handler(job_id))
            
            try:
                # Start conversion
                logger.info(f"Starting conversion for job {job_id}")
                logger.info(f"Current working directory: {os.getcwd()}")
                logger.info(f"Input file exists: {os.path.exists(obj_path)}")
                logger.info(f"Input file size: {os.path.getsize(obj_path)}")
                
                pdf_file = converter.convert(obj_path, output_pdf)
                logger.info(f"Conversion result: {pdf_file}")
                
                if pdf_file and os.path.exists(pdf_file):
                    download_url = f"http://{get_local_ip()}:5000/download/{job_id}"
                    logger.info(f"Conversion successful, download URL: {download_url}")
                    
                    # Update final status
                    conversion_status[job_id] = {
                        'progress': 100,
                        'message': 'Konvertierung erfolgreich abgeschlossen'
                    }
                    
                    return jsonify({
                        'success': True,
                        'downloadUrl': download_url,
                        'message': 'Conversion successful'
                    })
                else:
                    error_msg = "Conversion failed - PDF not created"
                    logger.error(error_msg)
                    # Update status with error
                    conversion_status[job_id] = {
                        'progress': -1,
                        'message': error_msg
                    }
                    return jsonify({
                        'success': False,
                        'message': error_msg
                    }), 500
                    
            except Exception as e:
                error_msg = f"Error during conversion: {str(e)}"
                logger.error(error_msg)
                logger.exception("Full stack trace:")
                # Update status with error
                conversion_status[job_id] = {
                    'progress': -1,
                    'message': f"Konvertierungsfehler: {str(e)}"
                }
                return jsonify({
                    'success': False,
                    'message': error_msg
                }), 500
                
        except Exception as e:
            error_msg = f"Error handling file: {str(e)}"
            logger.error(error_msg)
            logger.exception("Full stack trace:")
            return jsonify({
                'success': False,
                'message': error_msg
            }), 500
            
    except Exception as e:
        error_msg = f"General error in /convert: {str(e)}"
        logger.error(error_msg)
        logger.exception("Full stack trace:")
        return jsonify({
            'success': False,
            'message': error_msg
        }), 500

@app.route('/progress/<job_id>')
def get_progress(job_id):
    """Stream conversion progress updates"""
    def generate():
        while True:
            if job_id in conversion_status:
                status = conversion_status[job_id]
                # Konvertiere Status in JSON und sende als SSE
                yield f"data: {json.dumps(status)}\n\n"
                
                # Wenn Konvertierung abgeschlossen oder fehlgeschlagen
                if status['progress'] >= 100 or status['progress'] == -1:
                    break
            
            time.sleep(0.1)  # Kleine Pause zwischen Updates
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )

@app.route('/download/<job_id>')
def download(job_id):
    # Remove hyphens from job_id for comparison
    job_id_no_hyphens = job_id.replace('-', '')
    
    # Find the PDF file
    for filename in os.listdir(OUTPUT_FOLDER):
        # Remove hyphens from filename for comparison
        if job_id_no_hyphens in filename.replace('-', '') and filename.endswith('.pdf'):
            pdf_path = os.path.join(OUTPUT_FOLDER, filename)
            logger.info(f"Serving PDF for download: {pdf_path}")
            response = send_file(pdf_path, mimetype='application/pdf')
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
    
    logger.error(f"PDF not found for job: {job_id} (without hyphens: {job_id_no_hyphens})")
    return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    local_ip = get_local_ip()
    logger.info(f"Starting Flask server on {local_ip}:5000")
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=True) 