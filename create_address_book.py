#!/usr/bin/env python3
"""
Create an address book mapping usernames to Ethereum addresses from Ganache
"""
import json
from pathlib import Path
from step10_full_ganache import GanacheBlockchain

# Connect to Ganache
ganache = GanacheBlockchain()
if not ganache.connect():
    print("❌ Failed to connect to Ganache")
    exit(1)

print("✅ Connected to Ganache")
print(f"📡 Network ID: {ganache.w3.eth.chain_id}")

# Get available accounts
accounts = ganache.w3.eth.accounts
print(f"📊 Found {len(accounts)} accounts")

# Create address book mapping
address_book = {}
usernames = ["alice", "bob", "charlie", "dave", "eve"]

for i, username in enumerate(usernames):
    if i < len(accounts):
        address = accounts[i]
        address_book[username] = address
        print(f"  {username:10} → {address}")

# Save to file
address_book_path = Path("data/address_book.json")
address_book_path.parent.mkdir(parents=True, exist_ok=True)

with open(address_book_path, 'w') as f:
    json.dump(address_book, f, indent=2)

print(f"\n✅ Address book saved to {address_book_path}")
print(f"📝 {len(address_book)} addresses registered")
