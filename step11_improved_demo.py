"""
STEP 11: Updated Demo App with Fixed File Sharing
==================================================

This demo includes:
- Fixed file sharing (recipients can see shared files)
- Optional Ganache integration
- Better UI for shared files
"""

from step9_improved_sharing import SecureCloudStorage
import config
from pathlib import Path


class ImprovedDemoApp:
    """Updated demo application with proper file sharing"""
    
    def __init__(self):
        self.storage = None
        self.current_user = None
        self.use_ganache = False
    
    def print_header(self):
        """Print application header"""
        print("\n" + "=" * 80)
        print("SECURE CLOUD STORAGE SYSTEM - IMPROVED VERSION")
        print("Dynamic AES Encryption + Blockchain Key Management + File Sharing")
        print("=" * 80)
        
        if self.current_user:
            print(f"👤 User: {self.current_user}")
            print(f"🔗 Blockchain: {len(self.storage.blockchain)} blocks")
            if self.use_ganache:
                print(f"⛓️  Ganache: ENABLED")
            print("=" * 80)
    
    def print_menu(self):
        """Print main menu"""
        print("\n📋 MENU:")
        print("  1. Upload File")
        print("  2. Download File")
        print("  3. List My Files")
        print("  4. List Shared Files (received from others)")
        print("  5. Share File")
        print("  6. View Blockchain")
        print("  7. Switch User")
        print("  8. System Info")
        print("  9. View Sharing History")
        print("  0. Exit")
        print()
    
    def login(self, user_id=None):
        """Login or create user"""
        if user_id is None:
            user_id = input("👤 Enter user ID (or press Enter for 'demo_user'): ").strip()
            if not user_id:
                user_id = "demo_user"
        
        print(f"\n🔐 Logging in as {user_id}...")
        self.storage = SecureCloudStorage(user_id)
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
            content += f"Created by demo application\n"
            content += f"This file can be shared with other users!\n"
            with open(test_file, 'w') as f:
                f.write(content)
            file_path = str(test_file)
            print(f"📝 Created test file: {test_file.name}")
        
        try:
            result = self.storage.upload_file(file_path)
            print(f"\n✅ Upload successful!")
            print(f"   File ID: {result['file_id']}")
            print(f"   Block: #{result['block_id']}")
            print(f"   Size: {result['size']} bytes")
        except Exception as e:
            print(f"❌ Upload failed: {e}")
    
    def download_file(self):
        """Download file menu"""
        print("\n📥 DOWNLOAD FILE")
        print("-" * 80)
        
        # Show available files
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
            print(f"   Block: #{f['block_id']}")
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
            print("\nTip: Ask another user to share files with you!")
            return
        
        for i, f in enumerate(shared_files, 1):
            print(f"\n{i}. {f['name']}")
            print(f"   📤 Shared from: {f['shared_from']}")
            print(f"   File ID: {f['file_id']}")
            print(f"   Block: #{f['block_id']}")
            print(f"   Received: {f['timestamp']}")
        
        print(f"\nTotal: {len(shared_files)} shared file(s)")
    
    def share_file(self):
        """Share file menu - IMPROVED VERSION"""
        print("\n🤝 SHARE FILE")
        print("-" * 80)
        
        # Show only user's own files
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
            print(f"\n📝 What happens next:")
            print(f"   1. {recipient} logs into their account")
            print(f"   2. They select 'List Shared Files' (option 4)")
            print(f"   3. They'll see your shared file with your name")
            print(f"   4. They can download and decrypt it")
            
        except Exception as e:
            print(f"❌ Sharing failed: {e}")
    
    def view_blockchain(self):
        """View blockchain details"""
        print("\n🔗 BLOCKCHAIN")
        print("-" * 80)
        
        print(f"Owner: {self.storage.blockchain.owner}")
        print(f"Total Blocks: {len(self.storage.blockchain)}")
        print(f"Branches: {len(self.storage.blockchain.branches)}")
        
        print("\n📦 Blocks:")
        for block in self.storage.blockchain.chain:
            print(f"\n  Block #{block.block_id}")
            print(f"    Time: {block.timestamp}")
            print(f"    File: {block.file_id}")
            
            # Check if shared
            try:
                block_data = __import__('json').loads(block.data)
                if block_data.get('is_shared'):
                    print(f"    Type: 📤 Shared from {block_data.get('shared_from')}")
                else:
                    print(f"    Type: 📁 Own file")
            except:
                pass
            
            print(f"    Hash: {block.hash[:32]}...")
            print(f"    Prev: {block.previous_hash[:32]}...")
        
        # Validate
        if self.storage.blockchain.validate_chain():
            print("\n✅ Blockchain is valid (tamper-proof)")
        else:
            print("\n❌ Blockchain validation failed!")
    
    def view_sharing_history(self):
        """View sharing history"""
        print("\n📊 SHARING HISTORY")
        print("-" * 80)
        
        shares_path = config.DATA_DIR / 'shares.json'
        if not shares_path.exists():
            print("No sharing history yet")
            return
        
        with open(shares_path, 'r') as f:
            shares = __import__('json').load(f)
        
        # Filter for current user
        my_shares_sent = [s for s in shares if s['sender'] == self.current_user]
        my_shares_received = [s for s in shares if s['recipient'] == self.current_user]
        
        if my_shares_sent:
            print(f"\n📤 Files I shared ({len(my_shares_sent)}):")
            for s in my_shares_sent:
                print(f"  • Shared with {s['recipient']} on {s['timestamp'][:10]}")
        
        if my_shares_received:
            print(f"\n📥 Files shared with me ({len(my_shares_received)}):")
            for s in my_shares_received:
                print(f"  • From {s['sender']} on {s['timestamp'][:10]}")
        
        if not my_shares_sent and not my_shares_received:
            print("No sharing activity for this user")
    
    def system_info(self):
        """Display system information"""
        print("\n💻 SYSTEM INFORMATION")
        print("-" * 80)
        
        print(f"\n📊 Configuration:")
        print(f"  AES Key Size: {config.AES_KEY_SIZE} bits")
        print(f"  ECC Curve: {config.ECC_CURVE}")
        print(f"  Hash Algorithm: {config.HASH_ALGORITHM}")
        print(f"  Data Directory: {config.DATA_DIR}")
        
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
        
        print(f"\n🔐 Security Features:")
        print(f"  ✅ Dynamic AES-256-GCM encryption")
        print(f"  ✅ ECC (secp256k1) key management")
        print(f"  ✅ SHA-256 hashing")
        print(f"  ✅ Blockchain key storage")
        print(f"  ✅ File-level unique keys")
        print(f"  ✅ Tamper-proof blockchain")
        print(f"  ✅ Secure file sharing")
    
    def run(self):
        """Run the demo application"""
        self.print_header()
        
        # Login
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
                self.login()
            elif choice == '8':
                self.system_info()
            elif choice == '9':
                self.view_sharing_history()
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
║              SECURE CLOUD STORAGE SYSTEM - IMPROVED VERSION                 ║
║                                                                              ║
║  NEW FEATURES:                                                               ║
║  ✅ Fixed file sharing - recipients can now see shared files!               ║
║  ✅ Separate views for own files vs shared files                            ║
║  ✅ Sharing history tracking                                                ║
║  ✅ Better UI with clear indicators                                         ║
║                                                                              ║
║  TRY THIS:                                                                   ║
║  1. Login as "alice"                                                        ║
║  2. Upload a file                                                           ║
║  3. Share it with "bob"                                                     ║
║  4. Switch to "bob" (option 7)                                              ║
║  5. View shared files (option 4) - you'll see Alice's file!                ║
║  6. Download it (option 2)                                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    demo = ImprovedDemoApp()
    demo.run()


if __name__ == "__main__":
    main()
