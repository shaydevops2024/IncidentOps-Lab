import pika, psycopg2, os

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

def callback(ch, method, properties, body):
    cur.execute(
        "INSERT INTO events (event_type, message) VALUES (%s,%s)",
        ("queue", body.decode())
    )
    conn.commit()

connection = pika.BlockingConnection(pika.URLParameters(os.getenv("RABBITMQ_URL")))
channel = connection.channel()
channel.queue_declare(queue="events")
channel.basic_consume(queue="events", on_message_callback=callback, auto_ack=True)
channel.start_consuming()
