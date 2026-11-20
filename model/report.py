"""Accès générique aux rapports de résultats : n'importe quelle ligne, pour les 12 équipes, à n'importe quel tour.

  from model.report import table
  table("Coût de production interne par unité, USD > Chine > Hybride")   # tours x équipes

Le chemin est la suite des intitulés (sections puis ligne), séparés par « > » ; on peut n'en donner que la fin.
"""
import json

import numpy as np
import pandas as pd

from cesim.client import ROOT
from model.panel import available_rounds, num


TECHS = ("Thermique", "Hybride", "Électrique", "Hydrogène")
ZONES = ("USA", "Chine", "Europe")


def lines(idx):
    """Liste (chemin, valeurs des 12 équipes) pour le tour d'indice `idx`.

    chemin = (rapport, rubrique[, zone], ligne). Une ligne sans valeur est une rubrique, sauf une technologie
    que personne ne produit (ligne vide au milieu de ses voisines)."""
    R = [r for r in json.load(open(ROOT / "data" / "raw" / f"round_{idx}.json")) if r and len(r) >= 13]
    teams = next(r[1:13] for r in R if r[1] == "Ren'Auto")
    out, top, sub, zone = [], None, None, None
    for i, r in enumerate(R):
        lab, txt = r[0], [c.strip() for c in r[1:13]]
        if not lab:
            continue
        if all(c == "" for c in txt):
            nxt = next((q for q in R[i + 1:i + 3] if q[0] or q[1] == "Ren'Auto"), None)
            if nxt is not None and nxt[1] == "Ren'Auto":            # titre de rapport, suivi de l'en-tête des équipes
                top, sub, zone = lab, None, None
            elif lab in ZONES and sub is not None:
                zone = lab
            elif lab in TECHS and not (nxt is not None and nxt[0].startswith(("Prix de vente", "Chiffre d'affaires"))):
                out.append(((top, sub, zone, lab) if zone else (top, sub, lab), [np.nan] * 12))   # technologie absente
            else:
                sub, zone = lab, None
            continue
        vals = [num(c) for c in txt]
        path = tuple(x for x in (top, sub, zone, lab) if x)
        out.append((path, txt if all(np.isnan(vals)) else vals))
    return teams, out


def table(path, rounds=None):
    """Tableau tours x équipes de la première ligne dont le chemin se termine par `path`."""
    want = [p.strip() for p in path.split(">")]
    rows = {}
    for idx in rounds or available_rounds():
        teams, L = lines(idx)
        for p, v in L:
            if list(p[-len(want):]) == want or (len(want) == 1 and p[-1].startswith(want[0])):
                rows[idx] = pd.Series(v, index=teams)
                break
    return pd.DataFrame(rows).T


def find(word, idx=None):
    """Chemins contenant `word` (pour retrouver l'intitulé exact d'une ligne)."""
    idx = idx if idx is not None else available_rounds()[-1]
    return [" > ".join(p) for p, _ in lines(idx)[1] if word.lower() in " > ".join(p).lower()]
