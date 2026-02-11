# Dynamic AES Encryption and Blockchain Key Management Implementation

## Project Overview
This project implements the research paper "Dynamic AES Encryption and Blockchain Key Management: A Novel Solution for Cloud Data Security" using Python and Ganache blockchain.

## System Architecture

The system consists of three main components:

1. **Dynamic AES Encryption**: Files are encrypted with unique keys generated from file hash + blockchain hash
2. **ECC Key Management**: Public/private key pairs for securing blockchain blocks
3. **Blockchain Storage**: Private blockchain (Ganache) for storing encrypted keys with metadata

## Project Structure

```
blockchain-encryption/
├── README.md
├── requirements.txt
├── config.py                 # Configuration settings
├── crypto/
│   ├── __init__.py
│   ├── aes_encryption.py     # AES encryption/decryption
│   ├── ecc_encryption.py     # ECC key generation and encryption
│   └── key_generator.py      # Dynamic key generation logic
├── blockchain/
│   ├── __init__.py
│   ├── block.py              # Block structure
│   ├── blockchain.py         # Blockchain management
│   └── ganache_connector.py  # Ganache integration
├── storage/
│   ├── __init__.py
│   ├── file_manager.py       # File upload/download operations
│   └── cloud_simulator.py    # Simulated cloud storage
├── sharing/
│   ├── __init__.py
│   └── file_sharing.py       # Multi-branch blockchain for file sharing
├── tests/
│   ├── __init__.py
│   ├── test_encryption.py
│   ├── test_blockchain.py
│   └── test_integration.py
├── examples/
│   ├── demo_upload.py
│   ├── demo_download.py
│   └── demo_sharing.py
└── main.py                   # Main application interface
```

## Installation Steps

### Step 1: Install Ganache
- Download and install Ganache from https://trufflesuite.com/ganache/
- Start Ganache and note the RPC server URL (usually http://127.0.0.1:7545)

### Step 2: Install Python Dependencies
```bash
pip install web3 pycryptodome ecdsa hashlib pathlib --break-system-packages
```

### Step 3: Configure Ganache Connection
Update `config.py` with your Ganache settings

## Implementation Phases

### Phase 1: Core Cryptography (Steps 1-3)
- AES encryption implementation
- ECC key pair generation
- Dynamic key generation algorithm

### Phase 2: Blockchain Integration (Steps 4-6)
- Block structure definition
- Blockchain class implementation
- Ganache connection and storage

### Phase 3: File Operations (Steps 7-9)
- File encryption and upload
- File decryption and download
- Local and cloud storage management

### Phase 4: File Sharing (Step 10)
- Multi-branch blockchain implementation
- Shared file encryption with recipient's public key
- Permission management

### Phase 5: Testing and Demo (Steps 11-12)
- Unit tests for each component
- Integration tests
- Demo applications

## Key Features Implemented

✅ Dynamic AES-256 encryption with unique keys per file
✅ ECC (secp256k1) public/private key pairs
✅ SHA-256 hashing for key generation
✅ Private blockchain on Ganache
✅ Encrypted block storage (data encrypted with ECC public key)
✅ Multi-branch blockchain for file sharing
✅ File upload/download operations
✅ Secure key management (only user has private key)

## Security Features

1. **File-Level Security**: Each file encrypted with unique dynamic key
2. **Key Protection**: Keys encrypted with ECC before storage
3. **Decentralized Storage**: Blockchain prevents single point of failure
4. **Secure Sharing**: Files shared using recipient's public key
5. **Tamper-Proof**: Blockchain ensures data integrity

## Next Steps

Follow the step-by-step implementation in the numbered Python files.
Each step builds upon the previous one.

Start with: Step 1 - Setting up the project structure and configuration
