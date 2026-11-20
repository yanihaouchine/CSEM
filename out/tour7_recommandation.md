# Tour 7 — décisions prises (équipe tomobil)

Enregistrées pour l'équipe le 20/11 à 8h48 (`python3 -m cesim.save_team tour7`). Prévisionnel de la plateforme : résultat net 15 517 M USD, contre 12 452 M USD avec les décisions du tour 6 reconduites. Sauvegarde avant modification : `data/decisions_tour7_avant.txt`, `data/zone_tour7_depart.json`.

## Résultats du tour 6 (présentés avant toute décision)

- Résultat net 16 989 M USD (prévisionnel 17 752), bénéfice par action 10,4 USD, cours 149,4 → 183,9 USD, retour cumulé 24,8 %, rang 7 → 4.
- Demande 2 335 k unités pour 2 257 k prévues (+3,5 %), tout vendu, aucune rupture. Stocks finaux : 31 k Thermique, 130 k Hybride.
- Leviers ESG joués au tour 6 : l'impact « formation » passe de −3,0 à +6,6 points de demande, le score social de 2,32 à 3,47, la somme de nos impacts ESG de −7,9 % à +3,2 % (9ᵉ → 5ᵉ). Le score cumulé passe de 2,72 à 3,10.
- Marchés : le Thermique a perdu 34 % (USA), 40 % (Chine), 50 % (Europe), à peu près comme sa couverture (−35 à −39 %). Électrique : Chine 282 → 1 429 k, Europe 885 → 1 139 k (7 vendeurs au lieu de 2). Hydrogène : 1 153 k aux USA pour 2 vendeurs.
- Le rejeu chiffré du simulateur (`backtest.py`) n'a pas été relancé ce tour : il prend plus de 20 minutes depuis l'arrivée des nouvelles technologies, et le tour ne durait que 87 minutes.

## Nouveautés du tour 7 (relevé automatique)

- Couverture du Thermique à 0 dans les trois zones dès ce tour ; celle de l'Hybride tombe à 57 % (USA), 55 % (Chine), 55 % (Europe). Conditions de marché : « c'est la fin des véhicules thermiques et une réduction forte de la demande de véhicules hybrides ».
- Certification Bronze proposée (score 3,10 pour 2,75 requis).
- Nouvel événement « L'approvisionnement durable » (3 options) ; « prêt écologique » et « dilemme de la qualité » ont disparu.
- Les options de « coopération avancée » ne sont plus refusées (score d'au moins 3,0).

## Décisions

| Levier | Avant | Après | Test |
|---|---|---|---|
| Modèle 1, trois zones | Thermique | Électrique | couverture du Thermique à 0 : aucun marché |
| Licence Électrique | 2 équipements | +5, soit 7 | 1 750 M USD ; les vendeurs à 10 équipements font les meilleures marges du tour 6 |
| Prix Électrique | — | 55 000 USD, 440 000 RMB, 55 000 EUR | médianes du tour 6 : 415 000 RMB et 50 000 EUR ; coût unitaire lu : 37 494 USD, 249 837 RMB, 32 276 EUR |
| Publicité Électrique | — | 600 / 500 / 600 M USD | médiane des vendeurs du tour 6 : 500 |
| Hybride | prix et équipements du tour 6 | inchangés | non optimisé : le simulateur de stratégie ne sait pas encore traiter une gamme sans Thermique |
| Production | Thermique + Hybride, sous-traitance 541 k | Chine : Électrique 58,1 % (690 k) et Hybride 35,4 % (421 k) ; USA : Hybride 12,9 % (221 k) ; aucune sous-traitance | voir le tableau ci-dessous |
| R&D | 0 affecté | Hydrogène 1 280 700, Électrique 68 000, Hybride 38 800 jours-homme | la page R&D confirme que les trois étapes en cours sont couvertes ; 0 jour libre |
| Certification | aucune | Bronze | 8 M USD ; environ +11 % d'attraction d'après le moteur |
| Approvisionnement durable | participation partielle (présélectionnée) | engagement total | +882 M USD par rapport à l'option présélectionnée ; notoriété « modérée » au lieu de « mineure » ; capacité interne −5 % |
| Amélioration de processus | — | eau | −153 M USD, pas de perte de capacité |

Inchangés : priorité de formation « éthique », mentorat, salaire 6 300 USD, engagement de recyclabilité, 3 fournisseurs, énergie renouvelable 100 %, prix de transfert 1,00, transferts internes, pas de dette, pas de dividende.

### Volumes

Hypothèses de demande (aucune simulation fiable n'existe pour ce changement de régime) :
- Hybride : cellules du tour 6 multipliées par le rapport des couvertures (0,59 à 0,71), plus 10 % de report du Thermique, à parts de marché constantes : 175 k (USA), 213 k (Chine), 312 k (Europe), soit 700 k.
- Électrique : 140 k (USA), 220 k (Chine), 190 k (Europe), soit 550 k. Ordre de grandeur : cellules en hausse avec la couverture et le report du Thermique, une dizaine de vendeurs par zone, 7 à 8 % de part.

Trois niveaux de production comparés sur la plateforme, résultat net en M USD :

| Production | Ventes −25 % | Central | Ventes +25 % | Espérance (25 / 50 / 25) |
|---|---|---|---|---|
| Électrique 640 k, Hybride 592 k | 10 038 | 15 699 | 18 854 | 15 072 |
| Électrique 690 k, Hybride 640 k (retenu) | 9 855 | 15 517 | 20 138 | 15 257 |
| Électrique 740 k, Hybride 690 k | 9 350 | 14 859 | 19 826 | 14 723 |

Avec le niveau retenu : ventes −25 %, aucune dette à court terme, stocks 252 k Hybride et 280 k Électrique (revendables au tour 8) ; ventes +25 %, 106 k Hybride non servis, Électrique servi.

## Leviers examinés et non retenus

- Partenariat stratégique : −2 041 M USD pour environ +5 points de demande (soit +1 050 M USD). Non.
- Améliorations « énergie » (−875 M USD) et « CO2 » (−1 720 M USD) : elles retirent 15 % et 20 % de capacité à une usine de Chine déjà chargée à 93 %.
- Batteries : sous-traiter −1 003 M USD ; co-développer refusé (plus de jours-homme disponibles).
- Recyclabilité « cycle fermé » : −991 M USD.
- Hybride Europe à 8 équipements : −197 M USD de coût pour +3,7 % de demande estimés, gain net voisin de zéro.
- Publicité Électrique à 1 000 M USD par zone : −1 027 M USD à demande égale, effet inconnu sur cette technologie.
- Licence Hydrogène : 9 050 à 10 700 M USD. La R&D interne l'obtient ce tour pour 1 280 700 jours-homme déjà payés ; l'Hydrogène sera donc disponible au tour 8.
- Approvisionnement durable, « continuer l'actuel » : +90 M USD seulement par rapport à l'engagement total, sans gain de notoriété.

## Nouveauté apparue en cours de tour (relevé de 9h50)

- **« Ciblage de la stratégie marketing »**, un menu par produit sur les pages Marketing (`areaN.techK.mstrat`) : Équilibré (présélectionné), Prix bas, Équipements, Image de marque, Développement durable. Aide de la plateforme : « vous obtiendrez un effet plus important sur le segment de consommateurs ciblé. L'effet peut s'avérer négatif si vos décisions ne sont pas en accord avec la stratégie choisie. La comparaison sera faite avec les offres des concurrents séparément pour chaque segment de marché et type de technologie. » Le champ n'existait pas au relevé de 8h33.
- Notre position face aux concurrents du tour 6, par produit : prix dans le tiers haut (25 à 50 % des concurrents plus chers que nous), équipements et publicité au milieu (33 à 62 % en ont moins). Impact ESG lié aux décisions : 3ᵉ sur 12, mais 9 équipes sont déjà certifiées. Nous ne dominons nettement sur aucun axe.
- **Décision : « Équilibré » gardé sur les 6 produits.** Aucune équipe n'a encore joué ce levier, son effet n'est pas mesurable, et un ciblage mal aligné est pénalisé. Les résultats du tour 7 diront ce que les ciblages ont rapporté aux équipes qui les ont pris (si le rapport publie le choix) : à tester au tour 8.

## Risques

- La demande d'Électrique est estimée à la main : aux USA aucun vendeur n'existait au tour 6. L'écart peut dépasser ±40 %.
- Le prix de l'Hybride n'a pas été réoptimisé alors que son marché se contracte.
- 31 k Thermique restent en stock sans marché.
- Tous les concurrents doivent remplacer leur Thermique en même temps : le nombre de vendeurs d'Électrique et d'Hydrogène au tour 7 est inconnu.

## Pour le tour 8

- Hydrogène disponible (technologie + 1 équipement) : couverture 64 % aux USA et 70 % en Europe au tour 8, contre 34 % et 65 % pour l'Électrique. Choisir les deux modèles de chaque zone parmi Hybride, Électrique, Hydrogène.
- Généraliser `strategy.Scenarios` aux gammes sans Thermique pour retrouver une recherche marketing testée.
