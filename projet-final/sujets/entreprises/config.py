"""
Sujet « ninea » — répertoire des entreprises.

Les guichets transmettent en continu les immatriculations, modifications et
radiations d'entreprises. Le répertoire doit refléter ces mouvements
rapidement : une entreprise immatriculée doit être visible en quelques
minutes.

Ce fichier contient TOUT ce qui est propre au sujet :
  1. la fabrique d'événements   → ce que le producteur envoie dans Kafka
  2. le schéma                  → comment Spark décode les messages
  3. l'agrégation               → ce que l'on publie dans PostgreSQL
"""

# --------------------------------------------------------------------------
# 1. LES ÉVÉNEMENTS
# --------------------------------------------------------------------------

REGIONS = ["Dakar", "Thiès", "Diourbel", "Kaolack", "Saint-Louis",
           "Ziguinchor", "Louga", "Tambacounda"]

OPERATIONS = ["immatriculation", "modification", "radiation"]

FORMES = ["SARL", "SUARL", "SA", "GIE", "Entreprise individuelle"]

SECTEURS = ["Commerce", "Services", "BTP", "Agriculture", "Industrie",
            "Transport", "Restauration", "Artisanat"]

GUICHETS = ["Guichet unique Dakar", "Guichet régional", "Antenne locale",
            "Service en ligne"]


def fabriquer_evenement(numero, alea, horodatage):
    """Un mouvement transmis par un guichet."""
    region = alea.choice(REGIONS)
    operation = alea.choices(OPERATIONS, weights=[0.70, 0.22, 0.08])[0]
    guichet = alea.choice(GUICHETS)

    # Délai de traitement au guichet, en minutes.
    # Le service en ligne est plus rapide que les guichets physiques.
    if guichet == "Service en ligne":
        delai = alea.randint(1, 6)
    else:
        delai = alea.randint(3, 25)

    return {
        "identifiant": f"NIN-{numero:08d}",
        "operation": operation,
        "region": region,
        "guichet": guichet,
        "forme_juridique": alea.choice(FORMES),
        "secteur": alea.choice(SECTEURS),
        "effectif_declare": alea.choices(
            [alea.randint(1, 5), alea.randint(6, 50), alea.randint(51, 300)],
            weights=[0.72, 0.23, 0.05],
        )[0],
        "delai_traitement_minutes": delai,
        "horodatage": horodatage,
    }


# --------------------------------------------------------------------------
# 2. LE SCHÉMA — pour que Spark sache décoder le JSON
#
# Types possibles : "string", "int", "double", "boolean"
# --------------------------------------------------------------------------

SCHEMA = {
    "identifiant": "string",
    "operation": "string",
    "region": "string",
    "guichet": "string",
    "forme_juridique": "string",
    "secteur": "string",
    "effectif_declare": "int",
    "delai_traitement_minutes": "int",
    "horodatage": "string",
}


# --------------------------------------------------------------------------
# 3. LES AGRÉGATS — calculés par MongoDB, publiés dans PostgreSQL
#
# Chaque agrégat produit des lignes de la forme :
#   minute · dimension · valeur · effectif
# --------------------------------------------------------------------------

AGREGATS = {

    # Mouvements enregistrés par minute et par région
    "mouvements_par_region": [
        {"$group": {
            "_id": {"minute": "$minute", "dimension": "$region"},
            "effectif": {"$sum": 1},
            "valeur": {"$avg": "$effectif_declare"},
        }},
    ],

    # Répartition par type d'opération
    "operations": [
        {"$group": {
            "_id": {"minute": "$minute", "dimension": "$operation"},
            "effectif": {"$sum": 1},
            "valeur": {"$avg": "$delai_traitement_minutes"},
        }},
    ],

    # Immatriculations par secteur d'activité
    "immatriculations_par_secteur": [
        {"$match": {"operation": "immatriculation"}},
        {"$group": {
            "_id": {"minute": "$minute", "dimension": "$secteur"},
            "effectif": {"$sum": 1},
            "valeur": {"$avg": "$effectif_declare"},
        }},
    ],

    # Délai moyen de traitement par guichet, en minutes
    "delai_par_guichet": [
        {"$group": {
            "_id": {"minute": "$minute", "dimension": "$guichet"},
            "effectif": {"$sum": 1},
            "valeur": {"$avg": "$delai_traitement_minutes"},
        }},
    ],
}
