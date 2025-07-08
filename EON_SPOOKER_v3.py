#!/usr/bin/env python3
"""
EON-SPOOKER v3.0 - Enhanced Energy Data Processor
Supports legacy web portal format + new email-based xlsx formats (AP_AM & 180_280)

Features:
- Automatic format detection
- Multi-file processing
- 15-minute, hourly, and daily data aggregation
- Home Assistant YAML export
- Backward compatibility with v2.0

Author: Enhanced for v3.0 with email format support
"""

import argparse
import logging
import sys
import yaml
from pathlib import Path
from typing import List, Optional

from eon_spooker.unified_parser import parse_eon_file, parse_eon_files
from eon_spooker.yaml_generator import YAMLGenerator
from eon_spooker.exceptions import EONSpookerError


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def validate_files(file_paths: List[str]) -> List[str]:
    """Validate that all input files exist"""
    valid_files = []
    for file_path in file_paths:
        path = Path(file_path)
        if not path.exists():
            print(f"Warning: File not found: {file_path}")
            continue
        if not path.is_file():
            print(f"Warning: Not a file: {file_path}")
            continue
        valid_files.append(str(path.absolute()))
    
    if not valid_files:
        raise EONSpookerError("No valid input files found")
    
    return valid_files


def print_summary(result: dict) -> None:
    """Print processing summary"""
    print("\n" + "="*60)
    print("EON-SPOOKER v3.0 - Processing Summary")
    print("="*60)
    
    if 'formats' in result:
        # Multi-file result
        print(f"Files processed: {len(result['files'])}")
        print(f"Formats detected: {', '.join(result['formats'])}")
        print(f"Total records: {result['total_records']}")
        
        if result['metadata'].get('processing_errors'):
            print(f"Errors: {len(result['metadata']['processing_errors'])}")
            for error in result['metadata']['processing_errors']:
                print(f"  - {error}")
        
        if 'overall_date_range' in result['metadata']:
            date_range = result['metadata']['overall_date_range']
            print(f"Date range: {date_range['start'].date()} to {date_range['end'].date()}")
        
        print(f"Hourly records: {len(result.get('hourly_data', []))}")
        print(f"Daily records: {len(result.get('daily_data', []))}")
    
    else:
        # Single file result
        print(f"Format: {result['format']}")
        print(f"Records: {result['metadata']['total_records']}")
        
        if 'date_range' in result['metadata']:
            date_range = result['metadata']['date_range']
            if 'start' in date_range and 'end' in date_range:
                print(f"Date range: {date_range['start'].date()} to {date_range['end'].date()}")
                if 'days' in date_range:
                    print(f"Duration: {date_range['days']} days")
        
        print(f"Hourly records: {len(result.get('hourly_data', []))}")
        print(f"Daily records: {len(result.get('daily_data', []))}")
    
    print("="*60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="EON-SPOOKER v3.0 - Enhanced Energy Data Processor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single file (auto-detect format)
  python EON_SPOOKER_v3.py data.csv
  
  # Process multiple files
  python EON_SPOOKER_v3.py AP_AM.csv 180_280.csv
  
  # Override format detection
  python EON_SPOOKER_v3.py --format ap_am data.csv
  
  # Custom output file and resolution
  python EON_SPOOKER_v3.py --output energy_data.yaml --resolution hourly data.csv
  
  # Verbose logging
  python EON_SPOOKER_v3.py --verbose data.csv

Supported formats:
  - legacy: Original EON web portal format
  - ap_am: 15-minute interval data from email
  - 180_280: Daily cumulative readings from email
  - auto: Automatic detection (default)
        """
    )
    
    # Input files
    parser.add_argument(
        'files',
        nargs='+',
        help='CSV file(s) to process'
    )
    
    # Output options
    parser.add_argument(
        '-o', '--output',
        default='export.yaml',
        help='Output YAML file (default: export.yaml)'
    )
    
    # Format options
    parser.add_argument(
        '--format',
        choices=['auto', 'legacy', 'ap_am', '180_280'],
        default='auto',
        help='Force specific format (default: auto-detect)'
    )
    
    parser.add_argument(
        '--delimiter',
        default=';',
        help='CSV delimiter (default: ;)'
    )
    
    # Resolution options
    parser.add_argument(
        '--resolution',
        choices=['15min', 'hourly', 'daily', 'all'],
        default='hourly',
        help='Output time resolution (default: hourly)'
    )
    
    # Processing options
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Parse files but do not generate output'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Validate input files
        valid_files = validate_files(args.files)
        logger.info(f"Processing {len(valid_files)} file(s)")
        
        # Parse files
        if len(valid_files) == 1:
            # Single file processing
            format_override = None if args.format == 'auto' else args.format
            result = parse_eon_file(valid_files[0], args.delimiter, format_override)
        else:
            # Multi-file processing
            if args.format != 'auto':
                logger.warning("Format override ignored for multi-file processing (auto-detection used)")
            result = parse_eon_files(valid_files, args.delimiter)
        
        # Print summary
        print_summary(result)
        
        # Generate output
        if not args.dry_run:
            logger.info(f"Generating YAML output: {args.output}")
            
            yaml_generator = YAMLGenerator()
            
            # Determine which data to export based on resolution
            if args.resolution == '15min' and 'raw_data' in result:
                export_data = result['raw_data']
            elif args.resolution == 'hourly':
                export_data = result.get('hourly_data', [])
            elif args.resolution == 'daily':
                export_data = result.get('daily_data', [])
            elif args.resolution == 'all':
                # Export all available resolutions
                export_data = {
                    'hourly': result.get('hourly_data', []),
                    'daily': result.get('daily_data', [])
                }
                if 'raw_data' in result:
                    export_data['15min'] = result['raw_data']
            else:
                export_data = result.get('hourly_data', [])
            
            # Generate YAML
            if isinstance(export_data, dict):
                # Multi-resolution export
                yaml_content = yaml_generator.generate_multi_resolution_yaml(export_data)
            else:
                # Single resolution export - returns dict with import/export
                ha_data = yaml_generator._convert_to_ha_format(export_data)
                
                # Generate separate files for import and export
                base_name = Path(args.output).stem
                base_dir = Path(args.output).parent
                
                # Write import file
                if ha_data.get('import'):
                    import_file = base_dir / f"{base_name}_import.yaml"
                    import_header = f"# Home Assistant statistics data for import\n"
                    import_header += f"# Generated by EON-SPOOKER v3.0\n"
                    import_header += f"# Data points: {len(ha_data['import'])}\n\n"
                    import_yaml = yaml.dump(ha_data['import'], 
                                          default_flow_style=False,
                                          allow_unicode=True,
                                          sort_keys=False,
                                          indent=2)
                    
                    with open(import_file, 'w', encoding='utf-8') as f:
                        f.write(import_header + import_yaml)
                    
                    print(f"\nImport YAML written to: {import_file}")
                    import_size = import_file.stat().st_size
                    print(f"Import file size: {import_size:,} bytes")
                
                # Write export file
                if ha_data.get('export'):
                    export_file = base_dir / f"{base_name}_export.yaml"
                    export_header = f"# Home Assistant statistics data for export\n"
                    export_header += f"# Generated by EON-SPOOKER v3.0\n"
                    export_header += f"# Data points: {len(ha_data['export'])}\n\n"
                    export_yaml = yaml.dump(ha_data['export'], 
                                          default_flow_style=False,
                                          allow_unicode=True,
                                          sort_keys=False,
                                          indent=2)
                    
                    with open(export_file, 'w', encoding='utf-8') as f:
                        f.write(export_header + export_yaml)
                    
                    print(f"Export YAML written to: {export_file}")
                    export_size = export_file.stat().st_size
                    print(f"Export file size: {export_size:,} bytes")
                
                # Also create combined file for backward compatibility
                combined_yaml = f"# Combined import/export data\n# Generated by EON-SPOOKER v3.0\n\n"
                combined_yaml += yaml.dump(ha_data, 
                                         default_flow_style=False,
                                         allow_unicode=True,
                                         sort_keys=False,
                                         indent=2)
                
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(combined_yaml)
                
                print(f"Combined YAML written to: {args.output}")
                output_size = Path(args.output).stat().st_size
                print(f"Combined file size: {output_size:,} bytes")
        
        else:
            print("\nDry run completed - no output file generated")
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    
    except EONSpookerError as e:
        logger.error(f"EON-SPOOKER error: {e}")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
