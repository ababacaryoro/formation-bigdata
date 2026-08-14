"""
Sujet « telephonie » — données de téléphonie mobile.

Les antennes transmettent des enregistrements d'événements : appels, SMS,
connexions de données. Agrégées, ces traces permettent d'estimer la
population présente dans une zone et ses déplacements.

Les identifiants d'abonnés sont des jetons, jamais des numéros de téléphone :
ces données ne doivent pas permettre de réidentifier une personne.

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

# Poids démographiques : Dakar concentre l'essentiel du trafic
POIDS_REGIONS = [0.42, 0.15, 0.10, 0.08, 0.08, 0.07, 0.06, 0.04]

TYPES_EVENEMENT = ["appel_sortant", "appel_entrant", "sms", "donnees"]

MILIEUX = ["Urbain", "Rural"]


def fabriquer_evenement(numero, alea, horodatage):
    """Un enregistrement transmis par une antenne."""
    region = alea.choices(REGIONS, weights=POIDS_REGIONS)[0]
    milieu = "Urbain" if alea.random() < 0.65 else "Rural"
    type_evenement = alea.choices(
        TYPES_EVENEMENT, weights=[0.30, 0.28, 0.17, 0.25])[0]

    # Durée pour les appels, volume pour les données
    if type_evenement.startswith("appel"):
        duree = alea.randint(5, 400)
        volume = 0
    elif type_evenement == "donnees":
        duree = 0
        volume = alea.randint(50, 8000)
    else:
        duree = 0
        volume = 0

    return {
        "identifiant": f"CDR-{numero:09d}",
        # Jeton d'abonné : pseudonyme, jamais un numéro de téléphone
        "jeton_abonne": f"AB{alea.randrange(1, 15001):06d}",
        "antenne": f"ANT-{region[:2].upper()}-{alea.randrange(1, 60):03d}",
        "region": region,
        "milieu": milieu,
        "type_evenement": type_evenement,
        "duree_secondes": duree,
        "volume_ko": volume,
        "horodatage": horodatage,
    }


# --------------------------------------------------------------------------
# 2. LE SCHÉMA — pour que Spark sache décoder le JSON
#
# Types possibles : "string", "int", "double", "boolean"
# --------------------------------------------------------------------------

SCHEMA = {
    "identifiant": "string",
    "jeton_abonne": "string",
    "antenne": "string",
    "region": "string",
    "milieu": "string",
    "type_evenement": "string",
    "duree_secondes": "int",
    "volume_ko": "int",
    "horodatage": "string",
}


# --------------------------------------------------------------------------
# 3. LES AGRÉGATS — calculés par MongoDB, publiés dans PostgreSQL
#
# Chaque agrégat produit des lignes de la forme :
#   minute · dimension · valeur · effectif
# --------------------------------------------------------------------------

AGREGATS = {

    # Événements par minute et par région
    "evenements_par_region": [
        {"$group": {
            "_id": {"minute": "$minute", "dimension": "$region"},
            "effectif": {"$sum": 1},
            "valeur": {"$avg": "$duree_secondes"},
        }},
    ],

    # Répartition par type d'événement
    "types_evenement": [
        {"$group": {
            "_id": {"minute": "$minute", "dimension": "$type_evenement"},
            "effectif": {"$sum": 1},
            "valeur": {"$avg": "$volume_ko"},
        }},
    ],

    # Abonnés DISTINCTS par région : c'est l'estimation de population présente.
    # On rassemble d'abord les abonnés uniques, puis on les compte.
    "presence_par_region": [
        {"$group": {
            "_id": {"minute": "$minute", "dimension": "$region",
                    "abonne": "$jeton_abonne"},
        }},
        {"$group": {
            "_id": {"minute": "$_id.minute", "dimension": "$_id.dimension"},
            "effectif": {"$sum": 1},
            "valeur": {"$sum": 1},
        }},
    ],

    # Volume de données échangé par milieu de résidence
    "volume_par_milieu": [
        {"$match": {"type_evenement": "donnees"}},
        {"$group": {
            "_id": {"minute": "$minute", "dimension": "$milieu"},
            "effectif": {"$sum": 1},
            "valeur": {"$avg": "$volume_ko"},
        }},
    ],
}
