# Comportement du jeu — ce que l'on sait des mécanismes

Ce fichier sert à comprendre vite comment réagit le jeu (Cesim Global Challenge, cas automobile). Il se lit sans avoir suivi les tours précédents. Il ne décrit pas le code (voir le `README.md`) mais le marché : ce qui fait vendre, ce qui coûte, ce qui fait monter le cours de l'action.

Chaque affirmation porte son niveau de preuve :

- **Établi** : lu sur la plateforme, ou vérifié sur les données sans ambiguïté.
- **Probable** : mesuré sur les résultats des 12 équipes, avec un test à l'appui, mais sur peu de tours.
- **Hypothèse** : cohérent avec les données, pas encore testé ou test non concluant.
- **Infirmé** : idée essayée, que les données ne soutiennent pas.

Données utilisées : tour d'entraînement et tours 1 à 7. Dernière mise à jour : 20/11/2026 à 10h17, après les résultats du tour 7. Les tableaux chiffrés de la section 5 datent du calage sur les tours 1 à 4.

Règle d'entretien : après chaque tour, relancer les tests de la section 11 et corriger ici ce qui a changé. Une valeur qui n'a pas été revérifiée garde la date de son dernier test.

## 1. Repères

- 12 équipes, 3 zones (USA, Chine, Europe), 4 technologies (Thermique, Hybride, Électrique, Hydrogène), 10 tours.
- Le tour d'entraînement a été joué puis effacé : le tour 1 est reparti de la situation initiale, avec les mêmes conditions de marché. Dans les fichiers, `round_0` est la situation initiale, `round_1` l'entraînement, `round_k` le tour k−1. Le « tour précédent » du tour 1 est donc `round_0`.
- Toutes les équipes partent du même état. Les écarts viennent uniquement des décisions.
- Les résultats publient, pour les 12 équipes, les prix, équipements, publicité, demande, ventes, coûts, comptes, ESG, RH, production. Les décisions des concurrents sont donc connues après coup, jamais avant.

## 2. Ce qui fait le classement

- **Établi.** Le classement se fait sur le retour cumulé aux actionnaires. Tant que personne ne verse de dividende (cas des 12 équipes jusqu'ici), il vaut exactement (cours de l'action / 48,6)^(1/nombre de tours) − 1. Vérifié sur les 12 équipes aux tours 1 à 4, écart maximal 0,07 point. Seul le cours de l'action compte.
- **Probable.** Le cours suit les fonds propres par action et le bénéfice par action : cours ≈ 25 + 3,5 × fonds propres par action + 2,1 × bénéfice par action du tour (R² = 0,91 sur 60 observations, erreur moyenne 9 USD). Les fonds propres seuls expliquent 90 %. Accumuler du bénéfice est donc ce qui paie ; un bon tour isolé pèse peu.
- **Hypothèse.** La dette à court terme (découvert) pèse négativement, la réputation ESG positivement : coefficients du bon signe, mais non significatifs.
- **Hypothèse.** Un dividende détruit plus de cours qu'il ne rapporte. Une seule observation : au tour 5, POLRAMOS a versé environ 25 USD par action et son cours est passé de 130 à 50 USD (une perte de 7,5 USD par action explique une petite part de la chute). Son retour cumulé est tombé de 27,9 % à 9,3 %. La régression va dans le même sens (un dollar gardé en fonds propres vaut 3,5 USD de cours). Nous n'en versons pas.
- **Établi (20/11).** La part de marché d'une zone, notée par l'instructeur, se calcule sur les ventes : ventes de l'équipe / ventes totales de la zone, toutes technologies confondues. Écart avec la valeur publiée : 0,011 point au plus aux tours 4 à 6 (0,8 à 7,4 points si on la calcule sur la demande). `sim.team_zone` redonne les points du classement pour 107 cas sur 108. Une rupture de stock coûte donc deux fois : demande insatisfaite et part de marché.
- **Établi.** Quand un dividende a été versé, le retour cumulé l'inclut : ((cours + dividendes cumulés par action) / 48,6)^(1/nombre de tours) − 1.
- Au tour 4 nous étions 10ᵉ sur 12 (18,8 % par an, leader Ren'Auto 44,1 %). Au tour 5 : 7ᵉ (25,2 %). Au tour 6 : 4ᵉ (24,8 %, leader Ren'Auto 37,7 %, 2ᵉ Vrooom Vroooom 26,2 %), cours 183,9 USD. Notre retard vient des tours 1 et 2 (bénéfice par action 0,65 puis 0,29 USD, quand la plupart des équipes étaient entre 3,5 et 6,5), où une forte hausse de prix a laissé des stocks et un découvert.

## 3. Structure de l'offre

- **Établi.** Chaque équipe vend au plus 2 modèles par zone, à choisir parmi les technologies qu'elle possède ; le menu d'un modèle exclut seulement la technologie de l'autre modèle (vérifié au tour 6 : avec le modèle 1 en Électrique, le modèle 2 peut être Thermique ou Hybride). Chaque usine a 2 lignes de production soumises au même choix. L'Hydrogène n'apparaît qu'après achat de la licence (à la plateforme ou, depuis le tour 6, à une autre équipe) ou développement en R&D.
- **Établi.** Nous possédons l'Électrique avec 2 équipements (tour 6). Des licences donnent jusqu'à 5 équipements de plus tout de suite.
- **Établi.** Changer la technologie d'un modèle remet à zéro son prix, sa publicité, ses équipements et sa part estimée.
- **Établi.** Un produit se définit par zone : prix (monnaie locale), nombre d'équipements, publicité (k USD). Le nombre d'équipements disponibles par technologie vient de la R&D interne (jours-homme) ou de licences (disponibles tout de suite, environ 290 M USD par équipement au tour 4). Au tour 5 nous avons 8 équipements en Thermique, 7 en Hybride.
- **Établi.** L'Europe n'a pas d'usine : tout y est importé des USA ou de Chine (transport + droits de douane en % du coût unitaire).
- **Établi.** L'interdiction du Thermique annoncée par l'instructeur au tour 5 s'est faite par la couverture du réseau : −20 points au tour 6, puis 0 dans les trois zones à partir du tour 7. Un modèle Thermique n'a plus de marché à partir du tour 7. La couverture de l'Hybride a été abaissée en même temps de 40 points (55 à 57 % à partir du tour 7).
- **Établi.** Sur la plateforme, les champs d'un produit s'appellent `areaN.techK.*` avec K = 1 Thermique, 2 Hybride, 3 Électrique, 4 Hydrogène : quand un modèle change de technologie, ce sont d'autres champs qu'il faut remplir.
- Les messages du forum signés d'un autre nom que l'instructeur sont des plaisanteries d'étudiants (exemple : « propulsion à voile », tour 5).

- **Établi (tour 7).** Un menu « Ciblage de la stratégie marketing » est apparu par produit en cours de tour 7 (`areaN.techK.mstrat` : équilibré, prix bas, équipements, image de marque, développement durable). D'après l'aide, il amplifie l'effet du levier ciblé si nous sommes mieux placés que les concurrents de la cellule sur cet axe, et pénalise dans le cas contraire. **Effet inconnu** : aucune observation avant les résultats du tour 7 ; gardé à « équilibré » au tour 7. Le moteur ne le représente pas.
- **Établi.** Des champs peuvent apparaître pendant un tour : relancer `python3 -m cesim.inputs N` et `python3 leviers.py N` avant l'échéance, pas seulement à l'ouverture.

## 4. Taille des marchés et partage entre technologies

### Total par zone

- **Établi.** Le total d'une zone ne suit pas la croissance annoncée dans les conditions de marché. Écarts entre croissance réelle et annoncée : de −8 à +19 points. Au tour 5 : Europe +15,8 % pour −3 % annoncés, Chine +2,3 % pour +10 %, USA −0,7 % pour +2 %. Au tour 6 : Europe −24,7 % pour +6 % annoncés, Chine −6,5 % pour +6 %, USA −2,2 % pour +1 %. Erreur aveugle de notre prévision du total par zone : 3,1 / 2,4 / 4,2 / 9,8 / 18,8 % aux tours 2 à 6. L'écart grandit depuis que les couvertures bougent : le total d'une zone n'est pas une donnée du jeu, c'est la somme de demandes par technologie qui évoluent chacune de leur côté.
- **Hypothèse.** Le total baisse quand le prix moyen monte et monte avec la publicité totale (élasticités −0,5 et +0,05 dans le code). Ces coefficients n'expliquent qu'un quart des écarts. La hausse de l'Europe au tour 5 reste inexpliquée.
- Conséquence pratique : pour le tour 6 la croissance saisie est la moyenne de l'annonce et de la croissance réelle du tour précédent, et l'incertitude tirée dans les scénarios est large.

### Partage entre technologies

- **Établi.** La page Demande publie un graphique « Réseau de stations » : la couverture (%) de chaque technologie par zone, pour les tours 0 à 12, tours futurs compris. `python3 -m cesim.inputs N` l'enregistre dans `data/couverture_tour_N.json` et signale les révisions. Relevé du tour 6 :

| Zone | Techno | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 | T9 | T10 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| USA | Thermique | 95 | 95 | 95 | 95 | 86 | 56 | 46 | 36 | 36 | 24 |
| USA | Hybride | 55 | 65 | 75 | 85 | 96 | 97 | 97 | 97 | 96 | 95 |
| USA | Électrique | 9 | 11 | 14 | 17 | 21 | 27 | 32 | 34 | 35 | 36 |
| USA | Hydrogène | 0 | 0 | 0 | 0 | 26 | 36 | 47 | 64 | 68 | 74 |
| Chine | Thermique | 92 | 92 | 93 | 93 | 84 | 54 | 45 | 34 | 33 | 23 |
| Chine | Hybride | 52 | 62 | 72 | 83 | 94 | 94 | 95 | 94 | 94 | 93 |
| Chine | Électrique | 9 | 16 | 21 | 29 | 37 | 45 | 57 | 70 | 78 | 80 |
| Chine | Hydrogène | 0 | 0 | 0 | 0 | 8 | 11 | 26 | 26 | 29 | 30 |
| Europe | Thermique | 96 | 96 | 96 | 96 | 76 | 46 | 36 | 26 | 23 | 22 |
| Europe | Hybride | 56 | 66 | 76 | 86 | 86 | 77 | 67 | 56 | 56 | 46 |
| Europe | Électrique | 8 | 10 | 18 | 25 | 30 | 36 | 54 | 65 | 68 | 65 |
| Europe | Hydrogène | 0 | 0 | 0 | 0 | 25 | 35 | 50 | 70 | 75 | 80 |

- **Établi.** Le scénario révise ces courbes : entre le relevé du tour 5 et celui du tour 6, la couverture du Thermique a perdu 20 points à tous les tours à partir du tour 6 (après l'annonce de l'interdiction par l'instructeur). Elle ne tombe pas à zéro au tour 7 (36 à 46 %).
- **Probable depuis le tour 6.** La demande d'une technologie suit sa couverture, à peu près en proportion. Tour 6 : couverture du Thermique multipliée par 0,65 (USA), 0,64 (Chine), 0,61 (Europe) ; demande multipliée par 0,66, 0,60, 0,50. Tour 5 : −6 à −7 % aux USA et en Chine pour −10 % de couverture. Seule exception, l'Europe au tour 5 (+10 % malgré −21 % de couverture).
- **Probable.** La demande perdue par une technologie se reporte en partie sur les autres : au tour 6, 31 % de la perte du Thermique est allée à l'Hybride aux USA et 58 % à l'Hydrogène ; en Chine 23 % à l'Hybride et 50 % à l'Électrique ; en Europe presque rien (marché total −25 %).
- Rejeu aveugle de la taille des cellules (zone × technologie), total de zone compris, refait le 20/11 avec le tour 6 (`python3 -m model.market`) :

| Méthode | Tour 2 | Tour 3 | Tour 4 | Tour 5 | Tour 6 | Moyenne |
|---|---|---|---|---|---|---|
| Extrapolation de la tendance (« logit ») | 10,1 % | 3,5 % | 19,0 % | 9,8 % | 38,7 % | 16,2 % |
| Couverture, partage d'un total de zone (« sous-ensembles ») | 4,3 % | 17,4 % | 6,3 % | 22,9 % | 34,6 % | 17,1 % |
| Moyenne des deux (« mixte » jusqu'au tour 6) | 4,7 % | 7,8 % | 11,3 % | 13,9 % | 33,7 % | 14,3 % |
| Prévision directe par technologie (`market.direct_cells`) | 7,5 % | 27,4 % | 9,2 % | 14,5 % | 17,4 % | 15,2 % |
| « Mixte » depuis le 20/11 : moitié ancienne mixte, moitié directe | 5,2 % | 17,6 % | 7,1 % | 13,8 % | 20,8 % | 12,9 % |

- Aucune méthode ne domine, et la meilleure change d'un tour à l'autre : la couverture gagne aux tours 2 et 4, la tendance aux tours 3 et 5, la prévision directe au tour 6. Choisir la méthode sur les tours passés (marche avant) aurait donné à chaque fois la mauvaise au tour suivant. D'où le mélange, et des poids tirés au hasard dans les scénarios. C'est le maillon faible du simulateur.
- **Infirmé.** Régler des exposants (couverture, nombre de produits, équipements, tendance) sur les tours passés : la meilleure combinaison après coup fait 7 % d'erreur de partage, mais choisie en marche avant elle fait 25 / 19 / 12 % aux tours 3 à 5, pire que le mélange à poids fixes.
- Où la nouvelle « mixte » se trompe encore au tour 6 : Thermique +6 à +27 %, Hybride +2 à +9 %, Électrique −67 % en Chine et +101 % en Europe, Hydrogène −64 % en Europe et −99 % aux USA.
- **Probable.** L'attrait d'une technologie croît avec le nombre de produits offerts et leurs équipements. Un produit de plus dans une technologie agrandit le marché de cette technologie, il ne fait pas que le partager. Mesure aux tours 1 à 4 : attrait de l'Hybride ∝ nombre de produits^1,0 × équipements relatifs^1,2 (12 points). Nuance du tour 6 : l'Électrique en Europe est passé de 2 à 7 vendeurs pour +29 % de demande seulement (couverture +20 %), alors qu'en Chine un vendeur de plus s'est accompagné d'une demande ×5. Le nombre de vendeurs n'explique donc pas la taille d'une cellule nouvelle ; l'exposant est de 0,5 dans la prévision directe.
- **Probable.** Le scénario ajoute des sauts d'attrait annoncés seulement par une phrase des conditions de marché (tour 3 : « l'attrait des véhicules hybrides augmentera » ; tour 6 : « augmentation de la demande pour les véhicules hybrides et électriques »).
- **Établi.** Seul le relevé du tour en cours fait foi pour ce tour. Thermique au tour 6 : 76-66 % dans le relevé du tour 5, 56 / 54 / 46 % dans celui du tour 6. Thermique au tour 7 : 46 / 45 / 36 % dans le relevé du tour 6, 0 % dans celui du tour 7. Hybride au tour 7 : 97 / 95 / 67 % puis 57 / 55 / 55 %. `market.coverage()` lit toujours le relevé le plus récent : relancer `python3 -m cesim.inputs N` avant toute prévision.
- **Probable.** Le marché n'est pas un total de zone que les technologies se partagent : la demande perdue par le Thermique au tour 6 ne s'est reportée qu'en partie (voir ci-dessus), et le total de l'Europe a baissé de 25 %. Les deux méthodes qui partagent un total de zone se sont trompées de 31 à 35 % au tour 6 sur les cellules existantes, la prévision directe de 13 %. Pour le Thermique seul, la règle « demande précédente × rapport des couvertures » tombe à +1 %, +2 % et −6 % du réel (Chine, Europe, USA).
- **Probable.** L'Hybride a gagné 12 à 17 % par tour aux tours 5 et 6 dans les zones où sa couverture ne bougeait pas ou montait, et 0 % en Europe au tour 6 quand sa couverture a perdu 9 points. Avec la règle proportionnelle, une couverture de l'Hybride ramenée de 97 / 94 / 77 % à 57 / 55 / 55 % au tour 7 retire 30 à 40 % de sa demande aux USA et en Chine, près de 30 % en Europe. Non observé encore : c'est le pari le plus lourd du tour 7.
- **Infirmé (tour 5).** « Un client couvert par une seule technologie l'achète » (hypothèse du modèle « sous-ensembles ») : avec 25 % de couverture ce modèle attribuait d'office 78 k unités à l'Hydrogène en Europe, il en a reçu 1 k. `market.NEW_APPEAL["Hydrogène"]` est passé de 0,035 à 0,0005 sur cette observation ; le tour 6 (12,5 % du marché des USA pour 2 vendeurs) montre que cette valeur est devenue trop basse : l'attrait d'une technologie nouvelle dépend du prix auquel elle est offerte et du scénario, pas d'une constante.
- La prévision directe vaut : demande précédente × (1 + croissance annoncée) × rapport des couvertures × (nombre de produits / nombre précédent)^0,5. Elle ne s'applique qu'aux cellules déjà vendues ; une cellule nouvelle garde l'estimation par partage.
- **Infirmé (tour 6).** Un partage sans effet de la couverture (`market.tech_shares_offer`) faisait mieux aux tours 4 et 5, le tour 6 l'a contredit (37,8 % d'erreur). Gardé dans le code comme essai, non utilisé.
- Depuis le 20/11, `market.forecast` retire lui-même du cadre les produits d'une technologie sans réseau (couverture 0) et leur donne une demande nulle.
- **Infirmé (20/11, rejeu aveugle des tours 2 à 6, cellules déjà vendues).** Ajouter à la prévision directe la tendance propre de la cellule (sa croissance du tour précédent, hors couverture et nombre de produits, amortie) : erreur moyenne 15,0 % sans tendance, 15,4 / 16,5 / 18,5 % avec un amortissement de 0,25 / 0,5 / 0,75. La progression régulière de l'Hybride ne se prolonge pas d'elle-même.
- **Infirmé (20/11, même rejeu).** Faire dépendre la taille d'une cellule de l'attrait moyen de l'offre calculé par le moteur (prix par rapport au tour précédent, équipements, publicité), à la puissance τ : erreur moyenne 15,0 % pour τ = 0, puis 15,4 / 16,3 / 17,3 / 18,4 % pour τ = 0,25 à 1. L'idée explique bien l'Électrique en Chine au tour 6 (prix −25 %, demande ×5) mais se trompe dans l'autre sens en Europe (7 vendeurs au lieu de 2, demande +29 %) et dégrade le Thermique. L'exposant 0,5 sur le nombre de produits reste le meilleur (15,0 % contre 16,8 % sans, 22,4 % avec 1).
- **Infirmé (20/11, même rejeu).** Rappeler la pénétration d'une zone vers la médiane des trois zones : 15,0 % sans rappel, 15,3 / 15,9 / 16,5 % avec un rappel de 0,25 / 0,5 / 0,75.
- **Probable (20/11).** La pénétration d'une technologie (demande / (marché de base de la zone × couverture), le marché de base étant la demande de Thermique du tour d'entraînement divisée par sa couverture, puis les croissances annoncées cumulées) est proche d'une zone à l'autre : Hybride 0,12-0,13 (USA, Chine) au tour 1, puis 0,20-0,26 / 0,37-0,41 / 0,38-0,43 / 0,36-0,47 / 0,42-0,49 aux tours 2 à 6 ; Thermique 0,93-1,00 / 0,88-0,92 / 0,69-0,78 / 0,60-0,75 / 0,67-0,86 / 0,62-0,68 ; Électrique au tour 6 : 0,32 (Chine), 0,25 (Europe) ; Hydrogène au tour 6 : 0,31 (USA, 2 vendeurs), 0,07 (Europe, 1 vendeur). `market.penetration_table()` refait le tableau. Conséquence : une cellule nouvelle dans une zone se prévoit par analogie avec les autres zones (`market.analog_cells`, employé par `forecast` depuis le 20/11). Un seul cas rejoué en aveugle (Électrique en Europe au tour 4 : 143 k prévus pour 299 réels, contre 60 avec l'attrait par défaut) et un cas calculé à la main (Hybride en Europe au tour 1 d'après le tour d'entraînement : 387 k pour 392).
- **Probable (20/11).** L'erreur de taille dépend de l'ancienneté de la cellule. Cellules installées (vendues depuis 3 tours au moins, par 8 équipes au moins) : 0,18 en log pour la prévision directe, 0,14 pour la « mixte » (23 cas ; 0,08 et 0,12 au tour 6). Cellules jeunes : −0,01 / +0,29 / −0,59 / −1,28 / +0,61 pour l'Électrique, et un facteur 300 à 600 pour l'Hydrogène dont le prix a été divisé par trois. Les scénarios ne tiraient que 0,12 à 0,15 pour toutes : `market.SD_YOUNG` = 0,6 élargit désormais les cellules jeunes (`market.young_cells`). Une prévision de demande sur une cellule jeune est un ordre de grandeur, pas un chiffre.

### Électrique et Hydrogène : ce que l'on a vu

- **Établi.** L'Électrique en Europe est la poche de profit la plus riche du jeu. Tour 4 : MO'THOR, seule, 299 k unités avec 1 équipement. Tour 5 : 885 k unités pour 2 vendeurs. POLRAMOS y a vendu 333 k unités à 84 000 EUR avec 10 équipements, soit 65 000 USD de marge par véhicule et 20,8 Md USD de marge de contribution sur ce seul produit ; MO'THOR 552 k à 45 000 EUR avec 3 équipements (8,9 Md USD). La demande y est peu sensible au prix : un prix presque doublé n'a coûté que 40 % du volume, équipements en plus.
- **Établi.** L'Électrique en Chine est encombré et peu rentable : 5 vendeurs se partagent 282 k unités au tour 5, deux y perdent de l'argent.
- **Établi.** L'Hydrogène ne se vendait pas au tour 5 à 120 000 EUR et 140 000 USD (1 k unité par zone). Au tour 6, à 39 000 et 55 000 USD, deux vendeurs ont reçu 1 153 k unités de demande aux USA (marges faibles : 1 800 et 11 200 USD par véhicule, coût unitaire 37 000 à 44 000 USD), et un vendeur 290 k en Europe à 47 500 EUR, sans rien pouvoir livrer.
- **Établi.** Tour 6, Électrique : la Chine passe à 1 429 k unités pour 6 vendeurs, l'Europe à 1 139 k pour 7 vendeurs (2 au tour 5). La rente de POLRAMOS en Europe a disparu en un tour (20,8 → 1,5 Md USD). Les meilleures marges vont aux vendeurs à 10 équipements et prix élevé (Chine : 480 000 à 560 000 RMB, 4,5 à 6,5 Md USD de marge).
- **Établi.** Coûts lus au tour 7 : Électrique 27 340 USD à l'usine de Chine, 32 947 aux USA, hors équipements ; licence Électrique 350 M USD par équipement (5 au plus) ; licence Hydrogène 9 050 M USD avec 2 équipements, 10 700 M avec 5 ; licence Hybride 240 M USD par équipement.
- Coût unitaire d'un véhicule Électrique chez les concurrents : 30 000 à 41 000 USD.
- **Établi.** Ce que le simulateur aurait dit d'une entrée en Électrique en Europe au tour 6 (`offre.py`, données d'avant le tour) : cellule prévue à 1 400-2 300 k unités, +6,9 Md USD de marge pour nous, ramenés à zéro si 4 concurrents entraient aussi. Cinq sont entrés et la cellule a fait 1 139 k. Le scénario « plusieurs entrants » est le cas normal quand une poche de profit est visible dans les résultats publiés, pas le cas défavorable.
- **Probable.** Pour une technologie vue moins de 12 fois dans une zone, les paramètres Hybride de la zone prédisent mieux la répartition entre vendeurs que des paramètres propres. Erreur qui reste : 9 % avec 5 vendeurs (Chine, tour 5), 47 à 55 % avec 2 vendeurs. À 2 vendeurs le moteur ne dit presque rien.
- Prix moyens observés : Électrique en Europe 40 000 EUR (tour 4), 64 500 (tour 5), 53 300 (tour 6) ; en Chine 457 500, 540 000, 450 800 RMB. Hydrogène 120 000 à 140 000 (tour 5), 47 000 à 47 500 (tour 6). Équipements moyens de l'Électrique en Chine : 3, 6, 8.

### Ce que le tour 7 a tranché (20/11)

- **Établi.** Quand le Thermique a disparu, le total de chaque zone a tenu et même monté : +10,2 % (USA), +9,6 % (Chine), +4,7 % (Europe). Sa demande s'est reportée en entier. Hydrogène USA 3 998 k (8 vendeurs), Europe 2 087 k (6) ; Électrique Chine 5 300 k (11), Europe 4 510 k (9), USA 1 119 k (4).
- **Infirmé.** « La demande de l'Hybride suit sa couverture » : couverture ×0,59, demande ×1,21 aux USA et ×1,01 en Chine ; ×0,71 et ×0,81 en Europe.
- Rejeu aveugle des tailles de cellule au tour 7 : couverture 17,4 %, directe 39,5 %, tendance 47,2 %, mixte 24,5 %. Sur les tours 2 à 7, aucune pondération des trois méthodes ne fait mieux que 14,8 % en moyenne ; « mixte » reste la valeur par défaut.
- **Infirmé.** Report d'une part de la demande perdue dans la prévision directe (`market.REPORT`) : à 0,5, 39,5 → 23,7 % au tour 7 mais 17,4 → 23,2 % au tour 6. Parts calculées entre technologies vivantes (`market.LIVE_LOGIT`) : 47 → 62 % au tour 7.
- Pénétration au tour 7 (demande / marché de base × couverture) : Hybride 0,85 / 0,70 / 0,53 ; Électrique 0,34 / 0,87 / 0,63 ; Hydrogène 0,82 / 0,11 / 0,32 (USA, Chine, Europe).

## 5. Répartition de la demande entre équipes

- **Établi (tour 7).** Le rapport ESG publie des impacts sur la demande tous nuls depuis le tour 7, mais l'effet continue d'agir : erreur aveugle 12,3 % avec un impact nul, 7,2 % avec un impact reconstitué (moitié impact du tour précédent, moitié impact déduit des écarts relatifs des scores E, S, G, coefficients proches de 0,8 / 0,2 / 0,2). `panel2.esg_hidden` fait la reconstitution. Les scores E, S, G sont donc désormais la seule lecture de notre position ESG.
- **Probable (tour 7).** Ciblage de la stratégie marketing, résidu aveugle par option une fois l'ESG reconstitué : développement durable +3 à +8 % (12 produits, équipes à score ESG élevé), prix bas −2 à −4 % (15), équipements −4 % (16), équilibré 0 à +2 % (28). Effet faible, dans le bruit ; personne n'a pris « image de marque ».
- **Probable.** Technologies jeunes : les paramètres de l'Hybride de la zone restent meilleurs que des paramètres propres même avec 14 observations (Électrique Chine au tour 7 : 11,2 % contre 15,1 %). Seuil `sim.MIN_OBS` porté à 30.


Forme du moteur (`model/engine.py`) : chaque produit a une attraction, la demande d'une cellule (zone × technologie) se partage au prorata des attractions.

attraction = exp(−k × prix relatif^g) × équipements^f × (publicité + λ × publicité de l'autre produit + c)^a × effets ESG × qualité fournisseurs × certification × (part précédente)^h × pénalité de rupture

Erreur de ce moteur sur la répartition : 1 à 6 % une fois calé, 4,5 à 9 % en aveugle (7,4 / 9,3 / 4,5 / 6,7 / 6,9 % aux tours 2 à 6 ; hors Thermique : 12,5 / 14,8 / 5,5 / 8,8 / 9,5 %). Depuis le 20/11 les cellules observées moins de 12 fois sortent du calage (elles prennent les paramètres de l'Hybride de la zone) : le calage aveugle du tour 6 passe de 141 s à 3 s, sans changer les paramètres du Thermique ni de l'Hybride (prévisions ex ante identiques sur 3 graines, tours 4 à 6). Le rejeu aveugle applique désormais ce même repli, comme la recherche le faisait déjà : son erreur du tour 6 passe de 8,8 % à 6,9 % (l'ancien rejeu donnait à l'Électrique des paramètres ajustés sur 2 à 8 observations). Ce n'est pas un gain du moteur, c'est le rejeu qui mesure enfin ce que la recherche emploie. Variantes essayées le même jour, sans effet (±0,4 point) : rappel vers les valeurs neutres plus fort ou plus faible, poids plus grand aux tours récents, calage commun Hybride + Électrique + Hydrogène ; un seuil de 6 observations au lieu de 12 fait moins bien (8,3 % au tour 6). Les résidus aveugles n'ont pas de structure exploitable (corrélation de l'erreur avec le prix relatif +0,12, les équipements +0,06, la publicité −0,02, l'impact ESG 0,00, la qualité −0,19 ; tours 2 à 4) : il n'y a pas de mécanisme manquant visible, changer la forme du moteur ne rapporterait rien. Les équipes les plus mal prévues sont celles aux décisions extrêmes (Vrooom Vroooom, Ren'Auto, MO'THOR : 11 à 13 % d'erreur par produit, contre 5 à 6 % pour les équipes proches de la moyenne) ; Ren'Auto, à 10 équipements et prix très élevés, est tantôt sous-estimée de 15 à 20 %, tantôt surestimée de 40 %. Les valeurs du tableau datent du calage sur les tours 1 à 4 ; les tests par retrait n'ont pas été refaits avec le tour 5.

| Mécanisme | Niveau | Ce que disent les données |
|---|---|---|
| Déterminisme | **Établi** | Deux équipes aux décisions identiques reçoivent exactement la même demande (3 groupes d'équipes jumelles au tour d'entraînement, demande égale à l'unité près). Aucun aléa dans la répartition. |
| Prix | **Établi** | Levier le plus fort. Élasticité de la demande d'un produit à son prix, au prix moyen du marché : Chine −3,0 à −4,8 ; USA −2,4 à −4,0 ; Europe −1,8 à −2,0. La fourchette donne le moteur (bas) et une régression directe (haut). Conforme à la description du cas (sensibilité au prix : Chine élevée, USA moyenne, Europe faible). |
| Prix : repère des clients | **Hypothèse** | Le moteur juge le prix par rapport au prix moyen du marché au tour précédent. Le remplacer par le prix moyen du tour courant donne la même erreur aveugle (7,0 % contre 7,1 %) : les données ne tranchent pas. |
| Prix : effet plus que proportionnel | **Hypothèse** | Exposant g = 1,0 à 1,15. Fixer g = 1 ne change pas l'erreur (7,1 %). Non démontré. |
| Équipements | **Établi** | Exposant f : Chine 0,57 à 0,69 ; USA 0,45 ; Europe 0,25 à 0,28. Passer de 5 à 6 équipements donne +11 % de demande en Chine, +9 % aux USA, +5 % en Europe, pour 650 à 750 USD de coût par véhicule. |
| Publicité propre | **Établi** | Effet saturant. Aux niveaux actuels, doubler la publicité d'un produit augmente sa demande de 6 à 20 % (élasticité 0,09 à 0,27 ; plus forte aux USA, plus faible en Europe, conforme au cas). |
| Publicité de l'autre produit | **Probable** | La publicité d'un produit profite à l'autre produit de la même équipe sur le même marché, à hauteur de 29 % (λ = 0,29). Sans cet effet, l'erreur aveugle passe de 7,1 % à 8,4 %. En régression directe l'effet est net aux USA et en Chine, non significatif en Europe. |
| Sensibilité à la publicité variable | **Probable** | Le jeu l'annonce dans les conditions de marché : « marché devenu réactif » (tour 2), « de moins en moins sensibles » (tour 3), « plus irritée qu'impressionnée » (tour 4). Le coefficient mesuré tour par tour a doublé au tour 2 puis reculé. À lire chaque tour, réglé par `adv_mult` dans les entrées du tour. |
| Inertie de la part de marché | **Probable** | Exposant h = 0,08 à 0,15 sur la part du tour précédent. Sans elle, erreur aveugle 8,0 % au lieu de 7,1 %. Une part gagnée se conserve en partie le tour suivant. |
| Qualité des fournisseurs | **Probable** | Exposant 0,19 à 0,36 sur la qualité (échelle 1,75 à 3,5). Sans elle, l'erreur aveugle du tour 3 passe de 9 % à 17 %. Des fournisseurs bon marché de qualité 2 coûtent 10 à 18 % de demande face à la qualité 3,5. |
| Certification développement durable | **Probable** | Une équipe certifiée (Bronze ou plus) gagne environ 12 % d'attraction. Sans elle, erreur aveugle 7,8 % au lieu de 7,1 %. L'écart entre Bronze, Argent et Or n'est pas mesuré. |
| Impacts ESG | **Établi** | Le rapport ESG publie, en %, l'impact de chaque composante sur la demande. Les appliquer tels quels (coefficient 1) reproduit les données aussi bien qu'un coefficient ajusté (7,0 % contre 7,1 %). |
| Pénalité après rupture de stock | **Hypothèse** | Coefficient faible (0,14 × part de demande non servie) ; la retirer ne change presque rien (7,2 % contre 7,1 %). En revanche la vente perdue le tour même est certaine. |
| Produit nouveau | **Infirmé** | Pas de handicap mesurable pour un produit lancé dans le tour (coefficient −0,04). |

À retenir pour décider : une hausse de prix de 10 % coûte 16 à 37 % de volume selon la zone, toutes choses égales par ailleurs ; elle se justifie surtout en Europe. Nous l'avons appris à nos dépens en début de partie (+18 % de prix, demande Thermique divisée par deux).

### Ce que vaut la prévision de notre demande avant le tour (rejeu ex ante)

`python3 backtest.py --exante` rejoue chaque tour comme on le voyait en décidant : concurrents inconnus (scénarios), taille des marchés prévue, seules nos décisions marketing sont les vraies. Erreur de la médiane sur nos 6 produits, 20 scénarios par comportement, relevé du 20/11 :

| Notre état (ESG, qualité, certification) | Tour 2 | Tour 3 | Tour 4 | Tour 5 | Tour 6 | Réel dans P10-P90 |
|---|---|---|---|---|---|---|
| reconduit du tour précédent | 7,8 % | 43,6 % | 23,1 % | 9,8 % | 14,7 % | 63 % |
| saisi à la main dans les entrées du tour | — | — | 20,5 % | 12,0 % | 14,7 % | 78 % |
| prédit par `model/state.py` | 8,1 % | 44,5 % | 12,6 % | 12,6 % | 8,1 % | 77 % |
| réel (borne) | 9,1 % | 19,6 % | 12,2 % | 11,2 % | 8,0 % | 77 % |

- **Établi.** Notre propre état pèse autant que les décisions des concurrents : le reprendre du tour précédent coûte jusqu'à 30 points d'erreur. Le tour 3 reste imprévisible (première activation des impacts ESG, aucune donnée antérieure).
- **Probable.** Les six comportements de concurrents tirés par `strategy.py` sont bien centrés : avec notre état réel, biais de +1,5 % sur 30 cellules. Le statu quo seul surestime notre demande de 6 % (les concurrents s'améliorent d'un tour à l'autre). Ajouter la « règle apprise » ne change rien (erreur 11,3 % dans les deux cas) : non retenue.
- **Probable.** Paramètres du moteur pour une technologie peu observée : ceux de l'Hybride de la zone font mieux que des paramètres ajustés sur 1 à 3 observations (Électrique, tours 4 et 5 : 55, 9 et 47 % d'erreur contre 68, 10 et 59 %). Règle dans `sim.fit_params` : repli en dessous de 12 observations.
- **Établi.** Le rejeu aveugle habituel (section 11, première ligne) n'est pas une mesure de la prévision : il connaît les décisions réelles des 11 concurrents et notre état réel. Il mesure le moteur, pas l'usage que l'on en fait.
- Notre état tour par tour (impact ESG en log, qualité des fournisseurs, certification) : tour 2 : +0,07 / 3,5 / non ; tour 3 : −0,15 / 3,0 / non ; tour 4 : 0,00 / 3,5 / Bronze ; tour 5 : −0,04 / 4,33 / non ; tour 6 : +0,05 / 4,33 / non. Le passage du tour 2 au tour 3 valait à lui seul −30 % de demande ; la saisie du tour 4 (impact +0,15, certifié) était trop optimiste de 0,15.
- **Probable.** Les intervalles P10-P90 des scénarios sont bien calibrés pour un produit installé (18 cas sur 21 dans l'intervalle aux tours 2 à 5, avec notre état réel). Ils ne le sont pas pour un lancement : nos trois Hybrides lancés au tour 2 ont reçu moins que le P10, parce que 9 concurrents ont lancé le leur au même tour (3 vendeurs au tour 1, 11 à 12 au tour 2) et que le cadre « statu quo » ne contient que les produits du tour précédent.
- Tour 6, erreur de signe constant : la médiane était trop haute pour nos trois Thermiques (+14 %, +22 %, +21 %) et trop basse pour nos trois Hybrides (−13 %, −2 %, −7 %). C'est l'erreur de taille des marchés (chute du Thermique), pas celle du moteur.
- **Hypothèse.** L'incertitude sur notre propre impact ESG vaut environ 0,06 en log (erreur de prévision de 2 à 10 points selon le tour). `our_state_sd` l'ajoute aux scénarios ; elle n'y est pas par défaut.

## 6. Coûts et production

- **Établi.** Coût d'un équipement par véhicule : 700 USD (USA), 650 (Chine), 750 (Europe).
- **Établi.** Capacité : 200 k unités par usine aux USA, 250 k en Chine ; nous avons 9 et 5 usines. Une usine neuve coûte 1,2 Md USD (USA) ou 1,1 Md (Chine) et produit 2 tours plus tard. Amortissement dégressif 10 %.
- **Établi.** Les coûts changent fort d'un tour à l'autre : à relire chaque tour sur la page Planning. Au tour 6 la sous-traitance a renchéri de 20 à 30 % (Hybride Chine 21 666 USD) pendant que nos usines baissaient (Hybride Chine 17 922 USD, Thermique Chine 9 802 USD) : la sous-traitance n'est plus rentable que lorsque l'usine de Chine est pleine. Reprendre le plan de production du tour précédent aurait coûté environ 2 Md USD.
- **Établi.** Sous-traitance plafonnée par zone (tour 5 : 167 k aux USA, 484 k en Chine ; tour 6 : 189 k et 546 k). Pour l'Hybride elle coûte moins cher que nos usines (tour 5 : 18 000 USD en Chine contre 20 400 en interne, 19 600 contre 23 700 aux USA). Pour le Thermique, l'usine de Chine est moins chère (10 100 contre 12 100) et les deux se valent aux USA (13 100).
- **Établi.** Transport et droits de douane par véhicule au tour 5 : Chine → Europe 1 300 à 1 900 USD, Chine → USA 1 100 à 1 700, USA → Europe 2 600 à 3 600, USA → Chine 4 300 à 6 200. Produire en Chine pour l'Europe est la route la moins chère. Les droits changent avec les conditions de marché (Chine → Europe ramenés de 10 % à 7 % au tour 5).
- **Établi.** Fournisseurs de composants (page Achats) : le nombre de fournisseurs requis augmente avec le volume produit (3 au tour 5). En dessous, pénalité de 50 % sur le coût des composants, soit environ 3 800 USD par véhicule. Chaque fournisseur a un coût (5 250 à 8 500 USD), une qualité et une note de développement durable ; une étude à 5 M USD révèle les notes cachées. Sélectionner un nouveau fournisseur coûte 10 M USD.
- **Établi.** Les jours-homme de R&D non affectés sont payés quand même (500 USD par jour). L'affectation est remise à zéro à chaque tour : tout réaffecter, chaque tour.
- **Infirmé.** Pas d'économie d'échelle visible sur le coût de production interne du Thermique (élasticité au volume −0,01). Pour l'Hybride −0,07 à −0,15, sur 9 à 13 points seulement.
- **Établi.** Stocks : 650 à 800 USD par unité stockée, plus le coût du capital immobilisé (9 %). Le stock final se revend au tour suivant.
- **Établi.** Améliorations de processus (page Planning, cases à cocher, testées dans le prévisionnel au tour 5) : émissions de CO2, 7 M USD par usine et −20 % de capacité pendant le tour ; énergie, 11 M USD par usine et −15 % de capacité ; eau, 9 M USD par usine et +30 % de pertes pendant le tour. L'effet est cumulatif et définitif. Avec 14 usines, 98 à 154 M USD chacune : peu de chose face à un résultat de 16 Md USD, à condition que la capacité restante suffise (notre usine de Chine tourne à 96 %).
- **Établi.** Recyclabilité : 5 niveaux de directive ; le niveau 4 (« évaluation du cycle de vie ») ajoute 3 % au coût unitaire.

## 7. ESG, certifications, événements

C'est le groupe de leviers le plus rentable et celui que nous avions le plus négligé. `python3 -m model.esg` refait les tables.

- **Établi.** Chaque impact ESG est relatif à la moyenne des 12 équipes : impact % = 34 × (note de l'équipe / note moyenne − 1). Vérifié sur les fournisseurs, dont la note est publiée (pente 33,6 à 34,9 sur 4 tours, résidu inférieur à 0,2 point). La somme des impacts d'une composante sur les 12 équipes est nulle à chaque tour, et deux équipes aux décisions identiques reçoivent le même impact.
- **Établi.** Conséquence : une option gardée telle quelle perd de l'impact quand les autres équipes s'améliorent. « Conformité standard » : −1,9 %, −4,8 %, −5,6 % aux tours 3, 4, 5. Érosion habituelle d'environ 1 point par composante et par tour, plus forte le tour qui suit l'activation d'une composante.
- **Probable.** `model/state.py` prévoit notre impact ESG à partir de nos décisions : table du dernier tour pour la même option, effets additifs sinon, moitié de l'érosion observée. Rejeu aveugle sur les 12 équipes, erreur sur l'impact total : 10,5 / 3,8 / 1,9 points aux tours 4, 5, 6, contre 12,1 / 5,2 / 3,4 en reconduisant l'impact. Énergie renouvelable et améliorations de processus ne se prévoient pas ainsi (décisions non publiées) : niveau ou impact à saisir.
- **Établi.** Les notes des fournisseurs (qualité, développement durable) sont cachées avant le tour sauf étude, et changent d'un tour à l'autre : la loi relative appliquée à la note du tour précédent fait moins bien que l'impact reconduit.
- **Établi.** Image moyenne publiée par fournisseur, tours 2 à 5 : Maîtres Matérialistes 4,5 / 3,0 / 3,5 / 4,5 ; Fusions Dynamiques 4,0 / 3,5 / 4,0 / 5,0 ; Innovation Réinventée 3,5 / 3,0 / 3,25 / 3,25 ; Composants Colossaux 2,0 / 1,0 / 1,75 / 2,5 ; Singularités Quantiques 1,75 / 1,25 / 1,75 / 1,75. L'ordre ne change pas, le niveau si. Avec les mêmes fournisseurs notre qualité a valu 3,5 puis 3,0 puis 3,5.
- **Établi.** Les équipes convergent vers le même jeu de fournisseurs : Maîtres + Innovation pour 8 équipes au tour 3, Maîtres + Fusions + Innovation pour 9 équipes au tour 5. Quand presque tous ont le même, l'impact est proche de zéro (+0,7 %) : le levier ne paie que tant que l'on a une note d'avance, et coûte 2 à 6 % à ceux qui restent en arrière.
- **Établi.** Les composantes ESG se sont activées par étapes : rien au tour 1, les fournisseurs au tour 2, les sept composantes liées aux décisions au tour 3. Le tour d'activation est le plus coûteux pour qui n'a pas bougé : −7,8 % (énergie) et −8,2 % (processus) pour nous au tour 3, pendant que la moitié des équipes avait déjà agi.
- **Établi.** Ce qui entre dans la demande, d'après le moteur : la somme des sept composantes liées aux décisions (énergie renouvelable, recyclabilité, processus, formation, politiques du travail, politiques des fournisseurs, rémunération). Les trois composantes de résultat (impact des unités vendues, efficacité opérationnelle, rotation) sont publiées mais n'améliorent pas le rejeu.

- **Établi.** Le rapport ESG publie pour chaque équipe l'impact en % de dix composantes sur sa demande. Ces impacts sont relatifs aux concurrents : faire comme tout le monde rapporte peu (énergie renouvelable à 100 % : +1,3 % au tour 5 quand presque tous y sont), être en retard coûte cher (−4 à −9 %).
- **Établi.** La somme des dix impacts va de −15 % à +27 % selon l'équipe au tour 5. Ren'Auto, leader du classement, est à +27 % ; nous étions à −7,9 % (9ᵉ sur 12).

| Levier | Niveau | Ce que disent les 12 équipes |
|---|---|---|
| Priorités de formation | **Établi** | Cocher la seule priorité « éthique et lutte contre la corruption » : +11,7, +9,7, +8,0 et +8,0 points (4 observations sur 3 tours). Vérifié sur nous au tour 6 : impact formation de −3,0 à +6,6, score social de 2,32 à 3,47. Contrepartie mesurée : la R&D a livré environ 10 % de moins que les jours-homme affectés. Cocher beaucoup de priorités dilue l'effet (0 à −3). La « formation de base » pèse −5,7 points en régression. Coût nul dans le prévisionnel ; contrepartie attendue : efficacité de la R&D un peu plus faible (coefficient de productivité 1,07 contre 1,13 en moyenne chez ceux qui l'ont fait). Joué au tour 6. |
| Politique « règlement du travail » | **Probable** | Partenariat stratégique +5 points par rapport à l'engagement communautaire ; conformité standard −4,4. Le partenariat exige un score ESG d'au moins 3,0. |
| Quotas de direction | **Hypothèse** | Programmes de mentorat +1,0 point (4 observations). Coût nul. Joué au tour 6. |
| Améliorations de processus | **Probable** | Impact de −8 à +21 points selon le nombre d'améliorations faites par rapport aux autres. Chaque amélioration vaut plusieurs points ; « eau » ne coûte que 104 M USD et n'enlève pas de capacité. |
| Énergie renouvelable | **Probable** | 100 % dans les deux usines : +1,3 à +12,8 selon ce que font les autres ; en dessous : −4 à −9. Passer de 100 % à 0 % n'économise que 150 M USD. |
| Recyclabilité | **Probable** | Cycle fermé + engagement +3,0 (mais 629 M USD) ; cycle de vie + engagement +1,5 (coût nul) ; matériaux recyclés −1,4 ; recyclage de base −4,3. L'engagement n'est accepté qu'avec les deux directives les plus hautes. |
| Fournisseurs | **Probable** | Loi exacte : impact = 34 × (note « développement durable » moyenne de nos fournisseurs / moyenne des 12 équipes − 1), soit 8 à 12 points par point de note selon le tour (la régression tous tours confondus donnait 5,2, trop peu). L'effet qualité s'y ajoute. Notes publiées par fournisseur (image) : Fusions Dynamiques 4,0 ; Maîtres Matérialistes 3,5 ; Innovation Réinventée 3,25 ; les deux moins chers 1,75. |
| Productivité des ingénieurs | **Probable** | Critère noté. Variation du coefficient d'un tour à l'autre, 72 observations (12 équipes, tours 2 à 7) : dérive commune +0,02 ; formation de base activée +0,06 ; formation de base retirée −0,16 (nous et BM2P au tour 6, IronHorse au tour 7) ; −0,02 par autre priorité ajoutée. En marche avant : erreur 0,042 contre 0,045 en reconduisant le coefficient, 2,2 points de barème contre 2,6 (`python3 objectif.py --tour 8 --productivite`). Le salaire, le budget de formation et la rotation n'améliorent pas ce rejeu : aucun effet mesurable (Ren'Auto paie 25 000 USD et gagne +0,03 par tour, comme les autres). |
| Salaire et rotation | **Probable** | L'impact « rotation » est positif (+0,6 à +2,8) chez les équipes à 6 000 USD de salaire et plus, négatif en dessous (nous : −2,2 à 5 800 USD). L'impact « rémunération » lui-même est nul (±0,1). |

- **Établi.** Certification : score ESG cumulé requis 2,75 (Bronze, 8 M USD), 3,25 (Argent, 24 M), 4,00 (Or, 40 M). Le score cumulé est la moyenne des scores E, S et G du tour précédent. Le menu ne propose que les niveaux atteints : à 2,72 (tours 5 et 6) il n'offrait que « pas de certification » ; à 3,10 (tour 7) il offre le Bronze, pris.
- **Établi.** Un score ESG d'au moins 3,0 est exigé par la plateforme pour toute « coopération avancée » : partenariat stratégique, collaboration syndicale, co-développement (batteries, qualité). En dessous, ces options sont refusées à la saisie. Une fois permises, elles ne sont pas forcément rentables : le partenariat stratégique coûtait 2 041 M USD au tour 7.
- **Établi.** Une option présélectionnée d'un nouvel événement n'est pas la moins chère : au tour 7, « participation partielle » à l'approvisionnement durable coûtait 882 M USD de plus que « engagement total ».
- **Établi.** Politique « initiatives d'engagement communautaire » : consomme 150 000 jours-homme de R&D par tour.
- **Établi.** Événements : une décision par événement, effets durables, et la liste change (tour 5 : transparence, prêt écologique, batteries ; tour 6 : prêt écologique, dilemme de la qualité, batteries). Le prêt écologique accepté au tour 4 exige un score ESG de 3 ou plus, sinon le taux monte : dette remboursée au tour 6. Coût des options au tour 6 : batteries sous-traitées −804 M USD ; fournisseur alternatif « douteux » +72 M USD.
- L'effet des options d'événement sur la demande n'est pas publié par équipe : inconnu.

## 8. Finance et impôts

- **Établi.** Trois entités (USA maison mère, Chine, Europe). L'Europe encaisse sans produire : la trésorerie s'y accumule. Sans transferts internes, les USA et la Chine tombent en découvert (dette à court terme imprévue, taux majoré de 1 point).
- **Établi.** Taux au tour 5 : dette long terme 4,2 %, court terme 5,2 à 6,6 % ; rémunération de la trésorerie 3,2 % (USA), 4,2 % (Chine), 1,0 % (Europe). Impôt : USA 20 %, Chine 24 %, Europe 21 %.
- **Établi.** Les prix de transfert (1,00 à 2,00) déplacent le bénéfice entre entités : utiles quand une entité a des pertes reportables, sinon les droits de douane supplémentaires l'emportent.
- **Établi.** Le prévisionnel de la plateforme calcule exactement coûts, impôts et trésorerie, mais pas la demande : il applique les parts de marché qu'on lui saisit.
- La notation de crédit suit le ratio de fonds propres et la dette nette (nous : B+ au tour 2, BBB− au tour 3, AA au tour 4).
- **Établi (20/11).** La marge opérationnelle notée d'une entité est son EBIT divisé par son chiffre d'affaires total, cessions internes comprises : 12,217 / 12,652 / 41,643 % recalculés au tour 7 pour 12,217 / 12,652 / 41,643 publiés. Un prix de transfert déplace donc à la fois le numérateur et le dénominateur des entités qui produisent (USA, Chine), et seulement le numérateur de l'Europe.
- **Établi (20/11).** Les cessions internes changent fort d'un tour à l'autre avec le plan de production : Chine 21,0 Md USD au tour 7 et 5,2 au tour 8, USA 0 puis 8,8. La marge d'une entité calculée avec les cessions du tour précédent est fausse de plus de 10 points (Chine : 14 % au lieu de 27 % au tour 8).
- **Établi (20/11).** La page Impôts du prévisionnel a des onglets (compte de résultat et bilan par entité, ratios) : `oracle.previsionnel` les lit sans rien modifier. On y trouve la trésorerie de fin de tour de chaque entité (c'est elle, et non la trésorerie globale, qui décide d'un découvert), les fonds propres, les dettes, le ROE et le bénéfice par action prévus.

## 9. Comportement des concurrents

- **Établi.** D'un tour à l'autre, 46 % des prix montent, 19 % ne bougent pas, 21 % baissent. Hausse moyenne : +1 à +4 % par tour en Thermique, +7 à +9 % en Hybride (sauf au tour 3).
- **Établi.** Les équipements montent à chaque tour : en moyenne +0,6 à +1,1 par tour en Thermique, +1,6 à +3 en Hybride. Le maximum de 10 est atteint par certains dès le tour 1 en Thermique, dès le tour 3 en Hybride.
- **Établi.** Tous les concurrents vendent de l'Hybride depuis le tour 2. Électrique : 2 vendeurs au tour 4, 5 au tour 5 en Chine, 2 en Europe. Un seul a tenté l'Hydrogène (tour 5).
- **Établi.** Au tour 5, certains ont déjà quitté le Thermique (9 vendeurs en Chine, 11 ailleurs).
- **Probable.** Statu quo et prolongement de tendance prédisent mal les décisions individuelles ; l'optimiseur tire donc plusieurs comportements (`model/rivals.py`) et retient une stratégie à faible regret.
- **Établi.** Erreur moyenne de chaque comportement simulé sur les décisions réelles des concurrents, tours 3 et 4 : statu quo, prix à 6,3 et 7,2 %, équipements à 1,4 et 1,1 près ; règle apprise sur les tours passés 5,9 et 7,0 % ; tendance prolongée 7,4 et 9,2 % ; montée en gamme 8,2 et 6,4 % ; guerre des prix 11 et 14 % ; meilleure réponse 11 % ; équilibre 15 et 18 % (il pousse les prix 12 à 16 % trop haut et la publicité à plus du double). Les concurrents ne jouent pas l'optimum du moteur.
- **Établi.** Le statu quo sous-estime les équipements des concurrents de 1,0 à 1,4 par tour, et ne voit pas leurs progrès hors marketing : 62 % de concurrents certifiés en plus au tour 3, qualité des fournisseurs en hausse de 28 % au tour 4. Ces progrès expliquent les 6 points de biais du statu quo sur notre demande.
- **Établi.** Les concurrents entrent en groupe sur une technologie dès qu'elle paie ou qu'elle devient nécessaire : Hybride, 3 vendeurs au tour 1 et 11 à 12 au tour 2 ; Électrique en Europe, 2 vendeurs au tour 5 et 7 au tour 6. Vendeurs de Thermique : 12 / 11 / 12 (USA, Chine, Europe) au tour 4, 11 / 9 / 11 au tour 5, 10 / 7 / 7 au tour 6.
- Le leader, Ren'Auto, vend cher, cumule +27 % d'impact ESG, a une certification Argent, paie 10 000 USD ses ingénieurs et n'avait aucune rotation du personnel aux tours 3 et 4.
- POLRAMOS montre les deux extrêmes au même tour : 20,8 Md USD de marge sur l'Électrique en Europe, et un retour cumulé divisé par trois après un gros dividende et 3,7 Md USD perdus sur l'Hydrogène.

- **Établi (tour 7).** Changement de gamme : avec une place libre, un concurrent a lancé une technologie déjà vendue ailleurs 62 fois sur 100, une technologie jamais vendue 48 fois sur 100 (46 et 31 sur les tours 4 à 7). Échange d'un modèle vivant contre un autre : 15 % (13 occasions). `rivals.changement_de_gamme` ; en aveugle il prévoit 7 / 3 / 4 vendeurs pour 10 / 6 / 8 réels.
- **Établi (tour 8).** Nouveaux leviers : service client (garantie 1 à 5 ans, données clients notées en points Social relatifs à la moyenne), liquidation d'un stock sans vente (7 614 USD par Thermique), retour du prêt écologique, certification Argent ouverte à 3,34. Détail : `out/tour8_alignement.md`.

- **Infirmé (20/11, rejeu en marche avant des tours 4 à 7 ; script non conservé).** Un agent par équipe, appris sur ses décisions passées et son état (variations précédentes, ruptures, prix et équipements relatifs, variation de part, technologie, style propre de l'équipe), ne prévoit pas mieux les décisions que le statu quo : 9,3 % d'erreur sur les prix contre 8,3 %, 1,3 équipement contre 0,9, publicité 27 contre 20. Le style propre à une équipe dégrade toujours la prévision (7 tours, 30 à 40 observations par équipe). Les équipes aux décisions extrêmes (BM2P, MO'THOR, Ren'Auto : 18 à 26 % d'erreur au tour 7) restent imprévisibles.
- **Probable (même rejeu).** Seule régularité exploitable : un produit plus cher que le prix médian de sa cellule baisse son prix au tour suivant, un produit en rupture le monte (coefficient −0,38 sur le log du prix relatif). Appliquée à moitié, sans style d'équipe, elle ramène l'erreur sur les prix à 7,9 % (6,4 / 5,4 / 10,3 / 9,4 % aux tours 4 à 7, contre 7,2 / 5,6 / 10,6 / 9,8 %). Au tour 8, elle ne changeait pas le classement de nos décisions candidates (168,4 points attendus contre 167,8 avec les six comportements). Piste abandonnée le 20/11 : `agents.py` a été supprimé, la recherche garde les six comportements de `model/rivals.py`.

## 10. Ce que l'on ne sait pas encore

- Pourquoi le marché européen a grossi de 15,8 % au tour 5.
- Si la demande d'une technologie suit sa couverture en proportion dans tous les cas : vrai pour le Thermique au tour 6, faux en Europe au tour 5. Le tour 7 (Hybride à 55 %) tranchera.
- Quelle part de la demande perdue par une technologie se reporte sur les autres, et sur lesquelles (0 à 90 % selon la zone au tour 6).
- Comment prévoir un saut d'attrait du scénario (Hybride au tour 3, Électrique en Chine et Hydrogène aux USA au tour 6) autrement que par la phrase des conditions de marché.
- L'impact attendu de l'énergie renouvelable et des améliorations de processus pour un niveau donné : les décisions des équipes ne sont pas publiées, seul l'impact l'est.
- La taille des marchés Électrique et Hydrogène après la fin du Thermique, et le nombre de vendeurs qui s'y reportent (tour 7 : première observation à venir).
- La demande d'Électrique en fonction du prix, des équipements et de la publicité : une dizaine d'observations, dont deux seulement en Europe.
- Si la demande non servie d'une équipe en rupture est perdue ou reportée sur ses concurrents dans le même tour.
- L'écart d'effet entre certifications Bronze, Argent et Or.
- L'effet des options d'événement et des options jamais jouées (conformité minimale, recrutement aveugle, efficacité accrue en R&D).
- Ce à quoi oblige exactement l'« engagement » de recyclabilité aux tours suivants.

## 11. Comment revérifier

| Affirmation | Test |
|---|---|
| Répartition entre équipes, chaîne complète | `python3 backtest.py -v` (une minute depuis le 20/11) |
| Taille des marchés, partage entre technologies | `python3 -m model.market` (rejeu aveugle des 3 méthodes, table des attraits) |
| Utilité d'un mécanisme du moteur | le neutraliser dans `sim.shared_free` ou `engine.fit_joint(group_free=...)` et comparer l'erreur aveugle |
| Effets ESG, RH, fournisseurs | `python3 -m model.esg` |
| Prévision de notre demande dans les conditions réelles | `python3 backtest.py --exante` (`--candidats` pour comparer des jeux de comportements) |
| Prévision de notre impact ESG à partir de nos décisions | `python3 -m model.state` |
| Changement de technologie d'un modèle | `python3 offre.py --tour N` (preuve faible : 2 à 7 vendeurs par cellule) |
| Cours de l'action | régression du cours sur fonds propres et bénéfice par action, avec `model/report.py` |
| Équipes jumelles | chercher dans `model.panel2.build()` des lignes de même cellule aux prix, équipements et publicité identiques |
| Coût d'une option, option refusée | `oracle.Oracle(N).evaluate({champ: valeur})` : saisit dans la zone personnelle, lit le prévisionnel, restaure |
| Champs et options apparus | `python3 -m cesim.inputs N`, puis `python3 leviers.py N` |

## 12. Affirmations de départ et verdict

Trois idées étaient à vérifier au départ.

- « L'élasticité des prix » : **confirmée et chiffrée** (section 5). Elle diffère d'une zone à l'autre, du simple au double.
- « La publicité d'un produit impacte peut-être les autres » : **confirmée pour l'autre produit de la même équipe sur le même marché** (29 %), nette aux USA et en Chine, non démontrée en Europe. Aucun indice d'un effet d'une zone sur une autre.
- « Le déterminisme de certains marchés » : **confirmé pour la répartition entre équipes** (aucun aléa, équipes jumelles identiques). **Faux pour la taille des marchés** : elle ne se déduit pas de la seule croissance annoncée, elle dépend aussi des décisions collectives et de sauts d'attrait décidés par le scénario.

## 13. Pièges de la plateforme

- Les décisions de l'équipe au début d'un tour sont celles du tour précédent, sauf la R&D (remise à zéro) et les améliorations de processus (cases décochées).
- Le prévisionnel ne calcule pas la demande : il applique les parts de marché saisies page Demande. Toujours y reporter les parts du simulateur avant de lire un résultat.
- Changer la technologie d'un modèle efface son marketing (prix, publicité, équipements, part estimée), même si l'on revient aussitôt en arrière.
- Juste après une saisie, une page peut être rendue sans ses champs pendant une ou deux secondes : `oracle.py` réessaie, et `Oracle.resync()` remet toute la zone dans un état donné.
- L'instructeur peut bloquer décisions et résultats après une clôture (12 minutes après le tour 5, pour le débrief). Le tour suivant est déjà décompté pendant ce temps.
- Une option refusée (condition non remplie) ne provoque pas d'erreur visible : le champ garde simplement son ancienne valeur. `oracle.py` le détecte et rapporte le message.

