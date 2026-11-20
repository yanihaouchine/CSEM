"""Recherche de la famille de fonctions (prix, publicité) dont les paramètres restent
constants entre le tour d'entraînement et le tour 1 (mêmes conditions de départ)."""
import itertools
import sys
import warnings

import numpy as np
from scipy.optimize import least_squares

from model.panel2 import build

warnings.filterwarnings("ignore")
P0 = {"USA": 18500, "Chine": 125000, "Europe": 20000}


def cellstat(t, col, how):
    g = t.groupby("cell")[col]
    if how == "mean":
        return g.transform("mean").values
    if how == "median":
        return g.transform("median").values
    if how == "wmean":
        return ((t[col] * t["demand"]).groupby(t["cell"]).transform("sum") / t.groupby("cell")["demand"].transform("sum")).values
    if how == "gmean":
        return np.exp(np.log(t[col]).groupby(t["cell"]).transform("mean").values)
    return np.full(len(t), float(how))


PRICE = {  # (fonction, valeurs initiales)
    "exp(-k x^g)": (lambda th, x: -th[0] * x ** th[1], [2.0, 1.2]),
    "exp(-k x - m x²)": (lambda th, x: -th[0] * x - th[1] * x * x, [2.0, 0.2]),
    "x^-e exp(-k x)": (lambda th, x: -th[0] * np.log(x) - th[1] * x, [1.0, 1.5]),
    "x^-e": (lambda th, x: -th[0] * np.log(x) + 0 * th[1], [3.0, 0.0]),
}
ADV = {
    "a ln(y+c)": (lambda th, y: th[0] * np.log(y + abs(th[1])), [0.6, 1.5]),
    "a y/(y+c)": (lambda th, y: th[0] * y / (y + abs(th[1])), [1.0, 2.0]),
    "a (1-exp(-y/c))": (lambda th, y: th[0] * (1 - np.exp(-y / abs(th[1]))), [0.6, 1.5]),
    "a y^b": (lambda th, y: th[0] * y ** th[1], [0.3, 0.6]),
}


def search(reg, rounds=(1, 2), tech="Thermique", top=8):
    d = build()
    t = d[(d.tech == tech) & (d.region == reg) & (d["round"].isin(rounds))].copy()
    inv = np.unique(t["cell"].values, return_inverse=True)[1]
    D = t["demand"].values
    M = np.bincount(inv, D)[inv]
    lf = np.log(t["feat"].values)
    res = []
    for pref, aref in itertools.product(["const", "mean", "wmean", "median", "gmean"], ["abs", "mean", "mean_eff"]):
        ref = cellstat(t, "price", P0[reg] if pref == "const" else pref)
        x = t["price"].values / ref
        if aref == "abs":
            an = np.full(len(t), 600.0)
        elif aref == "mean":
            an = cellstat(t, "adv", "mean")
        else:
            an = None
        for (pn, (pf, p0)), (anm, (af, a0)) in itertools.product(PRICE.items(), ADV.items()):
            def model(th):
                eff = t["adv"].values + th[5] * t["adv_o"].values
                norm = an if an is not None else np.bincount(inv, eff)[inv] / np.bincount(inv)[inv]
                u = pf(th[0:2], x) + th[2] * lf + af(th[3:5], eff / norm)
                A = np.exp(u - u.max())
                return M * A / np.bincount(inv, A)[inv]
            best = None
            rng = np.random.default_rng(0)
            for s in range(5):
                x0 = np.array(p0 + [0.45] + a0 + [0.4]) * (1 + (0.3 * rng.normal(size=6) if s else 0))
                try:
                    o = least_squares(lambda th: (model(th) - D) / np.sqrt(D + 1), x0)
                except Exception:
                    continue
                if best is None or o.cost < best.cost:
                    best = o
            if best is None:
                continue
            e = model(best.x) - D
            res.append((np.abs(e).sum() / D.sum() * 100, np.abs(e).max(), pn, pref, anm, aref, np.round(best.x, 3)))
    res.sort(key=lambda r: r[0])
    print(f"=== {reg} {tech} tours {rounds} (n={len(t)})")
    for r in res[:top]:
        print(f"  {r[0]:.3f}% max {r[1]:5.2f}k | prix {r[2]:18s} réf {r[3]:6s} | pub {r[4]:16s} réf {r[5]:8s} | {r[6]}")
    return res


if __name__ == "__main__":
    for reg in (sys.argv[1:] or ["USA", "Chine", "Europe"]):
        search(reg)
