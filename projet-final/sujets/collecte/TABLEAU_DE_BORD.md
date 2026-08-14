# Sujet « collecte » — tableau de bord attendu

Les tablettes des enquêteurs remontent les questionnaires collectés. Votre
tableau de bord sert au **pilotage de la collecte** : où en est-on, et
peut-on faire confiance aux données qui arrivent ?

**Titre à donner :** `Pilotage de la collecte`

---

## Les indicateurs disponibles

| `indicateur` | `dimension` | `effectif` | `valeur` |
|---|---|---|---|
| `questionnaires_par_region` | région | questionnaires | durée moyenne |
| `statuts` | statut | questionnaires | taille moyenne des ménages |
| `duree_par_enqueteur` | enquêteur | questionnaires complets | durée moyenne en minutes |
| `refus_par_enqueteur` | enquêteur | questionnaires | taux de refus en % |

> Deux ou trois enquêteurs ont un comportement atypique : entretiens très
> courts, ou beaucoup de refus. Votre tableau de bord doit permettre de les
> repérer.

---

## Les quatre graphiques

### 1. Chiffre-clé — questionnaires collectés

- Type : **Big Number**
- Filtre : `indicateur = 'questionnaires_par_region'`
- Metric : `SUM(effectif)`

### 2. Répartition — les statuts

- Type : **Pie Chart** (ou Bar Chart)
- Filtre : `indicateur = 'statuts'`
- Metric : `SUM(effectif)` · Dimension : `dimension`

### 3. Contrôle qualité — durée par enquêteur

- Type : **Bar Chart**
- Filtre : `indicateur = 'duree_par_enqueteur'`
- Metric : `AVG(valeur)` · Dimension : `dimension`
- Triez par la métrique, **croissant** : les enquêteurs suspects apparaissent
  en premier
- Row limit : 15

### 4. Votre choix

Un quatrième graphique, libre. Le taux de refus par enquêteur est un bon
candidat, mais vous pouvez proposer autre chose.

---

## Le filtre du tableau de bord

Ajoutez un filtre sur `dimension` : il permettra de se concentrer sur une
région ou un enquêteur.

---

## Pour aller plus loin (facultatif)

L'indicateur `refus_par_enqueteur` est déjà calculé et disponible : ajoutez-le
en cinquième graphique si le temps le permet. Il complète bien le contrôle
qualité.

Ouvrez `sujets/collecte/config.py` et regardez la section `AGREGATS` : vous y
verrez comment chaque indicateur est calculé. Vous n'avez rien à y modifier.
