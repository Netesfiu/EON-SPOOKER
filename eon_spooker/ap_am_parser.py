"""
AP_AM format parser for EON-SPOOKER v3.0
Handles 15-minute interval data from email attachments
"""

import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from .exceptions import FileProcessingError

logger = logging.getLogger(__name__)


class APAMParser:
    """Parser for AP_AM format (15-minute interval data)"""
    
    def __init__(self):
        self.data = None
        self.metadata = {}
        
    def parse(self, file_path: str, delimiter: str = ';') -> Dict:
        """
        Parse AP_AM format CSV file
        
        Args:
            file_path: Path to the CSV file
            delimiter: CSV delimiter
            
        Returns:
            Dictionary containing parsed data and metadata
        """
        try:
            logger.info(f"Parsing AP_AM format file: {file_path}")
            
            # Read the full file
            df = pd.read_csv(file_path, delimiter=delimiter, encoding='utf-8-sig')
            
            # Note: ÖSSZEG and MAXIMUM values are discarded as per requirements
            summary_info = {}
            
            # Clean and process the data
            clean_data = self._clean_data(df)
            
            # Convert to time series format
            time_series_data = self._convert_to_time_series(clean_data)
            
            # Aggregate to hourly data (for HA compatibility)
            hourly_data = self._aggregate_to_hourly(time_series_data)
            
            # Calculate daily totals
            daily_data = self._calculate_daily_totals(time_series_data)
            
            result = {
                'format': 'ap_am',
                'summary': summary_info,
                'raw_data': time_series_data,
                'hourly_data': hourly_data,
                'daily_data': daily_data,
                'metadata': {
                    'file_path': file_path,
                    'total_records': len(time_series_data),
                    'date_range': self._get_date_range(time_series_data),
                    'interval_minutes': 15,
                    'data_columns': ['+A', '-A']
                }
            }
            
            logger.info(f"Successfully parsed {len(time_series_data)} records")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing AP_AM file: {e}")
            raise FileProcessingError(f"Failed to parse AP_AM file: {e}")
    
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
        
        # Remove rows that don't contain valid datetime data
        mask = pd.Series([True] * len(clean_df))
        
        for idx, row in clean_df.iterrows():
            first_col = str(row.iloc[0]).strip()
            
            # Skip summary rows
            if any(keyword in first_col.upper() for keyword in ['MAXIMUM', 'ÖSSZEG', 'SUM']):
                mask[idx] = False
                continue
            
            # Try to parse as datetime
            try:
                pd.to_datetime(first_col, format='%Y.%m.%d. %H:%M')
            except:
                mask[idx] = False
        
        clean_df = clean_df[mask].reset_index(drop=True)
        
        # Ensure we have the expected columns
        expected_cols = ['Dátum/Idő', '+A', '-A']
        if not all(col in clean_df.columns for col in expected_cols):
            raise FileProcessingError(f"Missing expected columns. Found: {clean_df.columns.tolist()}")
        
        return clean_df[expected_cols]
    
    def _convert_to_time_series(self, df: pd.DataFrame) -> List[Dict]:
        """Convert cleaned data to time series format"""
        
        time_series = []
        
        for _, row in df.iterrows():
            try:
                # Parse datetime
                dt_str = str(row['Dátum/Idő']).strip()
                dt = pd.to_datetime(dt_str, format='%Y.%m.%d. %H:%M')
                
                # Parse values
                import_val = self._safe_float(row['+A'])
                export_val = self._safe_float(row['-A'])
                
                if import_val is not None and export_val is not None:
                    time_series.append({
                        'datetime': dt,
                        'import_kwh': import_val,
                        'export_kwh': export_val,
                        'net_kwh': import_val - export_val
                    })
            
            except Exception as e:
                logger.warning(f"Skipping invalid row: {row.to_dict()} - {e}")
                continue
        
        # Sort by datetime
        time_series.sort(key=lambda x: x['datetime'])
        
        return time_series
    
    def _aggregate_to_hourly(self, time_series_data: List[Dict]) -> List[Dict]:
        """Aggregate 15-minute data to hourly intervals"""
        
        if not time_series_data:
            return []
        
        # Convert to DataFrame for easier aggregation
        df = pd.DataFrame(time_series_data)
        df['hour'] = df['datetime'].dt.floor('H')
        
        # Group by hour and sum the values
        hourly = df.groupby('hour').agg({
            'import_kwh': 'sum',
            'export_kwh': 'sum',
            'net_kwh': 'sum'
        }).reset_index()
        
        # Convert back to list of dictionaries
        hourly_data = []
        for _, row in hourly.iterrows():
            hourly_data.append({
                'datetime': row['hour'],
                'import_kwh': round(row['import_kwh'], 3),
                'export_kwh': round(row['export_kwh'], 3),
                'net_kwh': round(row['net_kwh'], 3)
            })
        
        return hourly_data
    
    def _calculate_daily_totals(self, time_series_data: List[Dict]) -> List[Dict]:
        """Calculate daily totals from time series data"""
        
        if not time_series_data:
            return []
        
        # Convert to DataFrame for easier aggregation
        df = pd.DataFrame(time_series_data)
        df['date'] = df['datetime'].dt.date
        
        # Group by date and sum the values
        daily = df.groupby('date').agg({
            'import_kwh': 'sum',
            'export_kwh': 'sum',
            'net_kwh': 'sum'
        }).reset_index()
        
        # Convert back to list of dictionaries
        daily_data = []
        for _, row in daily.iterrows():
            daily_data.append({
                'date': row['date'],
                'import_kwh': round(row['import_kwh'], 3),
                'export_kwh': round(row['export_kwh'], 3),
                'net_kwh': round(row['net_kwh'], 3)
            })
        
        return daily_data
    
    def _get_date_range(self, time_series_data: List[Dict]) -> Dict:
        """Get the date range of the data"""
        
        if not time_series_data:
            return {}
        
        dates = [record['datetime'] for record in time_series_data]
        return {
            'start': min(dates),
            'end': max(dates),
            'days': (max(dates) - min(dates)).days + 1
        }
    
    def _safe_float(self, value) -> Optional[float]:
        """Safely convert value to float"""
        try:
            if pd.isna(value) or value == '':
                return None
            return float(str(value).replace(',', '.'))
        except (ValueError, TypeError):
            return None


def parse_ap_am_file(file_path: str, delimiter: str = ';') -> Dict:
    """
    Convenience function to parse AP_AM format file
    
    Args:
        file_path: Path to the CSV file
        delimiter: CSV delimiter
        
    Returns:
        Parsed data dictionary
    """
    parser = APAMParser()
    return parser.parse(file_path, delimiter)


if __name__ == "__main__":
    # Test the parser
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        result = parse_ap_am_file(file_path)
        print(f"Parsed {result['metadata']['total_records']} records")
        print(f"Date range: {result['metadata']['date_range']}")
        print(f"Summary: {result['summary']}")
    else:
        print("Usage: python ap_am_parser.py <csv_file>")
