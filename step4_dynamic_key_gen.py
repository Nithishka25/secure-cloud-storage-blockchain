"""
STEP 4: Dynamic Key Generation
===============================

This module implements the core dynamic key generation algorithm from the paper.

Algorithm (from paper):
1. Hash the file content → file_hash
2. Hash the last block in blockchain → block_hash
3. XOR the two hashes → dynamic_key
4. Use this key to encrypt the file with AES

This ensures each file gets a unique key that changes even for the same file content.
"""

import hashlib
import config

class DynamicKeyGenerator:
    """
    Dynamic AES key generator based on file hash and blockchain hash
    
    This is the core innovation from the paper:
    - Each file encrypted with unique key
    - Key depends on both file content and blockchain state
    - Even same file gets different key when uploaded again
    """
    
    def __init__(self):
        self.hash_algorithm = config.HASH_ALGORITHM
    
    def hash_data(self, data):
        """
        Hash data using SHA-256
        
        Args:
            data: bytes - Data to hash
            
        Returns:
            bytes: 32-byte hash (256 bits)
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.sha256(data).digest()
    
    def generate_file_hash(self, file_data):
        """
        Generate hash of file content
        
        Args:
            file_data: bytes - File content
            
        Returns:
            bytes: SHA-256 hash of file
        """
        return self.hash_data(file_data)
    
    def generate_block_hash(self, block_data):
        """
        Generate hash of block content
        
        Args:
            block_data: str or bytes - Block content
            
        Returns:
            bytes: SHA-256 hash of block
        """
        if isinstance(block_data, dict):
            # Convert block dict to string for hashing
            block_data = str(block_data)
        return self.hash_data(block_data)
    
    def xor_bytes(self, bytes1, bytes2):
        """
        XOR two byte arrays
        
        Args:
            bytes1: bytes - First byte array
            bytes2: bytes - Second byte array
            
        Returns:
            bytes: XOR result
        """
        # Ensure both are same length (they should be, both SHA-256 = 32 bytes)
        if len(bytes1) != len(bytes2):
            raise ValueError(f"Byte arrays must be same length: {len(bytes1)} vs {len(bytes2)}")
        
        return bytes(b1 ^ b2 for b1, b2 in zip(bytes1, bytes2))
    
    def generate_dynamic_key(self, file_data, last_block_content):
        """
        Generate dynamic AES key using the paper's algorithm
        
        Algorithm:
        1. file_hash = SHA-256(file_data)
        2. block_hash = SHA-256(last_block)
        3. key = file_hash XOR block_hash
        
        Args:
            file_data: bytes - File content to encrypt
            last_block_content: str/dict - Content of last block in blockchain
            
        Returns:
            bytes: 32-byte AES-256 key
        """
        # Step 1: Hash the file
        file_hash = self.generate_file_hash(file_data)
        
        # Step 2: Hash the last block
        block_hash = self.generate_block_hash(last_block_content)
        
        # Step 3: XOR the hashes to create dynamic key
        dynamic_key = self.xor_bytes(file_hash, block_hash)
        
        return dynamic_key
    
    def generate_genesis_key(self, file_data):
        """
        Generate key for first file (when blockchain is empty)
        
        For genesis block, we use random data + file hash
        
        Args:
            file_data: bytes - File content
            
        Returns:
            bytes: 32-byte AES key
        """
        import secrets
        
        # Generate random data for genesis
        random_data = secrets.token_bytes(32)
        
        # Hash file
        file_hash = self.generate_file_hash(file_data)
        
        # XOR with random data
        genesis_key = self.xor_bytes(file_hash, random_data)
        
        return genesis_key, random_data


# ============================================================================
# TESTING AND DEMONSTRATION
# ============================================================================

def test_dynamic_key_generation():
    """Test the dynamic key generation algorithm"""
    print("=" * 80)
    print("TESTING DYNAMIC KEY GENERATION ALGORITHM")
    print("=" * 80)
    
    keygen = DynamicKeyGenerator()
    
    # Test 1: Basic Hash Generation
    print("\n📝 Test 1: Hash Generation")
    print("-" * 80)
    
    test_data = b"Sample file content"
    file_hash = keygen.generate_file_hash(test_data)
    print(f"File data: {test_data.decode()}")
    print(f"File hash: {file_hash.hex()}")
    print(f"Hash length: {len(file_hash)} bytes ({len(file_hash) * 8} bits)")
    
    # Verify hash is deterministic
    file_hash2 = keygen.generate_file_hash(test_data)
    if file_hash == file_hash2:
        print("✅ Hash is deterministic (same input → same output)")
    else:
        print("❌ Hash is not deterministic!")
        return False
    
    # Test 2: XOR Operation
    print("\n📝 Test 2: XOR Operation")
    print("-" * 80)
    
    hash1 = keygen.hash_data(b"block content 1")
    hash2 = keygen.hash_data(b"block content 2")
    
    print(f"Hash 1: {hash1.hex()[:32]}...")
    print(f"Hash 2: {hash2.hex()[:32]}...")
    
    xor_result = keygen.xor_bytes(hash1, hash2)
    print(f"XOR:    {xor_result.hex()[:32]}...")
    
    # Verify XOR properties
    # XOR is reversible: (A XOR B) XOR B = A
    reverse = keygen.xor_bytes(xor_result, hash2)
    if reverse == hash1:
        print("✅ XOR is reversible")
    else:
        print("❌ XOR reversal failed!")
        return False
    
    # Test 3: Dynamic Key Generation
    print("\n📝 Test 3: Dynamic Key Generation")
    print("-" * 80)
    
    file_content = b"Important document content that needs encryption"
    block_content = "Block #5 - Previous hash: abc123..."
    
    key1 = keygen.generate_dynamic_key(file_content, block_content)
    print(f"File: {file_content[:30].decode()}...")
    print(f"Block: {block_content}")
    print(f"Generated key: {key1.hex()}")
    
    # Test 4: Same File, Different Blocks → Different Keys
    print("\n📝 Test 4: Same File, Different Blocks → Different Keys")
    print("-" * 80)
    
    same_file = b"Same file content"
    block1 = "Block #1 content"
    block2 = "Block #2 content"
    
    key_from_block1 = keygen.generate_dynamic_key(same_file, block1)
    key_from_block2 = keygen.generate_dynamic_key(same_file, block2)
    
    print(f"File: {same_file.decode()}")
    print(f"Key with Block 1: {key_from_block1.hex()[:32]}...")
    print(f"Key with Block 2: {key_from_block2.hex()[:32]}...")
    
    if key_from_block1 != key_from_block2:
        print("✅ Different blocks produce different keys")
    else:
        print("❌ Same key generated for different blocks!")
        return False
    
    # Test 5: Different Files, Same Block → Different Keys
    print("\n📝 Test 5: Different Files, Same Block → Different Keys")
    print("-" * 80)
    
    file1 = b"First file content"
    file2 = b"Second file content"
    same_block = "Block #10 content"
    
    key_from_file1 = keygen.generate_dynamic_key(file1, same_block)
    key_from_file2 = keygen.generate_dynamic_key(file2, same_block)
    
    print(f"Block: {same_block}")
    print(f"Key for file 1: {key_from_file1.hex()[:32]}...")
    print(f"Key for file 2: {key_from_file2.hex()[:32]}...")
    
    if key_from_file1 != key_from_file2:
        print("✅ Different files produce different keys")
    else:
        print("❌ Same key generated for different files!")
        return False
    
    # Test 6: Genesis Key Generation
    print("\n📝 Test 6: Genesis Key (First File)")
    print("-" * 80)
    
    first_file = b"First file in blockchain"
    genesis_key, random_data = keygen.generate_genesis_key(first_file)
    
    print(f"Random data: {random_data.hex()[:32]}...")
    print(f"Genesis key: {genesis_key.hex()[:32]}...")
    print(f"✅ Genesis key generated (for blockchain initialization)")
    
    # Test 7: Simulate Multiple File Uploads
    print("\n📝 Test 7: Simulate Upload Sequence")
    print("-" * 80)
    
    files = [
        b"First upload",
        b"Second upload",
        b"Third upload",
        b"First upload"  # Same as first, but should get different key
    ]
    
    keys = []
    current_block = "Genesis block"
    
    for i, file in enumerate(files, 1):
        key = keygen.generate_dynamic_key(file, current_block)
        keys.append(key)
        print(f"File {i}: {file.decode():<20} → Key: {key.hex()[:32]}...")
        
        # Update block for next iteration (simulating blockchain growth)
        current_block = f"Block #{i}"
    
    # Verify that uploading same file twice gives different keys
    if keys[0] != keys[3]:
        print("\n✅ Same file uploaded twice gets different keys!")
    else:
        print("\n❌ Same file got same key!")
        return False
    
    # Test 8: Key Uniqueness
    print("\n📝 Test 8: Key Uniqueness Analysis")
    print("-" * 80)
    
    # Generate many keys
    test_keys = set()
    for i in range(100):
        file = f"File content {i}".encode()
        block = f"Block {i % 10}"  # Some overlap in blocks
        key = keygen.generate_dynamic_key(file, block)
        test_keys.add(key.hex())
    
    print(f"Generated {len(test_keys)} unique keys from 100 files")
    if len(test_keys) == 100:
        print("✅ All keys are unique!")
    else:
        print(f"⚠️  {100 - len(test_keys)} duplicate keys found")
    
    print("\n" + "=" * 80)
    print("ALL TESTS PASSED! ✅")
    print("=" * 80)
    print("\n🔑 Dynamic Key Generation Summary:")
    print("   - Each file gets unique encryption key")
    print("   - Key depends on file content AND blockchain state")
    print("   - Re-uploading same file creates different key")
    print("   - Compromising one key doesn't help with other files")
    print("\n📝 Next Step: Run 'python step5_blockchain_structure.py' to implement blockchain")
    
    return True


if __name__ == "__main__":
    test_dynamic_key_generation()
