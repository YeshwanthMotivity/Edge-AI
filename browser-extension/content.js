// Edge Policy AI - Content Script
console.log("Edge Policy AI content script loaded on:", window.location.href);

// Monitor file inputs for potential unauthorized document uploads
document.addEventListener('change', async (event) => {
    const target = event.target;
    if (target.tagName === 'INPUT' && target.type === 'file') {
        const file = target.files[0];
        if (!file) return;

        // Supported document types for real-time scanning
        const allowedTypes = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff'];
        const isSupported = allowedTypes.some(ext => file.name.toLowerCase().endsWith(ext));
        if (!isSupported) return;

        console.log("Edge Policy AI: Intercepted upload attempt for:", file.name);

        // Prepare for backend pre-check
        const formData = new FormData();
        formData.append('file', file);
        formData.append('policy', 'default_policy');

        try {
            const response = await fetch('http://127.0.0.1:8000/api/v1/pre-check', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) throw new Error('Backend check failed');

            const result = await response.json();

            if (!result.authorized) {
                console.error("Upload blocked by Edge Policy AI:", result.reason);

                // Block the upload by clearing the input
                target.value = '';

                // Notify background script to handle global logging and persistence
                chrome.runtime.sendMessage({
                    action: 'BLOCK_UPLOAD',
                    details: {
                        filename: file.name,
                        reason: result.reason,
                        url: window.location.href,
                        entities: result.detected_entities
                    }
                });

                // Immediate visual feedback to user
                alert(`⚠️ SECURITY ALERT: Upload Blocked\n\nFile: ${file.name}\nReason: ${result.reason}\n\nYour organization's privacy policy prohibits uploading documents containing sensitive data.`);
            } else {
                console.log("Upload authorized by Edge Policy AI.");
            }
        } catch (error) {
            console.error("Edge Policy AI security check failed:", error);
            // Default behavior on error: log and proceed (or block if ultra-secure)
        }
    }
}, true);

