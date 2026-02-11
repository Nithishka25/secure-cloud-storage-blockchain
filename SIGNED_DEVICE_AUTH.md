# Signed Device Authentication Implementation

## Overview

This document describes the **Ed25519 Signed Device Authentication** feature added to the Smart Contract-Driven Access Control system. This feature cryptographically binds file downloads to specific registered devices, providing an additional layer of security beyond ACL enforcement.

## Architecture

### Components

1. **Frontend (JavaScript)**
   - TweetSodium library for Ed25519 operations in the browser
   - `DeviceCrypto` module for managing device keypairs
   - Device public key registration during device setup
   - Request signing on every download

2. **Backend (Python/Flask)**
   - PyNaCl library for Ed25519 signature verification
   - Device public key storage (JSON file)
   - Signature verification before ACL enforcement
   - Timestamp validation to prevent replay attacks

3. **Smart Contract**
   - ACL checks (existing) - validates user has access
   - Device restrictions (existing) - validates device is allowed
   - Signature verification (new) - validates device identity

## How It Works

### Device Registration Flow

1. User clicks "Register Device"
2. Browser generates Ed25519 keypair (using TweetSodium)
3. Keypair is stored in browser localStorage for persistence
4. Device ID and public key are sent to server
5. Server stores mapping: `user_id::device_id -> public_key_b64`

### Download Request Flow

1. User clicks "Download File"
2. Browser creates message: `file_id:user_id:timestamp`
3. Message is signed with device private key (stored in localStorage)
4. Request includes:
   - File ID (URL path)
   - User ID (query param)
   - Device signature (base64 encoded)
   - Device public key (base64 encoded)
   - Timestamp (Unix seconds)

5. Server receives request and:
   - Verifies timestamp is recent (< 5 minutes old)
   - Reconstructs original message
   - Verifies signature using provided public key
   - Checks device ACL restrictions
   - Decrypts and returns file

## Security Properties

### What This Protects

- **Device-Binding**: Only the device holding the private key can sign valid requests
- **Replay Attack Prevention**: Timestamp validation prevents reusing old signatures
- **Message Integrity**: Signature proves the exact file_id and timestamp were signed
- **Per-Device Access Control**: Different devices can have different access levels

### What This Does NOT Protect

- **Key Storage**: Private key is stored in browser localStorage (vulnerable to XSS)
- **Post-Download**: Once downloaded, the plaintext file is not controlled
- **Transport Security**: Requires HTTPS in production (not enforced in demo)
- **Hardware Binding**: Not tied to actual hardware, only to browser storage

## API Changes

### POST /api/acl/register_device

```json
Request Body:
{
  "device_id": "device_alice_1234567890",
  "device_public_key": "base64_encoded_ed25519_public_key"
}

Response:
{
  "device_id": "device_alice_1234567890",
  "device_public_key": "base64_encoded_ed25519_public_key"
}
```

### GET /api/download/<file_id>

Additional query parameters for signed authentication:

- `device_signature` - Base64-encoded Ed25519 signature
- `device_public_key` - Base64-encoded public key (for new devices)
- `timestamp` - Unix timestamp (seconds) when message was signed
- `user_id` - Username (same as message)

Example:

```
GET /api/download/file_abc123?
  user_id=alice&
  device_signature=base64_signature&
  device_public_key=base64_pubkey&
  timestamp=1770474900
```

## File Structure

### Frontend

- `templates/index.html` - Register Device modal added
- `static/app.js` - `DeviceCrypto` module, updated `downloadFile()` and `confirmRegisterDevice()`

### Backend

- `step15_network_server.py` - Added signature verification functions, updated endpoints
- `data/device_public_keys.json` - Storage for device public keys (created on first use)

### Test & Demo

- `test_signed_auth_fixed.py` - Integration tests (all passing)
- `demo_signed_device_auth.py` - Full workflow demonstration

## Implementation Details

### Server-Side Signature Verification

```python
def verify_device_signature(user_id, device_id, message, signature_b64, public_key_b64=None):
    """
    Verifies an Ed25519 signature.

    Returns:
        (is_valid, error_message) tuple
    """
    # 1. Decode public key from base64
    public_key_bytes = base64.b64decode(public_key_b64)
    verify_key = VerifyKey(public_key_bytes)

    # 2. Decode signature from base64
    signature_bytes = base64.b64decode(signature_b64)

    # 3. Verify signature
    verify_key.verify(message.encode('utf-8'), signature_bytes)
```

### Timestamp Validation

```python
# Allow signatures up to 5 minutes old
time_diff = abs(current_time - sig_timestamp)
if time_diff > 300:  # 5 minutes
    return error("Signature timestamp is too old")
```

### Message Format

The message that must be signed is:

```
{file_id}:{user_id}:{timestamp}
```

Example:

```
abc123xyz:alice:1770474900
```

## Usage

### Register a Device (Frontend)

```javascript
// Generated automatically on first interaction
const keyPair = await DeviceCrypto.getOrGenerateKeyPair();
const publicKeyB64 = DeviceCrypto.publicKeyB64(keyPair.publicKey);

// Send to server
const response = await fetch("/api/acl/register_device", {
  method: "POST",
  body: JSON.stringify({
    device_id: "my_device_id",
    device_public_key: publicKeyB64,
  }),
});
```

### Sign Download Request (Frontend)

```javascript
// Automatically done in downloadFile()
const timestamp = Math.floor(Date.now() / 1000);
const message = `${fileId}:${currentUserId}:${timestamp}`;
const signature = DeviceCrypto.sign(message, keyPair.secretKey);
const signatureB64 = btoa(String.fromCharCode(...signature));

// Include in download URL
window.location.href =
  `/api/download/${fileId}?` +
  `user_id=${userId}&` +
  `device_signature=${signatureB64}&` +
  `device_public_key=${publicKeyB64}&` +
  `timestamp=${timestamp}`;
```

## Testing

Run the integration tests:

```bash
# Make sure server is running and Ganache is deployed
python test_signed_auth_fixed.py
```

Expected output:

- TEST 1 PASSED: Device registration and key storage
- TEST 2 PASSED: Signature verification
- TEST 3 PASSED: API endpoints available

Run the full workflow demo:

```bash
python demo_signed_device_auth.py
```

## Limitations & Future Improvements

### Current Limitations

1. **XSS Vulnerability**: Private key in localStorage is accessible to XSS attacks
2. **No Hardware Binding**: Tied to browser, not to specific hardware
3. **No Rate Limiting**: No protection against brute-force signature attempts
4. **Manual Timestamp**: Relies on client clock synchronization

### Future Enhancements

1. **WebAuthn/FIDO2**: Use platform authenticator for hardware-bound key storage
2. **Server-Side Key Derivation**: Derive device keys server-side instead of client-generated
3. **Certificate Pinning**: Pin expected public keys per device
4. **Rate Limiting**: Limit download attempts per signature
5. **Revocation Lists**: Server-maintained list of revoked devices
6. **Key Rotation**: Periodic key rotation with old key deprecation

## Troubleshooting

### "Signature verification failed"

- Check timestamp is within 5 minutes of current time
- Verify message format is: `fileId:userId:timestamp`
- Ensure public key matches the private key used to sign

### "No public key registered for device"

- Register device first with `/api/acl/register_device`
- Check `data/device_public_keys.json` for stored keys
- Verify `user_id::device_id` mapping exists

### "Signature timestamp too old"

- Signatures older than 5 minutes are rejected
- Request must be made immediately after signing
- Check client and server clock are synchronized

## Performance Considerations

- **Signature Generation**: ~1-2ms per signature (minimal impact)
- **Signature Verification**: ~1-2ms per verification (minimal impact)
- **Key Storage**: ~100 bytes per device public key
- **Network**: Adds ~100 bytes to request URL (public key + signature + timestamp)

## References

- Ed25519: https://en.wikipedia.org/wiki/EdDSA
- PyNaCl: https://pynacl.readthedocs.io/
- TweetSodium: https://github.com/dchest/tweetsodium
- NaCl Signing: https://nacl.cr.yp.to/sign.html
