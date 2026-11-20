"""Effet des décisions ESG, RH et fournisseurs, appris sur ce que les 12 équipes ont joué.

Les rapports publient, pour chaque équipe et chaque tour, les décisions (salaire, formation, priorités, politiques,
recyclabilité, fournisseurs, certification) et l'impact en % de chaque composante ESG sur la demande.
On en tire, pour chaque option, l'impact moyen observé et le nombre d'observations.

  python3 -m model.esg          # tables d'effets
  from model.esg import effects, predict_delta

Une option que personne n'a jouée n'a pas d'estimation : `predict_delta` renvoie None pour elle.
"""
import numpy as np
import pandas as pd

from model.panel import available_rounds
from model.report import lines

IMPACTS = {  # composante publiée -> nom court
    "Environnement (E) > Impact environnemental des unités vendues": "env_unites",
    "Environnement (E) > Efficacité opérationnelle ?": "efficacite",
    "Environnement (E) > Utilisation d'énergie renouvelable": "renouvelable",
    "Environnement (E) > Recyclabilité des produits": "recyclabilite",
    "Environnement (E) > Améliorations des processus": "processus",
    "Social (S) > Rémunération des employés": "remuneration",
    "Social (S) > Rotation des employés": "rotation",
    "Social (S) > Image de l'entreprise pour les priorités de formation": "formation",
    "Gouvernance (G) > Politiques du travail": "politiques",
    "Gouvernance (G) > Politiques des fournisseurs": "fournisseurs",
}
DECISIONS = {
    "Rapport RH > Ressources humaines > Salaire mensuel, USD": "salaire",
    "Rapport RH > Ressources humaines > Budget Formation mensuel, USD": "budget_formation",
    "Rapport ESG > Recyclabilité des produits > Directive interne": "directive",
    "Rapport ESG > Recyclabilité des produits > Engagement": "engagement",
    "Rapport ESG > Politiques d'entreprise > Règlement du travail et respect des droits des employés": "pol_reglement",
    "Rapport ESG > Politiques d'entreprise > Relations avec les salariés et syndicats": "pol_relations",
    "Rapport ESG > Politiques d'entreprise > Quotas pour les postes de direction": "pol_quotas",
    "Rapport ESG > Politiques d'entreprise > Certitications de développement durable": "certification",
    "Rapport ESG > Priorités de formation > Formation de base": "trn_base",
    "Rapport ESG > Priorités de formation > Sécurité au travail": "trn_securite",
    "Rapport ESG > Priorités de formation > Santé et bien-être du personnel": "trn_sante",
    "Rapport ESG > Priorités de formation > Politiques de non-discrimination": "trn_discrimination",
    "Rapport ESG > Priorités de formation > Ethique et lutte contre la corruption": "trn_ethique",
    "Rapport du fournisseur de composants > Attributs des fournisseurs de composants > Qualité": "f_qualite",
    "Rapport du fournisseur de composants > Attributs des fournisseurs de composants > Développement durable": "f_durable",
    "Rapport ESG > Score final > Environnement (E)": "score_E",
    "Rapport ESG > Score final > Social (S)": "score_S",
    "Rapport ESG > Score final > Gouvernance (G)": "score_G",
    "Rapport ESG > Score final > Réputation ESG": "score",
}
CHECKS = ("engagement", "trn_base", "trn_securite", "trn_sante", "trn_discrimination", "trn_ethique")


def panel(rounds=None):
    """Une ligne par (tour, équipe) : décisions publiées et impacts en % sur la demande."""
    rows = []
    for r in rounds or [x for x in available_rounds() if x >= 2]:
        teams, L = lines(r)
        D = {" > ".join(p): v for p, v in L}
        for i, t in enumerate(teams):
            row = dict(round=r, team=t)
            for k, short in IMPACTS.items():
                v = D.get("Rapport ESG > " + k)
                row[short] = v[i] if v is not None and not isinstance(v[i], str) else 0.0
            for k, short in DECISIONS.items():
                v = D.get(k)
                x = v[i] if v is not None else np.nan
                row[short] = (1.0 if isinstance(x, str) and x.strip() else 0.0) if short in CHECKS else x
            rows.append(row)
    df = pd.DataFrame(rows)
    for c in IMPACTS.values():
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    return df


def _by_option(df, impact, col):
    g = df.groupby(col)[impact].agg(["mean", "std", "count"]).rename(columns={"mean": "impact_moyen_pct", "std": "ecart_type", "count": "n"})
    return g.sort_values("impact_moyen_pct", ascending=False)


def _additive(df, impact, cols):
    """Effet propre de chaque option quand l'impact publié est la somme de plusieurs décisions (moindres carrés)."""
    X = pd.get_dummies(df[cols].astype(str), drop_first=False).astype(float)
    A = np.column_stack([X.values, np.ones(len(X))])
    b = np.linalg.lstsq(A, df[impact].values, rcond=None)[0]
    out = pd.DataFrame(dict(effet_pct=b[:-1], n=X.sum(0).values), index=X.columns)
    for c in cols:                                   # centré : effet par rapport à l'option la plus fréquente de chaque décision
        m = out.index.str.startswith(c + "_")
        ref = out[m]["n"].idxmax()
        out.loc[m, "effet_pct"] -= out.loc[ref, "effet_pct"]
    e = df[impact].values - A @ b
    return out, float(1 - e.var() / max(df[impact].var(), 1e-12))


def effects(df=None):
    """Tables d'effets par groupe de leviers. Seuls les tours où l'ESG agit sont utilisés."""
    df = panel() if df is None else df
    df = df[df[list(IMPACTS.values())].abs().sum(1) > 0]
    out = {}
    out["politiques"], out["r2_politiques"] = _additive(df, "politiques", ["pol_reglement", "pol_relations", "pol_quotas"])
    out["recyclabilite"] = _by_option(df.assign(opt=df["directive"].astype(str) + np.where(df["engagement"] > 0, " + engagement", "")), "recyclabilite", "opt")
    tr = ["trn_base", "trn_securite", "trn_sante", "trn_discrimination", "trn_ethique"]
    A = np.column_stack([df[tr].values, np.log(df["budget_formation"].clip(lower=1)), np.ones(len(df))])
    b = np.linalg.lstsq(A, df["formation"].values, rcond=None)[0]
    out["formation"] = pd.Series(b, index=tr + ["log_budget_formation", "constante"])
    out["r2_formation"] = float(1 - (df["formation"].values - A @ b).var() / max(df["formation"].var(), 1e-12))
    rel = np.log(df["salaire"] / df.groupby("round")["salaire"].transform("mean"))
    A = np.column_stack([rel, np.ones(len(df))])
    b = np.linalg.lstsq(A, df["remuneration"].values, rcond=None)[0]
    out["remuneration"] = dict(pct_par_10pct_de_salaire_relatif=float(b[0] * np.log(1.1)), constante=float(b[1]),
                               r2=float(1 - (df["remuneration"].values - A @ b).var() / max(df["remuneration"].var(), 1e-12)))
    A = np.column_stack([pd.to_numeric(df["f_durable"], errors="coerce").fillna(3.0), np.ones(len(df))])
    b = np.linalg.lstsq(A, df["fournisseurs"].values, rcond=None)[0]
    out["fournisseurs"] = dict(pct_par_point_de_note=float(b[0]), r2=float(1 - (df["fournisseurs"].values - A @ b).var() / max(df["fournisseurs"].var(), 1e-12)))
    out["plages"] = df[list(IMPACTS.values())].agg(["min", "median", "max"]).T
    out["n"] = len(df)
    return out


# libellé d'un menu de la plateforme -> libellé du rapport ESG (ils diffèrent)
MENU_TO_REPORT = {
    "esg2.labor.regulations": ("pol_reglement", {"Conformité minimale": "Conformité minimale", "Conformité standard": "Conformité standard",
                                                 "Initiatives d'engagement communautaire": "Initiatives d'engagement communautaire",
                                                 "Partenariat stratégique": "Partenariat stratégique"}),
    "esg2.employee.relations": ("pol_relations", {"Efficacité accrue en R&D": "Efficacité accrue en R&D", "Approche équilibrée": "Option intermédiaire",
                                                  "Accent sur le bien-être des employés": "Concentration sur le bien-être des employés",
                                                  "Collaboration syndicale": "Collaboration avec les syndicats"}),
    "esg2.management.quotas": ("pol_quotas", {"Recrutement aveugle, suppression des quotas": "Recrutement aveugle", "Priorisez modérément le recrutement diversifié": "Priorité modérée au recrutement diversifié",
                                              "Prime de départ": "Prime de départ", "Programmes de mentorat": "Programmes de mentorat"}),
}
DIRECTIVE = {"Recyclage des matériaux de base": "Recyclage basique des matériaux", "Conception pour le démontage facile": "Conception pour le démontage facile",
             "Utilisation de matériaux recyclés": "Utilisation de matériaux recyclés", "Évaluation du cycle de vie": "Évaluation du cycle de vie",
             "Systèmes de cycle fermé": "Systèmes à circuit fermé"}
TRN = ["esg.trn.basic", "esg.trn.work.safety", "esg.trn.personal.health", "esg.trn.non.discrimination", "esg.trn.ethics"]
TRN_COLS = ["trn_base", "trn_securite", "trn_sante", "trn_discrimination", "trn_ethique"]


class Impact:
    """Impact attendu (points de % de demande) d'un état de décisions ESG, d'après les 12 équipes.
    `points(state)` renvoie (total, détail, inconnus) ; state = {clé de la plateforme: valeur}."""

    def __init__(self, last_only=True):
        df = panel()
        df = df[df[list(IMPACTS.values())].abs().sum(1) > 0]
        self.df = df
        self.recent = df[df["round"] == df["round"].max()] if last_only else df
        self.eff = effects(df)
        r = self.recent.assign(combo=self.recent[TRN_COLS].astype(int).astype(str).agg("".join, axis=1))
        self.trn_combo = r.groupby("combo")["formation"].agg(["mean", "count"])
        d = df.assign(opt=df["directive"].astype(str) + np.where(df["engagement"] > 0, "+E", ""))
        self.recy = d[d["round"] == d["round"].max()].groupby("opt")["recyclabilite"].agg(["mean", "count"])
        self.recy_all = d.groupby("opt")["recyclabilite"].agg(["mean", "count"])

    def points(self, state):
        det, unknown = {}, []
        pol = self.eff["politiques"]
        for key, (col, mp) in MENU_TO_REPORT.items():
            if key in state:
                idx = f"{col}_{mp.get(state[key], state[key])}"
                if idx in pol.index and pol.loc[idx, "n"] >= 1:
                    det[key] = float(pol.loc[idx, "effet_pct"])
                else:
                    unknown.append(f"{key}={state[key]}")
        if all(k in state for k in TRN):
            combo = "".join(str(int(bool(state[k]))) for k in TRN)
            if combo in self.trn_combo.index:
                det["formation"] = float(self.trn_combo.loc[combo, "mean"])
            else:
                f = self.eff["formation"]
                det["formation"] = float(sum(f[c] * int(bool(state[k])) for k, c in zip(TRN, TRN_COLS)) + f["constante"] + f["log_budget_formation"] * np.log(1200))
                unknown.append(f"priorités {combo} jamais observées (extrapolé)")
        if "esg.recyclability" in state:
            opt = DIRECTIVE.get(state["esg.recyclability"], state["esg.recyclability"]) + ("+E" if state.get("esg.recyclability.commit") else "")
            t = self.recy if opt in self.recy.index else self.recy_all
            if opt in t.index:
                det["recyclabilite"] = float(t.loc[opt, "mean"])
            else:
                unknown.append(f"recyclabilité {opt}")
        return sum(det.values()), det, unknown


def predict_delta(group, option_from, option_to, eff=None):
    """Variation d'impact sur la demande (points de %) en changeant d'option ; None si l'une n'a jamais été observée."""
    eff = eff or effects()
    t = eff[group]
    key = "effet_pct" if "effet_pct" in t else "impact_moyen_pct"
    if option_from not in t.index or option_to not in t.index or t.loc[option_to, "n"] < 1:
        return None
    return float(t.loc[option_to, key] - t.loc[option_from, key])


if __name__ == "__main__":
    pd.set_option("display.width", 220)
    e = effects()
    us = panel().query("team == 'tomobil'").iloc[-1]
    print(f"{e['n']} observations (équipe x tour)\n")
    print(f"Politiques de travail : effet propre de chaque option, en points de % de demande (R2 {e['r2_politiques']:.2f})")
    print(e["politiques"].round(2).to_string())
    print("\nRecyclabilité : impact moyen par directive"); print(e["recyclabilite"].round(2).to_string())
    print(f"\nPriorités de formation : points de % par priorité cochée (R2 {e['r2_formation']:.2f})"); print(e["formation"].round(2).to_string())
    print("\nRémunération :", {k: round(v, 2) for k, v in e["remuneration"].items()})
    print("Fournisseurs :", {k: round(v, 2) for k, v in e["fournisseurs"].items()})
    print("\nPlage de chaque impact sur les 12 équipes (%), et nous au dernier tour :")
    print(e["plages"].assign(nous=us[list(IMPACTS.values())].astype(float)).round(2).to_string())
