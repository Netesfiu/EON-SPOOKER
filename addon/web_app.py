#!/usr/bin/env python3
"""
Web interface for EON-SPOOKER Home Assistant addon
"""

import os
import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
import requests

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'eon-spooker-addon-secret')

# Configuration from environment
INPUT_FOLDER = os.environ.get('EON_INPUT_FOLDER', '/share/eon-data')
OUTPUT_FOLDER = os.environ.get('EON_OUTPUT_FOLDER', '/share/eon-output')
RESOLUTION = os.environ.get('EON_RESOLUTION', 'hourly')
AUTO_PROCESS = os.environ.get('EON_AUTO_PROCESS', 'true').lower() == 'true'
AUTO_IMPORT = os.environ.get('EON_AUTO_IMPORT', 'false').lower() == 'true'
LOG_LEVEL = os.environ.get('EON_LOG_LEVEL', 'INFO')
NOTIFICATION_SERVICE = os.environ.get('EON_NOTIFICATION_SERVICE', '')

# Allowed file extensions
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_ha_supervisor_token():
    """Get Home Assistant Supervisor token"""
    try:
        with open('/data/options.json', 'r') as f:
            options = json.load(f)
        return os.environ.get('SUPERVISOR_TOKEN')
    except:
        return None

def call_ha_service(service, data=None):
    """Call Home Assistant service"""
    token = get_ha_supervisor_token()
    if not token:
        return False
    
    try:
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        url = f'http://supervisor/core/api/services/{service.replace(".", "/")}'
        response = requests.post(url, headers=headers, json=data or {})
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Failed to call HA service {service}: {e}")
        return False

def send_notification(message, title="EON-SPOOKER"):
    """Send notification to Home Assistant"""
    if NOTIFICATION_SERVICE:
        call_ha_service(NOTIFICATION_SERVICE, {
            'title': title,
            'message': message
        })

@app.route('/')
def index():
    """Main page"""
    # Get list of files in input and output folders
    input_files = []
    output_files = []
    
    try:
        input_path = Path(INPUT_FOLDER)
        if input_path.exists():
            input_files = [f.name for f in input_path.iterdir() if f.is_file() and allowed_file(f.name)]
    except Exception as e:
        logger.error(f"Error reading input folder: {e}")
    
    try:
        output_path = Path(OUTPUT_FOLDER)
        if output_path.exists():
            output_files = [f.name for f in output_path.iterdir() if f.is_file() and f.suffix in ['.yaml', '.yml']]
    except Exception as e:
        logger.error(f"Error reading output folder: {e}")
    
    return render_template('index.html', 
                         input_files=input_files,
                         output_files=output_files,
                         config={
                             'input_folder': INPUT_FOLDER,
                             'output_folder': OUTPUT_FOLDER,
                             'resolution': RESOLUTION,
                             'auto_process': AUTO_PROCESS,
                             'auto_import': AUTO_IMPORT
                         })

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = Path(INPUT_FOLDER) / filename
        
        try:
            # Create input folder if it doesn't exist
            Path(INPUT_FOLDER).mkdir(parents=True, exist_ok=True)
            file.save(str(filepath))
            flash(f'File {filename} uploaded successfully')
            
            # Auto-process if enabled
            if AUTO_PROCESS:
                return redirect(url_for('process_file', filename=filename))
                
        except Exception as e:
            flash(f'Error uploading file: {e}')
    else:
        flash('Invalid file type. Please upload CSV or Excel files.')
    
    return redirect(url_for('index'))

@app.route('/process/<filename>')
def process_file(filename):
    """Process a specific file"""
    try:
        input_file = Path(INPUT_FOLDER) / filename
        if not input_file.exists():
            flash(f'File {filename} not found')
            return redirect(url_for('index'))
        
        # Create output folder if it doesn't exist
        Path(OUTPUT_FOLDER).mkdir(parents=True, exist_ok=True)
        
        # Build command
        output_file = Path(OUTPUT_FOLDER) / f"{input_file.stem}_processed.yaml"
        cmd = [
            'python3', '/app/EON_SPOOKER_v3.py',
            '--resolution', RESOLUTION,
            '--output', str(output_file),
            str(input_file)
        ]
        
        if LOG_LEVEL == 'DEBUG':
            cmd.append('--verbose')
        
        # Run processing
        logger.info(f"Processing file: {filename}")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd='/app')
        
        if result.returncode == 0:
            flash(f'File {filename} processed successfully')
            send_notification(f'Successfully processed {filename}')
            
            # Auto-import if enabled
            if AUTO_IMPORT:
                return redirect(url_for('import_statistics', filename=f"{input_file.stem}_processed"))
        else:
            error_msg = result.stderr or result.stdout
            flash(f'Error processing file: {error_msg}')
            send_notification(f'Error processing {filename}: {error_msg}', 'EON-SPOOKER Error')
            logger.error(f"Processing error: {error_msg}")
    
    except Exception as e:
        flash(f'Error processing file: {e}')
        logger.error(f"Processing exception: {e}")
    
    return redirect(url_for('index'))

@app.route('/process_all')
def process_all():
    """Process all files in input folder"""
    try:
        input_path = Path(INPUT_FOLDER)
        if not input_path.exists():
            flash('Input folder not found')
            return redirect(url_for('index'))
        
        files = [f for f in input_path.iterdir() if f.is_file() and allowed_file(f.name)]
        
        if not files:
            flash('No files to process')
            return redirect(url_for('index'))
        
        # Create output folder if it doesn't exist
        Path(OUTPUT_FOLDER).mkdir(parents=True, exist_ok=True)
        
        # Process all files
        output_file = Path(OUTPUT_FOLDER) / f"combined_processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
        cmd = [
            'python3', '/app/EON_SPOOKER_v3.py',
            '--resolution', RESOLUTION,
            '--output', str(output_file)
        ] + [str(f) for f in files]
        
        if LOG_LEVEL == 'DEBUG':
            cmd.append('--verbose')
        
        logger.info(f"Processing {len(files)} files")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd='/app')
        
        if result.returncode == 0:
            flash(f'Successfully processed {len(files)} files')
            send_notification(f'Successfully processed {len(files)} files')
        else:
            error_msg = result.stderr or result.stdout
            flash(f'Error processing files: {error_msg}')
            send_notification(f'Error processing files: {error_msg}', 'EON-SPOOKER Error')
            logger.error(f"Processing error: {error_msg}")
    
    except Exception as e:
        flash(f'Error processing files: {e}')
        logger.error(f"Processing exception: {e}")
    
    return redirect(url_for('index'))

@app.route('/import_statistics/<filename>')
def import_statistics(filename):
    """Import statistics to Home Assistant"""
    try:
        # Look for import and export files
        import_file = Path(OUTPUT_FOLDER) / f"{filename}_import.yaml"
        export_file = Path(OUTPUT_FOLDER) / f"{filename}_export.yaml"
        
        success_count = 0
        
        if import_file.exists():
            if import_yaml_to_ha(import_file, 'import'):
                success_count += 1
        
        if export_file.exists():
            if import_yaml_to_ha(export_file, 'export'):
                success_count += 1
        
        if success_count > 0:
            flash(f'Successfully imported {success_count} statistics to Home Assistant')
            send_notification(f'Imported {success_count} statistics to Home Assistant')
        else:
            flash('No statistics files found or import failed')
    
    except Exception as e:
        flash(f'Error importing statistics: {e}')
        logger.error(f"Import exception: {e}")
    
    return redirect(url_for('index'))

def import_yaml_to_ha(yaml_file, stat_type):
    """Import YAML statistics to Home Assistant"""
    try:
        import yaml
        
        with open(yaml_file, 'r') as f:
            content = f.read()
        
        # Extract YAML data (skip header comments)
        yaml_start = content.find('- start:')
        if yaml_start == -1:
            return False
        
        yaml_data = yaml.safe_load(content[yaml_start:])
        
        # Call Home Assistant recorder service
        service_data = {
            'has_mean': False,
            'has_sum': True,
            'statistic_id': f'sensor.eon_{stat_type}',
            'source': 'recorder',
            'unit_of_measurement': 'kWh',
            'stats': yaml_data
        }
        
        return call_ha_service('recorder.import_statistics', service_data)
    
    except Exception as e:
        logger.error(f"Error importing {yaml_file}: {e}")
        return False

@app.route('/download/<filename>')
def download_file(filename):
    """Download output file"""
    try:
        file_path = Path(OUTPUT_FOLDER) / filename
        if file_path.exists():
            return send_file(str(file_path), as_attachment=True)
        else:
            flash('File not found')
    except Exception as e:
        flash(f'Error downloading file: {e}')
    
    return redirect(url_for('index'))

@app.route('/delete/<folder>/<filename>')
def delete_file(folder, filename):
    """Delete file"""
    try:
        if folder == 'input':
            file_path = Path(INPUT_FOLDER) / filename
        elif folder == 'output':
            file_path = Path(OUTPUT_FOLDER) / filename
        else:
            flash('Invalid folder')
            return redirect(url_for('index'))
        
        if file_path.exists():
            file_path.unlink()
            flash(f'File {filename} deleted successfully')
        else:
            flash('File not found')
    
    except Exception as e:
        flash(f'Error deleting file: {e}')
    
    return redirect(url_for('index'))

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    try:
        input_count = len(list(Path(INPUT_FOLDER).glob('*'))) if Path(INPUT_FOLDER).exists() else 0
        output_count = len(list(Path(OUTPUT_FOLDER).glob('*.yaml'))) if Path(OUTPUT_FOLDER).exists() else 0
        
        return jsonify({
            'status': 'running',
            'input_files': input_count,
            'output_files': output_count,
            'config': {
                'resolution': RESOLUTION,
                'auto_process': AUTO_PROCESS,
                'auto_import': AUTO_IMPORT
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

if __name__ == '__main__':
    # Create directories
    Path(INPUT_FOLDER).mkdir(parents=True, exist_ok=True)
    Path(OUTPUT_FOLDER).mkdir(parents=True, exist_ok=True)
    
    # Start Flask app
    app.run(host='0.0.0.0', port=5000, debug=(LOG_LEVEL == 'DEBUG'))
