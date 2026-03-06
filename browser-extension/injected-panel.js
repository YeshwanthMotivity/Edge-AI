// injected-panel.js
// injected-panel.js
const loginView = document.getElementById('loginView');
const mainView = document.getElementById('mainView');
const logoutBtn = document.getElementById('logoutBtn');
const authBtn = document.getElementById('authBtn');
const authToggleBtn = document.getElementById('authToggleBtn');
const authToggleText = document.getElementById('authToggleText');
const authTitle = document.getElementById('authTitle');
const authErrorMsg = document.getElementById('authErrorMsg');
const usernameInput = document.getElementById('usernameInput');
const passwordInput = document.getElementById('passwordInput');
const userFooterLabel = document.getElementById('userFooterLabel');
const closePanelBtn = document.getElementById('closePanelBtn');

let isRegisterMode = false;

// Talk to parent window to close the iframe
closePanelBtn.addEventListener('click', () => {
    window.parent.postMessage({ action: 'EDGE_POLICY_CLOSE_PANEL' }, '*');
});

// Auth Toggle Mode
authToggleBtn.addEventListener('click', (e) => {
    e.preventDefault();
    isRegisterMode = !isRegisterMode;
    authErrorMsg.style.display = 'none';

    if (isRegisterMode) {
        authTitle.innerText = 'Create Account';
        authBtn.innerText = 'Register';
        authToggleText.innerText = 'Already have an account?';
        authToggleBtn.innerText = 'Sign In';
    } else {
        authTitle.innerText = 'Sign In';
        authBtn.innerText = 'Authenticate';
        authToggleText.innerText = 'Need an account?';
        authToggleBtn.innerText = 'Register';
    }
});

// Authentication Logic
function checkAuth() {
    chrome.storage.local.get(['edgePolicyUser', 'edgePolicyToken'], (result) => {
        if (result.edgePolicyUser && result.edgePolicyToken) {
            // Logged in
            loginView.classList.remove('active');
            mainView.classList.add('active');
            logoutBtn.style.display = 'block';
            userFooterLabel.textContent = result.edgePolicyUser;
            updateUI(); // load logs
        } else {
            // Logged out
            mainView.classList.remove('active');
            loginView.classList.add('active');
            logoutBtn.style.display = 'none';
            userFooterLabel.textContent = 'Unauthenticated';
        }
    });
}

const API_BASE = 'http://127.0.0.1:8000/api/v1';

authBtn.addEventListener('click', async () => {
    const user = usernameInput.value.trim();
    const pass = passwordInput.value.trim();

    if (!user || pass.length < 6) {
        showAuthError("Please provide a username and at least 6 characters for password.");
        return;
    }

    authBtn.disabled = true;
    authBtn.innerText = 'Processing...';
    authErrorMsg.style.display = 'none';

    try {
        let endpoint = `${API_BASE}/auth/token`;
        let bodyPayload;
        let headers = {};

        if (isRegisterMode) {
            endpoint = `${API_BASE}/auth/register`;
            headers['Content-Type'] = 'application/json';
            bodyPayload = JSON.stringify({ username: user, password: pass });
        } else {
            // OAuth2 Form Data for login
            headers['Content-Type'] = 'application/x-www-form-urlencoded';
            bodyPayload = new URLSearchParams({
                username: user,
                password: pass
            }).toString();
        }

        const res = await fetch(endpoint, {
            method: 'POST',
            headers: headers,
            body: bodyPayload
        });

        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.detail || "Authentication Failed");
        }

        const data = await res.json();

        chrome.storage.local.set({
            edgePolicyUser: data.username,
            edgePolicyToken: data.access_token
        }, () => {
            usernameInput.value = '';
            passwordInput.value = '';
            checkAuth();
        });

    } catch (err) {
        showAuthError(err.message);
    } finally {
        authBtn.disabled = false;
        authBtn.innerText = isRegisterMode ? 'Register' : 'Authenticate';
    }
});

function showAuthError(msg) {
    authErrorMsg.innerText = msg;
    authErrorMsg.style.display = 'block';
}

document.getElementById('logoutBtn').addEventListener('click', () => {
    chrome.storage.local.remove(['edgePolicyToken', 'edgePolicyUser'], () => {
        document.getElementById('mainView').classList.remove('active');
        document.getElementById('loginView').classList.add('active');
        document.getElementById('logoutBtn').style.display = 'none';
        document.getElementById('userFooterLabel').textContent = 'Unauthenticated';
        clearFileInput();
    });
});

function clearFileInput() {
    const fileInput = document.getElementById('fileInput');
    const sanitizeBtn = document.getElementById('sanitizeBtn');
    const fileNameDisplay = document.getElementById('fileNameDisplay');
    const resultDiv = document.getElementById('sanitizeResult');

    if (fileInput) fileInput.value = '';
    if (fileNameDisplay) {
        fileNameDisplay.innerText = 'Select Document to Sanitize';
        fileNameDisplay.style.color = 'var(--text-muted)';
    }
    if (sanitizeBtn) sanitizeBtn.style.display = 'none';
    if (resultDiv) resultDiv.style.display = 'none';

    const dragContainer = document.getElementById('dragContainer');
    if (dragContainer) dragContainer.style.display = 'none';
}

checkAuth(); // Initial Check


// Tab Switching Logic
document.querySelectorAll('.tab-btn').forEach(button => {
    button.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

        button.classList.add('active');
        document.getElementById(button.dataset.target).classList.add('active');
    });
});

// Logs UI Logic
function updateUI() {
    chrome.storage.local.get(['blockLogs', 'edgePolicyUser'], (result) => {
        // Only show logs if authenticated
        if (!result.edgePolicyUser) return;

        const allLogs = result.blockLogs || [];
        const logs = allLogs.filter(log => log.user === result.edgePolicyUser);
        const container = document.getElementById('logList');

        let blocked = 0;
        let allowed = 0;

        container.innerHTML = '';
        if (logs.length > 0) {
            // Group by filename to create process timelines
            const groupedLogs = {};
            logs.forEach(log => {
                if (log.status === 'BLOCKED') blocked++;
                else allowed++;

                if (!groupedLogs[log.filename]) {
                    groupedLogs[log.filename] = [];
                }
                groupedLogs[log.filename].push(log);
            });

            // Sort by latest activity first
            const sortedFilenames = Object.keys(groupedLogs).sort((a, b) => {
                const latestA = groupedLogs[a][groupedLogs[a].length - 1].timestamp;
                const latestB = groupedLogs[b][groupedLogs[b].length - 1].timestamp;
                return latestB - latestA;
            });

            sortedFilenames.forEach(filename => {
                const fileLogs = groupedLogs[filename];
                const latestLog = fileLogs[fileLogs.length - 1];
                const isAuthorized = fileLogs.some(l => l.status === 'AUTHORIZED');
                const latestStatus = isAuthorized ? 'AUTHORIZED' : 'BLOCKED';

                const item = document.createElement('div');
                item.className = `log-item ${latestStatus}`;

                const site = latestLog.url ? (latestLog.url.includes('/') ? latestLog.url.split('/')[2].replace('www.', '') : latestLog.url) : 'Extension UI';

                let timelineHTML = '';
                fileLogs.forEach((l, index) => {
                    const lDate = new Date(l.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                    const lAction = l.status === 'BLOCKED' ? 'Intercepted (Blocked)' : 'Sanitized (Authorized)';
                    const color = l.status === 'BLOCKED' ? 'var(--danger)' : 'var(--success)';
                    timelineHTML += `<div style="margin-top: 6px; padding-left: 10px; border-left: 2px solid rgba(148,163,184,0.2); position: relative;">
                        <span style="position: absolute; left: -5px; top: 4px; width: 6px; height: 6px; background: ${color}; border-radius: 50%;"></span>
                        <span style="color: ${color}; font-weight: bold; font-size: 10px;">${lDate}</span> - <span style="font-size: 11px;">${lAction}</span>
                    </div>`;
                });

                item.innerHTML = `
                    <div class="log-meta">
                        <span>Source: ${site}</span>
                        <span class="status-badge">${latestStatus}</span>
                    </div>
                    <span class="log-filename" style="margin-bottom: 8px;">${filename}</span>
                    <div class="log-info" style="flex-direction: column; align-items: flex-start;">
                        ${timelineHTML}
                    </div>
                `;
                container.appendChild(item);
            });
        } else {
            container.innerHTML = '<div class="no-logs">Monitoring active. Awaiting activity...</div>';
        }

        document.getElementById('blockedCount').innerText = blocked;
        document.getElementById('allowedCount').innerText = allowed;
    });
}

// Listen to storage changes to auto-update logs when background script intercepts
chrome.storage.onChanged.addListener((changes, namespace) => {
    if (namespace === 'local' && changes.blockLogs) {
        updateUI();
    }
});

// Sanitize Tab Logic
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const sanitizeBtn = document.getElementById('sanitizeBtn');
const fileNameDisplay = document.getElementById('fileNameDisplay');
const resultDiv = document.getElementById('sanitizeResult');

let selectedFile = null;

uploadArea.addEventListener('click', () => fileInput.click());

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
        handleFileSelection(e.dataTransfer.files[0]);
    }
});

fileInput.addEventListener('change', () => {
    if (fileInput.files.length) {
        handleFileSelection(fileInput.files[0]);
    }
});

function handleFileSelection(file) {
    selectedFile = file;
    fileNameDisplay.innerText = file.name;
    fileNameDisplay.style.color = 'var(--text)';
    sanitizeBtn.style.display = 'block';
    resultDiv.style.display = 'none';

    const dragContainer = document.getElementById('dragContainer');
    if (dragContainer) dragContainer.style.display = 'none';

    // Allowed sizes & types check
    const allowedTypes = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff'];
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (!allowedTypes.includes(ext)) {
        showResult('Unsupported file type. Use PDF, PNG, or JPG.', 'error');
        sanitizeBtn.disabled = true;
    } else {
        sanitizeBtn.disabled = false;
    }
}

function showResult(message, type) {
    resultDiv.textContent = message;
    resultDiv.className = type; // 'success' or 'error'
    resultDiv.style.display = 'block';
}

sanitizeBtn.addEventListener('click', async () => {
    if (!selectedFile) return;

    // Loading state
    sanitizeBtn.disabled = true;
    sanitizeBtn.innerText = 'Sanitizing...';
    showResult('Processing and redacting document...', 'success');

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('policy', 'default_policy');

    try {
        const response = await fetch('http://127.0.0.1:8000/api/v1/process', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            let errorMsg = 'Failed to connect to Background Core';
            try {
                const errPayload = await response.json();
                errorMsg = errPayload.detail || errorMsg;
            } catch (e) { }
            throw new Error(errorMsg);
        }

        const result = await response.json();

        const preferredType = result.signed_path ? 'signed' : 'sanitized';
        const downloadUrl = `http://127.0.0.1:8000/api/v1/documents/${result.document_id}/download?type=${preferredType}`;

        showResult(`Sanitization complete. Neutralized ${result.entities_redacted} risks. Downloading...`, 'success');

        if (!chrome.runtime || !chrome.runtime.sendMessage) {
            throw new Error("Extension updated. Please refresh the web page to reconnect.");
        }

        // Log the authorized action so metrics increment
        chrome.runtime.sendMessage({
            action: 'LOG_ALLOWED',
            details: {
                filename: selectedFile.name,
                url: 'Extension UI',
                reason: 'Sanitized'
            }
        });

        // Let the background script download it, since chrome.downloads works broadly in background
        chrome.runtime.sendMessage({
            action: 'DOWNLOAD_SANITIZED',
            details: { url: downloadUrl, filename: `Sanitized_${selectedFile.name}` }
        });

        // Send the file to the parent window to render native auto-attach UI
        try {
            const fileRes = await fetch(downloadUrl);
            const blob = await fileRes.blob();
            const downloadFilename = `Sanitized_${selectedFile.name}`;

            const reader = new FileReader();
            reader.readAsDataURL(blob);
            reader.onloadend = () => {
                const dataUrl = reader.result;
                // Tell the parent window the file is ready to be dragged natively
                window.parent.postMessage({
                    action: 'EDGE_POLICY_FILE_READY',
                    payload: {
                        filename: downloadFilename,
                        dataUrl: dataUrl
                    }
                }, '*');
            };
        } catch (err) {
            console.warn("Failed to prepare native drag file:", err);
        }

    } catch (error) {
        console.error(error);
        showResult(error.message, 'error');
    } finally {
        sanitizeBtn.disabled = false;
        sanitizeBtn.innerText = 'Sanitize & Download';
        // Allow selecting the same file again if needed
        fileInput.value = '';
    }
});

// Auto-Populate Listener from Content Script Acknowledge Button
window.addEventListener('message', async (event) => {
    if (event.data && event.data.action === 'EDGE_POLICY_AUTO_POPULATE') {
        const { filename, dataUrl } = event.data.payload;
        try {
            const res = await fetch(dataUrl);
            const blob = await res.blob();
            const populatedFile = new File([blob], filename, { type: blob.type || 'application/pdf' });

            // Switch to process document tab manually
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

            const processBtn = document.querySelector('.tab-btn[data-target="sanitize-tab"]');
            if (processBtn) processBtn.classList.add('active');

            const processView = document.getElementById('sanitize-tab');
            if (processView) processView.classList.add('active');

            // Forward file to the standard dropzone handler
            handleFileSelection(populatedFile);
        } catch (err) {
            console.error("Failed to auto-populate file:", err);
        }
    }
});
