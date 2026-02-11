"""
STEP 3: Elliptic Curve Cryptography (ECC) Implementation
=========================================================

This module implements ECC key generation and encryption using secp256k1 curve.
ECC is used to encrypt blockchain blocks so only the user with private key can decrypt them.
"""

from ecdsa import SigningKey, VerifyingKey, SECP256k1
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import hashlib
import config

class ECCEncryption:
    """
    ECC-based encryption handler using secp256k1 curve
    
    Features:
    - secp256k1 curve (same as Bitcoin/Ethereum)
    - Public/Private key pair generation
    - Hybrid encryption: ECC for key exchange + AES for data
    - Key serialization for storage
    """
    
    def __init__(self):
        self.curve = SECP256k1
    
    def generate_key_pair(self):
        """
        Generate a new ECC key pair
        
        Returns:
            tuple: (private_key, public_key) as SigningKey and VerifyingKey objects
        """
        private_key = SigningKey.generate(curve=self.curve)
        public_key = private_key.get_verifying_key()
        return private_key, public_key
    
    def save_keys(self, private_key, public_key, user_id):
        """
        Save key pair to files
        
        Args:
            private_key: SigningKey object
            public_key: VerifyingKey object
            user_id: Unique identifier for the user
        """
        private_path = config.get_key_path(user_id, 'private')
        public_path = config.get_key_path(user_id, 'public')
        
        # Save private key (PEM format)
        with open(private_path, 'wb') as f:
            f.write(private_key.to_pem())
        
        # Save public key (PEM format)
        with open(public_path, 'wb') as f:
            f.write(public_key.to_pem())
        
        print(f"🔑 Keys saved:")
        print(f"   Private: {private_path}")
        print(f"   Public: {public_path}")
    
    def load_keys(self, user_id):
        """
        Load key pair from files
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            tuple: (private_key, public_key) or (None, None) if not found
        """
        private_path = config.get_key_path(user_id, 'private')
        public_path = config.get_key_path(user_id, 'public')
        
        try:
            with open(private_path, 'rb') as f:
                private_key = SigningKey.from_pem(f.read())
            
            with open(public_path, 'rb') as f:
                public_key = VerifyingKey.from_pem(f.read())
            
            return private_key, public_key
        except FileNotFoundError:
            return None, None
    
    def encrypt_data(self, data, public_key):
        """
        Encrypt data using hybrid encryption (ECIES-like)
        
        Process:
        1. Generate random AES key
        2. Encrypt data with AES
        3. Derive shared secret from public key
        4. Encrypt AES key with shared secret
        
        Args:
            data: bytes - Data to encrypt
            public_key: VerifyingKey object
            
        Returns:
            dict containing encrypted data and metadata
        """
        # Generate ephemeral key pair
        ephemeral_private = SigningKey.generate(curve=self.curve)
        ephemeral_public = ephemeral_private.get_verifying_key()
        
        # Derive shared secret using ECDH (Elliptic Curve Diffie-Hellman)
        shared_point = ephemeral_private.privkey.secret_multiplier * public_key.pubkey.point
        shared_secret = hashlib.sha256(
            str(shared_point.x()).encode() + str(shared_point.y()).encode()
        ).digest()
        
        # Generate random AES key
        aes_key = get_random_bytes(32)
        
        # Encrypt data with AES
        cipher = AES.new(aes_key, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(data)
        
        # Encrypt AES key with shared secret
        key_cipher = AES.new(shared_secret, AES.MODE_GCM)
        encrypted_key, key_tag = key_cipher.encrypt_and_digest(aes_key)
        
        return {
            'ciphertext': ciphertext,
            'nonce': cipher.nonce,
            'tag': tag,
            'encrypted_key': encrypted_key,
            'key_nonce': key_cipher.nonce,
            'key_tag': key_tag,
            'ephemeral_public_key': ephemeral_public.to_string()
        }
    
    def decrypt_data(self, encrypted_data, private_key):
        """
        Decrypt data encrypted with encrypt_data
        
        Args:
            encrypted_data: dict from encrypt_data
            private_key: SigningKey object
            
        Returns:
            bytes: decrypted data
        """
        # Reconstruct ephemeral public key
        ephemeral_public = VerifyingKey.from_string(
            encrypted_data['ephemeral_public_key'],
            curve=self.curve
        )
        
        # Derive shared secret
        shared_point = private_key.privkey.secret_multiplier * ephemeral_public.pubkey.point
        shared_secret = hashlib.sha256(
            str(shared_point.x()).encode() + str(shared_point.y()).encode()
        ).digest()
        
        # Decrypt AES key
        key_cipher = AES.new(shared_secret, AES.MODE_GCM, nonce=encrypted_data['key_nonce'])
        aes_key = key_cipher.decrypt_and_verify(
            encrypted_data['encrypted_key'],
            encrypted_data['key_tag']
        )
        
        # Decrypt data
        cipher = AES.new(aes_key, AES.MODE_GCM, nonce=encrypted_data['nonce'])
        plaintext = cipher.decrypt_and_verify(
            encrypted_data['ciphertext'],
            encrypted_data['tag']
        )
        
        return plaintext
    
    @staticmethod
    def public_key_to_string(public_key):
        """Convert public key to hex string"""
        return public_key.to_string().hex()
    
    @staticmethod
    def string_to_public_key(key_string):
        """Convert hex string to public key"""
        return VerifyingKey.from_string(bytes.fromhex(key_string), curve=SECP256k1)


# ============================================================================
# TESTING AND DEMONSTRATION
# ============================================================================

def test_ecc_encryption():
    """Test ECC encryption and key management"""
    print("=" * 80)
    print("TESTING ECC ENCRYPTION (secp256k1)")
    print("=" * 80)
    
    ecc = ECCEncryption()
    
    # Test 1: Key Generation
    print("\n📝 Test 1: Key Generation")
    print("-" * 80)
    
    private_key, public_key = ecc.generate_key_pair()
    print(f"✅ Generated key pair")
    print(f"Private key size: {len(private_key.to_string())} bytes")
    print(f"Public key size: {len(public_key.to_string())} bytes")
    print(f"Public key (hex): {public_key.to_string().hex()[:64]}...")
    
    # Test 2: Key Storage and Loading
    print("\n📝 Test 2: Key Storage and Loading")
    print("-" * 80)
    
    test_user_id = "test_user_001"
    ecc.save_keys(private_key, public_key, test_user_id)
    
    loaded_private, loaded_public = ecc.load_keys(test_user_id)
    
    if loaded_private and loaded_public:
        print("✅ Keys loaded successfully")
        # Verify they're the same
        if private_key.to_string() == loaded_private.to_string():
            print("✅ Private key matches")
        if public_key.to_string() == loaded_public.to_string():
            print("✅ Public key matches")
    else:
        print("❌ Failed to load keys")
        return False
    
    # Test 3: Encryption and Decryption
    print("\n📝 Test 3: Hybrid Encryption/Decryption")
    print("-" * 80)
    
    test_data = b"This is secret blockchain data that must be encrypted!"
    print(f"Original data: {test_data.decode()}")
    print(f"Data size: {len(test_data)} bytes")
    
    # Encrypt with public key
    encrypted = ecc.encrypt_data(test_data, public_key)
    print(f"\n🔒 Encrypted:")
    print(f"   Ciphertext: {encrypted['ciphertext'].hex()[:64]}...")
    print(f"   Encrypted AES key: {encrypted['encrypted_key'].hex()}")
    print(f"   Ephemeral public key: {encrypted['ephemeral_public_key'].hex()[:64]}...")
    
    # Decrypt with private key
    decrypted = ecc.decrypt_data(encrypted, private_key)
    print(f"\n🔓 Decrypted: {decrypted.decode()}")
    
    if test_data == decrypted:
        print("✅ Encryption/Decryption successful!")
    else:
        print("❌ Encryption/Decryption failed!")
        return False
    
    # Test 4: Multiple Users
    print("\n📝 Test 4: Multiple User Key Pairs")
    print("-" * 80)
    
    # Create keys for two users
    alice_private, alice_public = ecc.generate_key_pair()
    bob_private, bob_public = ecc.generate_key_pair()
    
    ecc.save_keys(alice_private, alice_public, "alice")
    ecc.save_keys(bob_private, bob_public, "bob")
    
    print("✅ Created and saved keys for Alice and Bob")
    
    # Alice encrypts data for Bob
    message = b"Secret message from Alice to Bob"
    encrypted_for_bob = ecc.encrypt_data(message, bob_public)
    
    # Bob decrypts
    decrypted_by_bob = ecc.decrypt_data(encrypted_for_bob, bob_private)
    
    if message == decrypted_by_bob:
        print("✅ Alice → Bob encryption successful!")
    else:
        print("❌ Alice → Bob encryption failed!")
        return False
    
    # Verify Alice cannot decrypt (she doesn't have Bob's private key)
    try:
        ecc.decrypt_data(encrypted_for_bob, alice_private)
        print("❌ Alice shouldn't be able to decrypt Bob's message!")
        return False
    except:
        print("✅ Alice correctly cannot decrypt message encrypted for Bob")
    
    # Test 5: Public Key Serialization
    print("\n📝 Test 5: Public Key Serialization")
    print("-" * 80)
    
    pub_string = ECCEncryption.public_key_to_string(public_key)
    print(f"Public key as string: {pub_string[:64]}...")
    
    reconstructed_pub = ECCEncryption.string_to_public_key(pub_string)
    
    if public_key.to_string() == reconstructed_pub.to_string():
        print("✅ Public key serialization successful!")
    else:
        print("❌ Public key serialization failed!")
        return False
    
    print("\n" + "=" * 80)
    print("ALL TESTS PASSED! ✅")
    print("=" * 80)
    print("\n📝 Next Step: Run 'python step4_dynamic_key_gen.py' to implement dynamic key generation")
    
    return True


if __name__ == "__main__":
    test_ecc_encryption()
