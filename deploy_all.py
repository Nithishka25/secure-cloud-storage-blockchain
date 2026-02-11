#!/usr/bin/env python3
"""Deploy contracts with proper UTF-8 encoding"""
import sys
import os

# Force UTF-8 output encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Now run the deployment
from step10_full_ganache import test_ganache_full

if __name__ == "__main__":
    test_ganache_full()
