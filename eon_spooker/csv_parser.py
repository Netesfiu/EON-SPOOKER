"""
CSV parsing functionality for EON-SPOOKER
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .config import CSV_COLUMNS, DATETIME_FORMAT, SUPPORTED_DELIMITERS, VARIABLE_FILTERS
from .exceptions import CSVFormatError, DataValidationError, FileProcessingError

logger = logging.getLogger(__name__)


class CSVParser:
    """Handles parsing and validation of E.ON W1000 CSV files"""
    
    def __init__(self, file_path: str, delimiter: Optional[str] = None):
        """
        Initialize CSV parser
        
        Args:
            file_path: Path to the CSV file
            delimiter: CSV delimiter (auto-detected if None)
        """
        self.file_path = Path(file_path)
        self.delimiter = delimiter
        self._validate_file()
        
    def _validate_file(self) -> None:
        """Validate that the file exists and is readable"""
        if not self.file_path.exists():
            raise FileProcessingError(f"File not found: {self.file_path}")
        
        if not self.file_path.is_file():
            raise FileProcessingError(f"Path is not a file: {self.file_path}")
        
        if self.file_path.suffix.lower() != '.csv':
            logger.warning(f"File does not have .csv extension: {self.file_path}")
    
    def _detect_delimiter(self) -> str:
        """Auto-detect CSV delimiter"""
        try:
            with open(self.file_path, 'r', encoding='utf-8-sig') as file:
                sample = file.read(1024)
                sniffer = csv.Sniffer()
                
                # Try to detect delimiter
                try:
                    dialect = sniffer.sniff(sample, delimiters=''.join(SUPPORTED_DELIMITERS))
                    return dialect.delimiter
                except csv.Error:
                    # Fallback: count occurrences of each delimiter
                    delimiter_counts = {delim: sample.count(delim) for delim in SUPPORTED_DELIMITERS}
                    return max(delimiter_counts, key=delimiter_counts.get)
                    
        except Exception as e:
            raise FileProcessingError(f"Failed to detect CSV delimiter: {e}")
    
    def _validate_headers(self, headers: List[str]) -> None:
        """Validate that CSV has required headers"""
        required_columns = set(CSV_COLUMNS.values())
        actual_columns = set(headers)
        
        missing_columns = required_columns - actual_columns
        if missing_columns:
            raise CSVFormatError(f"Missing required columns: {missing_columns}")
        
        logger.info(f"CSV validation passed. Found columns: {headers}")
    
    def _parse_datetime(self, datetime_str: str) -> datetime:
        """Parse datetime string from CSV"""
        try:
            return datetime.strptime(datetime_str, DATETIME_FORMAT)
        except ValueError as e:
            raise DataValidationError(f"Invalid datetime format '{datetime_str}': {e}")
    
    def _parse_value(self, value_str: str) -> float:
        """Parse numeric value from CSV"""
        try:
            return float(value_str)
        except ValueError as e:
            raise DataValidationError(f"Invalid numeric value '{value_str}': {e}")
    
    def parse(self) -> Dict[str, List[Dict]]:
        """
        Parse CSV file and return structured data
        
        Returns:
            Dictionary with keys for each data type containing lists of data points
        """
        if not self.delimiter:
            self.delimiter = self._detect_delimiter()
        
        logger.info(f"Parsing CSV file: {self.file_path} with delimiter '{self.delimiter}'")
        
        # Initialize data containers
        data = {
            'import_hourly': [],
            'export_hourly': [],
            'import_daily': [],
            'export_daily': []
        }
        
        try:
            with open(self.file_path, 'r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file, delimiter=self.delimiter)
                
                # Validate headers
                self._validate_headers(reader.fieldnames)
                
                # Process each row
                row_count = 0
                for row in reader:
                    row_count += 1
                    try:
                        self._process_row(row, data)
                    except (DataValidationError, ValueError) as e:
                        logger.warning(f"Skipping invalid row {row_count}: {e}")
                        continue
                
                logger.info(f"Successfully parsed {row_count} rows")
                
        except Exception as e:
            raise FileProcessingError(f"Failed to parse CSV file: {e}")
        
        # Validate parsed data
        self._validate_parsed_data(data)
        
        return data
    
    def _process_row(self, row: Dict[str, str], data: Dict[str, List[Dict]]) -> None:
        """Process a single CSV row"""
        variable_name = row[CSV_COLUMNS['VARIABLE_NAME']]
        timestamp = self._parse_datetime(row[CSV_COLUMNS['TIME']])
        value = self._parse_value(row[CSV_COLUMNS['VALUE']])
        
        # Create data point
        data_point = {
            'timestamp': timestamp,
            'value': value,
            'pod_name': row[CSV_COLUMNS['POD_NAME']]
        }
        
        # Categorize by variable name
        if variable_name == VARIABLE_FILTERS['IMPORT_HOURLY']:
            data['import_hourly'].append(data_point)
        elif variable_name == VARIABLE_FILTERS['EXPORT_HOURLY']:
            data['export_hourly'].append(data_point)
        elif variable_name == VARIABLE_FILTERS['IMPORT_DAILY']:
            data['import_daily'].append(data_point)
        elif variable_name == VARIABLE_FILTERS['EXPORT_DAILY']:
            data['export_daily'].append(data_point)
        else:
            logger.debug(f"Unknown variable name: {variable_name}")
    
    def _validate_parsed_data(self, data: Dict[str, List[Dict]]) -> None:
        """Validate the parsed data structure"""
        for data_type, data_points in data.items():
            if not data_points:
                logger.warning(f"No data found for {data_type}")
                continue
            
            # Sort by timestamp
            data_points.sort(key=lambda x: x['timestamp'])
            
            logger.info(f"Found {len(data_points)} data points for {data_type}")
            logger.debug(f"{data_type} date range: {data_points[0]['timestamp']} to {data_points[-1]['timestamp']}")
