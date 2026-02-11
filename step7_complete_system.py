"""
STEP 7: Complete System Integration
====================================

This module integrates all components into a complete file encryption system.
"""

import os
import uuid
from pathlib import Path
import json

# Import our modules
from step2_crypto_aes import AESEncryption
from step3_crypto_ecc import ECCEncryption
from step4_dynamic_key_gen import DynamicKeyGenerator
from step5_blockchain_structure import Blockchain, Block
import config


class SecureCloudStorage:
    """
    Complete secure cloud storage system
    
    Combines:
    - Dynamic AES encryption
    - ECC key management
    - Blockchain key storage
    
    Features:
    - Upload encrypted files
    - Download and decrypt files
    - Share files securely
    - Manage encryption keys via blockchain
    """
    
    def __init__(self, user_id):
        """
        Initialize storage system for a user
        
        Args:
            user_id: str - Unique user identifier
        """
        self.user_id = user_id
        self.aes = AESEncryption()
        self.ecc = ECCEncryption()
        self.keygen = DynamicKeyGenerator()
        
        # Load or create ECC keys
        self.private_key, self.public_key = self.ecc.load_keys(user_id)
        if not self.private_key:
            print(f"🔑 Generating new ECC key pair for {user_id}...")
            self.private_key, self.public_key = self.ecc.generate_key_pair()
            self.ecc.save_keys(self.private_key, self.public_key, user_id)
        
        # Load or create blockchain
        blockchain_path = config.get_blockchain_path(user_id)
        if blockchain_path.exists():
            self.blockchain = Blockchain.load_from_file(blockchain_path)
            print(f"📂 Loaded blockchain with {len(self.blockchain)} blocks")
        else:
            self.blockchain = Blockchain(user_id)
            self.blockchain.create_genesis_block()
            self.blockchain.save_to_file()
            print(f"🔗 Created new blockchain for {user_id}")
    
    def upload_file(self, file_path):
        """
        Upload and encrypt a file
        
        Process (from paper):
        1. Read file data
        2. Get latest block from blockchain
        3. Generate dynamic key = hash(file) XOR hash(block)
        4. Encrypt file with AES using dynamic key
        5. Create new block with encrypted key
        6. Encrypt block with ECC public key
        7. Store encrypted file and block
        
        Args:
            file_path: str or Path - File to upload
            
        Returns:
            dict: Upload result with file_id and block info
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if file_path.stat().st_size > config.MAX_FILE_SIZE:
            raise ValueError(f"File too large (max {config.MAX_FILE_SIZE} bytes)")
        
        print(f"\n📤 Uploading: {file_path.name}")
        print("-" * 80)
        
        # 1. Read file
        with open(file_path, 'rb') as f:
            file_data = f.read()
        print(f"✅ Read file: {len(file_data)} bytes")
        
        # 2. Get latest block
        latest_block = self.blockchain.get_latest_block()
        latest_block_content = latest_block.to_dict()
        print(f"✅ Got latest block: #{latest_block.block_id}")
        
        # 3. Generate dynamic key
        dynamic_key = self.keygen.generate_dynamic_key(file_data, latest_block_content)
        print(f"✅ Generated dynamic key: {dynamic_key.hex()[:32]}...")
        
        # 4. Encrypt file with AES
        encrypted_file_data = self.aes.encrypt_file(file_data, dynamic_key)
        print(f"✅ Encrypted file with AES-256-GCM")
        
        # 5. Generate unique file ID
        file_id = str(uuid.uuid4())
        
        # 6. Save encrypted file
        encrypted_file_path = config.get_file_path(file_id, encrypted=True)
        encrypted_file_bundle = {
            'ciphertext': encrypted_file_data['ciphertext'].hex(),
            'nonce': encrypted_file_data['nonce'].hex(),
            'tag': encrypted_file_data['tag'].hex(),
            'original_name': file_path.name
        }
        
        with open(encrypted_file_path, 'w') as f:
            json.dump(encrypted_file_bundle, f)
        print(f"✅ Saved encrypted file: {file_id}")
        
        # 7. Encrypt the AES key with ECC public key
        encrypted_key_data = self.ecc.encrypt_data(dynamic_key, self.public_key)
        
        # Convert to JSON-serializable format
        block_data = {
            'ciphertext': encrypted_key_data['ciphertext'].hex(),
            'nonce': encrypted_key_data['nonce'].hex(),
            'tag': encrypted_key_data['tag'].hex(),
            'encrypted_key': encrypted_key_data['encrypted_key'].hex(),
            'key_nonce': encrypted_key_data['key_nonce'].hex(),
            'key_tag': encrypted_key_data['key_tag'].hex(),
            'ephemeral_public_key': encrypted_key_data['ephemeral_public_key'].hex()
        }
        
        # 8. Add block to blockchain
        new_block = self.blockchain.add_block(
            data=json.dumps(block_data),
            file_id=file_id
        )
        print(f"✅ Created block #{new_block.block_id}")
        
        # 9. Save blockchain
        self.blockchain.save_to_file()
        print(f"✅ Saved blockchain")
        
        return {
            'file_id': file_id,
            'original_name': file_path.name,
            'size': len(file_data),
            'block_id': new_block.block_id,
            'encrypted_file_path': str(encrypted_file_path)
        }
    
    def download_file(self, file_id, output_path=None):
        """
        Download and decrypt a file
        
        Process:
        1. Get block for file_id
        2. Decrypt block with ECC private key to get AES key
        3. Load encrypted file
        4. Decrypt file with AES key
        5. Save decrypted file
        
        Args:
            file_id: str - File identifier
            output_path: str or Path - Where to save (optional)
            
        Returns:
            Path: Path to decrypted file
        """
        print(f"\n📥 Downloading: {file_id}")
        print("-" * 80)
        
        # 1. Get block
        block = self.blockchain.get_block_by_file_id(file_id)
        if not block:
            raise ValueError(f"File not found: {file_id}")
        print(f"✅ Found block #{block.block_id}")
        
        # 2. Decrypt block to get AES key
        block_data = json.loads(block.data)
        
        # Reconstruct encrypted data structure
        encrypted_key_data = {
            'ciphertext': bytes.fromhex(block_data['ciphertext']),
            'nonce': bytes.fromhex(block_data['nonce']),
            'tag': bytes.fromhex(block_data['tag']),
            'encrypted_key': bytes.fromhex(block_data['encrypted_key']),
            'key_nonce': bytes.fromhex(block_data['key_nonce']),
            'key_tag': bytes.fromhex(block_data['key_tag']),
            'ephemeral_public_key': bytes.fromhex(block_data['ephemeral_public_key'])
        }
        
        # Decrypt with private key
        dynamic_key = self.ecc.decrypt_data(encrypted_key_data, self.private_key)
        print(f"✅ Decrypted AES key from block")
        
        # 3. Load encrypted file
        encrypted_file_path = config.get_file_path(file_id, encrypted=True)
        with open(encrypted_file_path, 'r') as f:
            encrypted_file_bundle = json.load(f)
        
        # 4. Decrypt file
        encrypted_file_data = {
            'ciphertext': bytes.fromhex(encrypted_file_bundle['ciphertext']),
            'nonce': bytes.fromhex(encrypted_file_bundle['nonce']),
            'tag': bytes.fromhex(encrypted_file_bundle['tag'])
        }
        
        decrypted_data = self.aes.decrypt_file(encrypted_file_data, dynamic_key)
        print(f"✅ Decrypted file: {len(decrypted_data)} bytes")
        
        # 5. Save decrypted file
        if output_path is None:
            output_path = config.FILES_DIR / encrypted_file_bundle['original_name']
        else:
            output_path = Path(output_path)
        
        with open(output_path, 'wb') as f:
            f.write(decrypted_data)
        print(f"✅ Saved to: {output_path}")
        
        return output_path
    
    def list_files(self):
        """
        List all uploaded files
        
        Returns:
            list: File information
        """
        files = []
        
        for block in self.blockchain.chain[1:]:  # Skip genesis
            encrypted_path = config.get_file_path(block.file_id, encrypted=True)
            
            if encrypted_path.exists():
                with open(encrypted_path, 'r') as f:
                    bundle = json.load(f)
                
                files.append({
                    'file_id': block.file_id,
                    'name': bundle['original_name'],
                    'block_id': block.block_id,
                    'timestamp': block.timestamp
                })
        
        return files
    
    def share_file(self, file_id, recipient_user_id):
        """
        Share a file with another user
        
        Process:
        1. Get recipient's public key
        2. Get file's AES key (decrypt from our block)
        3. Encrypt AES key with recipient's public key
        4. Create branch in recipient's blockchain
        
        Args:
            file_id: str - File to share
            recipient_user_id: str - User to share with
            
        Returns:
            dict: Sharing info
        """
        print(f"\n🤝 Sharing {file_id} with {recipient_user_id}")
        print("-" * 80)
        
        # 1. Get recipient's public key
        recipient_ecc = ECCEncryption()
        _, recipient_public_key = recipient_ecc.load_keys(recipient_user_id)
        
        if not recipient_public_key:
            raise ValueError(f"Recipient {recipient_user_id} not found (no public key)")
        
        print(f"✅ Got recipient's public key")
        
        # 2. Get our block and decrypt to get AES key
        block = self.blockchain.get_block_by_file_id(file_id)
        if not block:
            raise ValueError(f"File not found: {file_id}")
        
        block_data = json.loads(block.data)
        encrypted_key_data = {
            'ciphertext': bytes.fromhex(block_data['ciphertext']),
            'nonce': bytes.fromhex(block_data['nonce']),
            'tag': bytes.fromhex(block_data['tag']),
            'encrypted_key': bytes.fromhex(block_data['encrypted_key']),
            'key_nonce': bytes.fromhex(block_data['key_nonce']),
            'key_tag': bytes.fromhex(block_data['key_tag']),
            'ephemeral_public_key': bytes.fromhex(block_data['ephemeral_public_key'])
        }
        
        aes_key = self.ecc.decrypt_data(encrypted_key_data, self.private_key)
        print(f"✅ Retrieved AES key")
        
        # 3. Encrypt AES key for recipient
        shared_key_data = recipient_ecc.encrypt_data(aes_key, recipient_public_key)
        
        shared_block_data = {
            'ciphertext': shared_key_data['ciphertext'].hex(),
            'nonce': shared_key_data['nonce'].hex(),
            'tag': shared_key_data['tag'].hex(),
            'encrypted_key': shared_key_data['encrypted_key'].hex(),
            'key_nonce': shared_key_data['key_nonce'].hex(),
            'key_tag': shared_key_data['key_tag'].hex(),
            'ephemeral_public_key': shared_key_data['ephemeral_public_key'].hex(),
            'shared_from': self.user_id,
            'original_file_id': file_id
        }
        
        print(f"✅ Encrypted key for recipient")
        
        # Return sharing data (recipient would add to their blockchain)
        return {
            'file_id': file_id,
            'shared_block_data': shared_block_data,
            'recipient': recipient_user_id,
            'sender': self.user_id
        }
    
    def get_public_key_hex(self):
        """Get public key as hex string for sharing"""
        return ECCEncryption.public_key_to_string(self.public_key)


# ============================================================================
# TESTING AND DEMONSTRATION
# ============================================================================

def test_complete_system():
    """Test the complete integrated system"""
    print("=" * 80)
    print("TESTING COMPLETE SECURE CLOUD STORAGE SYSTEM")
    print("=" * 80)
    
    # Create test file
    test_file = config.FILES_DIR / "test_document.txt"
    test_content = """This is a confidential document that needs to be encrypted.
It contains sensitive information that must be protected.
Using dynamic AES encryption with blockchain key management.
"""
    
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    print(f"\n📄 Created test file: {test_file}")
    
    # Test 1: Initialize User
    print("\n📝 Test 1: User Initialization")
    print("-" * 80)
    
    storage = SecureCloudStorage("alice")
    print(f"✅ Initialized storage for Alice")
    print(f"   Public key: {storage.get_public_key_hex()[:32]}...")
    
    # Test 2: Upload File
    print("\n📝 Test 2: Upload and Encrypt File")
    print("-" * 80)
    
    result = storage.upload_file(test_file)
    file_id = result['file_id']
    
    print(f"\n✅ Upload successful!")
    print(f"   File ID: {file_id}")
    print(f"   Block: #{result['block_id']}")
    print(f"   Size: {result['size']} bytes")
    
    # Test 3: List Files
    print("\n📝 Test 3: List Files")
    print("-" * 80)
    
    files = storage.list_files()
    for f in files:
        print(f"📄 {f['name']}")
        print(f"   ID: {f['file_id']}")
        print(f"   Block: #{f['block_id']}")
        print(f"   Time: {f['timestamp']}")
    
    # Test 4: Download File
    print("\n📝 Test 4: Download and Decrypt File")
    print("-" * 80)
    
    output_file = config.FILES_DIR / "downloaded_document.txt"
    downloaded_path = storage.download_file(file_id, output_file)
    
    # Verify content
    with open(downloaded_path, 'r') as f:
        downloaded_content = f.read()
    
    if downloaded_content == test_content:
        print("✅ File content matches original!")
    else:
        print("❌ File content mismatch!")
        return False
    
    # Test 5: Upload Multiple Files
    print("\n📝 Test 5: Upload Multiple Files")
    print("-" * 80)
    
    for i in range(3):
        test_file_i = config.FILES_DIR / f"file_{i}.txt"
        with open(test_file_i, 'w') as f:
            f.write(f"Content of file {i}")
        
        result = storage.upload_file(test_file_i)
        print(f"✅ Uploaded file_{i}.txt → Block #{result['block_id']}")
    
    print(f"\n📊 Blockchain now has {len(storage.blockchain)} blocks")
    
    # Test 6: File Sharing
    print("\n📝 Test 6: File Sharing")
    print("-" * 80)
    
    # Create Bob
    storage_bob = SecureCloudStorage("bob")
    print(f"✅ Created user Bob")
    
    # Alice shares file with Bob
    share_info = storage.share_file(file_id, "bob")
    print(f"✅ Alice shared file with Bob")
    print(f"   Encrypted with Bob's public key")
    
    # Test 7: Blockchain Validation
    print("\n📝 Test 7: Blockchain Integrity")
    print("-" * 80)
    
    if storage.blockchain.validate_chain():
        print("✅ Blockchain is valid and tamper-proof")
    else:
        print("❌ Blockchain validation failed!")
        return False
    
    print("\n" + "=" * 80)
    print("ALL TESTS PASSED! ✅")
    print("=" * 80)
    print("\n🎉 Complete System Summary:")
    print("   ✅ Dynamic AES encryption working")
    print("   ✅ ECC key management operational")
    print("   ✅ Blockchain key storage functional")
    print("   ✅ File upload/download working")
    print("   ✅ File sharing enabled")
    print("   ✅ Tamper-proof blockchain validated")
    print("\n📝 Next Step: Run 'python step8_demo_app.py' for interactive demo")
    
    return True


if __name__ == "__main__":
    test_complete_system()
