#!/usr/bin/env python3
"""
Quick test to check if encrypted files are accessible
"""
import json
from pathlib import Path
import config

# List encrypted files
encrypted_dir = config.ENCRYPTED_DIR
print(f"Encrypted dir: {encrypted_dir}")
print(f"Exists: {encrypted_dir.exists()}")

if encrypted_dir.exists():
    files = list(encrypted_dir.iterdir())
    print(f"\nTotal encrypted files: {len(files)}")
    
    if files:
        print("\nFirst 5 files:")
        for f in files[:5]:
            print(f"  {f.name}")
else:
    print("Encrypted directory does not exist!")
