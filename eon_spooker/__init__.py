"""
EON-SPOOKER v3.0: Professional Python package for EON energy data processing
Converts EON energy data files to formats suitable for Home Assistant and other systems
"""

__version__ = "3.0.0"
__author__ = "EON-SPOOKER Contributors"
__description__ = "Professional Python package for processing EON energy data files"

# Import main functions and classes for easy access
from .unified_parser import (
    UnifiedParser,
    parse_eon_file,
    parse_eon_files
)

from .format_detector import (
    detect_file_format,
    DataFormat
)

from .yaml_generator import YAMLGenerator

from .exceptions import (
    FileProcessingError,
    DataValidationError,
    CSVFormatError,
    ConfigurationError,
    EONSpookerError
)

# Import individual parsers for advanced usage
from .csv_parser import CSVParser
from .ap_am_parser import APAMParser
from .cumulative_parser import CumulativeParser

# Export all main components
__all__ = [
    # Main API functions
    'parse_eon_file',
    'parse_eon_files',
    'detect_file_format',
    
    # Main classes
    'UnifiedParser',
    'YAMLGenerator',
    
    # Data formats
    'DataFormat',
    
    # Exceptions
    'FileProcessingError',
    'DataValidationError',
    'CSVFormatError',
    'ConfigurationError',
    'EONSpookerError',
    
    # Individual parsers (for advanced usage)
    'CSVParser',
    'APAMParser',
    'CumulativeParser',
]

# Package metadata
__title__ = "EON-SPOOKER"
__summary__ = "Professional Python package for processing EON energy data files"
__uri__ = "https://github.com/Netesfiu/EON-SPOOKER"
__license__ = "MIT"
