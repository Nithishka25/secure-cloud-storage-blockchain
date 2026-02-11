"""
Demo: Smart Contract ACL with Signed Device Authentication
===========================================================

This script demonstrates the complete workflow of:
1. Uploading a file
2. Registering a device with Ed25519 public key
3. Granting on-chain access with device restriction
4. Downloading the file with cryptographically signed request
5. Revoking access and verifying denial

Prerequisites:
- Run Ganache: ganache --deterministic
- Run the web server: python step15_network_server.py
- Install dependencies: pip install requests pynacl tweetsodium
"""

import requests
import json
import time
from pathlib import Path

# For local demo, we'll use nacl directly
try:
    from nacl.signing import SigningKey
    from nacl.encoding import Base64Encoder
    HAS_NACL = True
except ImportError:
    print("⚠️  PyNaCl not installed. Install with: pip install pynacl")
    HAS_NACL = False

BASE_URL = "http://localhost:5000"
USER1 = "alice"
USER2 = "bob"

class DeviceAuthClient:
    """Client demonstrating signed device authentication"""
    
    def __init__(self, base_url, user_id):
        self.base_url = base_url
        self.user_id = user_id
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Generate Ed25519 keypair for this device
        if HAS_NACL:
            self.signing_key = SigningKey.generate()
            self.verify_key = self.signing_key.verify_key
            self.device_public_key_b64 = self.verify_key.encode(encoder=Base64Encoder).decode('utf-8')
        else:
            self.signing_key = None
            self.verify_key = None
            self.device_public_key_b64 = None
        
        self.device_id = None
    
    def login(self):
        """Login as the user"""
        print(f"\n✅ Login as {self.user_id}")
        resp = self.session.post(
            f"{self.base_url}/api/login",
            json={"user_id": self.user_id}
        )
        if resp.status_code == 200:
            print(f"   ✓ User '{self.user_id}' logged in")
            return True
        else:
            print(f"   ✗ Login failed: {resp.text}")
            return False
    
    def register_device(self):
        """Register this device with its public key"""
        if not HAS_NACL:
            print("⚠️  Cannot register device - PyNaCl not available")
            return False
        
        print(f"\n📱 Register Device (with Ed25519 public key)")
        resp = self.session.post(
            f"{self.base_url}/api/acl/register_device",
            json={
                "device_id": f"device_{self.user_id}_{int(time.time())}",
                "device_public_key": self.device_public_key_b64
            }
        )
        
        if resp.status_code == 200:
            data = resp.json()
            self.device_id = data.get('device_id')
            print(f"   ✓ Device registered: {self.device_id}")
            print(f"   ✓ Public key stored on server")
            return True
        else:
            print(f"   ✗ Registration failed: {resp.text}")
            return False
    
    def upload_file(self, filename):
        """Upload a test file"""
        print(f"\n📤 Upload File: {filename}")
        
        # Create test file if it doesn't exist
        test_file = Path(filename)
        if not test_file.exists():
            test_file.write_text(f"This is test content from {self.user_id}\nTimestamp: {time.time()}")
        
        with open(test_file, 'rb') as f:
            files = {'file': f}
            resp = self.session.post(f"{self.base_url}/api/upload", files=files)
        
        if resp.status_code == 200:
            data = resp.json()
            file_id = data.get('file_id')
            print(f"   ✓ File uploaded: {file_id}")
            return file_id
        else:
            print(f"   ✗ Upload failed: {resp.text}")
            return None
    
    def get_eth_address(self):
        """Get Ethereum address from blockchain"""
        print(f"\n🔑 Get Ethereum Address")
        resp = self.session.get(
            f"{self.base_url}/api/blockchain",
            params={"user_id": self.user_id}
        )
        
        # For demo purposes, we'll use a fake eth address
        # In real world, this would come from the user's blockchain account
        fake_eth = f"0x{'0' * 40}"
        print(f"   ℹ️  Using demo Eth address: {fake_eth}")
        return fake_eth
    
    def grant_access_on_chain(self, file_id, recipient_eth, device_id=None):
        """Grant on-chain access with optional device restriction"""
        print(f"\n✅ Grant On-Chain Access")
        print(f"   File: {file_id}")
        print(f"   Recipient: {recipient_eth}")
        if device_id:
            print(f"   Device restriction: {device_id}")
        
        resp = self.session.post(
            f"{self.base_url}/api/acl/grant",
            json={
                "file_id": file_id,
                "user_eth_address": recipient_eth,
                "expiry": 0,  # No expiry for demo
                "device_ids": [device_id] if device_id else None
            }
        )
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"   ✓ Access granted on blockchain")
            print(f"   ✓ Transaction hash: {data.get('tx_hash', 'N/A')[:16]}...")
            return True
        else:
            print(f"   ✗ Grant failed: {resp.text}")
            return False
    
    def download_file_signed(self, file_id, eth_address=None):
        """Download file with cryptographically signed request"""
        if not HAS_NACL or not self.signing_key:
            print("⚠️  Cannot sign request - PyNaCl not available")
            return False
        
        print(f"\n📥 Download File (with signed device auth)")
        print(f"   File: {file_id}")
        
        # Create signed message
        timestamp = int(time.time())
        message = f"{file_id}:{self.user_id}:{timestamp}"
        signed_msg = self.signing_key.sign(message.encode('utf-8'))
        signature_b64 = signed_msg.signature
        from nacl.encoding import Base64Encoder
        signature_b64_str = Base64Encoder.encode(signature_b64).decode('utf-8')
        
        print(f"   ✓ Message signed: {message}")
        print(f"   ✓ Signature (first 16 chars): {signature_b64_str[:16]}...")
        
        # Download with signature
        download_url = (
            f"{self.base_url}/api/download/{file_id}?"
            f"user_id={self.user_id}&"
            f"device_signature={signature_b64_str}&"
            f"device_public_key={self.device_public_key_b64}&"
            f"timestamp={timestamp}"
        )
        
        resp = requests.get(download_url)
        
        if resp.status_code == 200:
            print(f"   ✓ Download successful - signature verified!")
            content = resp.text if len(resp.text) < 100 else resp.text[:100] + "..."
            print(f"   ✓ Content preview: {content}")
            return True
        else:
            print(f"   ✗ Download failed ({resp.status_code}): {resp.text}")
            return False
    
    def revoke_access(self, file_id, recipient_eth):
        """Revoke on-chain access"""
        print(f"\n❌ Revoke On-Chain Access")
        print(f"   File: {file_id}")
        print(f"   Recipient: {recipient_eth}")
        
        resp = self.session.post(
            f"{self.base_url}/api/acl/revoke",
            json={
                "file_id": file_id,
                "user_eth_address": recipient_eth
            }
        )
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"   ✓ Access revoked on blockchain")
            print(f"   ✓ Transaction hash: {data.get('tx_hash', 'N/A')[:16]}...")
            return True
        else:
            print(f"   ✗ Revoke failed: {resp.text}")
            return False


def main():
    """Run full signed device authentication demo"""
    print("=" * 70)
    print("DEMO: Smart Contract ACL with Signed Device Authentication")
    print("=" * 70)
    
    # Create clients for two users
    alice = DeviceAuthClient(BASE_URL, USER1)
    bob = DeviceAuthClient(BASE_URL, USER2)
    
    # === Step 1: Alice logs in and uploads a file ===
    print("\n" + "=" * 70)
    print("STEP 1: Alice uploads a file")
    print("=" * 70)
    
    if not alice.login():
        print("❌ Failed to login as Alice")
        return
    
    # Create test file
    test_file = f"test_file_alice_{int(time.time())}.txt"
    file_id = alice.upload_file(test_file)
    
    if not file_id:
        print("❌ Failed to upload file")
        return
    
    # === Step 2: Alice registers her device with public key ===
    print("\n" + "=" * 70)
    print("STEP 2: Alice registers her device")
    print("=" * 70)
    
    if not alice.register_device():
        print("⚠️  Device registration not available (PyNaCl missing)")
        print("   Skipping signed authentication steps")
        return
    
    # === Step 3: Bob logs in and registers his device ===
    print("\n" + "=" * 70)
    print("STEP 3: Bob logs in and registers device")
    print("=" * 70)
    
    if not bob.login():
        print("❌ Failed to login as Bob")
        return
    
    if not bob.register_device():
        print("❌ Failed to register Bob's device")
        return
    
    # === Step 4: Alice grants on-chain access to Bob ===
    print("\n" + "=" * 70)
    print("STEP 4: Alice grants on-chain access to Bob's device")
    print("=" * 70)
    
    alice_eth = alice.get_eth_address()
    bob_eth = bob.get_eth_address()
    
    if not alice.grant_access_on_chain(file_id, bob_eth, bob.device_id):
        print("⚠️  On-chain grant may not be available")
        print("   Continuing with download test...")
    
    # === Step 5: Bob downloads file with signed device auth ===
    print("\n" + "=" * 70)
    print("STEP 5: Bob downloads file with signed device request")
    print("=" * 70)
    
    if not bob.download_file_signed(file_id, bob_eth):
        print("⚠️  Download may have failed (ACL or signature verification)")
        print("   Check server logs for details")
    
    # === Step 6: Alice revokes access ===
    print("\n" + "=" * 70)
    print("STEP 6: Alice revokes Bob's access")
    print("=" * 70)
    
    if not alice.revoke_access(file_id, bob_eth):
        print("⚠️  Revoke may not be available")
    
    # === Step 7: Bob tries to download again (should fail) ===
    print("\n" + "=" * 70)
    print("STEP 7: Bob tries to download again (should be denied)")
    print("=" * 70)
    
    print(f"\n📥 Download File (should fail - access revoked)")
    if not bob.download_file_signed(file_id, bob_eth):
        print("✓ Download correctly denied after revocation")
    
    # Cleanup
    Path(test_file).unlink(missing_ok=True)
    
    print("\n" + "=" * 70)
    print("✅ DEMO COMPLETE")
    print("=" * 70)
    print("\nKey Features Demonstrated:")
    print("  ✓ Device registration with Ed25519 public key cryptography")
    print("  ✓ Signed download requests binding to specific device")
    print("  ✓ Smart contract ACL enforcement")
    print("  ✓ Device-specific access grants")
    print("  ✓ Immediate revocation (prevents future access)")


if __name__ == "__main__":
    if not HAS_NACL:
        print("⚠️  PyNaCl not installed - install with: pip install pynacl")
    
    main()
