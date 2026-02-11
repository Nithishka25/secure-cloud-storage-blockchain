"""
STEP 8: Interactive Demo Application
=====================================

This is an interactive command-line demo of the secure cloud storage system.
"""

from step7_complete_system import SecureCloudStorage
import config
from pathlib import Path


class DemoApp:
    """Interactive demo application"""
    
    def __init__(self):
        self.storage = None
        self.current_user = None
    
    def print_header(self):
        """Print application header"""
        print("\n" + "=" * 80)
        print("SECURE CLOUD STORAGE SYSTEM")
        print("Dynamic AES Encryption + Blockchain Key Management")
        print("=" * 80)
        
        if self.current_user:
            print(f"👤 User: {self.current_user}")
            print(f"🔗 Blockchain: {len(self.storage.blockchain)} blocks")
            print("=" * 80)
    
    def print_menu(self):
        """Print main menu"""
        print("\n📋 MENU:")
        print("  1. Upload File")
        print("  2. Download File")
        print("  3. List Files")
        print("  4. Share File")
        print("  5. View Blockchain")
        print("  6. Switch User")
        print("  7. System Info")
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
            content = f"Test file for {self.current_user}\nCreated by demo application\n"
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
            print(f"  {i}. {f['name']} (ID: {f['file_id'][:8]}...)")
        
        choice = input("\nSelect file number (or Enter file ID): ").strip()
        
        try:
            if choice.isdigit() and 1 <= int(choice) <= len(files):
                file_id = files[int(choice) - 1]['file_id']
            else:
                file_id = choice
            
            output_path = input("Output path (or press Enter for default): ").strip()
            if not output_path:
                output_path = None
            
            downloaded = self.storage.download_file(file_id, output_path)
            print(f"\n✅ Downloaded to: {downloaded}")
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
    
    def list_files(self):
        """List all files"""
        print("\n📁 YOUR FILES")
        print("-" * 80)
        
        files = self.storage.list_files()
        
        if not files:
            print("No files uploaded yet")
            return
        
        for i, f in enumerate(files, 1):
            print(f"\n{i}. {f['name']}")
            print(f"   File ID: {f['file_id']}")
            print(f"   Block: #{f['block_id']}")
            print(f"   Uploaded: {f['timestamp']}")
        
        print(f"\nTotal: {len(files)} file(s)")
    
    def share_file(self):
        """Share file menu"""
        print("\n🤝 SHARE FILE")
        print("-" * 80)
        
        # Show files
        files = self.storage.list_files()
        if not files:
            print("No files to share")
            return
        
        print("Your files:")
        for i, f in enumerate(files, 1):
            print(f"  {i}. {f['name']}")
        
        choice = input("\nSelect file number: ").strip()
        
        if not choice.isdigit() or not (1 <= int(choice) <= len(files)):
            print("Invalid choice")
            return
        
        file_id = files[int(choice) - 1]['file_id']
        recipient = input("Enter recipient user ID: ").strip()
        
        if not recipient:
            print("Recipient required")
            return
        
        try:
            # Make sure recipient exists
            recipient_storage = SecureCloudStorage(recipient)
            
            share_info = self.storage.share_file(file_id, recipient)
            print(f"\n✅ File shared with {recipient}!")
            print(f"   They can now access the file securely")
            
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
            print(f"    Hash: {block.hash[:32]}...")
            print(f"    Prev: {block.previous_hash[:32]}...")
        
        # Validate
        if self.storage.blockchain.validate_chain():
            print("\n✅ Blockchain is valid (tamper-proof)")
        else:
            print("\n❌ Blockchain validation failed!")
    
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
        print(f"  Files: {len(files)}")
        print(f"  Blocks: {len(self.storage.blockchain)}")
        
        print(f"\n🔐 Security Features:")
        print(f"  ✅ Dynamic AES-256-GCM encryption")
        print(f"  ✅ ECC (secp256k1) key management")
        print(f"  ✅ SHA-256 hashing")
        print(f"  ✅ Blockchain key storage")
        print(f"  ✅ File-level unique keys")
        print(f"  ✅ Tamper-proof blockchain")
    
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
                self.list_files()
            elif choice == '4':
                self.share_file()
            elif choice == '5':
                self.view_blockchain()
            elif choice == '6':
                self.login()
            elif choice == '7':
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
║                    SECURE CLOUD STORAGE SYSTEM                               ║
║                                                                              ║
║  Implementation of:                                                          ║
║  "Dynamic AES Encryption and Blockchain Key Management"                     ║
║                                                                              ║
║  Features:                                                                   ║
║  • Dynamic AES-256 encryption with unique keys per file                     ║
║  • ECC (secp256k1) public/private key management                            ║
║  • Blockchain-based key storage                                             ║
║  • Secure file sharing                                                      ║
║  • Tamper-proof data integrity                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    demo = DemoApp()
    demo.run()


if __name__ == "__main__":
    main()
