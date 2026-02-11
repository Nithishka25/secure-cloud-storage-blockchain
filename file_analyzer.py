"""
Real-Time File Analysis and Algorithm Comparison
=================================================

This module analyzes uploaded files and compares encryption algorithms
in real-time, generating:
1. Original file histogram
2. Encrypted histograms (Traditional AES, Dynamic AES, CHACHA20)
3. Performance metrics (sensitivity, entropy, time)
4. Visual comparison charts
"""

import numpy as np
import hashlib
import time
import json
from pathlib import Path
from collections import Counter
import base64

from Crypto.Cipher import AES, ChaCha20
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

import config


class FileAnalyzer:
    """Analyzes and compares encryption algorithms on uploaded files"""
    
    def __init__(self):
        self.results = {}
    
    def analyze_file(self, file_path):
        """
        Complete analysis of a file with all three algorithms
        
        Args:
            file_path: Path to file to analyze
            
        Returns:
            dict: Complete analysis results with histograms and metrics
        """
        print(f"\n📊 Starting real-time analysis of: {file_path}")
        print("=" * 80)
        
        # Read file
        with open(file_path, 'rb') as f:
            original_data = f.read()
        
        file_size = len(original_data)
        print(f"File size: {file_size} bytes")
        
        # Analyze original file
        print("\n1️⃣ Analyzing original file...")
        original_histogram = self._calculate_histogram(original_data)
        original_entropy = self._calculate_entropy(original_data)
        original_sensitivity = self._calculate_sensitivity(original_data)
        
        # Encrypt and analyze with Traditional AES
        print("2️⃣ Encrypting with Traditional AES...")
        traditional_start = time.time()
        traditional_encrypted, traditional_key = self._encrypt_traditional_aes(original_data)
        traditional_time = time.time() - traditional_start
        
        traditional_histogram = self._calculate_histogram(traditional_encrypted)
        traditional_entropy = self._calculate_entropy(traditional_encrypted)
        traditional_sensitivity = self._calculate_sensitivity(traditional_encrypted)
        
        # Encrypt and analyze with Dynamic AES (Proposed)
        print("3️⃣ Encrypting with Dynamic AES (Proposed)...")
        dynamic_start = time.time()
        dynamic_encrypted, dynamic_key = self._encrypt_dynamic_aes(original_data)
        dynamic_time = time.time() - dynamic_start
        
        dynamic_histogram = self._calculate_histogram(dynamic_encrypted)
        dynamic_entropy = self._calculate_entropy(dynamic_encrypted)
        dynamic_sensitivity = self._calculate_sensitivity(dynamic_encrypted)
        
        # Encrypt and analyze with CHACHA20
        print("4️⃣ Encrypting with CHACHA20...")
        chacha_start = time.time()
        chacha_encrypted, chacha_key = self._encrypt_chacha20(original_data)
        chacha_time = time.time() - chacha_start
        
        chacha_histogram = self._calculate_histogram(chacha_encrypted)
        chacha_entropy = self._calculate_entropy(chacha_encrypted)
        chacha_sensitivity = self._calculate_sensitivity(chacha_encrypted)
        
        # Compile results
        results = {
            'file_name': Path(file_path).name,
            'file_size': file_size,
            'original': {
                'histogram': original_histogram,
                'entropy': original_entropy,
                'sensitivity': original_sensitivity,
                'data_preview': base64.b64encode(original_data[:100]).decode()
            },
            'traditional_aes': {
                'histogram': traditional_histogram,
                'entropy': traditional_entropy,
                'sensitivity': traditional_sensitivity,
                'encryption_time': traditional_time,
                'data_preview': base64.b64encode(traditional_encrypted[:100]).decode()
            },
            'dynamic_aes': {
                'histogram': dynamic_histogram,
                'entropy': dynamic_entropy,
                'sensitivity': dynamic_sensitivity,
                'encryption_time': dynamic_time,
                'data_preview': base64.b64encode(dynamic_encrypted[:100]).decode()
            },
            'chacha20': {
                'histogram': chacha_histogram,
                'entropy': chacha_entropy,
                'sensitivity': chacha_sensitivity,
                'encryption_time': chacha_time,
                'data_preview': base64.b64encode(chacha_encrypted[:100]).decode()
            },
            'comparison': self._generate_comparison(
                traditional_sensitivity, traditional_entropy, traditional_time,
                dynamic_sensitivity, dynamic_entropy, dynamic_time,
                chacha_sensitivity, chacha_entropy, chacha_time
            )
        }
        
        print("\n✅ Analysis complete!")
        print("=" * 80)
        
        return results
    
    def _calculate_histogram(self, data):
        """Calculate byte value distribution (0-255)"""
        # Count frequency of each byte value
        byte_counts = Counter(data)
        
        # Create histogram with all 256 possible byte values
        histogram = [byte_counts.get(i, 0) for i in range(256)]
        
        return histogram
    
    def _calculate_entropy(self, data):
        """
        Calculate Shannon entropy
        Higher entropy = more random = better encryption
        """
        if len(data) == 0:
            return 0
        
        # Count byte frequencies
        byte_counts = Counter(data)
        total_bytes = len(data)
        
        # Calculate entropy
        entropy = 0
        for count in byte_counts.values():
            if count > 0:
                probability = count / total_bytes
                entropy -= probability * np.log2(probability)
        
        return entropy
    
    def _calculate_sensitivity(self, data):
        """
        Calculate bit density (proportion of 1s in binary)
        Ideal is 0.5 (50%) for perfect randomness
        """
        # Convert to binary string
        binary_str = ''.join(format(byte, '08b') for byte in data)
        
        # Count 1s
        ones_count = binary_str.count('1')
        total_bits = len(binary_str)
        
        # Calculate sensitivity (bit density)
        sensitivity = ones_count / total_bits if total_bits > 0 else 0
        
        return sensitivity
    
    def _encrypt_traditional_aes(self, data):
        """Traditional AES-256-CBC encryption with static key"""
        # Generate a random key (simulating centralized key)
        key = get_random_bytes(32)  # 256 bits
        
        # Create cipher
        cipher = AES.new(key, AES.MODE_CBC)
        
        # Pad data to block size
        padded_data = pad(data, AES.block_size)
        
        # Encrypt
        encrypted = cipher.encrypt(padded_data)
        
        # Combine IV and encrypted data
        result = cipher.iv + encrypted
        
        return result, key
    
    def _encrypt_dynamic_aes(self, data):
        """
        Dynamic AES encryption (your proposed algorithm)
        Key = hash(file) XOR hash(blockchain_block)
        """
        # Calculate file hash
        file_hash = hashlib.sha256(data).digest()
        
        # Simulate blockchain block hash
        # In real system, this comes from latest blockchain block
        block_data = f"block_{time.time()}_{len(data)}".encode()
        block_hash = hashlib.sha256(block_data).digest()
        
        # Dynamic key generation: XOR of hashes
        dynamic_key = bytes(a ^ b for a, b in zip(file_hash, block_hash))
        
        # Create cipher with dynamic key
        cipher = AES.new(dynamic_key, AES.MODE_GCM)
        
        # Encrypt (GCM mode, more secure)
        encrypted, tag = cipher.encrypt_and_digest(data)
        
        # Combine nonce, tag, and encrypted data
        result = cipher.nonce + tag + encrypted
        
        return result, dynamic_key
    
    def _encrypt_chacha20(self, data):
        """
        CHACHA20 stream cipher encryption
        
        Note: In this Python implementation using PyCryptodome, ChaCha20 may
        appear slower than AES because:
        1. AES benefits from CPU hardware acceleration (AES-NI)
        2. ChaCha20 is pure software implementation
        
        In practice (real-world scenarios):
        - On mobile/IoT: ChaCha20 is faster (no AES-NI hardware)
        - On servers with AES-NI: AES is faster
        - On ARM processors: ChaCha20 is faster
        
        This benchmark shows software-only performance.
        """
        # Generate random key
        key = get_random_bytes(32)  # 256 bits
        
        # Create cipher
        cipher = ChaCha20.new(key=key)
        
        # Encrypt
        encrypted = cipher.encrypt(data)
        
        # Combine nonce and encrypted data
        result = cipher.nonce + encrypted
        
        return result, key
    
    def _generate_comparison(self, trad_sens, trad_ent, trad_time,
                            dyn_sens, dyn_ent, dyn_time,
                            cha_sens, cha_ent, cha_time):
        """Generate comparison metrics"""
        
        # Calculate improvements
        sens_improvement = ((dyn_sens - trad_sens) / trad_sens) * 100
        time_improvement = ((trad_time - dyn_time) / trad_time) * 100
        ent_improvement = ((dyn_ent - trad_ent) / trad_ent) * 100
        
        return {
            'sensitivity': {
                'traditional': trad_sens,
                'dynamic': dyn_sens,
                'chacha20': cha_sens,
                'improvement': sens_improvement
            },
            'entropy': {
                'traditional': trad_ent,
                'dynamic': dyn_ent,
                'chacha20': cha_ent,
                'improvement': ent_improvement
            },
            'speed': {
                'traditional': trad_time,
                'dynamic': dyn_time,
                'chacha20': cha_time,
                'improvement': time_improvement
            },
            'winner': {
                'security': 'Dynamic AES' if dyn_sens > trad_sens else 'Traditional AES',
                'speed': 'CHACHA20' if cha_time < dyn_time else 'Dynamic AES'
            }
        }


# Test function
if __name__ == "__main__":
    print("=" * 80)
    print("REAL-TIME FILE ANALYSIS AND COMPARISON")
    print("=" * 80)
    
    # Create test file
    test_file = config.FILES_DIR / "analysis_test.txt"
    with open(test_file, 'wb') as f:
        # Create some data with patterns (not fully random)
        data = b"Hello World! " * 100
        data += bytes(range(256)) * 10
        f.write(data)
    
    # Analyze
    analyzer = FileAnalyzer()
    results = analyzer.analyze_file(test_file)
    
    # Print results
    print("\n📊 ANALYSIS RESULTS")
    print("=" * 80)
    print(f"File: {results['file_name']}")
    print(f"Size: {results['file_size']} bytes")
    
    print("\n📈 ORIGINAL FILE:")
    print(f"  Entropy: {results['original']['entropy']:.4f}")
    print(f"  Sensitivity: {results['original']['sensitivity']:.4f} ({results['original']['sensitivity']*100:.2f}%)")
    
    print("\n🔒 TRADITIONAL AES:")
    print(f"  Entropy: {results['traditional_aes']['entropy']:.4f}")
    print(f"  Sensitivity: {results['traditional_aes']['sensitivity']:.4f} ({results['traditional_aes']['sensitivity']*100:.2f}%)")
    print(f"  Time: {results['traditional_aes']['encryption_time']:.6f}s")
    
    print("\n⭐ DYNAMIC AES (PROPOSED):")
    print(f"  Entropy: {results['dynamic_aes']['entropy']:.4f}")
    print(f"  Sensitivity: {results['dynamic_aes']['sensitivity']:.4f} ({results['dynamic_aes']['sensitivity']*100:.2f}%)")
    print(f"  Time: {results['dynamic_aes']['encryption_time']:.6f}s")
    
    print("\n⚡ CHACHA20:")
    print(f"  Entropy: {results['chacha20']['entropy']:.4f}")
    print(f"  Sensitivity: {results['chacha20']['sensitivity']:.4f} ({results['chacha20']['sensitivity']*100:.2f}%)")
    print(f"  Time: {results['chacha20']['encryption_time']:.6f}s")
    
    print("\n📊 COMPARISON:")
    comp = results['comparison']
    print(f"  Sensitivity Improvement: {comp['sensitivity']['improvement']:+.2f}%")
    print(f"  Entropy Improvement: {comp['entropy']['improvement']:+.2f}%")
    print(f"  Speed Improvement: {comp['speed']['improvement']:+.2f}%")
    print(f"  Security Winner: {comp['winner']['security']}")
    print(f"  Speed Winner: {comp['winner']['speed']}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE! ✅")
    print("=" * 80)