const API_BASE = "http://localhost:5000";
const cache    = {};

async function checkUrl(url) {
  if (cache[url]) return cache[url];
  try {
    const res  = await fetch(`${API_BASE}/predict`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ url }),
      signal:  AbortSignal.timeout(5000),
    });
    if (!res.ok) return null;
    const data = cache[url] = await res.json();
    return data;
  } catch { return null; }
}

chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.status !== "complete" || !tab.url) return;
  if (!tab.url.startsWith("http")) return;

  const result = await checkUrl(tab.url);
  if (!result) return;

  if (result.is_phishing) {
    chrome.action.setBadgeText({ tabId, text: "!" });
    chrome.action.setBadgeBackgroundColor({ tabId, color: "#ef4444" });
  } else {
    chrome.action.setBadgeText({ tabId, text: "" });
  }
});
