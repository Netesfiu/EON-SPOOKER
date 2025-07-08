# EON-SPOOKER Home Assistant Add-on Structure

This document describes how to set up the EON-SPOOKER add-on in your `hass-addons` repository.

## Directory Structure for hass-addons Repository

```
hass-addons/
├── eon-spooker/
│   ├── config.yaml
│   ├── Dockerfile
│   ├── run.sh
│   ├── icon.png
│   ├── README.md
│   ├── CHANGELOG.md
│   └── apparmor.txt
└── repository.yaml
```

## Files to Copy

### 1. config.yaml
Copy from: `eon_spooker_addon/config.yaml`
```yaml
name: "EON-SPOOKER"
description: "Convert EON energy meter CSV reports to Home Assistant statistics format"
version: "3.0.1"
slug: "eon_spooker"
init: false
arch:
  - aarch64
  - amd64
  - armhf
  - armv7
  - i386
startup: application
boot: manual
options:
  input_directory: "/share/eon_data"
  output_directory: "/share/eon_output"
  auto_process: false
  log_level: "info"
schema:
  input_directory: "str"
  output_directory: "str"
  auto_process: "bool"
  log_level: "list(debug|info|warning|error)?"
map:
  - "share:rw"
  - "config:r"
ports:
  "8099/tcp": 8099
ports_description:
  "8099/tcp": "Web interface"
webui: "http://[HOST]:[PORT:8099]"
```

### 2. Dockerfile
Copy from: `eon_spooker_addon/Dockerfile`

### 3. run.sh
Copy from: `eon_spooker_addon/run.sh`

### 4. icon.png
Copy from: `eon_spooker_addon/icon.png`
(Replace with proper 512x512 icon)

### 5. README.md (Add-on specific)
```markdown
# EON-SPOOKER Home Assistant Add-on

Convert EON energy meter CSV reports to Home Assistant statistics format.

## Installation

1. Add this repository to your Home Assistant add-on store
2. Install the EON-SPOOKER add-on
3. Configure the add-on options
4. Start the add-on

## Configuration

- `input_directory`: Directory where CSV files are located (default: /share/eon_data)
- `output_directory`: Directory where YAML files will be saved (default: /share/eon_output)
- `auto_process`: Automatically process new files (default: false)
- `log_level`: Logging level (debug, info, warning, error)

## Usage

1. Upload your EON CSV files to the configured input directory
2. Access the web interface at http://homeassistant.local:8099
3. Process files through the web interface or enable auto_process
4. Import the generated YAML files into Home Assistant

## Supported Formats

- Legacy format (original EON reports)
- AP_AM format (15-minute interval data)
- 180_280 format (daily cumulative data)
- Combined format processing

## Support

For issues and feature requests, visit: https://github.com/Netesfiu/EON-SPOOKER
```

### 6. repository.yaml (Root of hass-addons repo)
```yaml
name: "Netesfiu's Home Assistant Add-ons"
url: "https://github.com/Netesfiu/hass-addons"
maintainer: "Netesfiu"
```

## Installation Instructions

1. Clone your hass-addons repository
2. Create the `eon-spooker` directory
3. Copy the files from `eon_spooker_addon/` to `hass-addons/eon-spooker/`
4. Update the repository.yaml if needed
5. Commit and push to GitHub
6. Add the repository URL to Home Assistant

## Add-on Repository URL
```
https://github.com/Netesfiu/hass-addons
```

Users will add this URL in Home Assistant under:
Supervisor → Add-on Store → ⋮ → Repositories
