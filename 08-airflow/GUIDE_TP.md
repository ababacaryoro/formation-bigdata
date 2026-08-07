# Module 08 — Airflow : guide de travaux pratiques

Formation Big Data — ANSD / Data Innovation Lab

Airflow ne se manipule pas depuis un notebook : c'est une **interface web** et
des **fichiers Python** déposés dans un dossier. Ce guide vous accompagne.

Interface : <http://localhost:8080> · identifiants dans votre fichier `.env`.

---

## 0. Avant de commencer — Démarrage des services

Liser le fichier `docker-compose.yml`du répertoire `08-aiflow` et mettez en place votre fichier `.env` avec les 
informations nécessaires, inscrites dans le docker-compose (__POSTGRES_USER, MONGO_USER, AIRFLOW_USER__, ...).


Si vous avez déjà démarré cette pile, **repartez d'un état propre**. L'image
PostgreSQL n'exécute son initialisation que sur un répertoire de données vide :
si le volume existe déjà, les identifiants du fichier `.env` sont ignorés, et
vous obtiendrez l'erreur `role "ansd" does not exist`.

```bash
cp .env.exemple .env          # indispensable AVANT le premier démarrage. Mettre a jour les informations si nécessaire
docker compose down -v        # le -v efface les volumes
docker compose build          # construit l'image Airflow
docker compose up -d
```

Vérifiez ensuite que l'utilisateur existe bien (en remplaçant `user` par votre valeur de `POSTGRES_USER` dans le fichier `.env`):

```bash
docker compose exec postgres psql -U user -d restitution -c "\du"
```

Si cette commande répond, tout est en ordre. Sinon, c'est que le `.env` était
absent au moment du démarrage : reprenez au `down -v`.

Lorsque le service est en place, aller dans l'interface Airflow via l'url <http://localhost:8080>. 
Il est parfois nécessaire d'attendre quelques minutes pour que l'interface soit accessible (erreur `Ce site est inaccessible`) car le premier démarrage prend 4 à 5 minutes : Airflow initialise sa base. En attendant, vous pouvez vérifier les logs du conteneur Airflow
avec la commande `docker compose logs -f airflow` ou regarder directement sur Docker Desktop (cliquer sur le conteneur et aller dans `logs`).


---

## 1. Découvrir l'interface

Connectez-vous. La page d'accueil liste les DAG détectés. Vous devez voir :

- `01_premier_dag` — un DAG de découverte, qui ne fait rien d'utile
- `02_agregats_quotidiens` — la chaîne batch de l'architecture des projets

Chaque ligne indique le nom, l'état des dernières exécutions, la planification,
et un interrupteur pour activer ou suspendre le DAG.

> Un DAG déposé dans le dossier `dags/` est détecté en une minute environ. Si
> le vôtre n'apparaît pas, voyez la section Dépannage.

---

## 2. Lire un DAG avant de le lancer

Ouvrez `dags/01_premier_dag.py` dans VS Code. Trois choses à repérer :

**Le décorateur `@dag`** définit le graphe : son identifiant, sa planification,
sa date de début, ses tentatives en cas d'échec.

**Le décorateur `@task`** définit chaque étape. Une tâche est une fonction
Python ordinaire.

**L'enchaînement**, en une seule ligne :

```python
charger(transformer(extraire()))
```

Les dépendances se déduisent du passage des valeurs — inutile de les déclarer.
`transformer` recevra ce que `extraire` a retourné, et ne démarrera qu'après.

Dans l'interface, ouvrez le DAG puis l'onglet **Graph** ou cliquez sur "Afficher le graphe" (en haut, à gauche) : vous retrouvez ces
trois tâches et leurs flèches.

---

## 3. Déclencher une exécution

`01_premier_dag` est planifié sur `schedule=None` : il ne se déclenche que
manuellement.

1. Activez le DAG avec l'interrupteur, s'il est suspendu
2. Cliquez sur le bouton de déclenchement (**Trigger** ou **Déclencher**)
3. Observez l'exécution progresser dans l'onglet **Graph**

Les couleurs indiquent l'état : en cours, réussi, en échec, en attente de
nouvelle tentative.

---

## 4. Observer une reprise

La tâche `charger` échoue **volontairement une fois sur deux** en moyenne. Relancez le DAG
jusqu'à obtenir un échec — cela ne prend généralement pas longtemps.

Vous verrez alors :

- la tâche passe en échec ;
- Airflow attend vingt secondes ;
- il la relance automatiquement — deux tentatives sont prévues ;
- si elle finit par réussir, le DAG est réussi.

C'est toute la valeur de l'orchestration : un incident passager ne fait pas
tomber la chaîne, et personne n'a eu à intervenir.

---

## 5. Lire les journaux

Cliquez sur une tâche, puis sur l'onglet **Logs** ou **Journaux**. Vous y voyez tout ce que la
tâche a écrit, y compris la trace de l'erreur en cas d'échec.

C'est le premier réflexe de diagnostic — l'équivalent du
`docker compose logs` que vous employez depuis mardi.

Repérez dans les journaux les lignes que le code affiche avec `print` : elles
s'y retrouvent telles quelles.

---

## 6. Relancer une seule tâche

Sélectionnez une tâche réussie, puis **Clear** (effacer son état). Airflow la
relance, ainsi que tout ce qui en dépend.

C'est ce qui permet de corriger une étape sans refaire l'ensemble de la chaîne —
impossible avec un simple `cron`.

---

## 7. La chaîne batch réelle

Ouvrez `dags/02_agregats_quotidiens.py`. Ce DAG met en œuvre le second chemin de
l'architecture :

| Tâche | Rôle |
|---|---|
| `delimiter_periode` | Détermine la période à traiter, d'après le contexte fourni par Airflow |
| `preparer_donnees` | Crée un jeu d'actes de démonstration dans MongoDB |
| `compter_documents` | Vérifie qu'il y a quelque chose à traiter sur la période |
| `calculer_agregats` | Agrège et écrit dans PostgreSQL |
| `controler` | Vérifie la cohérence de la table de restitution |

Ce DAG est **autoporteur** : la tâche `preparer_donnees` crée elle-même les
données. Vous pouvez le déclencher sans avoir exécuté quoi que ce soit
auparavant.

Deux points méritent votre attention.

**Le paramétrage par la période.** La tâche ne traite pas « aujourd'hui » mais
un **intervalle** que lui fournit Airflow — par exemple, l'exécution de 2 h du
matin traite les vingt-quatre heures précédentes. Le traitement filtre les
documents sur cet intervalle.

Pourquoi ne pas simplement traiter « depuis hier » ? Parce qu'un traitement
paramétré par une période est **rejouable à l'identique** : relancer l'exécution
du 3 août recalcule exactement la journée du 3 août, même si on la relance en
décembre. C'est ce qui permet de corriger un bogue et de recalculer le passé.

> ⚠️ **Depuis Airflow 3**, écrire `schedule="0 2 * * *"` produit un intervalle
> de **durée nulle** : les deux bornes sont égales, et un filtre sur cet
> intervalle ne retourne jamais rien. Pour retrouver la sémantique classique, il
> faut la demander explicitement — c'est ce que fait ce DAG avec
> `CronDataIntervalTimetable`. C'est un changement que la plupart des exemples
> en ligne ignorent encore.

**L'idempotence.** Avant d'insérer, la tâche **supprime** les lignes de la
journée concernée. Rejouer la tâche remplace donc les données au lieu de les
dupliquer. Sans cette précaution, chaque nouvelle tentative doublerait les
effectifs publiés.

Déclenchez-le manuellement et suivez son exécution. S'il n'y a aucun document
sur la période, les tâches s'exécutent quand même et signalent qu'il n'y a rien
à faire — c'est voulu.

---

## 8. Vérifier le résultat dans PostgreSQL

```bash
docker compose exec postgres psql -U user -d restitution -c \
  "SELECT jour, region, type_acte, effectif FROM agregats_actes ORDER BY effectif DESC LIMIT 10;"
```

Si la commande répond `role "user" does not exist`, reprenez la section 0 :
le volume PostgreSQL a été créé avant que le fichier `.env` n'existe.

Cette table est celle que le tableau de bord viendra lire.

---

## 9. Pour aller plus loin (facultatif)

- Modifiez la planification de `02_agregats_quotidiens` pour qu'il tourne toutes
  les heures, et observez la différence.
- Ajoutez une tâche qui écrit un fichier de compte rendu après `controler`.
- Provoquez un échec dans `calculer_agregats` (par exemple en changeant le mot
  de passe PostgreSQL) et observez ce que disent les journaux.

---

## Dépannage

**Mon DAG n'apparaît pas dans l'interface**
Comptez une minute. Puis vérifiez qu'il n'y a pas d'erreur de syntaxe :

```bash
docker compose exec airflow python /opt/airflow/dags/MON_DAG.py
```

Si la commande ne dit rien, le fichier est correct. Une erreur d'import
s'affiche aussi en haut de la page d'accueil d'Airflow.

**Le DAG apparaît mais ne se déclenche pas**
Il est probablement suspendu : vérifiez l'interrupteur. Vérifiez aussi que sa
`start_date` est dans le passé.

**Une tâche reste en attente indéfiniment**
Elle attend une ressource. Regardez l'onglet des tâches en cours, et les
journaux de l'ordonnanceur :

```bash
docker compose logs airflow | tail -50
```

**`ModuleNotFoundError` dans une tâche**
La bibliothèque manque **dans le conteneur Airflow**, qui est distinct de celui
de Spark. Ajoutez-la au `Dockerfile.airflow`, puis :

```bash
docker compose build airflow && docker compose up -d
```

C'est notamment le cas de PySpark : il n'est **pas** dans le conteneur Airflow,
et n'a pas à y être. Airflow orchestre, il ne calcule pas — une tâche qui a
besoin de Spark déclenche un traitement dans le conteneur Spark plutôt que de
l'exécuter elle-même.

**Le DAG s'exécute mais ne traite aucun document**
Regardez les journaux de `delimiter_periode` : si les deux bornes de la période
sont identiques, l'intervalle est de durée nulle. Voir l'avertissement de la
section 7.

**Je veux repartir de zéro**

```bash
docker compose down -v && docker compose up -d
```

---

## À retenir

- Un DAG est du **code Python** : versionnable, testable, relisible.
- Les dépendances se déduisent du passage des valeurs entre tâches.
- Une tâche en échec est **relancée automatiquement** : elle doit donc être
  **idempotente**, c'est-à-dire produire le même résultat si on la rejoue.
- Paramétrer un traitement par une **période** plutôt que par « maintenant » le
  rend rejouable sur le passé.
- Airflow **déclenche** ; il ne calcule pas. Le calcul revient à Spark, le
  stockage aux bases.
