"""Test de rejeu du moteur structurel (model/engine.py).

On donne au moteur les décisions réelles des 12 équipes d'un tour et on compare
la demande simulée, puis les classements, à la réalité.
  - mode « calé »    : paramètres ajustés sur tous les tours (le moteur sait-il reproduire le passé ?)
  - mode « aveugle » : paramètres ajustés sur les tours antérieurs seulement (sait-il prédire ?)

Deux erreurs sont publiées en mode aveugle :
  - erreur_volume_pct : répartition entre équipes seule, la taille réelle de chaque marché étant donnée ;
  - erreur_chaine_pct : chaîne complète, la taille des marchés étant elle aussi prévue (model/market.py).
    C'est cette seconde erreur qui dit ce que vaut une prévision de demande faite avant le tour.
"""
import sys
import warnings

import numpy as np
import pandas as pd

from model import engine as E
from model import market
from model.sim import fit_params, params_for, team_zone
from model.panel2 import build

warnings.filterwarnings("ignore")
NAMES = {1: "Entraînement", **{i + 1: f"Tour {i}" for i in range(1, 11)}}
FREE = ["k", "g", "f", "a", "c", "h", "s", "q", "cert"]


def free_for(train, tech):
    free = list(FREE)
    if train["lqual"].abs().sum() == 0:
        free.remove("q")
    if train["cert1"].sum() == 0:
        free.remove("cert")
    if train["esg"].abs().max() < 0.05:
        free.remove("s")          # ESG pas encore actif : on garde le multiplicateur publié tel quel (s = 1)
    if train["p_share"].isna().all() or (train["p_share"].fillna(1 / 12).round(4) == round(1 / 12, 4)).all():
        free.remove("h")
    if tech != "Thermique" and train["p_share"].isna().any() and not train["p_share"].isna().all():
        free.append("new")
    return free


def simulate(test, train, ridge=0.02):
    params = fit_params(train, ridge=ridge)          # même calage que la recherche : repli sur l'Hybride sous 12 observations
    t = test.copy()
    t["sim_demand"] = np.nan
    for (reg, tech), g in t.groupby(["region", "tech"]):
        if len(g) > 1:                               # un vendeur seul : rien à répartir
            t.loc[g.index, "sim_demand"] = E.predict(params_for(params, reg, tech), g)
    return t[t["sim_demand"].notna()]


def spearman(a, b):
    return np.corrcoef(pd.Series(a).rank(), pd.Series(b).rank())[0, 1]


def team_table(t):
    t = t.copy()
    fill = (t["sales"] / t["demand"]).clip(upper=1)
    unit = ((t["rev"] - t["cogs"]) / t["sales"]).where(t["sales"] > 0, 0)
    t["sim_contrib"] = unit * t["sim_demand"] * fill - t["adv"]
    t["real_contrib"] = unit * t["sales"] - t["adv"]
    g = t.groupby("team").agg(dem_reel=("demand", "sum"), dem_sim=("sim_demand", "sum"), marge_reelle=("real_contrib", "sum"), marge_sim=("sim_contrib", "sum"))
    for c in list(g.columns):
        g["rg_" + c] = g[c].rank(ascending=False).astype(int)
    return g


def pdm_points(test, sim, col):
    """Critère « part de marché » du barème (3 zones x 12 équipes) : points prévus contre points réels.
    Ventes prévues = demande simulée x taux de service réel ; un vendeur seul dans sa cellule garde sa demande réelle.
    Renvoie (écart moyen en points, nombre de cas exacts sur 36)."""
    t = test.copy()
    t["x"] = sim[col].reindex(t.index).fillna(t["demand"])
    t["v"] = t["x"] * (t["sales"] / t["demand"]).clip(upper=1).fillna(1)
    m = team_zone(t, "x", "v").merge(team_zone(t, "demand", "sales"), on=["team", "region"], suffixes=("_sim", "_reel"))
    return float((m["points_sim"] - m["points_reel"]).abs().mean()), int((m["points_sim"] == m["points_reel"]).sum())


def run(mode, d, rounds, verbose=False):
    rows = []
    for r in rounds:
        test = d[d["round"] == r]
        train = d[d["round"] < r] if mode == "aveugle" else d
        sim = simulate(test, train)
        g = team_table(sim)
        err = (sim["sim_demand"] - sim["demand"]).abs().sum() / sim["demand"].sum() * 100
        chain = np.nan
        if mode == "aveugle" and r >= 3 and r in market.ANNOUNCED:
            # chaîne complète : taille des cellules prévue avec l'historique antérieur, puis répartition aveugle
            mk = market.forecast(market.blind_frame(d, r), market.ANNOUNCED[r], hist=market.history().loc[:r - 1])
            cell = sim["region"] + "|" + sim["tech"]
            full = sim["sim_demand"] / sim.groupby(cell)["demand"].transform("sum") * cell.map(mk)
            sim = sim.assign(sim_demand_chaine=full)
            chain = (full - sim["demand"]).abs().sum() / sim["demand"].sum() * 100
        pdm, pdm_ok = pdm_points(test, sim, "sim_demand_chaine" if "sim_demand_chaine" in sim else "sim_demand")
        rows.append(dict(mode=mode, tour=NAMES[r], erreur_volume_pct=err, erreur_chaine_pct=chain, pdm_ecart_points=pdm, pdm_exacts_sur_36=pdm_ok,
                         classement_ventes_exact=int((g.rg_dem_reel == g.rg_dem_sim).sum()),
                         ventes_a_1_rang=int(((g.rg_dem_reel - g.rg_dem_sim).abs() <= 1).sum()), rho_ventes=spearman(g.dem_reel, g.dem_sim),
                         classement_marge_exact=int((g.rg_marge_reelle == g.rg_marge_sim).sum()),
                         marge_a_1_rang=int(((g.rg_marge_reelle - g.rg_marge_sim).abs() <= 1).sum()), rho_marge=spearman(g.marge_reelle, g.marge_sim)))
        if verbose:
            print(f"\n=== {NAMES[r]} ({mode}) ===")
            print(g[["rg_dem_reel", "rg_dem_sim", "dem_reel", "dem_sim", "rg_marge_reelle", "rg_marge_sim", "marge_reelle", "marge_sim"]]
                  .sort_values("rg_marge_reelle").round(0).astype(int).to_string())
        sim.to_csv(f"out/rejeu_{mode}_{r}.csv", index=False)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    if "--exante" in sys.argv:           # prévision de notre demande dans les conditions réelles (concurrents et état inconnus)
        import exante
        exante.main([a for a in sys.argv[1:] if a != "--exante"])
        sys.exit()
    d = build()
    rounds = sorted(r for r in d["round"].unique() if r >= 2)
    pd.set_option("display.width", 250)
    res = pd.concat([run("calé", d, rounds, verbose="-v" in sys.argv), run("aveugle", d, rounds, verbose="-v" in sys.argv)])
    print("\n=== Synthèse (12 équipes) ===")
    print(res.round(2).to_string(index=False))
    market.backtest(d)
