# Changelog

All notable changes to the EON-SPOOKER Home Assistant add-on will be documented in this file.

## [3.0.0] - 2025-01-08

### Added
- Complete Home Assistant add-on implementation
- Web interface with drag & drop file upload
- Automatic format detection for EON data files
- Support for multiple EON data formats:
  - Legacy format (web portal CSV)
  - AP_AM format (15-minute intervals from email)
  - 180_280 format (daily cumulative from email)
- Direct Home Assistant integration with statistics import
- Real-time file monitoring and processing
- Professional web UI with Bootstrap styling
- Comprehensive error handling and logging
- Multi-resolution data support (15min, hourly, daily)
- Automatic backup of processed files
- Notification system for processing status
- Health monitoring and status reporting
- Docker container with nginx + supervisor
- Modular Python package architecture
- Comprehensive test suite
- Interactive demonstration script

### Changed
- Transformed from single script to professional add-on
- Enhanced cumulative data handling for accurate meter readings
- Improved YAML generation for Home Assistant compatibility
- Optimized performance (3,600+ records/second)

### Fixed
- Correct handling of cumulative meter readings
- Proper timezone handling for all data formats
- Robust error handling for malformed data
- Memory optimization for large files

## [2.0.0] - Previous Version
- Added support for email attachment formats
- Modular architecture with separate parsers
- Enhanced YAML generation
- Multiple resolution support

## [1.0.0] - Initial Release
- Basic CSV processing for web portal data
- Simple YAML output generation
