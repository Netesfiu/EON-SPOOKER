"""
Command-line interface for EON-SPOOKER
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from tkinter import Tk, filedialog
from typing import Optional

from . import __version__
from .csv_parser import CSVParser
from .data_processor import DataProcessor
from .yaml_generator import YAMLGenerator
from .exceptions import EONSpookerError


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s' if verbose else '%(levelname)s: %(message)s'
    
    logging.basicConfig(
        level=level,
        format=format_string,
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def select_file_gui() -> Optional[str]:
    """Open file selection dialog"""
    if os.environ.get('DISPLAY', '') is None:
        raise EnvironmentError('Unable to run GUI file selector. Use the "--path" argument to specify the file path.')
    
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    file_path = filedialog.askopenfilename(
        title="Select E.ON W1000 CSV file",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    
    root.destroy()
    
    if not file_path:
        raise ValueError("No file selected")
    
    return file_path


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser"""
    parser = argparse.ArgumentParser(
        description="Convert E.ON W1000 CSV data to YAML format for Home Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Use GUI file selector
  %(prog)s -p data.csv                        # Process specific file
  %(prog)s -p data.csv -o output/             # Custom output directory
  %(prog)s -p data.csv --timezone "+01:00"   # Custom timezone
  %(prog)s -p data.csv -v                     # Verbose logging
        """
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    parser.add_argument(
        '-p', '--path',
        metavar='FILE',
        help='Path to the E.ON W1000 CSV file'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        metavar='DIR',
        help='Output directory for YAML files (default: current directory)'
    )
    
    parser.add_argument(
        '--import-file',
        metavar='FILENAME',
        default='import.yaml',
        help='Filename for import data YAML (default: import.yaml)'
    )
    
    parser.add_argument(
        '--export-file',
        metavar='FILENAME',
        default='export.yaml',
        help='Filename for export data YAML (default: export.yaml)'
    )
    
    parser.add_argument(
        '--timezone',
        metavar='OFFSET',
        help='Timezone offset in format "+HH:MM" or "-HH:MM" (default: local timezone)'
    )
    
    parser.add_argument(
        '--delimiter',
        metavar='CHAR',
        help='CSV delimiter character (default: auto-detect)'
    )
    
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Do not backup existing output files'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Parse and process data but do not write output files'
    )
    
    return parser


def validate_args(args: argparse.Namespace) -> None:
    """Validate command-line arguments"""
    # Validate timezone format if provided
    if args.timezone:
        if not (len(args.timezone) == 6 and 
                args.timezone[0] in ['+', '-'] and
                args.timezone[3] == ':' and
                args.timezone[1:3].isdigit() and
                args.timezone[4:6].isdigit()):
            raise ValueError("Timezone must be in format '+HH:MM' or '-HH:MM'")
    
    # Validate delimiter if provided
    if args.delimiter and len(args.delimiter) != 1:
        raise ValueError("Delimiter must be a single character")


def main() -> int:
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Validate arguments
        validate_args(args)
        
        # Get input file path
        if args.path:
            csv_file_path = args.path
            if not Path(csv_file_path).exists():
                logger.error(f"File not found: {csv_file_path}")
                return 1
        else:
            logger.info("Opening file selection dialog...")
            csv_file_path = select_file_gui()
        
        logger.info(f"Processing file: {csv_file_path}")
        
        # Parse CSV file
        logger.info("Parsing CSV data...")
        parser_obj = CSVParser(csv_file_path, delimiter=args.delimiter)
        parsed_data = parser_obj.parse()
        
        # Process data
        logger.info("Processing data for Home Assistant format...")
        processor = DataProcessor(timezone_offset=args.timezone)
        processed_data = processor.process_data(parsed_data)
        processor.validate_processed_data(processed_data)
        
        if args.dry_run:
            logger.info("Dry run mode - not writing output files")
            for data_type, data in processed_data.items():
                logger.info(f"{data_type}: {len(data)} data points")
            return 0
        
        # Generate YAML files
        logger.info("Generating YAML files...")
        custom_filenames = {
            'import': args.import_file,
            'export': args.export_file
        }
        
        generator = YAMLGenerator(output_dir=args.output_dir)
        output_paths = generator.generate_yaml_files(
            processed_data,
            custom_filenames=custom_filenames,
            backup_existing=not args.no_backup
        )
        
        # Generate documentation
        documentation = generator.generate_documentation(output_paths, processed_data)
        
        # Print summary
        logger.info("Processing completed successfully!")
        logger.info("Generated files:")
        for data_type, file_path in output_paths.items():
            data_count = len(processed_data[data_type])
            logger.info(f"  {data_type}: {file_path} ({data_count} data points)")
        
        if args.verbose:
            print("\n" + documentation)
        
        return 0
        
    except EONSpookerError as e:
        logger.error(f"EON-SPOOKER error: {e}")
        return 1
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            logger.exception("Full traceback:")
        return 1


if __name__ == '__main__':
    sys.exit(main())
