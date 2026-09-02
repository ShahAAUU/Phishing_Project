const API_BASE = "http://localhost:5000";

(async () => {
  const url = window.location.href;
  if (!url.startsWith("http")) return;

  try {
    const res = await fetch(`${API_BASE}/predict`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ url }),
      signal:  AbortSignal.timeout(4000),
    });
    if (!res.ok) return;
    const data = await res.json();
    if (data.is_phishing) showWarningBanner(data);
  } catch { }
})();

function showWarningBanner(data) {
  if (document.getElementById("phishguard-banner")) return;
  const banner = document.createElement("div");
  banner.id = "phishguard-banner";
  banner.style.cssText = `
    position: fixed; top: 0; left: 0; right: 0;
    z-index: 2147483647; background: #7f1d1d;
    color: #fecaca; font-family: sans-serif; font-size: 14px;
    padding: 12px 16px; display: flex; align-items: center; gap: 12px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.4); border-bottom: 2px solid #ef4444;`;
  const conf  = Math.round(data.confidence);
  const flags = (data.flags || []).slice(0, 3).join(" · ");
  banner.innerHTML = `
    <span style="font-size:20px">⚠️</span>
    <div style="flex:1">
      <strong style="color:#f87171;font-size:15px;">PhishGuard Warning: Potential Phishing Site</strong>
      <div style="margin-top:2px;font-size:12px;opacity:.9;">
        Confidence: ${conf}%${flags ? ` · ${flags}` : ""}
      </div>
    </div>
    <button id="phishguard-dismiss" style="
      background:transparent; border:1px solid #ef4444; color:#fca5a5;
      padding:5px 12px; border-radius:6px; cursor:pointer; font-size:12px;">
      Dismiss
    </button>`;
  document.body.prepend(banner);
  document.getElementById("phishguard-dismiss").addEventListener("click", () => banner.remove());
  setTimeout(() => banner.remove(), 15000);
}
