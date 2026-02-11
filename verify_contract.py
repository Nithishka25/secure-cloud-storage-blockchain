"""
Advanced Ganache Contract Verification
=========================================

Tests if the contract stored in contract_info.json is actually deployed on Ganache.
"""

import json
from pathlib import Path
import config
from web3 import Web3


def verify_contract():
    """Verify if contract is deployed on Ganache"""
    print("\n" + "="*70)
    print("ADVANCED GANACHE CONTRACT VERIFICATION")
    print("="*70)
    
    # Step 1: Connect to Ganache
    print("\n[1/4] Connecting to Ganache...")
    try:
        w3 = Web3(Web3.HTTPProvider(config.GANACHE_URL))
        if w3.is_connected():
            print("✅ Connected to Ganache")
        else:
            print("❌ Cannot connect to Ganache")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False
    
    # Step 2: Load contract info
    print("\n[2/4] Loading contract info from file...")
    contract_file = config.DATA_DIR / 'contract_info.json'
    if not contract_file.exists():
        print(f"❌ Contract info file not found: {contract_file}")
        return False
    
    try:
        with open(contract_file, 'r') as f:
            contract_info = json.load(f)
        print(f"✅ Found contract info file")
        print(f"   Address: {contract_info.get('address')}")
    except Exception as e:
        print(f"❌ Error reading contract file: {e}")
        return False
    
    # Step 3: Check if contract address has code
    print("\n[3/4] Checking if contract is deployed on Ganache...")
    contract_address = contract_info.get('address')
    
    try:
        # Check if address has bytecode (means contract is deployed)
        bytecode = w3.eth.get_code(contract_address)
        
        if bytecode == b'0x' or bytecode == b'':
            print(f"❌ No contract found at address: {contract_address}")
            print(f"   The address exists but has no code")
            return False
        else:
            print(f"✅ Contract IS DEPLOYED!")
            print(f"   Bytecode length: {len(bytecode)} bytes")
            return True
            
    except Exception as e:
        print(f"❌ Error checking contract: {e}")
        return False


def test_with_storage_class():
    """Test using the actual storage class"""
    print("\n" + "="*70)
    print("TESTING WITH SecureCloudStorageWithGanache CLASS")
    print("="*70)
    
    try:
        from step12_integrated_ganache import SecureCloudStorageWithGanache
        
        print("\n[1/2] Creating storage instance...")
        storage = SecureCloudStorageWithGanache("test_user", use_ganache=True)
        print("✅ Storage created")
        
        print("\n[2/2] Getting Ganache status...")
        status = storage.get_ganache_status()
        print(f"Status: {json.dumps(status, indent=2)}")
        
        if status.get('connected'):
            print("\n✅ GANACHE IS PROPERLY CONNECTED!")
        else:
            print(f"\n❌ Ganache connection failed: {status.get('message')}")
            print("\nDEBUGGING INFO:")
            print(f"  - ganache_enabled: {storage.ganache_enabled}")
            if hasattr(storage, 'ganache') and storage.ganache:
                print(f"  - ganache object exists")
            
    except Exception as e:
        import traceback
        print(f"❌ Error: {e}")
        print(f"Traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    # Test 1: Basic contract verification
    contract_deployed = verify_contract()
    
    # Test 2: Test with actual storage class
    test_with_storage_class()
    
    if contract_deployed:
        print("\n" + "="*70)
        print("✅ SOLUTION: Contract IS deployed. Issue is in communication layer.")
        print("="*70)
        print("\nTroubleshooting steps:")
        print("1. Check if there are any exceptions in step12_integrated_ganache.py")
        print("2. Try restarting the Flask app")
        print("3. Check browser console for JavaScript errors")
        print("4. Check Flask server logs for Python errors")
