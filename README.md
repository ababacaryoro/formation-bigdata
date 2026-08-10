# Formation Big Data 

Support de la formation « Big Data, Outils et Méthodes ».

Ce dépôt contient l'ensemble du matériel : supports, notebooks, jeux de données,
environnements techniques et consignes de projet.

---

## Démarrer

### 1. Installer les outils

Suivez **[INSTALLATION.md](INSTALLATION.md)** : Visual Studio Code, ses
extensions, et `uv` pour la gestion de Python. Comptez vingt à trente minutes.

### 2. Récupérer le dépôt

```bash
git clone <adresse-du-depot> formation-bigdata
cd formation-bigdata
uv sync
```

`uv sync` installe la version de Python attendue et toutes les bibliothèques,
aux versions exactes. Tout le monde obtient ainsi le même environnement.

### 3. Engendrer les jeux de données

```bash
cd 00-data
python generate_data.py --auto
```

L'option `--auto` dimensionne le fichier selon la mémoire de votre poste.

> ⚠️ Utilisez toujours `--jeu tous` si vous régénérez : produire `individus`
> seul rendrait caduque la vérité terrain de l'appariement.

### 4. Chaque matin
Faire si besoin :
```bash
git pull
```
Gérer les conflits si besoin sur git. 

---

## Organisation du dépôt

Les modules sont numérotés dans l'ordre où ils sont abordés, mais nommés par
**thème**.

| Module | Contenu |
|---|---|
| `00-data/` | Générateurs des jeux de données |
| `01-limites-du-poste/` | Où s'arrête un poste de travail |
| `02-franchir-le-mur/` | Polars, DuckDB, Dask |
| `03-formats-parquet/` | Formats de données, Parquet, partitionnement |
| `04-docker/` | Conteneurs, `compose`, pile Jupyter + PostgreSQL |
| `05-mongodb/` | Modèle document, agrégations, index, réplication |
| `06-spark/` | Traitement distribué, transformations, fenêtrage |
| `07-kafka/` | Flux d'événements, ingestion continue |
| `08-airflow/` | Orchestration, DAG, idempotence |
| `09-visualisation/` | Restitution et tableaux de bord |
| `10-integration/` | La chaîne complète, de bout en bout |
| `projet-final/` | Consignes, grille d'évaluation, socle technique |
| `slides/` | Supports projetés, publiés au fil de l'eau |

### Correspondance avec les journées

| Jour | Modules |
|---|---|
| **J1** — Fondamentaux et calcul parallèle | `01`, `02`, `03` |
| **J2** — Architectures, conteneurs, NoSQL | `04`, `05` |
| **J3** — Traitement distribué avec Spark | `06`, `07` |
| **J4** — Flux et orchestration | `08`, `09` |
| **J5** — Restitution et projets | `10`, `projet-final` |

Chaque module contient un `README.md` ou un `GUIDE_TP.md` ou une documentation ainsi que le
`docker-compose.yml` des services dont il a besoin.

---

## Les jeux de données

Tous sont **engendrés localement** : aucun téléchargement, aucune dépendance
extérieure. Ils reproduisent des données de la statistique publique sénégalaise
— régions, départements, noms, structures démographiques réalistes — avec les
imperfections des fichiers administratifs : libellés incohérents, valeurs
aberrantes, formats de date multiples, doublons.

| Générateur | Produit |
|---|---|
| `generate_data.py` | Recensement, régions, état civil, entreprises |
| `generate_etat_civil_json.py` | Actes en JSON imbriqué, avec mentions marginales |
| `generate_projets.py` | Collecte terrain, prix de caisse, téléphonie |

```bash
python generate_data.py --auto                    # dimensionné selon la RAM
python generate_etat_civil_json.py --actes 50000  # pour MongoDB
python generate_projets.py --sujet cdr --lignes 2000000
python generate_projets.py --sujet prix --flux --debit 50   # en continu
```

Les fichiers produits ne sont **jamais** versionnés : ils se régénèrent en
quelques minutes.

---

## Environnements Docker

À partir du module `04`, les services tournent dans des conteneurs — rien n'est
installé sur votre poste.

```bash
cd 04-docker
cp .env.exemple .env      # AVANT le premier démarrage
docker compose up -d
docker compose ps
```

Le fichier `.env` doit exister **avant** le premier `up` : PostgreSQL et MongoDB
n'exécutent leur initialisation que sur un volume vide, et les identifiants ne
seraient jamais créés.

Pour repartir d'un état propre :

```bash
docker compose down -v    # le -v efface les volumes, donc les données
docker compose up -d
```

Les commandes utiles et les incidents fréquents sont recensés dans
**[04-docker/DEPANNAGE.md](04-docker/DEPANNAGE.md)**.

---

## Le projet

Chaque groupe construit une chaîne de données complète sur un
sujet tiré au sort.

```
   générateur ──► Kafka ──► Spark ──► MongoDB           (temps réel)

   MongoDB ──► Airflow ──► Spark ──► PostgreSQL ──► tableau de bord   (batch)
```

Tout est décrit dans **[projet-final/consignes.md](projet-final/consignes.md)** :
les cinq sujets, les jalons, le socle attendu, la grille d'évaluation.

Le squelette technique est fourni dans `projet-final/socle/` — vous n'écrivez
que ce qui relève de votre sujet, aux endroits marqués « À VOUS DE JOUER ».

---

## Environnement technique

| Composant | Version |
|---|---|
| Python | 3.12 |
| Spark / PySpark | 4.1.2 (Scala 2.13, Java 17) |
| MongoDB | 7 |
| PostgreSQL | 16 |
| Kafka | 4.0 (image officielle Apache) |
| Airflow | 3.3 |
| Superset | 4.1 |

Deux images sont construites pour la formation : `formation-spark` (Spark,
JupyterLab et les connecteurs Kafka, MongoDB, PostgreSQL déjà intégrés) et
`formation-jupyter` (environnement léger pour les premiers modules).

---

## Quelques pièges de version

Ces points ont été vérifiés par l'exécution du code, et diffèrent souvent de ce
qu'indiquent les documentations et aide-mémoire en ligne.

**Spark 4** active le mode strict (ANSI) par défaut : une conversion qui échoue
**lève une erreur** au lieu de produire une valeur manquante. Employez
`try_to_date`, `try_to_timestamp`, `try_cast`.

**Airflow 3** importe depuis `airflow.sdk`, et une planification écrite comme
une simple chaîne `cron` produit un intervalle de données de **durée nulle** —
un traitement filtrant sur cet intervalle ne trouverait jamais rien. Utilisez
`CronDataIntervalTimetable` pour retrouver la sémantique classique.

**Polars** emploie `collect(engine="streaming")`, et non l'ancien
`streaming=True`.

**DuckDB** n'a pas de fonction `initcap` : normalisez en clé
(`upper(trim(...))`), puis joignez une table de référence.

**pandas 3** stocke les chaînes dans un format compact adossé à Arrow : le
rapport entre taille sur disque et taille en mémoire n'est plus celui qu'on lit
souvent.

---

## Conventions

Les scripts `.sh` s'exécutent depuis **Git Bash** sous Windows, jamais depuis
PowerShell. Le fichier `.gitattributes` force les fins de ligne LF sur les
scripts, les fichiers YAML et les `Dockerfile` — sans quoi Bash échoue avec un
message obscur.

Ne versionnez jamais un fichier `.env`, ni les jeux de données engendrés.

Les notebooks sont conçus pour être exécutés cellule par cellule, dans l'ordre.
Ceux des premiers modules comportent des passages à compléter, marqués
`À COMPLÉTER` ; les suivants sont entièrement fournis.


--- 

## Fichiers partagés 

- Pour échanger en live, un document word est accessible via [ce lien](https://1drv.ms/w/c/ab584826bfa6bf60/IQBOcU0ZUqsPRLMcey5akGQDAWrdEYzUNFqNViYasLywwT8?e=vJRQbA). 

- Certains éléments utiles pour le cours (slides, images docker, ...) sont partagés dans l'[espace drive](https://drive.google.com/drive/folders/1bOeOwH7gqH6uQuXeYZSuNeklg5X0uiyc?usp=drive_link). 


---

*Formation dispensée par Ababacar Yoro BA, consultant indépendant.*
