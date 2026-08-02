# Module 04 — Docker : guide de travaux pratiques

Formation Big Data — ANSD / Data Innovation Lab



```bash
cd formation-bigdata/04-docker/2-Multi-container
```

Toutes les commandes commencent par `docker`. Si la commande n'est pas reconnue,
votre moteur de conteneurs n'est pas démarré : lancez Docker Desktop (ou Rancher
Desktop) et attendez que son icône passe au vert.

---

## Partie 1 — Une pile à deux services

Objectif : un JupyterLab et une base PostgreSQL, dans deux conteneurs qui se
parlent. Vous ne taperez plus de longues commandes : tout est décrit dans un
fichier.

### 2.1 Les identifiants

Le fichier `docker-compose.yml` fait appel à des variables. On les définit dans
un fichier `.env`, qui n'est **jamais** versionné sur git.

```bash
cp .env.exemple .env
```

Ouvrez `.env` dans VS Code et changez le mot de passe.

### 2.2 Vérifier le fichier `compose`

Ouvrez `docker-compose.yml` dans VS Code. **Cinq passages importants à vérifier**,
repérés par `À VÉRIFIER`. Ils portent sur :

1. la variable de mot de passe de PostgreSQL ;
2. la publication du port de la base ;
3. le volume de données de la base ;
4. le montage du dossier `notebooks` ;
5. la déclaration du volume nommé.

Prenez le temps de lire les commentaires : ils contiennent les formats attendus.

> **Attention à l'indentation.** Le YAML n'accepte que des espaces, jamais de
> tabulation, et les niveaux doivent être alignés. Si Docker se plaint d'un
> `yaml: line N`, c'est presque toujours cela.

### 2.3 Construire l'image Jupyter

Le service `jupyter` n'utilise pas une image toute faite : il en construit une à
partir du `Dockerfile` du dossier. Ouvrez ce fichier, il ne fait que quatre
instructions — vous en écrirez un semblable.

```bash
docker compose build
```

Si l'image a été préparée à l'avance et chargée sur votre poste, cette étape
est immédiate.

### 2.4 Démarrer la pile

```bash
docker compose up -d
```

`-d` signifie *detached* : les services tournent en arrière-plan et vous
récupérez la main.

```bash
docker compose ps
```

Vous devez voir deux services, en statut `running`. Celui de PostgreSQL doit
afficher `healthy` — c'est le `healthcheck` du fichier `compose` qui a vérifié
que la base répond.

### 2.5 Lire les journaux

C'est **le** réflexe de dépannage. Quand un service ne fonctionne pas, la
réponse est presque toujours dans ses journaux.

```bash
docker compose logs postgres      # les journaux de la base
docker compose logs jupyter       # ceux de Jupyter
docker compose logs -f jupyter    # en continu ; Ctrl+C pour sortir
```

Dans les journaux de Jupyter, repérez la ligne indiquant que le serveur est
lancé sur le port 8888.

### 2.6 Ouvrir JupyterLab

Dans votre navigateur : <http://localhost:8888>

Le mot de passe (jeton) est `formation`, tel que défini dans le `Dockerfile`.

Ouvrez `notebooks/jupyter_postgres.ipynb` et suivez-le. Rendez-vous ici après
la section 7 du notebook.

---


## Partie 2 — La persistance

Suivez la section 7 du notebook. En résumé :

```bash
docker compose down          # arrête et supprime les conteneurs
docker compose up -d         # relance
```

→ Les données sont toujours là.

```bash
docker compose down -v       # supprime AUSSI les volumes
docker compose up -d
```

→ La base `school` a disparu.

**C'est la leçon la plus importante du bloc.** Un conteneur est jetable ; un
volume persiste. Et l'option `-v` détruit des données sans confirmation.

---

## Les huit commandes à retenir

| Commande | Effet |
|---|---|
| `docker compose up -d` | Démarre la pile en arrière-plan |
| `docker compose ps` | État des services |
| `docker compose logs -f <service>` | Journaux en continu — le réflexe de dépannage |
| `docker compose exec <service> bash` | Entrer dans un conteneur en marche |
| `docker compose restart <service>` | Redémarrer un service |
| `docker compose down` | Arrêter et supprimer les conteneurs |
| `docker compose down -v` | … et supprimer les volumes (destructif) |
| `docker ps -a` / `docker images` | Que tourne-t-il, qu'ai-je téléchargé |

---
