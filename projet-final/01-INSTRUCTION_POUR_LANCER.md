# Projet final — comment lancer votre chaîne

Formation Big Data · ANSD / Data Innovation Lab

Vous allez lancer une chaîne de données complète, puis construire le tableau de
bord qui la restitue.

> **Il n'y a aucun code à écrire.** Tout est déjà en place : vous choisissez
> votre sujet, vous lancez trois commandes, et vous consacrez votre temps au
> tableau de bord — qui est votre livrable, avec un court rapport.

---

## L'architecture

```
  ┌─────────────┐   ┌───────┐   ┌───────────┐   ┌──────────┐
  │ producteur  │──►│ Kafka │──►│   Spark   │──►│ MongoDB  │
  │ (événements)│   │ (file)│   │(streaming)│   │ (données │
  └─────────────┘   └───────┘   └───────────┘   │  brutes) │
                                                └────┬─────┘
                                                     │
                          ┌──────────────────────────┘
                          ▼
                    ┌──────────┐   ┌────────────┐   ┌──────────┐
                    │ Airflow  │──►│ PostgreSQL │──►│ Superset │
                    │(toutes   │   │ (agrégats  │   │ (tableau │
                    │ les 2 mn)│   │  publiés)  │   │ de bord) │
                    └──────────┘   └────────────┘   └──────────┘
```

**Le rôle de chaque brique** — vous devrez pouvoir l'expliquer :

| Brique | À quoi elle sert |
|---|---|
| **Producteur** | Simule la source : il émet des événements en continu |
| **Kafka** | Reçoit les événements et les conserve, le temps qu'on les traite |
| **Spark** | Lit le flux, met les événements en forme, les range dans MongoDB |
| **MongoDB** | Conserve les données brutes, telles qu'elles sont arrivées |
| **Airflow** | Déclenche le calcul des indicateurs, toutes les deux minutes |
| **PostgreSQL** | Porte les indicateurs publiés, prêts à être affichés |
| **Superset** | Affiche le tableau de bord |

En une phrase : **MongoDB conserve ce qui est arrivé, PostgreSQL publie ce
qu'on en a tiré.**

---

## Votre sujet

Un sujet vous a été attribué :

| Sujet | Nom à utiliser |
|---|---|
| Relevés de prix de caisse | `prix` |
| Collecte de recensement | `collecte` |
| Déclarations d'état civil | `etat_civil` |
| Répertoire des entreprises | `ninea` |
| Données de téléphonie | `telephonie` |

Dans la suite, remplacez `VOTRE_SUJET` par ce nom.

Un seul fichier vous concerne :

- `sujets/VOTRE_SUJET/TABLEAU_DE_BORD.md` — les graphiques attendus

Le fichier `sujets/VOTRE_SUJET/config.py` décrit ce que produit votre chaîne :
consultez-le si vous êtes curieux, mais **vous n'avez rien à y modifier**.

---

## Étape 1 — Démarrer les services

```bash
cp .env.exemple .env          # AVANT tout démarrage
docker compose build
docker compose up -d
docker compose ps
```

Comptez trois à quatre minutes. Tous les services doivent afficher `running`,
et PostgreSQL, Kafka et MongoDB doivent être `healthy`.

---

## Étape 2 — Lancer le producteur

Ouvrez un terminal et **laissez-le tourner** :

```bash
docker compose exec spark python3 commun/producteur.py --sujet VOTRE_SUJET --debit 20
```

Vous devez voir le compteur d'événements augmenter.

👉 Ouvrez <http://localhost:8085> (Kafka UI), onglet *Topics* : votre file se
remplit.

---

## Étape 3 — Lancer l'ingestion

Ouvrez un **second terminal**, et laissez-le tourner aussi :

```bash
docker compose exec spark spark-submit commun/streaming.py --sujet VOTRE_SUJET
```

Toutes les dix secondes, une ligne s'affiche : `lot N : XXX événements écrits`.

👉 Ouvrez <http://localhost:8081> (Mongo Express) : votre base se remplit.

> Le premier lot met une trentaine de secondes à venir : Spark démarre sa
> machine virtuelle Java. C'est normal.

---

## Étape 4 — Activer l'agrégation

Une seule ligne à adapter — c'est la seule modification de tout le projet.
Ouvrez `airflow/dags/agregation.py` et remplacez le nom du sujet :

```python
SUJET = "VOTRE_SUJET"
```

Enregistrez. Puis, dans Airflow (<http://localhost:8080>) : attendez une minute que le DAG
apparaisse, activez-le avec l'interrupteur, et déclenchez-le une première fois
à la main.

Il se relancera ensuite tout seul, toutes les deux minutes.

**Vérifiez que les données arrivent :**

Sur le premier terminal et dans le dossier de travail : 
```bash
docker compose exec postgres psql -U user -d restitution -c \
  "SELECT indicateur, COUNT(*) FROM agregats GROUP BY indicateur;"
```
(si besoin, modifer dans la commande user par le nom de votre user dans le .env pour postgresql)

---

## Étape 5 — Construire le tableau de bord

C'est votre livrable. Tout est décrit dans
`sujets/VOTRE_SUJET/TABLEAU_DE_BORD.md`.

Superset : <http://localhost:8088>

**Connexion à la base** — *Settings → Database Connections → + Database →
PostgreSQL* :

| Champ | Valeur |
|---|---|
| Host | `postgres` |
| Port | `5432` |
| Database | `restitution` |
| Username / Password | ceux de votre `.env` |


> L'hôte est `postgres` et le port `5432` : ce sont ceux de l'intérieur du
> réseau Docker. `localhost:5444` ne fonctionnerait pas depuis Superset.

**Jeu de données** — *Datasets → + Dataset* → schéma `public`, table
`agregats`.

---

## La table `agregats`

Une seule table, avec toujours les mêmes colonnes :

| Colonne | Contenu |
|---|---|
| `indicateur` | Le nom de l'indicateur — c'est sur lui que vous filtrerez |
| `minute` | La minute concernée, au format `2026-08-14 10:23` |
| `dimension` | Région, produit, enquêteur… selon l'indicateur |
| `effectif` | Nombre d'événements |
| `valeur` | La valeur calculée (moyenne, taux, indice…) |
| `calcule_le` | Quand ce chiffre a été produit |

**Chaque graphique porte sur un seul indicateur** : mettez donc toujours un
filtre `indicateur = '...'` dans vos graphiques.

---

## Dépannage

**Le DAG n'apparaît pas dans Airflow**
Attendez une minute. Puis vérifiez la syntaxe :
`docker compose exec airflow python /opt/airflow/dags/agregation.py`

**La table `agregats` est vide**
Vérifiez dans l'ordre : le producteur tourne-t-il ? Mongo Express montre-t-il
des documents ? Le DAG s'est-il exécuté sans erreur ? Regardez les journaux de
la tâche dans Airflow.

**Superset ne voit pas la table**
Le DAG doit s'être exécuté au moins une fois : c'est lui qui crée la table.

**Un graphique reste vide**
Ouvrez *View query* : Superset montre le SQL engendré. Vérifiez le filtre sur
`indicateur`, et le filtre temporel — souvent réglé par défaut sur une période
qui exclut vos données.

**Tout redémarrer proprement**
```bash
docker compose down -v && docker compose up -d
```

---

## Votre livrable

**Un rapport, au format PDF, de trois à cinq pages.** Il contient :

1. **Votre sujet**, en quelques lignes : quelles données, à quoi elles servent
2. **L'architecture** : le schéma de la chaîne, et le rôle de chaque brique
   en une phrase — Kafka, Spark, MongoDB, Airflow, PostgreSQL, Superset
3. **Votre tableau de bord** : une capture d'écran d'ensemble, puis une capture
   par graphique, avec pour chacune ce qu'elle montre
4. **Le graphique que vous avez choisi** librement, et pourquoi
5. **Une difficulté** rencontrée, et comment vous l'avez traitée

Nommez le fichier `rapport_<sujet>_<vos noms>.pdf`.

> Un traitement de texte suffit — inutile de chercher mieux. Pour les captures :
> `Impr. écran` sous Windows, `Cmd + Maj + 4` sous macOS.

**Vous enverrez ce rapport par email à yoroba93@gmail.com au plus tard dimanche 23h59**. Si vous terminez votre tableau de bord, vous 
pourrez le présenter à l'écrant en séance.
