"""Comportements possibles des 11 concurrents pour le tour à venir.

Chaque fonction reçoit le cadre « statu quo » (chacun répète ses décisions) et renvoie un cadre modifié.
"""
import numpy as np
import pandas as pd

from model.sim import FEAT_COST, US, finalize, row_info, row_params, u_row

MAXFEAT = 10


def _rivals(f):
    return (f["team"] != US).values


def statu_quo(f, d, params, rng):
    return f.copy()


def tendance(f, d, params, rng, damp=0.6):
    """Chaque équipe prolonge (amorti) ses variations du dernier tour."""
    f = f.copy()
    last = f["round"].iloc[0] - 1
    prev = d[d["round"] == last].set_index(["team", "region", "tech"])
    key = list(zip(f["team"], f["region"], f["tech"]))
    pp = np.array([prev["p_price"].get(k, np.nan) for k in key])
    pf = np.array([prev["p_feat"].get(k, np.nan) for k in key])
    pa = np.array([prev["p_adv"].get(k, np.nan) for k in key])
    m = _rivals(f)
    dp = np.nan_to_num(np.log(f["price"].values / pp)) * damp
    df = np.nan_to_num(f["feat"].values - pf) * damp
    da = np.nan_to_num(np.log(np.maximum(f["adv"].values, 1) / np.maximum(pa, 1))) * damp
    f.loc[m, "price"] = (f["price"].values * np.exp(np.clip(dp, -0.12, 0.12)))[m]
    f.loc[m, "feat"] = np.clip(np.round(f["feat"].values + df), 1, MAXFEAT)[m]
    f.loc[m, "adv"] = (f["adv"].values * np.exp(np.clip(da, -0.5, 0.5)))[m]
    return f


def guerre_des_prix(f, d, params, rng):
    f = f.copy()
    m = _rivals(f)
    cut = rng.uniform(0.05, 0.10)
    f.loc[m, "price"] = f.loc[m, "price"] * (1 - cut)
    f.loc[m, "feat"] = np.clip(f.loc[m, "feat"] + 1, 1, MAXFEAT)
    return f


def montee_en_gamme(f, d, params, rng):
    """Imitation du leader : plus d'équipements, prix et publicité en hausse, effort ESG."""
    f = f.copy()
    m = _rivals(f)
    f.loc[m, "price"] = f.loc[m, "price"] * 1.05
    f.loc[m, "feat"] = np.clip(f.loc[m, "feat"] + 2, 1, MAXFEAT)
    f.loc[m, "adv"] = f.loc[m, "adv"] * 1.3
    f.loc[m, "esg"] = f.loc[m, "esg"] + 0.06
    f.loc[m & (f["cert1"] == 0).values, "cert1"] = 1.0
    return f


def meilleure_reponse(f, d, params, rng, markets=None, rounds=1, who=None):
    """Chaque concurrent choisit prix, équipements et publicité qui maximisent sa propre marge
    face aux décisions des autres ; `rounds` > 1 itère vers un équilibre."""
    f = f.copy()
    if markets is None:
        markets = f.groupby("cell")["last_demand"].sum().to_dict()
    pm = np.arange(0.85, 1.2001, 0.025)
    dfe = np.array([-1, 0, 1, 2, 3])
    am = np.array([0.5, 0.75, 1.0, 1.5, 2.0])
    P, Fd, Am = np.meshgrid(pm, dfe, am, indexing="ij")
    for _ in range(rounds):
        f = finalize(f)
        p = row_params(f, params)
        info = row_info(f)
        u = u_row(p, info, f["price"].values, f["feat"].values, np.maximum(f["adv"].values, 1), f["adv_o"].values)
        A = np.exp(u)
        cells, inv = np.unique(f["cell"].values, return_inverse=True)
        tot = np.bincount(inv, A)[inv]
        new = f[["price", "feat", "adv"]].values.copy()
        for i in np.where(_rivals(f) if who is None else (f["team"] == who).values)[0]:
            pi = {k: v[i] for k, v in p.items()}
            ii = {k: v[i] for k, v in info.items()}
            price = f["price"].values[i] * P
            feat = np.clip(f["feat"].values[i] + Fd, 1, MAXFEAT)
            adv = np.maximum(f["adv"].values[i], 50) * Am
            a = np.exp(u_row(pi, ii, price, feat, adv, f["adv_o"].values[i]))
            q = markets[f["cell"].values[i]] * a / (a + tot[i] - A[i])
            margin = (price * f["fx"].values[i] - f["unit_cost"].values[i] - feat * FEAT_COST[f["region"].values[i]]) * q / 1000 - adv
            j = np.unravel_index(np.argmax(margin), margin.shape)
            new[i] = [price[j], feat[j], adv[j]]
        f[["price", "feat", "adv"]] = new
    return finalize(f)


def equilibre(f, d, params, rng, markets=None):
    return meilleure_reponse(f, d, params, rng, markets=markets, rounds=3)


def bruit(f, rng, price=0.03, feat=0.3, adv=0.25):
    """Bruit sur les décisions des concurrents."""
    f = f.copy()
    m = _rivals(f)
    n = m.sum()
    f.loc[m, "price"] = f.loc[m, "price"] * np.exp(rng.normal(0, price, n))
    f.loc[m, "feat"] = np.clip(np.round(f.loc[m, "feat"] + rng.normal(0, feat * 2, n) * (rng.random(n) < 0.5)), 1, MAXFEAT)
    f.loc[m, "adv"] = np.maximum(f.loc[m, "adv"] * np.exp(rng.normal(0, adv, n)), 50)
    f.loc[m, "esg"] = f.loc[m, "esg"] + rng.normal(0, 0.04, n)
    return finalize(f)


BEHAVIOURS = {"statu quo": statu_quo, "tendance": tendance, "guerre des prix": guerre_des_prix,
              "montée en gamme": montee_en_gamme, "meilleure réponse": meilleure_reponse, "équilibre": equilibre}


def melange(f, d, params, rng, markets=None):
    """Chaque concurrent tire son propre comportement."""
    frames = {name: (fn(f, d, params, rng, markets=markets) if name in ("meilleure réponse", "équilibre") else fn(f, d, params, rng))
              for name, fn in BEHAVIOURS.items() if name != "équilibre"}
    out = f.copy()
    names = list(frames)
    for team in out["team"].unique():
        if team == US:
            continue
        src = frames[names[rng.integers(len(names))]]
        m = (out["team"] == team).values
        out.loc[m, ["price", "feat", "adv", "esg", "cert1"]] = src.loc[m, ["price", "feat", "adv", "esg", "cert1"]].values
    return finalize(out)


# ------------------------------------------------------------------ changement de gamme
# Probabilités qu'un concurrent lance une technologie dans une zone (calées par fit_gamme sur les transitions observées) :
#   libre_possede : il la vend déjà ailleurs et a une place (moins de 2 modèles, ou un modèle dont le réseau s'effondre) ;
#   libre_nouveau : il ne l'a jamais vendue (licence ou R&D à acquérir) et a une place ;
#   echange       : il la vend déjà ailleurs et doit lui sacrifier un modèle dont le réseau tient.
GAMME_P = dict(libre_possede=0.46, libre_nouveau=0.31, echange=0.15)   # fréquences observées aux tours 4 à 7 (28, 65 et 13 occasions) ; tour 7 seul : 0,62 / 0,48
DROP = 0.15          # baisse de couverture (en points) à partir de laquelle un modèle est « menacé »


def _gamme_options(f, d, cov, team, reg, new_round):
    """Pour un concurrent dans une zone : (modèle à remplacer ou None, candidats possédés, candidats jamais vendus, type de place)."""
    sold = list(f[(f["team"] == team) & (f["region"] == reg)]["tech"])
    c1 = {t: cov[reg][t].get(new_round - 1, 0.0) for t in cov[reg]}
    c0 = {t: cov[reg][t].get(max(new_round - 2, 0), 0.0) for t in cov[reg]}
    owned = set(d[d["team"] == team]["tech"])
    cand = [t for t in c1 if c1[t] > 0 and t not in sold]
    threatened = sorted((t for t in sold if c1[t] <= 0 or c0[t] - c1[t] >= DROP), key=lambda t: c1[t] - c0[t])
    if len(sold) < 2:
        out, kind = None, "libre"
    elif threatened:
        out, kind = threatened[0], "libre"
    else:
        ld = f[(f["team"] == team) & (f["region"] == reg)].set_index("tech")["last_demand"].fillna(0)
        out, kind = ld.idxmin(), "echange"
    return out, [t for t in cand if t in owned], [t for t in cand if t not in owned], kind, c1


def changement_de_gamme(f, d, params, rng, p=None):
    """Les concurrents changent de gamme : dans chaque zone, chacun peut lancer une technologie couverte qu'il n'y vend
    pas, à la place d'un modèle menacé (réseau en chute) ou, plus rarement, de son modèle le plus faible. Le nouveau
    produit prend le prix et les équipements médians de la cellule et la publicité moyenne de l'équipe dans la zone ;
    une cellule où personne ne vend n'est pas ouverte par ce comportement. S'applique après un autre comportement."""
    from model import market
    from model.sim import with_products
    cov, p = market.coverage(), {**GAMME_P, **(p or {})}
    if not cov:
        return f
    new_round = int(f["round"].iloc[0])
    for team in sorted(set(f["team"]) - {US}):
        for reg in sorted(set(f["region"])):
            out, owned, fresh, kind, c1 = _gamme_options(f, d, cov, team, reg, new_round)
            choice = None
            for pool, key in ((owned, "libre_possede" if kind == "libre" else "echange"), (fresh, "libre_nouveau" if kind == "libre" else None)):
                pool = [t for t in pool if ((f["cell"] == f"{reg}|{t}") & (f["team"] != team)).any()]
                if choice is None and key and pool and rng.random() < p[key]:
                    w = np.array([c1[t] for t in pool])
                    choice = pool[rng.choice(len(pool), p=w / w.sum())]
            if choice is None:
                continue
            mine = f[f["team"] == team]
            ref, zone = f[f["cell"] == f"{reg}|{choice}"], mine[mine["region"] == reg]
            keep = {c: (0, 0, 0) for c in mine["cell"] if c != f"{reg}|{out}"}
            f = with_products(f, {**keep, f"{reg}|{choice}": (float(ref["price"].median()), float(max(1, round(ref["feat"].median()))),
                                                              float(zone["adv"].mean() if len(zone) else ref["adv"].median()))}, team=team)
    return finalize(f)


def gamme_transitions(d, r):
    """Transitions de gamme observées entre le tour d'indice r-1 et r : une ligne par (concurrent, zone) avec la place
    disponible, les candidats, et la technologie réellement lancée."""
    from model import market
    from model.sim import status_quo_frame
    cov = market.coverage()
    f = status_quo_frame(d[d["round"] < r])
    now = d[d["round"] == r]
    rows = []
    for team in sorted(set(f["team"])):
        for reg in sorted(set(f["region"])):
            out, owned, fresh, kind, _ = _gamme_options(f, d[d["round"] < r], cov, team, reg, r)
            before = set(f[(f["team"] == team) & (f["region"] == reg)]["tech"])
            after = set(now[(now["team"] == team) & (now["region"] == reg)]["tech"])
            added = after - before
            rows.append(dict(tour=r - 1, team=team, zone=reg, place=kind, sortant=out, possedes=owned, nouveaux=fresh,
                             lance_possede=bool(added & set(owned)), lance_nouveau=bool(added & set(fresh))))
    return pd.DataFrame(rows)


def fit_gamme(d, rounds=None):
    """Fréquences observées des trois types de changement de gamme (tours où une technologie hors Thermique existe)."""
    T = pd.concat([gamme_transitions(d, r) for r in (rounds or [r for r in sorted(d["round"].unique()) if r >= 5])], ignore_index=True)
    T = T[T["team"] != US]
    lib, ech = T[T["place"] == "libre"], T[T["place"] == "echange"]
    a, b, c = lib[lib["possedes"].str.len() > 0], lib[lib["nouveaux"].str.len() > 0], ech[ech["possedes"].str.len() > 0]
    return dict(libre_possede=float(a["lance_possede"].mean()) if len(a) else np.nan, n_libre_possede=len(a),
                libre_nouveau=float(b["lance_nouveau"].mean()) if len(b) else np.nan, n_libre_nouveau=len(b),
                echange=float(c["lance_possede"].mean()) if len(c) else np.nan, n_echange=len(c)), T


# ------------------------------------------------------------------ règle apprise sur les tours passés
def _rule_features(t):
    g = t.groupby(t["region"] + "|" + t["tech"] + "|" + t["round"].astype(str))
    rel_p = np.log(t["p_price"]) - g["p_price"].transform(lambda x: np.log(x).mean())
    rel_f = t["p_feat"] - g["p_feat"].transform("mean")
    sh = np.log(t["p_share"].fillna(1 / 12) * 12)
    return np.column_stack([np.ones(len(t)), rel_p, rel_f, sh, (t["p_fill"] < 0.95) * 1.0, (t["tech"] == "Hybride") * 1.0])


def fit_rule(d):
    """Régression des variations de décisions sur la situation de l'équipe au tour précédent
    (prix relatif, équipements relatifs, part de marché, rupture)."""
    t = d[(d["round"] >= 3) & d["p_price"].notna() & (d["team"] != US)]
    if len(t) < 30:
        return None
    X = _rule_features(t)
    Y = np.column_stack([np.log(t["price"] / t["p_price"]), t["feat"] - t["p_feat"], np.log(t["adv"].clip(lower=50) / t["p_adv"].clip(lower=50))])
    B = np.linalg.lstsq(X, Y, rcond=None)[0]
    resid = Y - X @ B
    return dict(B=B, sd=resid.std(0), r2=1 - resid.var(0) / Y.var(0), n=len(t))


def regle_apprise(f, d, params, rng, rule=None):
    rule = rule or fit_rule(d)
    f = f.copy()
    if rule is None:
        return f
    m = _rivals(f)
    pred = np.nan_to_num(_rule_features(f) @ rule["B"])        # produit lancé dans le tour (pas d'historique) : décisions inchangées
    f.loc[m, "price"] = (f["price"].values * np.exp(np.clip(pred[:, 0], -0.15, 0.15)))[m]
    f.loc[m, "feat"] = np.clip(np.round(f["feat"].values + pred[:, 1]), 1, MAXFEAT)[m]
    f.loc[m, "adv"] = (f["adv"].values * np.exp(np.clip(pred[:, 2], -0.6, 0.6)))[m]
    return f


BEHAVIOURS["règle apprise"] = regle_apprise


def test_rule(d, target):
    """La règle apprise sur les tours < target prédit-elle mieux les décisions du tour target que le statu quo ?"""
    rule = fit_rule(d[d["round"] < target])
    t = d[(d["round"] == target) & d["p_price"].notna() & (d["team"] != US)]
    if rule is None or t.empty:
        return None
    pred = _rule_features(t) @ rule["B"]
    real = np.column_stack([np.log(t["price"] / t["p_price"]), t["feat"] - t["p_feat"], np.log(t["adv"].clip(lower=50) / t["p_adv"].clip(lower=50))])
    return pd.DataFrame(dict(erreur_regle=np.abs(real - pred).mean(0), erreur_statu_quo=np.abs(real).mean(0), r2_apprentissage=rule["r2"]),
                        index=["variation de prix (log)", "variation d'équipements", "variation de publicité (log)"])
