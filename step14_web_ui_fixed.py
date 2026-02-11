"""
STEP 14: Web UI with Flask (FIXED FOR WINDOWS)
===============================================

Fixed version that handles template paths correctly on Windows.
"""

from flask import Flask, render_template, request, jsonify, send_file, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
from pathlib import Path
import secrets
import sys

# Add current directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our blockchain system
from step12_integrated_ganache import SecureCloudStorageWithGanache
import config

# Get the directory where this script is located
BASE_DIR = Path(__file__).parent.absolute()

# Create Flask app with explicit template folder
app = Flask(__name__, 
            template_folder=str(BASE_DIR / 'templates'),
            static_folder=str(BASE_DIR / 'static'))

app.secret_key = secrets.token_hex(16)
CORS(app)

# Store active user sessions
user_sessions = {}

print(f"📁 Base directory: {BASE_DIR}")
print(f"📁 Templates directory: {BASE_DIR / 'templates'}")
print(f"📁 Static directory: {BASE_DIR / 'static'}")

# Check if directories exist
templates_dir = BASE_DIR / 'templates'
static_dir = BASE_DIR / 'static'

if not templates_dir.exists():
    print(f"⚠️  Creating templates directory: {templates_dir}")
    templates_dir.mkdir(exist_ok=True)

if not static_dir.exists():
    print(f"⚠️  Creating static directory: {static_dir}")
    static_dir.mkdir(exist_ok=True)

# Check for index.html
index_html = templates_dir / 'index.html'
if not index_html.exists():
    print(f"❌ ERROR: index.html not found at {index_html}")
    print(f"   Please make sure templates/index.html exists in the same directory as this script")
else:
    print(f"✅ Found index.html")

# Check for app.js
app_js = static_dir / 'app.js'
if not app_js.exists():
    print(f"⚠️  app.js not found at {app_js}")
else:
    print(f"✅ Found app.js")


def get_user_storage():
    """Get storage instance for current user"""
    if 'user_id' not in session:
        return None
    
    user_id = session['user_id']
    
    # Create or get existing storage
    if user_id not in user_sessions:
        user_sessions[user_id] = SecureCloudStorageWithGanache(user_id, use_ganache=True)
    
    return user_sessions[user_id]


@app.route('/')
def index():
    """Main page"""
    try:
        return render_template('index.html')
    except Exception as e:
        return f"""
        <h1>Template Error</h1>
        <p>Error: {str(e)}</p>
        <p>Template folder: {app.template_folder}</p>
        <p>Looking for: index.html</p>
        <p>Please make sure templates/index.html exists in: {BASE_DIR}</p>
        """, 500


@app.route('/api/login', methods=['POST'])
def login():
    """Login user"""
    data = request.json
    user_id = data.get('user_id', '').strip()
    
    if not user_id:
        return jsonify({'error': 'User ID required'}), 400
    
    session['user_id'] = user_id
    
    # Initialize storage
    storage = SecureCloudStorageWithGanache(user_id, use_ganache=True)
    user_sessions[user_id] = storage
    
    # Get status
    ganache_status = storage.get_ganache_status()
    
    return jsonify({
        'success': True,
        'user_id': user_id,
        'blocks': len(storage.blockchain),
        'ganache_connected': ganache_status['connected'],
        'ganache_status': ganache_status
    })


@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout user"""
    if 'user_id' in session:
        user_id = session['user_id']
        if user_id in user_sessions:
            del user_sessions[user_id]
        session.pop('user_id')
    
    return jsonify({'success': True})


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current user status"""
    storage = get_user_storage()
    if not storage:
        return jsonify({'logged_in': False}), 401
    
    ganache_status = storage.get_ganache_status()
    files = storage.list_files()
    
    return jsonify({
        'logged_in': True,
        'user_id': session['user_id'],
        'blocks': len(storage.blockchain),
        'files': len(files),
        'ganache_connected': ganache_status['connected'],
        'ganache_status': ganache_status
    })


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload and encrypt file"""
    storage = get_user_storage()
    if not storage:
        return jsonify({'error': 'Not logged in'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Save uploaded file temporarily
    filename = secure_filename(file.filename)
    temp_path = config.FILES_DIR / f"upload_{filename}"
    file.save(temp_path)
    
    try:
        # Upload to blockchain system
        result = storage.upload_file(temp_path)
        
        # Remove temp file
        os.remove(temp_path)
        
        return jsonify({
            'success': True,
            'file_id': result['file_id'],
            'filename': result['original_name'],
            'size': result['size'],
            'block_id': result['block_id'],
            'ganache_synced': result['ganache_synced']
        })
    
    except Exception as e:
        if temp_path.exists():
            os.remove(temp_path)
        return jsonify({'error': str(e)}), 500


@app.route('/api/files', methods=['GET'])
def list_files():
    """List all files"""
    storage = get_user_storage()
    if not storage:
        return jsonify({'error': 'Not logged in'}), 401
    
    files = storage.list_files()
    
    return jsonify({
        'files': files,
        'total': len(files)
    })


@app.route('/api/download/<file_id>', methods=['GET'])
def download_file(file_id):
    """Download and decrypt file"""
    storage = get_user_storage()
    if not storage:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        # Download file
        output_path = storage.download_file(file_id)
        
        # Send file
        return send_file(
            output_path,
            as_attachment=True,
            download_name=output_path.name
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/share', methods=['POST'])
def share_file():
    """Share file with another user"""
    storage = get_user_storage()
    if not storage:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.json
    file_id = data.get('file_id')
    recipient = data.get('recipient')
    
    if not file_id or not recipient:
        return jsonify({'error': 'File ID and recipient required'}), 400
    
    try:
        share_info = storage.share_file(file_id, recipient)
        
        return jsonify({
            'success': True,
            'file_id': file_id,
            'recipient': recipient,
            'ganache_synced': share_info.get('ganache_synced', False)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/blockchain', methods=['GET'])
def get_blockchain():
    """Get blockchain data"""
    storage = get_user_storage()
    if not storage:
        return jsonify({'error': 'Not logged in'}), 401
    
    blocks = []
    for block in storage.blockchain.chain:
        block_dict = block.to_dict()
        
        # Parse data to get metadata
        try:
            data = json.loads(block.data)
            block_dict['is_shared'] = data.get('is_shared', False)
            block_dict['shared_from'] = data.get('shared_from', None)
        except:
            block_dict['is_shared'] = False
            block_dict['shared_from'] = None
        
        blocks.append(block_dict)
    
    return jsonify({
        'blocks': blocks,
        'total': len(blocks),
        'valid': storage.blockchain.validate_chain()
    })


@app.route('/api/ganache/status', methods=['GET'])
def ganache_status():
    """Get detailed Ganache status"""
    storage = get_user_storage()
    if not storage:
        return jsonify({'error': 'Not logged in'}), 401
    
    status = storage.get_ganache_status()
    return jsonify(status)


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("BLOCKCHAIN FILE STORAGE - WEB UI")
    print("=" * 80)
    print("\n🌐 Starting web server...")
    print(f"   Base Directory: {BASE_DIR}")
    print(f"   URL: http://localhost:5000")
    print("\n📝 Features:")
    print("   ✅ File upload with drag & drop")
    print("   ✅ Download encrypted files")
    print("   ✅ Share files with users")
    print("   ✅ View blockchain")
    print("   ✅ Ganache status dashboard")
    print("\n⛓️  Ganache:")
    print("   If Ganache is running, files will auto-sync")
    print("   If not, local storage is used")
    
    # Check if templates exist before starting
    if not (templates_dir / 'index.html').exists():
        print("\n" + "=" * 80)
        print("❌ ERROR: Missing templates/index.html")
        print("=" * 80)
        print("\nPlease make sure you have these files in the same directory:")
        print("  1. step14_web_ui_fixed.py (this file)")
        print("  2. templates/index.html")
        print("  3. static/app.js")
        print("\nDirectory structure should be:")
        print("  your-folder/")
        print("  ├── step14_web_ui_fixed.py")
        print("  ├── templates/")
        print("  │   └── index.html")
        print("  └── static/")
        print("      └── app.js")
        print("\n" + "=" * 80)
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    print("\n" + "=" * 80)
    print("\n🚀 Open your browser to: http://localhost:5000\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')
