#!/usr/bin/env python3
"""
EON-SPOOKER Version Compatibility Test
=====================================

This script tests that the new v3.0 version produces identical results
to the original EON_SPOOKER.py script for all supported data formats.
"""

import os
import sys
import yaml
import json
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime

# Add the eon_spooker package to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from eon_spooker import parse_eon_file, parse_eon_files

def load_yaml_file(filepath):
    """Load and parse a YAML file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

def normalize_data_for_comparison(data):
    """Normalize data structure for comparison."""
    if isinstance(data, list):
        # Sort by timestamp for consistent comparison
        return sorted(data, key=lambda x: x.get('start', ''))
    return data

def calculate_data_hash(data):
    """Calculate hash of normalized data for comparison."""
    normalized = normalize_data_for_comparison(data)
    data_str = json.dumps(normalized, sort_keys=True, default=str)
    return hashlib.md5(data_str.encode()).hexdigest()

def run_original_script(input_file, output_file):
    """Run the original EON_SPOOKER.py script."""
    try:
        # Original script uses -p flag and generates fixed output files
        cmd = [sys.executable, 'EON_SPOOKER.py', '-p', input_file]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Script timed out"
    except Exception as e:
        return False, "", str(e)

def run_v3_script(input_file, output_file):
    """Run the new EON_SPOOKER_v3.py script."""
    try:
        cmd = [sys.executable, 'EON_SPOOKER_v3.py', '--output', output_file, input_file]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Script timed out"
    except Exception as e:
        return False, "", str(e)

def compare_yaml_outputs(original_file, v3_file):
    """Compare YAML outputs from both versions."""
    original_data = load_yaml_file(original_file)
    v3_data = load_yaml_file(v3_file)
    
    if original_data is None or v3_data is None:
        return False, "Failed to load one or both YAML files"
    
    # Calculate hashes for comparison
    original_hash = calculate_data_hash(original_data)
    v3_hash = calculate_data_hash(v3_data)
    
    if original_hash == v3_hash:
        return True, "Data structures are identical"
    else:
        # Detailed comparison
        original_norm = normalize_data_for_comparison(original_data)
        v3_norm = normalize_data_for_comparison(v3_data)
        
        if len(original_norm) != len(v3_norm):
            return False, f"Different number of records: original={len(original_norm)}, v3={len(v3_norm)}"
        
        # Compare first few records for detailed analysis
        differences = []
        for i, (orig, v3) in enumerate(zip(original_norm[:5], v3_norm[:5])):
            if orig != v3:
                differences.append(f"Record {i}: {orig} != {v3}")
        
        if differences:
            return False, f"Data differences found: {'; '.join(differences)}"
        else:
            return False, "Data structures differ but first 5 records are identical"

def test_file_compatibility(input_file, test_name):
    """Test compatibility for a specific input file."""
    print(f"\n{'='*60}")
    print(f"Testing: {test_name}")
    print(f"File: {input_file}")
    print(f"{'='*60}")
    
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        return False
    
    # Generate output filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_output = f"test_original_{timestamp}.yaml"
    v3_output = f"test_v3_{timestamp}.yaml"
    
    try:
        # Test original script
        print("🔄 Running original EON_SPOOKER.py...")
        orig_success, orig_stdout, orig_stderr = run_original_script(input_file, original_output)
        
        if not orig_success:
            print(f"❌ Original script failed:")
            print(f"   stdout: {orig_stdout}")
            print(f"   stderr: {orig_stderr}")
            return False
        
        print("✅ Original script completed successfully")
        
        # Test v3 script
        print("🔄 Running new EON_SPOOKER_v3.py...")
        v3_success, v3_stdout, v3_stderr = run_v3_script(input_file, v3_output)
        
        if not v3_success:
            print(f"❌ V3 script failed:")
            print(f"   stdout: {v3_stdout}")
            print(f"   stderr: {v3_stderr}")
            return False
        
        print("✅ V3 script completed successfully")
        
        # Compare outputs
        print("🔄 Comparing outputs...")
        
        # Original script generates fixed files: import.yaml and export.yaml
        original_import = "import.yaml"
        original_export = "export.yaml"
        
        # V3 script generates files with custom names
        v3_base_name = os.path.splitext(v3_output)[0]
        v3_import = f"{v3_base_name}_import.yaml"
        v3_export = f"{v3_base_name}_export.yaml"
        
        original_files = []
        v3_files = []
        
        if os.path.exists(original_import):
            original_files.append(original_import)
        if os.path.exists(original_export):
            original_files.append(original_export)
            
        if os.path.exists(v3_import):
            v3_files.append(v3_import)
        if os.path.exists(v3_export):
            v3_files.append(v3_export)
        
        print(f"📁 Original files: {original_files}")
        print(f"📁 V3 files: {v3_files}")
        
        # Compare import and export files separately
        comparisons_passed = 0
        total_comparisons = 0
        
        # Compare import files
        if original_import in original_files and v3_import in v3_files:
            total_comparisons += 1
            success, message = compare_yaml_outputs(original_import, v3_import)
            if success:
                print(f"✅ Import file comparison: {message}")
                comparisons_passed += 1
            else:
                print(f"❌ Import file comparison failed: {message}")
                # Show sample data for debugging
                print("\n🔍 Import file sample data:")
                orig_data = load_yaml_file(original_import)
                v3_data = load_yaml_file(v3_import)
                if orig_data and v3_data:
                    print(f"Original import first record: {orig_data[0] if isinstance(orig_data, list) and orig_data else 'N/A'}")
                    print(f"V3 import first record: {v3_data[0] if isinstance(v3_data, list) and v3_data else 'N/A'}")
        
        # Compare export files
        if original_export in original_files and v3_export in v3_files:
            total_comparisons += 1
            success, message = compare_yaml_outputs(original_export, v3_export)
            if success:
                print(f"✅ Export file comparison: {message}")
                comparisons_passed += 1
            else:
                print(f"❌ Export file comparison failed: {message}")
                # Show sample data for debugging
                print("\n🔍 Export file sample data:")
                orig_data = load_yaml_file(original_export)
                v3_data = load_yaml_file(v3_export)
                if orig_data and v3_data:
                    print(f"Original export first record: {orig_data[0] if isinstance(orig_data, list) and orig_data else 'N/A'}")
                    print(f"V3 export first record: {v3_data[0] if isinstance(v3_data, list) and v3_data else 'N/A'}")
        
        if total_comparisons == 0:
            print("❌ No output files found to compare")
            return False
        elif comparisons_passed == total_comparisons:
            print(f"✅ All {total_comparisons} file comparisons passed!")
            return True
        else:
            print(f"❌ {comparisons_passed}/{total_comparisons} file comparisons passed")
            return False
            
    finally:
        # Cleanup test files
        cleanup_files = [
            original_output, 
            v3_output,
            "import.yaml",  # Original script output
            "export.yaml",  # Original script output
        ]
        
        # Add v3 generated files
        v3_base_name = os.path.splitext(v3_output)[0]
        for suffix in ['_import', '_export']:
            cleanup_files.append(f"{v3_base_name}{suffix}.yaml")
        
        for file in cleanup_files:
            if os.path.exists(file):
                try:
                    os.remove(file)
                except:
                    pass

def main():
    """Main test function."""
    print("🧪 EON-SPOOKER Version Compatibility Test")
    print("=" * 60)
    print("Testing that v3.0 produces identical results to the original script")
    print("=" * 60)
    
    # Test files to check
    test_cases = [
        ("sample report data.csv", "Legacy Web Portal Format"),
        ("180_280.csv", "Daily Cumulative Format"),
        ("AP_AM.csv", "15-minute Interval Format"),
    ]
    
    results = []
    
    for input_file, description in test_cases:
        success = test_file_compatibility(input_file, description)
        results.append((description, success))
    
    # Summary
    print(f"\n{'='*60}")
    print("🏁 TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {description}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! V3.0 is fully compatible with the original script.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the differences above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
