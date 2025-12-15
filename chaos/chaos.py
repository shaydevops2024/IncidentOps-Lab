import requests, time

while True:
    time.sleep(180)
    requests.post("http://backend:8000/incident/redis")
