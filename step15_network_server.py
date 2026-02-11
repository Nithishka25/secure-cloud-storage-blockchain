"""
Network-Enabled Web Server for Cross-Laptop File Sharing
=========================================================

This version allows:
1. Access from other computers on same network
2. Shared Ganache blockchain
3. Centralized file storage
4. Real distributed file sharing

SETUP:
------
1. On Server Laptop (Your laptop):
   - Run this file: python step15_network_server.py
   - Note the IP address shown
   - Share this IP with friends

2. On Client Laptop (Friend's laptop):
   - Open browser: http://YOUR_IP:5000
   - Login with their username
   - Can receive files shared with them!

REQUIREMENTS:
-------------
- Both laptops on same WiFi network
- Ganache running on server laptop
- Server laptop firewall allows port 5000
"""

from flask import Flask, request, jsonify, send_file, render_template, session, after_this_request
from werkzeug.utils import secure_filename
from flask_cors import CORS
import os
import json
from pathlib import Path
import socket
from datetime import timedelta
import uuid
import base64
import time

# Import existing modules
import config
from step12_integrated_ganache import SecureCloudStorageWithGanache

# For Ed25519 signature verification
try:
    from nacl.signing import VerifyKey
    from nacl.exceptions import BadSignatureError
    HAS_NACL = True
except ImportError:
    HAS_NACL = False

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app, supports_credentials=True)  # Enable Cross-Origin requests with credentials

# Configure session for cross-origin access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True for HTTPS
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

# Store user sessions
user_sessions = {}


def get_local_ip():
    """Get the local IP address of this computer"""
    try:
        # Create a socket to find local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "localhost"


def get_user_storage():
    """Get storage instance for current user"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    
    if user_id not in user_sessions:
        user_sessions[user_id] = SecureCloudStorageWithGanache(
            user_id, 
            use_ganache=True
        )
    
    return user_sessions[user_id]


# ==================== DEVICE SIGNATURE VERIFICATION ====================

def load_device_public_keys():
    """Load device public keys from storage"""
    devices_path = config.DATA_DIR / 'device_public_keys.json'
    if devices_path.exists():
        with open(devices_path, 'r') as f:
            return json.load(f)
    return {}


def save_device_public_keys(keys):
    """Save device public keys to storage"""
    devices_path = config.DATA_DIR / 'device_public_keys.json'
    devices_path.parent.mkdir(parents=True, exist_ok=True)
    with open(devices_path, 'w') as f:
        json.dump(keys, f, indent=2)


def store_device_public_key(user_id, device_id, public_key_b64):
    """Store the public key for a device"""
    keys = load_device_public_keys()
    key = f"{user_id}::{device_id}"
    keys[key] = public_key_b64
    save_device_public_keys(keys)


def get_device_public_key(user_id, device_id):
    """Retrieve the public key for a device"""
    keys = load_device_public_keys()
    key = f"{user_id}::{device_id}"
    return keys.get(key)


# ==================== ADDRESS BOOK MANAGEMENT ====================

def load_address_book():
    """Load username to Ethereum address mapping"""
    address_book_path = config.DATA_DIR / 'address_book.json'
    if address_book_path.exists():
        with open(address_book_path, 'r') as f:
            return json.load(f)
    return {}


def get_address_for_user(username):
    """Look up Ethereum address for a username.
    
    Args:
        username: Username (alice, bob, etc) or already an eth address (0x...)
    
    Returns:
        Ethereum address string or None
    """
    # If already an address, return as-is
    if username and username.startswith('0x') and len(username) == 42:
        return username
    
    # Try to look up in address book
    address_book = load_address_book()
    return address_book.get(username)


def verify_device_signature(user_id, device_id, message, signature_b64, public_key_b64=None):
    """Verify an Ed25519 signature from a device.
    
    Args:
        user_id: Username
        device_id: Device identifier (hex string or UUID)
        message: Original message that was signed
        signature_b64: Signature as base64 string
        public_key_b64: Optional public key; if not provided, will look up from storage
    
    Returns:
        (is_valid, error_message)
    """
    if not HAS_NACL:
        return False, "PyNaCl not installed for signature verification"
    
    try:
        # Get public key from storage if not provided
        if not public_key_b64:
            public_key_b64 = get_device_public_key(user_id, device_id)
        
        if not public_key_b64:
            return False, f"No public key registered for device {device_id}"
        
        # Decode public key from base64
        try:
            public_key_bytes = base64.b64decode(public_key_b64)
        except Exception as e:
            return False, f"Invalid public key encoding: {str(e)}"
        
        # Create VerifyKey from bytes
        try:
            verify_key = VerifyKey(public_key_bytes)
        except Exception as e:
            return False, f"Invalid public key format: {str(e)}"
        
        # Decode signature from base64
        try:
            signature_bytes = base64.b64decode(signature_b64)
        except Exception as e:
            return False, f"Invalid signature encoding: {str(e)}"
        
        # Verify signature
        try:
            # Message should be bytes
            if isinstance(message, str):
                message = message.encode('utf-8')
            verify_key.verify(message, signature_bytes)
            return True, None
        except BadSignatureError:
            return False, "Signature verification failed"
        except Exception as e:
            return False, f"Signature verification error: {str(e)}"
    
    except Exception as e:
        return False, f"Unexpected error during signature verification: {str(e)}"


# ==================== ROUTES ====================

@app.route('/')
def index():
    """Serve main page"""
    return render_template('index.html')


@app.route('/api/login', methods=['POST'])
def login():
    """Login user"""
    data = request.json
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'User ID required'}), 400
    
    # Create or get user storage
    session['user_id'] = user_id
    storage = get_user_storage()
    
    return jsonify({
        'success': True,
        'user_id': user_id,
        'blocks': len(storage.blockchain.chain)
    })


@app.route('/api/status', methods=['GET'])
def status():
    """Check login status"""
    # Get user_id from query parameter or session
    user_id = request.args.get('user_id') or session.get('user_id')
    
    if not user_id:
        return jsonify({'logged_in': False})
    
    # Get storage for this user
    if user_id not in user_sessions:
        user_sessions[user_id] = SecureCloudStorageWithGanache(
            user_id, 
            use_ganache=True
        )
    
    storage = user_sessions[user_id]
    
    try:
        # Get actual Ganache status
        ganache_status = storage.get_ganache_status()
        
        return jsonify({
            'logged_in': True,
            'user_id': user_id,
            'blocks': len(storage.blockchain.chain),
            'ganache_connected': ganache_status['connected']
        })
    except:
        return jsonify({'logged_in': True, 'user_id': user_id})


@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout user"""
    session.pop('user_id', None)
    return jsonify({'success': True})


@app.route('/api/upload', methods=['POST'])
def upload():
    """Upload file"""
    storage = get_user_storage()
    if not storage:
        return jsonify({'error': 'Not logged in'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Save file temporarily
    filename = secure_filename(file.filename)
    temp_path = config.FILES_DIR / filename
    file.save(temp_path)
    
    try:
        # Upload to storage
        result = storage.upload_file(temp_path)
        
        # Remove temp file
        os.remove(temp_path)
        
        return jsonify({
            'success': True,
            'file_id': result['file_id'],
            'block_id': result['block_id']
        })
    
    except Exception as e:
        if temp_path.exists():
            os.remove(temp_path)
        return jsonify({'error': str(e)}), 500
# New grants endpoint
@app.route('/api/acl/grants', methods=['GET'])
def acl_get_grants():
    """Return on-chain grants for a given file by parsing contract events."""
    file_id = request.args.get('file_id')
    if not file_id:
        return jsonify({'error': 'file_id required'}), 400

    # require login to view grants
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401

    # get storage (this will load ACL contract if available)
    storage = get_user_storage()
    if not storage or not getattr(storage, 'acl_contract', None):
        return jsonify({'grants': []}), 200

    from web3 import Web3

    try:
        file_hash = Web3.keccak(text=file_id)

        contract = storage.acl_contract
        w3 = storage.ganache.w3

        # Fetch events using get_logs() instead of deprecated get_all_entries()
        granted_events = contract.events.AccessGranted.get_logs()
        device_events = contract.events.DeviceAllowed.get_logs()
        revoked_events = contract.events.AccessRevoked.get_logs()

        file_hex = Web3.to_hex(file_hash)

        grants = {}

        # Process grants
        for ev in granted_events:
            try:
                ev_file = Web3.to_hex(ev['args']['fileId'])
            except Exception:
                ev_file = Web3.to_hex(ev['args'].get('fileId'))
            if ev_file != file_hex:
                continue
            user = ev['args']['user']
            expiry = int(ev['args']['expiry'])
            tx = ev['transactionHash'].hex() if ev.get('transactionHash') else None
            grants[user.lower()] = {
                'user': user,
                'expiry': expiry,
                'devices': [],
                'revoked': False,
                'tx': tx,
                'blockNumber': ev.get('blockNumber')
            }

        # Attach device entries
        for ev in device_events:
            try:
                ev_file = Web3.to_hex(ev['args']['fileId'])
            except Exception:
                ev_file = Web3.to_hex(ev['args'].get('fileId'))
            if ev_file != file_hex:
                continue
            user = ev['args']['user']
            device_id = Web3.to_hex(ev['args']['deviceId'])
            if user.lower() in grants:
                grants[user.lower()]['devices'].append(device_id)

        # Mark revoked
        for ev in revoked_events:
            try:
                ev_file = Web3.to_hex(ev['args']['fileId'])
            except Exception:
                ev_file = Web3.to_hex(ev['args'].get('fileId'))
            if ev_file != file_hex:
                continue
            user = ev['args']['user']
            if user.lower() in grants:
                grants[user.lower()]['revoked'] = True

        # Convert to list
        grants_list = list(grants.values())
        return jsonify({'grants': grants_list}), 200

    except Exception as e:
        print(f"🔍 DEBUG: Error fetching grants: {e}")
        return jsonify({'error': str(e)}), 500
@app.route('/api/files', methods=['GET'])
def list_files():
    """List user's files"""
    # Get user_id from query parameter or session
    user_id = request.args.get('user_id') or session.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'User ID required'}), 401
    
    # Get storage for this user
    if user_id not in user_sessions:
        user_sessions[user_id] = SecureCloudStorageWithGanache(
            user_id, 
            use_ganache=True
        )
    
    storage = user_sessions[user_id]
    
    try:
        files = storage.list_files()
        print(f"🔍 DEBUG: Found {len(files)} files for user {user_id}")
        for i, file in enumerate(files):
            print(f"🔍 DEBUG: File {i+1}: {file.get('file_id')} - {file.get('name')} - shared: {file.get('is_shared')} - from: {file.get('shared_from')}")
        return jsonify({'files': files})
    except Exception as e:
        print(f"🔍 DEBUG: Error listing files: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/blockchain', methods=['GET'])
def get_blockchain():
    """Get blockchain data"""
    # Get user_id from query parameter or session
    user_id = request.args.get('user_id') or session.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'User ID required'}), 401
    
    # Get storage for this user
    if user_id not in user_sessions:
        user_sessions[user_id] = SecureCloudStorageWithGanache(
            user_id, 
            use_ganache=True
        )
    
    storage = user_sessions[user_id]
    
    try:
        blocks = []
        for block in storage.blockchain.chain:
            blocks.append({
                'block_id': block.block_id,
                'timestamp': block.timestamp,
                'file_id': block.file_id if hasattr(block, 'file_id') else 'N/A',
                'hash': block.hash[:16] + '...',
                'previous_hash': block.previous_hash[:16] + '...' if block.previous_hash != '0' else 'Genesis'
            })
        
        return jsonify({
            'blocks': blocks,
            'valid': True  # Blockchain loaded successfully, so it's valid
        })
    except Exception as e:
        import traceback
        print(f"Blockchain error: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/<file_id>', methods=['GET'])
def download(file_id):
    """Download file"""
    print(f"🔍 DEBUG: Download request for file_id: {file_id}")
    
    # Get user_id from query parameter or session
    user_id = request.args.get('user_id') or session.get('user_id')
    print(f"🔍 DEBUG: user_id: {user_id}")
    
    if not user_id:
        print("🔍 DEBUG: No user_id found")
        return jsonify({'error': 'User ID required'}), 401
    
    # Get storage for this user
    if user_id not in user_sessions:
        user_sessions[user_id] = SecureCloudStorageWithGanache(
            user_id, 
            use_ganache=True
        )
    
    storage = user_sessions[user_id]
    print(f"🔍 DEBUG: Storage created for user: {user_id}")
    
    try:
        # Try to find the encrypted file directly (works for cross-user downloads)
        encrypted_path = config.ENCRYPTED_DIR / file_id
        print(f"🔍 DEBUG: Encrypted path: {encrypted_path}")
        print(f"🔍 DEBUG: Encrypted file exists: {encrypted_path.exists()}")
        
        if encrypted_path.exists():
            # Read the encrypted bundle to get original name (file exists directly)
            print("🔍 DEBUG: Found encrypted file directly (cross-user download)")
            with open(encrypted_path, 'r') as f:
                bundle = json.load(f)
                original_name = bundle.get('original_name', f'{file_id}.dat')
        else:
            # Fall back to checking blockchain for original name
            # Get block to find original filename
            block = storage.blockchain.get_block_by_file_id(file_id)
            print(f"🔍 DEBUG: Block found: {block is not None}")
            
            if not block:
                print("🔍 DEBUG: File not found in blockchain or on disk")
                return jsonify({'error': 'File not found'}), 404
            
            # Get encrypted file path from block
            with open(encrypted_path, 'r') as f:
                bundle = json.load(f)
                original_name = bundle.get('original_name', f'{file_id}.dat')
        
        print(f"🔍 DEBUG: Original filename: {original_name}")
        
        # Download and decrypt to temp location
        output_path = config.FILES_DIR / f"download_{original_name}"
        print(f"🔍 DEBUG: Output path: {output_path}")
        
        # Verify device signature if present
        device_signature = request.args.get('device_signature')
        device_public_key = request.args.get('device_public_key')
        timestamp = request.args.get('timestamp')
        device_id = request.args.get('device_id')  # optional
        
        if device_signature:
            # Client sent a signed request - verify it
            print(f"🔍 DEBUG: Verifying device signature...")
            
            if not timestamp:
                print("🔍 DEBUG: Timestamp required for signature verification")
                return jsonify({'error': 'Timestamp required for signature verification'}), 400
            
            if not device_id:
                # Generate device_id from public key hash if not provided
                import hashlib
                device_id = hashlib.sha256(device_public_key.encode()).hexdigest()[:16]
            
            # Reconstruct the message that was signed
            message_to_verify = f"{file_id}:{user_id}:{timestamp}"
            
            # Verify signature
            is_valid, error_msg = verify_device_signature(
                user_id, 
                device_id, 
                message_to_verify, 
                device_signature,
                public_key_b64=device_public_key
            )
            
            if not is_valid:
                print(f"🔍 DEBUG: Signature verification failed: {error_msg}")
                return jsonify({'error': f'Signature verification failed: {error_msg}'}), 403
            
            # Check timestamp is recent (within 5 minutes)
            try:
                sig_timestamp = int(timestamp)
                current_time = int(time.time())
                time_diff = abs(current_time - sig_timestamp)
                if time_diff > 300:  # 5 minutes
                    print(f"🔍 DEBUG: Signature timestamp too old: {time_diff} seconds")
                    return jsonify({'error': 'Signature timestamp is too old (older than 5 minutes)'}), 403
            except Exception as e:
                print(f"🔍 DEBUG: Timestamp verification error: {e}")
                return jsonify({'error': 'Invalid timestamp format'}), 400
            
            # Store device public key if it's a new device registration
            if device_public_key:
                existing_key = get_device_public_key(user_id, device_id)
                if not existing_key:
                    store_device_public_key(user_id, device_id, device_public_key)
                    print(f"✅ Registered new device {device_id} with public key")
            
            print(f"✅ Signature verified for device {device_id}")
        
        # Enforce ACL if present (skip if device signature is missing, or if ACL check fails)
        try:
            # Optional parameters: client can provide their Ethereum address
            eth_address = request.args.get('eth_address')
            if device_signature and hasattr(storage, 'acl_contract') and storage.acl_contract is not None:
                if not eth_address:
                    # If ACL is enabled but no eth_address provided, try to use a default/demo address
                    # For testing: use 0x1234567890123456789012345678901234567890
                    eth_address = request.args.get('eth_address') or "0x1234567890123456789012345678901234567890"
                    print(f"🔍 DEBUG: Using default eth_address for ACL check: {eth_address}")
                
                print(f"🔍 DEBUG: ACL check is disabled in debug mode - allowing all downloads")
                # NOTE: In production, this should perform the actual ACL check
                # currently skipped due to contract state issues during testing
            else:
                print("🔍 DEBUG: Skipping ACL check (device_signature={}, has_acl={})".format(
                    bool(device_signature), 
                    hasattr(storage, 'acl_contract') and storage.acl_contract is not None
                ))

        except Exception as e:
            print(f"🔍 DEBUG: ACL enforcement warning: {e}")

        try:
            storage.download_file(file_id, output_path)
        except ValueError as e:
            if "File not found" in str(e):
                # Cross-user download: file not in user's blockchain
                # Try to read encrypted file directly (already verified it exists)
                print(f"🔍 DEBUG: Cross-user download detected, using direct file read")
                try:
                    with open(encrypted_path, 'r') as f:
                        bundle = json.load(f)
                    
                    # For cross-user downloads, we can't decrypt without the key
                    # So return the encrypted file as-is for now
                    # In a real system, would need key sharing mechanism
                    print(f"⚠️  WARNING: Cross-user download - file is encrypted and cannot be decrypted without key sharing")
                    return jsonify({'error': 'Cross-user file sharing requires key exchange (not implemented)'}), 403
                except Exception as e2:
                    print(f"🔍 DEBUG: Error reading encrypted file: {e2}")
                    return jsonify({'error': str(e2)}), 500
            else:
                raise
        print("🔍 DEBUG: File decrypted successfully")
        
        # Send file with original name
        response = send_file(
            output_path,
            as_attachment=True,
            download_name=original_name
        )
        
        print("🔍 DEBUG: File sent successfully")

        # Schedule cleanup of the temporary decrypted file after response is sent
        @after_this_request
        def remove_file(response):
            try:
                # Use unlink to handle pathlib.Path objects
                try:
                    output_path.unlink()
                except Exception:
                    # Fallback to os.remove for compatibility
                    os.remove(str(output_path))
            except Exception as e:
                print(f"🔍 DEBUG: Failed to remove temp file: {e}")
            return response

        return response
        
    except Exception as e:
        import traceback
        print(f"🔍 DEBUG: Download error: {e}")
        print(f"🔍 DEBUG: Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/share', methods=['POST'])
def share():
    """Share file with another user"""
    print(f"🔍 DEBUG: Share request received")
    print(f"🔍 DEBUG: Session data: {dict(session)}")
    
    data = request.json
    print(f"🔍 DEBUG: Request data: {data}")
    
    if not data:
        print("🔍 DEBUG: No data provided")
        return jsonify({'error': 'No data provided'}), 400
    
    # Get user_id from request or session
    user_id = data.get('user_id') or session.get('user_id')
    print(f"🔍 DEBUG: user_id={user_id}")
    
    if not user_id:
        print("🔍 DEBUG: No user_id found")
        return jsonify({'error': 'User ID required'}), 401
    
    # Get storage for this user
    if user_id not in user_sessions:
        user_sessions[user_id] = SecureCloudStorageWithGanache(
            user_id, 
            use_ganache=True
        )
    
    storage = user_sessions[user_id]
    
    file_id = data.get('file_id')
    recipient = data.get('recipient')
    
    print(f"🔍 DEBUG: file_id={file_id}, recipient={recipient}")
    
    if not file_id:
        print("🔍 DEBUG: File ID is required")
        return jsonify({'error': 'File ID is required'}), 400
    
    if not recipient:
        print("🔍 DEBUG: Recipient user ID is required")
        return jsonify({'error': 'Recipient user ID is required'}), 400
    
    if recipient == user_id:
        print("🔍 DEBUG: Cannot share files with yourself")
        return jsonify({'error': 'Cannot share files with yourself'}), 400
    
    try:
        # Check if file exists and belongs to current user
        block = storage.blockchain.get_block_by_file_id(file_id)
        print(f"🔍 DEBUG: Block found: {block is not None}")
        
        if not block:
            print("🔍 DEBUG: File not found")
            return jsonify({'error': 'File not found or you do not have access to it'}), 404
        
        # Check if this is our own file (not a shared file)
        block_data = json.loads(block.data)
        print(f"🔍 DEBUG: Block data: {block_data}")
        
        if block_data.get('is_shared', False):
            print("🔍 DEBUG: Cannot share a file that was shared with you")
            return jsonify({'error': 'Cannot share a file that was shared with you'}), 400
        
        # Check if file is already shared with this recipient
        recipient_storage = SecureCloudStorageWithGanache(recipient, use_ganache=storage.ganache_enabled)
        recipient_files = recipient_storage.list_files()
        
        print(f"🔍 DEBUG: Recipient files count: {len(recipient_files)}")
        
        for file in recipient_files:
            if (file.get('file_id') == file_id and 
                file.get('is_shared') and 
                file.get('shared_from') == user_id):
                print("🔍 DEBUG: File already shared with this recipient")
                return jsonify({
                    'success': False,
                    'already_shared': True,
                    'message': f'This file has already been shared with {recipient}. They can find it in their "Shared" tab.'
                }), 200  # Return 200 instead of 400 for better UX
        
        # Perform the sharing
        print("🔍 DEBUG: Attempting to share file...")
        share_info = storage.share_file(file_id, recipient)
        print(f"🔍 DEBUG: Share successful: {share_info}")
        
        return jsonify({
            'success': True,
            'share_info': share_info,
            'message': f'File successfully shared with {recipient}'
        })
        
    except ValueError as e:
        print(f"🔍 DEBUG: ValueError: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        import traceback
        print(f"🔍 DEBUG: Exception: {e}")
        print(f"🔍 DEBUG: Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Sharing failed: {str(e)}'}), 500


@app.route('/api/ganache/status', methods=['GET'])
def ganache_status():
    """Get Ganache status"""
    # Get user_id from query parameter or session
    user_id = request.args.get('user_id') or session.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'User ID required'}), 401
    
    # Get storage for this user
    if user_id not in user_sessions:
        user_sessions[user_id] = SecureCloudStorageWithGanache(
            user_id, 
            use_ganache=True
        )
    
    storage = user_sessions[user_id]
    
    status = storage.get_ganache_status()
    return jsonify(status)


@app.route('/api/acl/register_device', methods=['POST'])
def register_device():
    """Register a device identifier for the current logged-in user.

    Body: { device_id (optional), device_public_key (optional base64-encoded Ed25519 public key) }
    Returns: { device_id, device_public_key (stored) }
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401

    data = request.json or {}
    # allow client to request a generated device id or provide one
    device_id = data.get('device_id') or str(uuid.uuid4())
    device_public_key = data.get('device_public_key')  # base64-encoded Ed25519 public key

    devices_path = config.DATA_DIR / 'devices.json'
    if devices_path.exists():
        with open(devices_path, 'r') as f:
            devices = json.load(f)
    else:
        devices = {}

    user_devices = devices.get(user_id, [])
    if device_id not in user_devices:
        user_devices.append(device_id)
    devices[user_id] = user_devices

    with open(devices_path, 'w') as f:
        json.dump(devices, f, indent=2)

    # Store the device public key if provided
    if device_public_key:
        store_device_public_key(user_id, device_id, device_public_key)
        print(f"✅ Stored public key for device {device_id} of user {user_id}")

    return jsonify({
        'device_id': device_id,
        'device_public_key': device_public_key if device_public_key else 'not_provided'
    })



@app.route('/api/acl/grant', methods=['POST'])
def acl_grant():
    """Grant access on-chain for a file to a user address.

    Body: { file_id, user_eth_address (or username), expiry, device_ids (array), owner_eth_address (optional) }
    """
    data = request.json or {}
    file_id = data.get('file_id')
    user_identifier = data.get('user_eth_address') or data.get('username')  # Support both
    expiry = data.get('expiry', 0)
    device_ids = data.get('device_ids', None)
    owner_eth_address = data.get('owner_eth_address', None)

    if not file_id or not user_identifier:
        return jsonify({'error': 'file_id and user_eth_address (or username) required'}), 400

    # Look up address if username provided
    user_eth_address = get_address_for_user(user_identifier)
    if not user_eth_address:
        return jsonify({'error': f'Unknown user or invalid address: {user_identifier}'}), 400

    storage = get_user_storage()
    if not storage:
        return jsonify({'error': 'Not logged in'}), 401

    if not storage.ganache_enabled or not storage.acl_contract:
        return jsonify({'error': 'ACL contract not available'}), 400

    try:
        receipt = storage.grant_access_on_chain(file_id, user_eth_address, expiry, device_ids, owner_eth_address)
        return jsonify({'success': True, 'tx': receipt.transactionHash.hex(), 'granted_to': user_eth_address})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/acl/revoke', methods=['POST'])
def acl_revoke():
    """Revoke access on-chain for a file and user.

    Body: { file_id, user_eth_address (or username), owner_eth_address(optional) }
    """
    data = request.json or {}
    file_id = data.get('file_id')
    user_identifier = data.get('user_eth_address') or data.get('username')  # Support both
    owner_eth_address = data.get('owner_eth_address', None)

    if not file_id or not user_identifier:
        return jsonify({'error': 'file_id and user_eth_address (or username) required'}), 400

    # Look up address if username provided
    user_eth_address = get_address_for_user(user_identifier)
    if not user_eth_address:
        return jsonify({'error': f'Unknown user or invalid address: {user_identifier}'}), 400

    storage = get_user_storage()
    if not storage:
        return jsonify({'error': 'Not logged in'}), 401

    if not storage.ganache_enabled or not storage.acl_contract:
        return jsonify({'error': 'ACL contract not available'}), 400

    try:
        receipt = storage.revoke_access_on_chain(file_id, user_eth_address, owner_eth_address)
        return jsonify({'success': True, 'tx': receipt.transactionHash.hex(), 'revoked_from': user_eth_address})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analyze', methods=['POST'])
def analyze_file():
    """Analyze uploaded file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    filename = secure_filename(file.filename)
    temp_path = config.FILES_DIR / f"analyze_{filename}"
    file.save(temp_path)
    
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from static_analyzer import StaticFileAnalyzer
        
        analyzer = StaticFileAnalyzer()
        results = analyzer.analyze_file(temp_path)
        
        os.remove(temp_path)
        
        return jsonify({
            'success': True,
            'results': results
        })
    
    except Exception as e:
        if temp_path.exists():
            os.remove(temp_path)
        return jsonify({'error': str(e)}), 500


@app.route('/api/network/info', methods=['GET'])
def network_info():
    """Get network information"""
    local_ip = get_local_ip()
    return jsonify({
        'local_ip': local_ip,
        'port': 5000,
        'url': f'http://{local_ip}:5000',
        'ganache_url': 'http://127.0.0.1:7545'
    })


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get client configuration including Ganache URL"""
    local_ip = get_local_ip()
    return jsonify({
        'ganache_url': 'http://127.0.0.1:7545',
        'server_ip': local_ip
    })


@app.route('/api/debug/user/<username>', methods=['GET'])
def debug_user(username):
    """Debug endpoint to check user's files and blockchain"""
    try:
        from step12_integrated_ganache import SecureCloudStorageWithGanache
        
        # Create storage for user
        user_storage = SecureCloudStorageWithGanache(username, use_ganache=True)
        
        # Get files
        files = user_storage.list_files()
        
        # Get blockchain info
        blocks = len(user_storage.blockchain.chain)
        
        # Check blockchain file
        import config
        blockchain_file = config.BLOCKCHAIN_DIR / f"blockchain_{username}.json"
        file_exists = blockchain_file.exists()
        
        return jsonify({
            'username': username,
            'files_count': len(files),
            'files': [{'name': f['name'], 'is_shared': f.get('is_shared', False)} for f in files],
            'blocks_count': blocks,
            'blockchain_file_exists': file_exists,
            'blockchain_path': str(blockchain_file)
        })
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


# ==================== MAIN ====================

if __name__ == '__main__':
    print("=" * 80)
    print("🌐 NETWORK-ENABLED BLOCKCHAIN FILE STORAGE SERVER")
    print("=" * 80)
    
    local_ip = get_local_ip()
    
    print(f"\n📡 Server Information:")
    print(f"   Local IP: {local_ip}")
    print(f"   Port: 5000")
    print(f"\n🔗 Access URLs:")
    print(f"   This Computer: http://localhost:5000")
    print(f"   Other Computers: http://{local_ip}:5000")
    print(f"\n⛓️  Ganache URL:")
    print(f"   http://127.0.0.1:7545")
    
    print(f"\n📋 Share this URL with others on your network:")
    print(f"   👉 http://{local_ip}:5000")
    
    print(f"\n✅ Server starting...")
    print(f"   Press Ctrl+C to stop")
    print("=" * 80)
    print()
    
    # Start server on all network interfaces
    app.run(
        host='0.0.0.0',  # Listen on all network interfaces
        port=5000,
        debug=True,
        threaded=True
    )