from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'demo-topic-json',
    bootstrap_servers='localhost:9092',
    auto_offset_reset='earliest',
    group_id='demo-group-json',
    key_deserializer=lambda k: k.decode('utf-8') if k else None,
    value_deserializer=lambda v: json.loads(v.decode('utf-8'))
)

for message in consumer:
    print(f"Clé={message.key} | Partition={message.partition} | Valeur={message.value}")
