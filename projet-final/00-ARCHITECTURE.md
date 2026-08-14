# L'architecture, brique par brique

Formation Big Data · ANSD / Data Innovation Lab

```
  ┌─────────────┐   ┌───────┐   ┌───────────┐   ┌──────────┐
  │ producteur  │──►│ Kafka │──►│   Spark   │──►│ MongoDB  │
  │ (événements)│   │ (file)│   │(streaming)│   │ (données │
  └─────────────┘   └───────┘   └───────────┘   │  brutes) │
                                                 └────┬─────┘
                                                      │
                          ┌───────────────────────────┘
                          ▼
                    ┌──────────┐   ┌────────────┐   ┌──────────┐
                    │ Airflow  │──►│ PostgreSQL │──►│ Superset │
                    │(toutes   │   │ (agrégats  │   │ (tableau │
                    │ les 2 mn)│   │  publiés)  │   │ de bord) │
                    └──────────┘   └────────────┘   └──────────┘
```

---

## Deux chemins, deux rythmes

**Le chemin du haut est continu.** Il capte les événements au fur et à mesure
qu'ils arrivent, et les conserve tels quels. Rien n'est perdu, rien n'est
transformé au-delà du strict nécessaire.

**Le chemin du bas est périodique.** Toutes les deux minutes, il calcule les
indicateurs à publier. C'est lui qui alimente le tableau de bord.

Cette séparation n'est pas une complication gratuite : c'est celle qui existe
entre les **données brutes** qu'un institut collecte et les **statistiques**
qu'il publie.

---

## Pourquoi chaque brique

**Kafka** — parce que le producteur et le consommateur ne doivent pas dépendre
l'un de l'autre. Si Spark s'arrête, les événements s'accumulent dans Kafka au
lieu d'être perdus ; quand Spark repart, il reprend où il s'était arrêté.

**Spark** — parce qu'il sait lire un flux continu et le traiter par petits
lots, sans jamais s'arrêter. Sur de gros volumes, il répartirait le travail sur
plusieurs machines sans qu'on change le code.

**MongoDB** — parce que les événements arrivent sous forme de documents, de
structure parfois irrégulière, et qu'on veut les écrire vite sans les
contraindre.

**Airflow** — parce qu'un calcul périodique doit être déclenché, surveillé, et
relancé en cas d'échec. Un simple `cron` ne dirait pas ce qui s'est passé.

**PostgreSQL** — parce qu'un outil de visualisation interroge une table, pas
des documents. Et parce qu'un tableau de bord doit répondre vite : il lit
quelques milliers de lignes agrégées, jamais des millions d'événements.

**Superset** — parce que les chiffres ne servent à rien tant que personne ne
les voit.

---

## La question qui revient toujours

**Pourquoi deux bases de données ?**

MongoDB conserve **ce qui est arrivé**. PostgreSQL publie **ce qu'on en a
tiré**.

L'une est faite pour écrire vite, sans schéma imposé, et tout garder. L'autre
est faite pour être interrogée par des outils d'analyse. Les confondre est une
erreur d'architecture fréquente : un tableau de bord branché directement sur
les données brutes devient lent dès que le volume augmente.
