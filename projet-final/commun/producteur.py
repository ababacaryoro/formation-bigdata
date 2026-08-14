"""
Producteur — envoie des événements dans Kafka.

    python commun/producteur.py --sujet prix --debit 20

Le contenu des événements vient de `sujets/<sujet>/config.py`.
Ce programme, lui, ne change jamais.
"""

import argparse
import importlib
import json
import os
import random
import sys
import time
from datetime import datetime

from confluent_kafka import Producer

COURTIER = os.environ.get("KAFKA_BOOTSTRAP", "kafka:9092")


def main():
    parser = argparse.ArgumentParser(
        description="Envoie des événements dans Kafka.")
    parser.add_argument("--sujet", required=True,
                        help="prix · collecte · etat_civil · ninea · telephonie")
    parser.add_argument("--debit", type=int, default=20,
                        help="événements par seconde (défaut : 20)")
    parser.add_argument("--duree", type=int, default=None,
                        help="durée en secondes ; sans fin si absent")
    args = parser.parse_args()

    # On charge la configuration du sujet choisi
    config = importlib.import_module(f"sujets.{args.sujet}.config")

    producteur = Producer({"bootstrap.servers": COURTIER, "linger.ms": 50})
    alea = random.Random()
    pause = 1.0 / args.debit
    depart = time.time()
    envoyes = 0

    print(f"Sujet : {args.sujet}")
    print(f"Kafka : {COURTIER}  ·  file « {args.sujet} »")
    print(f"Débit : {args.debit} événements par seconde")
    print("Ctrl+C pour arrêter.\n")

    try:
        while True:
            if args.duree and time.time() - depart > args.duree:
                break

            envoyes += 1
            horodatage = datetime.now().isoformat(timespec="seconds")
            evenement = config.fabriquer_evenement(envoyes, alea, horodatage)

            producteur.produce(
                args.sujet,
                value=json.dumps(evenement, ensure_ascii=False).encode("utf-8"),
            )
            producteur.poll(0)

            if envoyes % 200 == 0:
                print(f"  {envoyes:>7} événements envoyés", end="\r", flush=True)
            time.sleep(pause)
    except KeyboardInterrupt:
        print("\nArrêt demandé.")
    finally:
        producteur.flush()
        print(f"\n{envoyes} événements envoyés au total.")


if __name__ == "__main__":
    sys.exit(main())
