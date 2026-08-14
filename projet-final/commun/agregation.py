"""
Agrégation — lit MongoDB, calcule les indicateurs, écrit dans PostgreSQL.

    python commun/agregation.py --sujet prix

Appelé toutes les deux minutes par Airflow. Peut aussi se lancer à la main.

Les agrégats calculés viennent de `sujets/<sujet>/config.py`.
Ce programme, lui, ne change jamais.

Il produit une seule table, `agregats`, avec toujours les mêmes colonnes :

    indicateur · minute · dimension · effectif · valeur · calcule_le

C'est cette table que Superset interrogera.
"""

import argparse
import importlib
import os
import sys
from datetime import datetime, timedelta

import psycopg2
from pymongo import MongoClient

MONGO_URI = os.environ["MONGO_URI"]
POSTGRES = {
    "host": os.environ.get("POSTGRES_HOTE", "postgres"),
    "dbname": os.environ.get("POSTGRES_DB", "restitution"),
    "user": os.environ["POSTGRES_USER"],
    "password": os.environ["POSTGRES_PASSWORD"],
}

# On recalcule les dix dernières minutes à chaque exécution.
# Les données plus anciennes restent en base : elles ont déjà été traitées.
FENETRE_MINUTES = 10


def creer_table(curseur):
    curseur.execute("""
        CREATE TABLE IF NOT EXISTS agregats (
            indicateur  TEXT,
            minute      TEXT,
            dimension   TEXT,
            effectif    BIGINT,
            valeur      DOUBLE PRECISION,
            calcule_le  TIMESTAMP DEFAULT now()
        )
    """)


def main():
    parser = argparse.ArgumentParser(
        description="Calcule les agrégats et les publie dans PostgreSQL.")
    parser.add_argument("--sujet", required=True)
    parser.add_argument("--fenetre", type=int, default=FENETRE_MINUTES,
                        help="nombre de minutes recalculées (défaut : 10)")
    args = parser.parse_args()

    config = importlib.import_module(f"sujets.{args.sujet}.config")

    # Bornes de la fenêtre : les N dernières minutes
    fin = datetime.now()
    debut = fin - timedelta(minutes=args.fenetre)
    minute_debut = debut.strftime("%Y-%m-%d %H:%M")

    print(f"Sujet   : {args.sujet}")
    print(f"Fenêtre : depuis {minute_debut}")

    client = MongoClient(MONGO_URI)
    collection = client[args.sujet]["evenements"]

    connexion = psycopg2.connect(**POSTGRES)
    with connexion, connexion.cursor() as curseur:
        creer_table(curseur)

        # On efface la fenêtre avant de la réécrire : relancer le programme
        # remplace les lignes au lieu de les ajouter une seconde fois.
        curseur.execute(
            "DELETE FROM agregats WHERE minute >= %s", (minute_debut,))

        total = 0
        for nom_indicateur, etapes in config.AGREGATS.items():
            # On ne garde que les événements de la fenêtre
            pipeline = [{"$match": {"minute": {"$gte": minute_debut}}}] + etapes
            resultats = list(collection.aggregate(pipeline))

            lignes = [
                (
                    nom_indicateur,
                    r["_id"]["minute"],
                    str(r["_id"]["dimension"]),
                    int(r.get("effectif", 0)),
                    float(r["valeur"]) if r.get("valeur") is not None else None,
                )
                for r in resultats
            ]

            if lignes:
                curseur.executemany(
                    "INSERT INTO agregats "
                    "(indicateur, minute, dimension, effectif, valeur) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    lignes,
                )
            total += len(lignes)
            print(f"  {nom_indicateur:<32} {len(lignes):>5} lignes")

    connexion.close()
    client.close()
    print(f"\n{total} lignes publiées dans PostgreSQL.")


if __name__ == "__main__":
    sys.exit(main())
