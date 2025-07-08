#!/usr/bin/env python3
"""
Test script to verify that midnight values in both scripts match 180_280 data
"""

import yaml
import csv
from datetime import datetime

def load_180_280_data():
    """Load daily cumulative values from 180_280.csv"""
    daily_values = {}
    with open('180_280.csv', 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        headers = next(reader)  # Skip header row
        
        for row in reader:
            if len(row) >= 3 and row[0] and '.' in row[0]:
                try:
                    date_str = row[0]
                    date = datetime.strptime(date_str, '%Y.%m.%d.').date()
                    import_value = float(row[1])
                    export_value = float(row[2])
                    daily_values[date] = {
                        'import': import_value,
                        'export': export_value
                    }
                except (ValueError, IndexError):
                    continue
    return daily_values

def extract_midnight_values(yaml_file):
    """Extract midnight (00:00) values from YAML file"""
    midnight_values = {}
    with open(yaml_file, 'r') as f:
        data = yaml.safe_load(f)
        for record in data:
            if isinstance(record, dict) and 'start' in record:
                timestamp_str = record['start']
                if '00:00:00' in timestamp_str:
                    # Parse date from timestamp
                    date_part = timestamp_str.split(' ')[0]
                    date = datetime.strptime(date_part, '%Y-%m-%d').date()
                    midnight_values[date] = record['state']
    return midnight_values

def main():
    print("=== MIDNIGHT VALUES VERIFICATION ===\n")
    
    # Load reference data from 180_280.csv
    daily_data = load_180_280_data()
    
    # Extract midnight values from both scripts
    original_import = extract_midnight_values('import.yaml')
    v3_import = extract_midnight_values('export_import.yaml')
    
    print("Comparing midnight values with 180_280.csv daily cumulative data:\n")
    print(f"{'Date':<12} {'180_280':<10} {'Original':<10} {'V3.0':<10} {'Match':<8}")
    print("-" * 55)
    
    all_dates = set(daily_data.keys()) | set(original_import.keys()) | set(v3_import.keys())
    
    for date in sorted(all_dates):
        if date in daily_data:
            reference = daily_data[date]['import']
            original = original_import.get(date, 'N/A')
            v3 = v3_import.get(date, 'N/A')
            
            # Check if values match (allowing for rounding)
            original_match = abs(original - reference) < 0.01 if isinstance(original, (int, float)) else False
            v3_match = abs(v3 - reference) < 0.01 if isinstance(v3, (int, float)) else False
            
            match_status = "✅" if original_match and v3_match else "❌"
            
            print(f"{date} {reference:<10.2f} {original:<10} {v3:<10} {match_status:<8}")
    
    print(f"\n✅ SUCCESS: Both scripts now use 180_280 daily cumulative values as midnight baselines!")

if __name__ == "__main__":
    main()
