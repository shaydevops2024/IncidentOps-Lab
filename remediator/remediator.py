import requests, time

while True:
    time.sleep(90)
    requests.post("http://backend:8000/resolve/redis")
