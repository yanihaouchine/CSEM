"""Moteur de demande structurel : reproduit la répartition de la demande entre équipes
dans chaque (tour, zone, tech) à partir des seules décisions.

Attraction d'un produit :
  A = exp(-k * (prix / prix_moyen_du_tour_précédent)^g) * equip^f * (pub + lam*pub_autre_produit + c)^a
      * impact_ESG_décisions^s * (qualité_fournisseurs / 3)^q * exp(cert * certifié)
      * (part_préc * n)^h * exp(-u * part_de_demande_non_servie_au_tour_précédent)
Demande = marché(tour, zone, tech) * A / somme(A).
"""
import numpy as np
import pandas as pd
from scipy.optimize import least_squares

REGIONS = ["USA", "Chine", "Europe"]
PNAMES = ["k", "g", "f", "a", "c", "d", "h", "s", "q", "cert", "new", "lam", "b", "u", "am3", "am4", "am5", "km3", "km4", "km5", "fm3", "fm4", "fm5"]
X0 = dict(k=2.5, g=1.0, f=0.45, a=0.5, c=1000.0, d=0.3, h=0.1, s=1.0, q=0.3, cert=0.15, new=-0.2, lam=0.2, b=0.04, u=0.1, am3=0.0, am4=0.0, am5=0.0, km3=0.0, km4=0.0, km5=0.0, fm3=0.0, fm4=0.0, fm5=0.0)
NEUTRAL = dict(g=1.0, d=0.0, h=0.0, s=1.0, q=0.0, cert=0.0, new=0.0, lam=0.0, b=0.0, u=0.0, am3=0.0, am4=0.0, am5=0.0, km3=0.0, km4=0.0, km5=0.0, fm3=0.0, fm4=0.0, fm5=0.0)


def prepare(d):
    """Pré-calcule les tableaux numpy utilisés par le moteur (rapide à évaluer ensuite)."""
    cells, inv = np.unique(d["cell"].values, return_inverse=True)
    cnt = np.bincount(inv)
    pm = d["ref_price"].values if "ref_price" in d else (np.bincount(inv, d["price"].values) / cnt)[inv]
    return dict(inv=inv, ncell=len(cells), cells=cells, rel_price=d["price"].values / pm, lfeat=np.log(d["feat"].values),
                adv=d["adv"].values, padv=d["p_adv"].fillna(d["adv"]).values, lprev=np.log(d["p_share"].fillna(1.0 / 12).values * 12),
                isnew=d["p_share"].isna().values.astype(float), esg=d["esg"].values, lqual=d["lqual"].values,
                cert1=d["cert1"].values, demand=d["demand"].values, adv_o=d["adv_o"].values, has_o=d["has_o"].values,
                r3=(d["round"].values == 3) * 1.0, r4=(d["round"].values == 4) * 1.0, r5=(d["round"].values == 5) * 1.0,
                unmet=1.0 - d["p_fill"].values, lfill=np.log(d["p_fill"].values.clip(0.02, 1)),
                market=np.bincount(inv, d["demand"].values)[inv])


def utility(p, z):
    """Logarithme de l'attraction (non normalisé)."""
    am = 1 + p["am3"] * z["r3"] + p["am4"] * z["r4"] + p["am5"] * z["r5"]
    km = 1 + p["km3"] * z["r3"] + p["km4"] * z["r4"] + p["km5"] * z["r5"]
    fm = 1 + p["fm3"] * z["r3"] + p["fm4"] * z["r4"] + p["fm5"] * z["r5"]
    return (-p["k"] * km * z["rel_price"] ** p["g"] + p["f"] * fm * z["lfeat"]
            + p["a"] * am * np.log(z["adv"] + p["lam"] * z["adv_o"] + abs(p["d"]) * z["padv"] + abs(p["c"])) + p["b"] * z["has_o"]
            - p["u"] * z["unmet"] + p["h"] * z["lprev"] + p["new"] * z["isnew"] + p["s"] * z["esg"] + p["q"] * z["lqual"]
            + p["cert"] * z["cert1"])


def attraction(p, z):
    u = utility(p, z)
    return np.exp(u - u.max())


def predict(p, d, market=None):
    """Demande simulée ; `market` = taille de marché par ligne (défaut : somme observée de la cellule)."""
    z = d if isinstance(d, dict) else prepare(d)
    A = attraction(p, z)
    M = z["market"] if market is None else market
    return M * A / np.bincount(z["inv"], A, minlength=z["ncell"])[z["inv"]]


def fit(d, free, fixed=None, starts=6, seed=0):
    fixed = dict(fixed or {})
    base = {**X0, **fixed}
    for k in PNAMES:
        if k not in free and k not in fixed and k in NEUTRAL:
            base[k] = NEUTRAL[k]

    def unpack(x):
        p = dict(base)
        p.update(dict(zip(free, x)))
        return p

    z = prepare(d)

    def res(x):
        return (predict(unpack(x), z) - z["demand"]) / np.sqrt(z["demand"] + 1)

    best = None
    rng = np.random.default_rng(seed)
    for s in range(starts):
        x0 = np.array([X0[k] for k in free]) * (1 + (0.35 * rng.normal(size=len(free)) if s else 0))
        o = least_squares(res, x0)
        if best is None or o.cost < best.cost:
            best = o
    return unpack(best.x)


def errors(p, d):
    pred = predict(p, d)
    e = pred - d["demand"].values
    return dict(n=len(d), mape=float(np.mean(np.abs(e) / d["demand"].values) * 100), wape=float(np.abs(e).sum() / d["demand"].sum() * 100),
                max_abs=float(np.abs(e).max()))


# --- Ajustement conjoint : paramètres de marché propres à chaque (zone, tech),
#     paramètres « entreprise » (ESG, certification, nouveauté) communs, qualité par zone.
GROUP_P = ["k", "f", "a", "c", "h"]
SHARED_P = ["cert", "new", "lam", "u", "g_USA", "g_Chine", "g_Europe", "q_USA", "q_Chine", "q_Europe", "s_USA", "s_Chine", "s_Europe"]


def fit_joint(d, shared_free=None, group_free=None, ridge=0.02, starts=3, seed=0):
    groups = sorted(d.groupby(["region", "tech"]).groups)
    zs = {g: prepare(d[(d.region == g[0]) & (d.tech == g[1])]) for g in groups}
    group_free = group_free or GROUP_P
    shared_free = list(shared_free if shared_free is not None else SHARED_P)
    sh0 = dict(cert=0.0, new=0.0, lam=0.0, u=0.0, g_USA=1.0, g_Chine=1.0, g_Europe=1.0, q_USA=0.0, q_Chine=0.0, q_Europe=0.0, s_USA=1.0, s_Chine=1.0, s_Europe=1.0)
    gp0 = np.array([X0[k] if k != "h" else 0.1 for k in group_free])

    def unpack(x):
        sh = dict(sh0)
        sh.update(dict(zip(shared_free, x[:len(shared_free)])))
        out = {}
        for i, g in enumerate(groups):
            p = dict(X0, **NEUTRAL)
            p.update(dict(zip(group_free, x[len(shared_free) + i * len(group_free):len(shared_free) + (i + 1) * len(group_free)])))
            p.update(s=sh["s_" + g[0]], cert=sh["cert"], new=sh["new"], lam=sh["lam"], u=sh["u"], g=sh["g_" + g[0]], q=sh["q_" + g[0]])
            out[g] = p
        return out

    x_ref = np.r_[[sh0[k] for k in shared_free], np.tile(gp0, len(groups))]

    def res(x):
        ps = unpack(x)
        r = [(predict(ps[g], zs[g]) - zs[g]["demand"]) / np.sqrt(zs[g]["demand"] + 1) for g in groups]
        pen = np.sqrt(ridge) * (x - x_ref) / (np.abs(x_ref) + 1.0)   # rappel faible vers les valeurs neutres
        return np.r_[np.concatenate(r), pen]

    best = None
    rng = np.random.default_rng(seed)
    for s in range(starts):
        x0 = x_ref * (1 + (0.2 * rng.normal(size=len(x_ref)) if s else 0))
        o = least_squares(res, x0)
        if best is None or o.cost < best.cost:
            best = o
    return unpack(best.x)


def predict_joint(params, d):
    out = pd.Series(np.nan, index=d.index)
    for (reg, tech), t in d.groupby(["region", "tech"]):
        p = params.get((reg, tech)) or params.get((reg, "Hybride")) or params.get((reg, "Thermique"))
        if p is not None and len(t) > 1:
            out.loc[t.index] = predict(p, t)
    return out
