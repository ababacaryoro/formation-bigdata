# Sujet « prix » — tableau de bord attendu

Les points de vente transmettent leurs relevés de prix au fil des transactions.
Votre tableau de bord suit l'évolution des prix et le fonctionnement de la
collecte.

**Titre à donner :** `Suivi des prix à la consommation`

---

## Les indicateurs disponibles

| `indicateur` | `dimension` | `effectif` | `valeur` |
|---|---|---|---|
| `releves_par_region` | région | nombre de relevés | prix moyen |
| `prix_par_produit` | produit | nombre de relevés | prix moyen en FCFA |
| `indice_par_region` | région | nombre de relevés | indice base 100 |

> L'indice vaut 100 quand le prix observé égale le prix de référence. Un indice
> de 107 signifie « 7 % au-dessus de la référence ».

---

## Les quatre graphiques

### 1. Chiffre-clé — relevés reçus

- Type : **Big Number**
- Filtre : `indicateur = 'releves_par_region'`
- Metric : `SUM(effectif)`

### 2. Répartition — prix moyen par produit

- Type : **Bar Chart**
- Filtre : `indicateur = 'prix_par_produit'`
- Metric : `AVG(valeur)` · Dimension : `dimension`
- Triez par la métrique, décroissant

### 3. Évolution — l'indice dans le temps

- Type : **Line Chart** (ou Time-series)
- Filtre : `indicateur = 'indice_par_region'`
- Metric : `AVG(valeur)` · Axe X : `minute` · Series : `dimension`

> `minute` est du texte, pas une date. Si Superset refuse de l'utiliser comme
> axe temporel, prenez un **Bar Chart** avec `minute` en dimension : le
> résultat est lisible aussi.

### 4. Votre choix

Un quatrième graphique, libre, qui apporte quelque chose que les trois autres
ne montrent pas. Vous devrez expliquer pourquoi vous l'avez retenu.

---

## Le filtre du tableau de bord

Ajoutez un filtre sur `dimension` : il permettra de se concentrer sur une
région ou un produit.

---

## L'indicateur à ajouter

Dans `sujets/prix/config.py`, ajoutez un agrégat au dictionnaire `AGREGATS`.
Quelques idées :

- le prix moyen par **type de point de vente** — le marché est-il moins cher
  que la boutique ?
- le nombre de relevés par **point de vente**, pour repérer ceux qui ne
  transmettent plus
- l'écart entre le prix le plus élevé et le plus bas, par produit

Relancez ensuite le DAG et ajoutez un graphique correspondant.
