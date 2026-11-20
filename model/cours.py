"""Cours de l'action et retour cumulé : ce qui fait le classement.

  python3 -m model.cours      # régressions, rejeu en marche avant, effet d'un dividende

Le classement se fait sur le retour cumulé aux actionnaires :
    ((cours + dividendes par action capitalisés à 9 % par tour) / 48,6)^(1/tours) - 1.
Deux régressions sur les 12 équipes :
  niveau    : cours = a + b x fonds propres par action + c x bénéfice par action + d x dividendes cumulés par action
  variation : cours(t) - cours(t-1) = a + b x bénéfice par action du tour + c x dividende par action du tour
Le coefficient c de la seconde dit ce qu'un dollar de dividende retire au cours. Tant qu'il est au-delà de -1,
un dividende détruit du retour cumulé.
"""
import numpy as np
import pandas as pd

from model.report import table

P0 = 48.6          # cours initial
RATE = 0.09        # taux auquel le retour cumulé capitalise les dividendes passés (coût du capital des conditions de marché)
R = "Ratios et indicateurs financiers > Ratios"
FIN = "Flux de trésorerie de la société mère, M USD > Flux de trésorerie généré par les opérations de financement"


def panel():
    """Une ligne par (tour, équipe) : cours, fonds propres et bénéfice par action, dividende du tour et cumulé."""
    P = table(f"{R} > Cours de l'action à la fin du tour, USD")
    E = table("Bilan, M USD, Global > Capitaux propres > Total des capitaux propres")
    N = table(f"{R} > Actions sur le marché à la fin du tour, millions d'actions")
    EPS = table(f"{R}, % > Bénéfice par action (EPS), USD")
    RET = table(f"{R} > Retour cumulé aux actionnaires (moyenne annuelle), %")
    DIV = (-table(f"{FIN} > Dividendes")).reindex(P.index).fillna(0.0)
    ISS = table(f"{FIN} > Flux de trésorerie généré par émission (+) ou rachat (-) d'actions").reindex(P.index).fillna(0.0)
    rows = []
    for t in P.columns:
        cum = 0.0
        for r in [x for x in P.index if x >= 2]:
            dps = DIV.loc[r, t] / N.loc[r, t]
            cum = cum * (1 + RATE) + dps
            prev = r - 1 if r > 2 else 0                     # le tour 1 repart de la situation initiale
            rows.append(dict(tour=r - 1, team=t, cours=P.loc[r, t], cours_prec=P.loc[prev, t], fp=E.loc[r, t] / N.loc[r, t], bpa=EPS.loc[r, t],
                             div=dps, cumdiv=cum, emission=ISS.loc[r, t], retour=RET.loc[r, t],
                             retour_calcule=(((P.loc[r, t] + cum) / P0) ** (1 / (r - 1)) - 1) * 100))
    T = pd.DataFrame(rows)
    T["d_cours"] = T["cours"] - T["cours_prec"]
    return T


def ols(T, y, cols):
    T = T.dropna(subset=cols + [y])
    X = np.column_stack([np.ones(len(T))] + [T[c].values.astype(float) for c in cols])
    yy = T[y].values.astype(float)
    b = np.linalg.pinv(X) @ yy
    e = yy - X @ b
    se = np.sqrt(np.diag(np.linalg.pinv(X.T @ X)) * (e @ e) / max(len(yy) - len(b), 1))
    return dict(coef=dict(zip(["cst"] + cols, b)), se=dict(zip(["cst"] + cols, se)), r2=1 - e.var() / yy.var(), rmse=float(np.sqrt((e ** 2).mean())), n=len(yy))


def predict(fit, row):
    return fit["coef"]["cst"] + sum(v * row[k] for k, v in fit["coef"].items() if k != "cst")


LEVEL = ["fp", "bpa", "cumdiv"]
DELTA = ["bpa", "div"]


def walk_forward(T, y, cols, first=4):
    """Régression ajustée sur les tours antérieurs, erreur sur le tour suivant."""
    rows = []
    for t in sorted(T["tour"].unique()):
        if t < first:
            continue
        f = ols(T[T["tour"] < t], y, cols)
        test = T[T["tour"] == t].dropna(subset=cols + [y])
        e = test[y].values - np.array([predict(f, r) for _, r in test.iterrows()])
        rows.append(dict(tour=t, rmse=float(np.sqrt((e ** 2).mean())), biais=float(e.mean())))
    return pd.DataFrame(rows)


def show(name, f):
    print(f"{name:42s} n={f['n']:3d} R2={f['r2']:.3f} rmse={f['rmse']:5.1f}  " + "  ".join(f"{k}={v:.2f}(±{f['se'][k]:.2f})" for k, v in f["coef"].items()))


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    T = panel()
    clean = T[T["emission"] == 0]                        # une émission d'actions change le nombre d'actions : hors régression
    print(f"Retour cumulé recalculé (dividendes capitalisés à {RATE:.0%}) : écart maximal avec le publié {np.abs(T.retour - T.retour_calcule).max():.2f} point")
    print(f"Observations avec dividende : {(T['div'] > 0).sum()} sur {len(T)}\n")
    show("niveau : FP + BPA", ols(clean, "cours", ["fp", "bpa"]))
    show("niveau : FP + BPA + dividendes cumulés", ols(clean, "cours", LEVEL))
    show("variation : BPA", ols(clean, "d_cours", ["bpa"]))
    fd = ols(clean, "d_cours", DELTA)
    show("variation : BPA + dividende du tour", fd)
    show("variation, tours 5 et suivants", ols(clean[clean.tour >= 5], "d_cours", DELTA))
    c, s = fd["coef"]["div"], fd["se"]["div"]
    print(f"\nUn dollar de dividende par action retire {-c:.2f} USD (±{s:.2f}) au cours et rapporte 1 USD à l'actionnaire : "
          f"effet net sur le retour cumulé {1 + c:+.2f} USD par dollar versé.")
    print("\nRejeu en marche avant (régression calée sur les tours antérieurs), erreur sur le cours en USD :")
    print("niveau :\n" + walk_forward(clean, "cours", LEVEL).round(1).to_string(index=False))
    print("variation (cours précédent + variation prévue) :\n" + walk_forward(clean, "d_cours", DELTA).round(1).to_string(index=False))
