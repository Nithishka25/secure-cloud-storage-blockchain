// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract FileAccessControl {
    struct AccessInfo {
        bool allowed;
        uint256 expiry; // unix timestamp, 0 = no expiry
        mapping(bytes32 => bool) devices; // deviceId -> allowed
        bool deviceRestrictionEnabled;
    }

    // fileId => user => access
    mapping(bytes32 => mapping(address => AccessInfo)) private accessMap;

    // file owner mapping
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
        // once set, only owner can change - allow reassign by current owner
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

    // helper to check access without device
    function isAccessAllowedNoDevice(bytes32 fileId, address user) public view returns (bool) {
        AccessInfo storage a = accessMap[fileId][user];
        if (!a.allowed) return false;
        if (a.expiry != 0 && block.timestamp > a.expiry) return false;
        return true;
    }
}
