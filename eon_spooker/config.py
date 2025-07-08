"""
Configuration constants and settings for EON-SPOOKER
"""

from typing import Dict, List

# CSV column names
CSV_COLUMNS = {
    'POD_NAME': 'POD Name',
    'VARIABLE_NAME': 'Variable name',
    'TIME': 'Time',
    'VALUE': 'Value [kWh]'
}

# Variable name filters for different data types
VARIABLE_FILTERS = {
    'IMPORT_HOURLY': "'+A'",
    'EXPORT_HOURLY': "'-A'",
    'IMPORT_DAILY': "'DP_1-1:1.8.0*0'",
    'EXPORT_DAILY': "'DP_1-1:2.8.0*0'"
}

# Date/time format used in E.ON CSV files
DATETIME_FORMAT = "%Y.%m.%d %H:%M:%S"

# Default output filenames
DEFAULT_OUTPUT_FILES = {
    'import': 'import.yaml',
    'export': 'export.yaml'
}

# Supported CSV delimiters
SUPPORTED_DELIMITERS = [';', ',', '\t']

# Default timezone offset format
DEFAULT_TIMEZONE_FORMAT = "%z"
