# Module 04 — Docker : guide de travaux pratiques

Formation Big Data — ANSD / Data Innovation Lab

Ce module se fait **au terminal**, pas dans un notebook. Ouvrez un terminal et
placez-vous dans le dossier du module :

```bash
cd formation-bigdata/04-docker/1-Docker-init
```

Toutes les commandes commencent par `docker`. Si la commande n'est pas reconnue,
votre moteur de conteneurs n'est pas démarré : lancez Docker Desktop (ou Rancher
Desktop) et attendez que son icône passe au vert.

---

## Partie 1 — Créer et gérer à partir du terminal 

### 1.1 Un programme qui s'exécute et disparaît

```bash
docker run python:3.12-slim python -c "print('Bonjour depuis un conteneur')"
```

Il vient de se passer beaucoup de choses : Docker a cherché l'image
`python:3.12-slim`, l'a trouvée localement (ou téléchargée), a créé un
conteneur, y a exécuté Python, a affiché le résultat, puis a arrêté le
conteneur.

Relancez la même commande. Elle est instantanée : l'image était déjà là.

### 1.2 Où sont passés ces conteneurs ?

```bash
docker ps            # les conteneurs en cours d'exécution
docker ps -a         # tous les conteneurs, y compris les arrêtés
```

`docker ps` ne montre rien : le conteneur s'est arrêté dès la fin du programme.
`docker ps -a` les montre tous, avec le statut `Exited (0)` — code 0, tout s'est
bien passé.

**Retenez** : un conteneur qui a fini son travail s'arrête. Ce n'est pas une
panne.

### 1.3 Entrer dans un conteneur

```bash
docker run -it python:3.12-slim bash
```

`-i` garde l'entrée ouverte, `-t` alloue un terminal. Vous êtes maintenant
**dans** le conteneur. Explorez :

```bash
ls /
cat /etc/os-release
python --version
pip list
exit
```

Vous étiez dans un Debian minimal, avec Python et presque rien d'autre. Et vous
n'avez rien installé sur votre machine.

### 1.4 Faire le ménage

```bash
docker ps -a                    # regardez combien de conteneurs traînent
docker container prune          # supprime tous les conteneurs arrêtés
```

Les conteneurs arrêtés ne consomment pas de mémoire, mais ils occupent du
disque. Prenez l'habitude.

### 1.5 Les images présentes

```bash
docker images
```

Notez la taille de `python:3.12-slim` : de l'ordre de 130 Mo. Une image
complète avec l'écosystème scientifique dépasserait 4 Go — d'où le choix d'une
base légère.

---

## Partie 2 — Créer avec un fichier Dockerfile

Le fichier `Dockerfile` dans le répertoire contient plusieurs commandes permettant de créer une image Docker contenant une application Python et toutes les dépendances nécessaires à son exécution.

### 2.1 Description

#### Choix de l'image de base

```dockerfile
FROM python:3.9-slim
```

- Utilise l'image officielle **Python 3.9**.
- La version **slim** est allégée afin de réduire la taille de l'image.


#### Définition du répertoire de travail

```dockerfile
WORKDIR /app
```

- Définit `/app` comme répertoire de travail dans le conteneur.
- Toutes les commandes suivantes seront exécutées depuis ce dossier.


#### Copie du fichier des dépendances

```dockerfile
COPY requirements.txt requirements.txt
```

- Copie le fichier `requirements.txt` dans le conteneur.
- Ce fichier contient la liste des bibliothèques Python à installer.


#### Mise à jour de pip

```dockerfile
RUN pip install --upgrade pip
```

- Met à jour le gestionnaire de paquets Python (`pip`) vers sa dernière version.


#### Installation des dépendances

```dockerfile
RUN pip install -r requirements.txt
```

- Installe toutes les bibliothèques définies dans `requirements.txt`.


#### Copie du code source

```dockerfile
COPY app app
```

- Copie le dossier `app` contenant le code de l'application dans le conteneur.


#### Commande de démarrage

```dockerfile
CMD ["python", "app/main.py"]
```

- Définit la commande exécutée automatiquement au lancement du conteneur.
- Lance le programme principal de l'application.


### 2.2 Lancement

### Construire l'image Docker

Depuis le répertoire contenant le `Dockerfile` :

```bash
docker build -t mon-application .
```

- `-t mon-application` : attribue un nom à l'image.
- `.` : indique que le `Dockerfile` se trouve dans le répertoire courant.


### Vérifier que l'image a été créée

```bash
docker images
```


### Lancer un conteneur

```bash
docker run --name mon-conteneur mon-application
```

- `--name mon-conteneur` : donne un nom au conteneur.
- `mon-application` : nom de l'image à exécuter.


### Voir les conteneurs en cours d'exécution

```bash
docker ps
```

Pour afficher tous les conteneurs (y compris ceux arrêtés) :

```bash
docker ps -a
```


### Arrêter le conteneur

```bash
docker stop mon-conteneur
```


### Redémarrer le conteneur

```bash
docker start mon-conteneur
```

### Supprimer le conteneur

```bash
docker rm mon-conteneur
```


### Supprimer l'image

```bash
docker rmi mon-application
```

---

**NB1 :** si l'application expose un serveur web (Flask, FastAPI, Django, etc.), il faut publier le port avec l'option `-p`. Par exemple, pour exposer le port 5000 du conteneur sur le port 5000 de la machine hôte :

```bash
docker run -p 5000:5000 --name mon-conteneur mon-application
```

**NB2 :** Il est possible de voir les images/conteneurs directement sur Docker Desktop, ainsi que rentrer dans les conteneurs pour lancer des commandes.