"""
Sujet « etat_civil » — déclarations dans les centres d'état civil.

Les centres déclarent naissances, mariages et décès au fil de l'eau. Une
partie des actes est numérisée, une autre reste sur registre papier.

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

TYPES_ACTE = ["naissance", "mariage", "deces"]

# Certaines régions numérisent moins que d'autres
TAUX_NUMERISATION = {
    "Dakar": 0.85, "Thiès": 0.70, "Diourbel": 0.55, "Kaolack": 0.60,
    "Saint-Louis": 0.65, "Ziguinchor": 0.50, "Louga": 0.45,
    "Tambacounda": 0.35,
}


def fabriquer_evenement(numero, alea, horodatage):
    """Une déclaration transmise par un centre d'état civil."""
    region = alea.choice(REGIONS)
    type_acte = alea.choices(TYPES_ACTE, weights=[0.72, 0.12, 0.16])[0]

    # Délai entre l'événement et sa déclaration, en jours.
    # Au-delà d'un mois, la déclaration est dite tardive.
    delai = alea.choices(
        [alea.randint(0, 5), alea.randint(6, 30), alea.randint(31, 365)],
        weights=[0.55, 0.28, 0.17],
    )[0]

    return {
        "identifiant": f"ACT-{numero:08d}",
        "type_acte": type_acte,
        "region": region,
        "centre": f"CEC-{region[:2].upper()}-{alea.randrange(1, 20):02d}",
        "sexe": alea.choice(["M", "F"]),
        "delai_jours": delai,
        "numerise": alea.random() < TAUX_NUMERISATION[region],
        "jugement_suppletif": delai > 365 or alea.random() < 0.08,
        "horodatage": horodatage,
    }


# --------------------------------------------------------------------------
# 2. LE SCHÉMA — pour que Spark sache décoder le JSON
#
# Types possibles : "string", "int", "double", "boolean"
# --------------------------------------------------------------------------

SCHEMA = {
    "identifiant": "string",
    "type_acte": "string",
    "region": "string",
    "centre": "string",
    "sexe": "string",
    "delai_jours": "int",
    "numerise": "boolean",
    "jugement_suppletif": "boolean",
    "horodatage": "string",
}


# --------------------------------------------------------------------------
# 3. LES AGRÉGATS — calculés par MongoDB, publiés dans PostgreSQL
#
# Chaque agrégat produit des lignes de la forme :
#   minute · dimension · valeur · effectif
# --------------------------------------------------------------------------

AGREGATS = {

    # Actes enregistrés par minute et par région
    "actes_par_region": [
        {"$group": {
            "_id": {"minute": "$minute", "dimension": "$region"},
            "effectif": {"$sum": 1},
            "valeur": {"$avg": "$delai_jours"},
        }},
    ],

    # Répartition par type d'acte
    "actes_par_type": [
        {"$group": {
            "_id": {"minute": "$minute", "dimension": "$type_acte"},
            "effectif": {"$sum": 1},
            "valeur": {"$avg": "$delai_jours"},
        }},
    ],

    # Part d'actes numérisés, par région, en %
    "numerisation_par_region": [
        {"$project": {
            "minute": 1,
            "region": 1,
            "est_numerise": {"$cond": ["$numerise", 1, 0]},
        }},
        {"$group": {
            "_id": {"minute": "$minute", "dimension": "$region"},
            "effectif": {"$sum": 1},
            "valeur": {"$avg": {"$multiply": ["$est_numerise", 100]}},
        }},
    ],

    # Part de déclarations tardives (plus de 30 jours), par région, en %
    "tardives_par_region": [
        {"$project": {
            "minute": 1,
            "region": 1,
            "est_tardive": {"$cond": [{"$gt": ["$delai_jours", 30]}, 1, 0]},
        }},
        {"$group": {
            "_id": {"minute": "$minute", "dimension": "$region"},
            "effectif": {"$sum": 1},
            "valeur": {"$avg": {"$multiply": ["$est_tardive", 100]}},
        }},
    ],
}
