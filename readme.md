# EON-SPOOKER Home Assistant Add-on

![Supports aarch64 Architecture][aarch64-shield]
![Supports amd64 Architecture][amd64-shield]
![Supports armhf Architecture][armhf-shield]
![Supports armv7 Architecture][armv7-shield]
![Supports i386 Architecture][i386-shield]

Process EON energy data files and import statistics directly to Home Assistant.

## About

EON-SPOOKER is a comprehensive Home Assistant add-on that processes energy data files from EON (Hungarian energy company) and imports them directly into your Home Assistant energy dashboard. The add-on features a modern web interface, automatic format detection, and seamless integration with Home Assistant's statistics system.

### Key Features

- 🌐 **Modern Web Interface** - Drag & drop file upload with real-time processing
- 🔍 **Automatic Format Detection** - Supports all EON data formats automatically
- 🏠 **Direct HA Integration** - One-click import to Home Assistant energy dashboard
- 📊 **Multiple Data Sources** - Web portal CSV, email attachments (AP_AM, 180_280)
- ⚡ **High Performance** - Process 3,600+ records per second
- 🛡️ **Robust Error Handling** - Graceful failure with detailed logging
- 📈 **Multi-Resolution Support** - 15-minute, hourly, and daily data
- 🔄 **Automatic Processing** - Monitor folders for new files
- 💾 **Backup & Recovery** - Automatic backup of processed files

## Installation

### Method 1: Add Repository URL

1. Navigate to **Supervisor** → **Add-on Store** in Home Assistant
2. Click the **⋮** menu → **Repositories**
3. Add this repository URL: `https://github.com/Netesfiu/EON-SPOOKER`
4. Find "EON-SPOOKER" in the add-on store and click **Install**

### Method 2: Manual Installation

1. Clone this repository to your Home Assistant add-ons folder:
   ```bash
   cd /usr/share/hassio/addons/local/
   git clone https://github.com/Netesfiu/EON-SPOOKER.git eon-spooker
   ```
2. Restart Home Assistant
3. Navigate to **Supervisor** → **Add-on Store**
4. Find "EON-SPOOKER" in the **Local add-ons** section and click **Install**

## Configuration

### Basic Configuration

```yaml
auto_process: true
input_folder: "/share/eon-data"
output_folder: "/share/eon-output"
resolution: "hourly"
log_level: "info"
auto_import: false
file_patterns:
  - "*.csv"
  - "*.xlsx"
  - "*.xls"
backup_files: true
notification_service: ""
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `auto_process` | bool | `true` | Automatically process uploaded files |
| `input_folder` | string | `/share/eon-data` | Folder to monitor for input files |
| `output_folder` | string | `/share/eon-output` | Folder for processed YAML files |
| `resolution` | list | `hourly` | Data resolution: `15min`, `hourly`, `daily`, `all` |
| `log_level` | list | `info` | Log level: `trace`, `debug`, `info`, `warning`, `error`, `fatal` |
| `auto_import` | bool | `false` | Automatically import statistics to HA |
| `file_patterns` | list | `["*.csv", "*.xlsx", "*.xls"]` | File patterns to monitor |
| `backup_files` | bool | `true` | Backup processed files |
| `notification_service` | string | `""` | HA notification service (optional) |

## Usage

### Web Interface

1. Start the add-on and open the **Web UI**
2. Upload your EON data files using drag & drop or file browser
3. Files are automatically processed and converted to Home Assistant format
4. Click **Import to HA** to add statistics to your energy dashboard

### Supported File Formats

The add-on automatically detects and processes:

- **Legacy Format** - CSV files from EON web portal
- **AP_AM Format** - 15-minute interval data from email attachments
- **180_280 Format** - Daily cumulative meter readings from email attachments

### File Organization

```
/share/
├── eon-data/          # Input files (monitored automatically)
├── eon-output/        # Generated YAML files
└── eon-backup/        # Backup of processed files
```

### Manual Processing

You can also use the command-line interface:

```bash
# Process a single file
python3 /app/EON_SPOOKER_v3.py --output /share/eon-output/result.yaml /share/eon-data/data.csv

# Process multiple files
python3 /app/EON_SPOOKER_v3.py --output /share/eon-output/combined.yaml /share/eon-data/*.csv

# Different resolutions
python3 /app/EON_SPOOKER_v3.py --resolution daily --output daily.yaml data.csv
```

## Home Assistant Integration

### Energy Dashboard Setup

1. Navigate to **Settings** → **Dashboards** → **Energy**
2. Add your electricity consumption/production sensors
3. Use the entity IDs from the generated YAML files
4. The add-on creates sensors like:
   - `sensor.eon_import_energy`
   - `sensor.eon_export_energy`

### Statistics Import

The add-on generates YAML files compatible with Home Assistant's `recorder.import_statistics` service:

```yaml
# Example service call
service: recorder.import_statistics
data:
  statistic_id: "sensor.eon_import_energy"
  source: "recorder"
  statistics: !include /share/eon-output/import_statistics.yaml
```

### Automation Example

```yaml
# Automatically process new files
automation:
  - alias: "Process EON Files"
    trigger:
      - platform: event
        event_type: folder_watcher
        event_data:
          event_type: created
          path: "/share/eon-data/"
    action:
      - service: hassio.addon_stdin
        data:
          addon: "local_eon-spooker"
          input: "process_new_files"
```

## Troubleshooting

### Common Issues

1. **Files not processing**
   - Check file format and encoding (UTF-8 recommended)
   - Verify file permissions in `/share/eon-data/`
   - Check add-on logs for error messages

2. **Statistics not importing**
   - Ensure entity IDs exist in Home Assistant
   - Check YAML file format and syntax
   - Verify recorder integration is enabled

3. **Web interface not accessible**
   - Check if port 8099 is available
   - Restart the add-on
   - Check network configuration

### Log Analysis

Enable debug logging for detailed troubleshooting:

```yaml
log_level: "debug"
```

Check logs in **Supervisor** → **EON-SPOOKER** → **Log**.

## Support

- 📖 [Documentation](https://github.com/Netesfiu/EON-SPOOKER/blob/main/README_V3.md)
- 🐛 [Issue Tracker](https://github.com/Netesfiu/EON-SPOOKER/issues)
- 💬 [Discussions](https://github.com/Netesfiu/EON-SPOOKER/discussions)

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armhf-shield]: https://img.shields.io/badge/armhf-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg
