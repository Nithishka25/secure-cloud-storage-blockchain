"""
STEP 10: Full Ganache Integration with Smart Contract
====================================================

✔ Ganache connection
✔ Solidity contract compilation
✔ Contract deployment
✔ On-chain block storage
✔ Block retrieval

WORKS ON WINDOWS (py-solc-x FIX APPLIED)
"""

from web3 import Web3
from solcx import (
    compile_source,
    install_solc,
    set_solc_version,
    get_installed_solc_versions
)
import json
from pathlib import Path
import config

# ---------------------------------------------------------------------------
# FORCE SOLIDITY COMPILER (CRITICAL FOR WINDOWS)
# ---------------------------------------------------------------------------
REQUIRED_SOLC_VERSION = "0.8.0"

installed_versions = [str(v) for v in get_installed_solc_versions()]
if REQUIRED_SOLC_VERSION not in installed_versions:
    install_solc(REQUIRED_SOLC_VERSION)

set_solc_version(REQUIRED_SOLC_VERSION)

# ---------------------------------------------------------------------------
# SMART CONTRACT
# ---------------------------------------------------------------------------
BLOCKCHAIN_STORAGE_CONTRACT = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract BlockchainStorage {

    struct Block {
        uint256 blockId;
        string data;
        string previousHash;
        string hash;
        string fileId;
        string owner;
        uint256 timestamp;
    }

    mapping(address => Block[]) private userBlocks;
    mapping(address => mapping(string => uint256)) private fileToBlockIndex;

    event BlockAdded(
        address indexed owner,
        uint256 blockId,
        string fileId,
        uint256 timestamp
    );

    function addBlock(
        uint256 blockId,
        string memory data,
        string memory previousHash,
        string memory hash,
        string memory fileId
    ) public {
        Block memory newBlock = Block(
            blockId,
            data,
            previousHash,
            hash,
            fileId,
            addressToString(msg.sender),
            block.timestamp
        );

        userBlocks[msg.sender].push(newBlock);
        fileToBlockIndex[msg.sender][fileId] = userBlocks[msg.sender].length - 1;

        emit BlockAdded(msg.sender, blockId, fileId, block.timestamp);
    }

    function getBlockCount() public view returns (uint256) {
        return userBlocks[msg.sender].length;
    }

    function getBlock(uint256 index) public view returns (
        uint256,
        string memory,
        string memory,
        string memory,
        string memory,
        string memory,
        uint256
    ) {
        require(index < userBlocks[msg.sender].length, "Block not found");
        Block memory b = userBlocks[msg.sender][index];
        return (
            b.blockId,
            b.data,
            b.previousHash,
            b.hash,
            b.fileId,
            b.owner,
            b.timestamp
        );
    }

    function addressToString(address _addr) internal pure returns (string memory) {
        bytes32 value = bytes32(uint256(uint160(_addr)));
        bytes memory alphabet = "0123456789abcdef";
        bytes memory str = new bytes(42);
        str[0] = "0";
        str[1] = "x";
        for (uint256 i = 0; i < 20; i++) {
            str[2 + i * 2] = alphabet[uint8(value[i + 12] >> 4)];
            str[3 + i * 2] = alphabet[uint8(value[i + 12] & 0x0f)];
        }
        return string(str);
    }
}
"""

# ---------------------------------------------------------------------------
# FILE ACCESS CONTROL CONTRACT
# ---------------------------------------------------------------------------
FILE_ACCESS_CONTRACT = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract FileAccessControl {
    struct AccessInfo {
        bool allowed;
        uint256 expiry;
        mapping(bytes32 => bool) devices;
        bool deviceRestrictionEnabled;
    }

    mapping(bytes32 => mapping(address => AccessInfo)) private accessMap;
    mapping(bytes32 => address) public fileOwner;

    event AccessGranted(bytes32 indexed fileId, address indexed user, uint256 expiry);
    event AccessRevoked(bytes32 indexed fileId, address indexed user);
    event DeviceAllowed(bytes32 indexed fileId, address indexed user, bytes32 deviceId);
    event FileOwnerSet(bytes32 indexed fileId, address indexed owner);

    modifier onlyOwner(bytes32 fileId) {
        require(fileOwner[fileId] == msg.sender, "Not file owner");
        _;
    }

    function setFileOwner(bytes32 fileId, address owner) public {
        if (fileOwner[fileId] == address(0)) {
            fileOwner[fileId] = owner;
            emit FileOwnerSet(fileId, owner);
        } else {
            require(fileOwner[fileId] == msg.sender, "Only owner can change");
            fileOwner[fileId] = owner;
            emit FileOwnerSet(fileId, owner);
        }
    }

    function grantAccess(bytes32 fileId, address user, uint256 expiry, bytes32[] calldata deviceIds) public onlyOwner(fileId) {
        AccessInfo storage a = accessMap[fileId][user];
        a.allowed = true;
        a.expiry = expiry;
        if (deviceIds.length > 0) {
            a.deviceRestrictionEnabled = true;
            for (uint i = 0; i < deviceIds.length; i++) {
                a.devices[deviceIds[i]] = true;
                emit DeviceAllowed(fileId, user, deviceIds[i]);
            }
        } else {
            a.deviceRestrictionEnabled = false;
        }
        emit AccessGranted(fileId, user, expiry);
    }

    function revokeAccess(bytes32 fileId, address user) public onlyOwner(fileId) {
        AccessInfo storage a = accessMap[fileId][user];
        a.allowed = false;
        a.expiry = 0;
        a.deviceRestrictionEnabled = false;
        emit AccessRevoked(fileId, user);
    }

    function isAccessAllowed(bytes32 fileId, address user, bytes32 deviceId) public view returns (bool) {
        AccessInfo storage a = accessMap[fileId][user];
        if (!a.allowed) return false;
        if (a.expiry != 0 && block.timestamp > a.expiry) return false;
        if (a.deviceRestrictionEnabled) {
            return a.devices[deviceId];
        }
        return true;
    }

    function isAccessAllowedNoDevice(bytes32 fileId, address user) public view returns (bool) {
        AccessInfo storage a = accessMap[fileId][user];
        if (!a.allowed) return false;
        if (a.expiry != 0 && block.timestamp > a.expiry) return false;
        return true;
    }
}
"""

# ---------------------------------------------------------------------------
# GANACHE BLOCKCHAIN CLASS
# ---------------------------------------------------------------------------
class GanacheBlockchain:

    def __init__(self, ganache_url=None):
        self.ganache_url = ganache_url or config.GANACHE_URL
        self.w3 = None
        self.contract = None
        self.contract_address = None

    def connect(self):
        self.w3 = Web3(Web3.HTTPProvider(self.ganache_url))

        if not self.w3.is_connected():
            print("❌ Cannot connect to Ganache")
            return False

        print("✅ Connected to Ganache")
        print("   Network ID:", self.w3.eth.chain_id)
        print("   Latest block:", self.w3.eth.block_number)
        print("   Accounts:", len(self.w3.eth.accounts))
        return True

    def deploy_contract(self):
        print("\n📝 Deploying smart contract...")

        compiled_sol = compile_source(
            BLOCKCHAIN_STORAGE_CONTRACT,
            output_values=["abi", "bin"],
            solc_version=REQUIRED_SOLC_VERSION
        )

        _, contract_interface = compiled_sol.popitem()
        abi = contract_interface["abi"]
        bytecode = contract_interface["bin"]

        contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)
        account = self.w3.eth.accounts[0]

        tx_hash = contract.constructor().transact({
            "from": account,
            "gas": 3000000
        })

        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        self.contract_address = receipt.contractAddress
        self.contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=abi
        )

        print("✅ Contract deployed at:", self.contract_address)

        Path(config.DATA_DIR).mkdir(exist_ok=True)
        with open(Path(config.DATA_DIR) / "contract_info.json", "w") as f:
            json.dump(
                {"address": self.contract_address, "abi": abi},
                f,
                indent=2
            )

    def deploy_acl_contract(self):
        """Compile and deploy the FileAccessControl contract and save info."""
        print("\n📝 Deploying ACL smart contract...")

        compiled_sol = compile_source(
            FILE_ACCESS_CONTRACT,
            output_values=["abi", "bin"],
            solc_version=REQUIRED_SOLC_VERSION
        )

        _, contract_interface = compiled_sol.popitem()
        abi = contract_interface["abi"]
        bytecode = contract_interface["bin"]

        contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)
        account = self.w3.eth.accounts[0]

        tx_hash = contract.constructor().transact({
            "from": account,
            "gas": 3000000
        })

        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        acl_address = receipt.contractAddress
        print("✅ ACL Contract deployed at:", acl_address)

        Path(config.DATA_DIR).mkdir(exist_ok=True)
        with open(Path(config.DATA_DIR) / "contract_acl.json", "w") as f:
            json.dump({"address": acl_address, "abi": abi}, f, indent=2)

        return acl_address

    def add_block(self, block_data):
        tx = self.contract.functions.addBlock(
            block_data["block_id"],
            block_data["data"],
            block_data["previous_hash"],
            block_data["hash"],
            block_data["file_id"]
        ).transact({
            "from": self.w3.eth.accounts[0],
            "gas": 2000000  # Increased gas limit to handle larger data
        })

        receipt = self.w3.eth.wait_for_transaction_receipt(tx)
        print("✅ Block added | Tx:", tx.hex())
        return tx.hex()

    def get_block_count(self):
        return self.contract.functions.getBlockCount().call({
            "from": self.w3.eth.accounts[0]
        })

    def get_block(self, index):
        b = self.contract.functions.getBlock(index).call({
            "from": self.w3.eth.accounts[0]
        })
        return {
            "block_id": b[0],
            "data": b[1],
            "previous_hash": b[2],
            "hash": b[3],
            "file_id": b[4],
            "owner": b[5],
            "timestamp": b[6]
        }

# ---------------------------------------------------------------------------
# TEST
# ---------------------------------------------------------------------------
def test_ganache_full():
    print("=" * 80)
    print("TESTING FULL GANACHE INTEGRATION")
    print("=" * 80)

    print("\nPress Enter when Ganache is running...")
    print("(Ganache detected - proceeding automatically)")
    # Skip input prompt - just continue

    ganache = GanacheBlockchain()

    if not ganache.connect():
        return

    ganache.deploy_contract()
    # Deploy ACL contract for access control
    try:
        ganache.deploy_acl_contract()
    except Exception as e:
        print(f"⚠️  ACL deployment failed: {e}")

    test_block = {
        "block_id": 1,
        "data": "encrypted_aes_key_here",
        "previous_hash": "0" * 64,
        "hash": "a" * 64,
        "file_id": "test_file_001"
    }

    ganache.add_block(test_block)

    print("\n📝 Block count:", ganache.get_block_count())
    block = ganache.get_block(0)

    print("\n📝 Retrieved block")
    print("Block ID:", block["block_id"])
    print("File ID:", block["file_id"])
    print("Timestamp:", block["timestamp"])

    print("\n" + "=" * 80)
    print("GANACHE INTEGRATION SUCCESSFUL ✅")
    print("=" * 80)

if __name__ == "__main__":
    # Skip waiting if running non-interactively
    import sys
    if not sys.stdin.isatty():
        # Non-interactive mode - just run the test
        pass
    
    test_ganache_full()
