# EON-SPOOKER v3.0 - Python Package

EON-SPOOKER v3.0 is a comprehensive Python package for processing EON energy data files and converting them into formats suitable for Home Assistant and other energy management systems.

## 🚀 What's New in v3.0

- **Modular Architecture**: Complete rewrite as a professional Python package
- **Automatic Format Detection**: Intelligent detection of EON data file formats
- **Unified Parser System**: Single interface for all EON data formats
- **Enhanced Error Handling**: Robust error handling with detailed logging
- **Original Script Compatibility**: 100% backward compatible with original script
- **Comprehensive Testing**: Full test suite ensuring reliability

## 📦 Package Structure

```
eon_spooker/
├── __init__.py              # Package initialization and main API
├── config.py                # Configuration constants
├── exceptions.py            # Custom exception classes
├── format_detector.py       # Automatic format detection
├── unified_parser.py        # Main unified parser
├── csv_parser.py           # Legacy format parser
├── ap_am_parser.py         # AP_AM format parser (15-min intervals)
├── cumulative_parser.py    # 180_280 format parser (daily cumulative)
└── yaml_generator.py       # YAML output generation
```

## 🔧 Installation

### Option 1: Direct Usage (Recommended)
```bash
git clone https://github.com/Netesfiu/EON-SPOOKER.git
cd EON-SPOOKER
pip install -r requirements.txt
```

### Option 2: Package Installation
```bash
pip install -e .  # Install in development mode
```

## 📋 Requirements

- Python 3.7+
- pandas >= 1.3.0
- PyYAML >= 5.4.0

## 🚀 Quick Start

### Simple File Processing
```python
from eon_spooker import parse_eon_file

# Parse any EON file with automatic format detection
result = parse_eon_file("your_eon_data.csv")
print(f"Format: {result['format']}")
print(f"Records: {result['metadata']['total_records']}")
```

### Multiple File Processing
```python
from eon_spooker import parse_eon_files

# Parse multiple files and combine results
files = ["180_280.csv", "AP_AM.csv"]
result = parse_eon_files(files)

# If both cumulative and consumption files are present,
# YAML data is automatically generated using original script logic
if 'yaml_data' in result:
    print(f"Import records: {len(result['yaml_data']['import'])}")
    print(f"Export records: {len(result['yaml_data']['export'])}")
```

### YAML Generation
```python
from eon_spooker import YAMLGenerator

generator = YAMLGenerator()
yaml_content = generator.generate_yaml(data)

# Save to file
with open("output.yaml", "w") as f:
    f.write(yaml_content)
```

## 📊 Supported Data Formats

### 1. Legacy Format (Web Portal CSV)
- **Source**: Downloaded from EON's web portal
- **Structure**: POD Name, Variable name, Time, Value [kWh]
- **Intervals**: Mixed (hourly, daily)
- **Auto-detected**: ✅

### 2. AP_AM Format (15-minute intervals)
- **Source**: Email attachments
- **Structure**: Dátum/Idő, +A, -A
- **Intervals**: 15-minute consumption data
- **Features**: Summary rows (MAXIMUM, ÖSSZEG)
- **Auto-detected**: ✅

### 3. 180_280 Format (Daily cumulative)
- **Source**: Email attachments
- **Structure**: Dátum, DP_1-1:1.8.0*0, DP_1-1:2.8.0*0
- **Intervals**: Daily cumulative meter readings
- **Features**: Actual meter readings (e.g., 31433 kWh)
- **Auto-detected**: ✅

## 🔍 Format Detection

The package automatically detects file formats based on:
- Column structure analysis
- Data pattern recognition
- Content validation
- Header inspection

```python
from eon_spooker import detect_file_format

format_type, metadata = detect_file_format("your_file.csv")
print(f"Detected format: {format_type.value}")
print(f"Metadata: {metadata}")
```

## 🛠️ Advanced Usage

### Custom Parser Configuration
```python
from eon_spooker import UnifiedParser

parser = UnifiedParser()

# Parse with format override
result = parser.parse_file("data.csv", format_override="ap_am")

# Parse multiple files
results = parser.parse_multiple_files(["file1.csv", "file2.csv"])
```

### Error Handling
```python
from eon_spooker import parse_eon_file, FileProcessingError

try:
    result = parse_eon_file("problematic_file.csv")
except FileProcessingError as e:
    print(f"Processing error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Logging Configuration
```python
import logging

# Configure logging for detailed output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('eon_spooker')
```

## 🏠 Home Assistant Integration

### Generated YAML Format
The package generates YAML files compatible with Home Assistant's `recorder.import_statistics` service:

```yaml
# Example output structure
- start: "2025-06-14 00:00:00+02:00"
  sum: 123.456
  state: 123.456
- start: "2025-06-14 01:00:00+02:00"
  sum: 124.567
  state: 124.567
```

### Import to Home Assistant
```yaml
service: recorder.import_statistics
data:
  has_mean: false
  has_sum: true
  statistic_id: sensor.eon_import
  source: recorder
  unit_of_measurement: kWh
  stats: !include your_import_data.yaml
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
python test_improvements.py
```

The test suite covers:
- ✅ Format detection accuracy
- ✅ Individual parser functionality
- ✅ Unified parser operations
- ✅ YAML generation
- ✅ Error handling
- ✅ Original script compatibility

## 📈 Performance

### Benchmarks
- **Small files** (< 1MB): ~0.1 seconds
- **Medium files** (1-10MB): ~0.5-2 seconds
- **Large files** (> 10MB): ~2-10 seconds

### Memory Usage
- **Baseline**: ~10MB for package loading
- **Per file**: ~2-5MB additional per processed file
- **Peak usage**: Typically < 50MB for normal operations

## 🔄 Migration from Original Script

### Drop-in Replacement
```python
# Old way (EON_SPOOKER.py)
# Manual script execution

# New way (v3.0)
from eon_spooker import parse_eon_files
result = parse_eon_files(["180_280.csv", "AP_AM.csv"])
```

### Backward Compatibility
- ✅ Exact same calculation logic
- ✅ Identical YAML output format
- ✅ Same timezone handling
- ✅ Compatible with Home Assistant
- ✅ All original data transformations preserved

## 🐛 Troubleshooting

### Common Issues

1. **Import Error**: Ensure all dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

2. **Format Detection Fails**: Check file structure and encoding
   ```python
   # Manual format specification
   result = parse_eon_file("file.csv", format_override="legacy")
   ```

3. **Memory Issues**: Process files individually for large datasets
   ```python
   # Process one file at a time
   for file_path in file_list:
       result = parse_eon_file(file_path)
   ```

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now all operations will show detailed debug information
result = parse_eon_file("debug_file.csv")
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### Development Setup
```bash
git clone https://github.com/Netesfiu/EON-SPOOKER.git
cd EON-SPOOKER
pip install -r requirements.txt
python test_improvements.py
```

## 📚 API Reference

### Main Functions
- `parse_eon_file(file_path, delimiter=';', format_override=None)`: Parse single file
- `parse_eon_files(file_paths, delimiter=';')`: Parse multiple files
- `detect_file_format(file_path, delimiter=';')`: Detect file format

### Classes
- `UnifiedParser`: Main parser class
- `YAMLGenerator`: YAML output generation
- `FileProcessingError`: Custom exception class

### Data Formats
- `DataFormat.LEGACY`: Legacy web portal format
- `DataFormat.AP_AM`: 15-minute interval format
- `DataFormat.CUMULATIVE_180_280`: Daily cumulative format

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Projects

- **Home Assistant Add-on**: See [readme.md](readme.md) for the Home Assistant add-on version
- **Original Script**: Legacy `EON_SPOOKER.py` for reference

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Netesfiu/EON-SPOOKER/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Netesfiu/EON-SPOOKER/discussions)
- **Documentation**: [Improvements Summary](IMPROVEMENTS_SUMMARY.md)

---

**EON-SPOOKER v3.0** - Professional Python package for EON energy data processing 🚀
