#!/usr/bin/with-contenv bashio

# ==============================================================================
# Home Assistant Add-on: EON-SPOOKER
# Runs the EON-SPOOKER energy data processor
# ==============================================================================

# Get configuration
AUTO_PROCESS=$(bashio::config 'auto_process')
INPUT_FOLDER=$(bashio::config 'input_folder')
OUTPUT_FOLDER=$(bashio::config 'output_folder')
RESOLUTION=$(bashio::config 'resolution')
LOG_LEVEL=$(bashio::config 'log_level')
AUTO_IMPORT=$(bashio::config 'auto_import')
FILE_PATTERNS=$(bashio::config 'file_patterns' '["*.csv", "*.xlsx"]')
BACKUP_FILES=$(bashio::config 'backup_files' 'true')
NOTIFICATION_SERVICE=$(bashio::config 'notification_service' '')

# Set log level
case "${LOG_LEVEL}" in
    trace)
        LOG_LEVEL_PYTHON="DEBUG"
        ;;
    debug)
        LOG_LEVEL_PYTHON="DEBUG"
        ;;
    info)
        LOG_LEVEL_PYTHON="INFO"
        ;;
    notice)
        LOG_LEVEL_PYTHON="INFO"
        ;;
    warning)
        LOG_LEVEL_PYTHON="WARNING"
        ;;
    error)
        LOG_LEVEL_PYTHON="ERROR"
        ;;
    fatal)
        LOG_LEVEL_PYTHON="CRITICAL"
        ;;
    *)
        LOG_LEVEL_PYTHON="INFO"
        ;;
esac

# Create directories if they don't exist
mkdir -p "${INPUT_FOLDER}"
mkdir -p "${OUTPUT_FOLDER}"

# Export configuration for the web app
export EON_AUTO_PROCESS="${AUTO_PROCESS}"
export EON_INPUT_FOLDER="${INPUT_FOLDER}"
export EON_OUTPUT_FOLDER="${OUTPUT_FOLDER}"
export EON_RESOLUTION="${RESOLUTION}"
export EON_LOG_LEVEL="${LOG_LEVEL_PYTHON}"
export EON_AUTO_IMPORT="${AUTO_IMPORT}"
export EON_FILE_PATTERNS="${FILE_PATTERNS}"
export EON_BACKUP_FILES="${BACKUP_FILES}"
export EON_NOTIFICATION_SERVICE="${NOTIFICATION_SERVICE}"

bashio::log.info "Starting EON-SPOOKER addon..."
bashio::log.info "Input folder: ${INPUT_FOLDER}"
bashio::log.info "Output folder: ${OUTPUT_FOLDER}"
bashio::log.info "Resolution: ${RESOLUTION}"
bashio::log.info "Auto process: ${AUTO_PROCESS}"
bashio::log.info "Auto import: ${AUTO_IMPORT}"

# Start supervisor to manage nginx and the web app
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
