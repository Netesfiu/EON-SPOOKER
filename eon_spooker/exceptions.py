"""
Custom exceptions for EON-SPOOKER
"""


class EONSpookerError(Exception):
    """Base exception for EON-SPOOKER errors"""
    pass


class CSVFormatError(EONSpookerError):
    """Raised when CSV file format is invalid or unexpected"""
    pass


class DataValidationError(EONSpookerError):
    """Raised when data validation fails"""
    pass


class FileProcessingError(EONSpookerError):
    """Raised when file processing encounters an error"""
    pass


class ConfigurationError(EONSpookerError):
    """Raised when configuration is invalid"""
    pass
