# Mise en place de l'environnement de travail

Formation Big Data — ANSD / Data Innovation Lab

Ce guide décrit l'installation à réaliser au plus tôt possible. Comptez 20 à 30 minutes. En cas de blocage, demandez de l'aide.

Outils installés : **Visual Studio Code** (éditeur), **uv** (gestionnaire d'environnements et de dépendances Python), **Git** (récupération du dépôt de la formation).

---

## 1. Installer Visual Studio Code

Téléchargez et installez VS Code depuis <https://code.visualstudio.com>.

Sous Windows, cochez pendant l'installation les options **« Ajouter à PATH »** et **« Ouvrir avec Code »** (menu contextuel de l'explorateur) : elles simplifient la suite.

## 2. Installer les extensions

Dans VS Code, ouvrez le panneau **Extensions** (`Ctrl+Shift+X`, ou `Cmd+Shift+X` sur macOS) et installez :

| Extension | Identifiant | Rôle |
|---|---|---|
| Python | `ms-python.python` | Support du langage, sélection de l'interpréteur |
| Pylance | `ms-python.vscode-pylance` | Autocomplétion et analyse de code |
| Jupyter | `ms-toolsai.jupyter` | Exécution des notebooks `.ipynb` dans VS Code |
| Data Wrangler *(optionnel)* | `ms-toolsai.datawrangler` | Exploration visuelle des DataFrames |
| Ruff *(optionnel)* | `charliermarsh.ruff` | Formatage et qualité du code |

Astuce : Tapez le nom ou collez l'identifiant dans la barre de recherche des extensions pour tomber directement sur la bonne.

## 3. Installer Git

Vérifiez d'abord si Git est déjà présent, dans un terminal :

```bash
git --version
```

Si la commande échoue, installez Git depuis <https://git-scm.com/downloads> (sous Windows, conservez les options par défaut).

## 4. Installer uv

`uv` remplace `pip`, `venv` et `conda` en un seul outil, beaucoup plus rapide. Il installe aussi Python lui-même : **inutile d'installer Python séparément**.

**Windows** — dans PowerShell :

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS / Linux** — dans un terminal :

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Fermez puis rouvrez le terminal**, et vérifiez :

```bash
uv --version
```

Si la commande n'est pas reconnue, voir la section Dépannage.

## 5. Récupérer le dépôt de la formation

Dans le dossier de votre choix :

```bash
git clone https://github.com/ababacaryoro/formation-bigdata.git
cd formation-bigdata
```

Puis ouvrez le dossier dans VS Code : `code .` (ou *Fichier → Ouvrir le dossier*).

## 6. Créer l'environnement virtuel et installer les dépendances

Le dépôt contient déjà les fichiers `pyproject.toml` (liste des dépendances) et `uv.lock` (versions exactes). Une seule commande suffit, dans le terminal intégré de VS Code (`Ctrl+ù` ou *Terminal → Nouveau terminal*) :

```bash
uv sync
```

Cette commande :

- installe la version de Python attendue si elle est absente ;
- crée l'environnement virtuel dans un dossier `.venv/` à la racine du projet ;
- installe toutes les bibliothèques de la formation (pandas, dask, pyarrow, jupyter, ipykernel…) aux versions exactes du `uv.lock`.

Tout le monde obtient ainsi **exactement le même environnement**, ce qui évite les écarts de comportement d'un poste à l'autre.

## 7. Connecter VS Code à cet environnement

1. Ouvrez la palette de commandes : `Ctrl+Shift+P` (`Cmd+Shift+P` sur macOS).
2. Tapez **« Python: Select Interpreter »** et validez.
3. Choisissez l'interpréteur situé dans `.venv` du projet (il est en général proposé en tête de liste, avec la mention *Recommended*).

Ouvrez ensuite un notebook, par exemple `01-limites-du-poste/notebooks/01_ca_marche.ipynb`. En haut à droite, cliquez sur **« Select Kernel »** → *Python Environments* → l'environnement `.venv` du projet.

## 8. Vérifier que tout fonctionne

Exécutez la première cellule du notebook (`Maj+Entrée`). Elle affiche les versions installées et un `✔` si l'environnement est correct.

En cas d'échec, vérifiez que le noyau sélectionné en haut à droite est bien celui du `.venv` du projet, et non un Python système.

---

## Commandes uv utiles

| Commande | Effet |
|---|---|
| `uv sync` | Installe / met à jour l'environnement à partir de `pyproject.toml` et `uv.lock` |
| `uv add <paquet>` | Ajoute une dépendance au projet et l'installe |
| `uv add --dev <paquet>` | Ajoute une dépendance de développement (tests, outils) |
| `uv remove <paquet>` | Retire une dépendance |
| `uv run <commande>` | Exécute une commande dans l'environnement du projet, sans l'activer |
| `uv run python script.py` | Exécute un script Python dans l'environnement du projet |
| `uv lock` | Recalcule le fichier de verrouillage des versions |
| `uv python list` | Liste les versions de Python disponibles / installées |
| `uv self update` | Met à jour uv |

Avec `uv run`, il n'est **jamais nécessaire d'activer manuellement** l'environnement virtuel. Si vous y tenez : `source .venv/bin/activate` (macOS/Linux) ou `.venv\Scripts\activate` (Windows).

Règle de versionnement : `pyproject.toml` et `uv.lock` sont suivis par Git ; le dossier `.venv/` ne l'est **jamais** (il figure dans le `.gitignore`).

---

## Dépannage

**`uv` : commande introuvable après installation**
Fermez complètement le terminal (et VS Code) puis rouvrez-les : la variable `PATH` n'est prise en compte qu'au démarrage d'une nouvelle session.

**Le téléchargement échoue derrière le pare-feu ou le proxy de l'institution**
Les accès suivants doivent être autorisés : `github.com`, `pypi.org`, `files.pythonhosted.org`, `astral.sh`. Si un proxy est en place, renseignez-le avant de relancer la commande :

```bash
# macOS / Linux
export HTTPS_PROXY=http://<serveur>:<port>
```

```powershell
# Windows (PowerShell)
$env:HTTPS_PROXY = "http://<serveur>:<port>"
```

En cas de connexion lente, augmentez le délai d'attente : `UV_HTTP_TIMEOUT=120`.

**L'environnement `.venv` n'apparaît pas dans la liste des interpréteurs**
Relancez `uv sync`, puis rechargez la fenêtre VS Code : palette de commandes → *Developer: Reload Window*. Si le problème persiste, choisissez *Enter interpreter path* et saisissez le chemin complet vers `.venv/bin/python` (macOS/Linux) ou `.venv\Scripts\python.exe` (Windows).

**Le notebook ne trouve pas de noyau (kernel)**
Le paquet `ipykernel` doit être présent dans l'environnement : `uv sync` l'installe automatiquement. Si nécessaire : `uv add --dev ipykernel`, puis resélectionnez le noyau.

**« Import could not be resolved » alors que la bibliothèque est installée**
Le mauvais interpréteur est sélectionné. Reprenez l'étape 7, puis rechargez la fenêtre.

**Aucune installation possible sur le poste (droits administrateur refusés)**
Signalez-le dès que possible : une solution de repli (environnement partagé sur serveur) sera mise en place.

---

## Annexe — Démarrer un projet uv depuis zéro

Utile pour votre projet de groupe ou pour vos travaux ultérieurs :

```bash
uv init mon-projet          # crée pyproject.toml, .python-version, .gitignore
cd mon-projet
uv python pin 3.12          # fige la version de Python
uv add pandas pyarrow       # ajoute les dépendances (crée .venv au passage)
uv add --dev ipykernel      # nécessaire pour les notebooks dans VS Code
code .                      # ouvre le projet dans VS Code
```
