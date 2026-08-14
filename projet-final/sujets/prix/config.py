"""
Sujet « prix » — relevés de prix de caisse.

Les points de vente transmettent leurs relevés au fil des transactions.
Ces données servent à calculer un indice des prix à la consommation.

Ce fichier contient TOUT ce qui est propre au sujet :
  1. la fabrique d'événements   → ce que le producteur envoie dans Kafka
  2. le schéma                  → comment Spark décode les messages
  3. l'agrégation               → ce que l'on publie dans PostgreSQL
"""

import random

# --------------------------------------------------------------------------
# 1. LES ÉVÉNEMENTS
# --------------------------------------------------------------------------

REGIONS = ["Dakar", "Thiès", "Diourbel", "Kaolack", "Saint-Louis",
           "Ziguinchor", "Louga", "Tambacounda"]

# (produit, prix de référence en FCFA)
PRODUITS = [
    ("Riz brisé importé", 550),
    ("Pain baguette", 175),
    ("Huile d'arachide", 1500),
    ("Sucre cristallisé", 700),
    ("Oignon", 500),
    ("Tomate fraîche", 700),
    ("Poisson frais", 1500),
    ("Viande de bœuf", 3500),
    ("Lait en poudre", 2400),
    ("Gaz butane 6 kg", 3500),
]

TYPES_POINT_VENTE = ["Marché", "Supérette", "Grande surface", "Boutique"]


def fabriquer_evenement(numero, alea, horodatage):
    """Un relevé de prix, transmis par une caisse."""
    produit, prix_reference = alea.choice(PRODUITS)
    region = alea.choice(REGIONS)

    # Le prix varie autour de la référence, un peu plus cher en boutique
    type_point_vente = alea.choice(TYPES_POINT_VENTE)
    majoration = 1.08 if type_point_vente == "Boutique" else 1.0
    prix = round(prix_reference * majoration * alea.uniform(0.85, 1.15))

    return {
        "identifiant": f"PRX-{numero:08d}",
        "produit": produit,
        "prix_fcfa": prix,
        "prix_reference": prix_reference,
        "quantite": alea.choice([1, 1, 1, 2, 3]),
        "region": region,
        "point_vente": f"PV-{region[:2].upper()}-{alea.randrange(1, 30):02d}",
        "type_point_vente": type_point_vente,
        "horodatage": horodatage,
    }


# --------------------------------------------------------------------------
# 2. LE SCHÉMA — pour que Spark sache décoder le JSON
#
# Types possibles : "string", "int", "double", "boolean"
# --------------------------------------------------------------------------

SCHEMA = {
    "identifiant": "string",
    "produit": "string",
    "prix_fcfa": "int",
    "prix_reference": "int",
    "quantite": "int",
    "region": "string",
    "point_vente": "string",
    "type_point_vente": "string",
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

    # Nombre de relevés reçus, par minute et par région
    "releves_par_region": [
        {"$group": {
            "_id": {"minute": "$minute", "dimension": "$region"},
            "effectif": {"$sum": 1},
            "valeur": {"$avg": "$prix_fcfa"},
        }},
    ],

    # Prix moyen par produit — la base de l'indice
    "prix_par_produit": [
        {"$group": {
            "_id": {"minute": "$minute", "dimension": "$produit"},
            "effectif": {"$sum": 1},
            "valeur": {"$avg": "$prix_fcfa"},
        }},
    ],

    # Indice : prix observé rapporté au prix de référence, en base 100.
    # Un indice de 105 signifie « 5 % au-dessus de la référence ».
    "indice_par_region": [
        {"$project": {
            "minute": 1,
            "region": 1,
            "rapport": {"$divide": ["$prix_fcfa", "$prix_reference"]},
        }},
        {"$group": {
            "_id": {"minute": "$minute", "dimension": "$region"},
            "effectif": {"$sum": 1},
            "valeur": {"$avg": {"$multiply": ["$rapport", 100]}},
        }},
    ],
}
