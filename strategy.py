"""Recherche de la meilleure stratégie par simulation, face à plusieurs comportements des concurrents.

  python3 strategy.py --tour 5            # recommandation pour le tour 5 (entrées : data/tour_5_inputs.json)
  python3 strategy.py --tour 3 --backtest # la méthode aurait-elle battu nos décisions réelles au tour 3 ?

Étapes : scénarios (comportements x bruit x incertitude du moteur) -> grille -> raffinement continu
-> matrice de gains stratégies x comportements -> plan de production (programme linéaire).
"""
import argparse
import json
import warnings

import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution, linprog

from cesim.client import ROOT
from model import market, rivals, sim
from model.panel2 import build

warnings.filterwarnings("ignore")
US = sim.US
REGIONS = sim.REGIONS
TECHS = ["Thermique", "Hybride"]
CELLS = [f"{r}|{t}" for r in REGIONS for t in TECHS]


# ------------------------------------------------------------------ scénarios
class Scenarios:
    """Pour chaque scénario et chacun de nos produits (`cells`, une gamme quelconque) : attraction totale des
    concurrents, taille du marché, paramètres du moteur. Permet d'évaluer une décision en quelques microsecondes."""

    def __init__(self, d, params, inputs, behaviours, n_per=40, seed=0, base=None, cells=None):
        """base : cadre du tour (défaut : statu quo) ; cells : nos produits `zone|tech` (défaut : les 6 de CELLS s'ils
        sont tous dans le cadre, sinon nos produits du cadre). Entrées optionnelles : `market_method`, `cell_factor`."""
        rng = np.random.default_rng(seed)
        self.inputs = inputs
        base = sim.status_quo_frame(d) if base is None else base.copy()
        if cells is None:                                     # défaut : les 6 de CELLS, sinon nos produits du cadre
            mine = set(base.loc[base["team"] == US, "cell"])
            cells = CELLS if set(CELLS) <= mine else our_cells(base)
        self.cells = cells = list(cells)
        zone = [c.split("|")[0] for c in cells]
        self.tech = np.array([c.split("|")[1] for c in cells])
        # indice de l'autre produit de la même zone (-1 s'il n'y en a pas)
        self.other = np.array([next((j for j in range(len(cells)) if j != i and zone[j] == zone[i]), -1) for i in range(len(cells))])
        us = (base["team"] == US).values
        if inputs.get("our_decisions"):                       # état déduit de nos décisions ESG, RH, fournisseurs
            from model import state
            self.state_detail = state.our_state(inputs, int(base["round"].iloc[0]), US)[1]
            base.loc[us, "esg"] = self.state_detail["esg"]
            if "lqual" in self.state_detail:
                base.loc[us, "lqual"] = self.state_detail["lqual"]
        for k, v in inputs.get("our_state", {}).items():      # ESG, certification attendus pour nous (saisie : prioritaire)
            base.loc[us, k] = v
        self.base = base
        method = inputs.get("market_method", "mixte")         # "mixte" (défaut) ou "directe" : voir model/market.py
        mk0 = market.forecast(base, inputs["growth"], method=method)
        rows, labels = [], []
        for name in behaviours:
            fn = rivals.BEHAVIOURS.get(name)
            for i in range(n_per):
                if name == "mélange":
                    f = rivals.melange(base, d, params, rng, markets=mk0)
                elif name in ("meilleure réponse", "équilibre"):
                    f = fn(base, d, params, rng, markets=mk0)
                else:
                    f = fn(base, d, params, rng)
                if inputs.get("gamme_concurrents"):          # concurrents qui changent de gamme (rivals.changement_de_gamme)
                    g = inputs["gamme_concurrents"]            # "tirée" : probabilités de rivals.GAMME_P ; ou dict de probabilités
                    f = rivals.changement_de_gamme(f, d, params, rng, p=g if isinstance(g, dict) else None)
                f = rivals.bruit(f, rng)
                mk = market.forecast(f, inputs["growth"], rng, method=method)
                scale = dict(k=np.exp(rng.normal(0, 0.08)), a=inputs.get("adv_mult", 1.0) * np.exp(rng.normal(0, 0.15)),
                             f=np.exp(rng.normal(0, 0.10)), s=np.exp(rng.normal(0, 0.15)))
                p = sim.row_params(f, params, scale)
                info = sim.row_info(f)
                u = sim.u_row(p, info, f["price"].values, f["feat"].values, np.maximum(f["adv"].values, 1), f["adv_o"].values)
                rec = {}
                for c in cells:
                    m = (f["cell"] == c).values
                    i_us = np.where(m & (f["team"] == US).values)[0]
                    if len(i_us) == 0:
                        continue
                    j = i_us[0]
                    # cell_factor : correction saisie de la taille d'une cellule (saut d'attrait annoncé par les conditions de marché)
                    rec[c] = dict(S=np.exp(u[m & (f["team"] != US).values]).sum(), M=mk[c] * inputs.get("cell_factor", {}).get(c, 1.0) * np.exp(rng.normal(0, 0.08)),
                                  **{k: v[j] for k, v in p.items()}, **{k: v[j] for k, v in info.items()})
                rows.append(rec)
                labels.append(name)
        self.labels = np.array(labels)
        keys = list(rows[0][cells[0]].keys())
        # tableaux (scénario, cellule)
        self.z = {k: np.array([[r[c][k] for c in cells] for r in rows]) for k in keys}
        sd = inputs.get("our_state_sd", 0.0)                  # incertitude sur notre impact ESG (log), commune à nos produits
        if sd:
            self.z["esg"] = self.z["esg"] + rng.normal(0, sd, (len(rows), 1))
        self.fx = np.array([inputs["fx"][c.split("|")[0]] for c in cells])
        self.fc = np.array([sim.FEAT_COST[c.split("|")[0]] for c in cells])
        self.mc = np.array([inputs["mc"][c] for c in cells])
        self.cap = inputs.get("supply_cap", {})
        b = base[us].set_index("cell").loc[cells]
        self.current = np.column_stack([b["price"].values, b["feat"].values, b["adv"].values])
        self.q0 = self._demand(self.current)[0].mean(0)      # demande de référence (décisions actuelles), par cellule
        self.gm0 = np.maximum(self.current[:, 0] * self.fx - self.mc - self.fc * self.current[:, 1], 0) * self.q0 / 1000

    def _demand(self, x):
        """x : (n, 3) = prix, équipements, publicité par cellule. Renvoie demande et ventes (scénario, cellule)."""
        z = self.z
        price, feat, adv = x[:, 0], x[:, 1], np.maximum(x[:, 2], 1.0)
        adv_o = np.where(self.other >= 0, adv[self.other], 0.0)   # publicité de l'autre produit dans la même zone
        u = sim.u_row(z, z, price[None, :], feat[None, :], adv[None, :], adv_o[None, :])
        a = np.exp(u)
        q = z["M"] * a / (a + z["S"])
        sales = q.copy()
        for tech, cap in self.cap.items():                        # plafond d'offre mondiale par technologie
            m = self.tech == tech
            if cap and m.any():
                tot = np.maximum(q[:, m].sum(1), 1e-9)
                sales[:, m] *= np.minimum(1.0, cap / tot)[:, None]
        return q, sales

    def profit(self, x, detail=False):
        """Gain par scénario (M USD) : marge du tour + valeur de la position laissée au tour suivant."""
        q, sales = self._demand(x)
        unit = x[:, 0] * self.fx - self.mc - self.fc * x[:, 1]
        margin = (unit[None, :] * sales / 1000).sum(1) - np.maximum(x[:, 2], 0).sum()
        w = self.inputs.get("carry_weight", 0.7)
        cont = w * (self.z["h"] * np.log(np.maximum(q, 1e-9) / self.q0) * self.gm0).sum(1)        # inertie de part de marché
        cont -= w * (self.z["u"] * (1 - sales / np.maximum(q, 1e-9)) * self.gm0).sum(1)           # pénalité de rupture
        if detail:
            return margin, cont, q, sales
        return margin + cont


ORDER = ["Thermique", "Hybride", "Électrique", "Hydrogène"]


def our_cells(base, team=US):
    """Nos produits `zone|tech` présents dans le cadre, par zone puis par technologie."""
    return sorted(set(base.loc[base["team"] == team, "cell"]), key=lambda c: (REGIONS.index(c.split("|")[0]), ORDER.index(c.split("|")[1])))


def score(v, risk=0.5):
    return v.mean() - risk * v.std()


# ------------------------------------------------------------------ optimisation
def bounds(sc, inputs):
    cur = sc.current
    # publicité : on reste dans une plage raisonnable autour de l'existant (le moteur extrapole mal aux extrêmes)
    adv_lo = np.maximum(100.0, cur[:, 2] * inputs.get("adv_down", 0.5))
    adv_hi = np.minimum(inputs.get("adv_max", 1500.0), np.maximum(cur[:, 2], 200.0) * inputs.get("adv_up", 2.0))
    feat_lo = np.maximum(1.0, cur[:, 1] - inputs.get("feat_down", 1))
    lo = np.column_stack([cur[:, 0] * (1 - inputs.get("price_down", 0.15)), feat_lo, adv_lo])
    hi = np.column_stack([cur[:, 0] * (1 + inputs.get("price_up", 0.15)), [inputs["max_feat"][c.split("|")[1]] for c in sc.cells], adv_hi])
    for c, (a, b) in inputs.get("price_bounds", {}).items():
        if c in sc.cells:
            lo[sc.cells.index(c), 0], hi[sc.cells.index(c), 0] = a, b
    return lo, hi


def grid_search(sc, inputs, mask=None, risk=0.5, sweeps=3):
    """Étage 1 : grille prix x équipements x publicité, cellule par cellule, répétée (publicité croisée)."""
    lo, hi = bounds(sc, inputs)
    x = np.clip(sc.current.copy(), lo, hi)
    sub = sc if mask is None else _subset(sc, mask)
    for _ in range(sweeps):
        for i in range(len(sc.cells)):
            best = (-1e18, None)
            for feat in range(int(lo[i, 1]), int(hi[i, 1]) + 1):
                for adv in np.linspace(lo[i, 2], hi[i, 2], 12):
                    for price in np.linspace(lo[i, 0], hi[i, 0], 25):
                        y = x.copy()
                        y[i] = [price, feat, adv]
                        s = score(sub.profit(y), risk)
                        if s > best[0]:
                            best = (s, y[i].copy())
            x[i] = best[1]
    return x


def refine(sc, inputs, x0, mask=None, risk=0.5, seed=0):
    """Étage 2 : évolution différentielle sur prix et publicité (équipements fixés par la grille)."""
    lo, hi = bounds(sc, inputs)
    sub = sc if mask is None else _subset(sc, mask)
    feats = x0[:, 1].copy()
    n = len(sc.cells)

    def f(v):
        x = np.column_stack([v[:n], feats, v[n:]])
        return -score(sub.profit(x), risk)

    b = list(zip(np.maximum(lo[:, 0], x0[:, 0] * 0.94), np.minimum(hi[:, 0], x0[:, 0] * 1.06))) + list(zip(np.maximum(lo[:, 2], x0[:, 2] * 0.6), np.minimum(hi[:, 2], x0[:, 2] * 1.6 + 1)))
    b = [(lo_, max(hi_, lo_ + 1e-6)) for lo_, hi_ in b]
    lb, ub = np.array([v[0] for v in b]), np.array([v[1] for v in b])
    start = lb + (ub - lb) * np.clip((np.r_[x0[:, 0], x0[:, 2]] - lb) / (ub - lb), 1e-6, 1 - 1e-6)   # strictement à l'intérieur
    r = differential_evolution(f, b, x0=start, maxiter=60, popsize=12, tol=1e-6, seed=seed, polish=False)
    x = np.column_stack([r.x[:n], feats, r.x[n:]])
    return x if -r.fun >= score(sub.profit(x0), risk) else x0


# ------------------------------------------------------------------ recherche conjointe à bornes larges (étape B)
def wide_bounds(sc, inputs, radius=None):
    """Bornes de recherche. radius=None : bornes larges (prix du coût de revient +5 % à +40 % au-dessus du prix
    actuel, publicité de 50 à 2 500 M USD). radius=r : zone de confiance, prix à ±r, publicité entre /(1+3r) et x(1+3r)."""
    cur, n = sc.current, len(sc.cells)
    feat_hi = np.array([inputs["max_feat"][c.split("|")[1]] for c in sc.cells], float)
    floor = (sc.mc + sc.fc * 1.0) * 1.05 / sc.fx                     # prix plancher : coût unitaire + 5 %
    if radius is None:
        lo = np.column_stack([np.maximum(floor, cur[:, 0] * 0.75), np.ones(n), np.full(n, 50.0)])
        hi = np.column_stack([cur[:, 0] * 1.40, feat_hi, np.full(n, inputs.get("adv_abs_max", 2500.0))])
    else:
        k = 1 + 3 * radius
        lo = np.column_stack([np.maximum(floor, cur[:, 0] * (1 - radius)), np.maximum(1.0, np.minimum(cur[:, 1], feat_hi) - 2), np.maximum(50.0, cur[:, 2] / k)])
        hi = np.column_stack([cur[:, 0] * (1 + radius), feat_hi, np.minimum(inputs.get("adv_abs_max", 2500.0), np.maximum(cur[:, 2], 100.0) * k)])
    return lo, np.maximum(hi, lo + 1e-6)


def search_joint(sc, inputs, radius=None, risk=0.5, seeds=(0, 1), maxiter=120, popsize=14, x0=None, objectif=None):
    """Prix, équipements (entiers) et publicité de nos n produits (`sc.cells`) cherchés ENSEMBLE par évolution
    différentielle, plusieurs départs. Renvoie la meilleure décision (arrondie) et son score.
    objectif : fonction x -> valeur à maximiser (ex. objectif.Bareme(sc, tour).score, les points du barème) ;
    par défaut la marge, moyenne moins `risk` écart-type."""
    val = objectif if objectif is not None else (lambda x: score(sc.profit(x), risk))
    lo, hi = wide_bounds(sc, inputs, radius)
    n = len(sc.cells)
    b = list(zip(lo.T.reshape(-1), hi.T.reshape(-1)))                 # ordre : n prix, n équipements, n publicités
    integrality = np.r_[np.zeros(n), np.ones(n), np.zeros(n)].astype(bool)
    unpack = lambda v: np.column_stack([v[:n], np.round(v[n:2 * n]), v[2 * n:]])
    f = lambda v: -val(unpack(v))
    best = None
    starts = [np.clip(sc.current, lo, hi)] + ([np.clip(x0, lo, hi)] if x0 is not None else [])
    for i, seed in enumerate(seeds):
        st = starts[min(i, len(starts) - 1)]
        r = differential_evolution(f, b, x0=st.T.reshape(-1), maxiter=maxiter, popsize=popsize, tol=1e-7, seed=seed, polish=False,
                                   integrality=integrality, init="sobol")
        if best is None or r.fun < best.fun:
            best = r
    x = tidy(unpack(best.x), sc.cells)
    x = np.clip(x, lo, hi)
    x[:, 1] = np.round(x[:, 1])
    return x, val(x)


def frontier(sc, inputs, behaviours, radii=(0.0, 0.03, 0.06, 0.10, 0.15, 0.20, 0.30, None), risk=0.5, verbose=True, objectif=None):
    """Frontière gain / éloignement : meilleure décision dans des zones de confiance de plus en plus larges autour
    des décisions du tour précédent. radius 0 = décisions reconduites ; None = bornes larges (optimum du modèle)."""
    rows, xs, prev = [], {}, None
    val = objectif if objectif is not None else (lambda x: score(sc.profit(x), risk))
    for r in radii:
        if r == 0.0:
            x = tidy(sc.current, sc.cells)
        else:
            x, _ = search_joint(sc, inputs, r, risk=risk, x0=prev, seeds=(0,) if r is not None else (0, 1), maxiter=80 if r is not None else 140, objectif=objectif)
            if prev is not None and val(prev) > val(x):
                x = prev                                              # une zone plus large contient la précédente
        prev = x
        v = sc.profit(x)
        name = "reconduit" if r == 0.0 else ("bornes larges" if r is None else f"±{int(r * 100)} %")
        xs[name] = x
        per = {b: v[sc.labels == b].mean() for b in behaviours}
        rows.append(dict(zone=name, objectif=val(x), moyenne=v.mean(), P10=np.quantile(v, .1), pire_comportement=min(per.values()),
                         ecart_prix_max=np.abs(x[:, 0] / sc.current[:, 0] - 1).max() * 100, pub_totale=x[:, 2].sum(),
                         equipements=" ".join(str(int(a)) for a in x[:, 1])))
        if verbose:
            print(f"  {name:14s} objectif {rows[-1]['objectif']:9.2f}  moyenne {v.mean():8.0f}  P10 {np.quantile(v, .1):8.0f}  écart de prix max {rows[-1]['ecart_prix_max']:4.1f} %  pub {x[:, 2].sum():6.0f}", flush=True)
    return pd.DataFrame(rows).set_index("zone"), xs


def _subset(sc, mask):
    s = object.__new__(Scenarios)
    s.__dict__.update(sc.__dict__)
    s.z = {k: v[mask] for k, v in sc.z.items()}
    s.labels = sc.labels[mask]
    return s


def tidy(x, cells=None):
    """Arrondis saisissables : prix à 100 (1000 en RMB), publicité à 50 M USD."""
    y = x.copy()
    for i, c in enumerate(cells or CELLS):
        step = 1000 if c.startswith("Chine") else 100
        y[i, 0] = round(y[i, 0] / step) * step
        y[i, 1] = round(y[i, 1])
        y[i, 2] = round(y[i, 2] / 50) * 50
    return y


def optimise(sc, inputs, behaviours, risk=0.5):
    """Une stratégie optimale par comportement supposé, plus la stratégie optimale en moyenne."""
    strategies = {"décisions actuelles": tidy(sc.current, sc.cells)}
    strategies["robuste (tous comportements)"] = tidy(refine(sc, inputs, grid_search(sc, inputs, risk=risk), risk=risk), sc.cells)
    for b in behaviours:
        m = sc.labels == b
        strategies[f"si « {b} »"] = tidy(refine(sc, inputs, grid_search(sc, inputs, m, risk=0.25), m, risk=0.25), sc.cells)
    strategies["prudente (pire 20 %)"] = tidy(refine(sc, inputs, grid_search(sc, inputs, risk=1.5), risk=1.5), sc.cells)
    return strategies


def payoff_matrix(sc, strategies, behaviours):
    rows = {}
    for name, x in strategies.items():
        v = sc.profit(x)
        rows[name] = {b: v[sc.labels == b].mean() for b in behaviours}
        rows[name]["moyenne"] = np.mean([rows[name][b] for b in behaviours])
        rows[name]["P10"] = np.quantile(v, 0.1)
    M = pd.DataFrame(rows).T
    regret = (M[behaviours].max(axis=0) - M[behaviours]).max(axis=1)
    M["regret max"] = regret
    return M


def choose(M):
    """Meilleure moyenne parmi les stratégies dont le regret maximal reste dans le meilleur tiers."""
    ok = M[M["regret max"] <= M["regret max"].quantile(0.4)]
    return ok["moyenne"].idxmax()


# ------------------------------------------------------------------ production (programme linéaire)
def production_plan(demand, prod):
    """Répartit stocks, usines et sous-traitance entre marchés au moindre coût.

    demand : dict cellule -> volume à couvrir ; prod : sources {nom: dict(zone, tech, cost, cap, pool)} + transport + margin.
    """
    src = list(prod["sources"])
    CELLS = list(demand)                                               # nos produits : ceux dont on donne la demande
    nc = len(CELLS)
    var = [(s, c) for s in src for c in CELLS if prod["sources"][s]["tech"] == c.split("|")[1]]
    nv = len(var)
    cost = np.array([prod["sources"][s]["cost"] + prod["transport"].get(f"{prod['sources'][s]['zone']}>{c.split('|')[0]}|{c.split('|')[1]}", 0.0) for s, c in var])
    c_obj = np.r_[cost, [prod["margin"][c] for c in CELLS]]            # variables d'écart : demande non servie, coûte la marge
    A_eq = np.zeros((nc, nv + nc))
    for j, (s, c) in enumerate(var):
        A_eq[CELLS.index(c), j] = 1
    A_eq[:, nv:] = np.eye(nc)
    b_eq = np.array([demand[c] for c in CELLS])
    A_ub, b_ub = [], []
    for s in src:                                                       # capacité de chaque source
        A_ub.append([1.0 if v[0] == s else 0.0 for v in var] + [0] * nc)
        b_ub.append(prod["sources"][s]["cap"])
    for pool, cap in prod.get("pools", {}).items():                     # capacités partagées (usine d'une zone, sous-traitance d'une zone)
        A_ub.append([1.0 if prod["sources"][v[0]].get("pool") == pool else 0.0 for v in var] + [0] * nc)
        b_ub.append(cap)
    r = linprog(c_obj, A_ub=np.array(A_ub), b_ub=np.array(b_ub), A_eq=A_eq, b_eq=b_eq, bounds=(0, None), method="highs")
    flows = pd.DataFrame([dict(source=s, cellule=c, k_unites=round(v, 1)) for (s, c), v in zip(var, r.x[:nv]) if v > 0.5])
    unmet = {c: round(v, 1) for c, v in zip(CELLS, r.x[nv:]) if v > 0.5}
    return flows, unmet


# ------------------------------------------------------------------ programme principal
def table(strategies, names=None, cells=None):
    cells = list(cells or CELLS)
    rows = []
    for name, x in strategies.items():
        if names and name not in names:
            continue
        for c, v in zip(cells, x):
            rows.append(dict(strategie=name, cellule=c, prix=int(v[0]), equip=int(v[1]), pub=int(v[2])))
    return pd.DataFrame(rows).pivot(index="cellule", columns="strategie", values=["prix", "equip", "pub"]).loc[cells]


def run(tour, n_per=40, backtest=False, verbose=True):
    d_all = build()
    idx = tour + 1                                   # indice interne du tour à décider
    d = d_all[d_all["round"] < idx]
    params = sim.fit_params(d)
    inputs = json.load(open(ROOT / "data" / f"tour_{tour}_inputs.json"))
    behaviours = inputs.get("behaviours", ["statu quo", "tendance", "guerre des prix", "montée en gamme", "meilleure réponse", "mélange"])
    sc = Scenarios(d, params, inputs, behaviours, n_per=n_per)
    strategies = optimise(sc, inputs, behaviours)
    M = payoff_matrix(sc, strategies, behaviours)
    best = choose(M)
    if verbose:
        pd.set_option("display.width", 250)
        print(f"\n=== Tour {tour} : matrice de gains (M USD, marge du tour + valeur de position) ===")
        print(M.round(0).astype(int).to_string())
        print(f"\nStratégie retenue : {best}")
        print(table(strategies, ["décisions actuelles", best, "prudente (pire 20 %)"], sc.cells).to_string())
        m, cont, q, sales = sc.profit(strategies[best], detail=True)
        print("\nDemande attendue (k unités) : " + ", ".join(f"{c} {q[:, i].mean():.0f} [{np.quantile(q[:, i], .1):.0f}-{np.quantile(q[:, i], .9):.0f}]" for i, c in enumerate(sc.cells)))
    out = dict(best=best, matrix=M, strategies=strategies, sc=sc, params=params, inputs=inputs)
    if backtest:
        out["backtest"] = evaluate_ex_post(d_all, idx, strategies, inputs, verbose)
    return out


def evaluate_ex_post(d_all, idx, strategies, inputs, verbose=True):
    """Évalue chaque stratégie avec les décisions RÉELLES des concurrents au tour `idx` et le moteur calé sur tout l'historique."""
    params = sim.fit_params(d_all)
    t = d_all[d_all["round"] == idx].copy()
    t["fx"] = np.where(t["sales"] > 0, t["rev"] / (t["sales"] * t["price"]) * 1000, np.nan)
    t["fx"] = t.groupby("region")["fx"].transform(lambda x: x.fillna(x.median()))
    t["unit_cost"] = np.where(t["sales"] > 0, t["cogs"] / t["sales"] * 1000, 0) - t["feat"] * t["region"].map(sim.FEAT_COST)
    markets = t.groupby("cell")["demand"].sum().to_dict()
    t["cell"] = t["region"] + "|" + t["tech"]
    markets = t.groupby("cell")["demand"].sum().to_dict()
    us = (t["team"] == US).values
    res = {}
    real = strategies.copy()
    cur = t[us].set_index("cell")
    real["décisions réellement jouées"] = np.column_stack([cur.reindex(CELLS)["price"].values, cur.reindex(CELLS)["feat"].values, cur.reindex(CELLS)["adv"].values])
    for name, x in real.items():
        f = t.copy()
        for c, v in zip(CELLS, x):
            m = us & (f["cell"] == c).values
            if m.sum() and not np.isnan(v[0]):
                f.loc[m, ["price", "feat", "adv"]] = v
        s = sim.simulate_round(f, params, markets, supply={})
        o = s[s["team"] == US]
        res[name] = dict(demande=o["sim_demand"].sum(), marge=o["sim_margin"].sum())
    R = pd.DataFrame(res).T.sort_values("marge", ascending=False)
    if verbose:
        print(f"\n=== Évaluation a posteriori (concurrents réels du tour {idx - 1}) ===")
        print(R.round(0).astype(int).to_string())
    return R


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tour", type=int, required=True)
    ap.add_argument("--backtest", action="store_true")
    ap.add_argument("--n", type=int, default=40)
    a = ap.parse_args()
    run(a.tour, n_per=a.n, backtest=a.backtest)
