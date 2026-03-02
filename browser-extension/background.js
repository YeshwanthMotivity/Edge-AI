// Edge Policy AI - Background Service Worker
console.log("Edge Policy AI background worker active.");

chrome.runtime.onInstalled.addListener(() => {
    console.log('Extension installed');
});
