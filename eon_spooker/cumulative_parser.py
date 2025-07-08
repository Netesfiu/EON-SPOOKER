"""
Cumulative format parser for EON-SPOOKER v3.0
Handles daily cumulative readings (180_280 format) from email attachments
"""

import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from .exceptions import FileProcessingError

logger = logging.getLogger(__name__)


class CumulativeParser:
    """Parser for cumulative format (daily readings)"""
    
    def __init__(self):
        self.data = None
        self.metadata = {}
        
    def parse(self, file_path: str, delimiter: str = ';') -> Dict:
        """
        Parse cumulative format CSV file
        
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
            
            # Note: ÖSSZEG and MAXIMUM values are discarded as per requirements
            summary_info = {}
            
            # Clean and process the data
            clean_data = self._clean_data(df)
            
            # Convert to time series format
            cumulative_data = self._convert_to_cumulative_series(clean_data)
            
            # Store cumulative data for use in hourly distribution
            self.cumulative_data = cumulative_data
            
            # Calculate daily consumption from cumulative readings
            daily_consumption = self._calculate_daily_consumption(cumulative_data)
            
            # Generate hourly data (distributed evenly across 24 hours)
            hourly_data = self._distribute_to_hourly(daily_consumption)
            
            result = {
                'format': 'cumulative_180_280',
                'summary': summary_info,
                'cumulative_data': cumulative_data,
                'daily_data': daily_consumption,
                'hourly_data': hourly_data,
                'metadata': {
                    'file_path': file_path,
                    'total_records': len(cumulative_data),
                    'date_range': self._get_date_range(cumulative_data),
                    'interval_type': 'daily',
                    'data_columns': self._get_data_columns(clean_data)
                }
            }
            
            logger.info(f"Successfully parsed {len(cumulative_data)} cumulative records")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing cumulative file: {e}")
            raise FileProcessingError(f"Failed to parse cumulative file: {e}")
    
    def _extract_summary_info(self, df: pd.DataFrame) -> Dict:
        """Extract summary information from header rows"""
        summary = {}
        
        try:
            # Look for MAXIMUM ÉRTÉK and ÖSSZEG rows
            for idx, row in df.iterrows():
                first_col = str(row.iloc[0]).strip()
                
                if 'MAXIMUM' in first_col.upper():
                    summary['maximum_import'] = self._safe_float(row.iloc[1]) if len(row) > 1 else None
                    summary['maximum_export'] = self._safe_float(row.iloc[2]) if len(row) > 2 else None
                
                elif 'ÖSSZEG' in first_col.upper() or 'SUM' in first_col.upper():
                    summary['total_import'] = self._safe_float(row.iloc[1]) if len(row) > 1 else None
                    summary['total_export'] = self._safe_float(row.iloc[2]) if len(row) > 2 else None
        
        except Exception as e:
            logger.warning(f"Could not extract summary info: {e}")
        
        return summary
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean the data by removing summary rows and invalid entries"""
        
        # Create a copy to work with
        clean_df = df.copy()
        
        # Remove rows that don't contain valid date data
        mask = pd.Series([True] * len(clean_df))
        
        for idx, row in clean_df.iterrows():
            first_col = str(row.iloc[0]).strip()
            
            # Skip summary rows
            if any(keyword in first_col.upper() for keyword in ['MAXIMUM', 'ÖSSZEG', 'SUM']):
                mask[idx] = False
                continue
            
            # Try to parse as date
            try:
                pd.to_datetime(first_col, format='%Y.%m.%d.')
            except:
                mask[idx] = False
        
        clean_df = clean_df[mask].reset_index(drop=True)
        
        # Ensure we have at least the date column
        if len(clean_df.columns) < 2:
            raise FileProcessingError(f"Insufficient columns in data. Found: {clean_df.columns.tolist()}")
        
        return clean_df
    
    def _get_data_columns(self, df: pd.DataFrame) -> List[str]:
        """Get the data columns (DP columns)"""
        data_cols = []
        for col in df.columns:
            if 'DP_' in col and ':' in col:
                data_cols.append(col)
        return data_cols
    
    def _convert_to_cumulative_series(self, df: pd.DataFrame) -> List[Dict]:
        """Convert cleaned data to cumulative time series format"""
        
        time_series = []
        data_columns = self._get_data_columns(df)
        
        for _, row in df.iterrows():
            try:
                # Parse date
                date_str = str(row.iloc[0]).strip()
                date = pd.to_datetime(date_str, format='%Y.%m.%d.').date()
                
                # Parse cumulative values - these are actual meter readings
                record = {
                    'date': date,
                    'datetime': pd.to_datetime(date_str, format='%Y.%m.%d.')
                }
                
                # Extract import and export values (actual cumulative meter readings)
                if len(data_columns) >= 2:
                    import_col = data_columns[0]  # Usually DP_1-1:1.8.0*0
                    export_col = data_columns[1]  # Usually DP_1-1:2.8.0*0
                    
                    import_val = self._safe_float(row[import_col])
                    export_val = self._safe_float(row[export_col])
                    
                    if import_val is not None and export_val is not None:
                        record.update({
                            'cumulative_import_kwh': import_val,
                            'cumulative_export_kwh': export_val,
                            'cumulative_net_kwh': import_val - export_val,
                            # Also store as import/export for YAML compatibility
                            'import_kwh': import_val,
                            'export_kwh': export_val
                        })
                        time_series.append(record)
            
            except Exception as e:
                logger.warning(f"Skipping invalid row: {row.to_dict()} - {e}")
                continue
        
        # Sort by date
        time_series.sort(key=lambda x: x['date'])
        
        return time_series
    
    def _calculate_daily_consumption(self, cumulative_data: List[Dict]) -> List[Dict]:
        """Calculate daily consumption from cumulative readings"""
        
        if len(cumulative_data) < 2:
            logger.warning("Not enough data points to calculate daily consumption")
            return []
        
        daily_consumption = []
        
        for i in range(1, len(cumulative_data)):
            current = cumulative_data[i]
            previous = cumulative_data[i-1]
            
            # Calculate daily consumption as difference between consecutive readings
            import_consumption = current['cumulative_import_kwh'] - previous['cumulative_import_kwh']
            export_consumption = current['cumulative_export_kwh'] - previous['cumulative_export_kwh']
            net_consumption = import_consumption - export_consumption
            
            daily_consumption.append({
                'date': current['date'],
                'datetime': current['datetime'],
                'import_kwh': round(max(0, import_consumption), 3),  # Ensure non-negative
                'export_kwh': round(max(0, export_consumption), 3),  # Ensure non-negative
                'net_kwh': round(net_consumption, 3)
            })
        
        return daily_consumption
    
    def _distribute_to_hourly(self, daily_data: List[Dict]) -> List[Dict]:
        """Distribute daily consumption evenly across 24 hours with cumulative tracking"""
        
        hourly_data = []
        
        # Get the starting cumulative values from the first day's readings
        if not daily_data:
            return hourly_data
        
        # Find the first cumulative reading to use as starting point
        first_cumulative = None
        if hasattr(self, 'cumulative_data') and self.cumulative_data:
            first_cumulative = self.cumulative_data[0]
        
        # Initialize cumulative counters with the first meter reading
        if first_cumulative:
            cumulative_import = first_cumulative['cumulative_import_kwh']
            cumulative_export = first_cumulative['cumulative_export_kwh']
        else:
            # Fallback to zero if no cumulative data found
            cumulative_import = 0.0
            cumulative_export = 0.0
        
        for day_record in daily_data:
            daily_import = day_record['import_kwh']
            daily_export = day_record['export_kwh']
            daily_net = day_record['net_kwh']
            
            # Distribute evenly across 24 hours
            hourly_import = daily_import / 24
            hourly_export = daily_export / 24
            hourly_net = daily_net / 24
            
            # Create 24 hourly records for this day
            base_date = day_record['datetime']
            
            for hour in range(24):
                hour_datetime = base_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                
                # Add hourly consumption to cumulative totals
                cumulative_import += hourly_import
                cumulative_export += hourly_export
                
                hourly_data.append({
                    'datetime': hour_datetime,
                    'import_kwh': round(hourly_import, 3),
                    'export_kwh': round(hourly_export, 3),
                    'net_kwh': round(hourly_net, 3),
                    # Store cumulative values for YAML generation
                    'cumulative_import_kwh': round(cumulative_import, 3),
                    'cumulative_export_kwh': round(cumulative_export, 3)
                })
        
        return hourly_data
    
    def _get_date_range(self, cumulative_data: List[Dict]) -> Dict:
        """Get the date range of the data"""
        
        if not cumulative_data:
            return {}
        
        dates = [record['datetime'] for record in cumulative_data]
        return {
            'start': min(dates),
            'end': max(dates),
            'days': len(cumulative_data)
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
        print(f"Generated {len(result['daily_data'])} daily consumption records")
        print(f"Date range: {result['metadata']['date_range']}")
        print(f"Summary: {result['summary']}")
    else:
        print("Usage: python cumulative_parser.py <csv_file>")
