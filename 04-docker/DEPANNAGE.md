# Docker — fiche de dépannage

Formation Big Data — ANSD / Data Innovation Lab

**Le réflexe, avant tout autre chose :**

```bash
docker compose ps          # qu'est-ce qui tourne, dans quel état ?
docker compose logs <service>   # pourquoi cela ne tourne pas
```

Neuf incidents sur dix se résolvent avec ces deux commandes.

---

## 1. « Cannot connect to the Docker daemon »

Le moteur de conteneurs n'est pas démarré.

**Windows / macOS** : lancez Docker Desktop (ou Rancher Desktop) et attendez que
l'icône passe au vert. Le démarrage prend parfois une minute.

**Linux** : `sudo systemctl start docker`

---

## 2. « port is already allocated » / « bind: address already in use »

Un autre programme occupe déjà le port demandé sur votre machine. Le plus
souvent : une installation de PostgreSQL déjà présente (port 5432), ou un
Jupyter lancé hier (port 8888).

**Solution — changer le port côté machine**, dans `docker-compose.yml` :

```yaml
ports:
  - "5433:5432"      # 5433 sur ma machine → 5432 dans le conteneur
```

Puis `docker compose up -d`. Pensez à utiliser 5433 pour vous connecter depuis
l'extérieur — mais **rien ne change pour Jupyter**, qui joint la base par le
réseau interne, sur le port 5432.

Pour identifier le coupable :

```bash
# Windows (PowerShell)
netstat -ano | findstr :5432
# macOS / Linux
lsof -i :5432
```

---

## 3. « yaml: line 23: did not find expected key »

Erreur d'indentation dans `docker-compose.yml`.

- Uniquement des **espaces**, jamais de tabulation
- Les éléments d'une même liste alignés sur la même colonne
- Un tiret et un espace devant chaque élément de liste

VS Code signale ces erreurs si le fichier est bien reconnu comme YAML (mention
en bas à droite de la fenêtre).

Pour vérifier sans démarrer :

```bash
docker compose config
```

Cette commande affiche le fichier tel que Docker le comprend, variables
remplacées. Très utile.

---

## 4. « variable is not set » / le mot de passe est vide

Le fichier `.env` est absent, mal nommé, ou dans le mauvais dossier.

- Il doit s'appeler exactement `.env`, avec le point, **sans extension**
  (attention à Windows, qui peut créer un `.env.txt` invisible)
- Il doit se trouver dans le **même dossier** que `docker-compose.yml`
- Pas d'espace autour du signe égal : `POSTGRES_USER=ensae`, pas
  `POSTGRES_USER = ensae`
- Pas de guillemets autour des valeurs

Vérification : `docker compose config` doit afficher les valeurs remplacées.

---

## 5. Le conteneur redémarre en boucle

`docker compose ps` affiche `restarting`. Le service plante au démarrage et
`restart: unless-stopped` le relance sans fin.

```bash
docker compose logs --tail 50 <service>
```

Causes fréquentes : mot de passe manquant, volume de données créé par une
version antérieure de PostgreSQL, disque plein.

Si le volume est en cause et que les données ne comptent pas :

```bash
docker compose down -v && docker compose up -d
```

---

## 6. « no space left on device »

Le disque est plein — souvent à cause d'images et de conteneurs accumulés.

```bash
docker system df           # ce que Docker occupe
docker system prune        # supprime conteneurs arrêtés, réseaux, cache
docker system prune -a     # supprime AUSSI les images non utilisées
```

`prune -a` obligera à retélécharger les images : à éviter si la connexion est
mauvaise.

---

## 7. Le téléchargement d'image échoue ou n'avance pas

Pare-feu ou proxy de l'institution. **Ne restez pas bloqué** : les images de la
formation ont été préparées à l'avance.

```bash
docker load -i images_formation.tar
docker images                        # vérifiez qu'elles sont présentes
```

---

## 8. JupyterLab ne s'ouvre pas dans le navigateur

- Vérifiez que le service tourne : `docker compose ps`
- Vérifiez l'adresse : <http://localhost:8888> (pas `https`)
- Le jeton demandé est `formation`
- Regardez les journaux : `docker compose logs jupyter`
- Si un pare-feu local bloque, essayez <http://127.0.0.1:8888>

---

## 9. Mon notebook a disparu

Il était enregistré **dans** le conteneur et non dans le volume monté.

Les fichiers créés en dehors du dossier `notebooks` disparaissent avec le
conteneur. Travaillez toujours dans `notebooks`, qui correspond à un vrai
dossier de votre disque.

---

## 10. Windows : « WSL 2 installation is incomplete » ou la virtualisation

Docker Desktop sous Windows s'appuie sur WSL 2, qui exige que la virtualisation
soit activée dans le BIOS.

- Vérifiez dans le Gestionnaire des tâches, onglet Performance : la mention
  « Virtualisation : activée » doit apparaître
- Sinon, l'activation se fait au démarrage de la machine, dans le BIOS — et
  requiert souvent des droits d'administration

**Si cela reste bloqué, signalez-le immédiatement** : une solution de repli est
prévue, avec les services hébergés sur une machine unique accessible par le
réseau. Ne perdez pas la matinée à essayer.

---

## Remise à zéro complète

En dernier recours, pour repartir d'un état propre — **toutes les données de la
pile sont perdues** :

```bash
docker compose down -v
docker compose build --no-cache
docker compose up -d
```
