"""
Chaîne batch quotidienne — MongoDB → PostgreSQL.

Formation Big Data — ANSD / Data Innovation Lab

Ce DAG illustre le chemin périodique de l'architecture : pendant qu'un flux
alimente MongoDB en continu, un traitement régulier calcule les agrégats
publiables et les dépose dans PostgreSQL, où le tableau de bord viendra les
lire.

    MongoDB conserve ce qui est arrivé.
    PostgreSQL publie ce qu'on en a tiré.

Ce DAG est AUTOPORTEUR : sa première tâche crée les données de démonstration.
Vous pouvez le déclencher sans avoir exécuté quoi que ce soit auparavant.

Deux notions y sont mises en œuvre :

  * l'INTERVALLE DE DONNÉES — le traitement est paramétré par une période, pas
    par « maintenant », ce qui le rend rejouable à l'identique sur le passé ;
  * l'IDEMPOTENCE — rejouer une tâche remplace les résultats au lieu de les
    ajouter une seconde fois. C'est indispensable, puisqu'une tâche en échec
    est automatiquement relancée.
"""

from datetime import datetime, timedelta

from airflow.sdk import dag, task
from airflow.timetables.interval import CronDataIntervalTimetable

# --------------------------------------------------------------------------
# Les identifiants de connexion ne sont JAMAIS en dur dans le code du DAG.
# Ils sont déclarés comme des « connexions » Airflow — ici via les variables
# d'environnement AIRFLOW_CONN_* du docker-compose, qui reprennent elles-
# mêmes les valeurs du fichier .env. On les relit à l'exécution de chaque
# tâche, jamais au chargement du module.
#
#   AIRFLOW_CONN_MONGO_FLUX           -> connexion "mongo_flux"
#   AIRFLOW_CONN_POSTGRES_RESTITUTION -> connexion "postgres_restitution"
# --------------------------------------------------------------------------

ID_CONNEXION_MONGO = "mongo_flux"
ID_CONNEXION_POSTGRES = "postgres_restitution"


def obtenir_uri_mongo() -> str:
    """Reconstruit l'URI Mongo à partir de la connexion Airflow."""
    from airflow.hooks.base import BaseHook

    connexion = BaseHook.get_connection(ID_CONNEXION_MONGO)
    return connexion.get_uri()


def obtenir_params_postgres() -> dict:
    """Reconstruit les paramètres psycopg2 à partir de la connexion Airflow."""
    from airflow.hooks.base import BaseHook

    connexion = BaseHook.get_connection(ID_CONNEXION_POSTGRES)
    return {
        "host": connexion.host,
        "port": connexion.port or 5432,
        "dbname": connexion.schema,
        "user": connexion.login,
        "password": connexion.password,
    }


# ══════════════════════════════════════════════════════════════════════════
#  POURQUOI CronDataIntervalTimetable PLUTÔT QU'UNE CHAÎNE CRON ?
#
#  Depuis Airflow 3, écrire simplement schedule="0 2 * * *" produit un
#  intervalle de données de DURÉE NULLE : data_interval_start et
#  data_interval_end sont égaux. Un traitement filtrant sur cet intervalle ne
#  retournerait jamais rien.
#
#  Pour retrouver la sémantique classique — « l'exécution de 2 h du matin
#  traite les vingt-quatre heures précédentes » — il faut la demander
#  explicitement, comme ci-dessous.
#
#  C'est un changement de comportement entre Airflow 2 et Airflow 3.
# ══════════════════════════════════════════════════════════════════════════


@dag(
    dag_id="02_agregats_quotidiens",
    description="Agrégats quotidiens des actes : MongoDB → PostgreSQL",
    schedule=CronDataIntervalTimetable("0 2 * * *", timezone="UTC"),
    start_date=datetime(2026, 8, 1),
    catchup=False,
    tags=["formation", "production"],
    default_args={"retries": 2, "retry_delay": timedelta(minutes=1)},
)
def agregats_quotidiens():

    @task
    def delimiter_periode(**contexte) -> dict:
        """Détermine la période à traiter.

        Airflow fournit les bornes de l'intervalle dans le contexte
        d'exécution. Paramétrer le traitement par ces bornes — plutôt que par
        « aujourd'hui » — est ce qui le rend rejouable sur n'importe quelle
        date passée.
        """
        debut = contexte["data_interval_start"]
        fin = contexte["data_interval_end"]

        # Garde-fou : si l'intervalle est de durée nulle (cas de certains
        # déclenchements manuels), on retient les 24 heures précédentes.
        if debut >= fin:
            debut = fin - timedelta(days=1)

        print(f"Période traitée : {debut}  →  {fin}")
        return {"debut": debut.isoformat(), "fin": fin.isoformat()}

    @task
    def preparer_donnees(periode: dict) -> int:
        """Alimente MongoDB en données de démonstration.

        Cette tâche rend le DAG autoporteur : elle crée un jeu d'actes réparti
        sur les sept derniers jours, de sorte que la période traitée contienne
        toujours quelque chose.

        Dans une chaîne réelle, cette tâche n'existerait pas : les données
        arriveraient par le flux.
        """
        import random
        from datetime import datetime as dt

        from pymongo import MongoClient

        REGIONS = ["Dakar", "Thiès", "Diourbel", "Saint-Louis", "Ziguinchor",
                   "Kaolack", "Tambacounda", "Matam"]
        TYPES = ["naissance", "mariage", "deces"]

        fin = dt.fromisoformat(periode["fin"])
        alea = random.Random(2026)

        client = MongoClient(obtenir_uri_mongo())
        collection = client["flux"]["actes"]

        # Idempotence : on repart d'un jeu propre plutôt que d'empiler
        collection.delete_many({"origine": "demonstration"})

        documents = []
        for i in range(1, 3001):
            instant = fin - timedelta(
                days=alea.randrange(0, 7),
                hours=alea.randrange(0, 24),
                minutes=alea.randrange(0, 60),
            )
            documents.append({
                "numero_acte": f"ACT-{i:07d}",
                "type_acte": alea.choices(TYPES, weights=[0.72, 0.12, 0.16])[0],
                "region": alea.choice(REGIONS),
                "sexe": alea.choice(["M", "F"]),
                "horodatage": instant.isoformat(),
                "origine": "demonstration",
            })

        collection.insert_many(documents)
        total = collection.count_documents({})
        client.close()

        print(f"{len(documents)} actes de démonstration insérés "
              f"(collection : {total} documents)")
        return len(documents)

    @task
    def compter_documents(periode: dict) -> int:
        """Vérifie qu'il y a quelque chose à traiter sur la période.

        Un contrôle en amont évite de lancer un traitement pour rien, et rend
        le diagnostic plus simple en cas d'anomalie.
        """
        from pymongo import MongoClient

        client = MongoClient(obtenir_uri_mongo())
        nombre = client["flux"]["actes"].count_documents({
            "horodatage": {"$gte": periode["debut"], "$lt": periode["fin"]}
        })
        client.close()

        print(f"{nombre} documents sur la période "
              f"[{periode['debut']} → {periode['fin']}]")
        if nombre == 0:
            print("Rien à traiter sur cette période.")
        return nombre

    @task
    def calculer_agregats(periode: dict, nombre: int) -> int:
        """Calcule les agrégats et les dépose dans PostgreSQL.

        L'agrégation est confiée à MongoDB lui-même, par son pipeline
        d'agrégation : c'est le moteur qui calcule, Airflow ne fait que
        déclencher et acheminer.

        Sur des volumes importants, cette tâche déclencherait un traitement
        Spark plutôt que de calculer elle-même. Le principe resterait le
        même : Airflow orchestre, il ne calcule pas.
        """
        import psycopg2
        from pymongo import MongoClient

        if nombre == 0:
            print("Aucun document : rien à écrire.")
            return 0

        # --- 1. Agrégation, côté MongoDB -----------------------------------
        client = MongoClient(obtenir_uri_mongo())
        resultats = list(client["flux"]["actes"].aggregate([
            {"$match": {"horodatage": {"$gte": periode["debut"],
                                       "$lt": periode["fin"]}}},
            {"$group": {"_id": {"region": "$region", "type": "$type_acte"},
                        "effectif": {"$sum": 1}}},
            {"$sort": {"effectif": -1}},
        ]))
        client.close()
        print(f"{len(resultats)} combinaisons région × type d'acte")

        # --- 2. Écriture dans PostgreSQL -----------------------------------
        jour = periode["debut"][:10]

        connexion = psycopg2.connect(**obtenir_params_postgres())
        with connexion, connexion.cursor() as curseur:
            curseur.execute("""
                CREATE TABLE IF NOT EXISTS agregats_actes (
                    jour        DATE,
                    region      TEXT,
                    type_acte   TEXT,
                    effectif    BIGINT,
                    calcule_le  TIMESTAMP DEFAULT now()
                )
            """)

            # IDEMPOTENCE : on efface la journée avant de l'insérer.
            # Sans cette ligne, chaque nouvelle tentative doublerait les
            # effectifs publiés — et une tâche en échec est rejouée
            # automatiquement.
            curseur.execute("DELETE FROM agregats_actes WHERE jour = %s", (jour,))

            curseur.executemany(
                "INSERT INTO agregats_actes (jour, region, type_acte, effectif) "
                "VALUES (%s, %s, %s, %s)",
                [(jour, r["_id"]["region"], r["_id"]["type"], r["effectif"])
                 for r in resultats],
            )
        connexion.close()

        print(f"{len(resultats)} lignes écrites pour la journée {jour}")
        return len(resultats)

    @task
    def controler(lignes: int) -> None:
        """Vérifie la cohérence de la table de restitution."""
        import psycopg2

        connexion = psycopg2.connect(**obtenir_params_postgres())
        with connexion, connexion.cursor() as curseur:
            curseur.execute("SELECT COUNT(*), COUNT(DISTINCT jour), "
                            "COALESCE(SUM(effectif), 0) FROM agregats_actes")
            total, jours, effectifs = curseur.fetchone()
            curseur.execute("SELECT region, SUM(effectif) FROM agregats_actes "
                            "GROUP BY region ORDER BY 2 DESC LIMIT 3")
            tete = curseur.fetchall()
        connexion.close()

        print(f"Table de restitution : {total} lignes, {jours} journée(s), "
              f"{effectifs} actes agrégés")
        print(f"Écrit lors de cette exécution : {lignes} lignes")
        for region, effectif in tete:
            print(f"   {region:<14} {effectif}")

    # --- Enchaînement ------------------------------------------------------
    # Les dépendances se déduisent du passage des valeurs entre tâches.
    periode = delimiter_periode()
    preparation = preparer_donnees(periode)
    nombre = compter_documents(periode)

    # `preparer_donnees` ne transmet pas de valeur utile à `compter_documents`,
    # mais celle-ci ne doit pas démarrer avant : on déclare alors la dépendance
    # explicitement, avec l'opérateur `>>`.
    preparation >> nombre

    controler(calculer_agregats(periode, nombre))


agregats_quotidiens()
