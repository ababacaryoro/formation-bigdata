from kafka import KafkaProducer
import time

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: v.encode('utf-8')
)

for i in range(10):
    message = f"Message numero {i}"
    producer.send('demo-topic', value=message)
    print(f"Envoyé : {message}")
    time.sleep(1)

producer.flush()
