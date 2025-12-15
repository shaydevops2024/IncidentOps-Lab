async function fetchServices() {
  const res = await fetch("/api/services");
  return res.json();
}

async function fetchSystemMetrics() {
  const res = await fetch("/api/system");
  return res.json();
}


async function fetchLogs(service) {
  const res = await fetch(`/api/logs/${service}`);
  return res.json();
}

async function action(service, type) {
  await fetch(`/api/${type}/${service}`, { method: "POST" });
}

function createCard(service, status, logs) {
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

      <div class="logs">
        ${logs.map(l => `> ${l}`).join("<br>")}
      </div>
    </div>
  `;
}

function createSystemCard(metrics) {
  return `
    <div class="card">
      <h2>SYSTEM</h2>

      <div class="meta">CPU: ${metrics.cpu}</div>
      <div class="meta">RAM: ${metrics.ram}</div>
      <div class="meta">FREE DISK: ${metrics.disk}</div>

      <div class="logs">
        > Metrics collected from backend host
      </div>
    </div>
  `;
}


async function render() {
  const services = await fetchServices();
  const system = await fetchSystemMetrics();

  let html = "";

  // System metrics window (FIRST)
  html += createSystemCard(system);

  // Service windows
  for (const [name, data] of Object.entries(services)) {
    const logs = await fetchLogs(name);
    html += createCard(name, data, logs);
  }

  document.getElementById("services").innerHTML = html;
}


setInterval(render, 3000);
render();
