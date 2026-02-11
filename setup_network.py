"""
Network Setup Helper for Cross-Laptop File Sharing
===================================================

This script helps you configure your system for network sharing.
"""

import socket
import subprocess
import platform
from pathlib import Path


def get_local_ip():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return None


def check_port_available(port):
    """Check if port is available"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex(('localhost', port))
        s.close()
        return result != 0
    except:
        return False


def update_ganache_config():
    """Update Ganache configuration for network access"""
    print("\n📝 Updating Ganache Configuration...")
    print("-" * 80)
    
    ganache_file = Path("step10_full_ganache.py")
    
    if not ganache_file.exists():
        print("❌ step10_full_ganache.py not found!")
        return False
    
    # ✅ READ WITH UTF-8 (FIX)
    with open(ganache_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update GANACHE_URL
    if 'GANACHE_URL = "http://127.0.0.1:7545"' in content:
        content = content.replace(
            'GANACHE_URL = "http://127.0.0.1:7545"',
            'GANACHE_URL = "http://0.0.0.0:7545"'
        )
        
        # ✅ WRITE WITH UTF-8 (FIX)
        with open(ganache_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Updated Ganache URL to listen on all interfaces")
    else:
        print("✅ Ganache URL already configured")
    
    return True


def print_firewall_instructions():
    """Print firewall configuration instructions"""
    system = platform.system()
    
    print("\n🔥 Firewall Configuration:")
    print("-" * 80)
    
    if system == "Windows":
        print("Windows Firewall Instructions:")
        print("1. Open 'Windows Defender Firewall with Advanced Security'")
        print("2. Click 'Inbound Rules' → 'New Rule'")
        print("3. Select 'Port' → Next")
        print("4. Select 'TCP' and enter port: 5000")
        print("5. Select 'Allow the connection'")
        print("6. Apply to all profiles → Next")
        print("7. Name it 'Blockchain File Server'")
        print("8. Repeat for port 7545 (Ganache)")
        print("\nOR run as Administrator:")
        print("  netsh advfirewall firewall add rule name=\"Flask Server\" dir=in action=allow protocol=TCP localport=5000")
        print("  netsh advfirewall firewall add rule name=\"Ganache\" dir=in action=allow protocol=TCP localport=7545")
    
    elif system == "Darwin":  # macOS
        print("macOS Firewall Instructions:")
        print("1. System Preferences → Security & Privacy → Firewall")
        print("2. Click 'Firewall Options'")
        print("3. Click '+' and add Python")
        print("4. Select 'Allow incoming connections'")
    
    elif system == "Linux":
        print("Linux Firewall Instructions (UFW):")
        print("  sudo ufw allow 5000/tcp")
        print("  sudo ufw allow 7545/tcp")
        print("  sudo ufw reload")
    
    print()


def print_ganache_instructions(local_ip):
    """Print Ganache setup instructions"""
    print("\n⛓️  Ganache Configuration:")
    print("-" * 80)
    print("1. Open Ganache application")
    print("2. Click 'Settings' (gear icon)")
    print("3. Go to 'Server' tab")
    print("4. Set:")
    print(f"   - Hostname: 0.0.0.0")
    print(f"   - Port: 7545")
    print("5. Click 'Restart' or 'Save and Restart'")
    print()


def print_usage_instructions(local_ip):
    """Print how to use the system"""
    print("\n" + "=" * 80)
    print("🎉 SETUP COMPLETE!")
    print("=" * 80)
    
    print(f"\n📡 YOUR NETWORK INFORMATION:")
    print(f"   Your IP Address: {local_ip}")
    print(f"   Server Port: 5000")
    print(f"   Ganache Port: 7545")
    
    print(f"\n🚀 HOW TO USE:")
    print(f"\n1️⃣  ON YOUR LAPTOP (Server):")
    print(f"   python step15_network_server.py")
    print(f"   Access at: http://localhost:5000")
    
    print(f"\n2️⃣  ON FRIEND'S LAPTOP (Client):")
    print(f"   Open browser and go to:")
    print(f"   👉 http://{local_ip}:5000")
    print(f"   Login with their username")
    
    print(f"\n3️⃣  SHARING FILES:")
    print(f"   Your Laptop:")
    print(f"   - Login as 'alice'")
    print(f"   - Upload file")
    print(f"   - Click 'Share' → Enter 'bob'")
    print(f"")
    print(f"   Friend's Laptop:")
    print(f"   - Open: http://{local_ip}:5000")
    print(f"   - Login as 'bob'")
    print(f"   - Go to 'Shared' tab")
    print(f"   - Download file from alice!")
    
    print(f"\n⚠️  REQUIREMENTS:")
    print(f"   ✓ Both laptops on same WiFi network")
    print(f"   ✓ Ganache running on YOUR laptop")
    print(f"   ✓ Firewall allows ports 5000 and 7545")
    
    print(f"\n📋 SHARE THIS WITH FRIENDS:")
    print(f"   URL: http://{local_ip}:5000")
    print("=" * 80)


def main():
    """Run network setup"""
    print("=" * 80)
    print("🌐 NETWORK SETUP FOR CROSS-LAPTOP FILE SHARING")
    print("=" * 80)
    
    # Get local IP
    print("\n🔍 Detecting network configuration...")
    local_ip = get_local_ip()
    
    if not local_ip:
        print("❌ Could not detect local IP address!")
        print("   Make sure you're connected to a network")
        return
    
    print(f"✅ Local IP: {local_ip}")
    
    # Check ports
    print("\n🔌 Checking ports...")
    port_5000_free = check_port_available(5000)
    port_7545_free = check_port_available(7545)
    
    if not port_5000_free:
        print("⚠️  Port 5000 is in use (Flask might already be running)")
    else:
        print("✅ Port 5000 is available")
    
    if not port_7545_free:
        print("⚠️  Port 7545 is in use (Ganache might already be running)")
    else:
        print("✅ Port 7545 is available")
    
    # Update Ganache config
    update_ganache_config()
    
    # Print instructions
    print_ganache_instructions(local_ip)
    print_firewall_instructions()
    print_usage_instructions(local_ip)
    
    print("\n✅ Setup complete! Follow the instructions above.")
    print()


if __name__ == "__main__":
    main()
