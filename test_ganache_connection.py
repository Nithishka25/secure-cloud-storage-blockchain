"""
Ganache Connection Diagnostic Tool
===================================

Tests connection to Ganache and provides troubleshooting steps.
"""

import socket
import time
from web3 import Web3
import config


def test_port_open(host, port, timeout=2):
    """Test if a port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"Error testing port: {e}")
        return False


def test_ganache_connection(ganache_url=None):
    """Test connection to Ganache RPC server"""
    ganache_url = ganache_url or config.GANACHE_URL
    host = ganache_url.replace("http://", "").replace("https://", "").split(":")[0]
    port = int(ganache_url.split(":")[-1])
    
    print("\n" + "="*70)
    print("GANACHE CONNECTION DIAGNOSTIC REPORT")
    print("="*70)
    
    print(f"\n🔍 Testing connection to: {ganache_url}")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    
    # Step 1: Test if port is open
    print("\n[1/3] Checking if port is open...")
    if test_port_open(host, port):
        print(f"✅ Port {port} is OPEN")
    else:
        print(f"❌ Port {port} is CLOSED or not responding")
        print("\n⚠️  SOLUTION: Start Ganache")
        print("   • Install: npm install -g ganache")
        print("   • Run: ganache --host 127.0.0.1 --port 7545")
        print("   • Or use Ganache GUI from: https://trufflesuite.com/ganache/")
        return False
    
    # Step 2: Test Web3 connection
    print("\n[2/3] Testing Web3 connection...")
    try:
        w3 = Web3(Web3.HTTPProvider(ganache_url))
        if w3.is_connected():
            print("✅ Web3 is CONNECTED")
        else:
            print("❌ Web3 connection failed")
            return False
    except Exception as e:
        print(f"❌ Web3 error: {e}")
        return False
    
    # Step 3: Check accounts
    print("\n[3/3] Checking accounts in Ganache...")
    try:
        accounts = w3.eth.accounts
        if accounts:
            print(f"✅ Found {len(accounts)} accounts")
            print(f"\n   Account 0: {accounts[0]}")
            
            # Check balance
            balance = w3.eth.get_balance(accounts[0])
            balance_eth = w3.from_wei(balance, 'ether')
            print(f"   Balance: {balance_eth} ETH")
            
            if float(balance_eth) > 0:
                print("✅ Account has sufficient balance")
            else:
                print("⚠️  Account has no balance")
        else:
            print("❌ No accounts found")
            return False
    except Exception as e:
        print(f"❌ Error checking accounts: {e}")
        return False
    
    print("\n" + "="*70)
    print("✅ ALL CHECKS PASSED - Ganache is ready!")
    print("="*70)
    return True


def test_alternative_ports():
    """Test alternative port configurations"""
    print("\n" + "="*70)
    print("ALTERNATIVE PORT TEST")
    print("="*70)
    
    ports = [
        ("http://127.0.0.1:7545", "Ganache CLI default"),
        ("http://127.0.0.1:8545", "Ganache GUI / common Ethereum"),
        ("http://127.0.0.1:9545", "Alternative Ganache port"),
    ]
    
    for url, desc in ports:
        host = url.replace("http://", "").split(":")[0]
        port = int(url.split(":")[-1])
        
        if test_port_open(host, port, timeout=1):
            print(f"✅ {desc} - {url} is OPEN")
            try:
                w3 = Web3(Web3.HTTPProvider(url))
                if w3.is_connected():
                    print(f"   ✅ Web3 connected!")
                    return url
            except:
                pass
        else:
            print(f"❌ {desc} - {url} is closed")
    
    return None


if __name__ == "__main__":
    # Test current configuration
    success = test_ganache_connection()
    
    if not success:
        print("\n🔄 Trying alternative ports...")
        alt_url = test_alternative_ports()
        
        if alt_url:
            print(f"\n✅ Found Ganache at: {alt_url}")
            print(f"\nUpdate config.py line 15 to:")
            print(f'   GANACHE_URL = "{alt_url}"')
