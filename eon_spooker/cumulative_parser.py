"""
Cumulative format parser for EON-SPOOKER v3.0
Handles daily cumulative readings (180_280 format) from email attachments
Uses the same calculation method as the original EON_SPOOKER.py script
"""

import pandas as pd
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Optional
from .exceptions import FileProcessingError

logger = logging.getLogger(__name__)


class CumulativeParser:
    """Parser for cumulative format (daily readings) - matches original script logic"""
    
    def __init__(self):
        self.data = None
        self.metadata = {}
        
    def parse(self, file_path: str, delimiter: str = ';') -> Dict:
        """
        Parse cumulative format CSV file using original script logic
        
        Args:
            file_path: Path to the CSV file
            delimiter: CSV delimiter
            
        Returns:
            Dictionary containing parsed data and metadata
        """
        try:
            logger.info(f"Parsing cumulative format file: {file_path}")
            
            # Read the full file
            df = pd.read_csv(file_path, delimiter=delimiter, encoding='utf-8-sig')
            
            # Extract data using original script logic
            data_dp_ap = self._process_data(df, "'DP_1-1:1.8.0*0'", "import daily data")
            data_dp_an = self._process_data(df, "'DP_1-1:2.8.0*0'", "export daily data")
            
            # For this format, we need to load the corresponding AP_AM data
            # Since we don't have it here, we'll create empty consumption data
            # This will be handled by the unified parser when both files are available
            data_ap = []  # Import consumption data (from AP_AM file)
            data_an = []  # Export consumption data (from AP_AM file)
            
            result = {
                'format': 'cumulative_180_280',
                'daily_cumulative': {
                    'import': data_dp_ap,
                    'export': data_dp_an
                },
                'consumption_data': {
                    'import': data_ap,
                    'export': data_an
                },
                'metadata': {
                    'file_path': file_path,
                    'total_records': len(data_dp_ap) + len(data_dp_an),
                    'date_range': self._get_date_range(data_dp_ap + data_dp_an),
                    'interval_type': 'daily',
                    'cumulative_data': True,
                    'data_columns': ['DP_1-1:1.8.0*0', 'DP_1-1:2.8.0*0']
                }
            }
            
            logger.info(f"Successfully parsed {len(data_dp_ap)} cumulative records")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing cumulative file: {e}")
            raise FileProcessingError(f"Failed to parse cumulative file: {e}")
    
    def _process_data(self, df: pd.DataFrame, filter_condition: str, desc: str) -> List[Dict]:
        """
        Process data using original script logic
        Looks for rows where the variable name matches the filter condition
        """
        filtered_data = []
        
        # Get headers
        headers = df.columns.tolist()
        
        # Find the column that contains the variable names
        variable_col = None
        time_col = None
        value_col = None
        
        # For 180_280 format, the structure is: Dátum, DP_1-1:1.8.0*0, DP_1-1:2.8.0*0
        if len(headers) >= 3:
            time_col = headers[0]  # Date column
            
            # Find the matching data column
            target_col = filter_condition.strip("'")
            if target_col in headers:
                value_col = target_col
        
        if time_col is None or value_col is None:
            logger.warning(f"Could not find required columns for {desc}")
            return filtered_data
        
        # Process each row
        for _, row in df.iterrows():
            try:
                time_str = str(row[time_col]).strip()
                
                # Skip summary rows
                if any(keyword in time_str.upper() for keyword in ['MAXIMUM', 'ÖSSZEG', 'SUM']):
                    continue
                
                # Parse date
                try:
                    date_obj = pd.to_datetime(time_str, format='%Y.%m.%d.')
                except:
                    continue  # Skip invalid dates
                
                # Get value
                value = self._safe_float(row[value_col])
                if value is not None:
                    filtered_data.append({
                        "start": date_obj,
                        "value": value
                    })
            
            except Exception as e:
                logger.debug(f"Skipping row in {desc}: {e}")
                continue
        
        return filtered_data
    
    def process_day_data(self, day_data: List[Dict], filter_data: List[Dict], desc: str) -> List[Dict]:
        """
        Process day data using original script logic
        This combines daily cumulative readings with consumption data to create hourly cumulative values
        """
        yaml_data = []
        
        for day in day_data:
            day_start = day["start"]
            day_values = [value for value in filter_data if value["start"].date() == day_start.date()]
            day_start_value = day["value"]
            prev_value = day_start_value
            
            for i in day_values:
                timestamp = i["start"]
                if timestamp.minute == 0:  # Only process hourly data
                    # Get local timezone offset
                    tz_offset = datetime.now(timezone.utc).astimezone().strftime('%z')
                    tz_offset = f"{tz_offset[:3]}:{tz_offset[3:]}"  # Insert colon between hours and minutes
                    
                    yaml_data.append({
                        'start': f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')}{tz_offset}",
                        'state': round(prev_value, 2),
                        'sum': round(prev_value, 2)
                    })
                prev_value += i["value"]
        
        return yaml_data
    
    def generate_yaml_data(self, consumption_import: List[Dict], consumption_export: List[Dict]) -> Dict:
        """
        Generate YAML data using original script logic
        This requires both cumulative readings and consumption data
        """
        if not hasattr(self, 'daily_cumulative'):
            return {'import': [], 'export': []}
        
        # Use original script logic
        yaml_data_import = self.process_day_data(
            self.daily_cumulative['import'], 
            consumption_import, 
            "import"
        )
        yaml_data_export = self.process_day_data(
            self.daily_cumulative['export'], 
            consumption_export, 
            "export"
        )
        
        return {
            'import': yaml_data_import,
            'export': yaml_data_export
        }
    
    def _get_date_range(self, data: List[Dict]) -> Dict:
        """Get the date range of the data"""
        
        if not data:
            return {}
        
        dates = [record['start'] for record in data]
        return {
            'start': min(dates),
            'end': max(dates),
            'days': len(data)
        }
    
    def _safe_float(self, value) -> Optional[float]:
        """Safely convert value to float"""
        try:
            if pd.isna(value) or value == '':
                return None
            return float(str(value).replace(',', '.'))
        except (ValueError, TypeError):
            return None


def parse_cumulative_file(file_path: str, delimiter: str = ';') -> Dict:
    """
    Convenience function to parse cumulative format file
    
    Args:
        file_path: Path to the CSV file
        delimiter: CSV delimiter
        
    Returns:
        Parsed data dictionary
    """
    parser = CumulativeParser()
    return parser.parse(file_path, delimiter)


if __name__ == "__main__":
    # Test the parser
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        result = parse_cumulative_file(file_path)
        print(f"Parsed {result['metadata']['total_records']} cumulative records")
        print(f"Date range: {result['metadata']['date_range']}")
    else:
        print("Usage: python cumulative_parser.py <csv_file>")
