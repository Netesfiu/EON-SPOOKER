"""
Format detection module for EON-SPOOKER v3.0
Automatically detects different EON data formats
"""

import pandas as pd
import logging
from typing import Tuple, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class DataFormat(Enum):
    """Supported data formats"""
    LEGACY = "legacy"           # Original web portal format
    AP_AM = "ap_am"            # 15-minute interval data
    CUMULATIVE_180_280 = "180_280"  # Daily cumulative readings
    UNKNOWN = "unknown"


class FormatDetector:
    """Detects EON data format from CSV files"""
    
    def __init__(self):
        self.format_signatures = {
            DataFormat.LEGACY: {
                'required_columns': ['POD Name', 'Variable name', 'Time', 'Value [kWh]'],
                'optional_columns': [],
                'row_patterns': []
            },
            DataFormat.AP_AM: {
                'required_columns': ['Dátum/Idő', '+A', '-A'],
                'optional_columns': [],
                'row_patterns': ['MAXIMUM ÉRTÉK', 'ÖSSZEG']
            },
            DataFormat.CUMULATIVE_180_280: {
                'required_columns': ['Dátum'],
                'optional_columns': ['DP_1-1:1.8.0*0', 'DP_1-1:2.8.0*0'],
                'row_patterns': ['MAXIMUM ÉRTÉK', 'ÖSSZEG']
            }
        }
    
    def detect_format(self, file_path: str, delimiter: str = ';') -> Tuple[DataFormat, dict]:
        """
        Detect the format of a CSV file
        
        Args:
            file_path: Path to the CSV file
            delimiter: CSV delimiter to use
            
        Returns:
            Tuple of (detected_format, metadata)
        """
        try:
            # Read first few rows to analyze structure
            df_sample = pd.read_csv(file_path, delimiter=delimiter, nrows=10, encoding='utf-8-sig')
            
            # Get column names
            columns = [col.strip() for col in df_sample.columns]
            
            logger.debug(f"Detected columns: {columns}")
            
            # Check for each format
            for format_type, signature in self.format_signatures.items():
                if self._matches_signature(columns, df_sample, signature):
                    metadata = self._extract_metadata(df_sample, format_type)
                    logger.info(f"Detected format: {format_type.value}")
                    return format_type, metadata
            
            logger.warning("Could not detect format, defaulting to UNKNOWN")
            return DataFormat.UNKNOWN, {}
            
        except Exception as e:
            logger.error(f"Error detecting format: {e}")
            return DataFormat.UNKNOWN, {}
    
    def _matches_signature(self, columns: list, df_sample: pd.DataFrame, signature: dict) -> bool:
        """Check if columns and data match a format signature"""
        
        # Check required columns
        required_cols = signature['required_columns']
        if not all(col in columns for col in required_cols):
            return False
        
        # For 180_280 format, check for DP columns (they have dynamic names)
        if signature == self.format_signatures[DataFormat.CUMULATIVE_180_280]:
            has_dp_columns = any('DP_' in col and ':' in col for col in columns)
            if not has_dp_columns:
                return False
        
        # Check for pattern rows (like MAXIMUM ÉRTÉK, ÖSSZEG)
        if signature['row_patterns']:
            first_column_values = df_sample.iloc[:, 0].astype(str).tolist()
            pattern_found = any(pattern in ' '.join(first_column_values) for pattern in signature['row_patterns'])
            if not pattern_found:
                return False
        
        return True
    
    def _extract_metadata(self, df_sample: pd.DataFrame, format_type: DataFormat) -> dict:
        """Extract metadata specific to the detected format"""
        metadata = {
            'format': format_type.value,
            'columns': df_sample.columns.tolist(),
            'sample_rows': len(df_sample)
        }
        
        if format_type == DataFormat.AP_AM:
            # Extract date range and interval info
            metadata.update({
                'interval_type': '15_minute',
                'has_summary_rows': True,
                'data_columns': ['+A', '-A']
            })
        
        elif format_type == DataFormat.CUMULATIVE_180_280:
            # Extract DP column information
            dp_columns = [col for col in df_sample.columns if 'DP_' in col and ':' in col]
            metadata.update({
                'interval_type': 'daily',
                'has_summary_rows': True,
                'data_columns': dp_columns,
                'cumulative_data': True
            })
        
        elif format_type == DataFormat.LEGACY:
            metadata.update({
                'interval_type': 'mixed',
                'has_summary_rows': False,
                'data_columns': ['Value [kWh]']
            })
        
        return metadata
    
    def get_recommended_parser(self, format_type: DataFormat) -> str:
        """Get the recommended parser class for a format"""
        parser_map = {
            DataFormat.LEGACY: 'LegacyCSVParser',
            DataFormat.AP_AM: 'APAMParser',
            DataFormat.CUMULATIVE_180_280: 'CumulativeParser',
            DataFormat.UNKNOWN: 'LegacyCSVParser'  # Fallback
        }
        return parser_map.get(format_type, 'LegacyCSVParser')


def detect_file_format(file_path: str, delimiter: str = ';') -> Tuple[DataFormat, dict]:
    """
    Convenience function to detect file format
    
    Args:
        file_path: Path to the CSV file
        delimiter: CSV delimiter
        
    Returns:
        Tuple of (format, metadata)
    """
    detector = FormatDetector()
    return detector.detect_format(file_path, delimiter)


if __name__ == "__main__":
    # Test the detector
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        format_type, metadata = detect_file_format(file_path)
        print(f"Format: {format_type.value}")
        print(f"Metadata: {metadata}")
    else:
        print("Usage: python format_detector.py <csv_file>")
