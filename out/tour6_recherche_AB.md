# Tour 6 — recherche sur l'ensemble des leviers

## Étape 0 — couverture des leviers

```
Tour 6 : 121 champs de décision
  A offre          10  technologie d'un modèle dans une zone, technologie d'une ligne de production
  B marketing      18  prix, équipements, publicité d'un produit
  C production     12  part de capacité d'une ligne, priorités de livraison, quantité sous-traitée
  D discrets       31  amélioration de processus, certification développement durable, fournisseur actif, part d'énergie renouvelable, politique de travail, priorité de formation, recyclabilité et engagement, salaire et budget de formation, étude d'un fournisseur, événement
  E finance         9  dette, dividende, transfert interne, prix de transfert, émission ou rachat d'actions
  F multi-tours    11  achat de licence, achat ou cession d'usines, effectif de R&D, jours-homme de R&D par technologie
  estimation       18  croissance estimée, demande future estimée, départs volontaires estimés, part de marché estimée
  hors recherche   12  licence entre équipes
```

## Étape A — offre : entrée sur une autre technologie (ordre de grandeur)


Électrique, 3 équipements, concurrents inchangés :

| Zone | Couverture | Vendeurs avec nous | Cellule, k unités | Notre demande à part égale |
|---|---|---|---|---|
| Chine | 45 % | 6 | 636 | 106 |
| Europe | 36 % | 3 | 2057 | 686 |
| USA | 27 % | 1 | 192 | 192 |

Hydrogène, 3 équipements, concurrents inchangés :

| Zone | Couverture | Vendeurs avec nous | Cellule, k unités | Notre demande à part égale |
|---|---|---|---|---|
| Chine | 11 % | 1 | 95 | 95 |
| Europe | 35 % | 2 | 412 | 206 |
| USA | 36 % | 2 | 46 | 23 |

## Étape B — marketing : frontière gain / éloignement

Prix, équipements et publicité des 6 produits cherchés ensemble, dans des zones de confiance de plus en plus larges autour des décisions du tour précédent. « Bornes larges » = optimum du modèle, à ne pas jouer tel quel.

| Zone de confiance | Gain moyen, M USD | P10 | Pire comportement | Publicité totale | Équipements |
|---|---|---|---|---|---|
| reconduit | 21600 | 18303 | 18758 | 3950 | 5 7 6 7 7 7 |
| ±3 % | 22370 | 18987 | 19438 | 4057 | 4 8 6 8 5 7 |
| ±6 % | 22721 | 19190 | 19752 | 4189 | 5 8 6 8 6 7 |
| ±10 % | 23148 | 19454 | 20116 | 4495 | 5 8 6 8 6 8 |
| ±15 % | 23585 | 19716 | 20476 | 4860 | 6 8 6 8 6 8 |
| ±20 % | 23899 | 19911 | 20718 | 5280 | 6 8 6 8 6 8 |
| ±30 % | 24458 | 20423 | 21191 | 5895 | 7 8 6 8 6 8 |
| bornes larges | 30510 | 24374 | 26193 | 11900 | 7 8 6 8 6 8 |

| Produit | reconduit | ±3 % | ±6 % | ±10 % | ±15 % | ±20 % | ±30 % | bornes larges |
|---|---|---|---|---|---|---|---|---|
| USA|Thermique | 22000 / 5 / 1100 | 22600 / 4 / 1009 | 23300 / 5 / 950 | 24100 / 5 / 850 | 25299 / 6 / 800 | 26300 / 6 / 800 | 27400 / 7 / 650 | 28100 / 7 / 1700 |
| USA|Hybride | 39700 / 7 / 400 | 40800 / 8 / 436 | 42082 / 8 / 450 | 43500 / 8 / 500 | 43500 / 8 / 580 | 44000 / 8 / 640 | 44000 / 8 / 750 | 44900 / 8 / 2500 |
| Chine|Thermique | 139000 / 6 / 650 | 143000 / 6 / 650 | 144000 / 6 / 700 | 141000 / 6 / 845 | 146000 / 6 / 900 | 147000 / 6 / 1000 | 143000 / 6 / 1100 | 143000 / 6 / 200 |
| Chine|Hybride | 243000 / 7 / 350 | 248000 / 8 / 381 | 249000 / 8 / 400 | 247000 / 8 / 450 | 250000 / 8 / 500 | 247000 / 8 / 550 | 248000 / 8 / 650 | 252000 / 8 / 2500 |
| Europe|Thermique | 25500 / 7 / 1050 | 26200 / 5 / 1144 | 27000 / 6 / 1239 | 28000 / 6 / 1350 | 29200 / 6 / 1500 | 29400 / 6 / 1650 | 29200 / 6 / 1995 | 29500 / 6 / 2500 |
| Europe|Hybride | 38800 / 7 / 400 | 39900 / 7 / 436 | 41100 / 7 / 450 | 42200 / 8 / 500 | 42200 / 8 / 580 | 42200 / 8 / 640 | 42100 / 8 / 750 | 43300 / 8 / 2500 |

Durée : 372 s.