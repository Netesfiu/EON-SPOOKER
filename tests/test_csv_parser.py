"""
Tests for CSV parser functionality
"""

import unittest
import tempfile
import os
from datetime import datetime
from pathlib import Path

from eon_spooker.csv_parser import CSVParser
from eon_spooker.exceptions import CSVFormatError, DataValidationError, FileProcessingError


class TestCSVParser(unittest.TestCase):
    """Test cases for CSVParser class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_csv_content = """POD Name;Variable name;Time;Value [kWh]
HU000120-11-S00000000000000297924;'+A';2025.06.14 00:00:00;0.144
HU000120-11-S00000000000000297924;'+A';2025.06.14 01:00:00;0.130
HU000120-11-S00000000000000297924;'-A';2025.06.14 00:00:00;0.000
HU000120-11-S00000000000000297924;'-A';2025.06.14 01:00:00;0.050
HU000120-11-S00000000000000297924;'DP_1-1:1.8.0*0';2025.06.14 00:00:00;1000.000
HU000120-11-S00000000000000297924;'DP_1-1:2.8.0*0';2025.06.14 00:00:00;2000.000"""
        
        # Create temporary CSV file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        self.temp_file.write(self.test_csv_content)
        self.temp_file.close()
        
    def tearDown(self):
        """Clean up test fixtures"""
        os.unlink(self.temp_file.name)
    
    def test_file_validation_success(self):
        """Test successful file validation"""
        parser = CSVParser(self.temp_file.name)
        self.assertEqual(parser.file_path, Path(self.temp_file.name))
    
    def test_file_not_found(self):
        """Test error when file doesn't exist"""
        with self.assertRaises(FileProcessingError):
            CSVParser("nonexistent_file.csv")
    
    def test_delimiter_detection(self):
        """Test automatic delimiter detection"""
        parser = CSVParser(self.temp_file.name)
        detected_delimiter = parser._detect_delimiter()
        self.assertEqual(detected_delimiter, ';')
    
    def test_parse_success(self):
        """Test successful CSV parsing"""
        parser = CSVParser(self.temp_file.name)
        data = parser.parse()
        
        # Check data structure
        self.assertIn('import_hourly', data)
        self.assertIn('export_hourly', data)
        self.assertIn('import_daily', data)
        self.assertIn('export_daily', data)
        
        # Check import hourly data
        self.assertEqual(len(data['import_hourly']), 2)
        self.assertEqual(data['import_hourly'][0]['value'], 0.144)
        self.assertIsInstance(data['import_hourly'][0]['timestamp'], datetime)
        
        # Check export hourly data
        self.assertEqual(len(data['export_hourly']), 2)
        self.assertEqual(data['export_hourly'][0]['value'], 0.000)
        
        # Check daily data
        self.assertEqual(len(data['import_daily']), 1)
        self.assertEqual(data['import_daily'][0]['value'], 1000.000)
        
        self.assertEqual(len(data['export_daily']), 1)
        self.assertEqual(data['export_daily'][0]['value'], 2000.000)
    
    def test_invalid_csv_headers(self):
        """Test error with invalid CSV headers"""
        invalid_content = "Wrong;Headers;Here;Value\n1;2;3;4"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(invalid_content)
            f.flush()
            
            with self.assertRaises(CSVFormatError):
                parser = CSVParser(f.name)
                parser.parse()
            
            os.unlink(f.name)
    
    def test_invalid_datetime_format(self):
        """Test handling of invalid datetime format"""
        invalid_content = """POD Name;Variable name;Time;Value [kWh]
HU000120-11-S00000000000000297924;'+A';invalid_date;0.144"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(invalid_content)
            f.flush()
            
            parser = CSVParser(f.name)
            # Should not raise exception but log warning and skip invalid rows
            data = parser.parse()
            self.assertEqual(len(data['import_hourly']), 0)
            
            os.unlink(f.name)
    
    def test_invalid_numeric_value(self):
        """Test handling of invalid numeric values"""
        invalid_content = """POD Name;Variable name;Time;Value [kWh]
HU000120-11-S00000000000000297924;'+A';2025.06.14 00:00:00;invalid_number"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(invalid_content)
            f.flush()
            
            parser = CSVParser(f.name)
            # Should not raise exception but log warning and skip invalid rows
            data = parser.parse()
            self.assertEqual(len(data['import_hourly']), 0)
            
            os.unlink(f.name)


if __name__ == '__main__':
    unittest.main()
