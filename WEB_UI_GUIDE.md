# 🌐 WEB UI GUIDE

## What You Get

A beautiful, modern web interface for your blockchain file storage system!

**Features:**
- 📤 Drag & drop file upload
- 📁 File management dashboard
- 🤝 Easy file sharing
- ⛓️ Blockchain explorer
- 🔗 Ganache status monitoring
- 📊 Real-time statistics

---

## Setup (3 Steps)

### Step 1: Install Flask

```bash
pip install flask flask-cors --break-system-packages
```

### Step 2: Start Ganache (Optional)

If you want blockchain sync:
```bash
# 1. Open Ganache
# 2. Run once:
python step10_full_ganache.py
```

### Step 3: Start Web Server

```bash
python step14_web_ui.py
```

Output:
```
🌐 Starting web server...
   URL: http://localhost:5000

📝 Features:
   ✅ File upload with drag & drop
   ✅ Download encrypted files
   ✅ Share files with users
   ✅ View blockchain
   ✅ Ganache status dashboard

🚀 Open your browser to: http://localhost:5000
```

---

## Using the Web UI

### 1. Login

**First Time:**
1. Open browser: `http://localhost:5000`
2. Enter a User ID (e.g., "alice")
3. Click "Login"
4. Account created automatically!

**Status Display:**
```
⛓️ Ganache: ✅ Connected    (if Ganache running)
OR
⛓️ Ganache: ⚠️ Offline     (if not running)
```

### 2. Upload Files

**Method 1: Drag & Drop**
- Drag file from your computer
- Drop onto the upload zone
- Done! ✅

**Method 2: Click to Browse**
- Click the upload zone
- Select file
- Upload starts automatically

**After Upload:**
```
✅ File uploaded successfully!
Block #1
✅ Synced to Ganache    (if connected)
```

### 3. Download Files

**Tab: My Files**
1. Click "📁 My Files" tab
2. See all your uploaded files
3. Click "Download" button
4. File decrypted and downloaded!

### 4. Share Files

**Tab: My Files**
1. Find file you want to share
2. Click "Share" button
3. Enter recipient's User ID
4. Click "Share"
5. Done! ✅

**Recipient's View:**
1. They login to their account
2. Click "🤝 Shared" tab
3. See your shared file!
4. Can download it

### 5. View Blockchain

**Tab: ⛓️ Blockchain**
- See all blocks in your chain
- Block details (hash, timestamp, file ID)
- Validation status
- Shared file indicators

### 6. Ganache Dashboard

**Tab: 🔗 Ganache**

**If Connected:**
```
Status: ✅ Connected
Blocks on Chain: 5
Network ID: 1337

✅ Decentralized storage
✅ Immutable records
✅ View in Ganache UI
```

**If Offline:**
```
Status: ⚠️ Offline

Setup instructions:
1. Download Ganache
2. Start Ganache
3. Deploy contract
4. Refresh page
```

---

## Features Explained

### 📤 Upload Tab
- **Drag & Drop**: Modern file upload
- **Status**: Shows if synced to Ganache
- **Encryption**: Automatic AES-256 encryption
- **Progress**: Real-time upload feedback

### 📁 My Files Tab
- **List**: All your uploaded files
- **Actions**: Download or Share
- **Metadata**: Block number, timestamp
- **Search**: Find files quickly (coming soon)

### 🤝 Shared Tab
- **Received**: Files others shared with you
- **Source**: Shows who shared it
- **Download**: Access shared files
- **Indication**: Clear "shared from" marker

### ⛓️ Blockchain Tab
- **Explorer**: See all blocks
- **Details**: Hash, previous hash, timestamp
- **Types**: Own files vs shared files
- **Validation**: Tamper-proof verification

### 🔗 Ganache Tab
- **Status**: Real-time connection status
- **Stats**: Blocks on chain, network ID
- **Contract**: Smart contract address
- **Setup**: Instructions if offline

---

## Multi-User Testing

### Scenario: Alice shares with Bob

**Terminal 1: Start Server**
```bash
python step14_web_ui.py
```

**Browser 1: Alice**
```
1. Open: http://localhost:5000
2. Login as: alice
3. Upload a file
4. Click "Share"
5. Enter: bob
6. Click "Share"
```

**Browser 2: Bob** (Incognito/Private window)
```
1. Open: http://localhost:5000
2. Login as: bob
3. Click "🤝 Shared" tab
4. See Alice's file!
5. Click "Download"
```

**Result:** Bob successfully downloads Alice's file! ✅

---

## File Structure

```
your-project/
├── step14_web_ui.py          ← Flask server
├── templates/
│   └── index.html            ← Web interface
├── static/
│   └── app.js                ← JavaScript code
├── data/                     ← Created automatically
│   ├── blockchain/
│   ├── files/
│   ├── encrypted/
│   └── keys/
```

---

## Compared to Command Line Demo

| Feature | CLI (step13) | Web UI (step14) |
|---------|-------------|-----------------|
| Interface | Terminal | Browser |
| Upload | Text input | Drag & drop |
| Visual | Text only | Modern UI |
| Multi-tab | No | Yes |
| Dashboard | No | Yes |
| Ease of use | ★★☆☆☆ | ★★★★★ |

---

## Screenshots (What You'll See)

### Login Screen
```
┌────────────────────────────────────┐
│   🔐 Blockchain File Storage       │
│                                    │
│   Secure file storage with AES-   │
│   256 encryption and blockchain    │
│                                    │
│   ┌──────────────────────────┐    │
│   │ Enter your User ID       │    │
│   └──────────────────────────┘    │
│                                    │
│   [       Login       ]            │
│                                    │
│   Don't have an account?           │
│   Just enter a new User ID!        │
└────────────────────────────────────┘
```

### Main Dashboard
```
┌────────────────────────────────────────────────────────────┐
│ 🔗 Blockchain File Storage        User: alice             │
│                                    3 Blocks  ✅ Connected   │
├────────────────────────────────────────────────────────────┤
│ [📤 Upload] [📁 My Files] [🤝 Shared] [⛓️ Blockchain] [🔗 Ganache] │
├────────────────────────────────────────────────────────────┤
│                                                            │
│           📂 Drag & Drop File Here                         │
│           or click to browse                               │
│                                                            │
│   ✅ File uploaded successfully!                           │
│   Block #3                                                 │
│   ✅ Synced to Ganache                                     │
└────────────────────────────────────────────────────────────┘
```

### Files List
```
┌────────────────────────────────────────────────────────────┐
│ My Files                                                   │
├────────────────────────────────────────────────────────────┤
│ 📄 document.pdf                           [Download] [Share]│
│ Block #1 • Jan 30, 2026, 3:45 PM                          │
├────────────────────────────────────────────────────────────┤
│ 📄 report.docx                           [Download] [Share]│
│ Block #2 • Jan 30, 2026, 4:12 PM                          │
└────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### "Cannot connect" error

```bash
# Check if Flask is installed
pip install flask flask-cors --break-system-packages

# Check if port 5000 is available
# Windows: netstat -ano | findstr :5000
# Mac/Linux: lsof -i :5000
```

### Files don't upload

```bash
# Check data directory exists
# Should be created automatically

# Check permissions
# Make sure you can write to the directory
```

### Ganache shows offline

```bash
# This is normal if Ganache not running
# Web UI works fine without Ganache!

# To enable Ganache:
1. Start Ganache
2. Run: python step10_full_ganache.py
3. Refresh web page
```

### Share doesn't work

```bash
# Both users must have logged in at least once
# Solution: Have recipient login first, then share
```

---

## Advanced Features

### Custom Port

```python
# Edit step14_web_ui.py, change last line:
app.run(debug=True, port=8080)  # Use port 8080
```

### Production Deployment

```bash
# Install production server
pip install gunicorn --break-system-packages

# Run
gunicorn -w 4 -b 0.0.0.0:5000 step14_web_ui:app
```

### HTTPS (SSL)

```python
# Generate certificate
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Edit step14_web_ui.py:
app.run(debug=True, port=5000, ssl_context=('cert.pem', 'key.pem'))
```

---

## Comparison with Video

Based on the video transcript you shared, here's how our implementation compares:

| Feature | Video Project | Our Implementation |
|---------|--------------|-------------------|
| File Upload | ✅ | ✅ Web UI + Drag & Drop |
| Encryption | AES | ✅ AES-256-GCM |
| Blockchain | ✅ | ✅ + Ganache |
| File Sharing | ✅ | ✅ Multi-user |
| Key Management | ✅ | ✅ ECC-based |
| Web Interface | ✅ | ✅ Modern UI |
| Download | ✅ | ✅ Decryption |
| User Auth | ✅ | ✅ Session-based |
| MetaMask | ✅ | ⚠️ Not implemented |

**Advantages of our implementation:**
- ✅ Dynamic key generation (from paper)
- ✅ Ganache integration
- ✅ Modern responsive UI
- ✅ Drag & drop upload
- ✅ Real-time status
- ✅ Blockchain explorer

---

## Quick Commands

```bash
# Install everything
pip install flask flask-cors pycryptodome ecdsa web3 py-solc-x --break-system-packages

# Start web UI
python step14_web_ui.py

# In browser
http://localhost:5000
```

---

## Success Checklist

✅ Web server starts successfully
✅ Can open http://localhost:5000
✅ Can login with user ID
✅ Can upload files (drag & drop works)
✅ Can download files
✅ Can share files between users
✅ Can view blockchain
✅ Ganache status shows correctly

---

## What's Next?

### Enhancements You Can Add:

1. **Search & Filter**
   - Search files by name
   - Filter by date
   - Sort by size

2. **File Preview**
   - Preview images
   - Preview PDFs
   - Preview text files

3. **Bulk Operations**
   - Upload multiple files
   - Download as ZIP
   - Batch sharing

4. **Analytics**
   - Storage usage
   - Upload history
   - Sharing stats

5. **Mobile App**
   - React Native
   - Flutter
   - Progressive Web App

---

**Your blockchain file storage now has a beautiful web interface!** 🎉

Open `http://localhost:5000` and enjoy! 
