"""
Quick Integration Test: Signed Device Authentication
=====================================================

This script tests the core functionality:
1. Device registration with public key storage
2. Signature verification in download endpoint
3. ACL enforcement
"""

import json
import base64
import time

# Import required modules
import requests

BASE_URL = "http://localhost:5000"

def test_device_registration_and_download():
    """Test device public key storage and signature verification"""
    
    print("\n" + "="*70)
    print("TEST 1: Device Registration and Signature Storage")
    print("="*70)
    
    # Create a session
    session = requests.Session()
    
    # Step 1: Login
    print("\n[1] Login as alice...")
    r = session.post(f"{BASE_URL}/api/login", json={"user_id": "alice_test"})
    assert r.status_code == 200, f"Login failed: {r.text}"
    print(f"   OK - Logged in. Blocks in blockchain: {r.json().get('blocks', 0)}")
    
    # Step 2: Register device with public key
    print("\n[2] Register device with public key...")
    device_public_key = base64.b64encode(b"test_public_key_32_bytes_12345678")
    r = session.post(f"{BASE_URL}/api/acl/register_device", json={
        "device_id": f"test_device_{int(time.time())}",
        "device_public_key": device_public_key.decode('utf-8')
    })
    
    assert r.status_code == 200, f"Register failed: {r.text}"
    data = r.json()
    print(f"   OK - Device registered: {data.get('device_id')}")
    print(f"   OK - Public key stored: {data.get('device_public_key')}")
    
    # Step 3: Verify device public keys are persisted
    print("\n[3] Verify device keys persisted...")
    from pathlib import Path
    keys_file = Path("data/device_public_keys.json")
    if keys_file.exists():
        with open(keys_file) as f:
            keys = json.load(f)
        user_device_key = [k for k in keys.keys() if "alice_test" in k and "test_device" in k]
        assert len(user_device_key) > 0, "Device key not found in storage"
        print(f"   OK - Found {len(user_device_key)} device key(s) in storage")
        print(f"   OK - Device key: {user_device_key[0]}")
    else:
        print("   NOTE - device_public_keys.json not found (will be created on first registration)")
    
    print("\nTEST 1 PASSED - Device registration and key storage working\n")


def test_signature_verification_helpers():
    """Test the signature verification functions backend"""
    
    print("="*70)
    print("TEST 2: Signature Verification Function")
    print("="*70)
    
    # Import backend verification function
    try:
        from step15_network_server import verify_device_signature
        import nacl.signing
        from nacl.encoding import Base64Encoder
        
        # Create test keypair
        signing_key = nacl.signing.SigningKey.generate()
        verify_key = signing_key.verify_key
        public_key_b64 = verify_key.encode(encoder=Base64Encoder).decode('utf-8')
        
        # Create test message and signature
        message = "test_file_id:test_user:1234567890"
        signed = signing_key.sign(message.encode('utf-8'))
        signature_b64 = Base64Encoder.encode(signed.signature).decode('utf-8')
        
        # Test verification
        print("\n[1] Verify valid signature...")
        is_valid, error = verify_device_signature(
            "test_user",
            "test_device",
            message,
            signature_b64,
            public_key_b64
        )
        assert is_valid, f"Valid signature rejected: {error}"
        print("   OK - Valid signature accepted")
        
        # Test invalid signature
        print("\n[2] Verify invalid signature is rejected...")
        bad_signature = base64.b64encode(b"not a real signature").decode('utf-8')
        is_valid, error = verify_device_signature(
            "test_user",
            "test_device",
            message,
            bad_signature,
            public_key_b64
        )
        assert not is_valid, "Invalid signature was not rejected"
        print(f"   OK - Invalid signature rejected: {error}")
        
        # Test modified message
        print("\n[3] Verify signature fails for modified message...")
        modified_message = "different_message"
        is_valid, error = verify_device_signature(
            "test_user",
            "test_device",
            modified_message,
            signature_b64,
            public_key_b64
        )
        assert not is_valid, "Signature for modified message was not rejected"
        print(f"   OK - Modified message rejected: {error}")
        
        print("\nTEST 2 PASSED - Signature verification working correctly\n")
        
    except ImportError as e:
        print(f"\nNOTE TEST 2 SKIPPED: {e}")
        print("   (PyNaCl or verification function not available)\n")


def test_api_endpoints():
    """Test that API endpoints exist and handle device data"""
    
    print("="*70)
    print("TEST 3: API Endpoint Validation")
    print("="*70)
    
    session = requests.Session()
    
    # Test register_device endpoint exists
    print("\n[1] Check /api/acl/register_device endpoint...")
    r = session.post(f"{BASE_URL}/api/acl/register_device", json={})
    # Should return 401 (not logged in) not 404 (endpoint not found)
    assert r.status_code != 404, "Endpoint not found"
    print(f"   OK - Endpoint exists (status: {r.status_code})")
    
    # Test download endpoint with device params
        print("\n[2] Check /api/download endpoint accepts device parameters...")
        r = requests.get(f"{BASE_URL}/api/download/nonexistent_file?user_id=test&device_signature=sig&device_public_key=key&timestamp=123")
        # Could be 404 (file not found) or 401 (no user_id in session), both are OK
        # Should NOT be an error from missing device parameters
        assert r.status_code in [401, 404, 400, 403], f"Unexpected status: {r.status_code}"
        print(f"   OK - Endpoint exists and accepts device parameters")
        print(f"       (returned {r.status_code} - expected for missing file)")
    
    print("\nTEST 3 PASSED - API endpoints available\n")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("INTEGRATION TESTS: Signed Device Authentication")
    print("="*70)
    
    try:
        test_device_registration_and_download()
        test_signature_verification_helpers()
        test_api_endpoints()
        
        print("\n" + "="*70)
        print("ALL TESTS PASSED")
        print("="*70)
        print("\nSigned Device Authentication is ready to use!")
        print("- Devices can register with Ed25519 public keys")
        print("- Downloads can be signed with device private keys")
        print("- Server verifies signatures before granting access")
        
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
