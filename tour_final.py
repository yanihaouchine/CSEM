"""Point de la frontière marketing, demande attendue, plan de production et décisions à saisir, pour une gamme quelconque.

  python3 tour_final.py 8                  # calcule et écrit out/tour8_strategie.json (rien n'est saisi sur la plateforme)
  python3 tour_final.py 8 --n 15 --rapide  # moins de scénarios, 4 zones de confiance au lieu de 8

Remplace les scripts des tours 5 et 6, câblés sur 6 produits Thermique + Hybride. La gamme est celle de nos produits du dernier
tour, ou celle de `lineup` dans data/tour_N_inputs.json :
    "lineup": {"USA": ["Hybride", "Hydrogène"], "Chine": ["Hybride", "Électrique"], "Europe": ["Électrique", "Hydrogène"]},
    "new_products": {"USA|Hydrogène": [52000, 3, 500]},     # prix (monnaie locale), équipements, publicité (M USD) de départ
    "entrants": 4                                           # concurrents supposés entrer dans nos cellules nouvelles,
                                                            # ou {"USA|Hydrogène": 3, ...} pour n'importe laquelle de nos cellules
`mc`, `fx`, `growth`, `max_feat` doivent couvrir tous nos produits (coûts lus sur la plateforme, hors équipements).

Choix du point : celui qui garde le meilleur gain dans le pire de trois mondes (moteur tel quel, clients 30 % plus
sensibles au prix, marchés 15 % plus petits), par rapport aux décisions reconduites. L'optimum à bornes larges
n'est jamais retenu.
"""
import argparse
import json
import warnings

import numpy as np
import pandas as pd

import offre as O
import strategy as S
from cesim.client import ROOT
from model import market, sim
from model.panel2 import build

warnings.filterwarnings("ignore")
AREA = {"USA": "area1", "Chine": "area2", "Europe": "area3"}
TECH = {"Thermique": "tech1", "Hybride": "tech2", "Électrique": "tech3", "Hydrogène": "tech4"}
BEHAVIOURS = ["statu quo", "tendance", "guerre des prix", "montée en gamme", "meilleure réponse", "mélange"]


def scenarios(d, params, inputs, n_per, seed=11):
    """Scénarios pour notre gamme : celle de `inputs["lineup"]` si elle est donnée, sinon nos produits du dernier tour."""
    base = sim.status_quo_frame(d)
    lineup = inputs.get("lineup") or O.current_lineup(base)
    start = {c: tuple(v) for c, v in inputs.get("new_products", {}).items()}
    sc, new, borrowed = O.scenarios(d, params, inputs, lineup, n_per=n_per, entrants=inputs.get("entrants", 0), seed=seed, start=start)
    return sc, new, borrowed


def world(sc, kscale=1.0, mscale=1.0):
    w = S._subset(sc, np.ones(len(sc.labels), bool))
    w.z = dict(sc.z)
    w.z["k"], w.z["M"] = sc.z["k"] * kscale, sc.z["M"] * mscale
    return w


def choose(sc, front):
    """Gain de chaque point de la frontière dans trois mondes, par rapport aux décisions reconduites."""
    worlds = {"moteur tel quel": world(sc), "clients 30 % plus sensibles au prix": world(sc, 1.3), "marchés 15 % plus petits": world(sc, 1.0, 0.85)}
    R = pd.DataFrame({name: {w: float(ws.profit(np.array(x)).mean()) for w, ws in worlds.items()} for name, x in front.items()}).T
    G = R - R.loc["reconduit"]
    G["pire monde"] = G.min(1)
    return G, G.drop(index=[i for i in G.index if i == "bornes larges"])["pire monde"].idxmax()


def run(tour, n_per=25, quantile=None, rapide=False, verbose=True, objectif="points"):
    d = build()
    d = d[d["round"] < tour + 1]
    params = sim.fit_params(d)
    inputs = json.load(open(ROOT / "data" / f"tour_{tour}_inputs.json"))
    sc, new, borrowed = scenarios(d, params, inputs, n_per)
    inp, cells = sc.inputs, sc.cells
    B = inp.get("behaviours", BEHAVIOURS)
    if verbose:
        print(f"Tour {tour} — produits : {', '.join(cells)}" + (f" ; nouveaux : {', '.join(new)}" if new else ""))
        for b in borrowed:
            print(f"  valeur reprise faute de saisie : {b}")
    radii = (0.0, 0.03, 0.06, 0.10, 0.15, 0.20, 0.30, None) if not rapide else (0.0, 0.06, 0.15, None)
    bareme = None
    if objectif == "points":                              # objectif : espérance de nos points au barème de l'instructeur
        import objectif as OB
        bareme = OB.Bareme(sc, tour)
    F, xs = S.frontier(sc, inp, B, radii=radii, verbose=verbose, objectif=bareme.score if bareme else None)
    G, best = choose(sc, xs)
    worst = best                                          # point de l'ancienne règle (pire de trois mondes, en marge)
    if bareme:                                            # règle en points : meilleure espérance, hors optimum à bornes larges
        # zone de confiance plafonnée (`bareme.rayon_max`, défaut ±6 %) : en contre-épreuve avec les concurrents réels
        # (python3 objectif.py --tour N), ±6 % donne +14 points au tour 5 et +7 au tour 6, ±15 % seulement +12 et +2
        rmax = inp.get("bareme", {}).get("rayon_max", 0.06) * 100 + 1e-9
        rayon = lambda k: 0.0 if k == "reconduit" else (1e9 if k == "bornes larges" else float(k.strip("± %")))
        pts = {k: bareme.score(S.tidy(np.array(v), cells)) for k, v in xs.items() if rayon(k) <= rmax}
        best = max(pts, key=pts.get)
        G["points"] = pd.Series({k: bareme.score(S.tidy(np.array(v), cells)) for k, v in xs.items()})
    x = S.tidy(np.array(xs[best]), cells)                 # valeurs saisissables (prix à 100 ou 1 000, publicité à 50 M USD)
    if verbose:
        pd.set_option("display.width", 250)
        print("\nGain par rapport aux décisions reconduites, M USD :")
        print(G.round(0).astype(int).to_string())
        print(f"\nPoint retenu : {best}" + (f" (objectif : points ; la règle en marge, pire de trois mondes, aurait retenu {worst})" if bareme else ""))
        if bareme:
            D = pd.concat({"reconduit": bareme.detail(S.tidy(sc.current, cells)), best: bareme.detail(x)}, axis=1)
            D[("écart", "points")] = D[(best, "points")] - D[("reconduit", "points")]
            print("\nPoints attendus par critère (concurrents : dernier tour + bruit ; erreur de rejeu environ 1,5 point par critère) :")
            print(D.round(2).to_string())
            Dt = D.drop("suite (tours suivants)", errors="ignore")       # la ligne « suite » porte sur les tours suivants, hors total du tour
            print(f"Total du tour : reconduit {Dt[('reconduit', 'points')].sum():.1f} -> {best} {Dt[(best, 'points')].sum():.1f}")
            if "suite (tours suivants)" in D.index:
                print(f"Tours suivants ({bareme.horizon} tour(s), poids {bareme.w_suite:.2f}) : {D.loc['suite (tours suivants)', (best, 'points')]:+.2f} point(s) dus à l'état laissé (part de marché, fonds propres, cours).")
            print("Bilan : " + (f"{bareme.fin['source']} ; découvert et indépendance financière recalculés dans chaque scénario." if bareme.fin
                                else "prévisionnel de la plateforme non lu (data/previsionnel_tourN.json absent) ; découvert et indépendance financière repris du dernier tour."))

    # quantile de la demande couvert par la production : celui qui maximise les points (stocks + demande non servie
    # + effet financier) quand l'objectif est le barème ; 0,75 avec l'ancien objectif ; --quantile force une valeur
    prod_table = None
    if quantile is None:
        quantile = 0.75
        if bareme:
            prod_table, quantile = bareme.production(x)
            if verbose:
                print("\nProduction : quantile de la demande à couvrir (k unités ; points attendus) :")
                print(prod_table.round(2).to_string())
                print(f"Quantile retenu : {quantile:.0%}")

    # demande attendue et parts de marché à saisir page Demande (en % du total prévu de la zone)
    m, cont, q, sales = sc.profit(x, detail=True)
    hist = market.history()
    last = int(d["round"].max())
    growth = inp["growth"]
    zone_total = {r: float(hist.loc[(last, r)].sum()) * (1 + growth[r]) for r in S.REGIONS}
    dem = {c: dict(moy=round(float(q[:, i].mean())), p10=round(float(np.quantile(q[:, i], .1))), p50=round(float(np.quantile(q[:, i], .5))),
                   plan=round(float(np.quantile(q[:, i], quantile))), p90=round(float(np.quantile(q[:, i], .9)))) for i, c in enumerate(cells)}
    shares = {c: round(dem[c]["moy"] / zone_total[c.split("|")[0]] * 100, 1) for c in cells}
    T = pd.DataFrame({c: dict(prix=x[i, 0], equip=x[i, 1], pub=x[i, 2], avant_prix=sc.current[i, 0], avant_equip=sc.current[i, 1], avant_pub=sc.current[i, 2],
                              **dem[c], pdm=shares[c]) for i, c in enumerate(cells)}).T
    if verbose:
        print(T.to_string())
        print(f"Marge du tour (moyenne des scénarios) : {m.mean():.0f} M USD ; P10 {np.quantile(m, .1):.0f}.")

    # décisions de la plateforme
    dec = {}
    for c, v in zip(cells, x):
        reg, tech = c.split("|")
        k = f"{AREA[reg]}.{TECH[tech]}"
        dec[f"{k}.price"], dec[f"{k}.feat"], dec[f"{k}.adv"] = int(v[0]), int(v[1]), int(v[2]) * 1000
        dec[f"{k}.share.est"] = shares[c]
    dec.update({"us.growth.prediction": growth["USA"] * 100, "asia.growth.prediction": growth["Chine"] * 100, "eu.growth.prediction": growth["Europe"] * 100})

    out = dict(point=best, objectif=objectif, quantile=quantile, production_points=(prod_table.round(3).to_dict("index") if prod_table is not None else None), points=(bareme.detail(x)["points"].round(2).to_dict() if bareme else None), cells=cells, strategy={c: [float(a) for a in v] for c, v in zip(cells, x)}, shares=shares, demand=dem,
               marge=float(m.mean()), gains=G.round(0).to_dict(), frontiere={k: np.array(v).tolist() for k, v in xs.items()}, decisions=dec)

    # plan de production (si les sources sont décrites dans les entrées du tour)
    prod = inp.get("production")
    if prod:
        fx = inp["fx"]
        prod = dict(prod, margin={c: float(v[0] * fx[c.split("|")[0]] - sim.FEAT_COST[c.split("|")[0]] * v[1]) for c, v in zip(cells, x)})
        flows, unmet = S.production_plan({c: dem[c]["plan"] for c in cells}, prod)
        src = {k: float(v) for k, v in flows.groupby("source").k_unites.sum().items()} if len(flows) else {}
        if verbose:
            print(f"\nPlan de production (demande couverte : quantile {quantile:.0%}) :")
            print(flows.to_string(index=False))
            print("sources :", src, "| non servi :", unmet)
        out.update(production=src, flows=flows.to_dict("records"), non_servi=unmet)
        for name, field in prod.get("fields", {}).items():              # source -> champ de la plateforme (% de capacité ou k unités)
            cap = prod.get("field_cap", {}).get(name)
            dec[field] = round(src.get(name, 0.0) / cap * 100 + 0.049, 1) if cap else int(round(src.get(name, 0.0)))
    elif verbose:
        print("\nPas de bloc `production` dans les entrées du tour : plan de production non calculé.")
    json.dump(out, open(ROOT / "out" / f"tour{tour}_strategie.json", "w"), indent=1, ensure_ascii=False)
    if verbose:
        print("\nDécisions (rien n'est saisi) :", json.dumps(dec, ensure_ascii=False))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("tour", type=int)
    ap.add_argument("--n", type=int, default=25, help="scénarios par comportement de concurrents")
    ap.add_argument("--quantile", type=float, default=None, help="quantile de la demande couvert par le plan de production (défaut : choisi en points, 0,75 avec --objectif marge)")
    ap.add_argument("--rapide", action="store_true")
    ap.add_argument("--objectif", choices=["points", "marge"], default="points", help="points du barème de l'instructeur (défaut) ou marge (ancienne règle)")
    a = ap.parse_args()
    run(a.tour, a.n, a.quantile, a.rapide, objectif=a.objectif)
