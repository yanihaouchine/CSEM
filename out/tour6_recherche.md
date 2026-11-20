# Tour 6 — recherche sur l'ensemble des leviers

## Étape 0 — couverture des leviers

```
Tour 6 : 121 champs de décision
  A offre          10  technologie d'un modèle dans une zone, technologie d'une ligne de production
  B marketing      18  prix, équipements, publicité d'un produit
  C production     12  part de capacité d'une ligne, priorités de livraison, quantité sous-traitée
  D discrets       31  amélioration de processus, certification développement durable, fournisseur actif, part d'énergie renouvelable, politique de travail, priorité de formation, recyclabilité et engagement, salaire et budget de formation, étude d'un fournisseur, événement
  E finance         9  dette, dividende, transfert interne, prix de transfert, émission ou rachat d'actions
  F multi-tours    11  achat de licence, achat ou cession d'usines, effectif de R&D, jours-homme de R&D par technologie
  estimation       18  croissance estimée, demande future estimée, départs volontaires estimés, part de marché estimée
  hors recherche   12  licence entre équipes
```

## Étape E — finance et impôts

Référence (avec les choix de l'étape D) : résultat net 17752 M USD, dette à court terme nouvelle [0.0], trésorerie de fin [17777089.0].

### Prix de transfert

| Champ | Valeur | Résultat net, M USD | Écart |
|---|---|---|---|
| transfer.us.to.asia | 1.00 | 17752 | +0 |
| transfer.us.to.asia | 1.25 | 17752 | +0 |
| transfer.us.to.asia | 1.50 | 17752 | +0 |
| transfer.us.to.asia | 1.75 | 17752 | +0 |
| transfer.us.to.asia | 2.00 | 17752 | +0 |
| transfer.us.to.eu | 1.00 | 17752 | +0 |
| transfer.us.to.eu | 1.25 | 17728 | -23 |
| transfer.us.to.eu | 1.50 | 17705 | -47 |
| transfer.us.to.eu | 1.75 | 17682 | -70 |
| transfer.us.to.eu | 2.00 | 17658 | -94 |
| transfer.asia.to.us | 1.00 | 17752 | +0 |
| transfer.asia.to.us | 1.25 | 17752 | +0 |
| transfer.asia.to.us | 1.50 | 17752 | +0 |
| transfer.asia.to.us | 1.75 | 17752 | +0 |
| transfer.asia.to.us | 2.00 | 17752 | +0 |
| transfer.asia.to.eu | 1.00 | 17752 | +0 |
| transfer.asia.to.eu | 1.25 | 17522 | -230 |
| transfer.asia.to.eu | 1.50 | 17292 | -460 |
| transfer.asia.to.eu | 1.75 | 17026 | -726 |
| transfer.asia.to.eu | 2.00 | 16748 | -1004 |

### Dette à long terme (encours 4.4 Md USD)

| Variation, k USD | Résultat net, M USD | Dette court terme nouvelle | Trésorerie de fin |
|---|---|---|---|
| -4400000 | 17752 | [0.0] | [17777089.0] |
| -2200000 | 17743 | [0.0] | [19968085.0] |
| 0 | 17734 | [0.0] | [22159082.0] |

### Transfert interne cash.us.to.asia

| Montant, k USD | Résultat net, M USD | Dette court terme nouvelle |
|---|---|---|
| 2000000 | 17739 | [0.0] |
| 4000000 | 17745 | [0.0] |
| 6000000 | 17752 | [0.0] |
| 8000000 | 17758 | [0.0] |
| 10000000 | 17765 | [0.0] |

### Transfert interne cash.us.to.eu

| Montant, k USD | Résultat net, M USD | Dette court terme nouvelle |
|---|---|---|
| -15000000 | 17801 | [0.0] |
| -13000000 | 17783 | [0.0] |
| -11000000 | 17765 | [0.0] |
| -9000000 | 17747 | [0.0] |
| -7000000 | 17729 | [0.0] |

Choix de l'étape E : {'cash.us.to.asia': 10000000, 'cash.us.to.eu': -15000000} ; résultat net 17801 M USD.

Dividendes : non cherchés (aucune équipe n'en a versé, effet sur le cours inconnu) ; laissés à 0.

Zone personnelle restaurée. 33 évaluations sur la plateforme.

Durée : 174 s.