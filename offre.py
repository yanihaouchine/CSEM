"""Comparaison d'offres : quelle technologie pour chaque modèle, dans chaque zone ?

  python3 offre.py --tour 6                                   # une zone à la fois : chaque changement permis
  python3 offre.py --tour 6 --offre '{"Europe": ["Électrique", "Hybride"]}'

`strategy.py` n'optimise que l'offre en place (Thermique + Hybride). Ici on rejoue la même recherche pour une
autre offre : le produit remplacé sort du cadre, le nouveau y entre (model/sim.with_products), la taille de sa
cellule vient de model/market.py (couverture du réseau, nombre de vendeurs) et sa part du moteur, avec les
paramètres Hybride de la zone quand la technologie est trop peu observée (sim.params_for).

Ce que vaut le résultat : PREUVE FAIBLE pour l'Électrique et l'Hydrogène (2 à 5 vendeurs par cellule, 3 tours).
Le tableau donne donc aussi la marge si N concurrents entrent en même temps dans la cellule (`--entrants`) :
au tour 7, quand le Thermique sera interdit, les 12 équipes devront déplacer leur modèle 1.
Coût unitaire d'un nouveau produit : `mc["zone|tech"]` des entrées du tour s'il y est (lu sur la plateforme),
sinon le coût médian des concurrents qui vendent déjà cette technologie dans la zone (signalé dans la sortie).
Aucune décision n'est saisie : le programme compare, la décision se prend ensuite.
"""
import argparse
import json
import warnings

import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution

import strategy as S
from cesim.client import ROOT
from model import sim
from model.panel2 import build

warnings.filterwarnings("ignore")
US = sim.US
ORDER = ["Thermique", "Hybride", "Électrique", "Hydrogène"]
MODELES = (("Thermique", "Électrique"), ("Hybride", "Électrique"))     # choix permis pour le modèle 1 et le modèle 2
BEHAVIOURS = ["statu quo", "tendance", "guerre des prix", "montée en gamme", "meilleure réponse", "mélange"]


def sort_cells(cells):
    return sorted(cells, key=lambda c: (S.REGIONS.index(c.split("|")[0]), ORDER.index(c.split("|")[1])))


def current_lineup(base):
    ours = base[base["team"] == US]
    return {z: [t for t in ORDER if ((ours["region"] == z) & (ours["tech"] == t)).any()] for z in S.REGIONS}


def default_decision(base, cell, inputs):
    """Décisions de départ d'un nouveau produit : prix moyen des vendeurs de la cellule, équipements permis, publicité moyenne."""
    reg, tech = cell.split("|")
    same = base[(base["cell"] == cell) & (base["team"] != US)]
    ours = base[(base["team"] == US) & (base["region"] == reg)]
    if len(same):
        w = same["last_demand"].fillna(0).values + 1.0
        price = float(np.average(same["price"].values, weights=w))
    else:
        price = float(inputs.get("new_price", {}).get(cell, ours["price"].max() * 1.3))
    feat = float(min(inputs.get("max_feat", {}).get(tech, 3), max(1, round(same["feat"].mean()) if len(same) else 3)))
    return price, feat, float(ours["adv"].mean())


def add_entrants(base, cells, n, rng):
    """Ajoute dans chaque cellule de `cells` les produits de n concurrents qui n'y sont pas encore (prix moyen de la cellule).
    n : entier, ou dict cellule -> nombre (les cellules absentes du dict ne reçoivent personne)."""
    f = base
    per = n if isinstance(n, dict) else {c: n for c in cells}
    for cell, k in per.items():
        reg, tech = cell.split("|")
        present = set(f[f["cell"] == cell]["team"])
        teams = [t for t in sorted(f["team"].unique()) if t != US and t not in present]
        ref = f[(f["cell"] == cell)]
        for t in list(rng.permutation(teams))[:int(k)]:
            src = f[(f["team"] == t) & (f["region"] == reg)]
            if src.empty:
                continue
            keep = {c: (0, 0, 0) for c in f[f["team"] == t]["cell"]}        # ses produits en place, dans toutes les zones, restent
            f = sim.with_products(f, {**keep, cell: (float(ref["price"].mean()), float(max(1, round(ref["feat"].mean()))), float(src["adv"].mean()))}, team=t)
    return f


def scenarios(d, params, inputs, lineup, n_per=12, entrants=0, seed=0, start=None):
    """Scénarios pour l'offre `lineup` ({zone: [techno, ...]}). Renvoie (Scenarios, cellules nouvelles, coûts repris)."""
    base = sim.status_quo_frame(d)
    ours = base[base["team"] == US].set_index("cell")
    products, new = {}, []
    for z in S.REGIONS:
        for t in lineup[z]:
            c = f"{z}|{t}"
            if c in ours.index:
                products[c] = tuple(ours.loc[c, ["price", "feat", "adv"]])
            else:
                products[c] = tuple((start or {}).get(c) or default_decision(base, c, inputs))
                new.append(c)
    base = sim.with_products(base, products)
    if entrants and (new or isinstance(entrants, dict)):          # dict : entrées supposées dans n'importe laquelle de nos cellules
        base = add_entrants(base, new, entrants, np.random.default_rng(seed))
    cells = sort_cells(products)
    mine = base[base["team"] == US].set_index("cell")
    mc, borrowed = dict(inputs.get("mc", {})), []
    for c in cells:
        if c not in mc:
            mc[c] = float(mine.loc[c, "unit_cost"])
            borrowed.append(c)
            if not np.isfinite(mc[c]):
                raise ValueError(f"coût unitaire inconnu pour {c} : l'ajouter à mc dans data/tour_N_inputs.json")
    # équipements disponibles d'une technologie absente de max_feat : 3 par défaut (à lire sur la page R&D)
    inp = {**inputs, "mc": mc, "max_feat": {**{t: 3 for t in ORDER}, **inputs.get("max_feat", {})}}
    borrowed += [f"max_feat[{c.split('|')[1]}] absent : 3 équipements supposés" for c in new if c.split("|")[1] not in inputs.get("max_feat", {})]
    sc = S.Scenarios(d, params, inp, inp.get("behaviours", BEHAVIOURS), n_per=n_per, seed=seed, base=base, cells=cells)
    sc.inputs = inp
    return sc, new, borrowed


def search(sc, new=(), radius=0.15, risk=0.5, seed=0, maxiter=35):
    """Prix, équipements et publicité de nos n produits cherchés ensemble, dans une zone de confiance de ±radius
    autour des décisions de départ (±2 radius pour un produit nouveau, dont le point de départ est arbitraire)."""
    n, cur, inp = len(sc.cells), sc.current, sc.inputs
    r = np.array([radius * (2 if c in new else 1) for c in sc.cells])
    k = 1 + 3 * r
    floor = (sc.mc + sc.fc) * 1.05 / sc.fx
    feat_hi = np.array([inp["max_feat"][c.split("|")[1]] for c in sc.cells], float)
    lo = np.column_stack([np.maximum(floor, cur[:, 0] * (1 - r)), np.maximum(1.0, np.minimum(cur[:, 1], feat_hi) - 2), np.maximum(50.0, cur[:, 2] / k)])
    hi = np.column_stack([np.maximum(cur[:, 0] * (1 + r), floor * 1.02), feat_hi, np.minimum(inp.get("adv_abs_max", 2500.0), np.maximum(cur[:, 2], 100.0) * k)])
    hi = np.maximum(hi, lo + 1e-6)
    unpack = lambda v: np.column_stack([v[:n], np.round(v[n:2 * n]), v[2 * n:]])
    f = lambda v: -S.score(sc.profit(unpack(v)), risk)
    b = list(zip(lo.T.reshape(-1), hi.T.reshape(-1)))
    res = differential_evolution(f, b, x0=np.clip(cur, lo, hi).T.reshape(-1), maxiter=maxiter, popsize=8, tol=1e-5, seed=seed, polish=False,
                                 integrality=np.r_[np.zeros(n), np.ones(n), np.zeros(n)].astype(bool))
    return unpack(res.x)


def alternatives(lineup, techs=None):
    """Offres obtenues en changeant la technologie d'un seul modèle dans une seule zone.
    techs : technologies que nous possédons (`techs` des entrées du tour, ex. ["Hybride", "Électrique", "Hydrogène"]) ;
    on compare alors, zone par zone, toutes les paires de technologies possédées. Sans `techs` : choix du tour 6."""
    out = {}
    if techs:
        import itertools
        for z in S.REGIONS:
            for pair in itertools.combinations([t for t in ORDER if t in techs], 2):
                if set(pair) != set(lineup[z]):
                    out[f"{z} : {' + '.join(lineup[z])} -> {' + '.join(pair)}"] = {**lineup, z: list(pair)}
        return out
    for z in S.REGIONS:
        for i, choix in enumerate(MODELES):
            now = next((t for t in lineup[z] if t in choix), None)
            for t in choix:
                if t != now and t not in lineup[z]:
                    alt = {**lineup, z: [x for x in lineup[z] if x != now] + [t]}
                    out[f"{z} : modèle {i + 1} {now or 'absent'} -> {t}"] = alt
    return out


def compare(tour, lineups=None, entrants=(0, 4, 8), n_per=12, radius=0.15, verbose=True):
    d_all = build()
    d = d_all[d_all["round"] < tour + 1]
    params = sim.fit_params(d)
    inputs = json.load(open(ROOT / "data" / f"tour_{tour}_inputs.json"))
    cur = current_lineup(sim.status_quo_frame(d))
    todo = {"offre actuelle": cur, **(lineups or alternatives(cur, inputs.get("techs")))}
    rows, decisions = [], {}
    for name, lu in todo.items():
        try:
            sc, new, borrowed = scenarios(d, params, inputs, lu, n_per, start={c: tuple(v) for c, v in inputs.get("new_products", {}).items()})
        except ValueError as e:                           # technologie que personne ne vend dans la zone : aucun coût de référence
            print(f"  {name:45s} non évaluée : {e}", flush=True)
            continue
        x = search(sc, new, radius)
        decisions[name] = dict(zip(sc.cells, x.tolist()))
        m, cont, q, sales = sc.profit(x, detail=True)
        row = dict(offre=name, marge=m.mean(), P10=np.quantile(m, .1),
                   demande_nouveaux=", ".join(f"{c} {q[:, sc.cells.index(c)].mean():.0f} [{np.quantile(q[:, sc.cells.index(c)], .1):.0f}-{np.quantile(q[:, sc.cells.index(c)], .9):.0f}]" for c in new),
                   cout_repris=", ".join(borrowed))
        for k in entrants:
            if k and new:                                 # mêmes décisions, k concurrents de plus dans les cellules nouvelles
                sk, _, _ = scenarios(d, params, inputs, lu, n_per, entrants=k, start={c: tuple(v) for c, v in decisions[name].items()})
                row[f"marge_si_{k}_entrants"] = sk.profit(x, detail=True)[0].mean()
        rows.append(row)
        if verbose:
            print(f"  {name:45s} marge {row['marge']:8.0f}  P10 {row['P10']:8.0f}  {row['demande_nouveaux']}", flush=True)
    T = pd.DataFrame(rows).set_index("offre")
    T.insert(1, "ecart_a_l_actuelle", T["marge"] - T.loc["offre actuelle", "marge"])
    return T, decisions


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tour", type=int, required=True)
    ap.add_argument("--offre", help='offre à tester, JSON {zone: [technos]} ; les zones absentes gardent leur offre')
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--entrants", type=int, nargs="*", default=[0, 4, 8])
    a = ap.parse_args()
    lus = None
    if a.offre:
        d0 = build()
        cur = current_lineup(sim.status_quo_frame(d0[d0["round"] < a.tour + 1]))
        lus = {a.offre: {**cur, **json.loads(a.offre)}}
    pd.set_option("display.width", 250)
    T, dec = compare(a.tour, lus, tuple(a.entrants), a.n)
    print("\n=== Offres comparées (M USD, marge du tour ; PREUVE FAIBLE pour Électrique et Hydrogène) ===")
    print(T.drop(columns=["demande_nouveaux", "cout_repris"]).round(0).to_string())
    for name, r in T.iterrows():
        if r["cout_repris"]:
            print(f"  {name} : valeurs reprises faute de saisie (coût unitaire des concurrents, équipements) : {r['cout_repris']}")
    json.dump(dict(table=json.loads(T.to_json(orient="index", force_ascii=False)), decisions=dec),
              open(ROOT / "out" / f"tour{a.tour}_offres.json", "w"), ensure_ascii=False, indent=1)
