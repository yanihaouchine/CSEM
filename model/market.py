"""Taille des marchés du tour suivant : total par zone, puis partage entre technologies.

Total par zone : croissance annoncée, corrigée du prix moyen et de la publicité totale (peu de points -> incertitude
tirée dans les scénarios).

Partage entre technologies : moyenne de deux méthodes (« mixte », retenue après rejeu aveugle, voir `backtest`),
parce qu'aucune ne domine : l'extrapolation surestime une progression qui ralentit, la couverture ne voit pas
les hausses d'attrait décidées par le scénario du jeu (annoncées seulement dans le texte des conditions de marché).
Méthode « couverture » :
la page Demande publie la couverture du réseau de chaque technologie, par zone, pour tous les tours — futurs compris
(`python3 -m cesim.inputs N` l'enregistre dans data/couverture_tour_N.json). Un client ne peut acheter qu'une
technologie couverte chez lui ; s'il a le choix, il se répartit selon l'attrait W de chaque technologie.
W se déduit des parts du tour précédent, puis suit le nombre de produits offerts et leurs équipements relatifs.
Méthode « logit » : prolonger, amortie, la progression de la part de chaque techno.
"""
import itertools
import json

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

from cesim.client import ROOT

EL_PRICE = (-0.5, 0.25)   # élasticité du marché total au prix moyen (moyenne, écart-type)
EL_ADV = (0.05, 0.03)     # élasticité à la publicité totale
ANALOG = True             # cellule nouvelle dans une zone : pénétration des autres zones (analog_cells) plutôt que NEW_APPEAL
SD_YOUNG = 0.6            # écart-type (log) ajouté dans les scénarios à la taille d'une cellule « jeune » (voir young_cells)
SD_TOTAL = 0.07           # écart-type (log) du total par zone : erreur aveugle de 2 à 4 % aux tours 2 à 4, 10 % au tour 5
PREV = {1: 0, 2: 0}
GAMMA_N, GAMMA_F = 1.0, 0.6      # attrait d'une techno ~ (nombre de produits)^1.0 x (équipements relatifs au Thermique)^0.6
COVERAGE_MODEL = "sous-ensembles"   # partage par couverture : "sous-ensembles" (tech_shares_coverage) ou "offre" (tech_shares_offer, essai écarté)
THETA_COV = 0.0                  # exposant de la couverture dans le modèle « offre »
W_DIRECT = 0.5                   # méthode « mixte » : poids de la prévision directe par technologie (direct_cells)
GAMMA_N_DIRECT = 0.5             # prévision directe : exposant du nombre de produits offerts
REPORT = 0.0                     # prévision directe : part de la demande perdue par une technologie dont la couverture baisse
                                 # qui se reporte sur les autres cellules de la zone (0 = aucun report). Voir direct_cells.
                                 # Essai non retenu : à 0,5 la directe passe de 39,5 à 23,7 % au tour 7 mais de 17,4 à 23,2 % au tour 6.
LIVE_LOGIT = False               # « logit » entre technologies encore couvertes seulement : essai INFIRMÉ au tour 7 (logit 62 % d'erreur contre 47 %)
MIX_LOGIT = 0.5                  # méthode « mixte » : poids de l'extrapolation logit, le reste au modèle de couverture
# attrait par produit d'une techno nouvelle dans la zone (Thermique = 1/12). Hydrogène : au tour 5 les deux premiers
# vendeurs (USA, Europe) ont reçu 1 k unité de demande chacun pour 25 % de couverture, soit un attrait de 0,0003 ;
# 0,035 prévoyait 130 à 190 k. À relever si les conditions de marché annoncent le décollage de l'Hydrogène.
NEW_APPEAL = {"Hybride": 0.02, "Électrique": 0.035, "Hydrogène": 0.0005}
REF = "Thermique"


_CACHE = {}


def _panel():
    """Panel des produits vendus ; relu seulement quand data/panel.csv change (la prévision l'appelle des centaines de fois)."""
    f = ROOT / "data" / "panel.csv"
    key = f.stat().st_mtime_ns
    if _CACHE.get("key") != key:
        raw = pd.read_csv(f)
        _CACHE.update(key=key, panel=raw[raw["demand"].notna() & (raw["demand"] > 0)])
    return _CACHE["panel"]


def young_cells(cells, hist, last):
    """Cellules « jeunes » : vendues depuis moins de 3 tours, ou par moins de 8 équipes au tour précédent.
    Rejeu aveugle de la prévision directe, tours 2 à 6 : erreur de 0,18 en log sur les 23 cellules installées,
    mais −0,01 / +0,29 / −0,59 / −1,28 / +0,61 sur l'Électrique et ×300 à ×600 sur l'Hydrogène (prix divisé par trois)."""
    off, out = offer_history(), set()
    for c in cells:
        reg, tech = c.split("|")
        age = sum(1 for k in range(1, last + 1) if (k, reg) in hist.index and hist.loc[(k, reg)].get(tech, 0) > 0)
        n_prev = off.loc[(last, reg, tech)]["n"] if (last, reg, tech) in off.index else 0
        if age < 3 or n_prev < 8:
            out.add(c)
    return out


def history():
    return _panel().groupby(["round", "region", "tech"])["demand"].sum().unstack(fill_value=0.0)


def offer_history():
    """Nombre de produits et équipements moyens par (tour, zone, techno)."""
    raw = _panel()
    if _CACHE.get("offer_key") != _CACHE["key"]:
        _CACHE.update(offer_key=_CACHE["key"], offer=raw.groupby(["round", "region", "tech"]).agg(n=("team", "size"), feat=("feat", "mean")))
    return _CACHE["offer"]


def coverage():
    """Couverture du réseau {zone: {techno: {tour: fraction}}}, d'après le relevé le plus récent."""
    files = sorted((ROOT / "data").glob("couverture_tour_*.json"), key=lambda f: int(f.stem.split("_")[-1]))
    if not files:
        return None
    c = json.load(open(files[-1]))
    return {reg: {tech: {int(k): v / 100.0 for k, v in s.items()} for tech, s in t.items()} for reg, t in c.items()}


# ------------------------------------------------------------------ partage par couverture
def subset_shares(W, C):
    """Part de chaque techno quand chaque client est couvert par la techno i avec la probabilité C[i]
    (indépendamment) et choisit parmi les technos couvertes au prorata de W."""
    k, out = len(W), np.zeros(len(W))
    for S in itertools.product([0, 1], repeat=k):
        if not any(S):
            continue
        p = np.prod([C[i] if S[i] else 1 - C[i] for i in range(k)])
        tot = sum(W[i] for i in range(k) if S[i])
        for i in range(k):
            if S[i]:
                out[i] += p * W[i] / tot
    return out


def fit_appeal(shares, C):
    """Attraits W (le premier fixé à 1) qui reproduisent les parts observées, étant donné la couverture."""
    sh = np.asarray(shares, float) / np.sum(shares)
    if len(sh) == 1:
        return np.ones(1)
    f = lambda x: (lambda s: s / s.sum() - sh)(subset_shares(np.r_[1.0, np.exp(x)], C))
    return np.r_[1.0, np.exp(least_squares(f, np.zeros(len(sh) - 1)).x)]


def appeal_table():
    """Attrait observé de chaque techno (Thermique = 1) par tour et zone : sert à ré-estimer GAMMA_N, GAMMA_F, NEW_APPEAL."""
    hist, off, cov = history(), offer_history(), coverage()
    rows = []
    for (r, reg), h in hist.groupby(level=[0, 1]):
        if r < 2:
            continue
        ref = REF if h[REF].iloc[0] > 0 else max(hist.columns, key=lambda t: h[t].iloc[0])   # Thermique disparu : la plus vendue sert de repère
        techs = [ref] + [t for t in hist.columns if t != ref and h[t].iloc[0] > 0]
        W = fit_appeal([h[t].iloc[0] for t in techs], [cov[reg][t][r - 1] for t in techs])
        for t, w in zip(techs, W):
            o, o0 = off.loc[(r, reg, t)], off.loc[(r, reg, ref)]
            rows.append(dict(tour=r - 1, zone=reg, tech=t, repere=ref, part=h[t].iloc[0] / h.iloc[0].sum(), couverture=cov[reg][t][r - 1], attrait=w,
                             n=o["n"], equip_relatifs=o["feat"] / o0["feat"], attrait_par_produit=w / o["n"]))
    return pd.DataFrame(rows)


def tech_shares_coverage(frame, hist, last, rng=None):
    """Parts des technos au tour de `frame`, par zone, par le modèle de couverture."""
    cov, off = coverage(), offer_history()
    new_round = int(frame["round"].iloc[0])
    out = {}
    for reg, f in frame.groupby("region"):
        cur = hist.loc[(last, reg)]
        techs = [REF] + sorted(t for t in f["tech"].unique() if t != REF) if REF in set(f["tech"]) else sorted(f["tech"].unique())
        old = [t for t in techs if cur.get(t, 0) > 0]
        Wp = dict(zip(old, fit_appeal([cur[t] for t in old], [cov[reg][t][max(last - 1, 1)] for t in old])))
        feat_ref_new = f[f["tech"] == techs[0]]["feat"].mean()
        feat_ref_old = off.loc[(last, reg, old[0])]["feat"]
        W = []
        for t in techs:
            ft = f[f["tech"] == t]
            n_new, rel_new = len(ft), ft["feat"].mean() / feat_ref_new
            if t in Wp:
                o = off.loc[(last, reg, t)]
                w = Wp[t] * (n_new / o["n"]) ** GAMMA_N * (rel_new / (o["feat"] / feat_ref_old)) ** GAMMA_F
            else:                                   # techno nouvelle dans la zone : attrait par produit par défaut (très incertain)
                w = NEW_APPEAL.get(t, 0.03) * n_new * Wp.get(techs[0], 1.0) * 12 / max(len(f[f["tech"] == techs[0]]), 1) * max(rel_new / 0.3, 0.3) ** GAMMA_F
            if rng is not None and t != techs[0]:
                w *= np.exp(rng.normal(0, 0.12 if t in Wp else 0.5))
            W.append(w)
        s = subset_shares(np.array(W), np.array([cov[reg][t][new_round - 1] for t in techs]))
        out[reg] = dict(zip(techs, s / s.sum()))
    return out


def tech_shares_offer(frame, hist, last, rng=None):
    """Parts des technos au tour de `frame`, par zone : la part du tour précédent, corrigée du nombre de produits
    offerts (exposant GAMMA_N), de leurs équipements relatifs (GAMMA_F) et de la couverture (THETA_COV).

    ESSAI ÉCARTÉ (COVERAGE_MODEL = "offre" pour le rejouer). Avec THETA_COV = 0 il faisait mieux que le modèle
    « sous-ensembles » aux tours 4 et 5 (erreur par cellule 8,4 et 10,9 % contre 11,3 et 13,9 %), mais le tour 6
    l'a infirmé : le Thermique a perdu 34 à 50 % de sa demande quand sa couverture est passée de 76-86 % à 46-56 %
    (37,8 % d'erreur contre 33,7 %). La couverture compte donc ; voir `direct_cells`."""
    cov, off = coverage(), offer_history()
    new_round = int(frame["round"].iloc[0])
    out = {}
    for reg, f in frame.groupby("region"):
        cur = hist.loc[(last, reg)]
        tot = cur.sum()
        techs = [REF] + sorted(t for t in f["tech"].unique() if t != REF) if REF in set(f["tech"]) else sorted(f["tech"].unique())
        ref = techs[0] if cur.get(techs[0], 0) > 0 else max(techs, key=lambda t: cur.get(t, 0))
        feat_ref_new, feat_ref_old = f[f["tech"] == ref]["feat"].mean(), off.loc[(last, reg, ref)]["feat"]
        W = []
        for t in techs:
            ft = f[f["tech"] == t]
            n_new, rel_new = len(ft), ft["feat"].mean() / feat_ref_new
            c1 = cov[reg][t][new_round - 1] if cov else 1.0
            if cur.get(t, 0) > 0:
                o = off.loc[(last, reg, t)]
                c0 = cov[reg][t][max(last - 1, 1)] if cov else 1.0
                w = cur[t] / tot * (c1 / max(c0, 1e-3)) ** THETA_COV * (n_new / o["n"]) ** GAMMA_N * (rel_new / (o["feat"] / feat_ref_old)) ** GAMMA_F
            else:                                   # techno nouvelle dans la zone : attrait par produit par défaut (très incertain)
                w = (NEW_APPEAL.get(t, 0.03) * n_new * cur[ref] / tot * 12 / max(len(f[f["tech"] == ref]), 1)
                     * c1 ** THETA_COV * max(rel_new / 0.3, 0.3) ** GAMMA_F)
            if rng is not None and t != ref:
                w *= np.exp(rng.normal(0, 0.12 if cur.get(t, 0) > 0 else 0.5))
            W.append(w)
        W = np.array(W)
        out[reg] = dict(zip(techs, W / W.sum()))
    return out


# ------------------------------------------------------------------ ancienne méthode : progression en logit
def tech_shares(hist, last, rng=None, live=None):
    """Part de chaque technologie au tour suivant, par zone : on prolonge la progression (logit) de la plus récente.

    live : {zone: technologies couvertes au tour prévu}. Quand le Thermique n'en fait plus partie, les parts du tour
    précédent et leur progression se calculent entre technologies vivantes seulement : sinon la progression mesurée
    contient la disparition du Thermique (ses parts se reportent mécaniquement sur les autres) et serait prolongée."""
    out = {}
    for reg in hist.index.get_level_values("region").unique():
        cur = hist.loc[(last, reg)]
        prev_r = PREV.get(last, last - 1)
        prv = hist.loc[(prev_r, reg)] if (prev_r, reg) in hist.index else cur
        if live is not None and LIVE_LOGIT and REF not in live.get(reg, {REF}):
            keep = [t for t in cur.index if t in live[reg]]
            cur, prv = cur[keep] / max(cur[keep].sum(), 1e-9), prv[keep] / max(prv[keep].sum(), 1e-9)
            lo = lambda x: np.log(np.clip(x, 1e-6, 1 - 1e-6) / (1 - np.clip(x, 1e-6, 1 - 1e-6)))
            sh = {}
            for tech in keep:
                if cur[tech] <= 0:
                    continue
                inc = lo(cur[tech]) - lo(prv[tech]) if prv[tech] > 0 else 0.7
                inc = 0.75 * inc + (rng.normal(0, 0.15) if rng is not None else 0.0)
                sh[tech] = 1 / (1 + np.exp(-(lo(cur[tech]) + inc)))
            tot = sum(sh.values())
            out[reg] = {k: v / tot for k, v in sh.items()} if tot > 0 else {}
            continue
        cur = cur / cur.sum()
        prv = prv / prv.sum()
        sh = {}
        for tech in cur.index:
            if tech == "Thermique" or cur[tech] <= 0:
                continue
            lo = lambda x: np.log(x / (1 - x))
            inc = lo(cur[tech]) - lo(prv[tech]) if prv[tech] > 0 else 0.7
            inc = 0.75 * inc + (rng.normal(0, 0.15) if rng is not None else 0.0)   # progression amortie
            sh[tech] = 1 / (1 + np.exp(-(lo(cur[tech]) + inc)))
        tot = sum(sh.values())
        if tot > 0.9:
            sh = {k: v * 0.9 / tot for k, v in sh.items()}
        sh["Thermique"] = 1 - sum(sh.values())
        out[reg] = sh
    return out


# ------------------------------------------------------------------ prévision directe par technologie
def direct_cells(frame, growth, hist, last, rng=None, report=None):
    """Demande de chaque cellule déjà vendue au tour précédent, prévue sans passer par un total de zone :
        demande précédente x (1 + croissance annoncée) x (couverture / couverture précédente)
                           x (nombre de produits / nombre précédent)^GAMMA_N_DIRECT.

    Le tour 6 a montré que la demande d'une technologie suit SA couverture et ne se reporte pas sur les autres :
    Thermique, couverture x0,65 / x0,64 / x0,61 (USA, Chine, Europe), demande x0,66 / x0,60 / x0,50, et le total
    de l'Europe a baissé de 25 % pour +6 % annoncés. Erreur de cette forme sur les cellules existantes, tours 2 à 6 :
    7,5 / 27,5 / 8,5 / 14,3 / 13,0 % (31 % au tour 6 pour le partage d'un total de zone). Elle ne voit pas les sauts
    d'attrait décidés par le scénario (Hybride au tour 3, Électrique en Chine et Hydrogène aux USA au tour 6).
    Une technologie dont la couverture tombe à 0 (Thermique à partir du tour 7) a une demande nulle."""
    cov, off = coverage(), offer_history()
    new_round = int(frame["round"].iloc[0])
    out = {}
    for (reg, tech), f in frame.groupby(["region", "tech"]):
        prev = hist.loc[(last, reg)].get(tech, 0.0) if (last, reg) in hist.index else 0.0
        if prev <= 0 or (last, reg, tech) not in off.index:
            continue
        ratio = 1.0
        if cov:
            c1, c0 = cov[reg][tech][new_round - 1], cov[reg][tech][max(last - 1, 1)]
            ratio = c1 / max(c0, 1e-3)
        v = prev * (1 + growth[reg]) * ratio * (len(f) / off.loc[(last, reg, tech)]["n"]) ** GAMMA_N_DIRECT
        out[f"{reg}|{tech}"] = v * (np.exp(rng.normal(0, 0.12)) if rng is not None else 1.0)
    tau = REPORT if report is None else report
    if tau and cov and (last, "USA") in hist.index:
        # report : la demande qu'une technologie perd avec sa couverture va en partie aux autres cellules de la zone,
        # au prorata de leur demande prévue x leur couverture. La technologie perdante peut elle-même recevoir d'une autre.
        add = {c: 0.0 for c in out}
        for reg in sorted(set(hist.index.get_level_values(1))):
            if (last, reg) not in hist.index:
                continue
            for tech, prev in hist.loc[(last, reg)].items():
                c1, c0 = cov[reg][tech][new_round - 1], cov[reg][tech][max(last - 1, 1)]
                if prev <= 0 or c1 >= c0:
                    continue
                lost = prev * (1 + growth[reg]) * (1 - c1 / max(c0, 1e-3))
                w = {c: out[c] * cov[reg][c.split("|")[1]][new_round - 1] for c in out if c.startswith(reg + "|") and c != f"{reg}|{tech}"}
                tot = sum(w.values())
                for c, x in w.items():
                    if tot > 0:
                        add[c] += tau * lost * x / tot
        out = {c: out[c] + add[c] for c in out}
    return out


# ------------------------------------------------------------------ cellule nouvelle : analogie avec les autres zones
def zone_scale(hist, r, growth=None):
    """Marché de base de chaque zone au tour d'indice interne r : demande de Thermique du tour d'entraînement divisée
    par sa couverture, puis croissances annoncées cumulées (`growth` pour le tour r lui-même s'il est donné)."""
    cov, out = coverage(), {}
    for reg in sorted(set(hist.index.get_level_values(1))):
        z = hist.loc[(1, reg)][REF] / cov[reg][REF][0]
        for k in range(3, r + 1):
            z *= 1 + (growth[reg] if growth is not None and k == r else ANNOUNCED[k][reg])
        out[reg] = z
    return out


def penetration_table():
    """Pénétration = demande / (marché de base de la zone x couverture), par tour, zone et technologie. Elle est proche
    d'une zone à l'autre pour une même technologie (Hybride, tours 1 à 6 : 0,12-0,13 / 0,20-0,26 / 0,37-0,41 /
    0,38-0,43 / 0,36-0,47 / 0,42-0,49) : c'est ce qui permet l'analogie entre zones."""
    hist, cov, rows = history(), coverage(), []
    for (r, reg), h in hist.groupby(level=[0, 1]):
        if r < 2 or r not in ANNOUNCED and r > 3:
            continue
        z = zone_scale(hist, r)[reg]
        for t in hist.columns:
            if h[t].iloc[0] > 0 and cov[reg][t][r - 1] > 0:
                rows.append(dict(tour=r - 1, zone=reg, tech=t, penetration=h[t].iloc[0] / (z * cov[reg][t][r - 1])))
    return pd.DataFrame(rows).pivot_table(index=["tech", "zone"], columns="tour", values="penetration")


def analog_cells(frame, growth, hist, last):
    """Taille d'une cellule nouvelle dans sa zone mais déjà vendue dans une autre zone au tour précédent :
        marché de base de la zone x couverture x pénétration médiane des autres zones x (vendeurs / vendeurs là-bas)^0,5.
    Un seul cas rejoué en aveugle : Électrique en Europe au tour 4 (143 k prévus, 299 réels ; le partage par attrait par
    défaut en donnait 60). Un cas calculé à la main : Hybride en Europe au tour 1 à partir des USA et de la Chine au tour
    d'entraînement (387 k pour 392 réels). Sans analogue (première apparition d'une technologie dans le jeu), la cellule
    garde l'estimation par partage, qui ne vaut presque rien (Hydrogène au tour 5 : 67 et 16 k prévus, 1 k réel)."""
    cov, off = coverage(), offer_history()
    if not cov or (1, "USA") not in hist.index:
        return {}
    new_round = int(frame["round"].iloc[0])
    try:
        z_new, z_old = zone_scale(hist, new_round, growth), zone_scale(hist, last)
    except KeyError:                                      # croissance annoncée d'un tour passé introuvable
        return {}
    out = {}
    for (reg, tech), f in frame.groupby(["region", "tech"]):
        if (last, reg) in hist.index and hist.loc[(last, reg)].get(tech, 0.0) > 0:
            continue
        pens, ns = [], []
        for other in z_old:
            c0 = cov[other][tech][max(last - 1, 1)]
            if other != reg and (last, other) in hist.index and hist.loc[(last, other)].get(tech, 0.0) > 0 and c0 > 0:
                pens.append(hist.loc[(last, other)][tech] / (z_old[other] * c0))
                ns.append(off.loc[(last, other, tech)]["n"])
        if pens:
            out[f"{reg}|{tech}"] = z_new[reg] * cov[reg][tech][new_round - 1] * np.median(pens) * (len(f) / np.median(ns)) ** GAMMA_N_DIRECT
    return out


# ------------------------------------------------------------------ prévision
def forecast(frame, growth, rng=None, method="mixte", hist=None):
    """Taille de chaque cellule `zone|tech` pour le tour décrit par `frame` (décisions des 12 équipes).

    growth : dict zone -> croissance annoncée (ex. 0.04). `hist` : historique à utiliser (défaut : tout le panel).
    method : "mixte" (défaut), "directe", "couverture" ou "logit". « mixte » = moitié partage d'un total de zone (lui-même
    moitié couverture, moitié tendance), moitié prévision directe par technologie (`direct_cells`). Avec `rng`,
    les poids sont tirés au hasard : l'incertitude sur la bonne méthode fait partie des scénarios.
    """
    hist = history() if hist is None else hist
    last = PREV.get(int(frame["round"].iloc[0]), int(frame["round"].iloc[0]) - 1)
    cov0 = coverage()
    dead = []
    if cov0:                                             # technologie sans réseau ce tour (Thermique dès le tour 7) : aucun marché
        nr = int(frame["round"].iloc[0]) - 1
        alive = np.array([cov0[r][t].get(nr, 1.0) > 0 for r, t in zip(frame["region"], frame["tech"])])
        dead = sorted(set((frame["region"] + "|" + frame["tech"])[~alive]))
        frame = frame[alive]
    ep = rng.normal(*EL_PRICE) if rng is not None else EL_PRICE[0]
    ea = rng.normal(*EL_ADV) if rng is not None else EL_ADV[0]
    if coverage() is None and COVERAGE_MODEL != "offre":
        method = "logit"
    sh_c = (tech_shares_offer if COVERAGE_MODEL == "offre" else tech_shares_coverage)(frame, hist, last, rng) if method != "logit" else None
    live = {reg: set(g["tech"]) for reg, g in frame.groupby("region")}        # `frame` ne contient plus que les technologies couvertes
    sh_l = tech_shares(hist, last, rng, live=live) if method != "couverture" else None
    w = {"logit": 1.0, "couverture": 0.0}.get(method, MIX_LOGIT if rng is None else rng.uniform(0, 1))
    out = {}
    for reg, t in frame.groupby("region"):
        techs = sorted(t["tech"].unique())
        t = t[t["last_demand"].notna() & t["p_price"].notna()]
        dprice = np.average(np.log(t["price"].values / t["p_price"].values), weights=t["last_demand"].values)
        dadv = np.log(max(t["adv"].sum(), 1) / max(t["p_adv"].fillna(t["adv"]).sum(), 1))
        total = hist.loc[(last, reg)].sum() * (1 + growth[reg]) * np.exp(ep * dprice + ea * dadv)
        if rng is not None:
            total *= np.exp(rng.normal(0, SD_TOTAL))
        sh = {}
        for tech in techs:
            c = sh_c[reg].get(tech, 0.0) if sh_c else 0.0
            l = sh_l[reg].get(tech, c) if sh_l else 0.0      # techno absente de l'historique : seule la couverture en parle
            sh[tech] = (1 - w) * c + w * l
        tot = sum(sh.values())
        for tech in techs:
            out[f"{reg}|{tech}"] = total * sh[tech] / tot
    if method in ("mixte", "directe") and W_DIRECT > 0:  # troisième méthode : prévision directe par technologie
        # « directe » : cellules déjà vendues par la prévision directe seule, cellules nouvelles par le partage
        wd = 1.0 if method == "directe" else (W_DIRECT if rng is None else rng.uniform(0, 1))
        for c, v in direct_cells(frame, growth, hist, last, rng).items():
            if c in out:
                out[c] = (1 - wd) * out[c] + wd * v
        if ANALOG:                                       # cellule nouvelle dans la zone, déjà vendue ailleurs
            for c, v in analog_cells(frame, growth, hist, last).items():
                if c in out:
                    out[c] = v
    if rng is not None and SD_YOUNG > 0:                 # cellule jeune : la taille prévue vaut un ordre de grandeur
        for c in sorted(young_cells(out, hist, last)):
            out[c] *= np.exp(rng.normal(0, SD_YOUNG))
    out.update({c: 0.0 for c in dead})
    return out


# ------------------------------------------------------------------ entrée sur une technologie
def entry_estimate(d, growth, tech, feat=1, replace=None, us="tomobil"):
    """Ordre de grandeur de la demande si nous lançons `tech` dans chaque zone au tour suivant, les concurrents
    ne changeant rien. `replace` : technologie du modèle abandonné pour lui faire place (ex. "Thermique"), ou None.

    Méthode : prévision « mixte » de la taille de la cellule (analogie avec les autres zones si la technologie est
    nouvelle dans la zone), puis part égale entre vendeurs (1/n).
    Très incertain pour une technologie peu vendue (attrait par produit : NEW_APPEAL) ; à lire comme un ordre de grandeur.
    """
    from model.sim import finalize, status_quo_frame
    base = status_quo_frame(d)
    rows = []
    for reg in sorted(base["region"].unique()):
        f = base[~((base["team"] == us) & (base["region"] == reg) & (base["tech"] == replace))] if replace else base
        new = dict(round=base["round"].iloc[0], region=reg, tech=tech, team=us, feat=feat, cell=f"{reg}|{tech}", price=np.nan, adv=0.0,
                   p_price=np.nan, last_demand=np.nan)
        g = finalize(pd.concat([f, pd.DataFrame([new])], ignore_index=True))
        mk0, mk1 = forecast(base, growth), forecast(g, growth)      # « mixte » ; cellule nouvelle : analogie avec les autres zones
        n = int(((g["region"] == reg) & (g["tech"] == tech)).sum())
        rows.append(dict(zone=reg, tech=tech, couverture=coverage()[reg][tech][int(base["round"].iloc[0]) - 1], vendeurs_avec_nous=n,
                         cellule_sans_nous=mk0.get(f"{reg}|{tech}", 0.0), cellule_avec_nous=mk1[f"{reg}|{tech}"],
                         notre_demande_part_egale=mk1[f"{reg}|{tech}"] / n,
                         perte_modele_remplace=(base[(base["team"] == us) & (base["region"] == reg) & (base["tech"] == replace)]["last_demand"].sum() if replace else 0.0)))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ rejeu aveugle de cet étage
_ANNOUNCED = {2: dict(USA=.05, Chine=.05, Europe=.05), 3: dict(USA=.05, Chine=.085, Europe=.03)}   # tours 1 et 2 : lus dans les conditions de marché


class _Announced(dict):
    """Croissance annoncée par indice interne de tour : data/tour_N_inputs.json (N = indice - 1), sinon les valeurs ci-dessus."""

    def __missing__(self, r):
        f = ROOT / "data" / f"tour_{r - 1}_inputs.json"
        if not f.exists():
            raise KeyError(r)
        return json.load(open(f))["growth"]

    def __contains__(self, r):
        return dict.__contains__(self, r) or (ROOT / "data" / f"tour_{r - 1}_inputs.json").exists()


ANNOUNCED = _Announced(_ANNOUNCED)


def blind_frame(d, r):
    """Décisions réelles du tour r (panel enrichi `d`) avec la demande du tour précédent."""
    raw = _panel()
    prev = raw[raw["round"] == PREV.get(r, r - 1)].set_index(["region", "tech", "team"])["demand"]
    t = d[d["round"] == r].copy()
    t["last_demand"] = [prev.get(k, np.nan) for k in zip(t["region"], t["tech"], t["team"])]
    t["cell"] = t["region"] + "|" + t["tech"]
    return t


def backtest(d, rounds=None, verbose=True):
    """Pour chaque tour : tailles de cellule prévues avec l'historique antérieur seulement, comparées au réel."""
    full = history()
    rows = []
    for r in rounds or [x for x in sorted(d["round"].unique()) if x >= 3]:
        f = blind_frame(d, r)
        act = f.groupby("cell")["demand"].sum()
        for method in ("logit", "couverture", "mixte", "directe"):
            mk = forecast(f, ANNOUNCED[r], method=method, hist=full.loc[:r - 1])
            for c in act.index:
                rows.append(dict(tour=r - 1, cellule=c, methode=method, prevu=mk.get(c, 0.0), reel=act[c]))
    T = pd.DataFrame(rows)
    T["zone"] = T["cellule"].str.split("|").str[0]
    S = T.assign(e=(T["prevu"] - T["reel"]).abs()).groupby(["tour", "methode"]).agg(e=("e", "sum"), reel=("reel", "sum"))
    Z = T.groupby(["tour", "methode", "zone"])[["prevu", "reel"]].sum()
    S["erreur_cellules_pct"] = S["e"] / S["reel"] * 100
    S["erreur_zones_pct"] = (Z["prevu"] - Z["reel"]).abs().groupby(level=[0, 1]).sum() / S["reel"] * 100
    if verbose:
        print("\n=== Rejeu aveugle de la taille des marchés (étage model/market.py) ===")
        print(S[["erreur_cellules_pct", "erreur_zones_pct"]].round(1).unstack().to_string())
    return T, S


if __name__ == "__main__":
    from model.panel2 import build
    pd.set_option("display.width", 250)
    T, S = backtest(build())
    print(T[T["methode"] == "mixte"].assign(err_pct=lambda x: (x.prevu / x.reel - 1) * 100).round(1).to_string(index=False))
    print(appeal_table().round(3).to_string(index=False))
