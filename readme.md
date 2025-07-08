# EON-SPOOKER Home Assistant Add-on

A comprehensive Home Assistant add-on for processing EON energy data and importing statistics into Home Assistant's energy dashboard.

## Features

- **Multi-format Support**: Handles legacy web portal CSV, AP_AM format (15-min intervals), and 180_280 format (daily cumulative)
- **Web Interface**: User-friendly web UI for file upload and processing
- **Auto-processing**: Automatically processes new files when uploaded
- **Direct HA Integration**: Import statistics directly into Home Assistant
- **File Monitoring**: Watches input folder for new files
- **Multiple Resolutions**: Support for 15-minute, hourly, and daily data
- **Notifications**: Optional Home Assistant notifications for processing status

## Installation

### Method 1: Add Repository to Home Assistant

1. In Home Assistant, go to **Supervisor** → **Add-on Store**
2. Click the **⋮** menu in the top right corner
3. Select **Repositories**
4. Add this repository URL: `https://github.com/Netesfiu/EON-SPOOKER`
5. Find "EON-SPOOKER" in the add-on store and click **Install**

### Method 2: Manual Installation

1. Copy all addon files to `/addons/eon-spooker/` in your Home Assistant configuration
2. Restart Home Assistant Supervisor
3. The add-on will appear in the local add-ons section

## Configuration

### Basic Configuration

```yaml
auto_process: true
input_folder: "/share/eon-data"
output_folder: "/share/eon-output"
resolution: "hourly"
log_level: "info"
auto_import: false
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `auto_process` | boolean | `true` | Automatically process uploaded files |
| `input_folder` | string | `/share/eon-data` | Folder to monitor for input files |
| `output_folder` | string | `/share/eon-output` | Folder for processed YAML files |
| `resolution` | string | `hourly` | Data resolution: `15min`, `hourly`, `daily`, or `all` |
| `log_level` | string | `info` | Log level: `trace`, `debug`, `info`, `warning`, `error`, `fatal` |
| `auto_import` | boolean | `false` | Automatically import statistics to Home Assistant |
| `file_patterns` | list | `["*.csv", "*.xlsx"]` | File patterns to monitor |
| `backup_files` | boolean | `true` | Backup processed files |
| `notification_service` | string | `""` | Home Assistant notification service (e.g., `notify.mobile_app_phone`) |

### Advanced Configuration Example

```yaml
auto_process: true
input_folder: "/share/eon-data"
output_folder: "/share/eon-output"
resolution: "hourly"
log_level: "info"
auto_import: true
file_patterns:
  - "*.csv"
  - "*.xlsx"
  - "*.xls"
backup_files: true
notification_service: "notify.mobile_app_phone"
```

## Usage

### Web Interface

1. Start the add-on
2. Open the web UI (available in the add-on info panel)
3. Upload your EON energy data files (CSV or Excel)
4. Files will be automatically processed if `auto_process` is enabled
5. Download the generated YAML files or import them directly to Home Assistant

### File Upload Methods

1. **Web Interface**: Drag & drop or browse files through the web UI
2. **Direct Copy**: Copy files to the configured input folder (`/share/eon-data` by default)
3. **Network Share**: If you have Samba add-on installed, access the share folder

### Supported File Formats

#### Legacy Format (Web Portal CSV)
- Downloaded from EON's web portal
- Contains mixed interval data
- Columns: POD Name, Variable name, Time, Value [kWh]

#### AP_AM Format (Email Attachments)
- 15-minute interval data from email attachments
- Columns: Dátum/Idő, +A, -A
- Contains summary rows (MAXIMUM, ÖSSZEG)

#### 180_280 Format (Email Attachments)
- Daily cumulative meter readings from email attachments
- Columns: Dátum, DP_1-1:1.8.0*0, DP_1-1:2.8.0*0
- Contains actual meter readings (e.g., 31433 kWh)

## Output Files

The add-on generates three types of YAML files:

1. **Import YAML** (`*_import.yaml`): For imported energy statistics
2. **Export YAML** (`*_export.yaml`): For exported energy statistics  
3. **Combined YAML** (`*.yaml`): Both import and export in one file

These files are compatible with Home Assistant's `recorder.import_statistics` service.

## Home Assistant Integration

### Energy Dashboard

1. Process your EON data files
2. Import the generated statistics using the web interface
3. Go to **Settings** → **Dashboards** → **Energy**
4. Configure your energy sources using the imported statistics

### Manual Statistics Import

You can also manually import statistics using the Developer Tools:

```yaml
service: recorder.import_statistics
data:
  has_mean: false
  has_sum: true
  statistic_id: sensor.eon_import
  source: recorder
  unit_of_measurement: kWh
  stats: !include /share/eon-output/your_file_import.yaml
```

## Troubleshooting

### Common Issues

1. **Files not processing**: Check file format and ensure it matches supported formats
2. **Import fails**: Verify Home Assistant has recorder component enabled
3. **Web UI not accessible**: Check if port 8099 is available
4. **Auto-processing not working**: Ensure `auto_process` is set to `true`

### Log Analysis

Check the add-on logs for detailed error information:

1. Go to **Supervisor** → **EON-SPOOKER**
2. Click **Logs** tab
3. Look for error messages or warnings

### File Format Detection

The add-on automatically detects file formats, but you can verify detection:

```bash
# Check format detection
python3 /app/EON_SPOOKER_v3.py --dry-run your_file.csv
```

## Development

### Building the Add-on

```bash
# Build for multiple architectures
docker buildx build --platform linux/amd64,linux/arm64,linux/arm/v7 -t eon-spooker .
```

### Local Testing

```bash
# Run locally for testing
docker run -p 8099:8099 -v /path/to/data:/share eon-spooker
```

## Support

- **Issues**: Report bugs on [GitHub Issues](https://github.com/Netesfiu/EON-SPOOKER/issues)
- **Discussions**: Join discussions on [GitHub Discussions](https://github.com/Netesfiu/EON-SPOOKER/discussions)
- **Documentation**: Full documentation available in the repository

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Changelog

### Version 3.0.0
- Complete rewrite as Home Assistant add-on
- Web interface for file management
- Multi-format support with auto-detection
- Direct Home Assistant integration
- File monitoring and auto-processing
- Improved error handling and logging

### Version 2.0.0
- Added support for email attachment formats
- Modular architecture with separate parsers
- Enhanced YAML generation
- Multiple resolution support

### Version 1.0.0
- Initial release
- Basic CSV processing for web portal data
- Simple YAML output generation
