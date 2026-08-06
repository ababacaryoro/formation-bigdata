#!/bin/bash
# Création du topic de démo

docker exec -it kafka /opt/kafka/bin/kafka-topics.sh \
  --create --topic demo-topic \
  --bootstrap-server localhost:9092 \
  --partitions 3 --replication-factor 1

docker exec -it kafka /opt/kafka/bin/kafka-topics.sh \
  --create --topic demo-topic-json \
  --bootstrap-server localhost:9092 \
  --partitions 3 --replication-factor 1

echo "Topics créés. Liste des topics :"

docker exec -it kafka /opt/kafka/bin/kafka-topics.sh \
  --list --bootstrap-server localhost:9092
