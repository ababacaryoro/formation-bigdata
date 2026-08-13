# Module 09 — Visualisation avec Superset : guide de travaux pratiques

Formation Big Data · ANSD / Data Innovation Lab

Superset est un outil de visualisation qui s'exécute dans un navigateur. Il ne
copie pas les données : il **interroge la base** à chaque affichage.

Ce guide vous accompagne de la connexion au tableau de bord. Comptez trente
minutes.

Adresse : <http://localhost:8088> · identifiants dans votre fichier `.env`.

> Les libellés de l'interface varient légèrement d'une version à l'autre. Si un
> menu ne porte pas exactement le nom indiqué, cherchez son équivalent : la
> logique en trois niveaux — connexion, jeu de données, graphique — ne change
> pas.

---

## 0. Préparation

Suivre les étapes suivantes : 

- Se positionner dans le dossier de travail `09-visualisation` avec un terminal
- Copier le fichier .env.example du dossier de travail et le renommer à .env tout court
- Lancer la commande de `docker compose up -d`

## 1. Vérifier qu'il y a quelque chose à montrer

Avant d'ouvrir Superset sur l'adresse `http://localhost:8088`, assurez-vous que la table de restitution est remplie.

```bash
docker compose exec postgres psql -U user -d restitution -c \
  "SELECT COUNT(*) AS lignes, COUNT(DISTINCT jour) AS jours FROM agregats_actes;"
```

Si la table est vide ou n'existe pas, déclenchez d'abord le DAG
`02_agregats_quotidiens` dans Airflow, à partir du dossier de Airflow.

---

## 2. Déclarer la connexion à PostgreSQL

*Settings → Database Connections → + Database → PostgreSQL*

| Champ | Valeur |
|---|---|
| Host | `postgres` |
| Port | `5432` |
| Database name | `restitution` |
| Username | `user` |
| Password | celui de votre `.env` |
| Display name | `Restitution ANSD` |

> ⚠️ **L'hôte est `postgres`, pas `localhost`.** Superset s'exécute dans un
> conteneur : il joint la base par son **nom de service**, sur le réseau interne
> de Docker, et donc sur le port 5432 — celui de l'intérieur, pas celui publié
> côté machine.
>
> C'est la même logique que celle rencontrée avec Jupyter et MongoDB.

Cliquez sur **Test Connection** avant de valider. Si le test échoue :

- vérifiez le nom d'hôte (`postgres`) et le port (`5432`) ;
- vérifiez que le service tourne : `docker compose ps` ;
- vérifiez les identifiants : ils doivent correspondre à votre `.env`.

---

## 3. Déclarer le jeu de données

*Datasets → + Dataset*

| Champ | Valeur |
|---|---|
| Database | `Restitution ANSD` |
| Schema | `public` |
| Table | `agregats_actes` |

Superset lit la structure de la table et en déduit les types. Les colonnes
numériques deviendront des **mesures**, les autres des **dimensions**.

Ouvrez le jeu de données créé : vous voyez un tableau brut. C'est le point de
départ de tout graphique.

---

## 4. Premier graphique : effectifs par région

*Charts → + Chart* → jeu de données `agregats_actes` → type **Bar Chart**.

Dans le panneau de configuration :

| Réglage | Valeur |
|---|---|
| Metric | `COUNT(*)` |
| X-axis | `region` |
| Sort by | la métrique, décroissant |
| Row limit | 20 |

Cliquez sur **Create chart**. Vous devez voir un histogramme des effectifs par
région, Dakar en tête.

Enregistrez sous le nom `Actes par région`.

> Si le graphique reste vide, ouvrez **View query** dans le menu du graphique :
> Superset affiche le SQL qu'il a engendré. C'est le premier réflexe de
> diagnostic — souvent, un filtre de date exclut tout.

---

## 5. Deuxième graphique : la ventilation par type d'acte

Reprenez le même jeu de données, type **Bar Chart** également.

| Réglage | Valeur |
|---|---|
| Metric | `COUNT(*)` |
| Dimensions | `region` |
| X-axis | `type_acte` |

Vous obtenez des barres ventilées : pour chaque région, la répartition entre
naissances, mariages et décès.

Enregistrez sous `Répartition par type`.

---

## 6. Troisième graphique : un chiffre unique

Un tableau de bord a besoin de repères simples autant que de graphiques.

*+ Chart* → type **Big Number**.

| Réglage | Valeur |
|---|---|
| Metric | `COUNT(*)` |

Enregistrez sous `Total des actes`.

---

## 7. Assembler un tableau de bord

*Dashboards → + Dashboard*

Donnez-lui un titre — par exemple `Suivi de l'état civil` — puis faites glisser
vos trois graphiques depuis le panneau de droite. Disposez-les : le chiffre
unique en haut, les deux histogrammes en dessous.

**Enregistrez.**

### Ajouter un filtre

Dans le panneau de gauche du tableau de bord, ajoutez un filtre sur la colonne
`region`. Il s'appliquera à tous les graphiques à la fois.

C'est ce qui distingue un tableau de bord d'une collection d'images : les
éléments se répondent.

---

## 8. Voir la chaîne complète en action

C'est la partie la plus démonstrative.

1. Notez le total affiché par le graphique `Total des actes`
2. Faire les actions suivantes : 
  - taper la commande `docker compose down` pour désactiver les conteneurs du dossier
  - ouvrir un nouveau terminal, retourner au dossier **08-airflow** dans le terminal et faire un `docker compose up -d`
  - attendre le démarrage de l'application, se connecter et déclenchez à nouveau `02_agregats_quotidiens` pour générer de nouvelles données, en faisant en sorte qu'elle soient sur de nouvelles dates, de nouvelles clés.
3. Attendez la fin de l'exécution
4. Dans la page web de Superset, actualisez le tableau de bord

Le chiffre change. Un événement produit il y a quelques minutes vient de
traverser MongoDB, PostgreSQL, ... pour apparaître ici. On pourrait tout mettre dans le même docker compose pour que la chaine soit complète.

> C'est aussi le moment de mesurer l'intérêt de la colonne `calcule_le` : sans
> elle, personne ne saurait de quand datent les chiffres affichés.

---

## 9. Ce qui distingue un bon tableau de bord

- Il répond à **une question**, il n'expose pas tout ce qui est disponible
- Chaque chiffre porte un **repère** : évolution, cible, comparaison
- Il indique **quand** il a été calculé
- Il tient sur un écran, sans défilement

Reprenez votre tableau de bord et demandez-vous : à quelle question
répond-il ? Si vous ne savez pas répondre en une phrase, il y a trop de choses
dessus.

---

## 10. Pour aller plus loin (facultatif)

- Créez un jeu de données à partir d'une **requête SQL** plutôt que d'une table
  (*SQL Lab → Save as dataset*) : utile pour joindre deux tables ou calculer un
  ratio.
- Ajoutez un graphique d'évolution dans le temps, si vous avez plusieurs
  journées d'agrégats.
- Explorez **SQL Lab** : il permet d'interroger la base directement, sans passer
  par un graphique.

---

## Dépannage

**Le test de connexion échoue**
L'hôte doit être `postgres` et le port `5432` — ceux de l'intérieur du réseau
Docker. `localhost:5444` ne fonctionnera pas depuis le conteneur Superset.

**La table n'apparaît pas dans la liste**
Elle n'existe pas encore : déclenchez le DAG Airflow. Vérifiez aussi le schéma,
qui doit être `public`.

**Le graphique est vide**
Ouvrez *View query* pour voir le SQL engendré, puis exécutez-le dans SQL Lab.
Cause la plus fréquente : un filtre temporel par défaut qui exclut vos données.

**Superset ne démarre pas**

```bash
docker compose logs superset | tail -40
```

Le premier démarrage prend deux à trois minutes : Superset initialise sa base de
métadonnées.

**J'ai perdu mes graphiques après un redémarrage**
Ils sont enregistrés dans le volume de Superset. Un `docker compose down -v` les
efface — comme toute donnée d'un volume supprimé.

---

## À retenir

- Trois niveaux : une **connexion**, un **jeu de données**, des **graphiques**
  assemblés en tableau de bord.
- Superset **interroge la base** à chaque affichage : il ne copie rien. D'où
  l'importance d'une table de restitution légère et déjà agrégée.
- Entre conteneurs, on se joint par **nom de service** et port interne.
- *View query* montre le SQL engendré : c'est l'outil de diagnostic à connaître.
- Un tableau de bord répond à une question ; il n'expose pas tout ce qu'on a.
