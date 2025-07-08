"""
Unified parser for EON-SPOOKER v3.0
Handles all EON data formats with auto-detection
"""

import logging
from typing import Dict, List, Optional, Union
from pathlib import Path

from .format_detector import detect_file_format, DataFormat
from .csv_parser import CSVParser  # Legacy parser
from .ap_am_parser import APAMParser
from .cumulative_parser import CumulativeParser
from .exceptions import FileProcessingError

logger = logging.getLogger(__name__)


class UnifiedParser:
    """Unified parser that can handle all EON data formats"""
    
    def __init__(self):
        # Note: Legacy parser will be instantiated per file due to constructor requirements
        self.parser_classes = {
            DataFormat.LEGACY: CSVParser,
            DataFormat.AP_AM: APAMParser,
            DataFormat.CUMULATIVE_180_280: CumulativeParser
        }
    
    def parse_file(self, file_path: str, delimiter: str = ';', format_override: Optional[str] = None) -> Dict:
        """
        Parse a single EON data file with automatic format detection
        
        Args:
            file_path: Path to the CSV file
            delimiter: CSV delimiter
            format_override: Override auto-detection with specific format
            
        Returns:
            Dictionary containing parsed data and metadata
        """
        try:
            logger.info(f"Parsing file: {file_path}")
            
            # Detect format unless overridden
            if format_override:
                try:
                    detected_format = DataFormat(format_override)
                    metadata = {'format': format_override}
                    logger.info(f"Using format override: {format_override}")
                except ValueError:
                    raise FileProcessingError(f"Invalid format override: {format_override}")
            else:
                detected_format, metadata = detect_file_format(file_path, delimiter)
            
            # Get appropriate parser class
            parser_class = self.parser_classes.get(detected_format)
            if not parser_class:
                raise FileProcessingError(f"No parser available for format: {detected_format.value}")
            
            # Parse the file
            if detected_format == DataFormat.LEGACY:
                # Legacy parser has different interface
                parser = parser_class(file_path, delimiter)
                result = parser.parse()
                # Standardize the result format
                result = self._standardize_legacy_result(result, file_path)
            else:
                # New parsers
                parser = parser_class()
                result = parser.parse(file_path, delimiter)
                
                # For cumulative format, use the actual cumulative readings for daily data
                if detected_format == DataFormat.CUMULATIVE_180_280 and 'cumulative_data' in result:
                    result['daily_data'] = result['cumulative_data']
            
            # Add detection metadata
            result['detection_metadata'] = metadata
            
            logger.info(f"Successfully parsed {file_path} as {detected_format.value}")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            raise FileProcessingError(f"Failed to parse file {file_path}: {e}")
    
    def parse_multiple_files(self, file_paths: List[str], delimiter: str = ';') -> Dict:
        """
        Parse multiple EON data files and combine results
        
        Args:
            file_paths: List of file paths to parse
            delimiter: CSV delimiter
            
        Returns:
            Dictionary containing combined parsed data
        """
        try:
            logger.info(f"Parsing {len(file_paths)} files")
            
            parsed_files = []
            combined_data = {
                'files': [],
                'formats': set(),
                'date_ranges': [],
                'total_records': 0,
                'hourly_data': [],
                'daily_data': [],
                'metadata': {
                    'file_count': len(file_paths),
                    'processing_errors': []
                }
            }
            
            for file_path in file_paths:
                try:
                    result = self.parse_file(file_path, delimiter)
                    parsed_files.append(result)
                    
                    # Track formats and metadata
                    combined_data['files'].append(file_path)
                    combined_data['formats'].add(result['format'])
                    combined_data['total_records'] += result['metadata'].get('total_records', 0)
                    
                    if 'date_range' in result['metadata']:
                        combined_data['date_ranges'].append(result['metadata']['date_range'])
                    
                    # Combine data
                    if 'hourly_data' in result:
                        combined_data['hourly_data'].extend(result['hourly_data'])
                    
                    if 'daily_data' in result:
                        combined_data['daily_data'].extend(result['daily_data'])
                
                except Exception as e:
                    error_msg = f"Error parsing {file_path}: {e}"
                    logger.warning(error_msg)
                    combined_data['metadata']['processing_errors'].append(error_msg)
            
            # Sort combined data by datetime
            if combined_data['hourly_data']:
                combined_data['hourly_data'].sort(key=lambda x: x['datetime'])
            
            if combined_data['daily_data']:
                # Handle mixed datetime/date types
                def get_sort_key(record):
                    dt = record.get('datetime', record.get('date'))
                    if hasattr(dt, 'date'):  # It's a datetime/Timestamp
                        return dt
                    else:  # It's a date
                        import pandas as pd
                        return pd.Timestamp(dt)
                
                combined_data['daily_data'].sort(key=get_sort_key)
            
            # Calculate overall date range
            if combined_data['date_ranges']:
                all_starts = [dr['start'] for dr in combined_data['date_ranges'] if 'start' in dr]
                all_ends = [dr['end'] for dr in combined_data['date_ranges'] if 'end' in dr]
                
                if all_starts and all_ends:
                    combined_data['metadata']['overall_date_range'] = {
                        'start': min(all_starts),
                        'end': max(all_ends)
                    }
            
            combined_data['formats'] = list(combined_data['formats'])
            combined_data['parsed_files'] = parsed_files
            
            logger.info(f"Successfully combined data from {len(parsed_files)} files")
            return combined_data
            
        except Exception as e:
            logger.error(f"Error parsing multiple files: {e}")
            raise FileProcessingError(f"Failed to parse multiple files: {e}")
    
    def _standardize_legacy_result(self, legacy_result: Dict, file_path: str) -> Dict:
        """Standardize legacy parser result to match new format"""
        
        # Convert legacy format to standardized format
        standardized = {
            'format': 'legacy',
            'summary': {},
            'hourly_data': [],
            'daily_data': [],
            'metadata': {
                'file_path': file_path,
                'total_records': 0,
                'interval_type': 'mixed',
                'data_columns': ['Value [kWh]']
            }
        }
        
        # Extract data from legacy result
        if 'data' in legacy_result:
            data = legacy_result['data']
            
            # Convert to hourly/daily format
            hourly_records = []
            daily_records = []
            
            for pod_name, pod_data in data.items():
                for variable, time_series in pod_data.items():
                    for time_str, value in time_series.items():
                        try:
                            # Try to parse datetime and categorize
                            import pandas as pd
                            dt = pd.to_datetime(time_str)
                            
                            record = {
                                'datetime': dt,
                                'pod_name': pod_name,
                                'variable': variable,
                                'value_kwh': float(value) if value else 0.0
                            }
                            
                            # Categorize by time resolution
                            if dt.minute == 0 and dt.second == 0:
                                if 'hour' in variable.lower() or 'órás' in variable.lower():
                                    hourly_records.append(record)
                                elif 'day' in variable.lower() or 'napi' in variable.lower():
                                    daily_records.append(record)
                                else:
                                    hourly_records.append(record)  # Default to hourly
                        
                        except Exception as e:
                            logger.warning(f"Skipping invalid legacy record: {e}")
                            continue
            
            standardized['hourly_data'] = hourly_records
            standardized['daily_data'] = daily_records
            standardized['metadata']['total_records'] = len(hourly_records) + len(daily_records)
        
        return standardized


def parse_eon_file(file_path: str, delimiter: str = ';', format_override: Optional[str] = None) -> Dict:
    """
    Convenience function to parse a single EON file
    
    Args:
        file_path: Path to the CSV file
        delimiter: CSV delimiter
        format_override: Override auto-detection with specific format
        
    Returns:
        Parsed data dictionary
    """
    parser = UnifiedParser()
    return parser.parse_file(file_path, delimiter, format_override)


def parse_eon_files(file_paths: List[str], delimiter: str = ';') -> Dict:
    """
    Convenience function to parse multiple EON files
    
    Args:
        file_paths: List of file paths to parse
        delimiter: CSV delimiter
        
    Returns:
        Combined parsed data dictionary
    """
    parser = UnifiedParser()
    return parser.parse_multiple_files(file_paths, delimiter)


if __name__ == "__main__":
    # Test the unified parser
    import sys
    
    if len(sys.argv) > 1:
        file_paths = sys.argv[1:]
        
        if len(file_paths) == 1:
            result = parse_eon_file(file_paths[0])
            print(f"Format: {result['format']}")
            print(f"Records: {result['metadata']['total_records']}")
            if 'date_range' in result['metadata']:
                print(f"Date range: {result['metadata']['date_range']}")
        else:
            result = parse_eon_files(file_paths)
            print(f"Formats: {result['formats']}")
            print(f"Total records: {result['total_records']}")
            print(f"Files processed: {len(result['files'])}")
    else:
        print("Usage: python unified_parser.py <csv_file1> [csv_file2] ...")
