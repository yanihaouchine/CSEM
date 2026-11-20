"""Construit le panel (tour, zone, tech, équipe) à partir des pages de résultats."""
import json
import re

import numpy as np
import pandas as pd

from cesim.client import ROOT

REGIONS = ["USA", "Chine", "Europe"]
TECHS = ["Thermique", "Hybride", "Électrique", "Hydrogène"]


def num(c):
    c = c.replace(" ", "").replace(" ", "").replace("%", "").replace("+", "")
    try:
        return float(c)
    except ValueError:
        return np.nan


def load_rows(idx):
    return json.load(open(ROOT / "data" / "raw" / f"round_{idx}.json"))


def available_rounds():
    return sorted(int(f.stem.split("_")[1]) for f in (ROOT / "data" / "raw").glob("round_*.json"))


def build():
    recs, team_recs = [], []
    for idx in available_rounds():
        R = load_rows(idx)
        teams = next(r[1:13] for r in R if len(r) >= 13 and r[1] == "Ren'Auto" or (len(r) >= 13 and r[0] == "" and r[1]))
        sec, tech = None, None
        cell = {}
        esg = np.zeros(12)
        in_esg = False
        tv = {}
        for r in R:
            if not r:
                continue
            lab = r[0]
            vals = [num(c) for c in r[1:13]] if len(r) >= 13 else None
            has = vals is not None and not all(np.isnan(vals))
            m = re.match(r"Résultats par zone, (\w+)", lab)
            m2 = re.match(r"Répartition de la marge par Tech, M USD, (\w+)", lab)
            if m:
                sec, tech = ("zone", m.group(1)), None
            elif m2:
                sec, tech = ("marge", m2.group(1)), None
            elif lab.endswith("parts de marché, %") or lab.startswith("Rapport") or lab.startswith("Création de valeur") or lab.startswith("Détails sur"):
                sec = ("other", lab)
                tech = None
            if lab == "Impact sur la demande":
                in_esg = True
            if lab == "Score final":
                in_esg = False
            if in_esg and has:
                esg += np.log1p(np.nan_to_num(np.array(vals)) / 100)
            if sec and sec[0] in ("zone", "marge"):
                if lab in TECHS and not has:
                    tech = lab
                    continue
                if tech and has:
                    key = None
                    if sec[0] == "zone":
                        key = {"Prix de vente": "price", "Nombre d'équipements": "feat", "Ventes, k": "sales", "Demande, k": "demand"}
                    else:
                        key = {"Publicité": "adv", "Marge de contribution": "contrib", "Coût total de l'unité vendue": "cogs", "Chiffre d'affaires": "rev"}
                    for k, v in key.items():
                        if lab.startswith(k):
                            for t, x in zip(teams, vals):
                                cell.setdefault((sec[1], tech, t), {})[v] = x
            if has and lab.startswith(("Cours de l'action à la fin", "RÉSULTAT NET ANNUEL", "Bénéfice par action", "Ratio des fonds propres", "Dividende")) and lab not in tv:
                tv[lab] = vals
        for (reg, tech, t), d in cell.items():
            recs.append(dict(round=idx, region=reg, tech=tech, team=t, esg=esg[teams.index(t)], **d))
        for lab, vals in tv.items():
            for t, x in zip(teams, vals):
                team_recs.append(dict(round=idx, team=t, var=lab, value=x))
    df = pd.DataFrame(recs)
    df = df.sort_values(["region", "tech", "team", "round"])
    g = df.groupby(["round", "region", "tech"])
    df["mkt"] = g["demand"].transform("sum")
    df["share"] = df["demand"] / df["mkt"]
    df["prev_share"] = df.groupby(["region", "tech", "team"])["share"].shift(1)
    df["prev_adv"] = df.groupby(["region", "tech", "team"])["adv"].shift(1)
    df.to_csv(ROOT / "data" / "panel.csv", index=False)
    pd.DataFrame(team_recs).to_csv(ROOT / "data" / "teams.csv", index=False)
    return df


if __name__ == "__main__":
    df = build()
    pd.set_option("display.width", 250)
    print(df.shape)
    print(df[(df.team == "tomobil")].to_string())
    print(df.groupby(["round", "region", "tech"])[["demand", "sales", "price", "feat", "adv"]].agg({"demand": "sum", "sales": "sum", "price": "mean", "feat": "mean", "adv": "mean"}).to_string())
