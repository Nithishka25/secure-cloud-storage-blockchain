"""
STEP 12: Integrated System with Ganache Auto-Sync
==================================================

This version automatically stores blocks on Ganache when available.
- Falls back to JSON storage if Ganache is not running
- Best of both worlds: local backup + blockchain storage
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
from step10_full_ganache import GanacheBlockchain
import config


class SecureCloudStorageWithGanache:
    """
    Complete system with automatic Ganache integration
    
    Features:
    - Stores blocks locally (JSON) - always works
    - Stores blocks on Ganache (blockchain) - when available
    - Automatic fallback if Ganache not running
    - File sharing works regardless
    """
    
    def __init__(self, user_id, use_ganache=True):
        """
        Initialize storage system
        
        Args:
            user_id: str - Unique user identifier
            use_ganache: bool - Try to connect to Ganache
        """
        self.user_id = user_id
        self.aes = AESEncryption()
        self.ecc = ECCEncryption()
        self.keygen = DynamicKeyGenerator()
        self.ganache = None
        self.acl_contract = None
        self.ganache_enabled = False
        
        # Load or create ECC keys
        self.private_key, self.public_key = self.ecc.load_keys(user_id)
        if not self.private_key:
            print(f"🔑 Generating new ECC key pair for {user_id}...")
            self.private_key, self.public_key = self.ecc.generate_key_pair()
            self.ecc.save_keys(self.private_key, self.public_key, user_id)
        
        # Load or create blockchain (local)
        blockchain_path = config.get_blockchain_path(user_id)
        if blockchain_path.exists():
            self.blockchain = Blockchain.load_from_file(blockchain_path)
            print(f"📂 Loaded local blockchain with {len(self.blockchain)} blocks")
        else:
            self.blockchain = Blockchain(user_id)
            self.blockchain.create_genesis_block()
            self.blockchain.save_to_file()
            print(f"🔗 Created new blockchain for {user_id}")
        
        # Try to connect to Ganache
        if use_ganache:
            self._init_ganache()
    
    def _init_ganache(self):
        """Initialize Ganache connection if available"""
        try:
            self.ganache = GanacheBlockchain()
            
            if self.ganache.connect():
                # Try to load existing contract
                contract_file = config.DATA_DIR / 'contract_info.json'
                
                if contract_file.exists():
                    with open(contract_file, 'r') as f:
                        info = json.load(f)
                    
                    # Load contract
                    self.ganache.contract_address = info['address']
                    self.ganache.contract = self.ganache.w3.eth.contract(
                        address=info['address'],
                        abi=info['abi']
                    )
                    print(f"⛓️  Connected to Ganache contract: {info['address'][:10]}...")
                    self.ganache_enabled = True
                    # Try to load ACL contract info if present
                    acl_file = config.DATA_DIR / 'contract_acl.json'
                    if acl_file.exists():
                        try:
                            with open(acl_file, 'r') as f:
                                info = json.load(f)
                            self.acl_contract = self.ganache.w3.eth.contract(
                                address=info['address'], abi=info['abi']
                            )
                            print(f"⛓️  Loaded ACL contract: {info['address'][:10]}...")
                        except Exception as e:
                            print(f"⚠️  Failed to load ACL contract: {e}")
                else:
                    print(f"⚠️  Ganache connected but no contract deployed")
                    print(f"   Run 'python step10_full_ganache.py' first to deploy contract")
                    self.ganache_enabled = False
            else:
                print(f"⚠️  Ganache not available - using local storage only")
                self.ganache_enabled = False
                
        except Exception as e:
            print(f"⚠️  Ganache initialization failed: {e}")
            print(f"   Continuing with local storage only")
            self.ganache_enabled = False
    
    def _store_block_on_ganache(self, block):
        """
        Store block on Ganache blockchain
        
        Args:
            block: Block object to store
        """
        if not self.ganache_enabled:
            return
        
        try:
            # Optimize data for gas efficiency
            block_data = {
                'block_id': block.block_id,
                'data': block.data[:50],  # Further truncate data
                'previous_hash': block.previous_hash[:10],  # Truncate hash
                'hash': block.hash[:10],  # Truncate hash
                'file_id': block.file_id
            }
            
            tx_hash = self.ganache.add_block(block_data)
            print(f"⛓️  Stored on Ganache: {tx_hash[:10]}...")
            
        except Exception as e:
            print(f"⚠️  Ganache storage failed: {e}")
            print(f"   Block saved locally only")
    
    def upload_file(self, file_path):
        """Upload and encrypt a file (with Ganache sync)"""
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
        print(f"✅ Generated dynamic key")
        
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
        print(f"✅ Saved encrypted file")
        
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
        
        # Add block to LOCAL blockchain
        new_block = self.blockchain.add_block(
            data=json.dumps(block_data),
            file_id=file_id
        )
        print(f"✅ Created block #{new_block.block_id}")
        
        # Save LOCAL blockchain
        self.blockchain.save_to_file()
        print(f"✅ Saved to local blockchain")
        
        # Store on GANACHE (if enabled)
        if self.ganache_enabled:
            self._store_block_on_ganache(new_block)

        # If ACL contract is available, set file owner mapping on-chain (best-effort)
        try:
            if self.ganache_enabled and self.acl_contract is not None:
                # Use deterministic bytes32 id for file
                from web3 import Web3
                file_hash = Web3.keccak(text=file_id)
                owner_addr = self.ganache.w3.eth.accounts[0]
                tx = self.acl_contract.functions.setFileOwner(file_hash, owner_addr).transact({
                    'from': owner_addr
                })
                self.ganache.w3.eth.wait_for_transaction_receipt(tx)
                print(f"⛓️  Set file owner on ACL contract for {file_id[:8]}...")
        except Exception as e:
            print(f"⚠️  Failed to set file owner on ACL contract: {e}")
        
        return {
            'file_id': file_id,
            'original_name': file_path.name,
            'size': len(file_data),
            'block_id': new_block.block_id,
            'encrypted_file_path': str(encrypted_file_path),
            'ganache_synced': self.ganache_enabled
        }
    
    def download_file(self, file_id, output_path=None):
        """Download and decrypt a file"""
        print(f"\n📥 Downloading: {file_id}")
        print("-" * 80)
        
        # Get block from LOCAL blockchain
        block = self.blockchain.get_block_by_file_id(file_id)
        if not block:
            raise ValueError(f"File not found: {file_id}")
        print(f"✅ Found block #{block.block_id}")
        
        # Decrypt block to get AES key
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
        """List all files"""
        # Force reload blockchain to get latest data
        blockchain_path = config.get_blockchain_path(self.user_id)
        if blockchain_path.exists():
            self.blockchain = Blockchain.load_from_file(blockchain_path)
            print(f"🔄 Reloaded blockchain with {len(self.blockchain)} blocks")
        
        files = []
        
        for block in self.blockchain.chain[1:]:  # Skip genesis
            try:
                block_data = json.loads(block.data)
                is_shared = block_data.get('is_shared', False)
                shared_from = block_data.get('shared_from', None)
                
                # Try to get encrypted file path
                encrypted_path = config.get_file_path(block.file_id, encrypted=True)
                
                # For shared files, also try alternative paths
                file_found = False
                original_name = f"file_{block.file_id}"
                
                if encrypted_path.exists():
                    with open(encrypted_path, 'r') as f:
                        bundle = json.load(f)
                    original_name = bundle.get('original_name', f"file_{block.file_id}")
                    file_found = True
                else:
                    # For shared files, the encrypted file might be in the original owner's directory
                    # Try to find it in the main encrypted directory
                    main_encrypted_path = config.ENCRYPTED_DIR / block.file_id
                    if main_encrypted_path.exists():
                        with open(main_encrypted_path, 'r') as f:
                            bundle = json.load(f)
                        original_name = bundle.get('original_name', f"file_{block.file_id}")
                        file_found = True
                    else:
                        print(f"⚠️  Encrypted file not found for {block.file_id}")
                        # Still include the file even if encrypted file is missing
                        original_name = f"file_{block.file_id} (missing)"
                        file_found = True
                
                if file_found:
                    files.append({
                        'file_id': block.file_id,
                        'name': original_name,
                        'block_id': block.block_id,
                        'timestamp': block.timestamp,
                        'is_shared': is_shared,
                        'shared_from': shared_from,
                        'type': 'shared' if is_shared else 'own'
                    })
                    
            except Exception as e:
                print(f"⚠️  Error processing block {block.block_id}: {e}")
                continue
        
        return files
    
    def share_file(self, file_id, recipient_user_id):
        """Share a file with another user"""
        print(f"\n🤝 Sharing {file_id} with {recipient_user_id}")
        print("-" * 80)
        
        # Get recipient's storage instance (with same Ganache setting)
        recipient_storage = SecureCloudStorageWithGanache(
            recipient_user_id, 
            use_ganache=self.ganache_enabled
        )
        
        # Get our block and decrypt to get AES key
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
        
        # Encrypt AES key for recipient
        shared_key_data = recipient_storage.ecc.encrypt_data(
            aes_key, 
            recipient_storage.public_key
        )
        
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
        
        # Add block to recipient's LOCAL blockchain
        print(f"🔍 DEBUG: Adding shared block with file_id: {file_id}")
        print(f"🔍 DEBUG: Shared block data: {shared_block_data}")
        
        new_block = recipient_storage.blockchain.add_block(
            data=json.dumps(shared_block_data),
            file_id=file_id
        )
        
        print(f"🔍 DEBUG: Created block with file_id: {new_block.file_id}")
        print(f"🔍 DEBUG: Block data: {new_block.data}")
        
        # Save recipient's LOCAL blockchain
        recipient_storage.blockchain.save_to_file()
        print(f"✅ Added to {recipient_user_id}'s local blockchain (Block #{new_block.block_id})")
        
        # Store on GANACHE if enabled
        if recipient_storage.ganache_enabled:
            recipient_storage._store_block_on_ganache(new_block)
        
        # Create sharing record
        share_record = {
            'file_id': file_id,
            'sender': self.user_id,
            'recipient': recipient_user_id,
            'shared_block_id': new_block.block_id,
            'timestamp': new_block.timestamp,
            'ganache_synced': recipient_storage.ganache_enabled
        }
        
        shares_path = config.DATA_DIR / 'shares.json'
        if shares_path.exists():
            with open(shares_path, 'r') as f:
                shares = json.load(f)
        else:
            shares = []
        
        shares.append(share_record)
        
        with open(shares_path, 'w') as f:
            json.dump(shares, f, indent=2)
        
        print(f"✅ File successfully shared!")
        
        return share_record
    
    def get_ganache_status(self):
        """Get Ganache connection status"""
        if not self.ganache_enabled:
            return {
                'connected': False,
                'message': 'Ganache not available'
            }
        
        try:
            block_count = self.ganache.get_block_count()
            return {
                'connected': True,
                'contract': self.ganache.contract_address,
                'blocks_on_chain': block_count,
                'network_id': self.ganache.w3.eth.chain_id
            }
        except:
            return {
                'connected': False,
                'message': 'Ganache connection lost'
            }
    
    def get_public_key_hex(self):
        """Get public key as hex string for sharing"""
        return ECCEncryption.public_key_to_string(self.public_key)

    def has_access(self, file_id, user_eth_address=None, device_id_hex=None):
        """Check ACL contract (if present) for access to file_id for given user address.

        file_id: uuid string
        user_eth_address: hex address string (0x...)
        device_id_hex: optional bytes32 hex (0x...)
        """
        if not self.acl_contract:
            # No ACL contract deployed -> allow by default
            return True

        try:
            from web3 import Web3
            from eth_utils import to_checksum_address
            file_hash = Web3.keccak(text=file_id)

            if user_eth_address is None:
                return False

            # DEBUG: Print details about what we're checking
            print(f"    [ACL CHECK] file_id={file_id[:16]}..., user={user_eth_address}, device_id={device_id_hex[:16] if device_id_hex else None}...")

            if device_id_hex:
                # normalize device id
                if device_id_hex.startswith('0x'):
                    device_hex = device_id_hex
                else:
                    device_hex = '0x' + device_id_hex
                device_bytes = Web3.to_bytes(hexstr=device_hex)
                # convert to bytes32 if needed
                device32 = Web3.to_hex(Web3.keccak(device_bytes))[:66]
                print(f"    [ACL CHECK] device_hex={device_hex[:20]}..., device32={device32}")
                result = self.acl_contract.functions.isAccessAllowed(file_hash, to_checksum_address(user_eth_address), Web3.to_bytes(hexstr=device32)).call({
                    'from': self.ganache.w3.eth.accounts[0]
                })
                print(f"    [ACL CHECK] isAccessAllowed returned: {result}")
                return result
            else:
                print(f"    [ACL CHECK] Checking without device")
                result = self.acl_contract.functions.isAccessAllowedNoDevice(file_hash, to_checksum_address(user_eth_address)).call({
                    'from': self.ganache.w3.eth.accounts[0]
                })
                print(f"    [ACL CHECK] isAccessAllowedNoDevice returned: {result}")
                return result
        except Exception as e:
            print(f"⚠️  ACL check failed: {e}")
            import traceback
            print(traceback.format_exc())
            return False
        
    def grant_access_on_chain(self, file_id, user_eth_address, expiry=0, device_ids=None, owner_eth_address=None):
        """Grant access on the ACL contract for a given file to a user.

        device_ids: list of string identifiers (will be keccak-hashed to bytes32)
        owner_eth_address: optional address to send the transaction from (must be unlocked on Ganache)
        """
        if not self.acl_contract:
            raise RuntimeError("ACL contract not loaded")

        from web3 import Web3
        from eth_utils import to_checksum_address

        file_hash = Web3.keccak(text=file_id)

        owner = owner_eth_address or self.ganache.w3.eth.accounts[0]

        dev_bytes = []
        if device_ids:
            for d in device_ids:
                # convert each device identifier string into bytes32 via keccak
                dev_bytes.append(Web3.keccak(text=str(d)))

        tx = self.acl_contract.functions.grantAccess(
            file_hash,
            to_checksum_address(user_eth_address),
            int(expiry),
            dev_bytes
        ).transact({'from': to_checksum_address(owner)})

        receipt = self.ganache.w3.eth.wait_for_transaction_receipt(tx)
        return receipt

    def revoke_access_on_chain(self, file_id, user_eth_address, owner_eth_address=None):
        """Revoke access on-chain for a given file and user."""
        if not self.acl_contract:
            raise RuntimeError("ACL contract not loaded")

        from web3 import Web3
        from eth_utils import to_checksum_address

        file_hash = Web3.keccak(text=file_id)
        owner = owner_eth_address or self.ganache.w3.eth.accounts[0]

        tx = self.acl_contract.functions.revokeAccess(
            file_hash,
            to_checksum_address(user_eth_address)
        ).transact({'from': to_checksum_address(owner)})

        receipt = self.ganache.w3.eth.wait_for_transaction_receipt(tx)
        return receipt


# Test the integrated system
if __name__ == "__main__":
    print("=" * 80)
    print("TESTING INTEGRATED SYSTEM WITH GANACHE AUTO-SYNC")
    print("=" * 80)
    
    print("\nThis system will:")
    print("  1. Store blocks locally (always works)")
    print("  2. Store blocks on Ganache (if available)")
    print("  3. Work even if Ganache is not running")
    
    # Create test file
    test_file = config.FILES_DIR / "integration_test.txt"
    with open(test_file, 'w') as f:
        f.write("Testing integrated Ganache system!")
    
    print("\n📝 Creating storage for Alice (with Ganache if available)")
    print("-" * 80)
    alice = SecureCloudStorageWithGanache("alice", use_ganache=True)
    
    print("\n📝 Alice uploads a file")
    print("-" * 80)
    result = alice.upload_file(test_file)
    
    print(f"\n📊 Upload Result:")
    print(f"   File ID: {result['file_id']}")
    print(f"   Block: #{result['block_id']}")
    print(f"   Ganache Synced: {result['ganache_synced']}")
    
    # Check Ganache status
    status = alice.get_ganache_status()
    print(f"\n⛓️  Ganache Status:")
    if status['connected']:
        print(f"   ✅ Connected")
        print(f"   Contract: {status['contract']}")
        print(f"   Blocks on chain: {status['blocks_on_chain']}")
    else:
        print(f"   ⚠️  {status['message']}")
        print(f"   Blocks stored locally only")
    
    print("\n" + "=" * 80)
    print("INTEGRATION TEST COMPLETE!")
    print("=" * 80)
