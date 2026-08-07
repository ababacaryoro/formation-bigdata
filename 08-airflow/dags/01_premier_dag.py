"""
Premier DAG — découverte d'Airflow.

Formation Big Data — ANSD / Data Innovation Lab

Ce DAG ne fait rien d'utile : il sert à comprendre la mécanique. Trois tâches
s'enchaînent, et la dernière échoue volontairement une fois sur deux, pour
observer la reprise automatique.

Déposez ce fichier dans le dossier `dags/`. Airflow le détecte en une minute.
"""

from datetime import datetime, timedelta

from airflow.sdk import dag, task

# Depuis Airflow 3, les objets `dag` et `task` viennent de `airflow.sdk`.
# Beaucoup d'exemples en ligne, écrits pour Airflow 2, importent encore
# `airflow.decorators` : cela fonctionne encore, mais c'est déconseillé.


@dag(
    dag_id="01_premier_dag",
    description="Découverte : enchaînement, reprise, journaux",
    schedule=None,                       # déclenchement manuel uniquement
    start_date=datetime(2026, 8, 1),
    catchup=False,                       # défaut depuis Airflow 3
    tags=["formation", "decouverte"],
    default_args={
        "retries": 2,                    # deux nouvelles tentatives
        "retry_delay": timedelta(seconds=20),
    },
)
def premier_dag():

    @task
    def extraire() -> dict:
        """Simule une extraction de données."""
        print("Extraction en cours…")
        return {"lignes": 1500, "source": "etat_civil"}

    @task
    def transformer(lot: dict) -> dict:
        """Reçoit le résultat de la tâche précédente."""
        print(f"Transformation de {lot['lignes']} lignes issues de {lot['source']}")
        return {"agregats": lot["lignes"] // 10}

    @task
    def charger(resultat: dict) -> None:
        """Échoue une fois sur deux, pour montrer la reprise."""
        import random

        if random.random() < 0.5:
            raise RuntimeError("Base de destination injoignable (échec simulé)")
        print(f"Chargement de {resultat['agregats']} agrégats — terminé")

    # Les dépendances se déduisent du passage des valeurs :
    # extraire → transformer → charger
    charger(transformer(extraire()))


premier_dag()
