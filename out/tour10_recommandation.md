# Tour 10 — décisions jouées le 20/11/2026 à 13h29 (échéance 14h00)

## Résultats du tour 9 (points recalculés par `model.points`, classement officiel non publié)

- tomobil : 126 points, 7ᵉ du tour (Vrooom Vroooom 172, Ren'Auto 170, POLRAMOS 152). Prévu : 139.
- Demande réelle 1 823 k unités pour 2 364 k prévues. Chine Électrique : 426 k pour 751 k prévues (sous le P10 de 610 k).
- Stock final 555 k (108 k Hybride, 447 k Électrique, tout en Chine), demande non servie 0.
- Points faibles : création de valeur 1, productivité 1, G 1, ROE 2, fournisseurs 2, parts de marché 2 / 3 / 3.
- Points forts : marge et coût unitaire Europe 12, marge et coût unitaire Chine 11, S 10, coût unitaire USA 10.

## Décisions du tour 10

| Levier | Décision | Raison |
|---|---|---|
| Marketing | reconduit du tour 9 | pas de recherche : le modèle a surestimé la demande de 30 % au tour 9 et il restait 30 minutes |
| Parts estimées | USA 2,7 / 2,3 ; Chine 2,8 / 3,5 ; Europe 3,4 / 1,9 % (Hybride / Électrique) | parts réelles du tour 9, marchés à +2,5 / +10 / −4,5 % |
| Production USA | Électrique 0 % (était 14,1), Hybride 12 % (était 24) | écouler le stock ; la Chine est moins chère même livrée aux USA (droits ramenés à 6 % + 800 USD) |
| Production Chine | Électrique 40,2 %, Hybride 59,8 % (usine pleine) | idem |
| R&D | 275 514 / 380 766 / 731 220 jours-homme (remise à zéro en début de tour) | personnel payé de toute façon |
| Certification | Bronze (8 M USD), seul niveau offert | +2 points |
| Événements | options sans coût gardées (fournisseur, batteries) | effet des autres options inconnu |
| Finance, RH, achats, ESG, prix de transfert | inchangés | non retestés faute de temps |

## Vérification sur le prévisionnel (demande attendue : 992 k Hybride, 898 k Électrique)

- Stock final 83 k Hybride + 52 k Électrique, demande non servie 0.
- Résultat net 27 980 M USD, découvert 0, trésorerie USA 46,1 / Chine 84,1 / Europe 13,6 Md USD, ROE 20,0 %.
- Enregistré pour l'équipe : colonne équipe 27 980 367 = zone personnelle.

## Non fait

- Recherche marketing, étapes D et E, test d'un dividende de dernier tour (rentabilité de l'action).

## Complément de 13h35 : garde-fous et fournisseurs

Décisions de l'équipe réenregistrées à 13h33 : colonne équipe 27 030 691 = zone personnelle. Sauvegarde : `data/decisions_tour10b_avant_enregistrement.txt`.

| Point examiné | Résultat | Décision |
|---|---|---|
| Fournisseur Innovation Réinventée | Au tour 9, les trois équipes qui l'ont retiré (Ren'Auto, IronHorse, Vrooom Vroooom) ont un score fournisseurs de 9,50 (10 points) contre 8,34 (2 points) pour les jeux à trois, une qualité de 5,00 contre 4,17 et une note durable de 4,50 contre 4,17. Prévisionnel : résultat net −950 M USD, composant 9 750 au lieu de 8 750 USD, marges −1,6 / −1,2 / −1,3 point (USA / Chine / Europe), découvert 0, 2 fournisseurs actifs pour 2 requis (`out/tour10_test_fournisseurs.json`). | **retiré** : +8 points sur le critère si les concurrents ne bougent pas, coût estimé de 1 à 4 points (résultat, marges USA et Chine) ; reste positif si d'autres équipes font de même |
| Plan de production | Stocks du tour 9 : 0 / 0 / 312 / 365 / 555 (nous) / 616. Un stock final de 0 à 311 k vaut 10 points ; 135 k prévus, non servi 0. La baisse de 8 % annoncée en Europe (−4,5 % saisi) ajoute environ 18 k de stock. | inchangé |
| Politiques « Partenariat stratégique » et « Collaboration syndicale » (jouées par les 4 meilleures en G) | refusées par la plateforme : score ESG 2,96 pour 3,0 requis (`out/tour10_test_politiques.json`) | impossible |
| « Accent sur le bien-être des employés » | refusée : plus de jours-homme disponibles ; effet appris −0,65 % de demande | écartée |
| Dividende de dernier tour | non testable ; seule observation défavorable (POLRAMOS, tour 5) | écarté |

Non fait : recherche marketing, étape E (prix de transfert), simulation de l'effet du retrait du fournisseur sur la demande (attendu positif : qualité et impact G en hausse, 135 k de stock pour l'absorber).

## Révision de 13h43 (remplace le marketing et la production ci-dessus)

Recherche rapide (`tour_final.py 10 --n 12 --rapide`, six comportements de concurrents, entrées du tour 9 avec taux de change et croissance à jour) : reconduit 134,4 points attendus, ±6 % 137,9.

| Produit | Prix | Équipements | Publicité, M USD |
|---|---|---|---|
| Hybride USA | 36 500 | 8 | 700 |
| Électrique USA | 53 800 | 8 | 950 |
| Hybride Chine | 207 000 RMB | 10 | 650 |
| Électrique Chine | 311 000 RMB | 9 | 1 000 |
| Hybride Europe | 37 400 EUR | 7 | 650 |
| Électrique Europe | 52 800 EUR | 7 | 900 |

- Équipements gardés à leur niveau (la recherche proposait 7 / 8 / 8 / 9 / 5 / 9) : les conditions annoncent encore une demande d'équipements en hausse.
- Production : USA Électrique 6 %, Hybride 15 % ; Chine inchangée (40,2 / 59,8 %).
- Parts estimées : 2,6 / 2,2 ; 3,0 / 4,0 ; 3,8 / 2,2 %.
- Prévisionnel : stock final 85 k Hybride + 76 k Électrique, non servi 0, découvert 0, résultat net 27 079 M USD.
- Enregistré pour l'équipe à 13h43 : colonne équipe 27 079 184 = zone personnelle.

## Révision de 13h50 (remplace celle de 13h43)

Rejeu des tours 7 à 9 (`python3 objectif.py --tour N`, décisions cherchées avec les données d'avant le tour, points évalués avec les concurrents réels) :

| Tour | joué | points ±6 % | points ±15 % | marge ±6 % | marge ±15 % |
|---|---|---|---|---|---|
| 7 | 153 | 157 | 163 | 152 | 149 |
| 8 | 130 | 126 | 135 | 122 | 126 |
| 9 | 131 | 131 | 141 | 130 | 135 |

La recherche en points à ±15 % est la meilleure sur les trois tours. Point ±15 % joué au tour 10 (prix et publicité ; équipements gardés) :

| Produit | Prix | Équipements | Publicité, M USD |
|---|---|---|---|
| Hybride USA | 36 500 | 8 | 850 |
| Électrique USA | 53 200 | 8 | 1 150 |
| Hybride Chine | 192 000 RMB | 10 | 798 |
| Électrique Chine | 282 000 RMB | 9 | 1 232 |
| Hybride Europe | 40 000 EUR | 7 | 750 |
| Électrique Europe | 46 700 EUR | 7 | 1 150 |

- Production : USA Électrique 12 %, Hybride 26 % ; Chine 50 / 50 %.
- Parts estimées : 2,6 / 2,3 ; 3,5 / 5,0 ; 3,6 / 3,0 %.
- Prévisionnel : stock final 112 k Hybride + 88 k Électrique, non servi 0, découvert 0, résultat net 26 269 M USD.
- Fournisseurs et politiques ont été changés à 13h33 (`out/tour10_test_fournisseurs.json`, `out/tour10_test_politiques.json`) : repris tels quels.
