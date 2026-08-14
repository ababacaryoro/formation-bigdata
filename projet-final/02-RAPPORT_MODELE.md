# Modèle de rapport

Formation Big Data · ANSD / Data Innovation Lab

Recopiez cette trame dans un traitement de texte, complétez-la, et exportez en
PDF. Trois à cinq pages suffisent.

Nom du fichier : `rapport_<sujet>_<vos noms>.pdf`

---

## Page de garde

- Titre : *Suivi en temps réel — <votre sujet>*
- Vos noms
- Formation Big Data, ANSD, août 2026

---

## 1. Le sujet

Quelques lignes : de quelles données s'agit-il, d'où viennent-elles, à quoi
servent-elles pour un institut de statistique ?

---

## 2. L'architecture

Reprenez le schéma ci-dessous, puis complétez le tableau **avec vos propres
mots**.

```
  producteur ──► Kafka ──► Spark ──► MongoDB
                                        │
                                        ▼
                  Airflow ──► PostgreSQL ──► Superset
```

| Brique | À quoi elle sert, en une phrase |
|---|---|
| Producteur | … |
| Kafka | … |
| Spark | … |
| MongoDB | … |
| Airflow | … |
| PostgreSQL | … |
| Superset | … |

Puis répondez à cette question : **pourquoi deux bases de données ?**

---

## 3. Le tableau de bord

Une **capture d'ensemble** du tableau de bord, puis une capture par graphique.

Sous chaque capture, deux ou trois lignes :

- ce que le graphique montre
- ce qu'on y observe (une région qui se détache, une évolution, une anomalie)

---

## 4. Le graphique de notre choix

Quel graphique avez-vous ajouté librement, et pourquoi ? Qu'apporte-t-il que
les autres ne montrent pas ?

---

## 5. Une difficulté

Qu'est-ce qui a résisté ? Comment l'avez-vous traité ? Une difficulté
honnêtement racontée vaut mieux qu'un rapport où tout s'est bien passé.

---

## Conseils

**Faites vos captures quand la chaîne tourne depuis un moment** : les graphiques
sont plus parlants avec dix minutes de données qu'avec deux.

**Vérifiez que les captures sont lisibles** une fois insérées — quitte à
recadrer sur le graphique plutôt que de capturer tout l'écran.

**Pour capturer** : `Impr. écran` ou `Win + Maj + S` sous Windows,
`Cmd + Maj + 4` sous macOS.
