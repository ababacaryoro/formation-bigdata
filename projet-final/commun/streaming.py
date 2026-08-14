"""
Ingestion — Spark lit le flux Kafka et écrit dans MongoDB.

    spark-submit commun/streaming.py --sujet prix

Le schéma des événements vient de `sujets/<sujet>/config.py`.
Ce programme, lui, ne change jamais.

Il tourne EN CONTINU : laissez-le dans un terminal et ouvrez-en un autre pour
la suite. Ctrl+C pour l'arrêter.
"""

import argparse
import importlib
import os
import sys

from pyspark.sql import SparkSession, functions as F
from pyspark.sql import types as T

COURTIER = os.environ.get("KAFKA_BOOTSTRAP", "kafka:9092")
MONGO_URI = os.environ["MONGO_URI"]

# Correspondance entre les types écrits dans config.py et ceux de Spark
TYPES = {
    "string": T.StringType(),
    "int": T.IntegerType(),
    "double": T.DoubleType(),
    "boolean": T.BooleanType(),
}


def main():
    parser = argparse.ArgumentParser(
        description="Lit un flux Kafka et l'écrit dans MongoDB.")
    parser.add_argument("--sujet", required=True)
    args = parser.parse_args()

    config = importlib.import_module(f"sujets.{args.sujet}.config")

    # Le schéma est construit à partir du dictionnaire de config.py
    schema = T.StructType([
        T.StructField(nom, TYPES[type_])
        for nom, type_ in config.SCHEMA.items()
    ])

    spark = (
        SparkSession.builder
        .appName(f"ingestion_{args.sujet}")
        .config("spark.mongodb.write.connection.uri", MONGO_URI)
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")

    print(f"Sujet   : {args.sujet}")
    print(f"Kafka   : {COURTIER}")
    print(f"MongoDB : base « {args.sujet} », collection « evenements »")
    print("En cours… Ctrl+C pour arrêter.\n")

    # 1. Lire le flux Kafka
    brut = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", COURTIER)
        .option("subscribe", args.sujet)
        .option("startingOffsets", "latest")
        .load()
    )

    # 2. Décoder le JSON, et ajouter la minute — c'est elle qui servira
    #    à découper le temps dans les agrégats.
    evenements = (
        brut
        .select(F.from_json(F.col("value").cast("string"), schema).alias("e"))
        .select("e.*")
        .withColumn("instant", F.to_timestamp("horodatage"))
        .withColumn("minute", F.date_format("instant", "yyyy-MM-dd HH:mm"))
    )

    # 3. Écrire chaque micro-lot dans MongoDB
    def vers_mongo(lot, numero):
        nombre = lot.count()
        if nombre == 0:
            return
        (lot.write.format("mongodb")
            .option("database", args.sujet)
            .option("collection", "evenements")
            .mode("append")
            .save())
        print(f"  lot {numero:>4} : {nombre:>5} événements écrits", flush=True)

    requete = (
        evenements.writeStream
        .foreachBatch(vers_mongo)
        .option("checkpointLocation", f"/tmp/checkpoint_{args.sujet}")
        .trigger(processingTime="10 seconds")
        .start()
    )

    try:
        requete.awaitTermination()
    except KeyboardInterrupt:
        print("\nArrêt demandé.")
    finally:
        requete.stop()
        spark.stop()


if __name__ == "__main__":
    sys.exit(main())
