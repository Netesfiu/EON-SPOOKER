#!/usr/bin/env python3
"""
Test script for EON-SPOOKER v3.0 improvements
Tests all parsers, format detection, and YAML generation
"""

import sys
import os
import logging
from pathlib import Path

# Add the eon_spooker package to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from eon_spooker.unified_parser import UnifiedParser, parse_eon_file, parse_eon_files
from eon_spooker.format_detector import detect_file_format
from eon_spooker.yaml_generator import YAMLGenerator
from eon_spooker.exceptions import FileProcessingError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_format_detection():
    """Test automatic format detection"""
    print("\n=== Testing Format Detection ===")
    
    test_files = [
        "sample report data.csv",
        "180_280.csv"
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            try:
                format_type, metadata = detect_file_format(file_path)
                print(f"✓ {file_path}: {format_type.value}")
                print(f"  Metadata: {metadata}")
            except Exception as e:
                print(f"✗ {file_path}: Error - {e}")
        else:
            print(f"⚠ {file_path}: File not found")


def test_individual_parsers():
    """Test individual parsers"""
    print("\n=== Testing Individual Parsers ===")
    
    test_files = [
        ("sample report data.csv", "legacy"),
        ("180_280.csv", "cumulative_180_280")
    ]
    
    for file_path, expected_format in test_files:
        if os.path.exists(file_path):
            try:
                result = parse_eon_file(file_path)
                print(f"✓ {file_path}:")
                print(f"  Format: {result['format']}")
                print(f"  Records: {result['metadata']['total_records']}")
                if 'date_range' in result['metadata']:
                    date_range = result['metadata']['date_range']
                    print(f"  Date range: {date_range.get('start')} to {date_range.get('end')}")
                
                # Check if format matches expected
                if result['format'] == expected_format:
                    print(f"  ✓ Format detection correct")
                else:
                    print(f"  ✗ Expected {expected_format}, got {result['format']}")
                    
            except Exception as e:
                print(f"✗ {file_path}: Error - {e}")
        else:
            print(f"⚠ {file_path}: File not found")


def test_unified_parser():
    """Test unified parser with multiple files"""
    print("\n=== Testing Unified Parser ===")
    
    test_files = []
    for file_path in ["sample report data.csv", "180_280.csv"]:
        if os.path.exists(file_path):
            test_files.append(file_path)
    
    if test_files:
        try:
            parser = UnifiedParser()
            result = parser.parse_multiple_files(test_files)
            
            print(f"✓ Processed {len(result['files'])} files")
            print(f"  Formats detected: {result['formats']}")
            print(f"  Total records: {result['total_records']}")
            print(f"  Processing errors: {len(result['metadata']['processing_errors'])}")
            
            if result['metadata']['processing_errors']:
                for error in result['metadata']['processing_errors']:
                    print(f"    Error: {error}")
            
            # Check for YAML data if both cumulative and consumption files are present
            if 'yaml_data' in result:
                print(f"  ✓ YAML data generated:")
                print(f"    Import records: {len(result['yaml_data']['import'])}")
                print(f"    Export records: {len(result['yaml_data']['export'])}")
            
        except Exception as e:
            print(f"✗ Unified parser error: {e}")
    else:
        print("⚠ No test files found")


def test_yaml_generation():
    """Test YAML generation"""
    print("\n=== Testing YAML Generation ===")
    
    try:
        # Test with sample data in the format expected by the YAML generator
        sample_data = [
            {
                'datetime': '2024-01-01 00:00:00+01:00',
                'import_kwh': 1.5,
                'export_kwh': 0.8
            },
            {
                'datetime': '2024-01-01 01:00:00+01:00',
                'import_kwh': 1.2,
                'export_kwh': 0.5
            }
        ]
        
        generator = YAMLGenerator()
        yaml_content = generator.generate_yaml(sample_data)
        
        print("✓ YAML generation successful")
        print(f"  Generated {len(yaml_content)} characters")
        
        # Save test YAML
        test_yaml_path = "test_output.yaml"
        with open(test_yaml_path, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        print(f"  ✓ Test YAML saved to {test_yaml_path}")
        
        # Test multi-resolution YAML generation
        multi_data = {
            'hourly': sample_data,
            'daily': [
                {
                    'date': '2024-01-01',
                    'import_kwh': 30.5,
                    'export_kwh': 15.2
                }
            ]
        }
        
        multi_yaml = generator.generate_multi_resolution_yaml(multi_data)
        print("✓ Multi-resolution YAML generation successful")
        
        # Save multi-resolution test YAML
        multi_yaml_path = "test_multi_output.yaml"
        with open(multi_yaml_path, 'w', encoding='utf-8') as f:
            f.write(multi_yaml)
        print(f"  ✓ Multi-resolution YAML saved to {multi_yaml_path}")
        
    except Exception as e:
        print(f"✗ YAML generation error: {e}")


def test_error_handling():
    """Test error handling"""
    print("\n=== Testing Error Handling ===")
    
    # Test with non-existent file
    try:
        result = parse_eon_file("non_existent_file.csv")
        print("✗ Should have raised an error for non-existent file")
    except FileProcessingError as e:
        print(f"✓ Correctly handled non-existent file: {e}")
    except Exception as e:
        print(f"✗ Unexpected error type: {e}")
    
    # Test with invalid format override
    if os.path.exists("sample report data.csv"):
        try:
            result = parse_eon_file("sample report data.csv", format_override="invalid_format")
            print("✗ Should have raised an error for invalid format")
        except FileProcessingError as e:
            print(f"✓ Correctly handled invalid format: {e}")
        except Exception as e:
            print(f"✗ Unexpected error type: {e}")


def test_original_script_compatibility():
    """Test compatibility with original script logic"""
    print("\n=== Testing Original Script Compatibility ===")
    
    # Check if we have the 180_280.csv file
    if os.path.exists("180_280.csv"):
        try:
            result = parse_eon_file("180_280.csv")
            
            print("✓ Cumulative format parsing:")
            print(f"  Format: {result['format']}")
            
            # Check if we have the expected data structure
            if 'daily_cumulative' in result:
                import_data = result['daily_cumulative']['import']
                export_data = result['daily_cumulative']['export']
                print(f"  Import records: {len(import_data)}")
                print(f"  Export records: {len(export_data)}")
                
                # Check data structure matches original script
                if import_data and 'start' in import_data[0] and 'value' in import_data[0]:
                    print("  ✓ Data structure matches original script")
                else:
                    print("  ✗ Data structure doesn't match original script")
            
        except Exception as e:
            print(f"✗ Error testing original script compatibility: {e}")
    else:
        print("⚠ 180_280.csv not found - cannot test original script compatibility")


def main():
    """Run all tests"""
    print("EON-SPOOKER v3.0 Improvement Tests")
    print("=" * 50)
    
    test_format_detection()
    test_individual_parsers()
    test_unified_parser()
    test_yaml_generation()
    test_error_handling()
    test_original_script_compatibility()
    
    print("\n" + "=" * 50)
    print("Test suite completed!")
    print("\nNext steps:")
    print("1. Review any errors or warnings above")
    print("2. Test with your actual EON data files")
    print("3. Use the unified parser in your applications")
    print("4. Generate YAML files for Home Assistant")


if __name__ == "__main__":
    main()
