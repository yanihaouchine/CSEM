# Tour 4 — recommandation (équipe tomobil)

Saisie dans la zone personnelle le 19/11 à 11h51. Les décisions d'équipe ne sont pas modifiées.

| Zone | Tech | Prix (avant → après) | Équipements | Publicité, M USD | Demande attendue, k unités (P10–P90) | PDM saisie, % |
|---|---|---|---|---|---|---|
| USA | Thermique | 19 900 → 19 500 USD | 5 | 900 → 800 | 609 (462–762) | 6,1 |
| USA | Hybride | 33 500 → 37 000 USD | 6 | 450 → 300 | 254 (190–325) | 2,5 |
| Chine | Thermique | 126 000 → 129 000 RMB | 6 | 500 → 450 | 488 (377–609) | 5,6 |
| Chine | Hybride | 215 000 → 230 000 RMB | 6 | 400 → 250 | 262 (189–334) | 3,0 |
| Europe | Thermique | 20 900 → 23 000 EUR | 5 | 450 → 750 | 625 (490–770) | 5,3 |
| Europe | Hybride | 32 000 → 35 000 EUR | 6 | 350 → 300 | 315 (244–400) | 2,7 |

Production : sous-traitance Hybride Chine 280 → 428 k (maximum, 19 900 USD pièce contre 23 200 en interne), ligne 2 Chine 45 % → 41 %. Le reste est inchangé.

Prévisionnel de la plateforme (résultat net, k USD), à hypothèses de demande égales (celles du modèle) :

- décisions d'origine : 8 348 573, avec 239 k Hybrides non livrés aux USA ;
- recommandation : 11 219 296, sans rupture.

Avec les parts de marché saisies à l'origine, les décisions d'origine donnaient 7 664 860.

Pour revenir en arrière : `python3 oracle.py original`, puis sous-traitance 280 et ligne 2 à 45 %.

## Test de rejeu sur les tours passés (première version du rejeu)

Le simulateur reçoit les décisions réelles des 12 équipes ; en mode aveugle il n'est calibré que sur les tours antérieurs.
Il ne reproduit pas exactement les classements : erreur de volume de 16 à 17 %, 8 équipes sur 12 à un rang près sur la marge.
Conséquence : on n'utilise que ses conclusions de direction (prix), pas ses chiffres. La hausse d'équipements en Europe, non confirmée par le rejeu, a été retirée.
