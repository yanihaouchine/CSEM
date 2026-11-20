"""Rejeu ex ante : que valait la prévision de NOTRE demande au moment de décider ?

  python3 exante.py                 # tours 2 à dernier tour publié
  python3 exante.py --tours 4 5 --n 40
  python3 backtest.py --exante     # même chose

Le rejeu aveugle de backtest.py donne au moteur les décisions réelles des 11 concurrents et notre état réel
(impact ESG, qualité des fournisseurs, certification). Au moment de décider on ne connaît ni les unes ni l'autre.
Ici le tour est rejoué comme `strategy.py` le voit : moteur calé sur les tours antérieurs, concurrents tirés
dans les comportements de model/rivals.py, taille des marchés prévue. Seules nos décisions marketing sont
les vraies. On compare la distribution de notre demande (P10, médiane, P90) à la demande réelle.

Variantes de notre état (lignes « état ») :
  reconduit : celui du tour précédent (ce que fait le simulateur sans saisie) ;
  saisi     : `our_state` de data/tour_N_inputs.json, tel qu'il avait été saisi avant le tour ;
  réel      : celui que les résultats ont publié (borne : ce que donnerait un état parfaitement prévu).
Variantes des concurrents : voir `CONFIGS` (entrées ajoutées à celles du tour).
"""
import argparse
import json
import warnings

import numpy as np
import pandas as pd

import strategy as S
from cesim.client import ROOT
from model import market, sim, state
from model.panel2 import build

warnings.filterwarnings("ignore")
US = sim.US
BEHAVIOURS = ["statu quo", "tendance", "guerre des prix", "montée en gamme", "meilleure réponse", "mélange"]
ORDER = ["Thermique", "Hybride", "Électrique", "Hydrogène"]
STATE = ["esg", "lqual", "cert1"]
STATE_SD = 0.06          # écart-type de l'erreur de prévision de notre impact ESG (rejeu de model/state.py : 4 à 10 points)
# configurations de concurrents comparées : nom -> entrées ajoutées
CONFIGS = {"actuel": {}}
CANDIDATS = {"actuel": {}, "+ règle apprise": {"behaviours": BEHAVIOURS + ["règle apprise"]},
             "règle apprise seule": {"behaviours": ["règle apprise"]}, "statu quo seul": {"behaviours": ["statu quo"]}}


def default_inputs(base, growth, cells):
    """Entrées minimales d'un tour sans fichier : taux de change et coûts repris du dernier rapport."""
    ours = base[base["team"] == US].set_index("cell")
    fx = base.groupby("region")["fx"].median().to_dict()
    mc = {c: float(np.nan_to_num(ours["unit_cost"].get(c, np.nan))) for c in cells}
    return dict(growth=dict(growth), fx=fx, mc=mc, max_feat={t: 10 for t in ORDER}, our_state={})


def load_inputs(tour, base, cells):
    f = ROOT / "data" / f"tour_{tour}_inputs.json"
    dflt = default_inputs(base, market.ANNOUNCED[tour + 1], cells)
    if not f.exists():
        return dflt, None
    inp = json.load(open(f))
    inp["mc"] = {**dflt["mc"], **inp.get("mc", {})}
    return inp, inp.get("our_state") or None


def replay(d_all, tour, n_per=30, configs=None, seed=0):
    """Rejoue un tour. Renvoie une ligne par (configuration, état, cellule)."""
    idx = tour + 1
    d = d_all[d_all["round"] < idx]
    params = sim.fit_params(d)
    real = d_all[(d_all["round"] == idx) & (d_all["team"] == US)].assign(c=lambda x: x["region"] + "|" + x["tech"]).set_index("c")
    cells = sorted(real.index, key=lambda c: (S.REGIONS.index(c.split("|")[0]), ORDER.index(c.split("|")[1])))
    x = real.loc[cells, ["price", "feat", "adv"]].values.astype(float)
    base = sim.with_products(sim.status_quo_frame(d), {c: tuple(v) for c, v in zip(cells, x)})
    inputs, typed = load_inputs(tour, base, cells)
    if inputs.get("entrants"):                   # changement de gamme : concurrents supposés entrer dans nos cellules nouvelles
        import offre
        mine = set(sim.status_quo_frame(d).query("team == @US")["cell"])
        base = offre.add_entrants(base, [c for c in cells if c not in mine], inputs["entrants"], np.random.default_rng(seed))
    prev_state = base[base["team"] == US].iloc[0][STATE].to_dict()
    states = {"reconduit": prev_state, "réel": real.iloc[0][STATE].to_dict()}
    if typed:
        states["saisi"] = {**prev_state, **typed}
    # prédit : impact ESG déduit de nos décisions publiées (model/state.py) ; énergie renouvelable au niveau « max »
    # quand nous étions au meilleur niveau ; certification connue au moment de décider ; qualité reconduite
    # (les notes des fournisseurs sont cachées avant le tour).
    P = state.panel()
    dec, now = state.decisions_of(US, idx, P), P[P["round"] == idx]
    niv = {"renouvelable": "max"} if dec["renouvelable"] != 0 and dec["renouvelable"] >= now["renouvelable"].max() - 1e-9 else {}
    pred = state.predict(dec, idx, US, P, niveaux=niv)
    states["prédit"] = {**prev_state, "esg": pred["esg"], "cert1": float(real.iloc[0]["cert1"])}
    rows = []
    for cname, extra in (configs or CONFIGS).items():
        inp = {**inputs, **extra, "our_state": {}}
        sc = S.Scenarios(d, params, inp, inp.get("behaviours", BEHAVIOURS), n_per=n_per, seed=seed, base=base, cells=cells)
        for sname, st in states.items():
            for k in STATE:                      # notre état est commun à nos produits : on le remplace dans les scénarios
                sc.z[k] = np.full_like(sc.z[k], float(st[k]))
            if sname == "prédit" and STATE_SD:   # incertitude de la prévision de notre impact ESG
                sc.z["esg"] = sc.z["esg"] + np.random.default_rng(seed + 1).normal(0, STATE_SD, (sc.z["esg"].shape[0], 1))
            q, _ = sc._demand(x)
            for i, c in enumerate(cells):
                p10, p50, p90 = np.quantile(q[:, i], [.1, .5, .9])
                r = float(real.loc[c, "demand"])
                rows.append(dict(tour=tour, concurrents=cname, etat=sname, cellule=c, reel=r, p10=p10, p50=p50, p90=p90,
                                 dans=bool(p10 <= r <= p90), rang=float((q[:, i] < r).mean())))
    return pd.DataFrame(rows)


def summary(T):
    """Par tour, configuration et état : biais et erreur de la médiane, part du réel dans P10-P90, rang moyen."""
    g = T.groupby(["concurrents", "etat", "tour"])
    s = pd.DataFrame(dict(biais_pct=(g["p50"].sum() / g["reel"].sum() - 1) * 100,
                          erreur_pct=g.apply(lambda t: (t["p50"] - t["reel"]).abs().sum() / t["reel"].sum() * 100),
                          dans_p10_p90=g["dans"].sum(), cellules=g["dans"].size(), rang_moyen=g["rang"].mean()))
    return s


def total(T):
    g = T.groupby(["concurrents", "etat"])
    return pd.DataFrame(dict(biais_pct=(g["p50"].sum() / g["reel"].sum() - 1) * 100,
                             erreur_pct=g.apply(lambda t: (t["p50"] - t["reel"]).abs().sum() / t["reel"].sum() * 100),
                             dans_p10_p90_pct=g["dans"].mean() * 100, rang_moyen=g["rang"].mean(), cellules=g["dans"].size()))


def run(tours=None, n_per=30, configs=None, verbose=True, save=True):
    d_all = build()
    tours = tours or [r - 1 for r in sorted(d_all["round"].unique()) if r >= 3]
    T = pd.concat([replay(d_all, t, n_per, configs) for t in tours], ignore_index=True)
    if save:
        T.to_csv(ROOT / "out" / "exante.csv", index=False)
    if verbose:
        pd.set_option("display.width", 250)
        print("\n=== Rejeu ex ante : notre demande, médiane des scénarios contre réel ===")
        print(summary(T).round(1).to_string())
        print("\n=== Ensemble des tours ===")
        print(total(T).round(2).to_string())
        print("\nrang_moyen : position du réel dans la distribution simulée (0,5 = centré ; proche de 0 = prévision trop haute).")
    return T


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tours", type=int, nargs="*")
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--candidats", action="store_true", help="compare les configurations de concurrents de CANDIDATS")
    ap.add_argument("-v", action="store_true")
    a = ap.parse_args(argv)
    T = run(a.tours, a.n, CANDIDATS if a.candidats else None, save=not a.candidats)
    if a.v:
        print(T.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
