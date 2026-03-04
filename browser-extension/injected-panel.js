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
        authTitle.innerText = 'Corporate Sign-In';
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

logoutBtn.addEventListener('click', () => {
    chrome.storage.local.remove(['edgePolicyUser', 'edgePolicyToken'], () => {
        checkAuth();
    });
});

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

        const logs = result.blockLogs || [];
        const container = document.getElementById('logList');

        let blocked = 0;
        let allowed = 0;

        if (logs.length > 0) {
            container.innerHTML = '';
            // For now, show all logs regardless of user, or filter by user?
            // User requested "user activities", let's show all logs but highlight the user
            logs.forEach(log => {
                if (log.status === 'BLOCKED') blocked++;
                else allowed++;

                const item = document.createElement('div');
                item.className = `log-item ${log.status}`;

                const date = new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                const site = log.url ? log.url.split('/')[2].replace('www.', '') : 'Unknown';
                const logUser = log.user || 'Unknown User';

                item.innerHTML = `
                    <div class="log-meta">
                        <span>${date} • ${site} • <span style="color:var(--primary)">${logUser}</span></span>
                        <span class="status-badge">${log.status}</span>
                    </div>
                    <span class="log-filename">${log.filename}</span>
                    <div class="log-info">
                        <span>Action: ${log.status === 'BLOCKED' ? 'Intercepted' : 'Sanitized'}</span>
                    </div>
                `;
                container.appendChild(item);
            });
        }

        document.getElementById('blockedCount').innerText = blocked;
        document.getElementById('allowedCount').innerText = allowed;
    });
}

// Live update if storage changes
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
        const response = await fetch('http://127.0.0.1:8000/api/v1/mask', {
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

        const downloadUrl = `http://127.0.0.1:8000/api/v1/documents/${result.document_id}/download?type=sanitized`;

        showResult(`Sanitization complete. Neutralized ${result.entities_redacted} risks. Downloading...`, 'success');

        // Let the background script download it, since chrome.downloads works broadly in background
        chrome.runtime.sendMessage({
            action: 'DOWNLOAD_SANITIZED',
            details: { url: downloadUrl, filename: `Sanitized_${selectedFile.name}` }
        });

    } catch (error) {
        console.error(error);
        showResult(error.message, 'error');
    } finally {
        sanitizeBtn.disabled = false;
        sanitizeBtn.innerText = 'Sanitize & Download';
    }
});
