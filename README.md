# IncidentOps-Lab

IncidentOps Arena is a hands-on DevOps / Platform Engineering demonstration project that simulates service operations, incidents, observability, and automated remediation through a live operator dashboard.

The project focuses on operational workflows, not just deployment:

- Service health visibility

- Manual & automated recovery

- Action-oriented logging

- System-level metrics

- Observability tooling

- This is designed to resemble an internal SRE / Platform control panel

## Project architecture:

``` bash
.
├── README.md
├── backend
│   ├── Dockerfile
│   ├── app
│   │   ├── __init__.py
│   │   ├── cache.py
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── main.py
│   │   ├── metrics.py
│   │   └── mq.py
│   └── requirements.txt
├── chaos
│   ├── Dockerfile
│   ├── chaos.py
│   └── requirements.txt
├── docker-compose.yml
├── frontend
│   ├── Dockerfile
│   ├── nginx.conf
│   └── site
│       ├── app.js
│       ├── index.html
│       └── styles.css
├── monitoring
│   ├── grafana
│   │   ├── dashboards
│   │   │   └── dashboards-overview.json
│   │   └── provisioning
│   │       ├── dashboards
│   │       │   └── dashboards.yml
│   │       └── datasources
│   │           └── datasources.yml
│   ├── loki
│   │   └── loki-config.yml
│   ├── prometheus
│   │   └── prometheus.yml
│   └── promtail
│       └── promtail-config.yml
├── postgres
│   └── init.sql
├── remediator
│   ├── Dockerfile
│   ├── remediator.py
│   └── requirements.txt
└── worker
    ├── Dockerfile
    ├── requirements.txt
    └── worker.py
```

## Services Included:

Core Control & Application Services

``` bash
____________________________________________________
| Service        | Description                     |
| -------------- | ------------------------------- |
| **frontend**   | Operator dashboard (Nginx + JS) |
| **backend**    | Control plane API (FastAPI)     |
| **worker**     | Background worker service       |
| **chaos**      | Failure simulation service      |
| **remediator** | Automated recovery logic        |
----------------------------------------------------
```
Infrastructure Services

``` bash
___________________________________
| Service      | Purpose          |
| ------------ | ---------------- |
| **postgres** | Database service |
| **redis**    | Cache service    |
| **rabbitmq** | Message queue    |
-----------------------------------
```

Observability Stack

``` bash
_______________________________________
| Service        | Purpose            |
| -------------- | ------------------ |
| **prometheus** | Metrics scraping   |
| **grafana**    | Metrics dashboards |
| **loki**       | Centralized logs   |
| **promtail**   | Log shipping       |
---------------------------------------
```

## Operator UI (What You See in the UI):

### 1. System Metrics (Host-Level)

Collected from the backend host (works on Docker, WSL, VM, or server):

- CPU – units + free percentage

- RAM – total / free

- Disk – total / free

Displayed in a dedicated SYSTEM METRICS window.

### 2. Service Windows (One per Service)

Each service has its own card showing:

- Status (UP / DOWN)

- Started time

- Recovery mode

- LED indicator

- Live action logs

Available Actions:

* Ping – check service responsiveness

* Start – bring service UP

* Stop – simulate failure

Only operator actions are shown in logs:

* ping

* start

* stop

* auto-remediation

---

### 3. Auto-Remediation Control

At the bottom of the UI:

AUTO-REMEDIATION button

What it does:

- Scans all services

- Finds those that are DOWN

- Restarts them deterministically

- Displays a popup listing recovered services

## Running the Project:

Start everything

``` bash
docker compose up --build
```

Open the UI:

``` bash
http://localhost:8080
```

## How to Test via CLI (API)

All actions are available through HTTP APIs.

List all services:

``` bash
curl http://localhost:8000/services
```

Get system metrics:

``` bash
curl http://localhost:8000/system
```

Ping a service:

``` bash
curl -X POST http://localhost:8000/ping/redis
```

Stop a service:

``` bash
curl -X POST http://localhost:8000/stop/redis
```

Start a service:

``` bash
curl -X POST http://localhost:8000/start/redis
```

Trigger auto-remediation:

``` bash
curl -X POST http://localhost:8000/remediate
```

Example response:

``` bash
{
  "status": "completed",
  "services_remediated": ["redis", "postgres"],
  "services_skipped": []
}
```

## How to Test via the UI

Stop a Service

1. Click Stop on any service

2. LED turns red

3. Log appears:

``` bash
Service stopped manually
```

Ping a Service:
* if UP:

``` bash
  Ping succeeded
```

* if DOWN:

``` bash
Ping failed (service DOWN)
```

---

Start a Service

1. Click Start

2. Service turns green

3. Popup confirms:

``` bash
Service redis was restarted successfully!!
```

Auto-Remediation

1. Stop multiple services

2. Click AUTO-REMEDIATION

3. Popup lists recovered services:

``` bash
The following services were restarted successfully:
• redis
• postgres
```

## Monitoring & Observability

Prometheus:

``` bash
http://localhost:9090
```

- API request counters
- Backend metrics

Grafana:

``` bash
http://localhost:3000
```

- Dashboards for system & service metrics
- Extendable with custom panels

Loki + Promtail:

- Centralized logging pipeline
- Ready for future log-based alerting


## Auto-Remediation Design

- Not automatic by default

- Operator-triggered

- Deterministic

- Visible and auditable









