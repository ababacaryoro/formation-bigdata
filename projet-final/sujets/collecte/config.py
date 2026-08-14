"""
Sujet « collecte » — pilotage d'une collecte de recensement.

Les tablettes des enquêteurs remontent en continu les questionnaires
collectés, avec la durée de l'entretien et le statut du ménage.

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

STATUTS = ["Complet", "Partiel", "Refus", "Absent"]

# Quelques enquêteurs ont un comportement atypique : entretiens très courts,
# ou beaucoup de refus. Le tableau de bord doit permettre de les repérer.
ENQUETEURS_RAPIDES = ["ENQ0007", "ENQ0023"]
ENQUETEURS_REFUS = ["ENQ0015"]


def fabriquer_evenement(numero, alea, horodatage):
    """Une remontée de questionnaire depuis une tablette."""
    enqueteur = f"ENQ{alea.randrange(1, 41):04d}"
    region = alea.choice(REGIONS)

    # Statut : beaucoup plus de refus chez certains enquêteurs
    if enqueteur in ENQUETEURS_REFUS:
        statut = alea.choices(STATUTS, weights=[0.35, 0.10, 0.40, 0.15])[0]
    else:
        statut = alea.choices(STATUTS, weights=[0.78, 0.07, 0.08, 0.07])[0]

    # Durée : anormalement courte chez certains enquêteurs
    if enqueteur in ENQUETEURS_RAPIDES:
        duree = alea.randint(3, 10)
    else:
        duree = alea.randint(18, 55)

    return {
        "identifiant": f"QST-{numero:08d}",
        "enqueteur": enqueteur,
        "region": region,
        "zone": f"ZD-{region[:2].upper()}-{alea.randrange(1, 25):03d}",
        "statut": statut,
        "duree_minutes": duree,
        "taille_menage": alea.randint(2, 15),
        "incoherences": alea.choices([0, 1, 2], weights=[0.80, 0.15, 0.05])[0],
        "horodatage": horodatage,
    }


# --------------------------------------------------------------------------
# 2. LE SCHÉMA — pour que Spark sache décoder le JSON
#
# Types possibles : "string", "int", "double", "boolean"
# --------------------------------------------------------------------------

SCHEMA = {
    "identifiant": "string",
    "enqueteur": "string",
    "region": "string",
    "zone": "string",
    "statut": "string",
    "duree_minutes": "int",
    "taille_menage": "int",
    "incoherences": "int",
    "horodatage": "string",
}


# --------------------------------------------------------------------------
# 3. LES AGRÉGATS — calculés par MongoDB, publiés dans PostgreSQL
#
# Chaque agrégat produit des lignes de la forme :
#   minute · dimension · valeur · effectif
#
# `minute` sert aux graphiques d'évolution, `dimension` aux répartitions.
# --------------------------------------------------------------------------

AGREGATS = {

    # Questionnaires collectés par minute et par région
    "questionnaires_par_region": [
        {"$group": {
            "_id": {"minute": "$minute", "dimension": "$region"},
            "effectif": {"$sum": 1},
            "valeur": {"$avg": "$duree_minutes"},
        }},
    ],

    # Répartition par statut : combien de complets, de refus…
    "statuts": [
        {"$group": {
            "_id": {"minute": "$minute", "dimension": "$statut"},
            "effectif": {"$sum": 1},
            "valeur": {"$avg": "$taille_menage"},
        }},
    ],

    # Durée moyenne d'entretien par enquêteur : une valeur très basse
    # signale des entretiens bâclés.
    "duree_par_enqueteur": [
        {"$match": {"statut": "Complet"}},
        {"$group": {
            "_id": {"minute": "$minute", "dimension": "$enqueteur"},
            "effectif": {"$sum": 1},
            "valeur": {"$avg": "$duree_minutes"},
        }},
    ],

    # Taux de refus par enquêteur, en %
    "refus_par_enqueteur": [
        {"$project": {
            "minute": 1,
            "enqueteur": 1,
            "est_refus": {"$cond": [{"$eq": ["$statut", "Refus"]}, 1, 0]},
        }},
        {"$group": {
            "_id": {"minute": "$minute", "dimension": "$enqueteur"},
            "effectif": {"$sum": 1},
            "valeur": {"$avg": {"$multiply": ["$est_refus", 100]}},
        }},
    ],
}
