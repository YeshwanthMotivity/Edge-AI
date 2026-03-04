// Edge Policy AI - Background Service Worker
console.log("Edge Policy AI background worker active.");

// Handle events from content scripts (e.g., blocked uploads)
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'BLOCK_UPLOAD') {
        const { filename, reason, url, entities } = message.details;

        console.warn(`[SECURITY EVENT] Blocked upload of ${filename} on ${url}`);

        // Visual indicator on extension icon
        chrome.action.setBadgeText({ text: '!' });
        chrome.action.setBadgeBackgroundColor({ color: '#ef4444' });

        // System-level notification
        chrome.notifications.create({
            type: 'basic',
            iconUrl: 'public/icon128.png',
            title: 'Security Policy Enforcement',
            message: `Upload of ${filename} was blocked due to sensitive data: ${entities.join(', ')}`,
            priority: 2
        });

        // Persistent logging in local storage
        const logEntry = {
            timestamp: new Date().toISOString(),
            action: 'BLOCK',
            filename,
            reason,
            url,
            entities,
            user: 'local_dev_user'
        };

        chrome.storage.local.get(['blockLogs'], (result) => {
            const logs = result.blockLogs || [];
            logs.unshift(logEntry);
            // Keep only latest 50 logs
            chrome.storage.local.set({ blockLogs: logs.slice(0, 50) });
        });
    }
});

