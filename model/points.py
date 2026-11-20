"""Barème de l'instructeur : la fonction objectif de l'optimiseur.

  python3 -m model.points            # rejeu (points recalculés contre points publiés), prévision aveugle, tableau du dernier tour
  python3 -m model.points 7          # tableau « où sont les points » pour la période 7 (rapports du tour 7)

À chaque tour les 12 équipes sont rangées sur chaque critère ; une équipe reçoit 1 + le nombre d'équipes strictement
moins bonnes qu'elle (certification : 0 / 2 / 4 / 6 points). Ce module
  - recalcule chaque critère à partir des rapports de la plateforme (`valeurs`), formules calées sur les tours 4 à 6 ;
  - applique la règle des points (`points`) et la rejoue contre le classement publié (`rejeu`) ;
  - dit où sont les points à prendre (`tableau`) ;
  - tire les valeurs des concurrents pour le tour à venir (`concurrents`) et rend l'espérance de nos points (`esperance`).
Un critère du classement publié qui n'a pas de formule ici fait échouer `controle()` : c'est une nouveauté à traiter.
"""
import sys

import numpy as np
import pandas as pd

from model import classement
from model.report import lines

US = "tomobil"
ZONES = {"US": "USA", "ASIE": "Chine", "EUROPE": "Europe"}
TECHS = ("Thermique", "Hybride", "Électrique", "Hydrogène")
CERT_POINTS = {"Pas de": 0, "Bronze": 2, "Argent": 4, "Or": 6}
# nom canonique -> (sens, début de l'intitulé dans le PDF)
CRITERES = {
    "ROE": (1, "RENTABILITÉ FINANCIÈRE"), "création de valeur": (1, "CRÉATION DE VALEUR"), "rentabilité de l'action": (1, "RENTABILITÉ DE L'ACTION"),
    "indépendance financière": (1, "INDÉPENDANCE FINANCIÈRE"), "découvert": (-1, "DÉCOUVERT"),
    "marge USA": (1, "MARGE OPÉRATIONNELLE US"), "marge Chine": (1, "MARGE OPÉRATIONNELLE ASIE"), "marge Europe": (1, "MARGE OPÉRATIONNELLE EUROPE"),
    "part USA": (1, "PART DE MARCHÉ US"), "part Chine": (1, "PART DE MARCHÉ ASIE"), "part Europe": (1, "PART DE MARCHÉ EUROPE"),
    "demande insatisfaite": (-1, "DEMANDE INSATISFAITE"), "stocks": (-1, "STOCKS EN VOLUME"),
    "coût unitaire USA": (-1, "COÛT MOYEN UNITAIRE PONDÉRÉ (véhicules vendus US"), "coût unitaire Chine": (-1, "COÛT MOYEN UNITAIRE PONDÉRÉ (véhicules vendus Asie"),
    "coût unitaire Europe": (-1, "COÛT MOYEN UNITAIRE PONDÉRÉ (véhicules vendus Europe"),
    "productivité": (1, "COÉFFICIENT DE PRODUCTIVITÉ"), "fournisseurs": (1, "SCORE DDRS"),
    "E": (1, "IMPACT ENVIRONNEMENTAL"), "S": (1, "IMPACT SOCIÉTAL"), "G": (1, "IMPACT GOUVERNANCE"), "certification": (1, "CERTIFICATION"),
}
ALIAS = {"COÛT MOYEN UNITAIRE PONDÉRÉ (véhicules vendus #1": "coût unitaire USA", "COÛT MOYEN UNITAIRE PONDÉRÉ (véhicules vendus #2": "coût unitaire Chine",
         "COÛT MOYEN UNITAIRE PONDÉRÉ (véhicules vendus #3": "coût unitaire Europe"}
SENS = {k: v[0] for k, v in CRITERES.items()}
_L = {}


def canon(label):
    """Intitulé du PDF -> nom canonique (None si inconnu)."""
    if label in ALIAS:
        return ALIAS[label]
    return next((k for k, (_, pre) in CRITERES.items() if label.startswith(pre)), None)


def _lines(idx):
    if idx not in _L:
        teams, L = lines(idx)
        _L[idx] = (teams, {" > ".join(p): v for p, v in L})
    return _L[idx]


def valeurs(idx):
    """Tableau critère x équipe recalculé depuis les rapports du tour d'indice idx (période idx - 1)."""
    teams, D = _lines(idx)
    S = lambda k: pd.to_numeric(pd.Series(D.get(k, [np.nan] * len(teams)), index=teams), errors="coerce")
    tot = lambda ok: sum(S(k).fillna(0) for k in D if ok(k))
    V = {}
    V["ROE"] = S("Ratios et indicateurs financiers > Ratios, % > Rentabilité des fonds propres (ROE)")
    V["création de valeur"] = S("Création de valeur, M USD > Fournisseurs > Création de valeur totale")
    B = "Bilan, M USD, Global > "
    fp, lt, ct = S(B + "Capitaux propres > Total des capitaux propres"), S(B + "Dettes > Dettes à long terme").fillna(0), S(B + "Dettes > Dettes à court terme (imprévues)").fillna(0)
    V["indépendance financière"] = fp / (fp + lt + ct) * 100          # fonds propres / (fonds propres + dettes financières) : écart nul aux tours 2 à 6
    V["découvert"] = ct
    for z, ca in (("USA", "Chiffre d'affaires total"), ("Chine", "Chiffre d'affaires total"), ("Europe", "Chiffre d'affaires")):
        V[f"marge {z}"] = S(f"Compte de résultat, M USD, {z} > Coûts > RÉSULTAT OPÉRATIONNEL (EBIT)") / S(f"Compte de résultat, M USD, {z} > Chiffre d'affaires > {ca}") * 100
        V[f"part {z}"] = S(f"Résultats par zone, {z} > {z} parts de marché, % > Total")
        V[f"coût unitaire {z}"] = S(next(k for k in D if k.endswith(f"Coût unitaire par produit vendu, USD > {z} > Moyenne pondérée")))
    V["demande insatisfaite"] = tot(lambda k: k.startswith("Détails sur la logistique") and k.endswith("Demande insatisfaite"))
    V["stocks"] = tot(lambda k: "Stocks, k unités" in k and k.split(" > ")[-1] in TECHS)
    V["productivité"] = S("Rapport RH > Ressources humaines > Coefficient de productivité")
    A = "Rapport du fournisseur de composants > Attributs des fournisseurs de composants > "
    V["fournisseurs"] = S(A + "Qualité") + S(A + "Développement durable")
    for k, n in (("E", "Environnement (E)"), ("S", "Social (S)"), ("G", "Gouvernance (G)")):
        V[k] = S(f"Rapport ESG > Score final > {n}")
    cert = pd.Series(D.get("Rapport ESG > Politiques d'entreprise > Certitications de développement durable", ["Pas de"] * len(teams)), index=teams).astype(str)
    V["certification"] = cert.map(lambda t: next((p for k, p in CERT_POINTS.items() if t.strip().startswith(k)), 0)).astype(float)
    # rentabilité de l'action = (cours + dividende par action du tour) / cours précédent - 1 (écart nul aux tours 5 et 6,
    # sauf l'équipe qui a émis des actions)
    if idx >= 2:
        R = "Ratios et indicateurs financiers > Ratios > "
        prev = _lines(idx - 1 if idx > 2 else 0)[1]
        cours, n = S(R + "Cours de l'action à la fin du tour, USD"), S(R + "Actions sur le marché à la fin du tour, millions d'actions")
        div = -S("Flux de trésorerie de la société mère, M USD > Flux de trésorerie généré par les opérations de financement > Dividendes").fillna(0)
        p0 = pd.to_numeric(pd.Series(prev[R + "Cours de l'action à la fin du tour, USD"], index=teams), errors="coerce")
        V["rentabilité de l'action"] = ((cours + div / n) / p0 - 1) * 100
    return pd.DataFrame(V).T.reindex(list(CRITERES))


def points(V):
    """Points par critère (lignes) et par équipe (colonnes) : 1 + nombre d'équipes strictement moins bonnes."""
    P = {}
    for c, row in V.iterrows():
        if c == "certification":
            P[c] = row
            continue
        v = row.values.astype(float) * SENS[c]
        P[c] = pd.Series([1.0 + np.sum(v < x - 1e-9) for x in v], index=V.columns) if not np.isnan(v).all() else row * np.nan
    return pd.DataFrame(P).T


def publie(periode=None):
    """Classement publié : (valeurs, points) en noms canoniques, pour une période (ou dict de toutes)."""
    df = classement.load()
    df = df[df["points"].notna()].assign(c=lambda t: t["critere"].map(canon))
    out = {}
    for p, t in df.groupby("periode"):
        out[int(p)] = (t.pivot_table(index="c", columns="equipe", values="valeur", aggfunc="first"), t.pivot_table(index="c", columns="equipe", values="points", aggfunc="first"))
    return out if periode is None else out[periode]


def controle():
    """Critères publiés sans formule : nouveauté du barème à traiter avant d'optimiser."""
    df = classement.load()
    df = df[df["points"].notna()]
    last = df[df["periode"] == df["periode"].max()]
    return sorted({c for c in last["critere"].unique() if canon(c) is None})


def rejeu(periodes=(4, 5, 6), verbose=True):
    """Points recalculés depuis les rapports contre points publiés. Renvoie l'écart absolu total par période."""
    rows = []
    for per in periodes:
        _, PP = publie(per)
        P = points(valeurs(per + 1)).reindex(PP.index)[PP.columns]
        d = (P - PP).abs()
        rows.append(dict(periode=per, criteres=len(PP), attributions=int(PP.notna().sum().sum()), ecarts=int((d > 0.5).sum().sum()),
                         total_nous_recalcule=float(P[US].sum()), total_nous_publie=float(PP[US].sum()),
                         ecart_total_max=float((P.sum() - PP.sum()).abs().max()), detail={c: int(n) for c, n in (d > 0.5).sum(1).items() if n}))
    T = pd.DataFrame(rows)
    if verbose:
        print("=== Rejeu du barème : points recalculés depuis les rapports contre points publiés ===")
        print(T.drop(columns="detail").to_string(index=False))
        for _, r in T.iterrows():
            if r["detail"]:
                print(f"  période {r['periode']} : écarts par critère {r['detail']}")
    return T


def tableau(idx, team=US):
    """Où sont les points : notre valeur, nos points, écart à l'équipe juste devant et juste derrière, points gagnables."""
    V = valeurs(idx)
    P = points(V)
    rows = []
    for c in V.index:
        if V.loc[c].isna().all():
            continue
        v, s = V.loc[c], SENS[c]
        better = v[(v - v[team]) * s > 1e-9]
        worse = v[(v - v[team]) * s < -1e-9]
        rows.append(dict(critere=c, valeur=v[team], points=P.loc[c, team], gagnables=6 - P.loc[c, team] if c == "certification" else len(better),
                         devant=(better * s).min() * s if len(better) else np.nan, qui_devant=(better * s).idxmin() if len(better) else "",
                         derriere=(worse * s).max() * s if len(worse) else np.nan, qui_derriere=(worse * s).idxmax() if len(worse) else "", ex_aequo=int((v == v[team]).sum() - 1)))
    return pd.DataFrame(rows).set_index("critere").sort_values("points")


# ------------------------------------------------------------------ prévision : concurrents du tour à venir
def historique():
    """Valeurs recalculées de tous les tours disponibles : dict période -> tableau critère x équipe."""
    from model.panel import available_rounds
    return {i - 1: valeurs(i) for i in available_rounds() if i >= 2}


def dispersion(H=None, avant=None):
    """Écart-type robuste de la variation d'un tour à l'autre de chaque critère (toutes équipes), et dérive médiane."""
    H = H or historique()
    per = sorted(p for p in H if avant is None or p < avant)
    out = {}
    for c in CRITERES:
        d = np.concatenate([(H[b].loc[c] - H[a].loc[c]).dropna().values.astype(float) for a, b in zip(per[-4:-1], per[-3:])] or [np.zeros(1)])
        d = d[np.isfinite(d)]
        if len(d) < 6:
            out[c] = (0.0, 0.0)
            continue
        q = np.quantile(d, [.25, .5, .75])
        out[c] = (float(q[1]), float((q[2] - q[0]) / 1.349))
    return out


def concurrents(V_last, disp, n=200, rng=None, derive=0.0):
    """Tire n scénarios de valeurs des 12 équipes pour le tour à venir : dernier tour + derive x dérive médiane + bruit.
    Renvoie un tableau (n, critères, équipes), dans l'ordre de V_last. Les critères entiers bornés à zéro (découvert,
    stocks, demande insatisfaite) restent positifs ; l'indépendance financière plafonne à 100."""
    rng = rng or np.random.default_rng(0)
    X = np.empty((n,) + V_last.shape)
    for i, c in enumerate(V_last.index):
        m, sd = disp.get(c, (0.0, 0.0))
        x = V_last.loc[c].values.astype(float)[None, :] + derive * m + rng.normal(0, sd, (n, V_last.shape[1]))
        if c in ("découvert", "stocks", "demande insatisfaite"):
            x = np.where(V_last.loc[c].values[None, :] <= 0, np.where(rng.random(x.shape) < 0.75, 0.0, np.abs(x)), np.maximum(x, 0.0))
        if c == "indépendance financière":
            x = np.minimum(x, 100.0)
        if c == "certification":
            x = np.repeat(V_last.loc[c].values.astype(float)[None, :], n, 0)
        X[:, i, :] = x
    return X


def points_scen(X, criteres, j):
    """Points de l'équipe de colonne j dans chaque scénario : tableau (n, critères)."""
    out = np.empty(X.shape[:2])
    for i, c in enumerate(criteres):
        if c == "certification":
            out[:, i] = X[:, i, j]
        else:
            v = X[:, i, :] * SENS[c]
            out[:, i] = 1.0 + (v < v[:, [j]] - 1e-9).sum(1)
    return np.nan_to_num(out)


def esperance(nous, X, criteres, teams, team=US):
    """Espérance de nos points par critère. nous : dict critère -> valeur (scalaire ou tableau de taille n) qui
    remplace notre valeur tirée ; les critères absents gardent la valeur tirée (dernier tour + bruit)."""
    j = list(teams).index(team)
    X = X.copy()
    for c, v in nous.items():
        if c in criteres:
            X[:, list(criteres).index(c), j] = v
    return pd.Series(points_scen(X, criteres, j).mean(0), index=list(criteres))


def rejeu_prevision(periodes=(5, 6), n=300, verbose=True):
    """Prévision aveugle des points : les 12 équipes reprises du tour précédent (+ bruit), comparées aux points réels.
    Deux lectures : toutes les valeurs reconduites (borne basse de ce que l'on sait avant un tour), et nos valeurs
    réelles face à des concurrents reconduits (ce que mesure l'objectif quand nos critères sont bien prévus)."""
    H = historique()
    rows = []
    for per in periodes:
        if per not in H or per - 1 not in H:
            continue
        disp = dispersion(H, avant=per)
        V0, V1 = H[per - 1], H[per]
        crit = [c for c in V1.index if not V1.loc[c].isna().all() and not V0.loc[c].isna().all()]
        X = concurrents(V0.loc[crit], disp, n, np.random.default_rng(per))
        real = points(V1.loc[crit])
        for t in V1.columns:
            j = list(V1.columns).index(t)
            e0 = points_scen(X, crit, j).mean(0)
            e1 = esperance({c: V1.loc[c, t] for c in crit}, X, crit, V1.columns, t).values
            rows.append(dict(periode=per, team=t, reel=real[t].sum(), reconduit=e0.sum(), nos_valeurs_reelles=e1.sum(),
                             err_crit_reconduit=np.abs(e0 - real[t].values).mean(), err_crit_reelles=np.abs(e1 - real[t].values).mean()))
    T = pd.DataFrame(rows)
    if verbose and len(T):
        print("\n=== Prévision aveugle des points (concurrents repris du tour précédent) ===")
        g = T.assign(e0=(T.reconduit - T.reel).abs(), e1=(T.nos_valeurs_reelles - T.reel).abs()).groupby("periode").agg(
            erreur_total_tout_reconduit=("e0", "mean"), erreur_total_nos_valeurs_reelles=("e1", "mean"),
            erreur_par_critere_reconduit=("err_crit_reconduit", "mean"), erreur_par_critere_nos_valeurs_reelles=("err_crit_reelles", "mean"))
        print(g.round(2).to_string())
        print(T[T.team == US].round(1).to_string(index=False))
    return T


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    from model.panel import available_rounds
    miss = controle()
    if miss:
        print("CRITÈRES PUBLIÉS SANS FORMULE (nouveauté du barème à traiter) :", miss)
    have = publie()
    rejeu([p for p in (4, 5, 6, 7, 8, 9, 10) if p in have and p + 1 in available_rounds()])
    rejeu_prevision([p for p in (5, 6, 7, 8, 9) if p + 1 in available_rounds()])
    idx = int(sys.argv[1]) + 1 if len(sys.argv) > 1 else available_rounds()[-1]
    print(f"\n=== Où sont les points : période {idx - 1} ===")
    print(tableau(idx).round(3).to_string())
    sys.exit(1 if miss else 0)
