// EdgeAI Policy - Content Script
console.log("%cEdgeAI Policy protection active", "color: #c084fc; font-weight: bold; font-size: 14px", "on:", window.location.href);

/**
 * Custom UI - Injected Dialog
 */
function showSecurityAlert(file, reason, entities) {
    const filename = file.name;
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

        // Auto-populate to Process Document tab
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onloadend = () => {
            const dataUrl = reader.result;
            const iframe = document.getElementById('edge-policy-iframe');
            if (iframe && iframe.contentWindow) {
                // Determine if panel is closed by checking opacity, click FAB to open if it is
                if (iframe.style.opacity === '0' || iframe.style.opacity === '') {
                    const fab = document.getElementById('edge-policy-fab');
                    if (fab) fab.click();
                }

                // Send the file over postMessage to the injected panel
                iframe.contentWindow.postMessage({
                    action: 'EDGE_POLICY_AUTO_POPULATE',
                    payload: {
                        filename: filename,
                        dataUrl: dataUrl
                    }
                }, '*');
            }
        };
    };
}

/**
 * Core Verification Logic
 */
async function verifyFileSecurity(file) {
    const allowedTypes = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.docx'];
    const isSupported = allowedTypes.some(ext => file.name.toLowerCase().endsWith(ext));
    if (!isSupported) return { authorized: true };

    console.log("EdgeAI Policy: Verification in progress for:", file.name);

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

    // Allow drops originating from our own panel to pass through naturally
    if (window._isEdgePolicyPanelDrag) return;

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

    console.log(`EdgeAI Policy: Intercepted ${event.type} attempt. Verifying security...`);

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

            showSecurityAlert(file, result.reason, result.detected_entities);
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

/**
 * Injected Side Panel UI
 */
function injectEdgePolicyPanel() {
    if (document.getElementById('edge-policy-fab')) return;

    // 1. Create the Floating Action Button (FAB)
    const fab = document.createElement('div');
    fab.id = 'edge-policy-fab';
    fab.style.cssText = `
        position: fixed !important;
        bottom: 24px !important;
        right: 24px !important;
        width: 48px !important;
        height: 48px !important;
        background: linear-gradient(135deg, #8b5cf6, #c084fc) !important;
        border-radius: 50% !important;
        box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.1) inset !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: pointer !important;
        z-index: 2147483646 !important;
        font-size: 24px !important;
        transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        user-select: none !important;
    `;
    fab.innerHTML = '🛡️';
    fab.title = "EdgeAI Policy";

    fab.addEventListener('mouseenter', () => fab.style.transform = 'scale(1.1)');
    fab.addEventListener('mouseleave', () => fab.style.transform = 'scale(1)');

    // 2. Create the hidden Iframe Container
    const panelContainer = document.createElement('iframe');
    panelContainer.id = 'edge-policy-iframe';
    panelContainer.src = chrome.runtime.getURL('injected-panel.html');
    panelContainer.style.cssText = `
        position: fixed !important;
        top: 24px !important;
        right: 24px !important;
        width: 380px !important;
        height: calc(100vh - 100px) !important;
        max-height: 800px !important;
        border: 1px solid rgba(192, 132, 252, 0.3) !important;
        border-radius: 16px !important;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.05) inset !important;
        z-index: 2147483647 !important;
        background: transparent !important;
        pointer-events: none !important;
        opacity: 0 !important;
        transform: translateX(120%) !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
        color-scheme: dark !important;
    `;

    document.documentElement.appendChild(fab);
    document.documentElement.appendChild(panelContainer);

    let isOpen = false;

    // 3. Toggle Logic
    const togglePanel = () => {
        isOpen = !isOpen;
        if (isOpen) {
            panelContainer.style.pointerEvents = 'auto';
            panelContainer.style.opacity = '1';
            panelContainer.style.transform = 'translateX(0)';
            fab.style.boxShadow = '0 0 20px rgba(192, 132, 252, 0.8)';
        } else {
            panelContainer.style.pointerEvents = 'none';
            panelContainer.style.opacity = '0';
            panelContainer.style.transform = 'translateX(120%)';
            fab.style.boxShadow = '0 4px 12px rgba(139, 92, 246, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.1) inset';
        }
    };

    fab.addEventListener('click', togglePanel);


    // 4. Listen for close message from the iframe or file ready
    window.addEventListener('message', (event) => {
        if (event.data && event.data.action === 'EDGE_POLICY_CLOSE_PANEL') {
            if (isOpen) togglePanel();
        } else if (event.data && event.data.action === 'EDGE_POLICY_FILE_READY') {
            const fileData = event.data.payload;
            if (!fileData) return;

            // Remove existing widget if any
            let existingWidget = document.getElementById('edge-policy-drag-widget');
            if (existingWidget) existingWidget.remove();

            const widget = document.createElement('div');
            widget.id = 'edge-policy-drag-widget';
            widget.style.cssText = `
                position: fixed !important;
                bottom: 24px !important;
                right: 90px !important;
                background: #1e293b !important;
                border: 1px solid rgba(52, 211, 153, 0.4) !important;
                border-radius: 12px !important;
                padding: 16px 20px !important;
                min-height: 60px !important;
                box-shadow: 0 10px 25px rgba(0,0,0,0.5), 0 0 0 1px rgba(52, 211, 153, 0.1) inset !important;
                display: flex !important;
                align-items: center !important;
                gap: 16px !important;
                z-index: 2147483647 !important;
                font-family: 'Inter', system-ui, sans-serif !important;
                line-height: 1.4 !important;
                transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
                user-select: none !important;
                color-scheme: dark !important;
            `;

            widget.innerHTML = `
                <div id="ep-widget-attach" style="display: flex; align-items: center; justify-content: flex-start; gap: 12px; cursor: pointer; flex-grow: 1; padding: 4px; border-radius: 8px; transition: background 0.2s;" title="Click to instantly attach to chat">
                    <div style="font-size: 24px;">📄</div>
                    <div style="display: flex; flex-direction: column;">
                        <span id="ep-widget-filename" style="font-size: 14px; font-weight: 600; color: #f8fafc; max-width: 180px; white-space: nowrap; text-overflow: ellipsis; overflow: hidden;">${fileData.filename}</span>
                    </div>
                </div>
                <div id="ep-widget-close" style="margin-left: 8px; font-size: 14px; color: #94a3b8; cursor: pointer; padding: 8px; transition: color 0.2s;">✕</div>
            `;

            document.documentElement.appendChild(widget);

            // Close button hover
            const closeBtn = widget.querySelector('#ep-widget-close');
            closeBtn.addEventListener('mouseenter', () => closeBtn.style.color = '#f8fafc');
            closeBtn.addEventListener('mouseleave', () => closeBtn.style.color = '#94a3b8');
            closeBtn.addEventListener('click', () => widget.remove());

            // Auto Attach button hover & click
            const attachBtn = widget.querySelector('#ep-widget-attach');
            const filenameText = widget.querySelector('#ep-widget-filename');

            attachBtn.addEventListener('mouseenter', () => {
                attachBtn.style.background = 'rgba(255, 255, 255, 0.05)';
            });
            attachBtn.addEventListener('mouseleave', () => {
                attachBtn.style.background = 'transparent';
            });

            let isAttached = false;
            attachBtn.addEventListener('click', () => {
                if (!cachedFile || isAttached) return;

                const dt = new DataTransfer();
                dt.items.add(cachedFile);

                // ChatGPT has multiple hidden inputs (e.g., Profile Picture uploader vs Chat attachments).
                // Grabbing the first one can hang the chat if it targets the settings Avatar uploader!
                // Safest approach: Find prompt area first, fallback to the LAST file input on the page.
                let fileInput = null;
                const promptArea = document.querySelector('textarea#prompt-textarea') || document.querySelector('textarea');

                if (promptArea) {
                    const form = promptArea.closest('form');
                    if (form) fileInput = form.querySelector('input[type="file"]');
                }

                if (!fileInput) {
                    const allInputs = Array.from(document.querySelectorAll('input[type="file"]'));
                    // Discard obvious image-only inputs
                    const documentInputs = allInputs.filter(inp => !inp.accept || !inp.accept.includes('image/'));
                    fileInput = documentInputs.pop() || allInputs.pop();
                }

                if (fileInput) {
                    isAttached = true;
                    fileInput.files = dt.files;
                    const changeEvent = new Event('change', { bubbles: true });
                    changeEvent._edgeCheckDone = true;
                    fileInput.dispatchEvent(changeEvent);

                    filenameText.innerText = 'Uploaded ✓';
                    filenameText.style.color = '#34d399';

                    setTimeout(() => {
                        widget.style.opacity = '0';
                        setTimeout(() => {
                            widget.remove();
                            if (isOpen) togglePanel();
                        }, 300);
                    }, 1000);
                } else {
                    filenameText.innerText = 'Input Not Found';
                    filenameText.style.color = '#f87171';
                }
            });

            // Hover effects for the whole widget
            widget.addEventListener('mouseenter', () => widget.style.transform = 'scale(1.02)');
            widget.addEventListener('mouseleave', () => widget.style.transform = 'scale(1)');

            // Pre-fetch the file for instant attach
            let cachedFile = null;
            fetch(fileData.dataUrl)
                .then(res => res.blob())
                .then(blob => {
                    cachedFile = new File([blob], fileData.filename, { type: 'application/pdf' });
                });
        }
    });
}

// Ensure the panel is injected when the DOM is ready, or immediately if already loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectEdgePolicyPanel);
} else {
    injectEdgePolicyPanel();
}
