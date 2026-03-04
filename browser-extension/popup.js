function updateUI() {
    chrome.storage.local.get(['blockLogs'], (result) => {
        const logs = result.blockLogs || [];
        const container = document.getElementById('logList');

        let blocked = 0;
        let allowed = 0;

        if (logs.length > 0) {
            container.innerHTML = '';
            logs.forEach(log => {
                if (log.status === 'BLOCKED') blocked++;
                else allowed++;

                const item = document.createElement('div');
                item.className = `log-item ${log.status}`;

                const date = new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                const site = log.url ? log.url.split('/')[2].replace('www.', '') : 'Unknown';

                item.innerHTML = `
                    <div class="log-meta">
                        <span>${date} • ${site}</span>
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

        // Reset badge
        chrome.action.setBadgeText({ text: '' });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    updateUI();
    // Live update if storage changes
    chrome.storage.onChanged.addListener(updateUI);
});
