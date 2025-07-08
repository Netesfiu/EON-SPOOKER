"""
Data processing functionality for EON-SPOOKER
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .exceptions import DataValidationError

logger = logging.getLogger(__name__)


class DataProcessor:
    """Processes parsed CSV data and converts it to Home Assistant format"""
    
    def __init__(self, timezone_offset: Optional[str] = None):
        """
        Initialize data processor
        
        Args:
            timezone_offset: Custom timezone offset (e.g., '+02:00')
        """
        self.timezone_offset = timezone_offset or self._get_local_timezone_offset()
    
    def _get_local_timezone_offset(self) -> str:
        """Get local timezone offset in +HH:MM format"""
        tz_offset = datetime.now(timezone.utc).astimezone().strftime('%z')
        return f"{tz_offset[:3]}:{tz_offset[3:]}"
    
    def process_data(self, parsed_data: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """
        Process parsed data and convert to Home Assistant YAML format
        
        Args:
            parsed_data: Data from CSV parser
            
        Returns:
            Dictionary with 'import' and 'export' keys containing YAML-ready data
        """
        logger.info("Processing data for Home Assistant format")
        
        result = {}
        
        # Process import data
        if parsed_data['import_hourly']:
            if parsed_data['import_daily']:
                result['import'] = self._process_energy_data(
                    parsed_data['import_daily'],
                    parsed_data['import_hourly'],
                    'import'
                )
            else:
                logger.warning("Missing import daily data, using hourly data only")
                result['import'] = self._process_hourly_only_data(
                    parsed_data['import_hourly'],
                    'import'
                )
        else:
            logger.warning("Missing import hourly data")
            result['import'] = []
        
        # Process export data
        if parsed_data['export_hourly']:
            if parsed_data['export_daily']:
                result['export'] = self._process_energy_data(
                    parsed_data['export_daily'],
                    parsed_data['export_hourly'],
                    'export'
                )
            else:
                logger.warning("Missing export daily data, using hourly data only")
                result['export'] = self._process_hourly_only_data(
                    parsed_data['export_hourly'],
                    'export'
                )
        else:
            logger.warning("Missing export hourly data")
            result['export'] = []
        
        return result
    
    def _process_energy_data(self, daily_data: List[Dict], hourly_data: List[Dict], data_type: str) -> List[Dict]:
        """
        Process energy data for a specific type (import/export)
        
        Args:
            daily_data: Daily total readings
            hourly_data: Hourly consumption/generation data
            data_type: 'import' or 'export' for logging
            
        Returns:
            List of Home Assistant statistics entries
        """
        logger.info(f"Processing {data_type} data: {len(daily_data)} daily points, {len(hourly_data)} hourly points")
        
        if not daily_data:
            logger.warning(f"No daily data available for {data_type}")
            return []
        
        yaml_data = []
        
        # Sort data by timestamp
        daily_data.sort(key=lambda x: x['timestamp'])
        hourly_data.sort(key=lambda x: x['timestamp'])
        
        # Process each day
        for day_entry in daily_data:
            day_start = day_entry['timestamp']
            day_start_value = day_entry['value']
            
            # Find hourly values for this day
            day_hourly_values = [
                entry for entry in hourly_data 
                if entry['timestamp'].date() == day_start.date()
            ]
            
            if not day_hourly_values:
                logger.warning(f"No hourly data found for {day_start.date()}")
                continue
            
            # Process hourly data for this day
            cumulative_value = day_start_value
            
            for hourly_entry in day_hourly_values:
                timestamp = hourly_entry['timestamp']
                
                # Only process data at the top of each hour
                if timestamp.minute == 0:
                    yaml_entry = {
                        'start': f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')}{self.timezone_offset}",
                        'state': round(cumulative_value, 3),
                        'sum': round(cumulative_value, 3)
                    }
                    yaml_data.append(yaml_entry)
                
                # Add hourly consumption/generation to cumulative total
                cumulative_value += hourly_entry['value']
        
        logger.info(f"Generated {len(yaml_data)} {data_type} statistics entries")
        return yaml_data
    
    def _process_hourly_only_data(self, hourly_data: List[Dict], data_type: str) -> List[Dict]:
        """
        Process hourly data when daily totals are not available
        
        Args:
            hourly_data: Hourly consumption/generation data
            data_type: 'import' or 'export' for logging
            
        Returns:
            List of Home Assistant statistics entries
        """
        logger.info(f"Processing {data_type} hourly-only data: {len(hourly_data)} points")
        
        if not hourly_data:
            return []
        
        yaml_data = []
        
        # Sort data by timestamp
        hourly_data.sort(key=lambda x: x['timestamp'])
        
        # Start with cumulative value of 0
        cumulative_value = 0.0
        
        for hourly_entry in hourly_data:
            timestamp = hourly_entry['timestamp']
            
            # Only process data at the top of each hour
            if timestamp.minute == 0:
                # Add current hourly value to cumulative total
                cumulative_value += hourly_entry['value']
                
                yaml_entry = {
                    'start': f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')}{self.timezone_offset}",
                    'state': round(cumulative_value, 3),
                    'sum': round(cumulative_value, 3)
                }
                yaml_data.append(yaml_entry)
            else:
                # For non-hour entries, just add to cumulative
                cumulative_value += hourly_entry['value']
        
        logger.info(f"Generated {len(yaml_data)} {data_type} statistics entries from hourly data")
        return yaml_data
    
    def validate_processed_data(self, processed_data: Dict[str, List[Dict]]) -> None:
        """
        Validate processed data for common issues
        
        Args:
            processed_data: Processed data to validate
        """
        for data_type, entries in processed_data.items():
            if not entries:
                logger.warning(f"No processed data for {data_type}")
                continue
            
            # Check for duplicate timestamps
            timestamps = [entry['start'] for entry in entries]
            if len(timestamps) != len(set(timestamps)):
                raise DataValidationError(f"Duplicate timestamps found in {data_type} data")
            
            # Check for negative values
            negative_values = [entry for entry in entries if entry['sum'] < 0]
            if negative_values:
                logger.warning(f"Found {len(negative_values)} negative values in {data_type} data")
            
            # Check for reasonable value ranges
            values = [entry['sum'] for entry in entries]
            max_value = max(values)
            min_value = min(values)
            
            logger.info(f"{data_type} data range: {min_value:.3f} - {max_value:.3f} kWh")
            
            # Warn about unusually high values (>10000 kWh)
            if max_value > 10000:
                logger.warning(f"Unusually high energy value detected in {data_type}: {max_value:.3f} kWh")
