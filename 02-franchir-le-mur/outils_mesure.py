"""Outils de mesure partagés — module `02-franchir-le-mur`.

Tous les notebooks du bloc importent ce module, afin que les quatre outils
comparés (pandas, Polars, DuckDB, Dask) soient mesurés exactement de la même
façon. Les résultats sont accumulés dans `resultats/` et rassemblés par le
notebook de comparaison.

Utilisation type dans un notebook :

    from outils_mesure import (contexte_machine, mesurer, enregistrer,
                               charger_toutes, FICHIER)

    contexte_machine()

    mesures = []
    mesures.append(mesurer("lecture", lambda: pl.read_csv(FICHIER)))
    enregistrer(mesures, outil="polars", volume="2M")
"""

from __future__ import annotations

import gc
import os
import threading
import time
from pathlib import Path

import pandas as pd
import psutil

# --------------------------------------------------------------------------
# Emplacements
# --------------------------------------------------------------------------

DOSSIER_DONNEES = Path("..") / "00-data"
FICHIER = DOSSIER_DONNEES / "individus.csv"
FICHIER_REGIONS = DOSSIER_DONNEES / "regions.csv"
DOSSIER_RESULTATS = Path("resultats")

# Volume de référence pour la comparaison à quatre outils : pandas doit pouvoir
# le tenir sur toutes les machines.
VOLUME_COMPARAISON = 2_000_000

# Les cinq opérations comparées, dans un ordre fixe (voir note sur le cache).
OPERATIONS = ["lecture", "filtre", "agregation", "tri", "jointure"]

_processus = psutil.Process(os.getpid())


# --------------------------------------------------------------------------
# Contexte d'exécution
# --------------------------------------------------------------------------


def memoire_mo() -> float:
    """Mémoire actuellement occupée par le noyau Python, en Mo."""
    return _processus.memory_info().rss / 1024**2


def contexte_machine(afficher: bool = True) -> dict:
    """Renvoie (et affiche) les caractéristiques du poste.

    Le nombre de cœurs est déterminant pour interpréter la comparaison :
    les moteurs multi-cœurs ne peuvent pas montrer leur avantage sur une
    machine qui n'en a qu'un.
    """
    infos = {
        "coeurs_logiques": psutil.cpu_count(logical=True),
        "coeurs_physiques": psutil.cpu_count(logical=False),
        "memoire_totale_go": round(psutil.virtual_memory().total / 1024**3, 1),
        "memoire_libre_go": round(psutil.virtual_memory().available / 1024**3, 1),
        "taille_fichier_mo": round(FICHIER.stat().st_size / 1024**2)
        if FICHIER.exists() else None,
    }
    if afficher:
        print(f"Cœurs logiques    : {infos['coeurs_logiques']}")
        print(f"Cœurs physiques   : {infos['coeurs_physiques']}")
        print(f"Mémoire totale    : {infos['memoire_totale_go']} Go")
        print(f"Mémoire libre     : {infos['memoire_libre_go']} Go")
        print(f"Fichier individus : {infos['taille_fichier_mo']} Mo")
        if infos["coeurs_logiques"] and infos["coeurs_logiques"] < 4:
            print("\n! Peu de cœurs disponibles : les moteurs multi-cœurs "
                  "(Polars, DuckDB, Dask)\n  ne pourront pas montrer leur "
                  "avantage sur cette machine.")
    return infos


# --------------------------------------------------------------------------
# Mesure
# --------------------------------------------------------------------------


def mesurer(operation: str, fonction, intervalle: float = 0.02,
            afficher: bool = True) -> dict:
    """Chronomètre une opération en surveillant son pic de mémoire.

    En cas d'échec (mémoire insuffisante, opération non supportée), l'erreur
    est capturée et enregistrée : un échec est une mesure, pas un accident.

    Renvoie un dictionnaire prêt à être empilé dans une liste de mesures.
    """
    gc.collect()
    depart_memoire = memoire_mo()
    arret = False
    sommet = [depart_memoire]

    def surveiller():
        while not arret:
            sommet[0] = max(sommet[0], memoire_mo())
            time.sleep(intervalle)

    veilleur = threading.Thread(target=surveiller, daemon=True)
    veilleur.start()

    statut, motif, duree = "ok", "", None
    depart = time.perf_counter()
    try:
        resultat = fonction()
        duree = time.perf_counter() - depart
        del resultat
    except MemoryError:
        duree = time.perf_counter() - depart
        statut, motif = "échec", "mémoire insuffisante"
    except Exception as erreur:  # noqa: BLE001 — on veut vraiment tout capturer
        duree = time.perf_counter() - depart
        statut = "échec"
        motif = f"{type(erreur).__name__}: {str(erreur)[:120]}"
    finally:
        arret = True
        veilleur.join()
        gc.collect()

    mesure = {
        "operation": operation,
        "secondes": round(duree, 3) if duree is not None else None,
        "pic_memoire_mo": round(sommet[0]),
        "surcout_memoire_mo": round(sommet[0] - depart_memoire),
        "statut": statut,
        "motif": motif,
    }

    if afficher:
        if statut == "ok":
            print(f"  {operation:<12} {mesure['secondes']:>8.3f} s   "
                  f"pic {mesure['pic_memoire_mo']:>6} Mo")
        else:
            print(f"  {operation:<12} {'ÉCHEC':>10}   {motif}")
    return mesure


def enregistrer(mesures: list[dict], outil: str, volume: str,
                lignes: int | None = None) -> pd.DataFrame:
    """Enregistre une campagne de mesures dans `resultats/`.

    `volume` vaut "2M" pour la comparaison de référence, ou "complet" pour la
    passe sur le fichier entier.
    """
    DOSSIER_RESULTATS.mkdir(exist_ok=True)
    tableau = pd.DataFrame(mesures)
    tableau.insert(0, "outil", outil)
    tableau.insert(1, "volume", volume)
    if lignes is not None:
        tableau.insert(2, "lignes", lignes)
    chemin = DOSSIER_RESULTATS / f"mesures_{outil}_{volume}.csv"
    tableau.to_csv(chemin, index=False)
    print(f"\n→ {chemin}")
    return tableau


def charger_toutes() -> pd.DataFrame:
    """Rassemble toutes les campagnes de mesures enregistrées."""
    fichiers = sorted(DOSSIER_RESULTATS.glob("mesures_*.csv"))
    if not fichiers:
        raise FileNotFoundError(
            "Aucune mesure trouvée. Exécutez d'abord les notebooks 01 à 03.")
    return pd.concat([pd.read_csv(f) for f in fichiers], ignore_index=True)


# --------------------------------------------------------------------------
# Note de protocole, affichable dans les notebooks
# --------------------------------------------------------------------------

PROTOCOLE = """\
Protocole de mesure — à lire avant d'interpréter les résultats

1. Deux lectures de la comparaison
   - « même travail »   : chaque outil charge tout le fichier, puis calcule.
                          On compare la vitesse brute des moteurs.
   - « même objectif »  : on demande seulement le résultat final ; chaque outil
                          est libre d'optimiser (ne lire que les colonnes
                          utiles, filtrer pendant la lecture…). C'est la
                          comparaison réaliste — et les écarts y sont bien
                          plus grands.

2. Cache du système de fichiers
   La deuxième lecture d'un même fichier est plus rapide que la première :
   le système d'exploitation la garde en mémoire. Tous les notebooks lisent
   donc le fichier dans le même ordre, et une lecture « à blanc » est faite
   avant la première mesure.

3. Nombre de cœurs
   Polars, DuckDB et Dask exploitent tous les cœurs ; pandas un seul. Sur une
   machine à un ou deux cœurs, l'avantage des premiers disparaît largement.
   Notez le nombre de cœurs de votre poste : il conditionne vos résultats.

4. Les échecs sont des mesures
   Sur le fichier complet, certaines opérations échoueront faute de mémoire.
   C'est un résultat, pas un incident : il est enregistré comme tel.
"""


def afficher_protocole() -> None:
    print(PROTOCOLE)
