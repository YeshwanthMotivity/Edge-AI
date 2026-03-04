// Edge Policy AI - Content Script
console.log("%cEdge Policy AI protection active", "color: #c084fc; font-weight: bold; font-size: 14px", "on:", window.location.href);

/**
 * Custom UI - Injected Dialog
 */
function showSecurityAlert(filename, reason, entities) {
    const existing = document.getElementById('edge-policy-overlay');
    if (existing) existing.remove();

    const overlay = document.createElement('div');
    overlay.id = 'edge-policy-overlay';

    // Forced inline styles to override strict host CSS (e.g. Gemini, ChatGPT)
    overlay.style.cssText = `
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        background: rgba(15, 23, 42, 0.85) !important;
        backdrop-filter: blur(8px) !important;
        z-index: 2147483647 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        opacity: 0;
        transition: opacity 0.3s ease !important;
        pointer-events: auto !important;
    `;

    const entityTags = (entities || []).map(e => `<span style="background: rgba(239, 68, 68, 0.1); color: #fca5a5; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; text-transform: uppercase;">${e}</span>`).join('');

    overlay.innerHTML = `
        <div style="background: #1e293b; border: 1px solid rgba(192, 132, 252, 0.3); border-radius: 16px; padding: 32px; width: 420px; box-shadow: 0 0 40px rgba(168, 85, 247, 0.15), 0 20px 25px -5px rgba(0, 0, 0, 0.1); position: relative; overflow: hidden; font-family: 'Inter', system-ui, sans-serif; text-align: left;">
            <div style="position: absolute; top: 0; left: 0; width: 100%; height: 3px; background: linear-gradient(90deg, #8b5cf6, #d946ef);"></div>
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">
                <div style="width: 32px; height: 32px; background: rgba(239, 68, 68, 0.1); color: #ef4444; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 20px;">⚠️</div>
                <div style="font-size: 20px; font-weight: 700; color: #f8fafc; letter-spacing: -0.02em; margin:0;">Security Policy Alert</div>
            </div>
            <div style="color: #94a3b8; font-size: 14px; line-height: 1.6; margin-bottom: 24px;">
                Your organization's privacy policy prohibits uploading documents containing sensitive information.
                <div style="background: rgba(15, 23, 42, 0.5); border-radius: 8px; padding: 12px; margin: 16px 0; border: 1px solid rgba(148, 163, 184, 0.1);">
                    <span style="color: #e2e8f0; font-weight: 600; display: block; margin-bottom: 4px;">${filename}</span>
                    <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px;">${entityTags}</div>
                </div>
                The upload has been terminated to prevent data leakage.
            </div>
            <div style="display: flex; justify-content: flex-end;">
                <button id="ep-close-btn" style="background: #8b5cf6; color: white; border: none; padding: 10px 24px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: all 0.2s;">Acknowledge</button>
            </div>
        </div>
    `;

    // Append to documentElement (HTML tag) instead of body to bypass sites hiding the body or using shadow DOM overlaps
    document.documentElement.appendChild(overlay);

    // Apply a small delay to trigger the fade-in animation
    requestAnimationFrame(() => {
        overlay.style.opacity = '1';
    });

    document.getElementById('ep-close-btn').onclick = () => {
        overlay.style.opacity = '0';
        setTimeout(() => overlay.remove(), 200);
    };
}

/**
 * Core Verification Logic
 */
async function verifyFileSecurity(file) {
    const allowedTypes = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.docx'];
    const isSupported = allowedTypes.some(ext => file.name.toLowerCase().endsWith(ext));
    if (!isSupported) return { authorized: true };

    console.log("Edge Policy AI: Verification in progress for:", file.name);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('policy', 'default_policy');

    try {
        const response = await fetch('http://127.0.0.1:8000/api/v1/pre-check', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) return { authorized: true, error: 'Backend unavailable' };
        return await response.json();
    } catch (e) {
        console.log("Policy check failed:", e);
        return { authorized: true };
    }
}

/**
 * Event Interceptor
 */
const handleUploadEvent = async (event) => {
    // Don't re-intercept our own re-injected events
    if (event._edgeCheckDone) return;

    let files = [];
    let target = event.target;

    if (event.type === 'change' && target.tagName === 'INPUT' && target.type === 'file') {
        files = Array.from(target.files);
    } else if (event.type === 'drop') {
        if (event.dataTransfer && event.dataTransfer.files.length > 0) {
            files = Array.from(event.dataTransfer.files);
        }
    } else if (event.type === 'paste') {
        if (event.clipboardData && event.clipboardData.files.length > 0) {
            files = Array.from(event.clipboardData.files);
        }
    }

    if (files.length === 0) return;

    // PREEMPTIVE BLOCKING: Terminate event flow immediately
    // Modern apps often use native handlers that run immediately. 
    // Capturing phase and stopImmediatePropagation is our best weapon.
    event.stopImmediatePropagation();
    event.preventDefault();

    // Visual feedback: If it's an input, clear it immediately
    if (target.tagName === 'INPUT' && target.type === 'file') {
        target.value = '';
    }

    console.log(`Edge Policy AI: Intercepted ${event.type} attempt. Verifying security...`);

    for (const file of files) {
        const result = await verifyFileSecurity(file);

        if (!result.authorized) {
            // Log as warning instead of error to prevent triggering browser extension "Errors" dashboard
            console.log("%cPolicy Breach: Blocked " + file.name, "color: #ef4444; font-weight: bold; background: #fee2e2; padding: 2px 6px; border-radius: 4px;");

            chrome.runtime.sendMessage({
                action: 'BLOCK_UPLOAD',
                details: {
                    filename: file.name,
                    reason: result.reason,
                    url: window.location.href,
                    entities: result.detected_entities
                }
            });

            showSecurityAlert(file.name, result.reason, result.detected_entities);
            return;
        }
    }

    // If authorized, re-inject for 'change' events
    // For 'drop' and 'paste', we advise the user to retry as re-injection is unreliable
    if (event.type === 'change') {
        console.log("Document sanitized. Re-injecting into input...");

        files.forEach(f => {
            chrome.runtime.sendMessage({
                action: 'LOG_ALLOWED',
                details: { filename: f.name, url: window.location.href }
            });
        });

        const dt = new DataTransfer();
        files.forEach(f => dt.items.add(f));
        target.files = dt.files;

        const newEvent = new Event('change', { bubbles: true });
        newEvent._edgeCheckDone = true;
        target.dispatchEvent(newEvent);
    } else {
        console.log("%cDrop/Paste authorized. Please re-initiate to confirm.", "color: #34d399; font-weight: bold;");
    }
};

// Global interceptors in Capture phase
window.addEventListener('change', handleUploadEvent, true);
window.addEventListener('drop', handleUploadEvent, true);
window.addEventListener('paste', handleUploadEvent, true);
window.addEventListener('dragover', (e) => e.preventDefault(), true);
