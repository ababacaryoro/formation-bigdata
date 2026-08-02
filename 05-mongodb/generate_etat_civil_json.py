"""
Génère des actes d'état civil au format JSON imbriqué — module MongoDB.

Ces documents ont une structure arborescente et de profondeur variable :

  - un noyau structuré (numéro, type, date, lieu) ;
  - des sous-documents (déclarant, parents, officier) ;
  - un tableau de **mentions marginales** de longueur variable — mariage,
    divorce, décès, rectification — qui est précisément ce qu'une table
    relationnelle représente mal ;
  - des champs présents ou absents selon le type d'acte.

C'est cette irrégularité qui justifie une base documentaire.

Sortie : un fichier JSON Lines (un document par ligne), format attendu par
`mongoimport`.

Exemple de lancement:
--------
    python generate_etat_civil_json.py --actes 200000 --sortie ./data/actes.jsonl
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

# --------------------------------------------------------------------------
# Référentiels
# --------------------------------------------------------------------------

REGIONS = {
    "Dakar": ["Dakar", "Guédiawaye", "Pikine", "Rufisque", "Keur Massar"],
    "Thiès": ["Thiès", "Mbour", "Tivaouane"],
    "Diourbel": ["Diourbel", "Bambey", "Mbacké"],
    "Kaolack": ["Kaolack", "Guinguinéo", "Nioro du Rip"],
    "Saint-Louis": ["Saint-Louis", "Dagana", "Podor"],
    "Louga": ["Louga", "Kébémer", "Linguère"],
    "Fatick": ["Fatick", "Foundiougne", "Gossas"],
    "Kolda": ["Kolda", "Vélingara", "Médina Yoro Foulah"],
    "Tambacounda": ["Tambacounda", "Bakel", "Goudiry", "Koumpentoum"],
    "Ziguinchor": ["Ziguinchor", "Bignona", "Oussouye"],
    "Matam": ["Matam", "Kanel", "Ranérou"],
    "Kaffrine": ["Kaffrine", "Birkelane", "Koungheul", "Malem Hodar"],
    "Sédhiou": ["Sédhiou", "Bounkiling", "Goudomp"],
    "Kédougou": ["Kédougou", "Salémata", "Saraya"],
}

POIDS_REGIONS = [0.230, 0.130, 0.110, 0.072, 0.065, 0.060, 0.055, 0.050,
                 0.050, 0.043, 0.042, 0.040, 0.035, 0.018]

NOMS = ["Diop", "Ndiaye", "Fall", "Sarr", "Ba", "Sow", "Diallo", "Gueye",
        "Faye", "Sy", "Cissé", "Mbaye", "Seck", "Thiam", "Dieng", "Camara",
        "Sagna", "Badji", "Diatta", "Mané", "Sané", "Diouf", "Wade", "Kane",
        "Barry", "Touré", "Diagne", "Samb", "Ndour", "Lô", "Niang", "Coly",
        "Goudiaby", "Bodian", "Tine", "Sylla", "Dramé", "Konaté", "Sonko",
        "Diedhiou", "Baldé", "Ndao", "Mendy", "Preira", "Traoré", "Kébé"]

PRENOMS_M = ["Mamadou", "Ousmane", "Ibrahima", "Moussa", "Cheikh", "Abdoulaye",
             "Modou", "Alioune", "Babacar", "Ababacar", "Amadou", "Souleymane",
             "Assane", "Malick", "Serigne", "Pape", "Lamine", "Idrissa",
             "Boubacar", "El Hadji", "Saliou", "Mor", "Bara", "Daouda", "Samba"]

PRENOMS_F = ["Fatou", "Aminata", "Awa", "Ndeye", "Astou", "Khadija",
             "Maimouna", "Seynabou", "Adama", "Coumba", "Bineta", "Sokhna",
             "Rokhaya", "Mariama", "Aissatou", "Dieynaba", "Yacine",
             "Nafissatou", "Oumou", "Anta", "Marième", "Fatoumata", "Kine",
             "Penda", "Diarra", "Soda"]

PROFESSIONS = ["Cultivateur", "Commerçant", "Enseignant", "Fonctionnaire",
               "Artisan", "Pêcheur", "Éleveur", "Chauffeur", "Couturier",
               "Mécanicien", "Infirmier", "Ménagère", "Étudiant", "Sans emploi",
               "Employé de bureau", "Maçon", "Tailleur", "Restaurateur"]

LIEUX_NAISSANCE = ["Hôpital régional", "Centre de santé", "Poste de santé",
                   "Domicile", "Clinique privée", "Maternité"]

CAUSES_DECES = ["Maladie", "Accident", "Cause naturelle", "Non déclarée"]

QUALITES_DECLARANT = ["Père", "Mère", "Grand-parent", "Oncle", "Tante",
                      "Chef de village", "Agent de santé", "Témoin"]


# --------------------------------------------------------------------------
# Outils
# --------------------------------------------------------------------------


def date_aleatoire(annee_min: int, annee_max: int, rng: random.Random) -> date:
    debut = date(annee_min, 1, 1)
    fin = date(annee_max, 12, 31)
    return debut + timedelta(days=rng.randrange((fin - debut).days))


def personne(rng: random.Random, sexe: str | None = None,
             nom_famille: str | None = None, avec_profession: bool = False,
             annee_min: int = 1950, annee_max: int = 2000) -> dict:
    sexe = sexe or rng.choice(["M", "F"])
    prenom = rng.choice(PRENOMS_M if sexe == "M" else PRENOMS_F)
    document = {
        "prenom": prenom,
        "nom": nom_famille or rng.choice(NOMS),
        "sexe": sexe,
    }
    if avec_profession:
        document["profession"] = rng.choice(PROFESSIONS)
        document["date_naissance"] = date_aleatoire(
            annee_min, annee_max, rng).isoformat()
    return document


def localite(rng: random.Random) -> tuple[str, str]:
    region = rng.choices(list(REGIONS), weights=POIDS_REGIONS)[0]
    return region, rng.choice(REGIONS[region])


# --------------------------------------------------------------------------
# Mentions marginales — le tableau de longueur variable
# --------------------------------------------------------------------------


def mentions_marginales(rng: random.Random, date_acte: date,
                        sexe: str) -> list[dict]:
    """Engendre 0 à 4 mentions, cohérentes entre elles et dans le tem.

    Une mention marginale est une annotation portée en marge d'un acte
    postérieurement à son établissement : mariage, divorce, décès,
    rectification, reconnaissance.
    """
    mentions = []
    age_acte = (date.today() - date_acte).days // 365
    curseur = date_acte

    # Rectification d'erreur matérielle : possible à tout moment.
    if rng.random() < 0.08:
        curseur = date_acte + timedelta(days=rng.randrange(30, 3650))
        mentions.append({
            "type": "rectification",
            "date": curseur.isoformat(),
            "motif": rng.choice([
                "Erreur d'orthographe du nom",
                "Erreur sur la date de naissance",
                "Erreur sur le prénom de la mère",
                "Omission du prénom du père",
            ]),
            "reference_jugement": f"JGT-{rng.randrange(1000, 9999)}/"
                                  f"{curseur.year}",
        })

    # Mariage, puis éventuellement divorce.
    if age_acte > 20 and rng.random() < 0.45:
        curseur = date_acte + timedelta(days=rng.randrange(20 * 365, 40 * 365))
        if curseur < date.today():
            conjoint_sexe = "F" if sexe == "M" else "M"
            region, commune = localite(rng)
            mentions.append({
                "type": "mariage",
                "date": curseur.isoformat(),
                "conjoint": personne(rng, sexe=conjoint_sexe),
                "lieu": {"region": region, "commune": commune},
                "regime": rng.choice(["Monogamie", "Polygamie"]),
            })

            if rng.random() < 0.12:
                divorce = curseur + timedelta(days=rng.randrange(365, 25 * 365))
                if divorce < date.today():
                    mentions.append({
                        "type": "divorce",
                        "date": divorce.isoformat(),
                        "reference_jugement": f"JGT-{rng.randrange(1000, 9999)}/"
                                              f"{divorce.year}",
                    })

    # Décès.
    if age_acte > 50 and rng.random() < 0.15:
        deces = date_acte + timedelta(days=rng.randrange(50 * 365, 95 * 365))
        if deces < date.today():
            region, commune = localite(rng)
            mentions.append({
                "type": "deces",
                "date": deces.isoformat(),
                "lieu": {"region": region, "commune": commune},
                "cause": rng.choice(CAUSES_DECES),
            })

    return sorted(mentions, key=lambda m: m["date"])


# --------------------------------------------------------------------------
# Actes
# --------------------------------------------------------------------------


def acte_naissance(rng: random.Random, numero: int) -> dict:
    region, commune = localite(rng)
    date_acte = date_aleatoire(1960, 2025, rng)
    date_naissance = date_acte - timedelta(days=rng.randrange(0, 400))
    sexe = rng.choices(["M", "F"], weights=[0.51, 0.49])[0]
    nom_famille = rng.choice(NOMS)

    document = {
        "numero_acte": f"NAI-{region[:2].upper()}-{date_acte.year}-{numero:07d}",
        "type_acte": "naissance",
        "date_enregistrement": date_acte.isoformat(),
        "centre_etat_civil": {
            "region": region,
            "commune": commune,
            "code_centre": f"CEC{rng.randrange(100, 999)}",
        },
        "titulaire": {
            **personne(rng, sexe=sexe, nom_famille=nom_famille),
            "date_naissance": date_naissance.isoformat(),
            "lieu_naissance": {
                "region": region,
                "commune": commune,
                "etablissement": rng.choice(LIEUX_NAISSANCE),
            },
        },
        "parents": {
            "pere": personne(rng, sexe="M", nom_famille=nom_famille,
                             avec_profession=True),
            "mere": personne(rng, sexe="F", avec_profession=True),
        },
        "declarant": {
            **personne(rng),
            "qualite": rng.choice(QUALITES_DECLARANT),
        },
        "officier_etat_civil": personne(rng),
        "mentions_marginales": mentions_marginales(rng, date_acte, sexe),
        "numerise": rng.random() < 0.62,
    }

    # Champs présents seulement dans certains cas : l'irrégularité voulue.
    if rng.random() < 0.18:
        document["jugement_suppletif"] = {
            "tribunal": f"Tribunal de {commune}",
            "reference": f"JS-{rng.randrange(100, 999)}/{date_acte.year}",
            "date": (date_acte - timedelta(days=rng.randrange(30, 900))).isoformat(),
        }
    if rng.random() < 0.09:
        document["observations"] = rng.choice([
            "Acte reconstitué après sinistre du centre",
            "Registre partiellement détérioré",
            "Déclaration tardive régularisée",
            "Double enregistrement signalé",
        ])
    # Père non déclaré : le sous-document est absent, pas vide.
    if rng.random() < 0.06:
        del document["parents"]["pere"]

    return document


def acte_mariage(rng: random.Random, numero: int) -> dict:
    region, commune = localite(rng)
    date_acte = date_aleatoire(1970, 2025, rng)

    return {
        "numero_acte": f"MAR-{region[:2].upper()}-{date_acte.year}-{numero:07d}",
        "type_acte": "mariage",
        "date_enregistrement": date_acte.isoformat(),
        "centre_etat_civil": {
            "region": region,
            "commune": commune,
            "code_centre": f"CEC{rng.randrange(100, 999)}",
        },
        "epoux": personne(rng, sexe="M", avec_profession=True,
                          annee_min=1940, annee_max=2003),
        "epouse": personne(rng, sexe="F", avec_profession=True,
                           annee_min=1945, annee_max=2005),
        "regime_matrimonial": rng.choices(
            ["Monogamie", "Polygamie limitée à 2", "Polygamie limitée à 3",
             "Polygamie limitée à 4"],
            weights=[0.62, 0.18, 0.12, 0.08])[0],
        "temoins": [
            {**personne(rng), "qualite": rng.choice(["Témoin époux",
                                                     "Témoin épouse"])}
            for _ in range(rng.randrange(2, 5))
        ],
        "officier_etat_civil": personne(rng),
        "mentions_marginales": (
            [{
                "type": "divorce",
                "date": (date_acte + timedelta(
                    days=rng.randrange(365, 20 * 365))).isoformat(),
                "reference_jugement": f"JGT-{rng.randrange(1000, 9999)}",
            }] if rng.random() < 0.14 else []
        ),
        "numerise": rng.random() < 0.55,
    }


def acte_deces(rng: random.Random, numero: int) -> dict:
    region, commune = localite(rng)
    date_acte = date_aleatoire(1980, 2025, rng)
    sexe = rng.choice(["M", "F"])
    age = rng.choices(
        [rng.randrange(0, 5), rng.randrange(5, 45), rng.randrange(45, 100)],
        weights=[0.12, 0.28, 0.60])[0]

    document = {
        "numero_acte": f"DEC-{region[:2].upper()}-{date_acte.year}-{numero:07d}",
        "type_acte": "deces",
        "date_enregistrement": date_acte.isoformat(),
        "centre_etat_civil": {
            "region": region,
            "commune": commune,
            "code_centre": f"CEC{rng.randrange(100, 999)}",
        },
        "defunt": {
            **personne(rng, sexe=sexe, avec_profession=True),
            "age_au_deces": age,
            "date_deces": (date_acte - timedelta(
                days=rng.randrange(0, 60))).isoformat(),
            "lieu_deces": {
                "region": region,
                "commune": commune,
                "etablissement": rng.choice(
                    ["Hôpital régional", "Domicile", "Centre de santé",
                     "Voie publique"]),
            },
        },
        "declarant": {
            **personne(rng),
            "qualite": rng.choice(["Conjoint", "Fils/Fille", "Frère/Sœur",
                                   "Voisin", "Agent hospitalier"]),
        },
        "officier_etat_civil": personne(rng),
        "mentions_marginales": [],
        "numerise": rng.random() < 0.48,
    }
    if rng.random() < 0.30:
        document["cause_deces"] = rng.choice(CAUSES_DECES)
    return document


# --------------------------------------------------------------------------
# Ligne de commande
# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Génère des actes d'état civil au format JSON Lines.")
    parser.add_argument("--actes", type=int, default=50_000,
                        help="nombre total d'actes (défaut : 50 000)")
    parser.add_argument("--sortie", type=Path,
                        default=Path("actes_etat_civil.jsonl"),
                        help="fichier de sortie (JSON Lines)")
    parser.add_argument("--graine", type=int, default=2026,
                        help="graine aléatoire, pour des données reproductibles")
    parser.add_argument("--indente", action="store_true",
                        help="produit aussi un extrait lisible de 5 documents")
    args = parser.parse_args(argv)

    rng = random.Random(args.graine)
    args.sortie.parent.mkdir(parents=True, exist_ok=True)

    # Répartition réaliste : les naissances dominent largement.
    fabriques = [(acte_naissance, 0.72), (acte_deces, 0.16),
                 (acte_mariage, 0.12)]
    fonctions = [f for f, _ in fabriques]
    poids = [p for _, p in fabriques]

    compteurs: dict[str, int] = {}
    with args.sortie.open("w", encoding="utf-8") as sortie:
        for i in range(1, args.actes + 1):
            fabrique = rng.choices(fonctions, weights=poids)[0]
            document = fabrique(rng, i)
            compteurs[document["type_acte"]] = compteurs.get(
                document["type_acte"], 0) + 1
            sortie.write(json.dumps(document, ensure_ascii=False) + "\n")
            if i % 10_000 == 0:
                print(f"  … {i:,}".replace(",", " "), end="\r", flush=True)

    taille = args.sortie.stat().st_size / 1024**2
    print(f"\n✔ {args.sortie} — {args.actes:,} actes, {taille:.1f} Mo"
          .replace(",", " "))
    for type_acte, nombre in sorted(compteurs.items()):
        print(f"    {type_acte:<12} {nombre:>8,}".replace(",", " "))

    if args.indente:
        extrait = args.sortie.with_name(args.sortie.stem + "_extrait.json")
        with args.sortie.open(encoding="utf-8") as source:
            documents = [json.loads(next(source)) for _ in range(5)]
        extrait.write_text(
            json.dumps(documents, ensure_ascii=False, indent=2),
            encoding="utf-8")
        print(f"    extrait lisible : {extrait}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
