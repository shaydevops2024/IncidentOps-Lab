from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from datetime import datetime
from prometheus_client import Counter, generate_latest

from .cache import set_status, get_status
from .mq import publish
import psutil
import shutil

app = FastAPI(title="IncidentOps Arena Backend")

# -----------------------------
# Prometheus Metrics
# -----------------------------
REQUESTS = Counter(
    "incidentops_api_requests_total",
    "Total API requests",
    ["endpoint"]
)

# -----------------------------
# In-memory service state
# (authoritative state for UI)
# -----------------------------
SERVICES = {
    # Core platform
    "backend": {
        "status": "up",
        "started": datetime.utcnow().isoformat(),
        "recovery": "self"
    },
    "worker": {
        "status": "up",
        "started": datetime.utcnow().isoformat(),
        "recovery": "manual"
    },
    "chaos": {
        "status": "up",
        "started": datetime.utcnow().isoformat(),
        "recovery": "manual"
    },
    "remediator": {
        "status": "up",
        "started": datetime.utcnow().isoformat(),
        "recovery": "manual"
    },

    # Data & messaging
    "postgres": {
        "status": "up",
        "started": datetime.utcnow().isoformat(),
        "recovery": "auto-remediator"
    },
    "redis": {
        "status": "up",
        "started": datetime.utcnow().isoformat(),
        "recovery": "auto-remediator"
    },
    "rabbitmq": {
        "status": "up",
        "started": datetime.utcnow().isoformat(),
        "recovery": "auto-remediator"
    },

    # Observability
    "prometheus": {
        "status": "up",
        "started": datetime.utcnow().isoformat(),
        "recovery": "manual"
    },
    "grafana": {
        "status": "up",
        "started": datetime.utcnow().isoformat(),
        "recovery": "manual"
    },
    "loki": {
        "status": "up",
        "started": datetime.utcnow().isoformat(),
        "recovery": "manual"
    },
    "promtail": {
        "status": "up",
        "started": datetime.utcnow().isoformat(),
        "recovery": "manual"
    }
}

# -----------------------------
# In-memory logs per service
# (last 20 lines per service)
# -----------------------------
LOGS = {service: [] for service in SERVICES}


# -----------------------------
# Helper functions
# -----------------------------
def log(service: str, message: str):
    ts = datetime.utcnow().isoformat()
    LOGS[service].append(f"{ts} | {message}")
    LOGS[service] = LOGS[service][-20:]


def ensure_service(service: str):
    if service not in SERVICES:
        raise HTTPException(status_code=404, detail="Unknown service")

def get_system_metrics():
    # CPU
    cpu_count = psutil.cpu_count(logical=True)
    cpu_percent = psutil.cpu_percent(interval=0.5)

    # RAM
    mem = psutil.virtual_memory()
    ram_total_gb = round(mem.total / (1024 ** 3), 2)
    ram_free_gb = round(mem.available / (1024 ** 3), 2)

    # Disk (root filesystem)
    disk = shutil.disk_usage("/")
    disk_total_gb = round(disk.total / (1024 ** 3), 2)
    disk_free_gb = round(disk.free / (1024 ** 3), 2)

    return {
        "cpu": f"{cpu_count} units, {100 - cpu_percent:.1f}% free",
        "ram": f"{ram_total_gb} GB total, {ram_free_gb} GB free",
        "disk": f"{disk_total_gb} GB total, {disk_free_gb} GB free"
    }



# -----------------------------
# API Endpoints
# -----------------------------

@app.get("/status")
def get_status_all():
    """
    Backward-compatible endpoint.
    Existing UI calls still work.
    """
    REQUESTS.labels(endpoint="/status").inc()
    return SERVICES


@app.get("/services")
def get_services():
    """
    New endpoint for dynamic UI discovery.
    """
    REQUESTS.labels(endpoint="/services").inc()
    return SERVICES


@app.get("/logs/{service}")
def get_logs(service: str):
    REQUESTS.labels(endpoint="/logs").inc()
    ensure_service(service)
    return LOGS[service]


@app.post("/ping/{service}")
def ping_service(service: str):
    REQUESTS.labels(endpoint="/ping").inc()
    ensure_service(service)

    log(service, "Ping requested")

    if SERVICES[service]["status"] == "up":
        log(service, "Service reachable")
    else:
        log(service, "Service unreachable")

    return {"service": service, "ping": "ok"}


@app.post("/stop/{service}")
def stop_service(service: str):
    REQUESTS.labels(endpoint="/stop").inc()
    ensure_service(service)

    SERVICES[service]["status"] = "down"
    set_status(service, "down")

    log(service, "Service stopped manually")
    publish(f"{service} stopped")

    return {"service": service, "status": "down"}


@app.post("/start/{service}")
def start_service(service: str):
    REQUESTS.labels(endpoint="/start").inc()
    ensure_service(service)

    SERVICES[service]["status"] = "up"
    SERVICES[service]["started"] = datetime.utcnow().isoformat()
    set_status(service, "up")

    log(service, "Service started manually")
    publish(f"{service} started")

    return {"service": service, "status": "up"}


@app.post("/incident/{service}")
def trigger_incident(service: str):
    REQUESTS.labels(endpoint="/incident").inc()
    ensure_service(service)

    SERVICES[service]["status"] = "down"
    set_status(service, "down")

    log(service, "Incident triggered")
    publish(f"{service} incident triggered")

    return {"service": service, "incident": "triggered"}


@app.post("/resolve/{service}")
def resolve_incident(service: str):
    REQUESTS.labels(endpoint="/resolve").inc()
    ensure_service(service)

    SERVICES[service]["status"] = "up"
    SERVICES[service]["started"] = datetime.utcnow().isoformat()
    set_status(service, "up")

    log(service, "Incident resolved automatically")
    publish(f"{service} incident resolved")

    return {"service": service, "status": "resolved"}


@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    return generate_latest()


@app.get("/system")
def system_metrics():
    REQUESTS.labels(endpoint="/system").inc()
    return get_system_metrics()

