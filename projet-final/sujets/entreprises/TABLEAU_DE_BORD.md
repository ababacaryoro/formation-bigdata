# Sujet « ninea » — tableau de bord attendu

Les guichets transmettent les immatriculations, modifications et radiations
d'entreprises. Votre tableau de bord suit **l'activité du répertoire** et le
**fonctionnement du service**.

**Titre à donner :** `Suivi du répertoire des entreprises`

---

## Les indicateurs disponibles

| `indicateur` | `dimension` | `effectif` | `valeur` |
|---|---|---|---|
| `mouvements_par_region` | région | mouvements | effectif déclaré moyen |
| `operations` | type d'opération | mouvements | délai moyen en minutes |
| `immatriculations_par_secteur` | secteur | immatriculations | effectif déclaré moyen |
| `delai_par_guichet` | guichet | mouvements | délai de traitement en minutes |

> Le **délai de traitement** est le temps entre l'arrivée au guichet et
> l'enregistrement. C'est un indicateur de qualité de service : plus il est
> court, plus vite l'entreprise est visible dans le répertoire.

---

## Les quatre graphiques

### 1. Chiffre-clé — mouvements enregistrés

- Type : **Big Number**
- Filtre : `indicateur = 'mouvements_par_region'`
- Metric : `SUM(effectif)`

### 2. Répartition — immatriculations par secteur

- Type : **Bar Chart**
- Filtre : `indicateur = 'immatriculations_par_secteur'`
- Metric : `SUM(effectif)` · Dimension : `dimension`
- Triez par la métrique, décroissant

### 3. Qualité de service — délai par guichet

- Type : **Bar Chart**
- Filtre : `indicateur = 'delai_par_guichet'`
- Metric : `AVG(valeur)` · Dimension : `dimension`
- Triez par la métrique, décroissant : les guichets les plus lents en premier

### 4. Votre choix

Un quatrième graphique, libre. L'évolution des mouvements dans le temps est un
bon candidat, ou la répartition entre immatriculations et radiations.

---

## Le filtre du tableau de bord

Ajoutez un filtre sur `dimension` : il permettra de se concentrer sur une
région, un secteur ou un guichet.

---

## Pour aller plus loin (facultatif)

L'indicateur `operations` est déjà calculé et disponible : ajoutez-le en
cinquième graphique si le temps le permet. Il montre la répartition entre
immatriculations, modifications et radiations.

Ouvrez `sujets/ninea/config.py` et regardez la section `AGREGATS` : vous y
verrez comment chaque indicateur est calculé. Vous n'avez rien à y modifier.
