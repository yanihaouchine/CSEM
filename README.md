# CSEM — simulateur et optimiseur pour Cesim Global Challenge

Outils écrits pour piloter l'équipe « tomobil » dans une session de [Cesim Global Challenge](https://www.cesim.com/fr/simulations/cesim-global-challenge-simulation-de-management-strategique-international) (cas automobile) à Bordeaux INP : 12 équipes, 3 marchés (USA, Chine, Europe), 4 technologies (Thermique, Hybride, Électrique, Hydrogène), 10 tours.

Le dépôt contient trois choses :

- un **simulateur** du jeu, reconstruit à partir des résultats publiés après chaque tour (décisions et résultats des 12 équipes) ;
- un **optimiseur** qui s'en sert pour proposer les décisions du tour suivant ;
- un **client** pour la plateforme : téléchargement des résultats, relevé des pages de décision, lecture du prévisionnel financier.

Ce que l'on a appris du jeu lui-même (demande, technologies, coûts, ESG, cours de l'action) est consigné dans [`docs/comportement.md`](docs/comportement.md), avec un niveau de preuve pour chaque affirmation.

## Ce que l'on cherche à maximiser

Le classement de la session n'est pas le retour aux actionnaires affiché par la plateforme, mais un barème de l'instructeur : à chaque tour, les équipes sont rangées sur une vingtaine de critères (ROE, marges opérationnelles et parts de marché par zone, coûts unitaires, stocks, demande non servie, scores ESG, certification…) et reçoivent de 1 à 12 points par critère. Seul le rang compte, et tous les critères pèsent autant.

`model/points.py` recalcule ces critères depuis les rapports et applique la règle des points (2 écarts sur 252 attributions au tour 4, 2 sur 264 au tour 5). `objectif.py` en fait la fonction objectif : l'espérance de nos points pour une décision donnée, les onze concurrents étant repris du dernier tour avec un bruit mesuré sur l'historique.

## Méthode

Une boucle par tour :

1. **Résultats.** `cesim.scrape` télécharge le tour qui vient de sortir, `model.panel` reconstruit le panel (une ligne par tour, zone, technologie, équipe).
2. **Rejeu.** `backtest.py` rejoue les tours passés avec un moteur calé sur les tours antérieurs seulement. Aucune recommandation n'est faite avant d'avoir regardé ce rejeu.
3. **Recherche.** Prix, équipements et publicité sont cherchés ensemble dans des zones de confiance autour des décisions précédentes ; la production est un programme linéaire sur un quantile de la demande simulée ; fournisseurs, ESG, RH et finance sont énumérés, avec les coûts lus sur le prévisionnel de la plateforme.
4. **Décision.** On ne joue pas l'optimum brut : le point retenu est celui qui garde le meilleur gain dans le pire de trois mondes (moteur tel quel, clients 30 % plus sensibles au prix, marchés 15 % plus petits).

Le simulateur a plusieurs étages :

| Étage | Fichier | Rôle |
|---|---|---|
| Taille des marchés | `model/market.py` | total par zone et partage entre technologies |
| Répartition entre équipes | `model/engine.py` | attraction de chaque produit (prix, équipements, publicité, ESG, fournisseurs, inertie) |
| Tour complet | `model/sim.py` | décisions des 12 équipes → demande, ventes, marge |
| Concurrents | `model/rivals.py` | comportements possibles des 11 autres équipes |
| Notre état | `model/state.py`, `model/esg.py` | impact ESG, qualité fournisseurs, certification déduits de nos décisions |
| Barème | `model/points.py`, `model/classement.py` | critères et points de l'instructeur |

## Ce que vaut le simulateur

Erreur moyenne sur les volumes en rejeu aveugle (`python3 backtest.py`, décisions des concurrents connues) :

| Tour | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|
| Répartition entre équipes (%) | 7,4 | 9,3 | 4,5 | 6,7 | 6,9 | 7,2 | 11,4 | 13,3 |
| Chaîne complète, taille des marchés comprise (%) | 9,1 | 18,2 | 8,3 | 14,9 | 22,6 | 26,4 | 18,2 | 21,7 |

La répartition entre équipes est bien reproduite. La taille des marchés est le maillon faible : le scénario du jeu modifie l'attrait des technologies d'un tour à l'autre, et l'erreur a grimpé quand le Thermique a été retiré du marché (tours 6 et 7).

Côté résultats, l'objectif en points a été adopté au tour 8. Nous avons fini 1ᵉʳ du tour 6 (171 points) et 3ᵉ du tour 7 (149), puis 130 et 126 points aux tours 8 et 9, où la demande a été surestimée (de 30 % au tour 9). Les fiches de `out/` détaillent chaque tour, erreurs comprises.

Limites connues :

- les décisions des concurrents ne sont pas connues avant le tour ; la prévision de notre propre demande vaut 8 à 23 % d'erreur selon les tours (`python3 backtest.py --exante`) ;
- les coûts ne sont pas simulés : ils sont lus sur la plateforme pour nous et repris du dernier rapport pour les concurrents ;
- Électrique et Hydrogène ont peu d'historique, le moteur y emploie les paramètres de l'Hybride ;
- R&D, licences et investissements en usines sont réglés à la main.

## Installation

Python 3.12, puis :

```
pip install -r requirements.txt
```

`model/classement.py` appelle `pdftotext` (paquet `poppler-utils`) pour lire les classements publiés en PDF.

## Utilisation

Tout ce qui suit fonctionne hors ligne, sur les données du dépôt :

```
python3 -m model.panel           # reconstruit data/panel.csv depuis data/raw/
python3 backtest.py -v           # rejeu calé et aveugle de tous les tours (environ 3 minutes)
python3 backtest.py --exante     # prévision de notre demande dans les conditions réelles
python3 -m model.market          # rejeu de l'étage « taille des marchés »
python3 -m model.points          # rejeu du barème et tableau « où sont les points »
python3 leviers.py 10            # registre des champs de décision du tour 10
python3 tour_final.py 10         # décisions proposées pour le tour 10
python3 offre.py --tour 10       # comparaison des technologies possibles pour nos modèles
python3 optimise_tout.py --tour 10 --sec   # recherche sans la plateforme
```

Les entrées propres à un tour (croissance annoncée, taux de change, coûts unitaires, bornes de recherche) sont dans `data/tour_N_inputs.json`.

Les commandes qui parlent à la plateforme demandent un compte dans une session ouverte :

```
export CESIM_USER=...  CESIM_PASSWORD=...  CESIM_ZONE=...   # ou un fichier identifiant.md, non suivi
python3 -m cesim.scrape          # télécharge les tours manquants
python3 -m cesim.inputs N        # relevé des pages de décision et des nouveautés du tour N
python3 optimise_tout.py --tour N --etapes D E
python3 -m cesim.save_team tourN # enregistre la zone personnelle comme décisions de l'équipe
```

`oracle.Oracle` ne travaille que dans la zone de décisions personnelle et la remet dans son état de départ ; seul `cesim.save_team` touche aux décisions de l'équipe.

## Organisation

```
cesim/            client de la plateforme (connexion, relevés, enregistrement)
model/            simulateur et barème
strategy.py       scénarios, frontière marketing, plan de production
objectif.py       points attendus d'une décision
oracle.py         prévisionnel de la plateforme utilisé comme calculateur de coûts
optimise_tout.py  recherche sur tous les leviers, par étapes
tour_final.py     décisions proposées pour un tour
offre.py          choix de la technologie de chaque modèle
leviers.py        registre des champs de décision
backtest.py       rejeu du simulateur
exante.py         rejeu de la prévision de notre demande
data/             résultats par tour (raw/), panel, entrées de chaque tour
out/              fiches de décision par tour (tourN_recommandation.md) et sorties des recherches
docs/             mécanismes du jeu
```

Les supports du cours, les forums et les sauvegardes des pages de décision ne sont pas dans le dépôt ; quelques fiches de `out/` y font référence.
