"""
Générateur de données simulées — Formation Big Data ANSD / Data Innovation Lab.

Produit des jeux de données réalistes du domaine de la statistique publique
sénégalaise, à volumétrie ajustable :

  - individus    : fichier de recensement (le gros fichier)
  - regions      : table de référence des régions (petite, pour les jointures)
  - etat_civil   : seconde source, partiellement recouvrante, avec variantes
                   d'écriture (module appariement / rapprochement flou)
  - entreprises  : répertoire d'entreprises (sujets de projet, jointures)

Les données sont volontairement imparfaites (valeurs manquantes, casse
incohérente, âges aberrants, doublons, formats de date multiples) afin de
reproduire les défauts habituels des données.

Exemples
--------
    python generate_data.py --auto
    python generate_data.py --jeu individus --lignes 6_000_000
    python generate_data.py --jeu tous --lignes 6_000_000 --format both

Aucune dépendance en dehors de numpy et pandas (pyarrow pour le format
Parquet). La génération est vectorisée et écrite par blocs : elle ne charge
jamais l'ensemble du fichier en mémoire.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Référentiels
# --------------------------------------------------------------------------

# Régions du Sénégal, chef-lieu et poids démographique indicatif.
REGIONS = [
    # (code, région, chef-lieu, poids, part urbaine)
    ("DK", "Dakar", "Dakar", 0.230, 0.97),
    ("TH", "Thiès", "Thiès", 0.130, 0.48),
    ("DB", "Diourbel", "Diourbel", 0.110, 0.40),
    ("KL", "Kaolack", "Kaolack", 0.072, 0.38),
    ("SL", "Saint-Louis", "Saint-Louis", 0.065, 0.44),
    ("LG", "Louga", "Louga", 0.060, 0.26),
    ("FK", "Fatick", "Fatick", 0.055, 0.20),
    ("KD", "Kolda", "Kolda", 0.050, 0.26),
    ("TC", "Tambacounda", "Tambacounda", 0.050, 0.25),
    ("ZG", "Ziguinchor", "Ziguinchor", 0.043, 0.53),
    ("MT", "Matam", "Matam", 0.042, 0.18),
    ("KF", "Kaffrine", "Kaffrine", 0.040, 0.18),
    ("SE", "Sédhiou", "Sédhiou", 0.035, 0.17),
    ("KE", "Kédougou", "Kédougou", 0.018, 0.24),
]

DEPARTEMENTS = {
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

NOMS = [
    "Diop", "Ndiaye", "Fall", "Sarr", "Ba", "Sow", "Diallo", "Gueye", "Faye",
    "Sy", "Cissé", "Mbaye", "Seck", "Thiam", "Dieng", "Camara", "Sagna",
    "Badji", "Diatta", "Mané", "Sané", "Diouf", "Wade", "Kane", "Barry",
    "Touré", "Diagne", "Samb", "Ndour", "Lô", "Niang", "Coly", "Goudiaby",
    "Bodian", "Tine", "Sylla", "Bâ", "Dramé", "Konaté", "Danfa", "Sonko",
    "Diedhiou", "Balde", "Kâ", "Ndao", "Mendy", "Preira", "Traoré", "Kébé",
]

PRENOMS_M = [
    "Mamadou", "Ousmane", "Ibrahima", "Moussa", "Cheikh", "Abdoulaye",
    "Modou", "Alioune", "Babacar", "Ababacar", "Amadou", "Souleymane",
    "Assane", "Malick", "Serigne", "Pape", "Lamine", "Idrissa", "Boubacar",
    "El Hadji", "Saliou", "Mor", "Bara", "Daouda", "Samba", "Insa",
]

PRENOMS_F = [
    "Fatou", "Aminata", "Awa", "Ndeye", "Astou", "Khadija", "Maimouna",
    "Seynabou", "Adama", "Coumba", "Bineta", "Sokhna", "Rokhaya", "Mariama",
    "Aissatou", "Dieynaba", "Yacine", "Nafissatou", "Oumou", "Anta",
    "Marième", "Fatoumata", "Kine", "Penda", "Diarra", "Soda",
]

SIT_MATRIMONIALE = ["Célibataire", "Marié(e) monogame", "Marié(e) polygame",
                    "Veuf(ve)", "Divorcé(e)"]
NIVEAU_INSTRUCTION = ["Aucun", "Coranique", "Primaire", "Moyen", "Secondaire",
                      "Supérieur"]
SIT_ACTIVITE = ["Occupé", "Chômeur", "Élève/Étudiant", "Au foyer", "Retraité",
                "Inactif"]
SECTEURS = ["Agriculture, élevage, pêche", "Industrie", "BTP", "Commerce",
            "Transport", "Services", "Administration publique", "Éducation",
            "Santé", "Artisanat"]
LIENS = ["Chef de ménage", "Époux/Épouse", "Fils/Fille", "Père/Mère",
         "Frère/Sœur", "Petit-fils/Petite-fille", "Neveu/Nièce", "Autre parent",
         "Sans lien de parenté"]
TYPE_LOGEMENT = ["Maison basse", "Maison à étage", "Appartement", "Baraque",
                 "Case", "Autre"]
SOURCE_EAU = ["Robinet intérieur", "Robinet dans la cour", "Borne fontaine",
              "Puits protégé", "Puits non protégé", "Forage", "Eau de surface"]
FORMES_JURIDIQUES = ["SARL", "SA", "SUARL", "GIE", "Entreprise individuelle",
                     "Association", "Coopérative"]

# --------------------------------------------------------------------------
# Outils
# --------------------------------------------------------------------------


def dimensionner_selon_ram(defaut: int = 3_000_000) -> int:
    """Propose un nombre de lignes adapté à la mémoire disponible du poste.

    L'objectif pédagogique est que le fichier soit inconfortable, mais que sa
    génération reste possible sur toutes les machines de la salle.
    """
    try:
        import psutil  # dépendance optionnelle

        go_dispo = psutil.virtual_memory().available / 1024**3
    except Exception:
        return defaut

    # Repères mesurés : ~180 octets par ligne en CSV, ~320 octets une fois
    # chargée en mémoire par pandas, et environ 30 s de génération par million
    # de lignes. On vise un fichier occupant 30 à 40 % de la mémoire libre :
    # le chargement passe, mais un tri ou une jointure (2 à 3 fois la taille
    # de la table) fait basculer la machine.
    if go_dispo < 4:
        return 3_000_000
    if go_dispo < 8:
        return 6_000_000
    if go_dispo < 16:
        return 10_000_000
    return 12_000_000


def _poids_regions() -> np.ndarray:
    poids = np.array([r[3] for r in REGIONS], dtype=float)
    return poids / poids.sum()


def _tailles_menages(rng: np.random.Generator, n_lignes: int) -> np.ndarray:
    """Tire des tailles de ménage jusqu'à couvrir n_lignes individus.

    La taille moyenne des ménages sénégalais étant élevée, la distribution est
    centrée autour de 7-9 personnes.
    """
    tailles_possibles = np.arange(1, 21)
    poids = np.exp(-((tailles_possibles - 8) ** 2) / 18.0)
    poids /= poids.sum()

    estimation = int(n_lignes / 8 * 1.3) + 10
    tailles = rng.choice(tailles_possibles, size=estimation, p=poids)
    cumul = np.cumsum(tailles)
    n_menages = int(np.searchsorted(cumul, n_lignes)) + 1
    tailles = tailles[:n_menages]
    # Ajustement du dernier ménage pour tomber exactement sur n_lignes.
    depassement = int(tailles.sum() - n_lignes)
    if depassement > 0:
        tailles[-1] = max(1, tailles[-1] - depassement)
    if tailles.sum() < n_lignes:
        tailles = np.append(tailles, n_lignes - tailles.sum())
    return tailles


def _degrader_casse(rng: np.random.Generator, valeurs: np.ndarray,
                    taux: float) -> np.ndarray:
    """Introduit des incohérences de casse et d'espacement (données saisies)."""
    valeurs = valeurs.astype(object)
    n = len(valeurs)
    masque = rng.random(n) < taux
    idx = np.flatnonzero(masque)
    if idx.size == 0:
        return valeurs
    variantes = rng.integers(0, 3, size=idx.size)
    for i, v in zip(idx, variantes):
        s = str(valeurs[i])
        if v == 0:
            valeurs[i] = s.upper()
        elif v == 1:
            valeurs[i] = s.lower()
        else:
            valeurs[i] = f"  {s} "
    return valeurs


def _trouer(rng: np.random.Generator, serie: pd.Series, taux: float) -> pd.Series:
    """Remplace aléatoirement une fraction des valeurs par des manquants."""
    masque = rng.random(len(serie)) < taux
    serie = serie.copy()
    serie[masque] = np.nan
    return serie


# --------------------------------------------------------------------------
# Jeu 1 — Recensement des individus
# --------------------------------------------------------------------------


def _bloc_individus(rng: np.random.Generator, n: int, offset_ind: int,
                    offset_men: int, degrader: bool) -> pd.DataFrame:
    """Construit un bloc de n individus regroupés en ménages."""
    tailles = _tailles_menages(rng, n)
    n_menages = len(tailles)
    n = int(tailles.sum())

    idx_menage = np.repeat(np.arange(n_menages), tailles)
    debut_menage = np.repeat(np.cumsum(tailles) - tailles, tailles)
    rang_dans_menage = np.arange(n) - debut_menage

    # Localisation : constante à l'intérieur d'un ménage.
    poids = _poids_regions()
    reg_menage = rng.choice(len(REGIONS), size=n_menages, p=poids)
    reg = reg_menage[idx_menage]
    noms_regions = np.array([r[1] for r in REGIONS])
    parts_urbaines = np.array([r[4] for r in REGIONS])

    region = noms_regions[reg]
    urbain_menage = rng.random(n_menages) < parts_urbaines[reg_menage]
    milieu = np.where(urbain_menage[idx_menage], "Urbain", "Rural")

    departement = np.empty(n, dtype=object)
    for i, (_, nom_region, *_rest) in enumerate(REGIONS):
        deps = np.array(DEPARTEMENTS[nom_region])
        masque = reg == i
        k = int(masque.sum())
        if k:
            departement[masque] = rng.choice(deps, size=k)

    # Démographie : structure très jeune, chefs de ménage plus âgés.
    age = rng.gamma(shape=2.0, scale=11.0, size=n).astype(int)
    age = np.clip(age, 0, 98)
    est_chef = rang_dans_menage == 0
    age[est_chef] = np.clip(
        rng.normal(48, 13, size=int(est_chef.sum())).astype(int), 18, 95
    )

    sexe = rng.choice(["M", "F"], size=n, p=[0.487, 0.513])
    # Le chef de ménage est plus souvent un homme.
    sexe[est_chef] = rng.choice(["M", "F"], size=int(est_chef.sum()),
                                p=[0.73, 0.27])

    prenom = np.empty(n, dtype=object)
    masque_h = sexe == "M"
    prenom[masque_h] = rng.choice(PRENOMS_M, size=int(masque_h.sum()))
    prenom[~masque_h] = rng.choice(PRENOMS_F, size=int((~masque_h).sum()))
    # Le nom de famille est partagé au sein du ménage.
    nom_menage = rng.choice(NOMS, size=n_menages)
    nom = nom_menage[idx_menage]

    # Lien avec le chef de ménage, cohérent avec l'âge.
    lien = np.where(
        est_chef, "Chef de ménage",
        np.where(age < 18, "Fils/Fille",
                 rng.choice(LIENS[1:], size=n,
                            p=[0.22, 0.30, 0.06, 0.12, 0.10, 0.08, 0.08, 0.04]))
    )

    # Situation matrimoniale, cohérente avec l'âge.
    sit_mat = np.where(
        age < 15, "Célibataire",
        rng.choice(SIT_MATRIMONIALE, size=n, p=[0.34, 0.36, 0.18, 0.08, 0.04])
    )

    # Instruction : dépend de l'âge et du milieu.
    p_inst_jeune = [0.18, 0.14, 0.30, 0.18, 0.14, 0.06]
    p_inst_age = [0.44, 0.22, 0.16, 0.08, 0.07, 0.03]
    instruction = np.where(
        age < 35,
        rng.choice(NIVEAU_INSTRUCTION, size=n, p=p_inst_jeune),
        rng.choice(NIVEAU_INSTRUCTION, size=n, p=p_inst_age),
    )
    instruction = instruction.astype(object)
    sans_instruction = (instruction == "Aucun") | (age < 3)
    instruction[age < 3] = None
    sait_lire = np.where(
        sans_instruction,
        rng.choice(["Oui", "Non"], size=n, p=[0.12, 0.88]),
        rng.choice(["Oui", "Non"], size=n, p=[0.93, 0.07]),
    )

    activite = np.where(
        age < 6, "Inactif",
        np.where(age < 18,
                 rng.choice(["Élève/Étudiant", "Occupé", "Inactif"], size=n,
                            p=[0.72, 0.14, 0.14]),
                 np.where(age >= 65,
                          rng.choice(["Retraité", "Occupé", "Inactif"], size=n,
                                     p=[0.18, 0.30, 0.52]),
                          np.where(
                              milieu == "Urbain",
                              # En ville : plus de chômage et de scolarisation.
                              rng.choice(SIT_ACTIVITE, size=n,
                                         p=[0.45, 0.14, 0.13, 0.20, 0.03, 0.05]),
                              # En milieu rural : emploi agricole plus fréquent.
                              rng.choice(SIT_ACTIVITE, size=n,
                                         p=[0.63, 0.05, 0.06, 0.19, 0.01, 0.06]),
                          ))),
    )
    secteur = rng.choice(SECTEURS, size=n,
                         p=[0.30, 0.05, 0.07, 0.20, 0.06, 0.14,
                            0.05, 0.04, 0.03, 0.06]).astype(object)
    secteur[activite != "Occupé"] = None

    # Date de naissance déduite de l'âge, avec trois formats de saisie.
    annee = 2026 - age - rng.integers(0, 2, size=n)
    mois = rng.integers(1, 13, size=n)
    jour = rng.integers(1, 29, size=n)
    fmt = rng.integers(0, 3, size=n) if degrader else np.zeros(n, dtype=int)
    a = np.char.mod("%04d", annee)
    m = np.char.mod("%02d", mois)
    j = np.char.mod("%02d", jour)
    date_naissance = np.empty(n, dtype=object)
    for code, gabarit in enumerate(((a, "-", m, "-", j),      # AAAA-MM-JJ
                                    (j, "/", m, "/", a),      # JJ/MM/AAAA
                                    (j, "-", m, "-", a))):    # JJ-MM-AAAA
        masque = fmt == code
        if not masque.any():
            continue
        g1, s1, g2, s2, g3 = gabarit
        date_naissance[masque] = np.char.add(
            np.char.add(np.char.add(g1[masque], s1),
                        np.char.add(g2[masque], s2)), g3[masque])

    # Caractéristiques du logement : constantes dans le ménage.
    type_log_menage = rng.choice(TYPE_LOGEMENT, size=n_menages,
                                 p=[0.44, 0.12, 0.10, 0.10, 0.20, 0.04])
    nb_pieces_menage = np.clip(rng.poisson(3.4, size=n_menages), 1, 15)
    eau_menage = rng.choice(SOURCE_EAU, size=n_menages,
                            p=[0.26, 0.22, 0.16, 0.09, 0.08, 0.13, 0.06])
    elec_menage = np.where(urbain_menage,
                           rng.choice(["Oui", "Non"], size=n_menages,
                                      p=[0.92, 0.08]),
                           rng.choice(["Oui", "Non"], size=n_menages,
                                      p=[0.45, 0.55]))

    df = pd.DataFrame({
        "id_individu": np.arange(offset_ind, offset_ind + n),
        "id_menage": np.char.mod("MEN%09d", idx_menage + offset_men),
        "region": region,
        "departement": departement,
        "milieu_residence": milieu,
        "nom": nom,
        "prenom": prenom,
        "sexe": sexe,
        "age": age,
        "date_naissance": date_naissance,
        "lien_chef_menage": lien,
        "situation_matrimoniale": sit_mat,
        "niveau_instruction": instruction,
        "sait_lire_ecrire": sait_lire,
        "situation_activite": activite,
        "secteur_activite": secteur,
        "nationalite": rng.choice(["Sénégalaise", "Autre CEDEAO", "Autre"],
                                  size=n, p=[0.965, 0.028, 0.007]),
        "type_logement": type_log_menage[idx_menage],
        "nb_pieces": nb_pieces_menage[idx_menage],
        "source_eau": eau_menage[idx_menage],
        "electricite": elec_menage[idx_menage],
    })

    if degrader:
        df["region"] = _degrader_casse(rng, df["region"].to_numpy(), 0.04)
        df["niveau_instruction"] = _trouer(rng, df["niveau_instruction"], 0.03)
        df["sait_lire_ecrire"] = _trouer(rng, df["sait_lire_ecrire"], 0.02)
        df["nb_pieces"] = _trouer(rng, df["nb_pieces"].astype("float"), 0.015)
        # Âges aberrants : codes de non-réponse mal nettoyés.
        aberrants = rng.random(n) < 0.002
        df.loc[aberrants, "age"] = rng.choice([999, -1, 0],
                                              size=int(aberrants.sum()))
        # Doublons exacts : ressaisies du même questionnaire.
        n_doublons = int(n * 0.004)
        if n_doublons:
            doublons = df.sample(n=n_doublons, random_state=int(rng.integers(1e6)))
            df = pd.concat([df, doublons], ignore_index=True)
            df = df.sample(frac=1.0, random_state=int(rng.integers(1e6)))
            df = df.reset_index(drop=True)

    return df


def generer_individus(chemin: Path, n_lignes: int, graine: int,
                      taille_bloc: int, formats: list[str],
                      degrader: bool = True) -> None:
    rng = np.random.default_rng(graine)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    csv = chemin.with_suffix(".csv")
    if csv.exists():
        csv.unlink()

    offset_ind, offset_men, ecrites = 1, 1, 0
    premier_bloc = True
    morceaux_parquet = []

    while ecrites < n_lignes:
        n = min(taille_bloc, n_lignes - ecrites)
        bloc = _bloc_individus(rng, n, offset_ind, offset_men, degrader)
        if "csv" in formats:
            bloc.to_csv(csv, mode="a", header=premier_bloc, index=False)
        if "parquet" in formats:
            morceaux_parquet.append(bloc)
        offset_ind += n
        offset_men += bloc["id_menage"].nunique()
        ecrites += n
        premier_bloc = False
        print(f"  … {ecrites:>12,} / {n_lignes:,} individus".replace(",", " "),
              end="\r", flush=True)

    print()
    if "parquet" in formats:
        pd.concat(morceaux_parquet, ignore_index=True).to_parquet(
            chemin.with_suffix(".parquet"), index=False)
        del morceaux_parquet

    if "csv" in formats:
        taille = csv.stat().st_size / 1024**2
        print(f"  ✔ {csv.name} — {taille:,.0f} Mo".replace(",", " "))


# --------------------------------------------------------------------------
# Jeu 2 — Table de référence des régions
# --------------------------------------------------------------------------


def generer_regions(chemin: Path, formats: list[str]) -> None:
    superficies = {
        "Dakar": 547, "Thiès": 6601, "Diourbel": 4824, "Kaolack": 5357,
        "Saint-Louis": 19034, "Louga": 24889, "Fatick": 6849, "Kolda": 13718,
        "Tambacounda": 42706, "Ziguinchor": 7339, "Matam": 29445,
        "Kaffrine": 11262, "Sédhiou": 7341, "Kédougou": 16800,
    }
    df = pd.DataFrame({
        "code_region": [r[0] for r in REGIONS],
        "region": [r[1] for r in REGIONS],
        "chef_lieu": [r[2] for r in REGIONS],
        "superficie_km2": [superficies[r[1]] for r in REGIONS],
        "poids_demographique": [r[3] for r in REGIONS],
        "part_urbaine": [r[4] for r in REGIONS],
    })
    chemin.parent.mkdir(parents=True, exist_ok=True)
    if "csv" in formats:
        df.to_csv(chemin.with_suffix(".csv"), index=False)
    if "parquet" in formats:
        df.to_parquet(chemin.with_suffix(".parquet"), index=False)
    print(f"  ✔ {chemin.stem} — {len(df)} régions")


# --------------------------------------------------------------------------
# Jeu 3 — Seconde source : registre d'état civil
# --------------------------------------------------------------------------


def _brouiller_texte(rng: np.random.Generator, valeurs: np.ndarray,
                     taux: float) -> np.ndarray:
    """Introduit des variantes d'écriture : lettre doublée, accent perdu…"""
    valeurs = valeurs.astype(object).copy()
    idx = np.flatnonzero(rng.random(len(valeurs)) < taux)
    accents = str.maketrans("éèêëàâîïôöûüç", "eeeeaaiioouuc")
    for i in idx:
        s = str(valeurs[i])
        choix = rng.integers(0, 4)
        if choix == 0 and len(s) > 2:
            p = int(rng.integers(1, len(s)))
            s = s[:p] + s[p] + s[p:]          # lettre doublée
        elif choix == 1:
            s = s.translate(accents)          # accents perdus
        elif choix == 2 and len(s) > 3:
            p = int(rng.integers(0, len(s) - 1))
            s = s[:p] + s[p + 1] + s[p] + s[p + 2:]   # inversion de lettres
        else:
            s = s.upper()
        valeurs[i] = s
    return valeurs


def generer_etat_civil(chemin_individus: Path, chemin: Path, graine: int,
                       formats: list[str], taux_recouvrement: float = 0.7,
                       n_max: int = 400_000) -> None:
    """Construit une seconde source recouvrant partiellement le recensement.

    Le fichier de vérité terrain (correspondances réelles) est écrit à part :
    il sert à mesurer la qualité de l'appariement, jamais à le réaliser.
    """
    rng = np.random.default_rng(graine + 1)
    source = chemin_individus.with_suffix(".csv")
    if not source.exists():
        print("  ! Fichier des individus absent : état civil ignoré.")
        return

    colonnes = ["id_individu", "nom", "prenom", "sexe", "date_naissance",
                "region", "departement"]
    base = pd.read_csv(source, usecols=colonnes, nrows=n_max * 2)
    base = base.drop_duplicates(subset="id_individu")
    n_apparies = int(min(len(base), n_max) * taux_recouvrement)
    apparies = base.sample(n=n_apparies, random_state=graine).reset_index(drop=True)

    df = pd.DataFrame({
        "id_acte": [f"EC{i:08d}" for i in range(1, len(apparies) + 1)],
        "nom_famille": _brouiller_texte(rng, apparies["nom"].to_numpy(), 0.35),
        "prenoms": _brouiller_texte(rng, apparies["prenom"].to_numpy(), 0.30),
        "sexe": apparies["sexe"],
        "date_naiss": apparies["date_naissance"],
        "lieu_naissance": apparies["departement"],
        "region_declaration": apparies["region"],
    })

    # Individus présents à l'état civil mais absents du recensement.
    n_hors = int(len(df) * 0.15)
    hors = pd.DataFrame({
        "id_acte": [f"EC{i:08d}" for i in range(len(df) + 1, len(df) + n_hors + 1)],
        "nom_famille": rng.choice(NOMS, size=n_hors),
        "prenoms": rng.choice(PRENOMS_M + PRENOMS_F, size=n_hors),
        "sexe": rng.choice(["M", "F"], size=n_hors),
        "date_naiss": pd.Series(rng.integers(1950, 2026, size=n_hors)).astype(str)
                      + "-01-01",
        "lieu_naissance": rng.choice(
            [d for deps in DEPARTEMENTS.values() for d in deps], size=n_hors),
        "region_declaration": rng.choice([r[1] for r in REGIONS], size=n_hors),
    })

    verite = pd.DataFrame({
        "id_acte": df["id_acte"],
        "id_individu": apparies["id_individu"],
    })

    complet = pd.concat([df, hors], ignore_index=True)
    complet = complet.sample(frac=1.0, random_state=graine).reset_index(drop=True)

    chemin.parent.mkdir(parents=True, exist_ok=True)
    if "csv" in formats:
        complet.to_csv(chemin.with_suffix(".csv"), index=False)
        verite.to_csv(chemin.with_name(chemin.stem + "_verite.csv"), index=False)
    if "parquet" in formats:
        complet.to_parquet(chemin.with_suffix(".parquet"), index=False)
    print(f"  ✔ {chemin.stem} — {len(complet):,} actes ".replace(",", " ")
          + f"({len(verite):,} correspondances réelles)".replace(",", " "))


# --------------------------------------------------------------------------
# Jeu 4 — Répertoire d'entreprises
# --------------------------------------------------------------------------


def generer_entreprises(chemin: Path, n: int, graine: int,
                        formats: list[str]) -> None:
    rng = np.random.default_rng(graine + 2)
    poids = _poids_regions()
    reg = rng.choice(len(REGIONS), size=n, p=poids)
    noms_regions = np.array([r[1] for r in REGIONS])

    departement = np.empty(n, dtype=object)
    for i, (_, nom_region, *_rest) in enumerate(REGIONS):
        masque = reg == i
        k = int(masque.sum())
        if k:
            departement[masque] = rng.choice(np.array(DEPARTEMENTS[nom_region]),
                                             size=k)

    enseignes = ["Sénégal", "Teranga", "Sahel", "Atlantique", "Baobab",
                 "Cayor", "Casamance", "Saloum", "Ferlo", "Dakar", "Niayes"]
    activites = ["Services", "Distribution", "Industries", "Logistique",
                 "Agro", "BTP", "Conseil", "Technologies", "Négoce"]
    forme = rng.choice(FORMES_JURIDIQUES, size=n)
    raison = (pd.Series(rng.choice(enseignes, size=n)) + " "
              + pd.Series(rng.choice(activites, size=n)) + " "
              + pd.Series(forme))

    effectif = np.clip(rng.lognormal(1.6, 1.3, size=n).astype(int), 1, 5000)
    df = pd.DataFrame({
        "id_entreprise": [f"ENT{i:07d}" for i in range(1, n + 1)],
        "raison_sociale": raison,
        "forme_juridique": forme,
        "secteur_activite": rng.choice(SECTEURS, size=n),
        "region": noms_regions[reg],
        "departement": departement,
        "annee_creation": rng.integers(1975, 2027, size=n),
        "effectif": effectif,
        "chiffre_affaires_fcfa": (effectif * rng.lognormal(15.0, 1.1, size=n)
                                  ).astype("int64"),
        "statut": rng.choice(["Actif", "En sommeil", "Radié"], size=n,
                             p=[0.82, 0.11, 0.07]),
    })
    df["chiffre_affaires_fcfa"] = _trouer(
        rng, df["chiffre_affaires_fcfa"].astype("float"), 0.08)

    chemin.parent.mkdir(parents=True, exist_ok=True)
    if "csv" in formats:
        df.to_csv(chemin.with_suffix(".csv"), index=False)
    if "parquet" in formats:
        df.to_parquet(chemin.with_suffix(".parquet"), index=False)
    print(f"  ✔ {chemin.stem} — {len(df):,} entreprises".replace(",", " "))


# --------------------------------------------------------------------------
# Ligne de commande
# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Génère les jeux de données de la formation Big Data ANSD.")
    parser.add_argument("--jeu", default="tous",
                        choices=["tous", "individus", "regions", "etat_civil",
                                 "entreprises"],
                        help="jeu de données à produire (défaut : tous)")
    parser.add_argument("--lignes", type=int, default=5_000_000,
                        help="nombre d'individus du recensement")
    parser.add_argument("--auto", action="store_true",
                        help="dimensionne le fichier selon la RAM disponible")
    parser.add_argument("--entreprises", type=int, default=150_000,
                        help="nombre d'entreprises du répertoire")
    parser.add_argument("--sortie", type=Path, default=Path("."),
                        help="répertoire de sortie (défaut : dossier courant)")
    parser.add_argument("--format", default="csv",
                        choices=["csv", "parquet", "both"],
                        help="format des fichiers produits")
    parser.add_argument("--graine", type=int, default=2026,
                        help="graine aléatoire, pour des données reproductibles")
    parser.add_argument("--taille-bloc", type=int, default=500_000,
                        help="nombre de lignes générées par bloc en mémoire")
    parser.add_argument("--propre", action="store_true",
                        help="désactive l'injection d'imperfections")
    args = parser.parse_args(argv)

    formats = ["csv", "parquet"] if args.format == "both" else [args.format]
    n_lignes = dimensionner_selon_ram() if args.auto else args.lignes
    sortie = args.sortie
    sortie.mkdir(parents=True, exist_ok=True)

    print(f"Génération des données — graine {args.graine}, sortie : {sortie}/")

    if args.jeu in ("tous", "regions"):
        generer_regions(sortie / "regions", formats)

    if args.jeu in ("tous", "individus"):
        libre = shutil.disk_usage(sortie).free / 1024**3
        estimation = n_lignes * 190 / 1024**3
        if libre < estimation * 1.5:
            print(f"  ! Espace disque insuffisant : {libre:.1f} Go libres pour "
                  f"~{estimation:.1f} Go attendus.")
            return 1
        print(f"  Recensement : {n_lignes:,} individus "
              .replace(",", " ") + f"(~{estimation:.1f} Go en CSV)")
        generer_individus(sortie / "individus", n_lignes, args.graine,
                          args.taille_bloc, formats, degrader=not args.propre)

    if args.jeu in ("tous", "etat_civil"):
        generer_etat_civil(sortie / "individus", sortie / "etat_civil",
                           args.graine, formats)

    if args.jeu in ("tous", "entreprises"):
        generer_entreprises(sortie / "entreprises", args.entreprises,
                            args.graine, formats)

    print("Terminé.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
