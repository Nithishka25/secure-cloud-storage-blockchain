"""
STEP 1: Project Configuration and Setup
========================================

This file contains all the configuration settings for the blockchain encryption system.
"""

import os
from pathlib import Path

# ============================================================================
# GANACHE BLOCKCHAIN CONFIGURATION
# ============================================================================

# Ganache RPC Server URL (default when you start Ganache)
GANACHE_URL = "http://127.0.0.1:7545"

# Account settings (Ganache provides 10 accounts by default)
# We'll use the first account as the "server" account
SERVER_ACCOUNT_INDEX = 0

# Gas limit for transactions
GAS_LIMIT = 3000000

# ============================================================================
# CRYPTOGRAPHY CONFIGURATION
# ============================================================================

# AES Settings
AES_KEY_SIZE = 256  # bits (32 bytes)
AES_BLOCK_SIZE = 16  # bytes
AES_MODE = 'GCM'  # Galois/Counter Mode for authenticated encryption

# ECC Settings (using secp256k1 curve - same as Bitcoin/Ethereum)
ECC_CURVE = 'secp256k1'

# Hash Algorithm
HASH_ALGORITHM = 'sha256'

# ============================================================================
# STORAGE CONFIGURATION
# ============================================================================

# Base directory for local storage
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
KEYS_DIR = DATA_DIR / 'keys'
FILES_DIR = DATA_DIR / 'files'
ENCRYPTED_DIR = DATA_DIR / 'encrypted'
BLOCKCHAIN_DIR = DATA_DIR / 'blockchain'

# Create directories if they don't exist
for directory in [DATA_DIR, KEYS_DIR, FILES_DIR, ENCRYPTED_DIR, BLOCKCHAIN_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ============================================================================
# BLOCKCHAIN SETTINGS
# ============================================================================

# Initial block data
GENESIS_BLOCK_DATA = "Genesis Block - Blockchain Encryption System"

# Block metadata fields
BLOCK_FIELDS = {
    'block_id': int,
    'timestamp': str,
    'data': str,  # This will be the encrypted AES key
    'previous_hash': str,
    'hash': str,
    'file_id': str,
    'owner': str
}

# ============================================================================
# FILE SHARING SETTINGS
# ============================================================================

# Maximum number of branches per blockchain
MAX_BRANCHES = 100

# Shared file prefix for branch identification
SHARED_FILE_PREFIX = "shared_"

# ============================================================================
# SYSTEM SETTINGS
# ============================================================================

# Enable debug logging
DEBUG = True

# Maximum file size (in bytes) - 100 MB
MAX_FILE_SIZE = 100 * 1024 * 1024

# Supported file types (empty list means all types allowed)
SUPPORTED_FILE_TYPES = []  # ['.txt', '.pdf', '.docx', '.jpg', '.png']

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_key_path(user_id, key_type='private'):
    """
    Get the path for storing user keys
    
    Args:
        user_id: Unique identifier for the user
        key_type: 'private' or 'public'
    
    Returns:
        Path object for the key file
    """
    return KEYS_DIR / f"{user_id}_{key_type}_key.pem"

def get_blockchain_path(user_id):
    """
    Get the path for storing user's blockchain data
    
    Args:
        user_id: Unique identifier for the user
    
    Returns:
        Path object for the blockchain file
    """
    return BLOCKCHAIN_DIR / f"{user_id}_blockchain.json"

def get_file_path(file_id, encrypted=False):
    """
    Get the path for storing files
    
    Args:
        file_id: Unique identifier for the file
        encrypted: Whether this is for encrypted file
    
    Returns:
        Path object for the file
    """
    directory = ENCRYPTED_DIR if encrypted else FILES_DIR
    return directory / file_id

# ============================================================================
# DISPLAY CONFIGURATION
# ============================================================================

def print_config():
    """Print current configuration settings"""
    print("=" * 80)
    print("BLOCKCHAIN ENCRYPTION SYSTEM - CONFIGURATION")
    print("=" * 80)
    print(f"\n📡 Ganache URL: {GANACHE_URL}")
    print(f"🔐 AES Key Size: {AES_KEY_SIZE} bits")
    print(f"🔑 ECC Curve: {ECC_CURVE}")
    print(f"📁 Data Directory: {DATA_DIR}")
    print(f"🐛 Debug Mode: {DEBUG}")
    print("=" * 80)
    print()

if __name__ == "__main__":
    print_config()
    print("✅ Configuration loaded successfully!")
    print("\n📝 Next Step: Run 'python step2_crypto_aes.py' to implement AES encryption")
