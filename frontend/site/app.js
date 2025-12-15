const services = ["postgres", "redis", "rabbitmq", "backend"]; // legacy reference, not used

// -----------------------------
// Popup (Modal) - reliable UI feedback (EXTENDED)
// -----------------------------
function ensurePopupElements() {
  if (document.getElementById("popup-overlay")) return;

  const overlay = document.createElement("div");
  overlay.id = "popup-overlay";
  overlay.style.position = "fixed";
  overlay.style.left = "0";
  overlay.style.top = "0";
  overlay.style.right = "0";
  overlay.style.bottom = "0";
  overlay.style.display = "none";
  overlay.style.alignItems = "center";
  overlay.style.justifyContent = "center";
  overlay.style.background = "rgba(0,0,0,0.6)";
  overlay.style.zIndex = "9999";

  const box = document.createElement("div");
  box.id = "popup-box";
  box.style.background = "#020617";
  box.style.border = "1px solid #1e293b";
  box.style.color = "#e5e7eb";
  box.style.padding = "18px";
  box.style.borderRadius = "10px";
  box.style.width = "420px";
  box.style.maxWidth = "92vw";
  box.style.boxShadow = "0 10px 30px rgba(0,0,0,0.45)";
  box.style.textAlign = "center";

  const title = document.createElement("div");
  title.id = "popup-title";
  title.style.fontWeight = "bold";
  title.style.fontSize = "18px";
  title.style.marginBottom = "10px";
  title.innerText = "Notification";

  const msg = document.createElement("div");
  msg.id = "popup-message";
  msg.style.fontSize = "14px";
  msg.style.color = "#cbd5e1";
  msg.style.marginBottom = "14px";
  msg.innerHTML = "";

  const btn = document.createElement("button");
  btn.id = "popup-close";
  btn.innerText = "OK";
  btn.style.padding = "10px 18px";
  btn.style.borderRadius = "8px";
  btn.style.cursor = "pointer";
  btn.style.border = "1px solid #334155";
  btn.style.background = "#1e293b";
  btn.style.color = "#e5e7eb";

  btn.addEventListener("click", () => {
    overlay.style.display = "none";
  });

  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) overlay.style.display = "none";
  });

  box.appendChild(title);
  box.appendChild(msg);
  box.appendChild(btn);
  overlay.appendChild(box);
  document.body.appendChild(overlay);
}

/**
 * EXTENDED: supports HTML so we can render lists safely
 */
function showPopup(messageHtml) {
  ensurePopupElements();

  const overlay = document.getElementById("popup-overlay");
  const msg = document.getElementById("popup-message");

  msg.innerHTML = messageHtml;
  overlay.style.display = "flex";

  setTimeout(() => {
    if (overlay) overlay.style.display = "none";
  }, 3000);
}

// -----------------------------
// API helpers
// -----------------------------
async function fetchServices() {
  const res = await fetch("/api/services");
  if (!res.ok) throw new Error(`fetchServices failed: ${res.status}`);
  return res.json();
}

async function fetchLogs(service) {
  const res = await fetch(`/api/logs/${service}`);
  if (!res.ok) throw new Error(`fetchLogs(${service}) failed: ${res.status}`);
  return res.json();
}

async function fetchSystemMetrics() {
  const res = await fetch("/api/system");
  if (!res.ok) throw new Error(`fetchSystemMetrics failed: ${res.status}`);
  return res.json();
}

// -----------------------------
// Actions (EXTENDED)
// -----------------------------
async function action(service, type) {
  const res = await fetch(`/api/${type}/${service}`, { method: "POST" });

  if (!res.ok) {
    showPopup(`Action <b>${type}</b> failed for <b>${service}</b> (HTTP ${res.status})`);
    return;
  }

  if (type === "start") {
    try {
      await new Promise(r => setTimeout(r, 600));
      const servicesState = await fetchServices();
      const s = servicesState[service];

      if (s && s.status === "up") {
        showPopup(`Service <b>${service}</b> was restarted successfully!!`);
      } else {
        showPopup(`Start requested for <b>${service}</b>. Waiting for it to become UP...`);
      }
    } catch (e) {
      showPopup(`Service <b>${service}</b> start requested successfully!!`);
    }
  }
}

/**
 * EXTENDED & FIXED:
 * - Uses HTML entity (&bull;) instead of Unicode bullet
 * - Prevents encoding issues like â€¢
 */
async function runRemediation() {
  const res = await fetch("/api/remediate", { method: "POST" });

  if (!res.ok) {
    showPopup(`Auto-remediation failed (HTTP ${res.status})`);
    return;
  }

  const data = await res.json();
  const remediated = data.services_remediated || [];

  if (remediated.length === 0) {
    showPopup("No services required remediation.");
    return;
  }

  // IMPORTANT: use &bull; instead of Unicode bullet
  const listHtml = remediated
    .map(svc => `&bull; <b>${svc}</b>`)
    .join("<br>");

  showPopup(`
    The following services were restarted successfully:<br><br>
    ${listHtml}
  `);
}

// -----------------------------
// Card builders
// -----------------------------
function createServiceCard(service, status, logs) {
  const ledClass = status.status === "up" ? "up" : "down";

  return `
    <div class="card">
      <h2>
        <span class="led ${ledClass}"></span>
        ${service.toUpperCase()}
      </h2>

      <div class="meta">Status: ${status.status}</div>
      <div class="meta">Started: ${status.started}</div>
      <div class="meta">Recovery: ${status.recovery}</div>

      <div class="buttons">
        <button onclick="action('${service}','ping')">Ping</button>
        <button onclick="action('${service}','start')">Start</button>
        <button onclick="action('${service}','stop')">Stop</button>
      </div>

      <div class="logs" id="logs-${service}">
        ${logs.map(l => `> ${l}`).join("<br>")}
      </div>
    </div>
  `;
}

function createSystemCard(metrics) {
  const cpu = metrics && metrics.cpu ? metrics.cpu : "N/A";
  const ram = metrics && metrics.ram ? metrics.ram : "N/A";
  const disk = metrics && metrics.disk ? metrics.disk : "N/A";

  return `
    <div class="card">
      <h2>SYSTEM METRICS</h2>

      <div class="meta">CPU: ${cpu}</div>
      <div class="meta">RAM: ${ram}</div>
      <div class="meta">FREE DISK: ${disk}</div>

      <div class="logs">
        > Collected from backend host
      </div>
    </div>
  `;
}

function createRemediationCard() {
  return `
    <div class="card">
      <h2>AUTO-REMEDIATION</h2>

      <div class="buttons">
        <button class="auto-remediation-btn" onclick="runRemediation()">AUTO-REMEDIATION</button>
      </div>

      <div class="auto-remediation-text">
        Recover all DOWN services automatically
      </div>
    </div>
  `;
}

// -----------------------------
// Rendering
// -----------------------------
async function render() {
  try {
    const services = await fetchServices();
    const systemMetrics = await fetchSystemMetrics();

    let gridHtml = "";

    gridHtml += createSystemCard(systemMetrics);

    for (const [name, data] of Object.entries(services)) {
      let logs = [];
      try {
        logs = await fetchLogs(name);
      } catch (e) {
        logs = [`Log fetch failed: ${e.message}`];
      }
      gridHtml += createServiceCard(name, data, logs);
    }

    const gridEl = document.getElementById("services");
    if (gridEl) gridEl.innerHTML = gridHtml;

    const footer = document.getElementById("footer-action");
    if (footer) footer.innerHTML = createRemediationCard();
  } catch (e) {
    const gridEl = document.getElementById("services");
    if (gridEl) {
      gridEl.innerHTML = `
        <div class="card">
          <h2>UI ERROR</h2>
          <div class="meta">Failed to load data from backend.</div>
          <div class="logs">> ${e.message}</div>
        </div>
      `;
    }

    const footer = document.getElementById("footer-action");
    if (footer) footer.innerHTML = createRemediationCard();
  }
}

// Polling (unchanged)
setInterval(render, 3000);
render();
