# Tour 8 — alignement du simulateur sur le tour 7 et nouveautés (20/11, 10h17)

Travail sur le simulateur seulement. Les décisions du tour 8 sont cherchées à part (`data/tour_8_inputs.json`, `tour_final.py`, `optimise_tout.py`, fiche `out/tour8_recommandation.md`) : rien n'a été saisi sur la plateforme ici.

## 1. Rejeu du tour 7 (avant toute recommandation)

| Mesure | Tour 6 | Tour 7 avant recalage | Tour 7 après |
|---|---|---|---|
| Répartition entre équipes, aveugle | 6,9 % | 12,9 % | **7,2 %** |
| Chaîne complète (taille des marchés comprise) | 22,6 % | 31,0 % | 26,5 % |
| Points de part de marché, écart moyen prévu / réel (36 cas) | 1,56 | 1,28 | 1,06 |
| Taille des cellules, méthode « mixte » | 20,8 % | 29,3 % (avec l'essai `LIVE_LOGIT`) | 24,5 % |

Prévision de notre demande enregistrée avant les résultats (`out/tour7_prevision_avant_resultats.json`) : erreur de la médiane 30 à 35 % avec 4 à 10 entrants supposés, 67 à 70 % sans entrant ; réel dans P10-P90 pour 2 à 4 produits sur 6. Réel : 1 734 k de demande pour 1 250 k prévus à la main ; 271 k non servis (Hybride USA 92, Hybride Chine 88, Électrique USA 92).

Classement de l'année 7 : 149 points, 3ᵉ du tour (Ren'Auto 202, POLRAMOS 152). Points perdus : parts de marché USA et Asie (2 et 2 : nous n'avons pas servi la demande), score fournisseurs (1), productivité (2), création de valeur (4). Aucun critère nouveau.

## 2. Ce que le tour 7 a appris

- **Le total d'une zone a tenu quand le Thermique a disparu** : +10,2 % (USA), +9,6 % (Chine), +4,7 % (Europe). Toute sa demande s'est reportée, et au-delà. L'Hybride n'a pas suivi sa couverture : couverture ×0,59, demande ×1,21 (USA), ×1,01 (Chine) ; ×0,71 et ×0,81 en Europe. La règle « proportionnelle à la couverture » est infirmée pour l'Hybride.
- Cellules du tour 7, k unités (vendeurs) : Hydrogène USA 3 998 (8), Europe 2 087 (6), Chine 293 (1) ; Électrique Chine 5 300 (11), Europe 4 510 (9), USA 1 119 (4) ; Hybride 5 040 / 4 114 / 3 859.
- Méthodes de taille de marché au tour 7 : couverture (partage d'un total de zone) 17,4 %, directe 39,5 %, tendance 47 %. Sur les tours 2 à 7 aucune pondération ne domine (14,8 à 16 % en moyenne) : « mixte » reste la valeur par défaut.
- **Les impacts ESG sont publiés à zéro depuis le tour 7, mais l'effet existe toujours.** Rejeu aveugle : 12,3 % avec un impact nul, 8,0 % avec celui du tour 6, 7,7 % avec un impact déduit des scores E, S, G, 7,2 % avec la moyenne des deux. `panel2.esg_hidden` le reconstitue.
- **Ciblage de la stratégie marketing** (publié par produit) : 28 produits « équilibré », 16 « équipements », 15 « prix bas », 12 « développement durable », aucun « image de marque ». Résidu aveugle une fois l'ESG reconstitué : développement durable +3 à +8 %, prix bas −2 à −4 %, équipements −4 %, équilibré 0 à +2 % (écart-type 7 à 17 %). Effet faible, non distinguable du bruit ; « équilibré » n'a rien coûté. Seul « développement durable » chez les équipes au score ESG élevé semble payer.
- Concurrents : au tour 7, un concurrent avec une place libre a lancé une technologie qu'il vendait déjà ailleurs 62 fois sur 100, une technologie jamais vendue 48 fois sur 100. Au tour 8 tous ont deux modèles vivants : seuls des échanges restent possibles (15 % observés, 13 occasions).

## 3. Nouveautés du tour 8

| Nouveauté | Ce qu'elle permet | Traitement |
|---|---|---|
| Hydrogène dans les menus (modèles et lignes) | 3 technologies possédées ; couverture tour 8 : USA 64 %, Europe 70 %, Chine 26 % | `techs` des entrées ; `offre.py --tour 8` compare les paires |
| Page « Service client » (`marketingaftersales`) | garantie 1 / 2 / 3 / 5 ans : effet positif annoncé sur la demande, coût en % du chiffre d'affaires (637 M USD à 1 an) ; collecte, protection, partage des données : points Social relatifs à la moyenne des équipes (protection avancée 5 points contre 2 ; collecte minimum 5 ; ne pas partager 6) | classé dans `leviers.py` (étape D) ; effet jamais observé : coût lu sur la plateforme, pas d'effet dans le moteur |
| Liquidation des stocks (`inv.liquid.*`) | 31 k Thermique en Chine, 7 614 USD l'unité (236 M USD) ; lot entier, seulement sans vente | classé (étape C) ; supprime 31 k du critère « stocks » |
| Événement « prêt écologique » revenu (3 options) | taux réduit jusqu'au tour 10 contre un engagement ESG | classé ; nous n'avons pas de dette |
| Certification Argent (score cumulé 3,34 pour 3,25) | 24 M USD ; +2 points au barème | à prendre |
| Document « Rachat d'actions » | rappel du levier `share.issue` | déjà classé (étape E) |
| Conditions de marché | croissance USA +2 à 3 %, Chine autour de +10 %, Europe −4 à −5 % ; RMB 0,1321 | dans `data/tour_8_inputs.json` |
| Licences | Hybride +1 (9 possédés), Électrique +2 (8 possédés), Hydrogène +1 à +5 | étape F |

## 4. Modifications du simulateur

| Fichier | Changement | Test |
|---|---|---|
| `model/panel2.py` | `esg_hidden` : impact ESG reconstitué quand il est publié à zéro | tour 7 aveugle 12,9 → 7,2 % ; tours 2 à 6 inchangés |
| `model/sim.py` | `MIN_OBS` 12 → 30 (repli sur l'Hybride de la zone) ; `team_zone` | Électrique Chine au tour 7 : 15,1 → 11,2 % ; parts publiées retrouvées à 0,011 point |
| `model/market.py` | `REPORT` (0) et `LIVE_LOGIT` (désactivé) : essais non retenus ; `appeal_table` sans Thermique | prévisions identiques à avant sur les tours 2 à 6 |
| `model/rivals.py`, `strategy.py` | `changement_de_gamme`, clé `gamme_concurrents` | tour 7 en aveugle : vendeurs prévus 7 / 3 / 4 pour 10 / 6 / 8 réels (Électrique Chine, Hydrogène Europe, Hydrogène USA) ; tour 8 : change notre demande de −4 à +6 %, donc non activé |
| `cesim/inputs.py` | annonces (forum, tâches, Manuels), page `marketingaftersales` | relevés des tours 7 et 8 |
| `leviers.py` | ciblage marketing, liquidation, service client | `python3 leviers.py 8` : aucun champ non classé |
| `backtest.py` | points de part de marché prévus contre réels | 38 s pour tout le rejeu |

## 5. Limites

- La taille des marchés reste le maillon faible (24,5 % par cellule au tour 7). Une prévision de demande pour le tour 8 vaut ±30 %.
- Ni le ciblage marketing, ni la garantie, ni les données clients ne sont dans le moteur : aucune observation pour les deux derniers.
- Le coût et le nombre d'équipements de notre Hydrogène n'ont pas été lus ici (une recherche occupait la zone personnelle).
