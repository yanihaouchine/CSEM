# Tour 8 — recherche sur l'ensemble des leviers

## Étape 0 — couverture des leviers

```
Tour 8 : 125 champs de décision
  A offre          10  technologie d'un modèle dans une zone, technologie d'une ligne de production
  B marketing      24  ciblage de la stratégie marketing d'un produit, prix, équipements, publicité d'un produit
  C production     11  part de capacité d'une ligne, priorités de livraison, quantité sous-traitée
  D discrets       30  amélioration de processus, certification développement durable, fournisseur actif, part d'énergie renouvelable, politique de travail, priorité de formation, recyclabilité et engagement, salaire et budget de formation, étude d'un fournisseur, événement
  E finance         9  dette, dividende, transfert interne, prix de transfert, émission ou rachat d'actions
  F multi-tours    11  achat de licence, achat ou cession d'usines, effectif de R&D, jours-homme de R&D par technologie
  estimation       18  croissance estimée, demande future estimée, départs volontaires estimés, part de marché estimée
  hors recherche   12  licence entre équipes
```

Objectif : points du barème de l'instructeur (model/points.py, objectif.py). Repères : 1 Md USD de coût = -1.2 point ; +1 % de demande = +0.57 point.

## Étape D — leviers discrets

Valeur d'un point de demande : 287 M USD par tour (marge brute / 100), à condition de pouvoir produire.
Référence : résultat net 21528 M USD, score ESG cumulé 3.34, fournisseurs requis 3.0.

### politique : esg2.labor.regulations

| Option | Résultat net, M USD | Demande, points de % | Valeur, M USD | Barème, points | Détail des points | Remarque |
|---|---|---|---|---|---|---|
| Conformité minimale | +1792 | inconnu | inconnu | +1.88 (coût seul) | {'marge USA': 0.28, 'marge Chine': 0.43, 'marge Europe': 0.1, 'ROE': 0.48, "rentabilité de l'action": 0.27, 'création de valeur': 0.32} | esg2.labor.regulations=Conformité minimale |
| Partenariat stratégique **(retenu)** | -1792 | +5.1 | -322 | +0.38 | {'part USA': 0.25, 'part Chine': 0.23, 'part Europe': 0.42, 'marge USA': -0.2, 'marge Chine': -0.25, 'marge Europe': -0.08, 'ROE': -0.17, "rentabilité de l'action": -0.08, 'création de valeur': 0.27} |  |
| Initiatives d'engagement communautaire | +0 | +0.0 | +0 | +0.00 |  |  |
| Conformité standard | +0 | -4.5 | -1298 | -2.40 | {'part USA': -0.27, 'part Chine': -0.13, 'part Europe': -0.53, 'marge USA': -0.05, 'marge Chine': -0.2, 'ROE': -0.38, "rentabilité de l'action": -0.27, 'création de valeur': -0.53} |  |

### politique : esg2.employee.relations

| Option | Résultat net, M USD | Demande, points de % | Valeur, M USD | Barème, points | Détail des points | Remarque |
|---|---|---|---|---|---|---|
| Efficacité accrue en R&D | +0 | inconnu | inconnu | +0.00 (coût seul) |  | esg2.employee.relations=Efficacité accrue en R&D |
| Approche équilibrée | +0 | +0.0 | +0 | +0.00 |  |  |
| Accent sur le bien-être des employés | +0 | -0.8 | -220 | -0.42 | {'part USA': -0.07, 'part Europe': -0.07, 'ROE': -0.08, 'création de valeur': -0.07} |  |
| Collaboration syndicale | -539 | -0.6 | -709 | -0.90 | {'part USA': -0.05, 'part Europe': -0.07, 'marge USA': -0.08, 'marge Chine': -0.17, 'marge Europe': -0.05, 'ROE': -0.23, "rentabilité de l'action": -0.12, 'création de valeur': -0.1} |  |

### politique : esg2.management.quotas

| Option | Résultat net, M USD | Demande, points de % | Valeur, M USD | Barème, points | Détail des points | Remarque |
|---|---|---|---|---|---|---|
| Recrutement aveugle, suppression des quotas | +0 | inconnu | inconnu | +0.00 (coût seul) |  | esg2.management.quotas=Recrutement aveugle, suppression des quotas |
| Priorisez modérément le recrutement diversifié | +0 | -0.0 | -2 | +0.00 |  |  |
| Programmes de mentorat | +0 | +0.0 | +0 | +0.00 |  |  |
| Prime de départ | +0 | -0.7 | -196 | -0.35 | {'part USA': -0.05, 'part Europe': -0.07, 'ROE': -0.07} |  |

### priorités de formation (base, sécurité, santé, non-discrimination, éthique)

| Option | Résultat net, M USD | Demande, points de % | Valeur, M USD | Barème, points | Détail des points | Remarque |
|---|---|---|---|---|---|---|
| 00111 | +0 | +1.5 | +418 | +1.07 | {'part USA': 0.13, 'part Chine': 0.07, 'part Europe': 0.13, 'marge USA': 0.07, 'marge Chine': 0.07, 'ROE': 0.12, "rentabilité de l'action": 0.05, 'création de valeur': 0.18, 'productivité': 0.25} | priorités 00111 jamais observées (extrapolé) |
| 00011 | +0 | +0.5 | +133 | +0.52 | {'création de valeur': 0.08, 'productivité': 0.25} | priorités 00011 jamais observées (extrapolé) |
| 00101 | +0 | +0.1 | +40 | +0.30 | {'productivité': 0.25} | priorités 00101 jamais observées (extrapolé) |
| 00001 | +0 | +0.0 | +0 | +0.25 | {'productivité': 0.25} |  |
| 01111 | +0 | -0.8 | -234 | -0.17 | {'part USA': -0.07, 'part Europe': -0.07, 'ROE': -0.08, 'création de valeur': -0.07, 'productivité': 0.25} | priorités 01111 jamais observées (extrapolé) |
| 01011 | +0 | -1.8 | -519 | -0.70 | {'part USA': -0.12, 'part Chine': -0.08, 'part Europe': -0.15, 'ROE': -0.22, "rentabilité de l'action": -0.12, 'création de valeur': -0.15, 'productivité': 0.25} | priorités 01011 jamais observées (extrapolé) |
| 00000 | inconnu | -5.8 | inconnu | inconnu |  | priorités 00000 jamais observées (extrapolé) |
| 00010 | inconnu | -4.5 | inconnu | inconnu |  | priorités 00010 jamais observées (extrapolé) |
| 00100 | inconnu | -4.8 | inconnu | inconnu |  | priorités 00100 jamais observées (extrapolé) |
| 00110 | inconnu | -3.5 | inconnu | inconnu |  | priorités 00110 jamais observées (extrapolé) |
| 01000 | inconnu | -8.1 | inconnu | inconnu |  | priorités 01000 jamais observées (extrapolé) |
| 01001 | inconnu | -3.1 | inconnu | inconnu |  | priorités 01001 jamais observées (extrapolé) |
| 01010 | inconnu | -6.8 | inconnu | inconnu |  | priorités 01010 jamais observées (extrapolé) |
| 01100 | inconnu | -7.1 | inconnu | inconnu |  | priorités 01100 jamais observées (extrapolé) |

### recyclabilité

| Option | Résultat net, M USD | Demande, points de % | Valeur, M USD | Barème, points | Détail des points | Remarque |
|---|---|---|---|---|---|---|
| Conception pour le démontage facile | +1044 | inconnu | inconnu | +1.20 (coût seul) | {'marge USA': 0.2, 'marge Chine': 0.25, 'marge Europe': 0.07, 'ROE': 0.35, "rentabilité de l'action": 0.13, 'création de valeur': 0.2} | recyclabilité Conception pour le démontage facile |
| Évaluation du cycle de vie + engagement | +0 | +0.0 | +0 | +0.00 |  |  |
| Systèmes de cycle fermé + engagement | -870 | +1.4 | -469 | -0.33 | {'part USA': 0.13, 'part Chine': 0.07, 'part Europe': 0.12, 'marge USA': -0.08, 'marge Chine': -0.17, 'marge Europe': -0.08, 'ROE': -0.22, "rentabilité de l'action": -0.12} |  |
| Recyclage des matériaux de base | +1914 | -5.7 | +281 | -0.67 | {'part USA': -0.32, 'part Chine': -0.17, 'part Europe': -0.67, 'marge USA': 0.23, 'marge Chine': 0.25, 'marge Europe': 0.1, 'ROE': 0.15, "rentabilité de l'action": 0.05, 'création de valeur': -0.3} |  |
| Évaluation du cycle de vie | +0 | -1.5 | -430 | -0.75 | {'part USA': -0.1, 'part Europe': -0.12, 'ROE': -0.18, "rentabilité de l'action": -0.1, 'création de valeur': -0.12} |  |
| Utilisation de matériaux recyclés | +522 | -2.9 | -309 | -0.82 | {'part USA': -0.17, 'part Chine': -0.1, 'part Europe': -0.25, 'ROE': -0.12, 'création de valeur': -0.18} |  |
| Systèmes de cycle fermé | -870 | inconnu | inconnu | -1.02 (coût seul) | {'marge USA': -0.15, 'marge Chine': -0.23, 'marge Europe': -0.08, 'ROE': -0.27, "rentabilité de l'action": -0.18, 'création de valeur': -0.1} | recyclabilité Systèmes à circuit fermé |
| Recyclage des matériaux de base + engagement | inconnu | inconnu | inconnu | inconnu |  | esg.recyclability.commit = True refusé par la plateforme (valeur restée à False) |
| Conception pour le démontage facile + engagement | inconnu | inconnu | inconnu | inconnu |  | esg.recyclability.commit = True refusé par la plateforme (valeur restée à False) |
| Utilisation de matériaux recyclés + engagement | inconnu | inconnu | inconnu | inconnu |  | esg.recyclability.commit = True refusé par la plateforme (valeur restée à False) |

### améliorations de processus (CO2, énergie, eau)

| Option | Résultat net, M USD | Demande, points de % | Valeur, M USD | Barème, points | Détail des points | Remarque |
|---|---|---|---|---|---|---|
| 011 **(retenu)** | -786 | +10.0 | +2079 | +3.97 | {'part USA': 0.58, 'part Chine': 0.37, 'part Europe': 0.78, 'marge USA': 0.12, 'marge Chine': 0.15, 'ROE': 0.58, "rentabilité de l'action": 0.35, 'création de valeur': 1.07} | points par amélioration : estimation prudente |
| 101 | -1336 | +10.0 | +1529 | +3.35 | {'part USA': 0.58, 'part Chine': 0.37, 'part Europe': 0.78, 'marge Chine': 0.07, 'marge Europe': -0.08, 'ROE': 0.48, "rentabilité de l'action": 0.22, 'création de valeur': 0.92} | points par amélioration : estimation prudente |
| 001 | -93 | +5.0 | +1340 | +2.37 | {'part USA': 0.25, 'part Chine': 0.23, 'part Europe': 0.42, 'marge USA': 0.13, 'marge Chine': 0.13, 'ROE': 0.42, "rentabilité de l'action": 0.2, 'création de valeur': 0.58} | points par amélioration : estimation prudente |
| 111 | -4776 | +15.0 | -478 | +1.67 | {'part USA': 0.88, 'part Chine': 0.53, 'part Europe': 1.23, 'marge USA': -0.6, 'marge Chine': -0.73, 'marge Europe': -0.32, 'ROE': -0.17, "rentabilité de l'action": -0.08, 'création de valeur': 0.92} | points par amélioration : estimation prudente |
| 010 | -698 | +5.0 | +735 | +1.62 | {'part USA': 0.25, 'part Chine': 0.23, 'part Europe': 0.42, 'marge Europe': -0.05, 'ROE': 0.22, "rentabilité de l'action": 0.1, 'création de valeur': 0.45} | points par amélioration : estimation prudente |
| 100 | -1251 | +5.0 | +182 | +0.98 | {'part USA': 0.25, 'part Chine': 0.23, 'part Europe': 0.42, 'marge USA': -0.1, 'marge Chine': -0.08, 'marge Europe': -0.08, 'création de valeur': 0.35} | points par amélioration : estimation prudente |
| 000 | +0 | +0.0 | +0 | +0.00 |  | points par amélioration : estimation prudente |
| 110 | -4706 | +10.0 | -1841 | -1.10 | {'part USA': 0.58, 'part Chine': 0.37, 'part Europe': 0.78, 'marge USA': -0.87, 'marge Chine': -0.95, 'marge Europe': -0.38, 'ROE': -0.55, "rentabilité de l'action": -0.35, 'création de valeur': 0.27} | points par amélioration : estimation prudente |

### énergie renouvelable, %

| Option | Résultat net, M USD | Demande, points de % | Valeur, M USD | Barème, points | Détail des points | Remarque |
|---|---|---|---|---|---|---|
| 100 | +0 | +0.0 | +0 | +0.00 |  |  |
| 50 | +62 | -5.5 | -1514 | -2.85 | {'part USA': -0.32, 'part Chine': -0.17, 'part Europe': -0.65, 'marge USA': -0.07, 'marge Chine': -0.23, 'ROE': -0.45, "rentabilité de l'action": -0.27, 'création de valeur': -0.67} |  |
| 0 | +124 | -11.0 | -3028 | -5.48 | {'part USA': -0.55, 'part Chine': -0.4, 'part Europe': -0.97, 'marge USA': -0.38, 'marge Chine': -0.55, 'ROE': -0.88, "rentabilité de l'action": -0.53, 'création de valeur': -1.18} |  |

### fournisseurs actifs

| Option | Résultat net, M USD | Demande, points de % | Valeur, M USD | Barème, points | Détail des points | Remarque |
|---|---|---|---|---|---|---|
| 4 **(retenu)** | -6064 | +9.9 | -3227 | +2.18 | {'part USA': 0.58, 'part Chine': 0.37, 'part Europe': 0.78, 'marge USA': -1.17, 'marge Chine': -1.33, 'marge Europe': -0.47, 'ROE': -0.8, "rentabilité de l'action": -0.55, 'fournisseurs': 4.73} | note = image moyenne publiée ; 5,2 pts (développement durable) + 8 pts (qualité) par point |
| 1+4+5 | +0 | +0.0 | +0 | +0.00 |  | note = image moyenne publiée ; 5,2 pts (développement durable) + 8 pts (qualité) par point |
| 1+4 | -6064 | +6.6 | -4173 | -0.78 | {'part USA': 0.35, 'part Chine': 0.23, 'part Europe': 0.53, 'marge USA': -1.37, 'marge Chine': -1.55, 'marge Europe': -0.5, 'ROE': -1.08, "rentabilité de l'action": -0.75, 'création de valeur': -0.42, 'fournisseurs': 3.77} | note = image moyenne publiée ; 5,2 pts (développement durable) + 8 pts (qualité) par point |
| 1+2+4 | -49 | -2.2 | -680 | -2.85 | {'part USA': -0.13, 'part Chine': -0.08, 'part Europe': -0.22, 'marge Chine': -0.07, 'ROE': -0.23, "rentabilité de l'action": -0.12, 'création de valeur': -0.25, 'fournisseurs': -1.68} | note = image moyenne publiée ; 5,2 pts (développement durable) + 8 pts (qualité) par point |
| 1 | -6064 | +3.3 | -5118 | -4.13 | {'part USA': 0.23, 'part Chine': 0.13, 'part Europe': 0.25, 'marge USA': -1.7, 'marge Chine': -1.7, 'marge Europe': -0.55, 'ROE': -1.27, "rentabilité de l'action": -0.95, 'création de valeur': -0.77, 'fournisseurs': 2.18} | note = image moyenne publiée ; 5,2 pts (développement durable) + 8 pts (qualité) par point |
| 4+5 | -3907 | -1.6 | -4380 | -7.12 | {'part USA': -0.12, 'part Europe': -0.12, 'marge USA': -1.1, 'marge Chine': -1.3, 'marge Europe': -0.35, 'ROE': -1.1, "rentabilité de l'action": -0.77, 'création de valeur': -0.95, 'fournisseurs': -1.27} | note = image moyenne publiée ; 5,2 pts (développement durable) + 8 pts (qualité) par point |
| 5 | inconnu | -13.2 | inconnu | inconnu |  | note = image moyenne publiée ; 5,2 pts (développement durable) + 8 pts (qualité) par point |
| 3 | inconnu | -33.0 | inconnu | inconnu |  | note = image moyenne publiée ; 5,2 pts (développement durable) + 8 pts (qualité) par point |
| 3+5 | inconnu | -23.1 | inconnu | inconnu |  | note = image moyenne publiée ; 5,2 pts (développement durable) + 8 pts (qualité) par point |
| 3+4 | inconnu | -11.5 | inconnu | inconnu |  | note = image moyenne publiée ; 5,2 pts (développement durable) + 8 pts (qualité) par point |
| 3+4+5 | inconnu | -12.1 | inconnu | inconnu |  | note = image moyenne publiée ; 5,2 pts (développement durable) + 8 pts (qualité) par point |
| 2 | inconnu | -19.8 | inconnu | inconnu |  | note = image moyenne publiée ; 5,2 pts (développement durable) + 8 pts (qualité) par point |
| 2+5 | inconnu | -16.5 | inconnu | inconnu |  | note = image moyenne publiée ; 5,2 pts (développement durable) + 8 pts (qualité) par point |
| 2+4 | inconnu | -4.9 | inconnu | inconnu |  | note = image moyenne publiée ; 5,2 pts (développement durable) + 8 pts (qualité) par point |

### certification

| Option | Résultat net, M USD | Demande, points de % | Valeur, M USD | Barème, points | Détail des points | Remarque |
|---|---|---|---|---|---|---|
| Argent **(retenu)** | -19 | +11.0 | +3132 | +7.13 | {'part USA': 0.62, 'part Chine': 0.38, 'part Europe': 0.82, 'marge USA': 0.22, 'marge Chine': 0.4, 'ROE': 0.78, "rentabilité de l'action": 0.47, 'création de valeur': 1.45, 'certification': 2.0} | l'écart entre niveaux n'est pas mesuré |
| Bronze | -6 | +11.0 | +3145 | +5.13 | {'part USA': 0.62, 'part Chine': 0.38, 'part Europe': 0.82, 'marge USA': 0.22, 'marge Chine': 0.4, 'ROE': 0.78, "rentabilité de l'action": 0.47, 'création de valeur': 1.45} | l'écart entre niveaux n'est pas mesuré |
| Pas de certification | +0 | +0.0 | +0 | -2.00 | {'certification': -2.0} | l'écart entre niveaux n'est pas mesuré |

### événement : esg.green.loan.gamble

| Option | Résultat net, M USD | Demande, points de % | Valeur, M USD | Barème, points | Détail des points | Remarque |
|---|---|---|---|---|---|---|
| Refuser l'offre | +0 | inconnu | inconnu | +0.00 (coût seul) |  | effet sur la demande non publié |
| Accepter l'offre avec un engagement moyen | +0 | inconnu | inconnu | +0.00 (coût seul) |  | effet sur la demande non publié |
| Accepter l'offre avec un engagement étendu | +0 | inconnu | inconnu | +0.00 (coût seul) |  | effet sur la demande non publié |

### événement : esg.battery.bargaining

| Option | Résultat net, M USD | Demande, points de % | Valeur, M USD | Barème, points | Détail des points | Remarque |
|---|---|---|---|---|---|---|
| Co-développer les batteries | +20 | inconnu | inconnu | +0.02 (coût seul) |  | effet sur la demande non publié |
| Conserver les batteries actuelles | +0 | inconnu | inconnu | +0.00 (coût seul) |  | effet sur la demande non publié |
| Sous traiter les batteries | -877 | inconnu | inconnu | -1.03 (coût seul) | {'marge USA': -0.15, 'marge Chine': -0.23, 'marge Europe': -0.08, 'ROE': -0.28, "rentabilité de l'action": -0.18, 'création de valeur': -0.1} | effet sur la demande non publié |

### salaire et budget de formation

| Option | Résultat net, M USD | Demande, points de % | Valeur, M USD | Barème, points | Détail des points | Remarque |
|---|---|---|---|---|---|---|
| 6300 / 2000 | +0 | +0.0 | +0 | +0.00 |  | effet par la rotation du personnel, non modélisé |
| 6800 / 2000 | -42 | inconnu | inconnu | -0.10 (coût seul) |  | effet par la rotation du personnel, non modélisé |
| 6300 / 3000 | -59 | inconnu | inconnu | -0.12 (coût seul) |  | effet par la rotation du personnel, non modélisé |
| 6800 / 3000 | -101 | inconnu | inconnu | -0.17 (coût seul) | {'ROE': -0.07} | effet par la rotation du personnel, non modélisé |
| 6300 / 4000 | -118 | inconnu | inconnu | -0.18 (coût seul) | {'ROE': -0.07} | effet par la rotation du personnel, non modélisé |
| 7800 / 2000 | -126 | inconnu | inconnu | -0.18 (coût seul) | {'ROE': -0.07} | effet par la rotation du personnel, non modélisé |
| 6800 / 4000 | -160 | inconnu | inconnu | -0.20 (coût seul) | {'ROE': -0.07} | effet par la rotation du personnel, non modélisé |
| 7800 / 3000 | -185 | inconnu | inconnu | -0.20 (coût seul) | {'ROE': -0.07} | effet par la rotation du personnel, non modélisé |
| 7800 / 4000 | -244 | inconnu | inconnu | -0.23 (coût seul) | {'ROE': -0.08} | effet par la rotation du personnel, non modélisé |

### Vérification du cumul des choix de l'étape D

Résultat net 21528 -> 13494 M USD ; score ESG 3.34 ; fournisseurs requis 3.0, actifs 1 ; dette à court terme nouvelle [0.0].

## Étape E — finance et impôts

Référence (avec les choix de l'étape D) : résultat net 13494 M USD, dette à court terme nouvelle [0.0], trésorerie de fin [31795762.0].

### Prix de transfert

| Champ | Valeur | Résultat net, M USD | Écart | Résultat USA / Chine / Europe | Barème, points |
|---|---|---|---|---|---|
| transfer.us.to.asia | 1.00 | 13494 | +0 | 1183 / 4667 / 7644 | +0.00 |
| transfer.us.to.asia | 1.10 | 13494 | +0 | 1183 / 4667 / 7644 | +0.00 |
| transfer.us.to.asia | 1.25 | 13494 | +0 | 1183 / 4667 / 7644 | +0.00 |
| transfer.us.to.asia | 1.50 | 13494 | +0 | 1183 / 4667 / 7644 | +0.00 |
| transfer.us.to.asia | 1.75 | 13494 | +0 | 1183 / 4667 / 7644 | +0.00 |
| transfer.us.to.asia | 2.00 | 13494 | +0 | 1183 / 4667 / 7644 | +0.00 |
| transfer.us.to.eu | 1.00 | 13494 | +0 | 1183 / 4667 / 7644 | +0.00 |
| transfer.us.to.eu | 1.10 | 13493 | -1 | 1194 / 4667 / 7633 | -0.02 |
| transfer.us.to.eu | 1.25 | 13492 | -3 | 1209 / 4667 / 7616 | -0.02 |
| transfer.us.to.eu | 1.50 | 13489 | -5 | 1234 / 4667 / 7588 | -0.02 |
| transfer.us.to.eu | 1.75 | 13487 | -8 | 1260 / 4667 / 7560 | +0.03 |
| transfer.us.to.eu | 2.00 | 13484 | -11 | 1285 / 4667 / 7531 | +0.03 |
| transfer.asia.to.us | 1.00 | 13494 | +0 | 1183 / 4667 / 7644 | +0.00 |
| transfer.asia.to.us | 1.10 | 13422 | -72 | 764 / 5014 / 7644 | -0.05 |
| transfer.asia.to.us | 1.25 | 13313 | -181 | 136 / 5533 / 7644 | -0.10 |
| transfer.asia.to.us | 1.50 | 12901 | -594 | -1143 / 6400 / 7644 | -1.03 |
| transfer.asia.to.us | 1.75 | 12453 | -1041 | -2457 / 7266 / 7644 | -3.05 |
| transfer.asia.to.us | 2.00 | 12006 | -1489 | -3771 / 8133 / 7644 | -5.28 |
| transfer.asia.to.eu | 1.00 | 13494 | +0 | 1183 / 4667 / 7644 | +0.00 |
| transfer.asia.to.eu | 1.10 | 13393 | -102 | 1183 / 5699 / 6511 | +0.70 |
| transfer.asia.to.eu | 1.25 | 13240 | -255 | 1183 / 7246 / 4811 | +1.40 |
| transfer.asia.to.eu | 1.50 | 12969 | -526 | 1183 / 9824 / 1961 | -0.38 |
| transfer.asia.to.eu | 1.75 | 12407 | -1087 | 1183 / 12403 / -1179 | -3.30 |
| transfer.asia.to.eu | 2.00 | 11310 | -2185 | 1183 / 14982 / -4855 | -7.28 |

### Dette à long terme (encours 0.0 Md USD)

| Variation, k USD | Résultat net, M USD | Dette court terme nouvelle | Trésorerie de fin |
|---|---|---|---|
| 0 | 13240 | [0.0] | [31795762.0] |

### Transfert interne cash.us.to.asia

| Montant, k USD | Résultat net, M USD | Dette court terme nouvelle |
|---|---|---|
| 2000000 | 13235 | [0.0] |
| 4000000 | 13237 | [0.0] |
| 6000000 | 13240 | [0.0] |
| 8000000 | 13242 | [0.0] |
| 10000000 | 13245 | [0.0] |

### Transfert interne cash.us.to.eu

| Montant, k USD | Résultat net, M USD | Dette court terme nouvelle |
|---|---|---|
| -15000000 | 13250 | [0.0] |
| -13000000 | 13266 | [0.0] |
| -11000000 | 13245 | [0.0] |
| -9000000 | 13223 | [0.0] |
| -7000000 | 13201 | [0.0] |

Choix de l'étape E : {'transfer.asia.to.eu': 1.25, 'cash.us.to.asia': 10000000, 'cash.us.to.eu': -13000000} ; résultat net 13266 M USD.

Dividendes : non cherchés (aucune équipe n'en a versé, effet sur le cours inconnu) ; laissés à 0.

Zone personnelle restaurée. 97 évaluations sur la plateforme.

Durée : 525 s.