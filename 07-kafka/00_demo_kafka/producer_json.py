from kafka import KafkaProducer
import json
import time
import random

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    key_serializer=lambda k: k.encode('utf-8'),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

clients = ["client_A", "client_B", "client_C"]

for i in range(15):
    client = random.choice(clients)
    event = {"client": client, "montant": round(random.uniform(10, 500), 2), "id": i}
    producer.send('demo-topic-json', key=client, value=event)
    print(f"Envoyé : {event}")
    time.sleep(0.5)

producer.flush()
