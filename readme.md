# EON-SPOOKER Home Assistant Add-on

Process EON energy data files and import statistics directly to Home Assistant.

## Usage

### Supported File Formats

The add-on automatically detects and processes:

- **Legacy Format** - CSV files from EON w1000
- **AP_AM Format** - 15-minute interval data from eon-portal exports
- **180_280 Format** - Daily cumulative meter readings from eon-portal exports

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

`to-do`
