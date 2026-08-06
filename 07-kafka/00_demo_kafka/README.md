# Démo Kafka - Formation

## Contenu du dossier

- `docker-compose.yml` : lance un broker Kafka en mode KRaft (sans Zookeeper)
- `create_topic.sh` : crée le topic `demo-topic` (3 partitions)
- `producer.py` : producer simple (messages texte)
- `consumer.py` : consumer simple (messages texte)
- `producer_json.py` : producer avec messages JSON + clé (partitionnement)
- `consumer_json.py` : consumer avec messages JSON + clé

## Prérequis

- Docker + Docker Compose
- Python 3.8+
- `pip install kafka-python`

## Installation

```bash
docker compose up -d
chmod +x create_topic.sh
./create_topic.sh
```

## Déroulé de la démo live

1. `docker compose up -d` → montrer que Kafka démarre
2. `chmod +x create_topic.sh ` puis `./create_topic.sh` → créer le topic en live, voir la liste des topics
3. Lancer `python consumer.py` dans un terminal
4. Lancer `python producer.py` dans un autre terminal → les messages apparaissent en direct côté consumer
5. Enchaîner avec `producer_json.py` / `consumer_json.py` pour parler partitionnement par clé
   - Montrer que tous les messages d'une même clé (ex: `client_A`) arrivent toujours sur la même partition

## Nettoyage

```bash
docker compose down
```
