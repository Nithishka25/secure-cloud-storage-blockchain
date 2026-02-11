"""
STEP 2: AES Encryption Implementation
======================================

This module implements AES-256-GCM encryption and decryption.
GCM (Galois/Counter Mode) provides both confidentiality and authenticity.
"""

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import hashlib
import config

class AESEncryption:
    """
    AES-256-GCM encryption handler
    
    Features:
    - 256-bit key size for maximum security
    - GCM mode for authenticated encryption
    - Unique nonce for each encryption
    - Automatic padding not needed (GCM is a stream cipher mode)
    """
    
    def __init__(self):
        self.key_size = config.AES_KEY_SIZE // 8  # Convert bits to bytes (32 bytes)
        
    def encrypt_file(self, plaintext_data, key):
        """
        Encrypt file data using AES-256-GCM
        
        Args:
            plaintext_data: bytes - The file data to encrypt
            key: bytes - 32-byte AES key
            
        Returns:
            dict containing:
                - ciphertext: encrypted data
                - nonce: unique value for this encryption
                - tag: authentication tag
        """
        # Ensure key is correct size
        if len(key) != self.key_size:
            raise ValueError(f"Key must be {self.key_size} bytes, got {len(key)}")
        
        # Create cipher object with random nonce
        cipher = AES.new(key, AES.MODE_GCM)
        
        # Encrypt and get authentication tag
        ciphertext, tag = cipher.encrypt_and_digest(plaintext_data)
        
        return {
            'ciphertext': ciphertext,
            'nonce': cipher.nonce,
            'tag': tag
        }
    
    def decrypt_file(self, encrypted_data, key):
        """
        Decrypt file data using AES-256-GCM
        
        Args:
            encrypted_data: dict with ciphertext, nonce, and tag
            key: bytes - 32-byte AES key
            
        Returns:
            bytes: decrypted file data
            
        Raises:
            ValueError: if authentication fails (tampered data)
        """
        # Ensure key is correct size
        if len(key) != self.key_size:
            raise ValueError(f"Key must be {self.key_size} bytes, got {len(key)}")
        
        # Create cipher with the same nonce used for encryption
        cipher = AES.new(key, AES.MODE_GCM, nonce=encrypted_data['nonce'])
        
        # Decrypt and verify authentication tag
        try:
            plaintext = cipher.decrypt_and_verify(
                encrypted_data['ciphertext'],
                encrypted_data['tag']
            )
            return plaintext
        except ValueError as e:
            raise ValueError("Decryption failed: Data may have been tampered with") from e
    
    @staticmethod
    def generate_random_key():
        """
        Generate a random 256-bit AES key
        
        Returns:
            bytes: 32-byte random key
        """
        return get_random_bytes(32)
    
    @staticmethod
    def hash_to_key(data):
        """
        Convert arbitrary data to a 256-bit AES key using SHA-256
        
        Args:
            data: bytes - Data to hash
            
        Returns:
            bytes: 32-byte key derived from hash
        """
        return hashlib.sha256(data).digest()


# ============================================================================
# TESTING AND DEMONSTRATION
# ============================================================================

def test_aes_encryption():
    """Test AES encryption and decryption"""
    print("=" * 80)
    print("TESTING AES-256-GCM ENCRYPTION")
    print("=" * 80)
    
    aes = AESEncryption()
    
    # Test 1: Basic encryption/decryption
    print("\n📝 Test 1: Basic Encryption/Decryption")
    print("-" * 80)
    
    test_data = b"This is a secret file content that needs to be encrypted!"
    print(f"Original data: {test_data.decode()}")
    print(f"Data size: {len(test_data)} bytes")
    
    # Generate random key
    key = AESEncryption.generate_random_key()
    print(f"\n🔑 Generated key: {key.hex()[:64]}...")
    print(f"Key size: {len(key)} bytes ({len(key) * 8} bits)")
    
    # Encrypt
    encrypted = aes.encrypt_file(test_data, key)
    print(f"\n🔒 Encrypted ciphertext: {encrypted['ciphertext'].hex()[:64]}...")
    print(f"Nonce: {encrypted['nonce'].hex()}")
    print(f"Tag: {encrypted['tag'].hex()}")
    
    # Decrypt
    decrypted = aes.decrypt_file(encrypted, key)
    print(f"\n🔓 Decrypted data: {decrypted.decode()}")
    
    # Verify
    if test_data == decrypted:
        print("✅ Encryption/Decryption successful!")
    else:
        print("❌ Encryption/Decryption failed!")
        return False
    
    # Test 2: Hash-based key generation
    print("\n📝 Test 2: Hash-based Key Generation")
    print("-" * 80)
    
    source_data = b"some_unique_identifier_for_key_generation"
    hash_key = AESEncryption.hash_to_key(source_data)
    print(f"Source data: {source_data.decode()}")
    print(f"Generated key: {hash_key.hex()}")
    
    encrypted2 = aes.encrypt_file(test_data, hash_key)
    decrypted2 = aes.decrypt_file(encrypted2, hash_key)
    
    if test_data == decrypted2:
        print("✅ Hash-based key generation successful!")
    else:
        print("❌ Hash-based key generation failed!")
        return False
    
    # Test 3: Tamper detection
    print("\n📝 Test 3: Tamper Detection")
    print("-" * 80)
    
    encrypted3 = aes.encrypt_file(test_data, key)
    
    # Tamper with ciphertext
    tampered = encrypted3.copy()
    tampered['ciphertext'] = b'X' * len(tampered['ciphertext'])
    
    try:
        aes.decrypt_file(tampered, key)
        print("❌ Tamper detection failed!")
        return False
    except ValueError as e:
        print(f"✅ Tamper detected: {e}")
    
    # Test 4: Different file types
    print("\n📝 Test 4: Encrypting Different Data Types")
    print("-" * 80)
    
    # Simulate different file types
    text_file = b"Text file content"
    binary_file = bytes([i % 256 for i in range(1000)])  # Binary data
    
    for name, data in [("Text", text_file), ("Binary", binary_file)]:
        encrypted = aes.encrypt_file(data, key)
        decrypted = aes.decrypt_file(encrypted, key)
        status = "✅" if data == decrypted else "❌"
        print(f"{status} {name} file: {len(data)} bytes encrypted and decrypted")
    
    print("\n" + "=" * 80)
    print("ALL TESTS PASSED! ✅")
    print("=" * 80)
    print("\n📝 Next Step: Run 'python step3_crypto_ecc.py' to implement ECC key management")
    
    return True


if __name__ == "__main__":
    test_aes_encryption()
