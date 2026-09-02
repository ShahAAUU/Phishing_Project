const API_BASE = "http://localhost:5000";

async function checkApiHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(2500) });
    const data = await res.json();
    return data.status === "ok";
  } catch { return false; }
}

async function predictUrl(url) {
  const res = await fetch(`${API_BASE}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
    signal: AbortSignal.timeout(6000),
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

function getCurrentTabUrl() {
  return new Promise(resolve => {
    chrome.tabs.query({ active: true, currentWindow: true }, tabs => {
      resolve(tabs[0]?.url || "");
    });
  });
}

function showLoading() {
  const card = document.getElementById("resultCard");
  card.className = "result-card loading";
  card.innerHTML = `
    <div class="spinner"></div>
    <div class="result-title" style="color:#94a3b8">Analyzing...</div>
    <div class="result-sub">Contacting detection API</div>`;
  document.getElementById("confSection").style.display  = "none";
  document.getElementById("flagsSection").style.display = "none";
}

function showResult(data) {
  const card       = document.getElementById("resultCard");
  const isPhishing = data.is_phishing;
  const conf       = Math.round(data.confidence);
  const flags      = data.flags || [];

  if (isPhishing) {
    card.className = "result-card danger";
    card.innerHTML = `
      <div class="result-icon">⚠️</div>
      <div class="result-title">Phishing Detected!</div>
      <div class="result-sub">This site may be trying to steal your data</div>`;
  } else if (conf < 70) {
    card.className = "result-card warning";
    card.innerHTML = `
      <div class="result-icon">⚠️</div>
      <div class="result-title">Suspicious</div>
      <div class="result-sub">Proceed with caution</div>`;
  } else {
    card.className = "result-card safe";
    card.innerHTML = `
      <div class="result-icon">✅</div>
      <div class="result-title">Looks Safe</div>
      <div class="result-sub">No phishing indicators found</div>`;
  }

  const confSection = document.getElementById("confSection");
  const fillClass   = isPhishing ? "danger-fill" : conf < 70 ? "warning-fill" : "safe-fill";
  confSection.style.display = "block";
  document.getElementById("confValue").textContent = `${conf}%`;
  const fill = document.getElementById("confFill");
  fill.className = `conf-bar-fill ${fillClass}`;
  setTimeout(() => { fill.style.width = `${conf}%`; }, 50);

  if (flags.length > 0) {
    const flagsSection = document.getElementById("flagsSection");
    const flagsList    = document.getElementById("flagsList");
    flagsSection.style.display = "block";
    flagsList.innerHTML = flags.map(f =>
      `<div class="flag-item"><div class="flag-dot"></div>${f}</div>`
    ).join('');
  }
  document.getElementById("methodText").textContent = data.method || "";
}

function showError(msg) {
  const card = document.getElementById("resultCard");
  card.className = "result-card loading";
  card.innerHTML = `
    <div class="result-icon">❌</div>
    <div class="result-title" style="color:#f87171">Error</div>
    <div class="result-sub" style="color:#94a3b8">${msg}</div>`;
}

function updateApiStatus(online) {
  const dot  = document.getElementById("statusDot");
  const text = document.getElementById("statusText");
  if (online) {
    dot.className    = "status-dot online";
    text.textContent = "API connected";
  } else {
    dot.className    = "status-dot offline";
    text.textContent = "API offline - start Flask";
  }
}

async function init() {
  const url   = await getCurrentTabUrl();
  const urlEl = document.getElementById("currentUrl");
  urlEl.textContent = url || "Unknown";

  const online = await checkApiHealth();
  updateApiStatus(online);

  document.getElementById("checkBtn").addEventListener("click", async () => {
    const btn = document.getElementById("checkBtn");
    btn.disabled    = true;
    btn.textContent = "Checking...";
    showLoading();
    try {
      const result = await predictUrl(url);
      showResult(result);
    } catch (e) {
      showError("Could not reach API. Is Flask running?");
    } finally {
      btn.disabled    = false;
      btn.textContent = "🔍 Check This Page";
    }
  });

  document.getElementById("scanBtn").addEventListener("click", async () => {
    const input   = document.getElementById("customUrl");
    const scanUrl = input.value.trim();
    if (!scanUrl) return;
    const fullUrl = scanUrl.startsWith("http") ? scanUrl : `https://${scanUrl}`;
    document.getElementById("currentUrl").textContent = fullUrl;
    showLoading();
    try {
      const result = await predictUrl(fullUrl);
      showResult(result);
    } catch (e) {
      showError("Could not reach API. Is Flask running?");
    }
  });

  document.getElementById("customUrl").addEventListener("keydown", e => {
    if (e.key === "Enter") document.getElementById("scanBtn").click();
  });

  if (online && url && (url.startsWith("http://") || url.startsWith("https://"))) {
    document.getElementById("checkBtn").click();
  }
}

init();
