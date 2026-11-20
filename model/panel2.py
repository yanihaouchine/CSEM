"""Panel enrichi : composantes ESG séparées (décisions vs résultats) et valeurs du tour précédent."""
import json
import re

import numpy as np
import pandas as pd

from cesim.client import ROOT
from model.panel import available_rounds, num

PREV = {1: 0, 2: 0, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 7, 9: 8, 10: 9, 11: 10}
# composantes qui dépendent directement d'une décision du tour / d'un résultat du tour
ESG_DEC = ["Utilisation d'énergie renouvelable", "Recyclabilité des produits", "Améliorations des processus",
           "Image de l'entreprise", "Politiques du travail", "Politiques des fournisseurs", "Rémunération des employés"]
ESG_OUT = ["Impact environnemental des unités vendues", "Efficacité opérationnelle", "Rotation des employés"]


def esg_components(idx):
    R = json.load(open(ROOT / "data" / "raw" / f"round_{idx}.json"))
    teams, on, out = None, False, {}
    for r in R:
        if not r:
            continue
        if r[0] == "Rapport ESG":
            on = True
        elif r[0] == "Score final":
            on = False
        if len(r) >= 13 and r[1] == "Ren'Auto":
            teams = r[1:13]
        if on and len(r) >= 13 and "%" in "".join(r[1:13]):
            out[r[0]] = np.log1p(np.nan_to_num(np.array([num(c) for c in r[1:13]])) / 100)
    rows = []
    for i, t in enumerate(teams):
        dec = sum(v[i] for k, v in out.items() if k.startswith(tuple(ESG_DEC)))
        res = sum(v[i] for k, v in out.items() if k.startswith(tuple(ESG_OUT)))
        rows.append(dict(round=idx, team=t, esg_dec=dec, esg_out=res))
    return pd.DataFrame(rows)


CERT = {"Pas de": 0, "Bronze": 1, "Argent": 2, "Or": 3, "Platine": 4}


def visible_decisions(idx):
    """Décisions des équipes lisibles dans les rapports : qualité fournisseurs, certification, engagement."""
    R = json.load(open(ROOT / "data" / "raw" / f"round_{idx}.json"))
    teams = next(r[1:13] for r in R if len(r) >= 13 and r[1] == "Ren'Auto")
    row = lambda lab: next((r for r in R if r and r[0].startswith(lab)), None)
    q, cert, eng = row("Qualité"), row("Certitications"), row("Engagement")
    out = []
    for i, t in enumerate(teams):
        qual = num(q[1 + i]) if q else np.nan
        out.append(dict(round=idx, team=t, qual=3.0 if not qual or np.isnan(qual) else qual,
                        cert=next((v for k, v in CERT.items() if cert and cert[1 + i].startswith(k)), 0),
                        engage=1.0 if eng and eng[1 + i].strip() else 0.0))
    return pd.DataFrame(out)


def esg_hidden(E):
    """Tours où le rapport publie des impacts ESG tous nuls (à partir du tour 7) : l'effet existe toujours, il n'est
    plus publié. Rejeu aveugle du tour 7 : 12,3 % d'erreur de répartition avec un impact nul, 8,0 % avec l'impact du
    tour précédent, 7,7 % avec un impact déduit des scores E, S, G du tour, 7,2 % avec la moyenne des deux (retenue).
    Impact déduit des scores : régression, sur les tours où il est publié, de l'impact sur les écarts relatifs des
    scores E, S, G à la moyenne des 12 équipes (coefficients proches de 0,8 / 0,2 / 0,2)."""
    E = E.sort_values(["round", "team"]).reset_index(drop=True)
    mx = E.groupby("round")["esg_dec"].apply(lambda x: x.abs().max())
    hidden = [r for r in mx.index if r >= 4 and mx[r] < 1e-9]
    E["esg_cache"] = E["round"].isin(hidden)
    if not hidden:
        return E
    from model.report import table
    S = [table(f"Rapport ESG > Score final > {c}") for c in ("Environnement (E)", "Social (S)", "Gouvernance (G)")]
    rel = lambda r, t: [s.loc[r, t] / s.loc[r].mean() - 1 for s in S]
    known = E[(E["round"] >= 4) & ~E["esg_cache"]]
    b = np.linalg.lstsq(np.array([rel(r, t) for r, t in zip(known["round"], known["team"])]), known["esg_dec"].values, rcond=None)[0]
    for r in sorted(hidden):                              # dans l'ordre : un tour caché sert de « précédent » au suivant
        prev = E[E["round"] == PREV.get(r, r - 1)].set_index("team")["esg_dec"]
        m = E["round"] == r
        E.loc[m, "esg_dec"] = [0.5 * prev.get(t, 0.0) + 0.5 * float(np.dot(rel(r, t), b)) for t in E.loc[m, "team"]]
    return E


def build(rounds=None):
    rounds = rounds or available_rounds()
    df = pd.read_csv(ROOT / "data" / "panel.csv")
    df = df.drop(columns=["prev_share", "prev_adv", "esg"]).merge(esg_hidden(pd.concat([esg_components(i) for i in rounds])), on=["round", "team"])
    df = df.merge(pd.concat([visible_decisions(i) for i in rounds]), on=["round", "team"])
    df["esg"] = df["esg_dec"]          # seuls les impacts liés aux décisions jouent sur la demande du tour
    # autre produit de la même équipe sur le même marché (ex. l'Hybride pour une ligne Thermique)
    live = df[df["demand"].notna() & (df["demand"] > 0)]
    tot = live.groupby(["round", "region", "team"]).agg(adv_all=("adv", "sum"), n_prod=("adv", "size")).reset_index()
    df = df.merge(tot, on=["round", "region", "team"], how="left")
    df["adv_o"] = (df["adv_all"] - df["adv"].fillna(0)).clip(lower=0).fillna(0)
    df["has_o"] = (df["n_prod"].fillna(1) > 1).astype(float)
    df["lqual"] = np.log(df["qual"] / 3.0)
    df["cert1"] = (df["cert"] >= 1).astype(float)
    key = ["region", "tech", "team"]
    df["pr"] = df["round"].map(PREV)
    df["fill"] = (df["sales"] / df["demand"]).clip(0, 1)
    prev = df[["round"] + key + ["share", "adv", "price", "feat", "fill"]].rename(
        columns={"round": "pr", "share": "p_share", "adv": "p_adv", "price": "p_price", "feat": "p_feat", "fill": "p_fill"})
    df = df.merge(prev, on=["pr"] + key, how="left")
    pe = df[["round", "team", "esg_dec", "esg_out"]].drop_duplicates().rename(columns={"round": "pr", "esg_dec": "p_esg_dec", "esg_out": "p_esg_out"})
    df = df.merge(pe, on=["pr", "team"], how="left")
    df[["p_esg_dec", "p_esg_out"]] = df[["p_esg_dec", "p_esg_out"]].fillna(0.0)
    df["p_fill"] = df["p_fill"].fillna(1.0)
    # prix de référence du marché = prix moyen (pondéré par la demande) du tour précédent :
    # ce sont les prix des concurrents qui fixent le repère des clients
    live = df[df["demand"].notna() & (df["demand"] > 0)]
    ref = (live.assign(pd_=live["price"] * live["demand"]).groupby(["round", "region", "tech"])
           .agg(pd_=("pd_", "sum"), dem=("demand", "sum")).reset_index())
    ref["ref_price"] = ref["pd_"] / ref["dem"]
    df = df.merge(ref[["round", "region", "tech", "ref_price"]].rename(columns={"round": "pr"}), on=["pr", "region", "tech"], how="left")
    df = df[df["demand"].notna() & (df["demand"] > 0) & (df["round"] > 0)].copy()
    df["cell"] = df["round"].astype(str) + "|" + df["region"] + "|" + df["tech"]
    df["ref_price"] = df["ref_price"].fillna(df.groupby("cell")["price"].transform("mean"))   # techno nouvelle : pas d'historique
    return df.reset_index(drop=True)


if __name__ == "__main__":
    d = build()
    print(d.shape)
    print(d[d.team == "tomobil"][["round", "region", "tech", "price", "feat", "adv", "demand", "p_share", "p_adv", "esg_dec", "esg_out", "p_esg_dec", "p_esg_out"]].round(3).to_string())
