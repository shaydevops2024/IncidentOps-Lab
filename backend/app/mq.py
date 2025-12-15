import pika
from .config import RABBITMQ_URL

def publish(message):
    conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    ch = conn.channel()
    ch.queue_declare(queue="events")
    ch.basic_publish(exchange="", routing_key="events", body=message)
    conn.close()
