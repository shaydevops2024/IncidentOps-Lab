from prometheus_client import Counter, generate_latest

REQUESTS = Counter("api_requests_total", "Total API requests")

def metrics():
    return generate_latest()
