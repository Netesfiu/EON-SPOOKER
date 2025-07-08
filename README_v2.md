# E.ON W1000 "Spooker" v2.0

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A Python utility that converts E.ON W1000 portal CSV data to YAML format for Home Assistant integration. This tool processes energy consumption and generation data from the [E.ON W1000 portal](https://energia.eon-hungaria.hu/W1000/) and formats it for use with Home Assistant's `recorder.import_statistics` service.

## 🆕 What's New in v2.0

- **Modular Architecture**: Complete code refactoring with separate modules for parsing, processing, and output generation
- **Enhanced Error Handling**: Comprehensive validation and user-friendly error messages
- **Improved CLI**: Advanced command-line interface with multiple options and better help
- **Auto-detection**: Automatic CSV delimiter detection and timezone handling
- **Data Validation**: Built-in checks for data integrity and common issues
- **Backup Support**: Automatic backup of existing output files
- **Comprehensive Logging**: Detailed logging with configurable verbosity levels
- **Test Suite**: Complete test coverage for reliability
- **Better Documentation**: Improved README with clear examples and troubleshooting

## 📋 Requirements

- **Python 3.8 or higher**
- Access to the E.ON W1000 portal
- [Spook integration](https://github.com/frenck/spook) for Home Assistant (recommended)

## 🚀 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Netesfiu/EON-SPOOKER.git
   cd EON-SPOOKER
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## 📊 Acquiring Data from E.ON W1000

1. **Log in** to your [W1000 portal](https://energia.eon-hungaria.hu/W1000/Account/Login)

2. **Create a workarea** if you haven't already

3. **Create a new report** with the "+" icon and add these curves:
   - `+A` (Energy import)
   - `-A` (Energy export)
   - `DP_1-1:1.8.0*0` (Daily import totals)
   - `DP_1-1:2.8.0*0` (Daily export totals)

4. **Set the time period:**
   - Click "day" and select "custom"
   - Enter your date range in `dd/mm/yyyy` format
   - Press the checkmark icon

5. **Export the data:**
   - Click "export" or use the **≡** menu
   - Choose `Profile Table` format
   - Select `Comma separated values (.csv)`
   - **Important:** Ensure `Include status` is **unchecked**
   - Click export and download the file

## 🖥️ Usage

### Basic Usage (GUI File Selector)
```bash
python EON_SPOOKER_v2.py
```

### Command Line Usage
```bash
# Process a specific file
python EON_SPOOKER_v2.py -p "path/to/your/file.csv"

# Custom output directory
python EON_SPOOKER_v2.py -p data.csv -o output/

# Custom timezone
python EON_SPOOKER_v2.py -p data.csv --timezone "+01:00"

# Verbose logging
python EON_SPOOKER_v2.py -p data.csv -v

# Dry run (parse but don't write files)
python EON_SPOOKER_v2.py -p data.csv --dry-run

# Custom output filenames
python EON_SPOOKER_v2.py -p data.csv --import-file my_import.yaml --export-file my_export.yaml
```

### Advanced Options
```bash
# See all available options
python EON_SPOOKER_v2.py --help

# Custom CSV delimiter
python EON_SPOOKER_v2.py -p data.csv --delimiter ";"

# Disable file backup
python EON_SPOOKER_v2.py -p data.csv --no-backup
```

## 📁 Output Files

The script generates two YAML files:
- `import.yaml` - Energy consumption data
- `export.yaml` - Energy generation/export data

Each file contains timestamped statistics ready for Home Assistant import.

## 🏠 Home Assistant Integration

### Using the Recorder Service

1. Go to **Developer Tools > Services**
2. Search for `recorder.import_statistics`
3. Configure the service call:

```yaml
service: recorder.import_statistics
data:
  has_mean: false
  has_sum: true
  statistic_id: sensor.w1000_import  # Your sensor entity ID
  source: recorder
  unit_of_measurement: kWh
  stats:
    # Paste the contents of import.yaml here
    - start: "2025-06-14 00:00:00+02:00"
      sum: 123.456
      state: 123.456
    - start: "2025-06-14 01:00:00+02:00"
      sum: 124.567
      state: 124.567
    # ... more entries
```

4. Click **Call Service**

### ⚠️ Important Notes

- **Always backup your Home Assistant database** before importing statistics
- **Test with a small dataset first** to ensure compatibility
- **Statistics cannot be easily undone** once imported
- Use the `--dry-run` option to validate data before processing

## 🔧 Troubleshooting

### Common Issues

**File not found error:**
```bash
# Ensure the file path is correct
python EON_SPOOKER_v2.py -p "C:/full/path/to/file.csv"
```

**CSV format error:**
```bash
# Check delimiter and try manual specification
python EON_SPOOKER_v2.py -p data.csv --delimiter ";"
```

**No GUI available:**
```bash
# Use command line mode
python EON_SPOOKER_v2.py -p data.csv
```

**Timezone issues:**
```bash
# Specify timezone manually
python EON_SPOOKER_v2.py -p data.csv --timezone "+02:00"
```

### Verbose Logging

For detailed troubleshooting information:
```bash
python EON_SPOOKER_v2.py -p data.csv -v
```

## 🧪 Testing

Run the test suite to verify functionality:
```bash
python -m pytest tests/ -v
```

## 📝 Backward Compatibility

The original `EON_SPOOKER.py` script is preserved for backward compatibility. However, we recommend migrating to the new `EON_SPOOKER_v2.py` for improved reliability and features.

## 🤝 Contributing

Contributions are welcome! Please feel free to:
- Report bugs by opening an issue
- Suggest new features
- Submit pull requests
- Improve documentation

### Development Setup

1. Clone the repository
2. Install development dependencies: `pip install -r requirements.txt`
3. Run tests: `python -m pytest tests/`
4. Follow PEP 8 style guidelines

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Projects

- [frenck/Spook](https://github.com/frenck/spook) - Home Assistant integration
- [ZsBT/hass-w1000-portal](https://github.com/ZsBT/hass-w1000-portal) - Alternative W1000 integration

## 📞 Support

If you encounter issues:
1. Check the [troubleshooting section](#-troubleshooting)
2. Run with verbose logging (`-v` flag)
3. Search existing [GitHub issues](https://github.com/Netesfiu/EON-SPOOKER/issues)
4. Create a new issue with detailed information

---

**Read this in other languages:**
- [🇭🇺 Magyar](languages/readme.hu.md)
- [🇺🇸 English](languages/readme.en.md)
