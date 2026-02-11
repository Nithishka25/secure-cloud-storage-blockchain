"""
STEP 13: Final Demo with Automatic Ganache Sync
================================================

This is the complete demo application that:
- Stores blocks locally (JSON) AND on Ganache
- Works even if Ganache is not running
- Shows Ganache status in the UI
"""

from step12_integrated_ganache import SecureCloudStorageWithGanache
import config
from pathlib import Path


class FinalDemoApp:
    """
    Complete demo with Ganache integration
    
    Features:
    - Auto-connects to Ganache if available
    - Falls back to local storage if Ganache unavailable
    - Shows sync status in menu
    - All file operations work regardless
    """
    
    def __init__(self):
        self.storage = None
        self.current_user = None
    
    def print_header(self):
        """Print application header with Ganache status"""
        print("\n" + "=" * 80)
        print("SECURE CLOUD STORAGE - GANACHE INTEGRATED")
        print("=" * 80)
        
        if self.current_user:
            print(f"👤 User: {self.current_user}")
            print(f"🔗 Local Blocks: {len(self.storage.blockchain)}")
            
            # Show Ganache status
            status = self.storage.get_ganache_status()
            if status['connected']:
                print(f"⛓️  Ganache: ✅ CONNECTED")
                print(f"   Contract: {status['contract'][:10]}...")
                print(f"   Chain Blocks: {status['blocks_on_chain']}")
            else:
                print(f"⛓️  Ganache: ⚠️  {status['message']}")
                print(f"   (Using local storage)")
            
            print("=" * 80)
    
    def print_menu(self):
        """Print main menu"""
        print("\n📋 MENU:")
        print("  1. Upload File")
        print("  2. Download File")
        print("  3. List My Files")
        print("  4. List Shared Files")
        print("  5. Share File")
        print("  6. View Blockchain (Local)")
        print("  7. View Ganache Status")
        print("  8. Switch User")
        print("  9. System Info")
        print("  0. Exit")
        print()
    
    def login(self, user_id=None):
        """Login or create user"""
        if user_id is None:
            user_id = input("👤 Enter user ID (or press Enter for 'demo_user'): ").strip()
            if not user_id:
                user_id = "demo_user"
        
        print(f"\n🔐 Logging in as {user_id}...")
        print("   Connecting to Ganache (if available)...")
        
        self.storage = SecureCloudStorageWithGanache(user_id, use_ganache=True)
        self.current_user = user_id
        
        print(f"✅ Logged in successfully!")
    
    def upload_file(self):
        """Upload file menu"""
        print("\n📤 UPLOAD FILE")
        print("-" * 80)
        
        file_path = input("Enter file path (or press Enter to create test file): ").strip()
        
        if not file_path:
            # Create test file
            test_file = config.FILES_DIR / f"test_{self.current_user}.txt"
            content = f"Test file for {self.current_user}\n"
            content += f"This file is stored on Ganache blockchain!\n"
            content += f"(If Ganache is running)\n"
            with open(test_file, 'w') as f:
                f.write(content)
            file_path = str(test_file)
            print(f"📝 Created test file: {test_file.name}")
        
        try:
            result = self.storage.upload_file(file_path)
            print(f"\n✅ Upload successful!")
            print(f"   File ID: {result['file_id']}")
            print(f"   Local Block: #{result['block_id']}")
            
            if result['ganache_synced']:
                print(f"   ⛓️  Ganache: ✅ Synced to blockchain!")
                print(f"   You can view this in Ganache UI")
            else:
                print(f"   ⛓️  Ganache: ⚠️  Local storage only")
                
        except Exception as e:
            print(f"❌ Upload failed: {e}")
    
    def download_file(self):
        """Download file menu"""
        print("\n📥 DOWNLOAD FILE")
        print("-" * 80)
        
        files = self.storage.list_files()
        if not files:
            print("No files available")
            return
        
        print("Available files:")
        for i, f in enumerate(files, 1):
            status = f"📤 from {f['shared_from']}" if f['is_shared'] else "📁 Your file"
            print(f"  {i}. {f['name']} - {status}")
        
        choice = input("\nSelect file number: ").strip()
        
        try:
            if choice.isdigit() and 1 <= int(choice) <= len(files):
                file_id = files[int(choice) - 1]['file_id']
                file_name = files[int(choice) - 1]['name']
            else:
                print("Invalid choice")
                return
            
            output_path = input(f"Output path (or Enter for '{file_name}'): ").strip()
            if not output_path:
                output_path = config.FILES_DIR / f"downloaded_{file_name}"
            
            downloaded = self.storage.download_file(file_id, output_path)
            print(f"\n✅ Downloaded to: {downloaded}")
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
    
    def list_my_files(self):
        """List only user's own files"""
        print("\n📁 MY FILES")
        print("-" * 80)
        
        files = self.storage.list_files()
        my_files = [f for f in files if not f['is_shared']]
        
        if not my_files:
            print("No files uploaded yet")
            return
        
        for i, f in enumerate(my_files, 1):
            print(f"\n{i}. {f['name']}")
            print(f"   File ID: {f['file_id']}")
            print(f"   Local Block: #{f['block_id']}")
            print(f"   Uploaded: {f['timestamp']}")
        
        print(f"\nTotal: {len(my_files)} file(s)")
    
    def list_shared_files(self):
        """List files shared with this user"""
        print("\n📤 SHARED WITH ME")
        print("-" * 80)
        
        files = self.storage.list_files()
        shared_files = [f for f in files if f['is_shared']]
        
        if not shared_files:
            print("No files shared with you yet")
            print("\nTip: Another user can share files with you!")
            return
        
        for i, f in enumerate(shared_files, 1):
            print(f"\n{i}. {f['name']}")
            print(f"   📤 Shared from: {f['shared_from']}")
            print(f"   File ID: {f['file_id']}")
            print(f"   Block: #{f['block_id']}")
            print(f"   Received: {f['timestamp']}")
        
        print(f"\nTotal: {len(shared_files)} shared file(s)")
    
    def share_file(self):
        """Share file menu"""
        print("\n🤝 SHARE FILE")
        print("-" * 80)
        
        files = self.storage.list_files()
        my_files = [f for f in files if not f['is_shared']]
        
        if not my_files:
            print("No files to share")
            return
        
        print("Your files:")
        for i, f in enumerate(my_files, 1):
            print(f"  {i}. {f['name']}")
        
        choice = input("\nSelect file number: ").strip()
        
        if not choice.isdigit() or not (1 <= int(choice) <= len(my_files)):
            print("Invalid choice")
            return
        
        file_id = my_files[int(choice) - 1]['file_id']
        file_name = my_files[int(choice) - 1]['name']
        
        recipient = input("Enter recipient user ID: ").strip()
        
        if not recipient:
            print("Recipient required")
            return
        
        if recipient == self.current_user:
            print("❌ Cannot share with yourself!")
            return
        
        try:
            share_info = self.storage.share_file(file_id, recipient)
            
            print(f"\n✅ File '{file_name}' shared with {recipient}!")
            
            if share_info.get('ganache_synced'):
                print(f"   ⛓️  Also synced to Ganache blockchain")
            
            print(f"\n📝 {recipient} can now:")
            print(f"   1. Login to their account")
            print(f"   2. View 'Shared Files' (option 4)")
            print(f"   3. Download the file")
            
        except Exception as e:
            print(f"❌ Sharing failed: {e}")
    
    def view_blockchain(self):
        """View local blockchain"""
        print("\n🔗 LOCAL BLOCKCHAIN")
        print("-" * 80)
        
        print(f"Owner: {self.storage.blockchain.owner}")
        print(f"Total Blocks: {len(self.storage.blockchain)}")
        
        print("\n📦 Blocks:")
        for block in self.storage.blockchain.chain:
            print(f"\n  Block #{block.block_id}")
            print(f"    Time: {block.timestamp}")
            print(f"    File: {block.file_id}")
            
            try:
                block_data = __import__('json').loads(block.data)
                if block_data.get('is_shared'):
                    print(f"    Type: 📤 Shared from {block_data.get('shared_from')}")
                else:
                    print(f"    Type: 📁 Own file")
            except:
                print(f"    Type: Genesis")
            
            print(f"    Hash: {block.hash[:32]}...")
        
        if self.storage.blockchain.validate_chain():
            print("\n✅ Blockchain is valid")
        else:
            print("\n❌ Blockchain validation failed!")
    
    def view_ganache_status(self):
        """View detailed Ganache status"""
        print("\n⛓️  GANACHE BLOCKCHAIN STATUS")
        print("-" * 80)
        
        status = self.storage.get_ganache_status()
        
        if status['connected']:
            print(f"\n✅ CONNECTED TO GANACHE")
            print(f"\n📊 Details:")
            print(f"   Contract Address: {status['contract']}")
            print(f"   Network ID: {status['network_id']}")
            print(f"   Blocks on Chain: {status['blocks_on_chain']}")
            
            print(f"\n💡 Benefits:")
            print(f"   ✅ Decentralized storage")
            print(f"   ✅ Immutable records")
            print(f"   ✅ Can view in Ganache UI")
            print(f"   ✅ Ethereum blockchain backed")
            
            print(f"\n🔍 View in Ganache:")
            print(f"   1. Open Ganache UI")
            print(f"   2. Go to 'Transactions' tab")
            print(f"   3. See your block additions")
        else:
            print(f"\n⚠️  NOT CONNECTED")
            print(f"   Reason: {status['message']}")
            
            print(f"\n📝 To enable Ganache:")
            print(f"   1. Download Ganache from trufflesuite.com")
            print(f"   2. Start Ganache (Quick Start)")
            print(f"   3. Run: python step10_full_ganache.py")
            print(f"   4. Restart this demo")
            
            print(f"\n💡 Current setup:")
            print(f"   ✅ Local storage working")
            print(f"   ✅ All features available")
            print(f"   ⚠️  No blockchain backup")
    
    def system_info(self):
        """Display system information"""
        print("\n💻 SYSTEM INFORMATION")
        print("-" * 80)
        
        print(f"\n👤 User Info:")
        print(f"  User ID: {self.current_user}")
        print(f"  Public Key: {self.storage.get_public_key_hex()[:64]}...")
        
        print(f"\n📁 Storage:")
        files = self.storage.list_files()
        own_files = [f for f in files if not f['is_shared']]
        shared_files = [f for f in files if f['is_shared']]
        print(f"  My Files: {len(own_files)}")
        print(f"  Shared Files: {len(shared_files)}")
        print(f"  Total Blocks: {len(self.storage.blockchain)}")
        
        print(f"\n⛓️  Blockchain:")
        status = self.storage.get_ganache_status()
        if status['connected']:
            print(f"  Local: ✅ {len(self.storage.blockchain)} blocks")
            print(f"  Ganache: ✅ {status['blocks_on_chain']} blocks")
            print(f"  Status: FULLY SYNCED")
        else:
            print(f"  Local: ✅ {len(self.storage.blockchain)} blocks")
            print(f"  Ganache: ⚠️  Offline")
            print(f"  Status: LOCAL ONLY")
        
        print(f"\n🔐 Security:")
        print(f"  ✅ AES-256-GCM encryption")
        print(f"  ✅ ECC (secp256k1) keys")
        print(f"  ✅ SHA-256 hashing")
        print(f"  ✅ Dynamic key generation")
        print(f"  ✅ Tamper-proof blockchain")
    
    def run(self):
        """Run the application"""
        self.print_header()
        self.login()
        
        while True:
            self.print_header()
            self.print_menu()
            
            choice = input("Select option: ").strip()
            
            if choice == '1':
                self.upload_file()
            elif choice == '2':
                self.download_file()
            elif choice == '3':
                self.list_my_files()
            elif choice == '4':
                self.list_shared_files()
            elif choice == '5':
                self.share_file()
            elif choice == '6':
                self.view_blockchain()
            elif choice == '7':
                self.view_ganache_status()
            elif choice == '8':
                self.login()
            elif choice == '9':
                self.system_info()
            elif choice == '0':
                print("\n👋 Goodbye!")
                break
            else:
                print("❌ Invalid option")
            
            input("\nPress Enter to continue...")


def main():
    """Main entry point"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║           SECURE CLOUD STORAGE - GANACHE INTEGRATED VERSION                 ║
║                                                                              ║
║  NEW: Automatic Ganache Blockchain Sync!                                    ║
║                                                                              ║
║  📦 Local Storage:  Always works (JSON files)                               ║
║  ⛓️  Ganache Sync:  Automatic (when Ganache running)                        ║
║  🔄 Auto Fallback:  Works even if Ganache offline                           ║
║                                                                              ║
║  SETUP:                                                                      ║
║  1. (Optional) Start Ganache                                                ║
║  2. (Optional) Run: python step10_full_ganache.py                           ║
║  3. Run this demo - it auto-connects!                                       ║
║                                                                              ║
║  FEATURES:                                                                   ║
║  ✅ Upload files → Stored locally + Ganache                                 ║
║  ✅ Share files → Both users get Ganache sync                               ║
║  ✅ View status → See if Ganache connected                                  ║
║  ✅ Works offline → No Ganache? No problem!                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    demo = FinalDemoApp()
    demo.run()


if __name__ == "__main__":
    main()
