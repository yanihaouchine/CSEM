"""Simulateur d'un tour complet : les 12 équipes décident, on obtient la demande,
les ventes et la marge de chacune.

Chaîne : décisions -> taille des marchés (model/market.py) -> répartition entre équipes
(mêmes formules que model/engine.py) -> ventes -> marge de contribution.
"""
import warnings

import numpy as np
import pandas as pd

from model import engine as E
from model.panel2 import build

warnings.filterwarnings("ignore")

US = "tomobil"
REGIONS = ["USA", "Chine", "Europe"]
FEAT_COST = {"USA": 700.0, "Chine": 650.0, "Europe": 750.0}
PCOLS = ["k", "g", "f", "a", "c", "h", "s", "q", "cert", "new", "lam", "u"]


# ------------------------------------------------------------------ paramètres
def shared_free(train):
    free = ["g_USA", "g_Chine", "g_Europe"]
    if train["has_o"].sum() > 0:
        free.append("lam")
    if train["esg"].abs().max() >= 0.05:
        free += ["s_USA", "s_Chine", "s_Europe"]
    if (train["p_fill"] < 0.99).sum() >= 3:
        free.append("u")
    if train["lqual"].abs().sum() > 0:
        free += ["q_USA", "q_Chine", "q_Europe"]
    if train["cert1"].sum() > 0:
        free.append("cert")
    if train["p_share"].isna().any():
        free.append("new")
    return free


MIN_OBS = 30     # en dessous, les paramètres d'une cellule (zone, tech) ne sont pas fiables : repli sur l'Hybride de la zone.
                 # 12 jusqu'au tour 7 ; relevé à 30 ensuite : au tour 7, en aveugle, l'Électrique de Chine (14 observations)
                 # fait 15,1 % d'erreur avec ses paramètres propres et 11,2 % avec ceux de l'Hybride. Tours 2 à 6 inchangés.


def fit_params(d, ridge=0.02):
    """Paramètres du moteur par (zone, tech), ajustés sur l'historique `d`.
    Une technologie observée moins de MIN_OBS fois dans une zone n'a pas de paramètres propres : `params_for` lui
    donne ceux de l'Hybride de la zone (rejeu aveugle de l'Électrique, tours 4 et 5 : 55, 9 et 47 % d'erreur avec
    le repli, contre 68, 10 et 59 % avec des paramètres ajustés sur 1 à 3 observations)."""
    n = d.groupby(["region", "tech"])["team"].transform("size")
    d = d[((n >= MIN_OBS) | d["tech"].isin(["Thermique", "Hybride"])).values]
    # les cellules trop peu observées sortent du calage lui-même : avec 5 paramètres pour 1 à 3 observations
    # elles rendaient le problème dégénéré (141 s au lieu de 3 s pour le calage aveugle du tour 6). Les paramètres du
    # Thermique et de l'Hybride n'en changent pas : prévisions ex ante identiques sur 3 graines aux tours 4 à 6.
    return E.fit_joint(d, shared_free(d), ridge=ridge)


def params_for(params, region, tech):
    return params.get((region, tech)) or params.get((region, "Hybride")) or params[(region, "Thermique")]


# ------------------------------------------------------------------ formule d'attraction (vectorisée)
def u_row(p, info, price, feat, adv, adv_o):
    """Log-attraction d'un produit. `p` et `info` : dicts de scalaires ou de tableaux diffusables."""
    return (-p["k"] * (price / info["ref_price"]) ** p["g"] + p["f"] * np.log(feat)
            + p["a"] * np.log(adv + p["lam"] * adv_o + np.abs(p["c"]))
            - p["u"] * info["unmet"] + p["h"] * info["lprev"] + p["new"] * info["isnew"]
            + p["s"] * info["esg"] + p["q"] * info["lqual"] + p["cert"] * info["cert1"])


# ------------------------------------------------------------------ état et cadre du tour suivant
def status_quo_frame(d, last=None):
    """Lignes (équipe, zone, tech) du tour suivant, chaque équipe répétant ses dernières décisions."""
    last = last or d["round"].max()
    t = d[d["round"] == last].copy()
    wm = (t["price"] * t["demand"]).groupby(t["cell"]).transform("sum") / t.groupby("cell")["demand"].transform("sum")
    f = pd.DataFrame(dict(
        round=last + 1, region=t["region"].values, tech=t["tech"].values, team=t["team"].values,
        price=t["price"].values, feat=t["feat"].values, adv=t["adv"].values,
        p_price=t["price"].values, p_feat=t["feat"].values, p_adv=t["adv"].values,
        p_share=t["share"].values, p_fill=t["fill"].fillna(1).values, ref_price=wm.values,
        esg=t["esg"].values, lqual=t["lqual"].values, cert1=t["cert1"].values,
        last_demand=t["demand"].values, last_sales=t["sales"].values,
        # coût unitaire hors équipements (USD) et taux de change implicite du dernier tour
        fx=np.where(t["sales"] > 0, t["rev"] / (t["sales"] * t["price"]) * 1000, np.nan),
        unit_cost=np.where(t["sales"] > 0, t["cogs"] / t["sales"] * 1000, np.nan),
    ))
    f["fx"] = f.groupby("region")["fx"].transform(lambda x: x.fillna(x.median()))
    f["unit_cost"] = f["unit_cost"] - f["feat"] * f["region"].map(FEAT_COST)
    f["unit_cost"] = f.groupby(["region", "tech"])["unit_cost"].transform(lambda x: x.fillna(x.median()))
    f["cell"] = f["region"] + "|" + f["tech"]
    return finalize(f)


def finalize(f):
    """Recalcule ce qui dépend des décisions : publicité de l'autre produit de l'équipe sur le marché."""
    tot = f.groupby(["region", "team"])["adv"].transform("sum")
    f["adv_o"] = tot - f["adv"]
    f["has_o"] = (f.groupby(["region", "team"])["adv"].transform("size") > 1).astype(float)
    return f


def with_products(base, products, team=US):
    """Aligne les produits de `team` dans le cadre `base` sur `products` (dict `zone|tech` -> (prix, équipements,
    publicité)) : les produits absents du dict sont retirés, les nouveaux sont ajoutés avec ces décisions,
    les produits déjà présents gardent leurs décisions précédentes. Sert au lancement d'un modèle ou au changement
    de technologie (le cadre « statu quo » ne contient que les produits du tour précédent)."""
    mine = (base["team"] == team).values
    f = base[~mine | base["cell"].isin(list(products)).values].copy()
    ref = base[mine].iloc[0]
    new = []
    for cell, (price, feat, adv) in products.items():
        if ((f["team"] == team) & (f["cell"] == cell)).any():
            continue
        reg, tech = cell.split("|")
        same = base[base["cell"] == cell]
        new.append(dict(round=ref["round"], region=reg, tech=tech, team=team, price=price, feat=feat, adv=adv,
                        p_price=np.nan, p_feat=np.nan, p_adv=np.nan, p_share=np.nan, p_fill=1.0,
                        ref_price=same["ref_price"].iloc[0] if len(same) else price,   # cellule nouvelle : notre prix sert de repère
                        esg=ref["esg"], lqual=ref["lqual"], cert1=ref["cert1"], last_demand=np.nan, last_sales=np.nan,
                        fx=base.loc[base["region"] == reg, "fx"].median(),
                        unit_cost=same["unit_cost"].median() if len(same) else np.nan, cell=cell))
    if new:
        f = pd.concat([f, pd.DataFrame(new)], ignore_index=True)
    return finalize(f.reset_index(drop=True))


def row_info(f):
    return dict(ref_price=f["ref_price"].values, unmet=1.0 - f["p_fill"].values,
                lprev=np.log(f["p_share"].fillna(1 / 12).values * 12), isnew=f["p_share"].isna().values.astype(float),
                esg=f["esg"].values, lqual=f["lqual"].values, cert1=f["cert1"].values)


def row_params(f, params, scale=None):
    """Paramètres du moteur alignés sur les lignes de `f` ; `scale` = multiplicateurs par nom (scénarios)."""
    out = {k: np.array([params_for(params, r, t)[k] for r, t in zip(f["region"], f["tech"])], float) for k in PCOLS}
    for k, m in (scale or {}).items():
        out[k] = out[k] * m
    return out


# ------------------------------------------------------------------ simulation complète
def simulate_round(f, params, markets, scale=None, supply=None):
    """Demande, ventes et marge de chaque ligne de `f` (décisions des 12 équipes).

    markets : dict cellule -> taille du marché (k unités) ; supply : dict (équipe, tech) -> offre mondiale max.
    """
    f = finalize(f.copy())
    p = row_params(f, params, scale)
    u = u_row(p, row_info(f), f["price"].values, f["feat"].values, np.maximum(f["adv"].values, 1.0), f["adv_o"].values)
    cells, inv = np.unique(f["cell"].values, return_inverse=True)
    A = np.exp(u - u.max())
    share = A / np.bincount(inv, A)[inv]
    f["sim_demand"] = share * f["cell"].map(markets).values
    f["sim_sales"] = f["sim_demand"] * (f["p_fill"].clip(0.6, 1) if supply is None else 1.0)
    if supply:
        for (team, tech), cap in supply.items():
            m = (f["team"] == team) & (f["tech"] == tech)
            tot = f.loc[m, "sim_demand"].sum()
            if tot > cap:
                f.loc[m, "sim_sales"] = f.loc[m, "sim_demand"] * cap / tot
    unit_margin = f["price"] * f["fx"] - f["unit_cost"] - f["feat"] * f["region"].map(FEAT_COST)
    f["sim_margin"] = unit_margin * f["sim_sales"] / 1000 - f["adv"]
    return f


def team_zone(f, demand="sim_demand", sales="sim_sales"):
    """Par équipe et par zone, toutes technologies confondues : demande, ventes, chiffre d'affaires (M USD) et part de
    marché (%). C'est l'entrée des trois critères « part de marché » du barème de l'instructeur.

    La part publiée (« Résultats par zone > parts de marché > Total ») se calcule sur les VENTES : ventes de l'équipe /
    ventes totales de la zone. Vérifié aux tours 4 à 6 sur les 12 équipes : écart maximal 0,011 point (arrondi), contre
    0,8 à 7,4 points si on la calcule sur la demande. Une rupture de stock coûte donc de la part de marché notée.
    `f` : sortie de simulate_round, ou le panel d'un tour avec demand="demand", sales="sales"."""
    g = f.assign(_d=f[demand], _s=f[sales], _ca=f[sales] * f["price"] * f["fx"] / 1000 if "fx" in f else np.nan)
    out = g.groupby(["team", "region"]).agg(demande=("_d", "sum"), ventes=("_s", "sum"), ca=("_ca", "sum"), produits=("_s", "size")).reset_index()
    out["part"] = out["ventes"] / out.groupby("region")["ventes"].transform("sum") * 100
    out["rang"] = out.groupby("region")["part"].rank(ascending=False, method="min").astype(int)
    out["points"] = 1 + (out.groupby("region")["part"].rank(method="min") - 1).astype(int)   # barème : 1 + équipes strictement moins bonnes
    return out


def check(verbose=True):
    """Rejoue chaque tour passé avec les décisions réelles et compare aux résultats publiés."""
    d = build()
    params = fit_params(d)
    rows = []
    for r in sorted(d["round"].unique()):
        if r < 2:
            continue
        t = d[d["round"] == r].copy()
        t["fx"] = np.where(t["sales"] > 0, t["rev"] / (t["sales"] * t["price"]) * 1000, np.nan)
        t["fx"] = t.groupby("region")["fx"].transform(lambda x: x.fillna(x.median()))
        t["unit_cost"] = np.where(t["sales"] > 0, t["cogs"] / t["sales"] * 1000, 0) - t["feat"] * t["region"].map(FEAT_COST)
        markets = t.groupby("cell")["demand"].sum().to_dict()
        t["cell_full"] = t["cell"]
        s = simulate_round(t, params, markets)
        s["sim_sales"] = s["sim_demand"] * s["fill"].fillna(1)
        s["sim_margin"] = (s["price"] * s["fx"] - s["unit_cost"] - s["feat"] * s["region"].map(FEAT_COST)) * s["sim_sales"] / 1000 - s["adv"]
        real = (s["rev"] - s["cogs"]).fillna(0) - s["adv"].fillna(0)
        g = s.assign(real=real).groupby("team").agg(dem=("demand", "sum"), sim_dem=("sim_demand", "sum"), marge=("real", "sum"), sim_marge=("sim_margin", "sum"))
        rows.append(dict(tour=r - 1, err_volume=(s["sim_demand"] - s["demand"]).abs().sum() / s["demand"].sum() * 100,
                         err_marge=(g.sim_marge - g.marge).abs().sum() / g.marge.abs().sum() * 100,
                         rang_marge_exact=int((g.marge.rank() == g.sim_marge.rank()).sum())))
    out = pd.DataFrame(rows)
    if verbose:
        print(out.round(2).to_string(index=False))
    return out


if __name__ == "__main__":
    check()
