# Tour 9 — décisions jouées (20/11, enregistrées pour l'équipe à 12h15, échéance 13h00)

## Retour du tour 8
- 130 points (5ᵉ du tour à égalité ; POLRAMOS 167, Ren'Auto 164), contre 152 au tour 7 et 168 prévus.
- Pertes par rapport au tour 7 : stocks −5 (473 k), part de marché Europe −5 (Électrique à 58 300 EUR : 236 k de demande contre 354 k), rentabilité de l'action −5, ROE −3, gouvernance −3, coût unitaire Chine −3.
- Contre-épreuve (`python3 objectif.py --tour 8`, concurrents réels) : marge ±6 % 122 points, marge ±15 % 126, points ±6 % 126, joué 130, points ±15 % 135. L'objectif en points n'est pas en cause ; la prévision des points l'est (38 points d'écart).
- Rejeu aveugle du simulateur au tour 8 : 11,4 % d'erreur de volume, 18,2 % pour la chaîne complète. Notre demande avait été surestimée de 8 %.

## Nouveautés du tour 9
| Nouveauté | Traitement |
|---|---|
| Certification retombée à « Pas de certification » ; seul le Bronze est offert (score cumulé 3,21) | Bronze repris : +2 points pour 6 M USD |
| 1 387 500 jours-homme de R&D inoccupés | tous affectés (Hybride 275 514, Électrique 380 766, Hydrogène 731 220) : coût nul au prévisionnel, un équipement de plus par technologie au tour 10 |
| Rachat d'actions (`share.buyback`, 247,80 USD) | écarté : 150 M d'actions créent 15 Md USD de découvert en Europe (−9 points) ; jamais joué, et la loi du cours (fonds propres par action) annonce une baisse du cours |
| Événement « conflit avec le fournisseur » | « poursuivre le partenariat » gardé : les deux autres options coûtent 1,4 et 0,8 Md USD (−1,6 et −1,1 point) pour un effet sur la demande non publié |
| Améliorations de processus affichées à coût nul | faux une fois cochées : −3,7 Md USD (−2,5 à −2,8 points) ; écartées à un tour de la fin |
| Droits USA → Chine 30 %, USA → Europe 15 % ; RMB 0,1387, EUR 1,2181 | dans `data/tour_9_inputs.json` ; l'Hybride pour l'Europe passe en partie par l'usine de Chine |
| Conditions : équipements plus demandés, Hydrogène en forte hausse | équipements jamais réduits (la recherche voulait 7 et 5 sur l'Hybride USA et Europe : refusé, coût 0,4 point attendu) ; Hydrogène non lancé (1 équipement contre 7,9 en moyenne chez les vendeurs) |
| Liquidation du stock de Thermique (31 k en Chine) | faite : −51 M USD, 31 k de stock noté en moins |

## Décisions
| Produit | Tour 8 | Tour 9 (prix, équipements, publicité M USD) | Demande attendue (P10 – P90), k |
|---|---|---|---|
| Hybride USA | 38 500, 8, 500 | 36 300, 8, 600 | 299 (239 – 353) |
| Électrique USA | 51 800, 8, 700 | 51 100, 8, 800 | 296 (108 – 594) |
| Hybride Chine | 234 000 RMB, 9, 450 | 220 000, 10, 550 | 446 (340 – 603) |
| Électrique Chine | 352 000 RMB, 8, 700 | 331 000, 9, 850 | 751 (610 – 855) |
| Hybride Europe | 37 500 EUR, 7, 500 | 37 900, 7, 550 | 322 (112 – 622) |
| Électrique Europe | 58 300 EUR, 7, 700 | 54 900, 7, 800 | 250 (204 – 297) |

- Point ±6 % de la recherche en points (`tour_final.py 9 --rapide`), plafond `rayon_max` inchangé. Points attendus : 134,7 reconduit, 139,1 retenu (part Chine +2,7, création de valeur +1,4, part USA +0,8 ; marge USA −0,5). Mondes défavorables : +1,6 Md USD de marge dans le pire des trois.
- Production : quantile 60 % de la demande simulée (70 % donnait le même total à 0,06 point près ; 60 % retenu parce que la demande du tour 8 avait été surestimée). Chine 60,2 % Électrique et 39,8 % Hybride (usine pleine), USA 14,1 % et 24,0 %, pas de sous-traitance. Les 442 k unités en stock sont écoulées d'abord. Prévisionnel : aucun non servi, 8 k de stock final à la demande moyenne.
- Finance : transfert Europe → USA ramené de 11 à 7 Md USD. Trésorerie de fin prévue USA 40,5 / Chine 74,4 / Europe 11,0 Md USD ; à 11 Md l'Europe tombait en découvert dans les scénarios de ventes basses (+0,65 point, coût 23 M USD). Premier usage du bilan par scénario (`Bareme.bilan`).
- Inchangés après examen : fournisseurs (3 actifs pour 2 requis), politiques de travail, priorités de formation (formation de base : +2,6 points de productivité attendus mais environ −3 en sociétal), salaire et budget (aucun effet mesuré sur la productivité), prix de transfert à 1,00, dette nulle, pas de dividende, énergie renouvelable 100 %.
- Non refait faute de temps : étape D complète sur la plateforme (fournisseurs, politiques, service client), étape E pour les prix de transfert.

Résultat net au prévisionnel : 29 296 M USD (33 419 avec les parts estimées du tour 8, trop hautes). Colonne de l'équipe vérifiée : 29 296 024, identique à la zone personnelle.
