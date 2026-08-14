"""
Agrégation périodique — toutes les deux minutes.

Formation Big Data · ANSD / Data Innovation Lab

Ce DAG appelle `commun/agregation.py`, qui lit MongoDB, calcule les
indicateurs de votre sujet et les publie dans PostgreSQL.

    ┌─────────────────────────────────────────────────────────────┐
    │  UNE SEULE LIGNE À CHANGER : le nom de votre sujet, ci-dessous │
    └─────────────────────────────────────────────────────────────┘
"""

from datetime import datetime, timedelta

from airflow.sdk import dag, task

# ══════════════════════════════════════════════════════════════════════════
#  VOTRE SUJET — remplacez par le vôtre
#  prix · collecte · etat_civil · ninea · telephonie
# ══════════════════════════════════════════════════════════════════════════
SUJET = "prix"


@dag(
    dag_id=f"agregation_{SUJET}",
    description="Calcule les agrégats et les publie dans PostgreSQL",
    # Toutes les deux minutes. Le flux venant de démarrer, on ne raisonne pas
    # en journées : chaque exécution recalcule les dix dernières minutes.
    schedule=timedelta(minutes=2),
    start_date=datetime(2026, 8, 10),
    catchup=False,
    max_active_runs=1,          # une seule exécution à la fois
    tags=["projet", SUJET],
    default_args={"retries": 1, "retry_delay": timedelta(seconds=30)},
)
def agregation():

    @task.bash
    def calculer() -> str:
        """Lance le programme d'agrégation."""
        return f"cd /opt/airflow/projet && python commun/agregation.py --sujet {SUJET}"

    @task
    def controler() -> None:
        """Affiche l'état de la table de restitution."""
        import os

        import psycopg2

        connexion = psycopg2.connect(
            host="postgres",
            dbname=os.environ.get("POSTGRES_DB", "restitution"),
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
        )
        with connexion, connexion.cursor() as curseur:
            curseur.execute(
                "SELECT COUNT(*), COUNT(DISTINCT indicateur), "
                "COUNT(DISTINCT minute), MAX(minute) FROM agregats")
            lignes, indicateurs, minutes, derniere = curseur.fetchone()
        connexion.close()

        print(f"Table agregats : {lignes} lignes · {indicateurs} indicateurs "
              f"· {minutes} minutes")
        print(f"Dernière minute publiée : {derniere}")

    calculer() >> controler()


agregation()
