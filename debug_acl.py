#!/usr/bin/env python3
"""
Minimal debug script to test ACL check directly
"""
import sys
sys.path.insert(0, '/Users/kanishka/Documents/projj-before novelty')

from step12_integrated_ganache import SecureCloudStorageWithGanache
from step10_full_ganache import GanacheBlockchain

# Initialize storage
storage = SecureCloudStorageWithGanache("alice_debug", use_ganache=True)

# Check if we have ACL contract
print(f"Has ACL contract: {storage.acl_contract is not None}")

# Check the grant  
if storage.acl_contract:
    # Get a file that we know was granted
    file_id = "a1c6b17b-2314-4b13-9295-bcb5add66297"
    user_eth = "0x1234567890123456789012345678901234567890"
    device_id = "0x3e721df4adbb96576b645073dd465a2592020b978aa4276327df970338f7bc9a"
    
    print(f"\nTesting ACL check:")
    print(f"  file_id: {file_id}")
    print(f"  user: {user_eth}")
    print(f"  device_id: {device_id[:20]}...")
    
    result = storage.has_access(file_id, user_eth, device_id)
    print(f"\nResult: {result}")
