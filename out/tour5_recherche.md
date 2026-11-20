# Tour 5 — recherche sur l'ensemble des leviers

## Étape 0 — couverture des leviers

```
Tour 5 : 120 champs de décision
  A offre          10  technologie d'un modèle dans une zone, technologie d'une ligne de production
  B marketing      18  prix, équipements, publicité d'un produit
  C production     12  part de capacité d'une ligne, priorités de livraison, quantité sous-traitée
  D discrets       31  amélioration de processus, certification développement durable, fournisseur actif, part d'énergie renouvelable, politique de travail, priorité de formation, recyclabilité et engagement, salaire et budget de formation, étude d'un fournisseur, événement
  E finance         8  dette, dividende, transfert interne, prix de transfert
  F multi-tours    11  achat de licence, achat ou cession d'usines, effectif de R&D, jours-homme de R&D par technologie
  estimation       18  croissance estimée, demande future estimée, départs volontaires estimés, part de marché estimée
  hors recherche   12  licence entre équipes
```

## Étape A — offre : entrée sur une autre technologie (ordre de grandeur)


Électrique, 3 équipements, concurrents inchangés :

| Zone | Couverture | Vendeurs avec nous | Cellule, k unités | Notre demande à part égale |
|---|---|---|---|---|
| Chine | 37 % | 3 | 339 | 113 |
| Europe | 30 % | 2 | 1033 | 517 |
| USA | 21 % | 1 | 78 | 78 |

Hydrogène, 3 équipements, concurrents inchangés :

| Zone | Couverture | Vendeurs avec nous | Cellule, k unités | Notre demande à part égale |
|---|---|---|---|---|
| Chine | 8 % | 1 | 35 | 35 |
| Europe | 25 % | 1 | 164 | 164 |
| USA | 26 % | 1 | 96 | 96 |

## Étape B — marketing : frontière gain / éloignement

Prix, équipements et publicité des 6 produits cherchés ensemble, dans des zones de confiance de plus en plus larges autour des décisions du tour précédent. « Bornes larges » = optimum du modèle, à ne pas jouer tel quel.

| Zone de confiance | Gain moyen, M USD | P10 | Pire comportement | Publicité totale | Équipements |
|---|---|---|---|---|---|
| reconduit | 20297 | 16385 | 17394 | 2850 | 5 6 6 6 5 6 |
| ±3 % | 21098 | 17092 | 18024 | 2990 | 4 7 5 7 5 6 |
| ±6 % | 21633 | 17437 | 18416 | 3276 | 4 7 5 7 6 6 |
| ±10 % | 22116 | 17674 | 18765 | 3580 | 4 7 6 7 6 7 |
| ±15 % | 22586 | 18111 | 19087 | 4058 | 5 7 6 7 6 7 |
| ±20 % | 22992 | 18583 | 19351 | 4540 | 5 7 5 7 6 7 |
| ±30 % | 23548 | 18940 | 19724 | 5200 | 6 7 5 7 6 7 |
| bornes larges | 30808 | 23111 | 24488 | 15000 | 6 7 5 7 6 7 |

| Produit | reconduit | ±3 % | ±6 % | ±10 % | ±15 % | ±20 % | ±30 % | bornes larges |
|---|---|---|---|---|---|---|---|---|
| USA|Thermique | 19500 / 5 / 800 | 20085 / 4 / 850 | 20670 / 4 / 900 | 21400 / 4 / 1000 | 22400 / 5 / 1100 | 23300 / 5 / 1280 | 25300 / 6 / 1450 | 26600 / 6 / 2500 |
| USA|Hybride | 37000 / 6 / 300 | 38100 / 7 / 300 | 39200 / 7 / 350 | 40500 / 7 / 390 | 41100 / 7 / 435 | 41000 / 7 / 480 | 40800 / 7 / 550 | 42000 / 7 / 2500 |
| Chine|Thermique | 129000 / 6 / 450 | 132870 / 5 / 490 | 136740 / 5 / 531 | 141000 / 6 / 550 | 139000 / 6 / 650 | 137000 / 5 / 700 | 138000 / 5 / 800 | 141000 / 5 / 2500 |
| Chine|Hybride | 230000 / 6 / 250 | 236000 / 7 / 250 | 243000 / 7 / 295 | 248000 / 7 / 300 | 249000 / 7 / 350 | 249000 / 7 / 400 | 244000 / 7 / 450 | 254000 / 7 / 2500 |
| Europe|Thermique | 23000 / 5 / 750 | 23690 / 5 / 800 | 24380 / 6 / 850 | 25300 / 6 / 950 | 26000 / 6 / 1087 | 26200 / 6 / 1200 | 26300 / 6 / 1400 | 26300 / 6 / 2500 |
| Europe|Hybride | 35000 / 6 / 300 | 36000 / 6 / 300 | 37100 / 6 / 350 | 38400 / 7 / 390 | 40100 / 7 / 435 | 40500 / 7 / 480 | 40800 / 7 / 550 | 41000 / 7 / 2500 |

Durée : 176 s.