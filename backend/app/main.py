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
# UI-visible log categories (ADDED)
# Only these will be shown in service windows
# -----------------------------
UI_LOG_TYPES = {
    "ACTION_PING",
    "ACTION_START",
    "ACTION_STOP",
    "ACTION_REMEDIATE"
}

# -----------------------------
# In-memory service state
# (authoritative state for UI)
# -----------------------------
SERVICES = {
    "postgres": {
        "status": "up",
        "started": datetime.utcnow().isoformat(),
        "recovery": "auto-remediator (idle)"
    },
    "redis": {
        "status": "up",
        "started": datetime.utcnow().isoformat(),
        "recovery": "auto-remediator (idle)"
    },
    "rabbitmq": {
        "status": "up",
        "started": datetime.utcnow().isoformat(),
        "recovery": "auto-remediator (idle)"
    },
    "backend": {
        "status": "up",
        "started": datetime.utcnow().isoformat(),
        "recovery": "self"
    },

    # -----------------------------
    # Added platform services (UI windows)
    # -----------------------------
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

    # Observability services
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
# (last 20 lines – extended internally)
# -----------------------------
LOGS = {service: [] for service in SERVICES}


# -----------------------------
# Helper functions
# -----------------------------
def log(service: str, message: str, log_type: str = "INFO"):
    """
    Extended logger (backward compatible).
    - Old calls still work (default INFO)
    - Operator actions are tagged with ACTION_*
    """
    ts = datetime.utcnow().isoformat()

    entry = {
        "timestamp": ts,
        "type": log_type,
        "message": message
    }

    LOGS[service].append(entry)
    LOGS[service] = LOGS[service][-50:]


def ensure_service(service: str):
    if service not in SERVICES:
        raise HTTPException(status_code=404, detail="Unknown service")


def get_system_metrics():
    # CPU
    cpu_units = psutil.cpu_count(logical=True)
    cpu_percent = psutil.cpu_percent(interval=0.3)
    cpu_free = round(100 - cpu_percent, 1)

    # RAM
    mem = psutil.virtual_memory()
    ram_total = round(mem.total / (1024 ** 3), 2)
    ram_free = round(mem.available / (1024 ** 3), 2)

    # DISK
    disk = shutil.disk_usage("/")
    disk_total = round(disk.total / (1024 ** 3), 2)
    disk_free = round(disk.free / (1024 ** 3), 2)

    return {
        "cpu": f"{cpu_units} units, {cpu_free}% free",
        "ram": f"{ram_total} GB total, {ram_free} GB free",
        "disk": f"{disk_total} GB total, {disk_free} GB free"
    }


# -----------------------------
# Remediation helpers (EXISTING + TAGGING)
# -----------------------------
def _set_recovery_state(service: str, state: str):
    if service in SERVICES:
        if "auto-remediator" in SERVICES[service].get("recovery", ""):
            SERVICES[service]["recovery"] = state


def remediate_service(service: str):
    ensure_service(service)

    if SERVICES[service]["status"] != "down":
        log(service, "Auto-remediation skipped (service already UP)")
        return False

    _set_recovery_state(service, "auto-remediator (running)")
    log(service, "Auto-remediation started", "ACTION_REMEDIATE")

    SERVICES[service]["status"] = "up"
    SERVICES[service]["started"] = datetime.utcnow().isoformat()
    set_status(service, "up")

    publish(f"{service} auto-remediated")
    log(service, "Auto-remediation completed", "ACTION_REMEDIATE")

    _set_recovery_state(service, "auto-remediator (idle)")
    return True


# -----------------------------
# API Endpoints
# -----------------------------
@app.get("/status")
def get_status_all():
    REQUESTS.labels(endpoint="/status").inc()
    return SERVICES


@app.get("/services")
def get_services():
    REQUESTS.labels(endpoint="/services").inc()
    return SERVICES


@app.get("/logs/{service}")
def get_logs(service: str):
    REQUESTS.labels(endpoint="/logs").inc()
    ensure_service(service)

    filtered_logs = []

    for entry in LOGS[service]:
        if isinstance(entry, dict) and entry.get("type") in UI_LOG_TYPES:
            filtered_logs.append(f"{entry['timestamp']} | {entry['message']}")

    return filtered_logs


@app.get("/system")
def system_metrics():
    REQUESTS.labels(endpoint="/system").inc()
    return get_system_metrics()


@app.post("/ping/{service}")
def ping_service(service: str):
    REQUESTS.labels(endpoint="/ping").inc()
    ensure_service(service)

    log(service, "Ping succeeded", "ACTION_PING")
    return {"service": service, "ping": "ok"}


@app.post("/stop/{service}")
def stop_service(service: str):
    REQUESTS.labels(endpoint="/stop").inc()
    ensure_service(service)

    SERVICES[service]["status"] = "down"
    set_status(service, "down")

    log(service, "Service stopped manually", "ACTION_STOP")
    publish(f"{service} stopped")

    return {"service": service, "status": "down"}


@app.post("/start/{service}")
def start_service(service: str):
    REQUESTS.labels(endpoint="/start").inc()
    ensure_service(service)

    SERVICES[service]["status"] = "up"
    SERVICES[service]["started"] = datetime.utcnow().isoformat()
    set_status(service, "up")

    log(service, "Service started manually", "ACTION_START")
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


@app.post("/remediate")
def run_remediation():
    REQUESTS.labels(endpoint="/remediate").inc()

    remediated = []
    skipped = []

    for service in SERVICES.keys():
        if SERVICES[service]["status"] == "down":
            ok = remediate_service(service)
            if ok:
                remediated.append(service)
            else:
                skipped.append(service)

    log(
        "backend",
        f"Remediation triggered. Remediated={remediated} Skipped={skipped}",
        "ACTION_REMEDIATE"
    )

    return {
        "status": "completed",
        "services_remediated": remediated,
        "services_skipped": skipped
    }


@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    return generate_latest()
