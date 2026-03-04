// Edge Policy AI - Background Service Worker
console.log("Edge Policy AI background worker active.");

// Handle events from content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'DOWNLOAD_SANITIZED') {
        chrome.downloads.download({
            url: message.details.url,
            filename: message.details.filename
        });
        return;
    }

    if (message.action === 'BLOCK_UPLOAD' || message.action === 'LOG_ALLOWED') {
        const details = message.details;
        const isBlock = message.action === 'BLOCK_UPLOAD';

        console.log(`[POLICY] ${isBlock ? 'Blocked' : 'Allowed'} upload: ${details.filename} on ${details.url}`);

        if (isBlock) {
            // Visual indicator on extension icon
            chrome.action.setBadgeText({ text: '!' });
            chrome.action.setBadgeBackgroundColor({ color: '#ef4444' });

            // System-level notification
            chrome.notifications.create({
                type: 'basic',
                iconUrl: 'public/icon128.png',
                title: 'Security Policy Enforcement',
                message: `Upload of ${details.filename} was blocked due to sensitive data.`,
                priority: 2
            });
        }

        // Fetch current user and log
        chrome.storage.local.get(['blockLogs', 'edgePolicyUser'], (result) => {
            const currentUser = result.edgePolicyUser || 'Unauthenticated User';

            const logEntry = {
                id: Date.now(),
                timestamp: new Date().toISOString(),
                status: isBlock ? 'BLOCKED' : 'AUTHORIZED',
                filename: details.filename,
                reason: details.reason || 'Sanitized / Safe',
                url: details.url,
                entities: details.entities || [],
                user: currentUser
            };

            const logs = result.blockLogs || [];
            logs.unshift(logEntry);
            // Keep latest 100 entries
            chrome.storage.local.set({ blockLogs: logs.slice(0, 100) });
        });
    }
});
