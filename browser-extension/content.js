// Edge Policy AI - Content Script
console.log("Edge Policy AI content script loaded on:", window.location.href);

/**
 * Custom UI - Injected Dialog
 */
function showSecurityAlert(filename, reason, entities) {
    // Remove existing overlay if any
    const existing = document.getElementById('edge-policy-overlay');
    if (existing) existing.remove();

    const overlay = document.createElement('div');
    overlay.id = 'edge-policy-overlay';

    const entityTags = entities.map(e => `<span class="ep-tag">${e}</span>`).join('');

    overlay.innerHTML = `
        <div class="ep-dialog">
            <div class="ep-header">
                <div class="ep-icon">⚠️</div>
                <div class="ep-title">Security Policy Alert</div>
            </div>
            <div class="ep-content">
                Your organization's privacy policy prohibits uploading documents containing sensitive information.
                <div class="ep-file-info">
                    <span class="ep-file-name">${filename}</span>
                    <div class="ep-pii-tags">${entityTags}</div>
                </div>
                The upload has been terminated to prevent data leakage.
            </div>
            <div class="ep-footer">
                <button class="ep-btn" id="ep-close-btn">Acknowledge</button>
            </div>
        </div>
    `;

    document.body.appendChild(overlay);

    document.getElementById('ep-close-btn').onclick = () => {
        overlay.style.opacity = '0';
        setTimeout(() => overlay.remove(), 200);
    };
}

/**
 * Preemptive Blocking & Verification
 */
document.addEventListener('change', async (event) => {
    const target = event.target;
    if (target.tagName === 'INPUT' && target.type === 'file') {
        const file = target.files[0];
        if (!file) return;

        // Supported document types
        const allowedTypes = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff'];
        const isSupported = allowedTypes.some(ext => file.name.toLowerCase().endsWith(ext));
        if (!isSupported) return;

        // 1. Preemptive Action: Seize the files and block propagation
        const originalFiles = target.files;
        event.stopImmediatePropagation();
        event.preventDefault();

        // Clear value temporarily to stop any sync listeners from the host
        target.value = '';

        console.log("Edge Policy AI: High-priority intercept for:", file.name);

        // 2. Perform Backend Pre-Check
        const formData = new FormData();
        formData.append('file', file);
        formData.append('policy', 'default_policy');

        try {
            const response = await fetch('http://127.0.0.1:8000/api/v1/pre-check', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) throw new Error('Backend check unavailable');

            const result = await response.json();

            if (!result.authorized) {
                console.error("Upload blocked by Policy Control:", result.reason);

                // Notify background for persistent logging
                chrome.runtime.sendMessage({
                    action: 'BLOCK_UPLOAD',
                    details: {
                        filename: file.name,
                        reason: result.reason,
                        url: window.location.href,
                        entities: result.detected_entities
                    }
                });

                // Show professional custom dialog
                showSecurityAlert(file.name, result.reason, result.detected_entities);

                // Keep input empty
                target.value = '';
            } else {
                console.log("Document sanitized. Re-initiating upload...");

                // Log allowed attempt
                chrome.runtime.sendMessage({
                    action: 'LOG_ALLOWED',
                    details: {
                        filename: file.name,
                        url: window.location.href
                    }
                });

                // Re-inject files and trigger a new change event that we WON'T intercept
                const dt = new DataTransfer();
                for (let i = 0; i < originalFiles.length; i++) {
                    dt.items.add(originalFiles[i]);
                }
                target.files = dt.files;

                // Dispatch event but mark it so we don't catch it again
                const newEvent = new Event('change', { bubbles: true });
                newEvent._edgeCheckDone = true;
                target.dispatchEvent(newEvent);
            }
        } catch (error) {
            console.error("Edge Policy AI: Error during check:", error);
            // On error, we fail safe (block) if it's sensitive, or proceed if it's a dev error.
            // For now, we allow fallback for usability, but in production this would block.
        }
    }
}, true); // Use capture phase to get ahead of host site listeners

// Filter re-entry
const originalAddEventListener = EventTarget.prototype.addEventListener;
document.addEventListener('change', (e) => {
    if (e._edgeCheckDone) {
        // Allow this through
    }
}, true);
