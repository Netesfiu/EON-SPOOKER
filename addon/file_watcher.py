#!/usr/bin/env python3
"""
File watcher service for EON-SPOOKER Home Assistant addon
Monitors input folder for new files and processes them automatically
"""

import os
import time
import logging
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment
INPUT_FOLDER = os.environ.get('EON_INPUT_FOLDER', '/share/eon-data')
OUTPUT_FOLDER = os.environ.get('EON_OUTPUT_FOLDER', '/share/eon-output')
RESOLUTION = os.environ.get('EON_RESOLUTION', 'hourly')
AUTO_PROCESS = os.environ.get('EON_AUTO_PROCESS', 'true').lower() == 'true'
LOG_LEVEL = os.environ.get('EON_LOG_LEVEL', 'INFO')

# Allowed file extensions
ALLOWED_EXTENSIONS = {'.csv', '.xlsx', '.xls'}

class EONFileHandler(FileSystemEventHandler):
    """Handle file system events for EON data files"""
    
    def __init__(self):
        self.processing = set()  # Track files being processed
    
    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        if file_path.suffix.lower() in ALLOWED_EXTENSIONS:
            logger.info(f"New file detected: {file_path.name}")
            
            # Wait a bit to ensure file is fully written
            time.sleep(2)
            
            if AUTO_PROCESS:
                self.process_file(file_path)
    
    def on_moved(self, event):
        """Handle file move events (e.g., from temp to final location)"""
        if event.is_directory:
            return
        
        dest_path = Path(event.dest_path)
        if dest_path.suffix.lower() in ALLOWED_EXTENSIONS:
            logger.info(f"File moved to: {dest_path.name}")
            
            # Wait a bit to ensure file is fully written
            time.sleep(2)
            
            if AUTO_PROCESS:
                self.process_file(dest_path)
    
    def process_file(self, file_path):
        """Process a detected file"""
        if str(file_path) in self.processing:
            logger.info(f"File {file_path.name} is already being processed")
            return
        
        try:
            self.processing.add(str(file_path))
            logger.info(f"Processing file: {file_path.name}")
            
            # Create output folder if it doesn't exist
            Path(OUTPUT_FOLDER).mkdir(parents=True, exist_ok=True)
            
            # Build command
            output_file = Path(OUTPUT_FOLDER) / f"{file_path.stem}_auto_processed.yaml"
            cmd = [
                'python3', '/app/EON_SPOOKER_v3.py',
                '--resolution', RESOLUTION,
                '--output', str(output_file),
                str(file_path)
            ]
            
            if LOG_LEVEL == 'DEBUG':
                cmd.append('--verbose')
            
            # Run processing
            result = subprocess.run(cmd, capture_output=True, text=True, cwd='/app')
            
            if result.returncode == 0:
                logger.info(f"Successfully processed {file_path.name}")
                
                # Send notification via web app
                try:
                    import requests
                    requests.post('http://localhost:5000/api/notify', 
                                json={'message': f'Auto-processed {file_path.name}'})
                except:
                    pass  # Web app might not be ready yet
            else:
                error_msg = result.stderr or result.stdout
                logger.error(f"Error processing {file_path.name}: {error_msg}")
        
        except Exception as e:
            logger.error(f"Exception processing {file_path.name}: {e}")
        
        finally:
            self.processing.discard(str(file_path))

def main():
    """Main file watcher loop"""
    logger.info("Starting EON-SPOOKER file watcher")
    logger.info(f"Monitoring folder: {INPUT_FOLDER}")
    logger.info(f"Auto-process enabled: {AUTO_PROCESS}")
    
    # Create input folder if it doesn't exist
    Path(INPUT_FOLDER).mkdir(parents=True, exist_ok=True)
    
    if not AUTO_PROCESS:
        logger.info("Auto-processing disabled, file watcher will only log events")
    
    # Setup file watcher
    event_handler = EONFileHandler()
    observer = Observer()
    observer.schedule(event_handler, INPUT_FOLDER, recursive=False)
    
    try:
        observer.start()
        logger.info("File watcher started successfully")
        
        # Keep the watcher running
        while True:
            time.sleep(10)
            
            # Health check - ensure input folder still exists
            if not Path(INPUT_FOLDER).exists():
                logger.warning(f"Input folder {INPUT_FOLDER} no longer exists, recreating...")
                Path(INPUT_FOLDER).mkdir(parents=True, exist_ok=True)
    
    except KeyboardInterrupt:
        logger.info("File watcher stopped by user")
    except Exception as e:
        logger.error(f"File watcher error: {e}")
    finally:
        observer.stop()
        observer.join()
        logger.info("File watcher stopped")

if __name__ == '__main__':
    main()
