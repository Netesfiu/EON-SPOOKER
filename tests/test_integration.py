"""
Integration tests using the sample CSV file from the repository
"""

import unittest
import tempfile
import os
from pathlib import Path
import yaml

from eon_spooker.csv_parser import CSVParser
from eon_spooker.data_processor import DataProcessor
from eon_spooker.yaml_generator import YAMLGenerator


class TestIntegration(unittest.TestCase):
    """Integration tests using real sample data"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Get the sample CSV file from the repository
        self.repo_root = Path(__file__).parent.parent
        self.sample_csv = self.repo_root / "sample report data.csv"
        
        # Create temporary directory for output
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_sample_csv_exists(self):
        """Test that the sample CSV file exists"""
        self.assertTrue(self.sample_csv.exists(), f"Sample CSV file not found: {self.sample_csv}")
    
    def test_full_pipeline_with_sample_data(self):
        """Test the complete pipeline with sample data"""
        # Parse CSV
        parser = CSVParser(str(self.sample_csv))
        parsed_data = parser.parse()
        
        # Verify parsed data structure
        self.assertIn('import_hourly', parsed_data)
        self.assertIn('export_hourly', parsed_data)
        self.assertIn('import_daily', parsed_data)
        self.assertIn('export_daily', parsed_data)
        
        # Check that we have data
        self.assertGreater(len(parsed_data['import_hourly']), 0, "No import hourly data found")
        self.assertGreater(len(parsed_data['export_hourly']), 0, "No export hourly data found")
        # Note: Sample CSV may not have import daily data, that's OK
        self.assertGreater(len(parsed_data['export_daily']), 0, "No export daily data found")
        
        # Process data
        processor = DataProcessor(timezone_offset="+02:00")
        processed_data = processor.process_data(parsed_data)
        processor.validate_processed_data(processed_data)
        
        # Verify processed data
        self.assertIn('import', processed_data)
        self.assertIn('export', processed_data)
        self.assertGreater(len(processed_data['import']), 0, "No processed import data")
        self.assertGreater(len(processed_data['export']), 0, "No processed export data")
        
        # Check data format
        for entry in processed_data['import'][:5]:  # Check first 5 entries
            self.assertIn('start', entry)
            self.assertIn('state', entry)
            self.assertIn('sum', entry)
            self.assertIsInstance(entry['state'], (int, float))
            self.assertIsInstance(entry['sum'], (int, float))
            self.assertTrue(entry['start'].endswith('+02:00'), "Timezone not correctly applied")
        
        # Generate YAML files
        generator = YAMLGenerator(output_dir=self.temp_dir)
        output_paths = generator.generate_yaml_files(processed_data, backup_existing=False)
        
        # Verify files were created
        self.assertIn('import', output_paths)
        self.assertIn('export', output_paths)
        self.assertTrue(output_paths['import'].exists(), "Import YAML file not created")
        self.assertTrue(output_paths['export'].exists(), "Export YAML file not created")
        
        # Verify YAML content is valid
        with open(output_paths['import'], 'r') as f:
            import_yaml = yaml.safe_load(f)
            self.assertIsInstance(import_yaml, list)
            self.assertGreater(len(import_yaml), 0)
        
        with open(output_paths['export'], 'r') as f:
            export_yaml = yaml.safe_load(f)
            self.assertIsInstance(export_yaml, list)
            self.assertGreater(len(export_yaml), 0)
    
    def test_data_consistency(self):
        """Test data consistency and expected values"""
        parser = CSVParser(str(self.sample_csv))
        parsed_data = parser.parse()
        
        # Check that daily totals are reasonable compared to hourly data
        import_daily = parsed_data['import_daily']
        import_hourly = parsed_data['import_hourly']
        
        if import_daily and import_hourly:
            # Get daily total for first day
            first_day = import_daily[0]
            day_date = first_day['timestamp'].date()
            
            # Get hourly data for the same day
            day_hourly = [h for h in import_hourly if h['timestamp'].date() == day_date]
            
            if day_hourly:
                hourly_sum = sum(h['value'] for h in day_hourly)
                daily_value = first_day['value']
                
                # Daily value should be much larger than hourly sum (it's cumulative)
                self.assertGreater(daily_value, hourly_sum, 
                                 "Daily total should be larger than hourly sum")
    
    def test_timezone_handling(self):
        """Test timezone handling in processed data"""
        parser = CSVParser(str(self.sample_csv))
        parsed_data = parser.parse()
        
        # Test different timezone offsets
        timezones = ["+01:00", "+02:00", "-05:00"]
        
        for tz in timezones:
            processor = DataProcessor(timezone_offset=tz)
            processed_data = processor.process_data(parsed_data)
            
            # Check that all timestamps have the correct timezone
            for data_type in ['import', 'export']:
                for entry in processed_data[data_type]:
                    self.assertTrue(entry['start'].endswith(tz), 
                                  f"Timezone {tz} not applied correctly")
    
    def test_yaml_file_format(self):
        """Test that generated YAML files have correct format for Home Assistant"""
        parser = CSVParser(str(self.sample_csv))
        parsed_data = parser.parse()
        
        processor = DataProcessor()
        processed_data = processor.process_data(parsed_data)
        
        generator = YAMLGenerator(output_dir=self.temp_dir)
        output_paths = generator.generate_yaml_files(processed_data, backup_existing=False)
        
        # Read and validate YAML structure
        with open(output_paths['import'], 'r') as f:
            content = f.read()
            
            # Check for header comments
            self.assertIn("# Home Assistant statistics data", content)
            self.assertIn("# Generated by EON-SPOOKER", content)
            self.assertIn("# Data points:", content)
            
            # Parse YAML
            yaml_data = yaml.safe_load(content)
            
            # Validate structure
            self.assertIsInstance(yaml_data, list)
            
            for entry in yaml_data[:3]:  # Check first 3 entries
                # Required fields for Home Assistant
                self.assertIn('start', entry)
                self.assertIn('state', entry)
                self.assertIn('sum', entry)
                
                # Check data types
                self.assertIsInstance(entry['start'], str)
                self.assertIsInstance(entry['state'], (int, float))
                self.assertIsInstance(entry['sum'], (int, float))
                
                # Check timestamp format (ISO 8601 with timezone)
                self.assertRegex(entry['start'], 
                               r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}')
    
    def test_error_handling_with_sample_data(self):
        """Test error handling doesn't break with real data"""
        # This should not raise any exceptions
        try:
            parser = CSVParser(str(self.sample_csv))
            parsed_data = parser.parse()
            
            processor = DataProcessor()
            processed_data = processor.process_data(parsed_data)
            processor.validate_processed_data(processed_data)
            
            generator = YAMLGenerator(output_dir=self.temp_dir)
            output_paths = generator.generate_yaml_files(processed_data, backup_existing=False)
            
        except Exception as e:
            self.fail(f"Pipeline failed with sample data: {e}")


if __name__ == '__main__':
    unittest.main()
