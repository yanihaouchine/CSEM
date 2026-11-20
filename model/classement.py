"""Classement de l'instructeur (barème à points) : du PDF de la page Manuels vers un tableau exploitable.

  python3 -m model.classement data/docs/instructeur_2011/doc_3.pdf     # -> data/classement_instructeur.csv

Une ligne par (période, critère, équipe) : valeur publiée et points reçus (1 à 12, plus de points = mieux classé).
Les colonnes du PDF suivent toujours l'ordre des équipes de la plateforme ; aux premières périodes certaines équipes
portent encore un nom de couleur, on les rattache par leur position.
"""
import re
import subprocess
import sys

import pandas as pd

from cesim.client import ROOT

TEAMS = ["Ren'Auto", "AURA", "IronHorse", "YANAUTO", "tomobil", "GT-Automobile VI", "Vrooom Vroooom", "POLRAMOS", "Ça Roule",
         "BM2P - BMDoublePied", "TABCHOUR AUTO", "MO'THOR"]
SUMMARY = ("TOTAL POINTS", "total points cumul", "CLASSEMENT DU TOUR", "CLASSEMENT GÉNÉRAL", "Classement", "CLASSEMENT", "DECOUVERT")
# sens de chaque critère : +1 = plus c'est grand, mieux c'est ; -1 = l'inverse
SENS = {"DÉCOUVERT": -1, "DEMANDE INSATISFAITE EN VOLUME": -1, "STOCKS EN VOLUME": -1, "COÛT MOYEN UNITAIRE PONDÉRÉ": -1}


def cells(line):
    """Douze dernières cellules d'une ligne (séparées par au moins deux espaces), et l'intitulé qui précède."""
    parts = [p for p in re.split(r"\s{2,}", line.strip()) if p != ""]
    if len(parts) < 12:
        return None, None
    return " ".join(parts[:-12]).strip(), parts[-12:]


def number(x):
    x = x.replace(" ", "").replace(" ", "").replace("%", "").replace(",", ".")
    try:
        return float(x)
    except ValueError:
        return None


def parse(pdf):
    txt = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
    rows, period, pending = [], None, None
    for line in txt.splitlines():
        m = re.match(r"\s*(PERIODE TEST|P[ée]riode\s+(\d+))", line)
        if m:
            period, pending = (0 if m.group(2) is None else int(m.group(2))), None
            continue
        if period is not None and line.strip().startswith("CERTIFICATION"):
            pending = ("CERTIFICATION", None)          # les cellules « Pas de certification » sont coupées sur deux lignes
            continue
        lab, vals = cells(line)
        if vals is None or period is None:
            continue
        if lab.lower() == "points" and pending:
            crit, raw = pending
            if raw is None:
                raw = [{0: "Pas de certification", 2: "Bronze", 4: "Argent", 6: "Or"}.get(int(number(p) or 0), "?") for p in vals]
            n = sum(1 for r in rows if r["periode"] == period and r["equipe"] == TEAMS[0] and r["critere"].split(" #")[0] == crit)
            if n or (crit.startswith("COÛT MOYEN") and not crit.rstrip().endswith(")")):
                crit = f"{crit} #{n + 1}"                # intitulé tronqué dans le PDF : 1 = US, 2 = Asie, 3 = Europe
            for team, v, p in zip(TEAMS, raw, vals):
                rows.append(dict(periode=period, critere=crit, equipe=team, valeur=number(v), texte=v, points=number(p)))
            pending = None
        elif lab.startswith(SUMMARY) or lab.lower().startswith("total points"):
            for team, v in zip(TEAMS, vals):
                rows.append(dict(periode=period, critere=lab, equipe=team, valeur=number(v), texte=v, points=None))
        elif lab:
            pending = (lab, vals)
    df = pd.DataFrame(rows)
    df["sens"] = [next((s for k, s in SENS.items() if c.startswith(k)), 1) for c in df["critere"]]
    return df


def load():
    return pd.read_csv(ROOT / "data" / "classement_instructeur.csv")


def totals(df=None):
    """Points par période et cumul, par équipe (recalculés à partir des points par critère)."""
    df = load() if df is None else df
    p = df[df["points"].notna()].groupby(["periode", "equipe"])["points"].sum().unstack()
    return p


if __name__ == "__main__":
    df = parse(sys.argv[1])
    df.to_csv(ROOT / "data" / "classement_instructeur.csv", index=False)
    pd.set_option("display.width", 250)
    print(len(df), "lignes ;", df["periode"].nunique(), "périodes")
    print(df.groupby("periode")["critere"].nunique().to_dict())
    T = totals(df)
    print("points recalculés par période :"); print(T.astype(int).rename(columns=lambda c: c[:9]).to_string())
    pub = df[df["critere"].str.lower().str.startswith("total points de")].pivot_table(index="periode", columns="equipe", values="valeur", aggfunc="first")
    print("écart maximal avec le total publié :", float((T.reindex(columns=pub.columns) - pub).abs().max().max()))
    us = df[(df["equipe"] == "tomobil") & df["points"].notna()].pivot_table(index="critere", columns="periode", values="points", aggfunc="first")
    print(us.to_string())
