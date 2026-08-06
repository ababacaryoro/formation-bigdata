from kafka import KafkaConsumer

consumer = KafkaConsumer(
    'demo-topic',
    bootstrap_servers='localhost:9092',
    auto_offset_reset='earliest',
    group_id='demo-group',
    value_deserializer=lambda v: v.decode('utf-8')
)

print("En attente de messages...")
for message in consumer:
    print(f"Reçu : {message.value} (partition={message.partition}, offset={message.offset})")
