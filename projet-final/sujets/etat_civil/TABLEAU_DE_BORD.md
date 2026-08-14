# Sujet « etat_civil » — tableau de bord attendu

Les centres d'état civil déclarent naissances, mariages et décès. Votre tableau
de bord suit **l'activité des centres** et la **qualité de l'enregistrement**.

**Titre à donner :** `Suivi de l'état civil`

---

## Les indicateurs disponibles

| `indicateur` | `dimension` | `effectif` | `valeur` |
|---|---|---|---|
| `actes_par_region` | région | actes | délai moyen en jours |
| `actes_par_type` | type d'acte | actes | délai moyen en jours |
| `numerisation_par_region` | région | actes | part numérisée en % |
| `tardives_par_region` | région | actes | part de déclarations tardives en % |

> Une déclaration est dite **tardive** au-delà de trente jours. Le taux de
> numérisation varie fortement d'une région à l'autre.

---

## Les quatre graphiques

### 1. Chiffre-clé — actes enregistrés

- Type : **Big Number**
- Filtre : `indicateur = 'actes_par_region'`
- Metric : `SUM(effectif)`

### 2. Répartition — les types d'actes

- Type : **Pie Chart** (ou Bar Chart)
- Filtre : `indicateur = 'actes_par_type'`
- Metric : `SUM(effectif)` · Dimension : `dimension`

### 3. Qualité — la numérisation par région

- Type : **Bar Chart**
- Filtre : `indicateur = 'numerisation_par_region'`
- Metric : `AVG(valeur)` · Dimension : `dimension`
- Triez par la métrique, **croissant** : les régions en retard apparaissent
  en premier

### 4. Votre choix

Un quatrième graphique, libre. Les déclarations tardives par région sont un bon
candidat — c'est un indicateur de couverture de l'état civil.

---

## Le filtre du tableau de bord

Ajoutez un filtre sur `dimension` : il permettra de se concentrer sur une
région ou un type d'acte.

---

## Pour aller plus loin (facultatif)

L'indicateur `tardives_par_region` est déjà calculé et disponible : ajoutez-le
en cinquième graphique si le temps le permet. C'est un indicateur de couverture
de l'état civil.

Ouvrez `sujets/etat_civil/config.py` et regardez la section `AGREGATS` : vous y
verrez comment chaque indicateur est calculé. Vous n'avez rien à y modifier.
