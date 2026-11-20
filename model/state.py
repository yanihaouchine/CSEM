"""État de l'entreprise : ce que nos décisions hors marketing font à notre demande.

Le moteur (model/engine.py) utilise trois grandeurs par équipe : `esg` (somme des impacts ESG liés aux décisions,
en log), `lqual` (qualité des fournisseurs) et `cert1` (certification). Le simulateur les reprenait du tour
précédent ; or elles changent avec nos décisions, et c'était la première source d'erreur de la prévision
(rejeu ex ante : 19 % d'erreur avec l'état reconduit, 11 % avec l'état réel).

Règle du jeu observée (voir docs/comportement.md, section 7) : chaque impact ESG est relatif à la moyenne des 12 équipes,
    impact % = W x (note de l'équipe / note moyenne des équipes - 1),  W proche de 34,
et deux équipes aux décisions identiques reçoivent le même impact. La somme des impacts sur les 12 équipes est nulle.
Conséquence : une option garde à peu près son impact d'un tour au suivant, mais il s'érode quand les autres équipes
s'améliorent.

Prévision de l'impact d'une composante pour le tour r, à partir des tours < r :
  1. table du dernier tour : impact reçu par les équipes qui ont joué exactement la même option ;
  2. sinon, effets additifs des options du dernier tour (composantes à plusieurs décisions) ;
  3. sinon, dernier tour où l'option a été jouée ; sinon l'impact que nous avions (reconduit) ;
  fournisseurs : l'option est le jeu de fournisseurs actifs (leurs notes sont cachées avant le tour et changent
  d'un tour à l'autre ; la loi relative appliquée à la note du tour précédent fait moins bien que l'impact reconduit) ;
  énergie renouvelable et améliorations de processus : la décision n'est pas publiée, impact reconduit ;
  on peut donner un niveau (`niveaux={"renouvelable": "max"}` : impact de la meilleure équipe du dernier tour)
  ou un impact (`impacts={...}`) quand on change ces décisions. `valeurs(composante)` liste les impacts observés.
  `drift` ajoute l'érosion moyenne observée entre les deux derniers tours (0 = aucune, 1 = toute).

  python3 -m model.state        # rejeu aveugle de la prévision, pour les 12 équipes
"""
import json

import numpy as np
import pandas as pd

from cesim.client import ROOT
from model import esg

# composantes qui entrent dans `esg` du moteur (panel2.ESG_DEC) -> décisions publiées qui les déterminent
COMPONENTS = {
    "politiques": ["pol_reglement", "pol_relations", "pol_quotas"],
    "recyclabilite": ["directive", "engagement"],
    "formation": list(esg.TRN_COLS),
    "fournisseurs": ["jeu_fournisseurs"],
    "renouvelable": [],
    "processus": [],
    "remuneration": [],
}
SUPPLIERS = ["Maîtres Matérialistes", "Composants Colossaux", "Singularités Quantiques", "Fusions Dynamiques", "Innovation Réinventée"]   # ordre de la page Achats (supplier.1 à supplier.5)
W_REL = 34.0                 # impact % = W_REL x (note / moyenne - 1), mesuré sur les fournisseurs (33,6 à 34,9)
DRIFT = 0.5                  # érosion appliquée par défaut : 0,5 fait mieux que 0 et 1 au tour 5, seul tour qui le teste (preuve faible)
_PANEL = None


def panel():
    global _PANEL
    if _PANEL is None:
        df = esg.panel()
        df["f_durable"] = pd.to_numeric(df["f_durable"], errors="coerce")
        df["f_qualite"] = pd.to_numeric(df["f_qualite"], errors="coerce")
        sets = pd.concat([supplier_sets(r) for r in sorted(df["round"].unique())])
        _PANEL = df.merge(sets, on=["round", "team"], how="left")
    return _PANEL


def supplier_sets(idx):
    """Jeu de fournisseurs actifs de chaque équipe au tour d'indice idx (noms triés, séparés par « + »)."""
    R = json.load(open(ROOT / "data" / "raw" / f"round_{idx}.json"))
    teams = next(r[1:13] for r in R if len(r) >= 13 and r[1] == "Ren'Auto")
    i0 = next((i for i, r in enumerate(R) if r and r[0] == "Fournisseurs actifs"), None)
    i1 = next((i for i, r in enumerate(R) if r and r[0].startswith("Attributs des fournisseurs")), None)
    if i0 is None or i1 is None:
        return pd.DataFrame(dict(round=idx, team=teams, jeu_fournisseurs=np.nan))
    sup = [r for r in R[i0 + 1:i1] if r and r[0] in SUPPLIERS]
    return pd.DataFrame(dict(round=idx, team=teams, jeu_fournisseurs=["+".join(sorted(r[0] for r in sup if r[1 + i].strip())) for i in range(12)]))


def valeurs(comp, r=None, df=None):
    """Impacts observés pour une composante au dernier tour publié (ou au tour d'indice r) : valeur -> nombre d'équipes."""
    df = panel() if df is None else df
    r = r or df["round"].max()
    return df[df["round"] == r][comp].round(1).value_counts().sort_index(ascending=False).to_dict()


def _key(row, cols):
    return "|".join(str(row[c]) for c in cols)


def active(df, comp):
    """Tours où la composante agit (impacts non tous nuls)."""
    return sorted(r for r, t in df.groupby("round") if t[comp].abs().sum() > 0)


def decisions_of(team, r, df=None):
    """Décisions publiées de `team` au tour d'indice r (ligne du panel ESG)."""
    df = panel() if df is None else df
    t = df[(df["team"] == team) & (df["round"] == r)]
    return None if t.empty else t.iloc[0].to_dict()


def _erosion(df, comp, cols, s):
    """Variation moyenne de l'impact d'une même option entre les deux derniers tours connus."""
    act = [x for x in active(df, comp) if x <= s]
    if len(act) < 2 or not cols:
        return 0.0
    a = df[df["round"] == act[-2]].assign(k=lambda t: t.apply(_key, axis=1, cols=cols)).groupby("k")[comp].mean()
    b = df[df["round"] == act[-1]].assign(k=lambda t: t.apply(_key, axis=1, cols=cols)).groupby("k")[comp].mean()
    common = a.index.intersection(b.index)
    return float((b[common] - a[common]).mean()) if len(common) else 0.0


def predict_component(comp, dec, r, df=None, prev=None, drift=None, team=None, niveau=None):
    """Impact attendu (%) de la composante `comp` au tour r pour une équipe aux décisions `dec`.
    prev : impact que l'équipe avait au dernier tour (repli) ; niveau : "max" ou "min" pour une composante dont
    la décision n'est pas publiée. Renvoie (impact, source)."""
    df = panel() if df is None else df
    drift = DRIFT if drift is None else drift
    hist = df[df["round"] < r]
    act = active(hist, comp)
    cols = COMPONENTS[comp]
    if not act:
        return 0.0, "inactive"
    s = act[-1]
    last = hist[hist["round"] == s]
    if niveau in ("max", "min"):
        return float(last[comp].max() if niveau == "max" else last[comp].min()), f"niveau {niveau}"
    if not cols or any(c not in dec or (isinstance(dec[c], float) and np.isnan(dec[c])) for c in cols):
        return float(prev or 0.0), "reconduit"
    ero = drift * _erosion(hist, comp, cols, s)
    key = _key(dec, cols)
    keys = last.apply(_key, axis=1, cols=cols)
    if (keys == key).any():
        return float(last.loc[keys == key, comp].mean() + ero), "table"
    if len(cols) > 1 and all((last[c].astype(str) == str(dec[c])).any() for c in cols):
        X = pd.get_dummies(last[cols].astype(str)).astype(float)
        b = np.linalg.lstsq(np.column_stack([X.values, np.ones(len(X))]), last[comp].values, rcond=None)[0]
        v = b[-1] + sum(b[list(X.columns).index(f"{c}_{dec[c]}")] for c in cols)
        return float(v + ero), "additif"
    for q in reversed(act[:-1]):                                   # option absente du dernier tour : tour antérieur
        t = hist[hist["round"] == q]
        k = t.apply(_key, axis=1, cols=cols)
        if (k == key).any():
            return float(t.loc[k == key, comp].mean() + ero), f"table du tour {q - 1}"
    return float(prev or 0.0), "reconduit"


def predict(dec, r, team=None, df=None, drift=None, impacts=None, niveaux=None):
    """État attendu au tour d'indice r pour des décisions `dec` (mêmes noms que model.esg.panel).

    team : équipe dont on reprend l'impact précédent quand une composante ne se prévoit pas ;
    impacts : {composante: %} imposés à la main. Renvoie dict(esg, detail, sources[, lqual])."""
    df = panel() if df is None else df
    prev_row = None
    if team is not None:
        t = df[(df["team"] == team) & (df["round"] < r)]
        prev_row = None if t.empty else t.sort_values("round").iloc[-1]
    detail, sources = {}, {}
    for comp in COMPONENTS:
        if impacts and comp in impacts:
            detail[comp], sources[comp] = float(impacts[comp]), "saisi"
            continue
        prev = float(prev_row[comp]) if prev_row is not None else 0.0
        detail[comp], sources[comp] = predict_component(comp, dec, r, df, prev, drift, team, (niveaux or {}).get(comp))
    out = dict(esg=float(sum(np.log1p(v / 100) for v in detail.values())), detail=detail, sources=sources)
    q = dec.get("f_qualite")
    if q is None or not np.isfinite(q):                           # qualité non donnée : celle du même jeu de fournisseurs au dernier tour
        last = df[df["round"] == df[df["round"] < r]["round"].max()]
        same = last[last["jeu_fournisseurs"] == dec.get("jeu_fournisseurs")]["f_qualite"].dropna()
        q = float(same.mean()) if len(same) else None
    if q is not None and np.isfinite(q) and q > 0:
        out["lqual"] = float(np.log(q / 3.0))
    return out


def from_platform(state):
    """Décisions au format de la plateforme ({identifiant du champ: valeur}) -> noms du panel ESG."""
    dec = {}
    for key, (col, mp) in esg.MENU_TO_REPORT.items():
        if key in state:
            dec[col] = mp.get(state[key], state[key])
    if "esg.recyclability" in state:
        dec["directive"] = esg.DIRECTIVE.get(state["esg.recyclability"], state["esg.recyclability"])
        dec["engagement"] = 1.0 if state.get("esg.recyclability.commit") else 0.0
    if all(k in state for k in esg.TRN):
        for k, c in zip(esg.TRN, esg.TRN_COLS):
            dec[c] = 1.0 if state[k] else 0.0
    if all(f"supplier.{i + 1}" in state for i in range(len(SUPPLIERS))):
        dec["jeu_fournisseurs"] = "+".join(sorted(n for i, n in enumerate(SUPPLIERS) if state[f"supplier.{i + 1}"]))
    if "f_qualite" in state:
        dec["f_qualite"] = float(state["f_qualite"])
    return dec


def our_state(inputs, r, team):
    """État à donner au simulateur pour le tour d'indice r, d'après le bloc `our_decisions` des entrées du tour :
    décisions au format du panel ESG ou de la plateforme, plus `impacts` (optionnel) pour les composantes saisies.
    Les décisions non renseignées sont reprises de notre dernier tour."""
    blk = dict(inputs.get("our_decisions") or {})
    impacts, niveaux = blk.pop("impacts", None), blk.pop("niveaux", None)
    df = panel()
    t = df[(df["team"] == team) & (df["round"] < r)].sort_values("round")
    dec = {} if t.empty else t.iloc[-1].to_dict()
    dec.pop("f_qualite", None)                                    # la qualité ne se reconduit pas ici : le cadre la porte déjà
    dec.update(from_platform(blk))
    dec.update({k: v for k, v in blk.items() if k in set(sum(COMPONENTS.values(), [])) | {"f_qualite"}})
    if isinstance(dec.get("jeu_fournisseurs"), (list, tuple)):
        dec["jeu_fournisseurs"] = "+".join(sorted(dec["jeu_fournisseurs"]))
    p = predict(dec, r, team, df, impacts=impacts, niveaux=niveaux)
    return {k: p[k] for k in ("esg", "lqual") if k in p}, p


def effet(avant, apres, r, team=None, s=1.3):
    """Effet sur la demande (%) de passer des décisions `avant` à `apres` au tour r ; s : poids de l'ESG dans le moteur."""
    a, b = predict(avant, r, team), predict(apres, r, team)
    d = b["esg"] - a["esg"]
    return dict(delta_esg=d, demande_pct=float((np.exp(s * d) - 1) * 100),
                detail={c: b["detail"][c] - a["detail"][c] for c in COMPONENTS if abs(b["detail"][c] - a["detail"][c]) > 1e-9})


# ------------------------------------------------------------------ rejeu aveugle
def backtest(drifts=(0.0, 0.5, 1.0), verbose=True):
    """Pour chaque tour où l'ESG agit déjà au tour précédent, et chaque équipe : impact prévu à partir des tours
    antérieurs et des décisions de l'équipe, comparé à l'impact publié. Référence : l'impact reconduit."""
    df = panel()
    rows = []
    for r in sorted(df["round"].unique()):
        for comp in COMPONENTS:
            if not [x for x in active(df, comp) if x < r] or r not in active(df, comp):
                continue
            for _, row in df[df["round"] == r].iterrows():
                p = df[(df["team"] == row["team"]) & (df["round"] < r)].sort_values("round")
                prev = float(p.iloc[-1][comp]) if len(p) else 0.0
                rec = dict(tour=r - 1, team=row["team"], comp=comp, reel=row[comp], reconduit=prev)
                for dr in drifts:
                    rec[f"prevu_{dr}"], src = predict_component(comp, row.to_dict(), r, df, prev, dr, row["team"])
                    rec["source"] = src
                rows.append(rec)
    T = pd.DataFrame(rows)
    cols = ["reconduit"] + [f"prevu_{d}" for d in drifts]
    by_comp = T.groupby("comp").apply(lambda t: pd.Series({c: (t[c] - t["reel"]).abs().mean() for c in cols} | {"n": len(t)}))
    tot = T.groupby(["tour", "team"]).apply(lambda t: pd.Series({c: np.log1p(t[c] / 100).sum() for c in ["reel"] + cols})).reset_index()
    by_round = tot.groupby("tour").apply(lambda t: pd.Series({c: (t[c] - t["reel"]).abs().mean() * 100 for c in cols}))
    if verbose:
        pd.set_option("display.width", 220)
        print("=== Erreur moyenne par composante (points de % d'impact), 12 équipes ===")
        print(by_comp.round(2).to_string())
        print("\n=== Erreur moyenne sur l'impact ESG total d'une équipe (points de log x 100), par tour ===")
        print(by_round.round(2).to_string())
        print("\nSources :", T.groupby("comp")["source"].agg(lambda x: dict(x.value_counts())).to_dict())
    return T, by_comp, by_round


if __name__ == "__main__":
    backtest()
