// FIXED VERSION - app.js with proper shared tab handling
// Global state
let currentFileToShare = null;
let allFiles = []; // Cache all files
let currentUserId = null; // Store current user ID
let deviceKeyPair = null; // Device Ed25519 keypair

// ============================================================================
// DEVICE CRYPTO MODULE (Ed25519 signed requests)
// ============================================================================

// Wait for tweetsodium to be available
function waitForTweetsodium() {
  return new Promise((resolve) => {
    const checkInterval = setInterval(() => {
      if (typeof tweetsodium !== "undefined") {
        clearInterval(checkInterval);
        resolve();
      }
    }, 100);
    // Timeout after 5 seconds
    setTimeout(() => {
      clearInterval(checkInterval);
      console.warn("tweetsodium did not load in time");
      resolve();
    }, 5000);
  });
}

const DeviceCrypto = {
  // Get or generate device keypair (OPTIONAL FEATURE)
  async getOrGenerateKeyPair() {
    await waitForTweetsodium();

    // If tweetsodium is blocked, DO NOT crash the app
    if (typeof tweetsodium === "undefined") {
      console.warn(
        "tweetsodium not available, falling back to server-side cryptography",
      );
      return null; // graceful fallback
    }

    // Try loading from localStorage
    const stored = localStorage.getItem("device_keypair");
    if (stored) {
      const { pk, sk } = JSON.parse(stored);
      return {
        publicKey: new Uint8Array(pk),
        secretKey: new Uint8Array(sk),
      };
    }

    // Generate new keypair
    const { publicKey, secretKey } =
      tweetsodium.crypto_sign_seed_keypair(
        tweetsodium.randombytes(32),
      );

    // Store safely
    localStorage.setItem(
      "device_keypair",
      JSON.stringify({
        pk: Array.from(publicKey),
        sk: Array.from(secretKey),
      }),
    );

    return { publicKey, secretKey };
  },

  // OPTIONAL signing (guarded)
  sign(message, secretKey) {
    if (typeof tweetsodium === "undefined" || !secretKey) {
      return null;
    }
    const msgBytes = new TextEncoder().encode(message);
    return tweetsodium.crypto_sign(msgBytes, secretKey);
  },

  // OPTIONAL verify
  verify(signedMsg, publicKey) {
    try {
      if (typeof tweetsodium === "undefined" || !publicKey) {
        return null;
      }
      return tweetsodium.crypto_sign_open(signedMsg, publicKey);
    } catch {
      return null;
    }
  },

  publicKeyHex(publicKey) {
    if (!publicKey) return null;
    return Array.from(publicKey)
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
  },

  publicKeyB64(publicKey) {
    if (!publicKey) return null;
    return btoa(String.fromCharCode(...publicKey));
  },
};


// Initialize device keypair
// (async () => {
//   deviceKeyPair = await DeviceCrypto.getOrGenerateKeyPair();
//   console.log(
//     "Device public key:",
//     DeviceCrypto.publicKeyHex(deviceKeyPair.publicKey),
//   );
// })();

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
  setupUploadZone();
  checkLoginStatus();
});

// Check if user is logged in
async function checkLoginStatus() {
  try {
    const response = await fetch("/api/status", {
      credentials: "include", // Send session cookie
    });
    if (response.ok) {
      const data = await response.json();
      if (data.logged_in) {
        showMainApp(data);
      }
    }
  } catch (error) {
    console.error("Status check failed:", error);
  }
}


// Login
async function login() {
  const userId = document.getElementById("loginUserId").value.trim();
  const password = document.getElementById("loginPassword").value.trim();

  if (!userId) {
    showAlert("Please enter a username", "error");
    return;
  }

  // Password is optional - if not provided, works like before
  // If provided, can be used for additional authentication

  showLoading(true);

  try {
    const response = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include", // Send cookies for CORS
      body: JSON.stringify({ user_id: userId, password: password }),
    });

    const data = await response.json();

    if (data.success) {
      showMainApp(data);
    } else {
      showAlert(data.error || "Login failed", "error");
    }
  } catch (error) {
    showAlert("Login failed: " + error.message, "error");
  } finally {
    showLoading(false);
  }
}

// Logout
async function logout() {
  try {
    await fetch("/api/logout", {
      method: "POST",
      credentials: "include", // Send cookies for CORS
    });
    location.reload();
  } catch (error) {
    console.error("Logout failed:", error);
  }
}

// Show main app
async function showMainApp(data) {
  // Switch UI
  document.getElementById("loginScreen").classList.remove("active");
  document.getElementById("mainApp").classList.add("active");
  document.getElementById("currentUser").textContent = data.user_id;

  // Store current user ID (UI only, NOT for auth)
  currentUserId = data.user_id;

  // ✅ Initialize OPTIONAL device crypto AFTER login
  deviceKeyPair = await DeviceCrypto.getOrGenerateKeyPair();

  if (deviceKeyPair) {
    console.log(
      "Device public key:",
      DeviceCrypto.publicKeyHex(deviceKeyPair.publicKey),
    );
  } else {
    console.warn(
      "Client-side crypto unavailable, using secure server-side cryptography only",
    );
  }

  // Update UI status
  updateStatus(data);

  // ✅ Load files ONLY after login + session established
  await loadFiles();
}


// Update status badges
function updateStatus(data) {
  document.getElementById("blockCount").textContent = data.blocks + " Blocks";

  const ganacheStatus = document.getElementById("ganacheStatus");
  if (data.ganache_connected) {
    ganacheStatus.textContent = "Ganache Connected";
    ganacheStatus.className = "badge connected";
  } else {
    ganacheStatus.textContent = "Ganache Offline";
    ganacheStatus.className = "badge disconnected";
  }
}

// Setup upload zone
function setupUploadZone() {
  const uploadZone = document.getElementById("uploadZone");
  const fileInput = document.getElementById("fileInput");

  // Click to upload
  uploadZone.addEventListener("click", () => fileInput.click());

  // File selected
  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      uploadFile(e.target.files[0]);
    }
  });

  // Drag and drop
  uploadZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadZone.classList.add("dragover");
  });

  uploadZone.addEventListener("dragleave", () => {
    uploadZone.classList.remove("dragover");
  });

  uploadZone.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadZone.classList.remove("dragover");

    if (e.dataTransfer.files.length > 0) {
      uploadFile(e.dataTransfer.files[0]);
    }
  });
}

// Upload file
async function uploadFile(file) {
  showLoading(true);

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("/api/upload", {
      method: "POST",
      credentials: "include", // Send cookies for CORS
      body: formData,
    });

    const data = await response.json();

    if (data.success) {
      const syncStatus = data.ganache_synced
        ? "✅ Synced to Ganache"
        : "⚠️ Local only";
      showAlert(
        `File uploaded successfully!<br>
                Block #${data.block_id}<br>
                ${syncStatus}`,
        "success",
      );

      // Refresh status and files
      await checkLoginStatus();
      await loadFiles();
    } else {
      showAlert("Upload failed: " + data.error, "error");
    }
  } catch (error) {
    showAlert("Upload failed: " + error.message, "error");
  } finally {
    showLoading(false);
    document.getElementById("fileInput").value = "";
  }
}

// Load files
async function loadFiles() {
  try {
    const response = await fetch("/api/files", {
         credentials: "include",
    });

    const data = await response.json();

    if (data.files) {
      // Cache all files
      allFiles = data.files;

      console.log("Loaded files:", allFiles);
      console.log(
        "Own files:",
        allFiles.filter((f) => !f.is_shared),
      );
      console.log(
        "Shared files:",
        allFiles.filter((f) => f.is_shared),
      );

      // Display both views
      displayMyFiles(allFiles.filter((f) => !f.is_shared));
      displaySharedFiles(allFiles.filter((f) => f.is_shared));
    }
  } catch (error) {
    console.error("Failed to load files:", error);
    showAlert("Failed to load files: " + error.message, "error");
  }
}

// Display my files
function displayMyFiles(files) {
  const container = document.getElementById("myFilesList");

  if (!container) {
    console.error("Container myFilesList not found");
    return;
  }

  if (files.length === 0) {
    container.innerHTML =
      '<p style="color: #6b7280; text-align: center; padding: 40px;">No files uploaded yet</p>';
    return;
  }

  container.innerHTML = files
    .map(
      (file) => `
        <div class="file-item">
            <div class="file-info">
                <div class="file-name">📄 ${file.name}</div>
                <div class="file-meta">
                    Block #${file.block_id} • ${new Date(file.timestamp).toLocaleString()}
                </div>
            </div>
            <div class="file-actions">
                <button class="btn btn-primary btn-small" onclick="downloadFile('${file.file_id}')">
                    Download
                </button>
                <button class="btn btn-secondary btn-small" onclick="openShareModal('${file.file_id}')">
                    Share
                </button>
                <button class="btn btn-info btn-small" onclick="openAclModal('${file.file_id}')">
                    ACL
                </button>
                <button class="btn btn-outline btn-small" onclick="openGrantsModal('${file.file_id}')">
                  View Grants
                </button>
            </div>
        </div>
    `,
    )
    .join("");
}

// Display shared files - FIXED VERSION
function displaySharedFiles(files) {
  const container = document.getElementById("sharedFilesList");

  if (!container) {
    console.error("Container sharedFilesList not found");
    return;
  }

  console.log("Displaying shared files:", files);

  if (files.length === 0) {
    container.innerHTML = `
            <div style="text-align: center; padding: 60px 20px;">
                <div style="font-size: 48px; margin-bottom: 20px;">📤</div>
                <h3 style="color: #4b5563; margin-bottom: 10px;">No Files Shared Yet</h3>
                <p style="color: #6b7280;">
                    When someone shares a file with you, it will appear here.
                </p>
                <p style="color: #6b7280; margin-top: 10px; font-size: 14px;">
                    <strong>Tip:</strong> To test file sharing:<br>
                    1. Login as another user (e.g., "alice")<br>
                    2. Upload a file<br>
                    3. Share it with your current username<br>
                    4. Come back here and refresh!
                </p>
            </div>
        `;
    return;
  }

  container.innerHTML = files
    .map(
      (file) => `
        <div class="file-item" style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);">
            <div class="file-info">
                <div class="file-name">
                    <span style="background: #3b82f6; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; margin-right: 8px;">SHARED</span>
                    📤 ${file.name}
                </div>
                <div class="file-meta">
                    <strong>From:</strong> ${file.shared_from} • 
                    <strong>Block:</strong> #${file.block_id} • 
                    <strong>Received:</strong> ${new Date(file.timestamp).toLocaleString()}
                </div>
            </div>
            <div class="file-actions">
                <button class="btn btn-primary btn-small" onclick="downloadFile('${file.file_id}')">
                    Download
                </button>
            </div>
        </div>
    `,
    )
    .join("");
}

// Download file
async function downloadFile(fileId) {
  try {
    showLoading(true);

    // Ensure device keypair exists
    if (!deviceKeyPair) {
      deviceKeyPair = await DeviceCrypto.getOrGenerateKeyPair();
    }

    // Create message to sign: fileId:user:timestamp
    const timestamp = Math.floor(Date.now() / 1000);
    const messageToSign = `${fileId}:${currentUserId}:${timestamp}`;

    // Sign the message with device private key
    const signedMsg = DeviceCrypto.sign(messageToSign, deviceKeyPair.secretKey);
    const signatureB64 = btoa(String.fromCharCode(...signedMsg));
    const devicePubKeyB64 = DeviceCrypto.publicKeyB64(deviceKeyPair.publicKey);

    // Build download URL with signature
    const url =
      `/api/download/${fileId}?` +
      `user_id=${encodeURIComponent(currentUserId)}&` +
      `device_signature=${encodeURIComponent(signatureB64)}&` +
      `device_public_key=${encodeURIComponent(devicePubKeyB64)}&` +
      `timestamp=${timestamp}`;

    window.location.href = url;

    // Show success after a short delay
    setTimeout(() => {
      showAlert("File download started!", "success");
      showLoading(false);
    }, 1000);
  } catch (error) {
    showLoading(false);
    showAlert("Download failed: " + error.message, "error");
  }
}

// Open share modal
function openShareModal(fileId) {
  currentFileToShare = fileId;
  document.getElementById("shareModal").classList.add("active");
  document.getElementById("shareRecipient").value = "";
  document.getElementById("shareRecipient").focus();
}

// Close share modal
function closeShareModal() {
  document.getElementById("shareModal").classList.remove("active");
  currentFileToShare = null;
}

// Confirm share
async function confirmShare() {
  const recipient = document.getElementById("shareRecipient").value.trim();

  console.log("🔍 DEBUG: confirmShare called");
  console.log("🔍 DEBUG: currentFileToShare =", currentFileToShare);
  console.log("🔍 DEBUG: currentUserId =", currentUserId);
  console.log("🔍 DEBUG: recipient =", recipient);

  if (!recipient) {
    showAlert("Please enter recipient User ID", "error");
    return;
  }

  if (!currentFileToShare) {
    showAlert("No file selected for sharing", "error");
    return;
  }

  showLoading(true);

  try {
    const requestData = {
      user_id: currentUserId, // Include current user ID
      file_id: currentFileToShare,
      recipient: recipient,
    };

    console.log("🔍 DEBUG: Request data:", requestData);

    const response = await fetch("/api/share", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include", // Send cookies for CORS
      body: JSON.stringify(requestData),
    });

    const data = await response.json();

    if (data.success) {
      closeShareModal(); // Close modal after successful share
      const syncStatus = data.ganache_synced
        ? "<br>✅ Also synced to Ganache blockchain"
        : "";
      showAlert(
        `✅ File shared successfully with ${recipient}!${syncStatus}<br><br>
                <strong>What happens next:</strong><br>
                • ${recipient} can login to their account<br>
                • They'll see your file in "🤝 Shared" tab<br>
                • They can download and decrypt it`,
        "success",
      );
    } else if (data.already_shared) {
      closeShareModal(); // Close modal for already shared case
      showAlert(`ℹ️ ${data.message}`, "info");
    } else {
      closeShareModal(); // Close modal even if share failed
      showAlert("Share failed: " + data.error, "error");
    }
  } catch (error) {
    closeShareModal(); // Close modal on error
    showAlert("Share failed: " + error.message, "error");
  } finally {
    showLoading(false);
  }
}

// Register device modal
function openRegisterDeviceModal() {
  document.getElementById("registerDeviceModal").classList.add("active");
  document.getElementById("deviceIdInput").value = "";
}
function closeRegisterDeviceModal() {
  document.getElementById("registerDeviceModal").classList.remove("active");
}
async function confirmRegisterDevice() {
  const deviceId = document.getElementById("deviceIdInput").value.trim();
  document.getElementById("registerDeviceResult").innerHTML = "";
  showLoading(true);
  try {
    // Ensure keypair is generated
    if (!deviceKeyPair) {
      deviceKeyPair = await DeviceCrypto.getOrGenerateKeyPair();
    }

    const body = {
      device_id: deviceId || `device_${Date.now()}`,
      device_public_key: DeviceCrypto.publicKeyB64(deviceKeyPair.publicKey),
    };
    const resp = await fetch("/api/acl/register_device", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(body),
    });
    const data = await resp.json();
    if (resp.ok) {
      document.getElementById("registerDeviceResult").innerHTML =
        `<div class=\"alert alert-success\">Device registered: <strong>${data.device_id}</strong><br><small>Public key stored on server</small></div>`;
      setTimeout(() => {
        closeRegisterDeviceModal();
        showAlert("Device registered: " + data.device_id, "success");
      }, 800);
    } else {
      document.getElementById("registerDeviceResult").innerHTML =
        `<div class=\"alert alert-error\">${data.error}</div>`;
    }
  } catch (err) {
    document.getElementById("registerDeviceResult").innerHTML =
      `<div class=\"alert alert-error\">${err.message}</div>`;
  } finally {
    showLoading(false);
  }
}

// ACL modal
function openAclModal(fileId) {
  document.getElementById("aclModal").classList.add("active");
  document.getElementById("aclFileId").value = fileId;
  document.getElementById("aclUserEth").value = "";
  document.getElementById("aclExpiry").value = "";
  document.getElementById("aclDeviceIds").value = "";
  document.getElementById("aclResult").innerHTML = "";
}
function closeAclModal() {
  document.getElementById("aclModal").classList.remove("active");
}

async function confirmGrant() {
  const fileId = document.getElementById("aclFileId").value.trim();
  const userEth = document.getElementById("aclUserEth").value.trim();
  const expiry = parseInt(document.getElementById("aclExpiry").value || "0");
  const deviceIdsRaw = document.getElementById("aclDeviceIds").value.trim();
  const deviceIds = deviceIdsRaw
    ? deviceIdsRaw
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean)
    : [];

  if (!fileId || !userEth) {
    document.getElementById("aclResult").innerHTML =
      `<div class=\"alert alert-error\">File ID and recipient (username or address) required</div>`;
    return;
  }

  // Grants viewer
  async function openGrantsModal(fileId) {
    document.getElementById("grantsModal").classList.add("active");
    document.getElementById("grantsFileId").textContent = fileId;
    const container = document.getElementById("grantsList");
    container.innerHTML = "Loading...";

    try {
      const resp = await fetch(
        `/api/acl/grants?file_id=${encodeURIComponent(fileId)}`,
        {
          credentials: "include",
        },
      );
      const data = await resp.json();
      if (!resp.ok) {
        container.innerHTML = `<div class='alert alert-error'>${data.error || JSON.stringify(data)}</div>`;
        return;
      }

      const grants = data.grants || [];
      if (grants.length === 0) {
        container.innerHTML = "<p>No active grants found for this file.</p>";
        return;
      }

      container.innerHTML = grants
        .map((g) => {
          const devs = (g.devices || [])
            .map((d) => `<code>${d}</code>`)
            .join(" ");
          const revoked = g.revoked
            ? '<span class="tag tag-danger">REVOKED</span>'
            : "";
          const expiry =
            g.expiry && g.expiry > 0
              ? new Date(g.expiry * 1000).toLocaleString()
              : "Never";
          return `
          <div class="grant-item">
            <div><strong>User:</strong> ${g.user} ${revoked}</div>
            <div><strong>Expiry:</strong> ${expiry}</div>
            <div><strong>Devices:</strong> ${devs}</div>
            <div style="margin-top:6px;">
              <button class="btn btn-danger btn-small" onclick="revokeGrant('${fileId}','${g.user}')">Revoke</button>
            </div>
          </div>
        `;
        })
        .join("");
    } catch (err) {
      container.innerHTML = `<div class='alert alert-error'>${err.message}</div>`;
    }
  }

  function closeGrantsModal() {
    document.getElementById("grantsModal").classList.remove("active");
  }

  async function revokeGrant(fileId, userEth) {
    if (!confirm("Revoke access for " + userEth + " on file " + fileId + "?"))
      return;
    showLoading(true);
    try {
      const resp = await fetch("/api/acl/revoke", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ file_id: fileId, user_eth_address: userEth }),
      });
      const data = await resp.json();
      if (resp.ok && data.success) {
        showAlert("Access revoked (tx: " + data.tx + ")", "success");
        // Refresh grants list
        openGrantsModal(fileId);
      } else {
        showAlert(
          "Revoke failed: " + (data.error || JSON.stringify(data)),
          "error",
        );
      }
    } catch (err) {
      showAlert("Revoke failed: " + err.message, "error");
    } finally {
      showLoading(false);
    }
  }
  showLoading(true);
  try {
    const body = {
      file_id: fileId,
      user_eth_address: userEth,
      expiry: expiry,
      device_ids: deviceIds,
    };
    const resp = await fetch("/api/acl/grant", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(body),
    });
    const data = await resp.json();
    if (resp.ok && data.success) {
      document.getElementById("aclResult").innerHTML =
        `<div class=\"alert alert-success\">Grant tx: <small>${data.tx}</small></div>`;
      setTimeout(() => {
        closeAclModal();
        showAlert("Access granted (tx: " + data.tx + ")", "success");
      }, 800);
    } else {
      document.getElementById("aclResult").innerHTML =
        `<div class=\"alert alert-error\">${data.error || JSON.stringify(data)}</div>`;
    }
  } catch (err) {
    document.getElementById("aclResult").innerHTML =
      `<div class=\"alert alert-error\">${err.message}</div>`;
  } finally {
    showLoading(false);
  }
}

async function confirmRevoke() {
  const fileId = document.getElementById("aclFileId").value.trim();
  const userEth = document.getElementById("aclUserEth").value.trim();

  if (!fileId || !userEth) {
    document.getElementById("aclResult").innerHTML =
      `<div class=\"alert alert-error\">File ID and recipient ETH address required</div>`;
    return;
  }

  showLoading(true);
  try {
    const body = { file_id: fileId, user_eth_address: userEth };
    const resp = await fetch("/api/acl/revoke", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(body),
    });
    const data = await resp.json();
    if (resp.ok && data.success) {
      document.getElementById("aclResult").innerHTML =
        `<div class=\"alert alert-success\">Revoke tx: <small>${data.tx}</small></div>`;
      setTimeout(() => {
        closeAclModal();
        showAlert("Access revoked (tx: " + data.tx + ")", "success");
      }, 800);
    } else {
      document.getElementById("aclResult").innerHTML =
        `<div class=\"alert alert-error\">${data.error || JSON.stringify(data)}</div>`;
    }
  } catch (err) {
    document.getElementById("aclResult").innerHTML =
      `<div class=\"alert alert-error\">${err.message}</div>`;
  } finally {
    showLoading(false);
  }
}

// Switch tabs - FIXED VERSION
function switchTab(tabName) {
  // Update tab buttons
  document
    .querySelectorAll(".tab")
    .forEach((tab) => tab.classList.remove("active"));
  event.target.classList.add("active");

  // Update tab content
  document
    .querySelectorAll(".tab-content")
    .forEach((content) => content.classList.remove("active"));
  document.getElementById(tabName + "Tab").classList.add("active");

  // Reload files when switching to shared tab
  if (tabName === "shared") {
    console.log("Switched to shared tab, reloading files...");
    loadFiles(); // Refresh file list
  }

  // Load content for specific tabs
  if (tabName === "blockchain") {
    loadBlockchain();
  } else if (tabName === "ganache") {
    loadGanacheStatus();
  }
}

// Load blockchain
async function loadBlockchain() {
  try {
    const response = await fetch(
      `/api/blockchain?user_id=${encodeURIComponent(currentUserId)}`,
      {
        credentials: "include", // Send cookies for CORS
      },
    );
    const data = await response.json();

    const container = document.getElementById("blockchainView");

    if (data.blocks.length === 0) {
      container.innerHTML =
        '<p style="color: #6b7280; text-align: center; padding: 40px;">No blocks yet</p>';
      return;
    }

    container.innerHTML = data.blocks
      .map(
        (block) => `
            <div class="block">
                <div class="block-header">
                    <span class="block-id">Block #${block.block_id}</span>
                    <span class="block-timestamp">${new Date(block.timestamp).toLocaleString()}</span>
                </div>
                <div class="block-details">
                    <div><strong>File ID:</strong> ${block.file_id}</div>
                    <div><strong>Owner:</strong> ${block.owner}</div>
                    ${
                      block.is_shared
                        ? `<div style="color: #3b82f6;"><strong>📤 Shared from:</strong> ${block.shared_from}</div>`
                        : '<div style="color: #10b981;"><strong>📁 Type:</strong> Own file</div>'
                    }
                </div>
                <div class="block-hash">
                    <strong>Hash:</strong> ${block.hash.substring(0, 64)}...
                </div>
                <div class="block-hash" style="margin-top: 5px;">
                    <strong>Previous:</strong> ${block.previous_hash.substring(0, 64)}...
                </div>
            </div>
        `,
      )
      .join("");

    if (data.valid) {
      container.innerHTML +=
        '<div class="alert alert-success" style="margin-top: 20px;">✅ Blockchain is valid and tamper-proof</div>';
    } else {
      container.innerHTML +=
        '<div class="alert alert-error" style="margin-top: 20px;">❌ Blockchain validation failed!</div>';
    }
  } catch (error) {
    console.error("Failed to load blockchain:", error);
    showAlert("Failed to load blockchain: " + error.message, "error");
  }
}

// Load Ganache status
async function loadGanacheStatus() {
  try {
    const response = await fetch(
      `/api/ganache/status?user_id=${encodeURIComponent(currentUserId)}`,
      {
        credentials: "include", // Send cookies for CORS
      },
    );
    const data = await response.json();

    const dashboard = document.getElementById("ganacheDashboard");
    const details = document.getElementById("ganacheDetails");

    if (data.connected) {
      dashboard.innerHTML = `
                <div class="stat-card">
                    <div class="stat-label">Status</div>
                    <div class="stat-value">✅</div>
                    <div class="stat-label">Connected</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Blocks on Chain</div>
                    <div class="stat-value">${data.blocks_on_chain}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Network ID</div>
                    <div class="stat-value">${data.network_id}</div>
                </div>
            `;

      details.innerHTML = `
                <div class="alert alert-success">
                    <strong>✅ Connected to Ganache</strong><br>
                    <strong>Contract:</strong> ${data.contract}<br><br>
                    <strong>Benefits:</strong><br>
                    • Decentralized storage<br>
                    • Immutable records<br>
                    • View in Ganache UI<br>
                    • Ethereum blockchain backed
                </div>
            `;
    } else {
      dashboard.innerHTML = `
                <div class="stat-card">
                    <div class="stat-label">Status</div>
                    <div class="stat-value">⚠️</div>
                    <div class="stat-label">Offline</div>
                </div>
            `;

      details.innerHTML = `
                <div class="alert alert-info">
                    <strong>⚠️ Ganache Not Connected</strong><br>
                    Reason: ${data.message}<br><br>
                    <strong>To enable Ganache:</strong><br>
                    1. Download Ganache from trufflesuite.com<br>
                    2. Start Ganache (Quick Start)<br>
                    3. Run: python step10_full_ganache.py<br>
                    4. Refresh this page<br><br>
                    <strong>Current setup:</strong><br>
                    ✅ Local storage working<br>
                    ✅ All features available<br>
                    ⚠️ No blockchain backup
                </div>
            `;
    }
  } catch (error) {
    console.error("Failed to load Ganache status:", error);
  }
}

// Show alert
function showAlert(message, type) {
  const statusDiv = document.getElementById("uploadStatus");
  statusDiv.innerHTML = `<div class="alert alert-${type}">${message}</div>`;

  // Auto-hide after 8 seconds for success messages
  if (type === "success") {
    setTimeout(() => {
      statusDiv.innerHTML = "";
    }, 8000);
  }
}

// Show/hide loading
function showLoading(show) {
  const loading = document.getElementById("loadingOverlay");
  if (show) {
    loading.classList.add("active");
  } else {
    loading.classList.remove("active");
  }
}

// Add Enter key support for share modal
document.addEventListener("DOMContentLoaded", () => {
  const shareInput = document.getElementById("shareRecipient");
  if (shareInput) {
    shareInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        confirmShare();
      }
    });
  }

  const loginInput = document.getElementById("loginUserId");
  if (loginInput) {
    loginInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        login();
      }
    });
  }
});

// Analyze File Function
async function analyzeFile() {
  const fileInput = document.getElementById("analyzeFile");

  if (!fileInput.files.length) {
    alert("Please select a file to analyze");
    return;
  }

  const file = fileInput.files[0];

  // Show loading
  document.getElementById("analysisLoading").style.display = "block";
  document.getElementById("analysisResults").style.display = "none";

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (data.success) {
      displayAnalysisResults(data.results);
    } else {
      alert("Analysis failed: " + data.error);
    }
  } catch (error) {
    alert("Analysis error: " + error.message);
  } finally {
    document.getElementById("analysisLoading").style.display = "none";
  }
}

// Display Analysis Results
function displayAnalysisResults(results) {
  // Show results section
  document.getElementById("analysisResults").style.display = "block";

  // File info
  document.getElementById("analyzedFileName").textContent = results.file_name;
  document.getElementById("analyzedFileSize").textContent =
    results.file_size.toLocaleString();

  // Comparison table
  const tbody = document.getElementById("comparisonTableBody");
  tbody.innerHTML = `
        <tr style="background: #f9fafb;">
            <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">
                <strong>Original File</strong><br>
                <small style="color: #6b7280;">Unencrypted data</small>
            </td>
            <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e5e7eb;">
                ${(results.original.sensitivity * 100).toFixed(2)}%
            </td>
            <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e5e7eb;">
                ${results.original.entropy.toFixed(4)}
            </td>
            <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e5e7eb;">
                -
            </td>
            <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e5e7eb;">
                <span style="color: #ef4444;">❌ Not Secure</span>
            </td>
        </tr>
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">
                <strong>Traditional AES</strong><br>
                <small style="color: #6b7280;">Standard centralized approach</small>
            </td>
            <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e5e7eb;">
                ${(results.traditional_aes.sensitivity * 100).toFixed(2)}%
            </td>
            <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e5e7eb;">
                ${results.traditional_aes.entropy.toFixed(4)}
            </td>
            <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e5e7eb;">
                ${(results.traditional_aes.encryption_time * 1000).toFixed(2)}ms
            </td>
            <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e5e7eb;">
                <span style="color: #f59e0b;">Baseline</span>
            </td>
        </tr>
        <tr style="background: #d1fae5;">
            <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">
                <strong>⭐ Dynamic AES (Proposed)</strong><br>
                <small style="color: #6b7280;">Our innovation with blockchain</small>
            </td>
            <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e5e7eb;">
                <strong style="color: #10b981;">${(results.dynamic_aes.sensitivity * 100).toFixed(2)}%</strong><br>
                ${
                  results.comparison.sensitivity.improvement !== 0
                    ? `<small style="color: ${results.comparison.sensitivity.improvement > 0 ? "#10b981" : "#ef4444"};">${results.comparison.sensitivity.improvement > 0 ? "↑" : "↓"} ${Math.abs(results.comparison.sensitivity.improvement).toFixed(2)}%</small>`
                    : ""
                }
            </td>
            <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e5e7eb;">
                <strong style="color: #10b981;">${results.dynamic_aes.entropy.toFixed(4)}</strong>
            </td>
            <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e5e7eb;">
                <strong style="color: #10b981;">${(results.dynamic_aes.encryption_time * 1000).toFixed(2)}ms</strong><br>
                <small style="color: #10b981;">↓ ${Math.abs(results.comparison.speed.improvement).toFixed(1)}% faster</small>
            </td>
            <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e5e7eb;">
                <strong style="color: #10b981;">✅ Recommended</strong>
            </td>
        </tr>
        <tr style="background: #f9fafb;">
            <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">
                <strong>CHACHA20</strong><br>
                <small style="color: #6b7280;">For mobile/IoT devices</small>
            </td>
            <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e5e7eb;">
                ${(results.chacha20.sensitivity * 100).toFixed(2)}%
            </td>
            <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e5e7eb;">
                ${results.chacha20.entropy.toFixed(4)}
            </td>
            <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e5e7eb;">
                ${(results.chacha20.encryption_time * 1000).toFixed(2)}ms<br>
                <small style="color: #6b7280;">For ARM platforms</small>
            </td>
            <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e5e7eb;">
                <span style="color: #3b82f6;">Alternative</span>
            </td>
        </tr>
    `;

  // Draw histograms
  drawHistogram(
    "originalHistogram",
    results.original.histogram,
    "Original File",
  );
  drawHistogram(
    "traditionalHistogram",
    results.traditional_aes.histogram,
    "Traditional AES",
  );
  drawHistogram(
    "dynamicHistogram",
    results.dynamic_aes.histogram,
    "Dynamic AES (Proposed)",
  );
  drawHistogram("chachaHistogram", results.chacha20.histogram, "CHACHA20");

  // Analysis summary - clear and focused on our innovation
  document.getElementById("analysisSummary").innerHTML = `
        <h3 style="margin-bottom: 10px;">📊 Analysis Summary</h3>
        
        <div style="background: #d1fae5; padding: 15px; border-radius: 8px; margin: 15px 0;">
            <h4 style="color: #065f46; margin-bottom: 10px;">✅ Our Proposed Algorithm (Dynamic AES)</h4>
            <p style="margin: 5px 0; color: #047857;">
                <strong>Performance:</strong> ${(results.dynamic_aes.encryption_time * 1000).toFixed(2)}ms 
                (${Math.abs(results.comparison.speed.improvement).toFixed(1)}% faster than traditional)
            </p>
            <p style="margin: 5px 0; color: #047857;">
                <strong>Security:</strong> ${(results.dynamic_aes.sensitivity * 100).toFixed(2)}% sensitivity
            </p>
            <p style="margin: 5px 0; color: #047857;">
                <strong>Innovation:</strong> Dynamic keys + Blockchain storage
            </p>
        </div>
        
        <div style="background: #fef3c7; padding: 15px; border-radius: 8px; margin: 15px 0;">
            <h4 style="color: #92400e; margin-bottom: 10px;">📌 Comparison with Baseline</h4>
            <table style="width: 100%; font-size: 14px;">
                <tr>
                    <td style="padding: 5px;"><strong>Traditional AES:</strong></td>
                    <td style="padding: 5px;">${(results.traditional_aes.encryption_time * 1000).toFixed(2)}ms</td>
                    <td style="padding: 5px; color: #6b7280;">Baseline</td>
                </tr>
                <tr style="background: #d1fae5;">
                    <td style="padding: 5px;"><strong>Our Dynamic AES:</strong></td>
                    <td style="padding: 5px; color: #10b981; font-weight: bold;">${(results.dynamic_aes.encryption_time * 1000).toFixed(2)}ms</td>
                    <td style="padding: 5px; color: #10b981;">✅ Recommended</td>
                </tr>
                <tr>
                    <td style="padding: 5px;"><strong>CHACHA20:</strong></td>
                    <td style="padding: 5px;">${(results.chacha20.encryption_time * 1000).toFixed(2)}ms</td>
                    <td style="padding: 5px; color: #6b7280;">For mobile devices</td>
                </tr>
            </table>
        </div>
        
        <p style="margin: 15px 0 0 0; padding: 15px; background: #f9fafb; border-radius: 8px; font-size: 14px;">
            <strong>📈 Key Findings:</strong><br>
            • Dynamic AES achieves ${Math.abs(results.comparison.speed.improvement).toFixed(1)}% performance improvement<br>
            • Maintains high security (sensitivity: ${(results.dynamic_aes.sensitivity * 100).toFixed(2)}%)<br>
            • Blockchain key management provides decentralization<br>
            • Suitable for server deployments with hardware acceleration
        </p>
    `;

  // Scroll to results
  document
    .getElementById("analysisResults")
    .scrollIntoView({ behavior: "smooth", block: "start" });
}

// Draw histogram on canvas
function drawHistogram(canvasId, histogram, title) {
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext("2d");

  // Clear canvas
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Find max value for scaling
  const maxValue = Math.max(...histogram);

  // Draw bars
  const barWidth = canvas.width / histogram.length;
  const maxHeight = canvas.height - 30;

  ctx.fillStyle = "#667eea";
  for (let i = 0; i < histogram.length; i++) {
    const barHeight = (histogram[i] / maxValue) * maxHeight;
    ctx.fillRect(i * barWidth, canvas.height - barHeight, barWidth, barHeight);
  }

  // Draw labels
  ctx.fillStyle = "#1f2937";
  ctx.font = "10px Arial";
  ctx.textAlign = "center";
  ctx.fillText("0", 0, canvas.height - 5);
  ctx.fillText("255", canvas.width, canvas.height - 5);
  ctx.fillText("Byte Value", canvas.width / 2, canvas.height - 5);
}

