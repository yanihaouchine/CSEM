# Tour 6 — décisions prises (équipe tomobil)

Enregistrées pour l'équipe le 19/11 à 16h30 (`python3 -m cesim.save_team tour6`). Prévisionnel de la plateforme : résultat net 17 752 M USD, contre 15 515 M USD avec les décisions du tour 5 reconduites. Sauvegarde avant modification : `data/decisions_tour6_avant.txt`.

## Rejeu du tour 5 (présenté avant toute décision)

- Résultat : 18 201 M USD de résultat net (prévisionnel 16 410), bénéfice par action 11,2 USD (2ᵉ du tour), cours 96,7 → 149,4 USD, retour cumulé 18,8 % → 25,2 %, rang 10 → 7.
- Notre demande : 2 378 k unités pour 2 221 k prévues (+7 %). Europe Thermique 570 k pour 464 k prévus (au-dessus de la fourchette haute, 530 k). Pas de rupture en Hybride (871 k demandés, 928 k offerts) ; 10 k Thermique non servis aux USA.
- Taille des marchés, prévision écrite avant résultats (concurrents au statu quo) : erreur par cellule 9,7 % (extrapolation), 15,4 % (couverture), 11,4 % (mixte). Le nouvel étage n'a pas fait mieux que l'ancien ce tour-ci. L'Europe a grossi de 15,8 % pour −3 % annoncés ; aucune méthode ne l'a vu.

## Nouveautés du tour 6 (relevé automatique)

- Nouvel événement « Le dilemme de la qualité » (3 options). L'événement « transparence » a disparu.
- Nouveau champ : émission d'actions (page Finance). Laissé à 0.
- La licence Hydrogène peut s'acheter à une autre équipe.
- Couverture du Thermique abaissée de 20 points à partir de ce tour (USA 56 %, Chine 54 %, Europe 46 %).
- Sous-traitance devenue plus chère que nos usines (Hybride Chine 21 666 USD contre 17 922 en interne).
- Jours-homme de R&D remis à zéro : 1 387 500 non affectés dans les décisions reconduites.

## Décisions

| Levier | Avant | Après | Test |
|---|---|---|---|
| Prix | 22 000 USD, 39 700 USD, 139 000 RMB, 243 000 RMB, 25 500 EUR, 38 800 EUR | 22 600, 40 800, 143 000, 248 000, 26 200, 39 900 | seul point de la frontière qui reste gagnant si les clients sont 30 % plus sensibles au prix |
| Équipements Hybride | 7 / 7 / 7 | 8 (USA) / 8 (Chine) / 7 (Europe) | idem |
| Publicité, M USD | 1 100 / 400 / 650 / 350 / 1 050 / 400 | 1 000 / 450 / 650 / 400 / 1 150 / 450 | idem |
| Production | Chine 87 % T + 9 % H, USA 12 % T + 5 % H, sous-traitance H 167 + 484 | Chine 76,6 % T + 20,3 % H, USA 21,4 % T + 16,8 % H, sous-traitance H Chine 541, USA 0 | programme linéaire ; prévisionnel : aucune demande non servie |
| R&D | 0 affecté | Électrique 597 137, Hybride 274 707, Hydrogène 515 656 jours-homme | prévisionnel : 0 jour libre |
| Priorités de formation | base + non-discrimination | éthique seule | coût nul ; impact observé +11,7 / +9,7 / +8,0 points de demande chez les équipes qui l'ont jouée (3 tours), nous étions à −3,0 |
| Quotas de direction | recrutement diversifié | programmes de mentorat | coût nul ; +1,0 point (4 observations) |
| Amélioration de processus | aucune | eau | −104 M USD ; +5 points estimés (écarts observés 8 à 10) |
| Recyclabilité | cycle de vie | cycle de vie + engagement | coût nul ; +1,5 point (7 observations) |
| Salaire / formation R&D | 5 800 / 1 400 USD | 6 300 / 2 000 USD | −77 M USD ; les équipes à 6 000 USD et plus ont un impact « rotation » positif (+0,6 à +1,9), nous −2,2 |
| Dette long terme | 4,4 Md USD | remboursée | +18 M USD ; trésorerie maison mère 17,8 Md USD |

Matrice de gains de la frontière marketing et détail : `out/tour6_recherche_AB.md`. Balayage des leviers sur la plateforme : `out/tour6_recherche_DE.log`, `out/tour6_etape2.json`.

### Frontière marketing (gain par rapport aux décisions reconduites, M USD)

| Zone de confiance | Moteur tel quel | Clients 30 % plus sensibles au prix | Marchés 15 % plus petits |
|---|---|---|---|
| ±3 % | +781 | +54 | +631 |
| ±3 % sans retrait d'équipements Thermique (retenu) | +699 | +25 | +565 |
| ±6 % | +1 147 | −75 | +917 |
| ±10 % | +1 592 | −196 | +1 244 |
| ±30 % | +2 947 | −262 | +2 195 |
| bornes larges (publicité 11 900 M USD) | +9 084 | +316 | +6 580 |

Le point « bornes larges » n'est jamais joué : il met la publicité au maximum sur cinq produits, là où le moteur n'a aucune observation.

## Hypothèse défavorable

Ventes 25 % sous la prévision, production inchangée : résultat net 11 586 M USD, aucune dette à court terme nouvelle, trésorerie maison mère 16,7 Md USD, stocks finaux 453 k Thermique et 353 k Hybride. Le stock de Thermique est le risque principal si l'interdiction annoncée pour le tour 7 bloque réellement la vente.

## Leviers examinés et non retenus

- Améliorations « énergie » (−1 169 M USD) et « CO2 » (−2 164 M USD) : elles retirent 15 % et 20 % de capacité ce tour et créent de la demande non servie avec ce plan de production.
- Recyclabilité « cycle fermé » : −629 M USD pour +3,0 points, moins bon que l'engagement seul.
- « Partenariat stratégique », « collaboration syndicale », co-développement (qualité, batteries) : refusés par la plateforme tant que le score ESG est sous 3,0 (le nôtre : 2,72 cumulé).
- Dilemme de la qualité, « fournisseur alternatif mais douteux » : +72 M USD, effet d'image inconnu. Non pris.
- Batteries « sous-traiter » : −804 M USD, bénéfice inconnu. Non pris.
- Énergie renouvelable sous 100 % : +75 à +150 M USD, −5 à −11 points de demande. Non.
- « Conformité minimale » : +1 192 M USD, effet d'image inconnu (la « conformité standard » coûte déjà 4,4 points). Non.
- Certification : aucune option proposée (score 2,72 pour 2,75 requis).
- Émission d'actions, dividende : 0.

## Non fait ce tour, faute de temps

- Fournisseurs (32 combinaisons) : le balayage a planté sur ce groupe ; les 3 fournisseurs actuels sont gardés (note de développement durable 4,17, la meilleure observée).
- Entrée sur l'Électrique : voir la note ci-dessous.

## Finance et impôts, balayés après l'enregistrement (16h38)

- Prix de transfert : 1,00 partout est le meilleur choix. Chine → Europe à 1,25 coûte 230 M USD, à 2,00 coûte 1 004 M USD ; USA → Europe à 2,00 coûte 94 M USD ; les deux autres sont sans effet.
- Dette : le remboursement complet (déjà pris) donne 17 752 M USD, contre 17 734 M USD sans remboursement.
- Transferts internes : envoyer 2 Md USD de plus en Chine rapporte 6 M USD, retirer 2 Md USD de plus d'Europe rapporte 18 M USD (la trésorerie rapporte 4,2 % en Chine, 3,2 % aux USA, 1,0 % en Europe). Non pris : le gain est de 0,1 % du résultat et le calculateur ne lit pas encore la trésorerie de la filiale Europe, donc le test « ventes −25 % sans découvert en Europe » n'a pas pu être fait.

## Entrée sur l'Électrique : étudiée, non prise ce tour

- Constat du tour 5 : 885 k unités d'Électrique en Europe pour 2 vendeurs ; POLRAMOS y gagne 20,8 Md USD de marge de contribution (333 k unités à 84 000 EUR, 10 équipements), MO'THOR 8,9 Md USD (552 k à 45 000 EUR, 3 équipements).
- Notre situation : technologie possédée, 2 équipements (licences possibles jusqu'à +5), aucune ligne de production en Électrique. Le modèle 1 ou 2 d'une zone peut passer en Électrique ; son marketing repart alors de zéro.
- Pourquoi pas ce tour : il faudrait retirer le Thermique ou l'Hybride d'Europe (7,95 et 7,27 Md USD de marge de contribution au tour 5), reconvertir une ligne d'usine, et le simulateur n'a que deux observations de demande d'Électrique en Europe. Décision non testable dans le temps restant.
- Pour le tour 7 : la R&D Électrique est financée ce tour (597 137 jours-homme, un équipement de plus). À étudier en premier dès les résultats : coût unitaire d'une ligne Électrique (à lire sur la plateforme), nombre de concurrents entrés en Europe au tour 6, prix tenus.

## Second passage de l'optimiseur (16h47 à 16h52), décisions confirmées et ré-enregistrées

- Marketing recherché à nouveau en tenant compte du gain ESG attendu (+8 % d'attraction, la moitié des estimations) : aucun point ne bat les décisions enregistrées de plus de 100 M USD dans le pire des trois mondes (±3 % : +118 / +18 / +88 M USD ; ±6 % : +542 / −173 / +395 ; ±10 % : +1 043 / −301 / +794). Décisions gardées.
- Fournisseurs : les 15 autres combinaisons d'au moins 3 fournisseurs ont été évaluées sur la plateforme. Toutes économisent sur les composants (jusqu'à +1 436 M USD) mais perdent 3 à 23 points de demande par la note moyenne ; aucune ne bat la combinaison actuelle (la plus proche : −163 M USD).
- Production : avec le gain ESG, la demande simulée moyenne (Thermique 1 309 k, Hybride 1 149 k) est au niveau de l'offre planifiée (1 342 k et 1 151 k). Produire 104 k Hybride de plus a été chiffré : gain espéré d'environ +40 M USD, parce qu'il faut déplacer du Thermique vers l'usine USA (+290 M USD de transport). Non pris. Le risque de ce tour est donc une rupture en Hybride si les leviers ESG donnent tout leur effet.
- Ré-enregistrement d'équipe à 16h53 : équipe et zone personnelle à 17 751 772 k USD.
