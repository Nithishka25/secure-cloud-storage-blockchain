# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies (1 minute)

```bash
pip install pycryptodome ecdsa web3 --break-system-packages
```

### Step 2: Test the System (2 minutes)

```bash
# Test each component
python step2_crypto_aes.py       # AES encryption
python step3_crypto_ecc.py       # ECC encryption
python step4_dynamic_key_gen.py  # Dynamic keys
python step5_blockchain_structure.py  # Blockchain
python step7_complete_system.py  # Full system
```

You should see ✅ symbols and "ALL TESTS PASSED!" for each.

### Step 3: Run the Demo (2 minutes)

```bash
python step8_demo_app.py
```

Try these actions:
1. Press Enter to use default user
2. Press 1 to upload (then press Enter to create test file)
3. Press 3 to list files
4. Press 2 to download
5. Press 5 to view blockchain

## 📁 Project Structure

```
blockchain-encryption/
├── config.py                    # Configuration
├── step2_crypto_aes.py         # AES encryption
├── step3_crypto_ecc.py         # ECC encryption
├── step4_dynamic_key_gen.py    # Dynamic key generation
├── step5_blockchain_structure.py # Blockchain
├── step6_ganache_integration.py  # Ganache (optional)
├── step7_complete_system.py    # Complete system
├── step8_demo_app.py           # Interactive demo
└── data/                        # Auto-created storage
    ├── keys/                    # User keys
    ├── files/                   # Original files
    ├── encrypted/               # Encrypted files
    └── blockchain/              # Blockchain data
```

## 🎯 What It Does

This system implements the research paper:
**"Dynamic AES Encryption and Blockchain Key Management"**

### Key Features

✅ **Dynamic Encryption**: Each file gets a unique encryption key
✅ **Blockchain Storage**: Keys stored in tamper-proof blockchain
✅ **ECC Security**: Public/private key encryption
✅ **File Sharing**: Secure sharing between users
✅ **Integrity**: Automatic tamper detection

### How It Works

1. **Upload File** → File hashed → Blockchain hashed → Keys XORed → Unique AES key
2. **Encrypt** → File encrypted with AES-256-GCM
3. **Secure Key** → AES key encrypted with ECC public key
4. **Store** → Encrypted key saved in blockchain block
5. **Download** → Block decrypted → AES key retrieved → File decrypted

## 🔐 Security Highlights

- **AES-256-GCM**: Military-grade encryption
- **secp256k1**: Bitcoin/Ethereum-grade key management
- **SHA-256**: Cryptographic hashing
- **Blockchain**: Tamper-proof storage
- **Dynamic Keys**: Each file = unique key

## 🧪 Quick Tests

### Test 1: Upload and Download
```bash
python step7_complete_system.py
```
Look for: "✅ File content matches original!"

### Test 2: Interactive Demo
```bash
python step8_demo_app.py
```
Upload a file, then download it - verify it works!

### Test 3: File Sharing
```bash
python step8_demo_app.py
```
1. Create user "alice" (option 6)
2. Upload file (option 1)
3. Share with "bob" (option 4)
4. Switch to "bob" (option 6)
5. View shared files

## ⚠️ Troubleshooting

### "Module not found"
```bash
pip install pycryptodome ecdsa web3 --break-system-packages
```

### "Permission denied"
Run from your home directory or Documents folder

### Tests fail with ❌
1. Check Python version: `python --version` (need 3.8+)
2. Reinstall packages
3. Run tests in order (step2 → step3 → step4 → etc.)

## 📚 Learn More

- **Full Guide**: See `IMPLEMENTATION_GUIDE.md`
- **Paper**: `Dynamic_AES_Encryption_and_Blockchain_Key_Management.pdf`
- **Code**: Each step file has detailed comments

## 🎉 Success Indicators

You'll know it's working when you see:
- ✅ symbols in test output
- "ALL TESTS PASSED!" messages
- Files created in `data/` directory
- Blockchain saved as JSON files
- Upload/download works in demo

## 💡 Next Steps

1. **Understand the code**: Read through each step file
2. **Modify**: Try changing encryption parameters
3. **Extend**: Add new features (web UI, cloud storage, etc.)
4. **Deploy**: Connect to real Ganache blockchain

---

**You're all set!** The system is ready to use. 🎊

For detailed documentation, see `IMPLEMENTATION_GUIDE.md`
