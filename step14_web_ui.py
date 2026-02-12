"""
STEP 14: Web UI with Flask
===========================

A complete web interface for the blockchain file storage system.

Features:
- File upload with drag & drop
- Download files
- Share files with other users
- View blockchain
- Ganache status dashboard
- User login/switching
"""

from flask import Flask, render_template, request, jsonify, send_file, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
from pathlib import Path
import secrets
import os
import config

# Ensure upload directory exists (important for cloud)
config.FILES_DIR.mkdir(parents=True, exist_ok=True)

# Import our blockchain system
# from step12_integrated_ganache import SecureCloudStorageWithGanache
import config

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-later")
#app.secret_key = secrets.token_hex(16)
CORS(app)

# Store active user sessions
user_sessions = {}

def get_ganache_storage():
    try:
        from step12_integrated_ganache import SecureCloudStorageWithGanache
        return SecureCloudStorageWithGanache()
    except Exception as e:
        print("⚠️ Ganache not available in cloud environment:", e)
        return None

def create_user_storage(user_id):
    try:
        from step12_integrated_ganache import SecureCloudStorageWithGanache
        return SecureCloudStorageWithGanache(user_id, use_ganache=True)
    except Exception as e:
        print("⚠️ Ganache not available, falling back:", e)
        return None


def get_user_storage():
    user_id = session.get("user_id")
    if not user_id:
        return None

    if user_id not in user_sessions:
        user_sessions[user_id] = create_user_storage(user_id)

    return user_sessions[user_id]



@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    user_id = data.get("user_id")
    password = data.get("password")

    if not user_id:
        return jsonify({"success": False, "message": "User ID required"}), 400

    # Create session
    session["user_id"] = user_id

    # Initialize user storage lazily
    if user_id not in user_sessions:
        user_sessions[user_id] = create_user_storage(user_id)

    return jsonify({
        "success": True,
        "user_id": user_id,
        "message": "Login successful"
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


@app.route("/api/status")
def get_status():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"logged_in": False})

    return jsonify({
        "logged_in": True,
        "user_id": user_id
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


@app.route('/api/analyze', methods=['POST'])
def analyze_file():
    """
    Analyze uploaded file - completely static results for same file
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Save uploaded file temporarily
    filename = secure_filename(file.filename)
    temp_path = config.FILES_DIR / f"analyze_{filename}"
    file.save(temp_path)
    
    try:
        # Import static analyzer
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from static_analyzer import StaticFileAnalyzer
        
        # Analyze file (completely deterministic)
        analyzer = StaticFileAnalyzer()
        results = analyzer.analyze_file(temp_path)
        
        # Remove temp file
        os.remove(temp_path)
        
        return jsonify({
            'success': True,
            'results': results
        })
    
    except Exception as e:
        if temp_path.exists():
            os.remove(temp_path)
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


if __name__ == '__main__':
    print("=" * 80)
    print("BLOCKCHAIN FILE STORAGE - WEB UI")
    print("=" * 80)
    print("\n🌐 Starting web server...")
    print("   URL: http://localhost:5000")
    print("\n📝 Features:")
    print("   ✅ File upload with drag & drop")
    print("   ✅ Download encrypted files")
    print("   ✅ Share files with users")
    print("   ✅ View blockchain")
    print("   ✅ Ganache status dashboard")
    print("\n⛓️  Ganache:")
    print("   If Ganache is running, files will auto-sync")
    print("   If not, local storage is used")
    print("\n" + "=" * 80)
    print("\n🚀 Open your browser to: http://localhost:5000\n")
 

    app.run(
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 5000)),
    debug=False
    )
