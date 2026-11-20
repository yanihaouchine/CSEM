# Tour 8 — décisions prises (équipe tomobil)

Enregistrées pour l'équipe le 20/11 à 10h28 (`python3 -m cesim.save_team tour8`). Prévisionnel de la plateforme : résultat net 27 871 M USD, contre 21 528 M USD avec les décisions du tour 7 reconduites. Sauvegardes : `data/decisions_tour8_avant.txt`, `data/decisions_tour8_avant_enregistrement.txt`, `data/decisions_tour8_equipe.txt`.

Premier tour joué avec l'objectif en points du barème de l'instructeur (`model/points.py`, `objectif.py`), et non plus en marge.

## Validation présentée avant de décider

- Barème rejoué depuis les rapports : 2 écarts sur 252 attributions (tour 4), 2 sur 264 (tour 5), 8 (tour 6), 26 (tour 7). Au tour 7, 20 des 26 écarts viennent des stocks et de la demande non servie, que l'instructeur publie avec d'autres valeurs que les rapports (nos stocks : 0 publié, 31 dans le rapport).
- Prévision des points avec des concurrents repris du tour précédent : erreur de 1,4 à 1,9 point par critère, 6 à 16 points sur un total.
- Contre-épreuve avec les concurrents réels (`python3 objectif.py --tour N`) : la recherche en points à ±6 % aurait donné 161 points au lieu de 147 au tour 5 et 178 au lieu de 171 au tour 6 ; ±15 % fait moins bien (159 et 173) ; la recherche en marge ne gagne rien (148 et 170).
- Le rejeu du moteur de demande (`backtest.py`) n'a pas été relancé ici : le simulateur est recalé en parallèle (`out/tour8_alignement.md`).

## Résultats du tour 7

- 3ᵉ du tour au classement publié (149 points ; Ren'Auto 202, POLRAMOS 152). Résultat net 20 042 M USD.
- Demande 1 734 k unités, ventes 1 462 k : 271 k non servis (Hybride USA 92, Électrique USA 92, Hybride Chine 87). La production était trop basse et l'usine des USA tournait à 13 %.
- Critères faibles : part de marché USA (4,27 %, 2 points), part Chine (4,49 %, 2 points), productivité des ingénieurs (2), score fournisseurs (1, les 12 équipes à égalité), création de valeur (4).
- Électrique en Chine : vendu 440 000 RMB pour un prix médian de 320 000 ; 186 k unités, quand les vendeurs à 340 000 – 350 000 RMB et 7 équipements en ont fait 347 à 355 k pour la même marge de contribution.
- Marchés : Hydrogène aux USA 3 998 k (8 vendeurs), Électrique en Chine 5 300 k (11), en Europe 4 510 k (9), aux USA 1 119 k (4 vendeurs, dont deux n'ont presque rien livré).
- Les impacts ESG par composante ne sont plus publiés (tous à zéro dans le rapport) : la loi « score du pilier = fonction des impacts » est calée sur le tour 6.

## Nouveautés du tour 8

| Nouveauté | Traitement |
|---|---|
| Page « Service client » (`marketingaftersales`) : garantie 1, 2, 3 ou 5 ans ; collecte, protection et partage des données. Document de l'instructeur : la garantie augmente la demande, les données comptent dans le score S par rapport à la moyenne des équipes | ajoutée au relevé (`cesim/inputs.py`), au registre (`leviers.py`) et à l'étape D ; voir décisions |
| Hydrogène disponible (technologie + 1 équipement) | non lancé ce tour, voir plus bas |
| Certification Argent proposée (score cumulé 3,34) | prise |
| Événement « prêt écologique » de retour ; « approvisionnement durable » disparu | refusé : nous n'avons pas de dette |
| Ciblage de la stratégie marketing (apparu en cours de tour 7) | gardé à « Équilibré » : les rapports ne publient pas le choix des équipes, effet toujours inobservable |
| Document « Rachat d'actions » | non joué : jamais observé |
| Conditions de marché : USA +2 à 3 %, Chine environ +10 %, Europe −4 à −5 % ; RMB −5 % ; droits d'entrée aux USA portés à 15 % | saisis dans `data/tour_8_inputs.json` |
| Quiz individuel (avant 13 h) et fiche de classement des flyers (avant 13 h 30) | à faire par l'équipe, hors plateforme de décision |

## Décisions

| Levier | Avant | Après | Test |
|---|---|---|---|
| Hybride USA | 40 800 USD, 8 équipements, 450 M | 38 500, 8, 500 | point ±6 % de la recherche en points |
| Électrique USA | 55 000 USD, 7, 600 M | 51 800, 8, 700 | idem |
| Hybride Chine | 248 000 RMB, 8, 400 M | 234 000, 9, 450 | idem |
| Électrique Chine | 440 000 RMB, 7, 500 M | 352 000, 8, 700 | au-delà de ±6 % : justifié par les ventes observées au tour 7 ; +3,3 points attendus par rapport au point ±6 %, et mieux dans les trois mondes défavorables |
| Hybride Europe | 39 900 EUR, 7, 450 M | 37 500, 7, 500 | ±6 %, 7 équipements gardés (même total de points qu'avec 6) |
| Électrique Europe | 55 000 EUR, 7, 600 M | 58 300, 7, 700 | point ±6 % |
| Production | Chine 93 %, USA 13 % | Chine : Électrique 66,5 %, Hybride 30,9 % ; USA : Électrique 24,9 %, Hybride 37,1 % | couvre le quantile 75 % de la demande simulée, choisi en points (stocks + demande non servie + résultat) ; aucun non servi au prévisionnel |
| Routes | — | Électrique pour l'Europe fait en Chine, Hybride pour l'Europe fait aux USA | coûts lus : l'écart USA − Chine rendu en Europe est de 7 100 USD pour l'Électrique, 4 400 pour l'Hybride |
| Certification | Bronze | Argent | −19 M USD ; +2 points directs |
| Amélioration de processus | — | eau | −93 M USD ; environ +0,25 sur le score E |
| Service client | 1 an, protection basique | garantie 2 ans, protection avancée | −323 et −244 M USD ; effets annoncés par l'instructeur, jamais observés : pas modéré |
| R&D | 0 affecté | Hybride 275 514, Électrique 380 766, Hydrogène 731 220 jours-homme | un équipement de plus par technologie au tour 9 ; 0 jour libre |

Inchangés : gamme Hybride + Électrique dans les trois zones, 3 fournisseurs, formation « éthique », mentorat, engagement communautaire, recyclabilité « cycle de vie » + engagement, énergie renouvelable 100 %, salaire 6 300 USD, prix de transfert 1,00, transferts internes, pas de dette, pas de dividende.

Points attendus (concurrents repris du tour 7) : 161,6 avec le marketing reconduit, 167,9 avec les décisions jouées. Gains : part de marché Chine +3,2, création de valeur +2,1, part USA +0,9, marge Chine +0,7 ; pertes : coût unitaire Chine −1,0, marge USA −0,3. Le score fournisseurs y est surévalué (les 12 équipes sont à égalité : 1 point réel).

Demande attendue (k unités, moyenne et P10 – P90) : Hybride USA 298 (246 – 357), Électrique USA 345 (113 – 675), Hybride Chine 347 (262 – 434), Électrique Chine 413 (337 – 493), Hybride Europe 308 (234 – 375), Électrique Europe 347 (289 – 418).

## Leviers testés et non retenus

- Amélioration « énergie » : −698 M USD et capacité réduite de 15 % ce tour (1 530 et 1 063 k au lieu de 1 800 et 1 250), d'où 85 k unités non servies au prévisionnel. Saisie puis retirée.
- Partenariat stratégique : −3 074 M USD avec nos volumes du tour 8 (1 792 annoncés avant le changement de production), soit environ −5,8 points de résultat pour +5 points de gouvernance et +2,5 de demande espérés. Gain trop mince et non robuste. Saisi puis retiré.
- Amélioration « CO2 » : −4 Md USD environ.
- Fournisseur 4 seul : il nous placerait seuls en tête du score fournisseurs (+11 points), mais la pénalité pour moins de 3 fournisseurs coûte 6 064 M USD (environ −11 points).
- Garantie 3 ans (−599 M USD) et 5 ans (−1 078 M USD).
- Prix de transfert : aucun gain en points (le résultat des entités bouge de quelques dizaines de M USD).
- Dividende : un dollar versé retire 2,1 USD au cours (72 observations, 18 avec dividende) ; la rentabilité de l'action, qui inclut le dividende, y perd.
- Hydrogène aux USA : marché de 3 998 k unités, mais nous n'avons qu'un équipement (médiane des vendeurs : 6), il faudrait une licence et une ligne de production, et le simulateur n'a pas été testé sur cette cellule. Non testable dans le temps du tour.

## Recherche d'une avance de 60 points sur tous les concurrents

Objectif cherché : notre total du tour moins celui du meilleur concurrent (`objectif.Bareme.ecart`, points des 12 équipes recalculés dans chaque scénario).

| Stratégie | Nos points | Meilleur concurrent | Écart moyen | P10 – P90 | Probabilité d'être 1ᵉʳ du tour |
|---|---|---|---|---|---|
| Décisions reconduites | 154 | 195 (Ren'Auto) | −41 | −58 à −25 | 0 % |
| Décisions jouées | 168 | 194 | −26 | −42 à −8 | 5 % |
| Marketing à ±15 % | 174 | 195 | −21 | −38 à −5 | 4 % |
| Marketing à ±30 % | 179 | 195 | −16 | −33 à −1 | 7 % |
| Bornes larges (optimum du modèle, non jouable) | 189 | 194 | −5 | −20 à +9 | 38 % |
| Bornes larges et tous nos critères hors marketing au maximum (borne théorique) | 209 | 191 | +17 | +1 à +31 | 91 % |

Aucune stratégie n'atteint +60 : la probabilité est nulle dans tous les cas, borne théorique comprise. Ren'Auto a fait 202 points au tour 7 sur 256 possibles ; le devancer de 60 demanderait la quasi-totalité des points. Hors Ren'Auto, les décisions jouées nous placent environ 13 points devant le deuxième (POLRAMOS, 155).

## Risques

- La demande d'Électrique aux USA va de 113 à 675 k selon les scénarios (4 vendeurs au tour 7, nombre d'entrants inconnu) ; la production en couvre 439.
- Stocks attendus à la demande moyenne : 290 k unités (critère noté), dont 170 d'Électrique en Chine.
- L'usine de Chine est à 97,4 % : aucune marge si la demande chinoise dépasse le plan.
- Les valeurs des concurrents sont reprises du tour 7 : un concurrent qui change de gamme ou de prix déplace les rangs de part de marché et de coût unitaire.
- Garantie et protection des données : effet réel inconnu.

## Pour le tour 9

- Hydrogène : comparer en points Hybride + Hydrogène aux USA (`offre.py`), avec le coût d'une licence et d'une ligne.
- Productivité des ingénieurs (2 points) : la « formation de base » la fait monter de 0,01 à 0,06 par tour et son retrait l'a fait chuter de 0,14 ; à arbitrer contre le score S.
- Mesurer sur les résultats du tour 8 l'effet de la garantie et de la protection des données.
- Comprendre les stocks et la demande non servie tels que l'instructeur les publie.

## Recherche d'une stratégie sur trois tours (marge de 200 points)

Classement général publié après le tour 7 (cumul des tours 1 à 7) : Ren'Auto 1 006, Vrooom Vroooom 939, GT-Automobile VI 931, IronHorse 871, TABCHOUR 866, YANAUTO 865, POLRAMOS 816, tomobil 810, BM2P 798. Rythme moyen des tours 5 à 7 : Ren'Auto 170, tomobil 155, Vrooom 154, GT 144, TABCHOUR 133, YANAUTO 127, IronHorse 123.

- Une marge de 200 points en trois tours demande 67 points d'avance par tour sur le meilleur concurrent. La borne théorique du tour 8 (optimum du modèle sans zone de confiance et tous nos critères hors marketing au maximum) est de +17 : trois tours à ce niveau feraient +51. La cible est hors d'atteinte, quel que soit le temps de calcul.
- Leviers dont l'effet dure trois tours, chiffrés en points :
  - licences d'équipements (Électrique 10, Hybride 10) : +0,3 à +0,5 point par tour, parce que les équipements font monter le coût unitaire moyen, critère noté ; moins que le coût des licences (environ −1,3 point). Non retenu.
  - amélioration « énergie » (définitive) : l'amélioration « eau » prise au tour 7 n'a pas fait monter notre score E (2,97 puis 2,96) ; gain incertain, coût certain (−698 M USD et −15 % de capacité ce tour). Non retenu.
  - productivité des ingénieurs : elle revient vers la moyenne d'un tour à l'autre (coefficient −0,41 sur le niveau précédent), chute de 0,12 à 0,18 quand on retire la formation de base (nous au tour 6, IronHorse au tour 7) et ne remonte que de 0,03 à 0,05 quand on la remet. Environ +3 points par tour au mieux, contre un risque sur le score S (11 points). Non retenu sans test.
  - part de marché : l'inertie (exposant 0,08 à 0,15) reporte une partie du gain de ce tour sur les suivants ; c'est déjà dans les décisions jouées.
- Ce qui est atteignable au général : en gardant environ 165 points par tour, nous reprenons 40 à 45 points par tour à IronHorse, 30 à 35 à TABCHOUR et YANAUTO, et dépassons POLRAMOS : la 4ᵉ place est à portée (il faut 61, 56 et 55 points sur trois tours). GT (121 points d'avance) et Vrooom (129) demandent 40 points de mieux par tour, ce que nous n'avons fait contre aucun des deux ; Ren'Auto (196) est hors de portée.
- deepeirb n'a pas été utilisé : une recherche complète prend ici moins de trois minutes, la limite est l'information (concurrents inconnus, effets jamais observés), pas le calcul.

## Agents concurrents (test fait à 10h53, décisions inchangées)

- Rejeu en marche avant des tours 4 à 7 : un agent par équipe (décisions passées, état, style propre) se trompe plus que le statu quo sur les prix (9,3 % contre 8,3 %), les équipements et la publicité. Retenu : la seule réaction commune qui tient, le retour des prix vers le prix médian de la cellule, appliquée à moitié (7,9 %).
- Nos décisions candidates face à ces agents (100 scénarios) : reconduit 162,1 points ; ±6 % 165,4 ; décisions jouées 168,4 ; Électrique Chine à 375 000 RMB 167,3 ; à 330 000 RMB 169,4 ; ±15 % 169,7. Même ordre qu'avec les six comportements (161,3 / 164,4 / 167,8 / 166,6 / 169,0 / 168,8). Écart attendu au meilleur concurrent : −27 points.
- Les décisions enregistrées à 10h28 sont gardées : le gain d'un prix plus bas en Chine (+1 point) ne couvre pas le risque de rupture, l'usine de Chine étant à 97 %.

## Diagnostic SWOT de l'instructeur (tour 7) et piste des agents

- Piste « agents concurrents » abandonnée, script supprimé. L'objectif reste le total de points du barème.
- Ce que l'instructeur dit de nous, et ce que les décisions du tour 8 en font :
  - faiblesse « 87,1 % de la capacité des USA inoccupée » : l'usine des USA passe à 62 % (Électrique USA, Hybride USA et Europe) ; c'est ce qui supprime les 271 k unités non servies du tour 7 ;
  - faiblesse « absence sur l'Hydrogène » : non traitée ce tour (1 équipement, pas de test possible avant l'échéance) ; R&D Hydrogène financée (731 220 jours-homme) pour le tour 9 ;
  - faiblesse et menace « dépendance à l'Hybride, marché en recul » : l'Électrique passe de 43 % à 53 % de nos volumes prévus ;
  - force « stocks quasi nuls » : critère noté, gardé par un plan de production réglé en points (quantile 75 %) ;
  - opportunité « déployer la trésorerie en R&D ou en retour aux actionnaires » : R&D entièrement affectée ; dividende et rachat d'actions non retenus (un dollar de dividende retire 2,1 USD au cours : +2 rangs de ROE environ contre −2 à −3 rangs de rentabilité de l'action ; rachat jamais observé).
- Ce qu'il dit des concurrents confirme où nous prenons des rangs sans effort : dettes à court terme imprévues (IronHorse 13,0 Md USD, Ça Roule 10,1, AURA 5,9) et stocks lourds (IronHorse, Vrooom, AURA, GT, YANAUTO) nous laissent en tête sur le découvert, l'indépendance financière et les stocks.
