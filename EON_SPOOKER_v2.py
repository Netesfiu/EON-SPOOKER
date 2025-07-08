#!/usr/bin/env python3
"""
EON-SPOOKER v2.0 - E.ON W1000 CSV to YAML converter for Home Assistant

This is the new modular version of EON-SPOOKER with improved architecture,
error handling, and additional features.

For backward compatibility, the original EON_SPOOKER.py is preserved.
"""

import sys
from eon_spooker.cli import main

if __name__ == '__main__':
    sys.exit(main())
