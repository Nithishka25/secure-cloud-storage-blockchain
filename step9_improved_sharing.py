"""
UPDATED: Complete File Sharing Implementation
==============================================

This fixes the file sharing so recipients can actually see and download shared files.
Also includes proper Ganache integration.
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
    Complete secure cloud storage system with proper file sharing
    """
    
    def __init__(self, user_id):
        """Initialize storage system for a user"""
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
        """Upload and encrypt a file"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if file_path.stat().st_size > config.MAX_FILE_SIZE:
            raise ValueError(f"File too large (max {config.MAX_FILE_SIZE} bytes)")
        
        print(f"\n📤 Uploading: {file_path.name}")
        print("-" * 80)
        
        # Read file
        with open(file_path, 'rb') as f:
            file_data = f.read()
        print(f"✅ Read file: {len(file_data)} bytes")
        
        # Get latest block
        latest_block = self.blockchain.get_latest_block()
        latest_block_content = latest_block.to_dict()
        print(f"✅ Got latest block: #{latest_block.block_id}")
        
        # Generate dynamic key
        dynamic_key = self.keygen.generate_dynamic_key(file_data, latest_block_content)
        print(f"✅ Generated dynamic key: {dynamic_key.hex()[:32]}...")
        
        # Encrypt file with AES
        encrypted_file_data = self.aes.encrypt_file(file_data, dynamic_key)
        print(f"✅ Encrypted file with AES-256-GCM")
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        
        # Save encrypted file
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
        
        # Encrypt the AES key with ECC public key
        encrypted_key_data = self.ecc.encrypt_data(dynamic_key, self.public_key)
        
        # Convert to JSON-serializable format
        block_data = {
            'ciphertext': encrypted_key_data['ciphertext'].hex(),
            'nonce': encrypted_key_data['nonce'].hex(),
            'tag': encrypted_key_data['tag'].hex(),
            'encrypted_key': encrypted_key_data['encrypted_key'].hex(),
            'key_nonce': encrypted_key_data['key_nonce'].hex(),
            'key_tag': encrypted_key_data['key_tag'].hex(),
            'ephemeral_public_key': encrypted_key_data['ephemeral_public_key'].hex(),
            'is_shared': False,
            'owner': self.user_id
        }
        
        # Add block to blockchain
        new_block = self.blockchain.add_block(
            data=json.dumps(block_data),
            file_id=file_id
        )
        print(f"✅ Created block #{new_block.block_id}")
        
        # Save blockchain
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
        """Download and decrypt a file"""
        print(f"\n📥 Downloading: {file_id}")
        print("-" * 80)
        
        # Get block
        block = self.blockchain.get_block_by_file_id(file_id)
        if not block:
            raise ValueError(f"File not found: {file_id}")
        print(f"✅ Found block #{block.block_id}")
        
        # Decrypt block to get AES key
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
        
        # Load encrypted file
        encrypted_file_path = config.get_file_path(file_id, encrypted=True)
        with open(encrypted_file_path, 'r') as f:
            encrypted_file_bundle = json.load(f)
        
        # Decrypt file
        encrypted_file_data = {
            'ciphertext': bytes.fromhex(encrypted_file_bundle['ciphertext']),
            'nonce': bytes.fromhex(encrypted_file_bundle['nonce']),
            'tag': bytes.fromhex(encrypted_file_bundle['tag'])
        }
        
        decrypted_data = self.aes.decrypt_file(encrypted_file_data, dynamic_key)
        print(f"✅ Decrypted file: {len(decrypted_data)} bytes")
        
        # Save decrypted file
        if output_path is None:
            output_path = config.FILES_DIR / encrypted_file_bundle['original_name']
        else:
            output_path = Path(output_path)
        
        with open(output_path, 'wb') as f:
            f.write(decrypted_data)
        print(f"✅ Saved to: {output_path}")
        
        return output_path
    
    def list_files(self, include_shared=True):
        """
        List all files (own and shared)
        
        Args:
            include_shared: bool - Whether to include shared files
            
        Returns:
            list: File information
        """
        files = []
        
        for block in self.blockchain.chain[1:]:  # Skip genesis
            encrypted_path = config.get_file_path(block.file_id, encrypted=True)
            
            if encrypted_path.exists():
                with open(encrypted_path, 'r') as f:
                    bundle = json.load(f)
                
                # Get block data to check if shared
                block_data = json.loads(block.data)
                is_shared = block_data.get('is_shared', False)
                shared_from = block_data.get('shared_from', None)
                
                files.append({
                    'file_id': block.file_id,
                    'name': bundle['original_name'],
                    'block_id': block.block_id,
                    'timestamp': block.timestamp,
                    'is_shared': is_shared,
                    'shared_from': shared_from,
                    'type': 'shared' if is_shared else 'own'
                })
        
        return files
    
    def share_file(self, file_id, recipient_user_id):
        """
        Share a file with another user - FIXED VERSION
        
        This now properly adds the shared file to recipient's blockchain
        """
        print(f"\n🤝 Sharing {file_id} with {recipient_user_id}")
        print("-" * 80)
        
        # 1. Get recipient's storage instance
        recipient_storage = SecureCloudStorage(recipient_user_id)
        
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
        shared_key_data = recipient_storage.ecc.encrypt_data(aes_key, recipient_storage.public_key)
        
        shared_block_data = {
            'ciphertext': shared_key_data['ciphertext'].hex(),
            'nonce': shared_key_data['nonce'].hex(),
            'tag': shared_key_data['tag'].hex(),
            'encrypted_key': shared_key_data['encrypted_key'].hex(),
            'key_nonce': shared_key_data['key_nonce'].hex(),
            'key_tag': shared_key_data['key_tag'].hex(),
            'ephemeral_public_key': shared_key_data['ephemeral_public_key'].hex(),
            'is_shared': True,
            'shared_from': self.user_id,
            'original_file_id': file_id,
            'owner': recipient_user_id
        }
        
        print(f"✅ Encrypted key for recipient")
        
        # 4. Add block to recipient's blockchain (THIS IS THE KEY FIX!)
        new_block = recipient_storage.blockchain.add_block(
            data=json.dumps(shared_block_data),
            file_id=file_id  # Same file_id so they access the same encrypted file
        )
        
        # 5. Save recipient's blockchain
        recipient_storage.blockchain.save_to_file()
        print(f"✅ Added to {recipient_user_id}'s blockchain (Block #{new_block.block_id})")
        
        # 6. Create a sharing record
        share_record = {
            'file_id': file_id,
            'sender': self.user_id,
            'recipient': recipient_user_id,
            'shared_block_id': new_block.block_id,
            'timestamp': new_block.timestamp
        }
        
        # Save sharing record for tracking
        shares_path = config.DATA_DIR / 'shares.json'
        if shares_path.exists():
            with open(shares_path, 'r') as f:
                shares = json.load(f)
        else:
            shares = []
        
        shares.append(share_record)
        
        with open(shares_path, 'w') as f:
            json.dump(shares, f, indent=2)
        
        print(f"✅ File successfully shared with {recipient_user_id}!")
        print(f"   They can now see it in their file list (marked as 'shared')")
        
        return share_record
    
    def get_public_key_hex(self):
        """Get public key as hex string for sharing"""
        return ECCEncryption.public_key_to_string(self.public_key)


# Test the improved sharing
if __name__ == "__main__":
    print("=" * 80)
    print("TESTING IMPROVED FILE SHARING")
    print("=" * 80)
    
    # Create test file
    test_file = config.FILES_DIR / "shared_test.txt"
    with open(test_file, 'w') as f:
        f.write("This file will be shared between Alice and Bob!")
    
    print("\n📝 Step 1: Alice uploads a file")
    print("-" * 80)
    alice = SecureCloudStorage("alice")
    result = alice.upload_file(test_file)
    file_id = result['file_id']
    print(f"✅ Alice uploaded: {result['original_name']}")
    print(f"   File ID: {file_id}")
    
    print("\n📝 Step 2: Alice shares file with Bob")
    print("-" * 80)
    share_info = alice.share_file(file_id, "bob")
    
    print("\n📝 Step 3: Bob lists his files (should see shared file)")
    print("-" * 80)
    bob = SecureCloudStorage("bob")
    bob_files = bob.list_files()
    
    print(f"Bob's files ({len(bob_files)} total):")
    for f in bob_files:
        status = "📤 Shared from " + f['shared_from'] if f['is_shared'] else "📁 Own file"
        print(f"  {status}: {f['name']}")
    
    print("\n📝 Step 4: Bob downloads the shared file")
    print("-" * 80)
    bob_output = config.FILES_DIR / "bob_received_file.txt"
    bob.download_file(file_id, bob_output)
    
    # Verify
    with open(bob_output, 'r') as f:
        bob_content = f.read()
    
    with open(test_file, 'r') as f:
        original_content = f.read()
    
    if bob_content == original_content:
        print("\n✅ SUCCESS! Bob can access Alice's shared file!")
        print("   Content matches original perfectly")
    else:
        print("\n❌ Content mismatch!")
    
    print("\n" + "=" * 80)
    print("FILE SHARING TEST COMPLETE!")
    print("=" * 80)
