# Tour 5 — recommandation (équipe tomobil)

Zone personnelle, état au 19/11 à 14h53. Enregistrement comme décisions de l'équipe prévu à 15h30.

## Ce qui a changé depuis la première version
- Interdiction du Thermique pur à partir de 2035 (message de l'instructeur) : il reste ce tour et le suivant. La part de marché laissée compte moins ; la R&D quitte le Thermique.
- Certification Bronze impossible ce tour : score ESG cumulé 2,72 pour 2,75 requis. La demande simulée baisse d'environ 10 %.
- Salaire R&D 5 300 -> 5 800 USD et formation 700 -> 1 400 USD par mois : notre score social (2,26) est le plus bas des 12 équipes. Coût : 83 M USD.

## Marketing
| Zone | Tech | Prix (tour 4 -> tour 5) | Équipements | Publicité, M USD | Demande attendue (P10-P90), k unités |
|---|---|---|---|---|---|
| USA | Thermique | 19 500 -> 22 000 USD | 5 | 800 -> 1 100 | 467 (356-645) |
| USA | Hybride | 37 000 -> 39 700 USD | 6 -> 7 | 300 -> 400 | 238 (190-287) |
| Chine | Thermique | 129 000 -> 139 000 RMB | 6 | 450 -> 650 | 443 (362-546) |
| Chine | Hybride | 230 000 -> 243 000 RMB | 6 -> 7 | 250 -> 350 | 313 (248-377) |
| Europe | Thermique | 23 000 -> 25 500 EUR | 5 -> 7 | 750 -> 1 050 | 464 (400-530) |
| Europe | Hybride | 35 000 -> 38 800 EUR | 6 -> 7 | 300 -> 400 | 296 (242-347) |

## Production
Usine Chine : Thermique 87 %, Hybride 9 %. Usine USA : Thermique 12 %, Hybride 5 %. Sous-traitance Hybride : Chine 484 k, USA 167 k.

## Autres décisions
- Achats : 3e fournisseur (Fusions Dynamiques).
- R&D : Hybride 309 077 jours-homme, Électrique 812 121, Hydrogène 266 000 ; Thermique 0.
- Événements : batteries actuelles conservées, transparence sélective (inchangé), prêt écologique inchangé.

## Matrice de gains (M USD)
| Stratégie | Statu quo | Tendance | Guerre des prix | Montée en gamme | Meilleure réponse | Mélange | Moyenne |
|---|---|---|---|---|---|---|---|
| Décisions du tour 4 reconduites | 20 937 | 21 155 | 17 076 | 17 512 | 23 513 | 19 891 | 20 014 |
| Recommandation | 23 116 | 23 423 | 18 597 | 19 185 | 26 303 | 21 860 | 22 081 |
| Optimum du modèle | 24 499 | 24 947 | 19 389 | 20 120 | 28 077 | 22 987 | 23 337 |

## Prévisionnel de la plateforme
Résultat net 16,39 Md USD, aucune demande non servie, stocks finaux 128 k Thermique et 70 k Hybride, trésorerie de fin de tour 17,7 Md USD.

## Remboursement de dette long terme : 4 Md USD (ajouté à 15h03)
- Effet attendu : économie d'intérêts, moindre exposition à la pénalité de taux du prêt écologique (score ESG 2,72 pour 3 requis).
- Prévisionnel : résultat net 16 392 -> 16 410 M USD ; trésorerie de fin de tour de la maison mère 17,7 -> 13,7 Md USD.
- Hypothèse défavorable (ventes 25 % sous la prévision, production inchangée) : résultat net 10 572 M USD, trésorerie 12,6 Md USD, aucune nouvelle dette à court terme affichée sur la page Finance.
- Non vérifié : la trésorerie de chaque filiale (Chine, Europe) dans ce cas défavorable, compte tenu des transferts internes déjà saisis.
- Remboursement total (8,4 Md USD) écarté ce tour : +37 M USD seulement, pour un coussin réduit à 9,4 Md USD.

## Enregistrement pour l'équipe : fait à 15h11
- À 15h09 la colonne de l'équipe affichait encore les décisions reconduites du tour 4 (résultat prévu 4,58 Md USD, 2 fournisseurs au lieu de 3, R&D non affectée). L'enregistrement, programmé pour 15h30, a été fait tout de suite ; la tâche programmée a tout de même tourné à 15h30 et a ré-enregistré la même zone (16 410 402 k USD), sans rien changer.
- `python3 -m cesim.save_team tour5` : équipe 4 577 624 -> 16 410 402 k USD, identique à la zone personnelle. Vérifié de nouveau à 15h24 sur la liste des décisions.
- Rien de nouveau sur le forum de session avant l'enregistrement (le message « propulsion à voile » vient d'un étudiant).

## Relevés ajoutés après coup (pour le tour 6)
- Couverture du réseau par technologie (page Demande) : le Thermique passe dès ce tour de 95-96 % à 86 % (USA), 84 % (Chine), 76 % (Europe). La recommandation ci-dessus ne le savait pas : sa demande de Thermique, surtout en Europe, est probablement trop haute. Prévision des marchés refaite avant résultats dans `out/tour5_prevision_marches.json`.
- Améliorations de processus (page Planning), testées dans le prévisionnel puis décochées : CO2 98 M USD et −20 % de capacité ce tour (résultat net prévu −533 M USD à production inchangée, l'usine de Chine étant à 96 %), énergie 154 M USD et −15 %, eau 126 M USD et +30 % de pertes (−107 M USD). Non prises ce tour ; à étudier au tour 6 en déplaçant de la production vers les USA (usine à 17 %).

## Décision étudiée et non prise : produire plus d'Hybride (15h31)
- Décision : +36 à +126 k Hybride à l'usine USA (ligne 2, usine à 17 % de charge). Effet attendu : éviter une rupture, l'offre mondiale d'Hybride étant de 928 k.
- Simulateur, 180 scénarios, nos décisions du tour 5 : demande d'Hybride moyenne 842 k (partage par extrapolation, celui de la recommandation), 903 k (méthode mixte), 975 k (couverture seule) ; probabilité de rupture 20 %, 45 %, 68 %. Thermique : stock final moyen 158 à 269 k pour 128 k prévus.
- Gain espéré de +54 k unités (marge perdue 10 k USD par unité manquante, 4,5 k USD par unité invendue reportée) : +32 M USD (mixte), −143 M USD (extrapolation), +208 M USD (couverture). Pour +36 k : +39, −86, +157.
- Verdict : gain espéré inférieur à 0,3 % du résultat et de signe contraire selon la méthode de marché, dont aucune ne domine en rejeu aveugle. Pas de modification. Les résultats du tour 5 diront quelle méthode avait raison.

## Optimiseur relancé avec le simulateur ajusté (15h37), décisions inchangées
- Simulateur calé sur les tours 1 à 4, nouvel étage des marchés (méthode mixte), offre mondiale fixée à ce qui est déjà planifié (Thermique 1 497 k, Hybride 928 k), 150 scénarios.

| Stratégie | Statu quo | Tendance | Guerre des prix | Montée en gamme | Meilleure réponse | Mélange | Moyenne | P10 |
|---|---|---|---|---|---|---|---|---|
| Tour 4 reconduit | 19 837 | 19 711 | 17 359 | 17 382 | 19 657 | 19 574 | 18 920 | 16 385 |
| Jouée au tour 5 | 22 741 | 22 429 | 18 898 | 19 110 | 23 766 | 22 261 | 21 534 | 17 880 |
| Optimum du modèle | 24 506 | 24 322 | 19 679 | 20 085 | 26 388 | 23 773 | 23 126 | 18 914 |

- Optimum du modèle : Thermique 23 000 USD / 141 000 RMB / 26 300 EUR, Hybride 42 700 USD / 260 000 RMB / 41 300 EUR, publicité 1 500 / 600 / 900 / 500 / 1 500 / 600 M USD, un équipement de moins en Thermique Chine et Europe. Il est collé aux bornes de recherche (publicité doublée, Hybride Europe +18 %) : c'est la zone où le moteur extrapole mal, on ne le joue pas tel quel.
- Seul écart nouveau par rapport à la recommandation : l'Hybride un peu plus cher, parce que la demande d'Hybride prévue approche l'offre. Variante testée, règle des 70 % appliquée au nouvel optimum : Hybride 41 000 USD, 251 000 RMB, 39 400 EUR (au lieu de 39 700, 243 000, 38 800).
  - Écart moyen avec la stratégie jouée : +372 M USD (mixte, gain dans 83 % des scénarios), +177 (extrapolation seule), +577 (couverture seule), +51 (marchés 15 % plus petits).
  - Clients 30 % plus sensibles au prix : −152 M USD, perte dans 100 % des scénarios.
- Verdict : la variante échoue à l'hypothèse défavorable sur le prix pour un gain de 1 à 2 % ; non appliquée. À reprendre au tour 6 avec les résultats du tour 5 (y a-t-il eu rupture en Hybride ?).
