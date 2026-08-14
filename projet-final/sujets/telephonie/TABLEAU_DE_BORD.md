# Sujet « telephonie » — tableau de bord attendu

Les antennes transmettent des enregistrements d'événements. Agrégées, ces
traces permettent d'estimer la **population présente** dans une zone.

**Titre à donner :** `Estimation de la présence de population`

---

## Les indicateurs disponibles

| `indicateur` | `dimension` | `effectif` | `valeur` |
|---|---|---|---|
| `evenements_par_region` | région | événements | durée moyenne d'appel |
| `types_evenement` | type d'événement | événements | volume moyen en Ko |
| `presence_par_region` | région | abonnés distincts | abonnés distincts |
| `volume_par_milieu` | urbain / rural | événements de données | volume moyen en Ko |

> `presence_par_region` compte les **abonnés distincts**, et non les
> événements : c'est ce qui en fait une estimation de population présente. Une
> personne qui passe dix appels ne compte qu'une fois.

---

## Les quatre graphiques

### 1. Chiffre-clé — événements reçus

- Type : **Big Number**
- Filtre : `indicateur = 'evenements_par_region'`
- Metric : `SUM(effectif)`

### 2. Répartition — présence par région

- Type : **Bar Chart**
- Filtre : `indicateur = 'presence_par_region'`
- Metric : `AVG(valeur)` · Dimension : `dimension`
- Triez par la métrique, décroissant

> On prend la **moyenne** et non la somme : additionner les abonnés distincts
> de plusieurs minutes compterait plusieurs fois la même personne.

### 3. Évolution — la présence dans le temps

- Type : **Line Chart** (ou Bar Chart)
- Filtre : `indicateur = 'presence_par_region'`
- Metric : `SUM(valeur)` · Axe X : `minute` · Series : `dimension`

### 4. Votre choix

Un quatrième graphique, libre. La répartition des types d'événements, ou le
volume de données échangé selon le milieu, sont de bons candidats.

---

## Le filtre du tableau de bord

Ajoutez un filtre sur `dimension` : il permettra de se concentrer sur une
région.

---

## Pour aller plus loin (facultatif)

L'indicateur `volume_par_milieu` est déjà calculé et disponible : ajoutez-le en
cinquième graphique si le temps le permet. Il compare l'usage des données entre
milieu urbain et rural.

Ouvrez `sujets/telephonie/config.py` et regardez la section `AGREGATS` : vous y
verrez comment chaque indicateur est calculé. Vous n'avez rien à y modifier.
