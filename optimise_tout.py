"""Recherche sur l'ensemble des leviers de décision.

  python3 optimise_tout.py --tour N                 # toutes les étapes disponibles
  python3 optimise_tout.py --tour N --etapes D E    # seulement certaines étapes
  python3 optimise_tout.py --tour N --sec           # sans la plateforme (étapes A et B seulement)

Deux évaluateurs : le simulateur local pour la demande, le prévisionnel de la plateforme pour les coûts
(oracle.Oracle, dans la zone personnelle, restaurée à la fin). Rien n'est enregistré pour l'équipe ici :
le programme propose, la décision se prend ensuite, test à l'appui.

Étapes (voir leviers.py pour la liste des champs de chacune) :
  0  contrôle de couverture : tout champ de la plateforme doit être classé
  A  offre : ordre de grandeur d'une entrée sur une autre technologie (model/market.entry_estimate)
  B  marketing : frontière gain / éloignement (strategy.frontier)
  D  leviers discrets : énumération par groupe, coût lu sur la plateforme, effet sur la demande d'après
     ce que les 12 équipes ont joué (model/esg.Impact)
  E  finance et impôts : prix de transfert, dette, transferts internes
Sortie : out/tourN_recherche.md et out/tourN_recherche.json
"""
import argparse
import itertools
import json
import time
import warnings

import numpy as np
import pandas as pd

from cesim.client import ROOT
from leviers import report as lever_report

warnings.filterwarnings("ignore")
PROCESS = ["esg.emissions.invest", "esg.energy.invest", "esg.water.invest"]
POINTS_PER_PROCESS = 5.0      # points de demande par amélioration de processus : estimation prudente (écarts observés : 8 à 10)
POINTS_RENEWABLE = 11.0       # écart de demande entre 0 % et 100 % d'énergie renouvelable (observé : -8,6 % contre +2,4 %)
POINTS_PER_NOTE = 5.2         # points de demande par point de note « développement durable » des fournisseurs
POINTS_CERT = 11.0            # certification obtenue (moteur : +0,11 en log)
OUT = ROOT / "out"


def M(x):
    """k USD -> M USD."""
    return None if x is None else x / 1000.0


# ====================================================================== étape D : leviers discrets
def groups_D(o, impact):
    """Candidats de chaque groupe : liste de (libellé, décisions, points de demande ou None si inconnu, remarque)."""
    st, base = o.state, o.base
    from model.esg import MENU_TO_REPORT, TRN
    cur_pts, _, _ = impact.points(base)
    pts = lambda dec: impact.points({**base, **dec})
    G = {}
    # politiques de travail : chaque option de chaque menu, les autres inchangées (effets additifs)
    for key in MENU_TO_REPORT:
        if key in st:
            c = []
            for opt in st[key]["options"]:
                p, _, unk = pts({key: opt})
                c.append((opt, {key: opt}, None if unk else p - cur_pts, "; ".join(unk)))
            G[f"politique : {key}"] = c
    # priorités de formation : les 32 combinaisons
    if all(k in st for k in TRN):
        c = []
        for combo in itertools.product([False, True], repeat=5):
            dec = dict(zip(TRN, combo))
            p, _, unk = pts(dec)
            c.append(("".join(str(int(x)) for x in combo), dec, p - cur_pts, "; ".join(unk)))
        G["priorités de formation (base, sécurité, santé, non-discrimination, éthique)"] = c
    # recyclabilité x engagement
    if "esg.recyclability" in st:
        c = []
        for opt in st["esg.recyclability"]["options"]:
            for eng in (False, True):
                dec = {"esg.recyclability": opt, "esg.recyclability.commit": eng}
                p, _, unk = pts(dec)
                c.append((opt + (" + engagement" if eng else ""), dec, None if unk else p - cur_pts, "; ".join(unk)))
        G["recyclabilité"] = c
    # améliorations de processus : 8 combinaisons
    if all(k in st for k in PROCESS):
        G["améliorations de processus (CO2, énergie, eau)"] = [
            ("".join(str(int(x)) for x in combo), dict(zip(PROCESS, combo)), POINTS_PER_PROCESS * sum(combo), "points par amélioration : estimation prudente")
            for combo in itertools.product([False, True], repeat=3)]
    # énergie renouvelable
    ren = [k for k in st if k.startswith("esg.renew.energy")]
    if ren:
        G["énergie renouvelable, %"] = [(str(v), {k: v for k in ren}, POINTS_RENEWABLE * (v - np.mean([float(base[k]) for k in ren])) / 100, "")
                                         for v in (0, 50, 100)]
    # fournisseurs : tous les sous-ensembles non vides
    sup = sorted(k for k in st if k.startswith("supplier."))
    if sup:
        notes = supplier_notes()
        cur = [k for k in sup if base[k]]
        mean = lambda ks: np.mean([notes.get(int(k.split(".")[1]), np.nan) for k in ks])
        c = []
        for combo in itertools.product([False, True], repeat=len(sup)):
            ks = [k for k, x in zip(sup, combo) if x]
            if not ks:
                continue
            d = mean(ks) - mean(cur)
            c.append(("+".join(k.split(".")[1] for k in ks), dict(zip(sup, combo)), None if np.isnan(d) else (POINTS_PER_NOTE + 8.0) * d,
                      "note = image moyenne publiée ; 5,2 pts (développement durable) + 8 pts (qualité) par point"))
        G["fournisseurs actifs"] = c
    # certification
    if "esg.reporting" in st and len(st["esg.reporting"]["options"]) > 1:
        G["certification"] = [(opt, {"esg.reporting": opt}, (POINTS_CERT if not opt.startswith("Pas") else 0.0) - (POINTS_CERT if not str(base["esg.reporting"]).startswith("Pas") else 0.0),
                               "l'écart entre niveaux n'est pas mesuré") for opt in st["esg.reporting"]["options"]]
    # événements : coût seulement, l'effet sur la demande n'est pas publié
    for key in [k for k in st if k.startswith("esg.") and o.page.get(k) == "events" and len(st[k]["options"]) > 1]:
        G[f"événement : {key}"] = [(opt, {key: opt}, None, "effet sur la demande non publié") for opt in st[key]["options"]]
    # service client (apparu au tour 8) : garantie, collecte, protection et partage des données. Effet annoncé par
    # l'instructeur (demande, score S relatif à la moyenne des équipes) mais jamais observé : coût seulement
    for key in [k for k in st if k.startswith("esg.after.sales.") and len(st[k].get("options", {})) > 1]:
        G[f"service client : {key}"] = [(opt, {key: opt}, None, "effet annoncé (demande, score S), jamais observé") for opt in st[key]["options"]]
    # salaire et budget de formation : coût seulement. Sur la productivité des ingénieurs ils n'ont aucun effet mesurable
    # (objectif.productivite_rejeu) ; l'effet sur le score S passe par la rotation du personnel, non modélisé
    sal, trn = "rd.engineer.salary.1", "rd.engineer.training.1"
    if sal in st and trn in st:
        s0, t0 = float(base[sal]), float(base[trn])
        G["salaire et budget de formation"] = [(f"{int(s)} / {int(t)}", {sal: int(s), trn: int(t)}, None if (s, t) != (s0, t0) else 0.0, "productivité : aucun effet mesuré ; score S par la rotation, non modélisé")
                                               for s in (s0, s0 + 500, s0 + 1500) for t in (t0, round(t0 * 1.5), t0 * 2)]
    return G


def supplier_notes():
    """Image moyenne publiée de chaque fournisseur (1 à 5) au dernier tour, par numéro de fournisseur."""
    from model.panel import available_rounds
    from model.report import lines
    names = ["Maîtres Matérialistes", "Composants Colossaux", "Singularités Quantiques", "Fusions Dynamiques", "Innovation Réinventée"]
    _, L = lines(available_rounds()[-1])
    out = {}
    for p, v in L:
        if len(p) >= 2 and p[-2] == "Image moyenne par fournisseur" and p[-1] in names and not isinstance(v[0], str):
            out[names.index(p[-1]) + 1] = float(v[0])
    return out


def composante(groupe):
    """Composante ESG (donc pilier noté E, S ou G) que déplace un groupe de leviers de l'étape D."""
    for debut, comp in (("politique", "politiques"), ("priorités de formation", "formation"), ("recyclabilité", "recyclabilite"),
                        ("améliorations de processus", "processus"), ("énergie renouvelable", "renouvelable"), ("fournisseurs", "fournisseurs")):
        if groupe.startswith(debut):
            return comp
    return None


def en_points(bareme, x, groupe, option, dnet, dpts, etat=None):
    """Valeur d'une option en points du barème : coût (résultat net), demande, score du pilier ESG, effet direct,
    bilan (découvert et indépendance financière de l'état `etat` lu sur la plateforme), tours suivants.
    Renvoie (total, détail par critère). dpts inconnu : seul le coût est compté."""
    kw = dict(d_net=dnet or 0.0)
    if etat and etat.get("previsionnel"):
        kw["finance"] = etat["previsionnel"]
    if groupe.startswith("améliorations de processus"):      # effet cumulatif et définitif, payé une seule fois
        kw["durable"] = True
    comp = composante(groupe)
    if dpts is not None:
        kw["d_demande"] = dpts
        if comp == "fournisseurs":                           # dpts = 13,2 points par point de note : 5,2 d'impact G, et le score DDRS (qualité + durable)
            d_note = dpts / (POINTS_PER_NOTE + 8.0)
            kw["d_impacts"] = {comp: POINTS_PER_NOTE * d_note}
            kw["valeurs"] = {"fournisseurs": float(bareme.nous["fournisseurs"]) + 2 * d_note}
        elif comp:
            kw["d_impacts"] = {comp: dpts}
    if comp == "formation" and set(option) <= {"0", "1"}:    # les priorités de formation portent la productivité des ingénieurs, critère noté
        import objectif as OB
        dprod, _ = OB.productivite([c == "1" for c in option])
        kw["valeurs"] = {"productivité": float(bareme.last["productivité"]) + dprod}
    if groupe == "certification":
        from model.points import CERT_POINTS
        kw["valeurs"] = {"certification": next((v for k, v in CERT_POINTS.items() if option.startswith(k)), 0)}
    L = bareme.levier(x, **kw)
    return float(L.sum()), {k: round(float(v), 2) for k, v in L.items() if abs(v) >= 0.05}


def step_D(o, vpp, log, bareme=None, x=None):
    from model.esg import Impact
    impact = Impact()
    base = o.evaluate({})
    chosen, rows = {}, []
    log(f"\n## Étape D — leviers discrets\n\nValeur d'un point de demande : {vpp:.0f} M USD par tour (marge brute / 100), à condition de pouvoir produire.\n"
        f"Référence : résultat net {M(base['net']):.0f} M USD, score ESG cumulé {base.get('score_esg')}, fournisseurs requis {base.get('fournisseurs_requis')}.")
    for name, cands in groups_D(o, impact).items():
        res = []
        # la plateforme ne sert que pour les candidats plausibles : tous si le groupe est petit, sinon la base et les meilleurs en demande
        if len(cands) > 12:
            known = sorted([c for c in cands if c[2] is not None], key=lambda c: -c[2])
            keep = {c[0] for c in known[:6]} | {c[0] for c in cands if all(o.base.get(k) == v or (isinstance(v, bool) and bool(o.base.get(k)) == v) for k, v in c[1].items())}
        else:
            keep = {c[0] for c in cands}
        for label, dec, dpts, note in cands:
            r = o.evaluate(dec) if label in keep else None
            if r and "refus" in r:
                res.append(dict(groupe=name, option=label, d_net=None, d_points=dpts, valeur=None, note=r["refus"], dec=dec))
                continue
            dnet = M(r["net"] - base["net"]) if r else None
            total = None if (dnet is None or dpts is None) else dnet + dpts * vpp
            pts, det = en_points(bareme, x, name, label, dnet, dpts, r) if (bareme is not None and dnet is not None) else (None, {})
            res.append(dict(groupe=name, option=label, d_net=dnet, d_points=dpts, valeur=total, bareme=pts, bareme_detail=det, note=note, dec=dec,
                            requis=r.get("fournisseurs_requis") if r else None, actifs=r.get("fournisseurs_actifs") if r else None,
                            score=r.get("score_esg") if r else None, dette_ct=sum(r.get("dette_ct_nouvelle") or [0]) if r else None))
        # une option jamais jouée par personne (effet extrapolé) n'est pas retenue : elle reste affichée pour information
        # avec le barème : l'option se juge en points (seuil 0,3 point), toujours à effet connu ; sinon en M USD (seuil 1 M USD)
        crit, seuil = ("bareme", 0.3) if bareme is not None else ("valeur", 1)
        ok = [r for r in res if r["valeur"] is not None and r.get(crit) is not None and "extrapolé" not in r["note"]]
        best = max(ok, key=lambda r: r[crit]) if ok else None
        cur = next((x for x in res if x["d_net"] is not None and abs(x["d_net"]) < 1e-9 and (x["d_points"] in (0, 0.0))), None)
        log(f"\n### {name}\n\n| Option | Résultat net, M USD | Demande, points de % | Valeur, M USD | Barème, points | Détail des points | Remarque |\n|---|---|---|---|---|---|---|")
        tri = lambda r: -(r[crit] if r.get(crit) is not None else (r["bareme"] - 1e3 if r.get("bareme") is not None else -1e9))
        for r in sorted(res, key=tri)[:14]:
            f = lambda v, s="{:+.0f}": "inconnu" if v is None else s.format(v)
            mark = " **(retenu)**" if best is r and r[crit] > seuil else ""
            cout_seul = " (coût seul)" if r.get("bareme") is not None and r["d_points"] is None else ""
            log(f"| {r['option']}{mark} | {f(r['d_net'])} | {f(r['d_points'], '{:+.1f}')} | {f(r['valeur'])} | {f(r.get('bareme'), '{:+.2f}')}{cout_seul} | {r.get('bareme_detail') or ''} | {r['note']} |")
        if best and best[crit] > seuil:
            chosen.update(best["dec"])
        rows += res
    return chosen, rows


# ====================================================================== étape E : finance et impôts
def step_E(o, dec, log, bareme=None, x=None):
    base = o.evaluate(dec)
    ZN = {"USA": "net_usa", "Chine": "net_chine", "Europe": "net_europe"}
    if bareme is not None and base.get("previsionnel"):       # le bilan de référence est celui de l'état de départ de l'étape
        bareme.plateforme(base["previsionnel"])

    def pts(r):
        """Points du barème d'un état du prévisionnel par rapport à la référence : marges opérationnelles par entité
        (EBIT / chiffre d'affaires total, cessions internes comprises, lues sur la plateforme), ROE, rentabilité de
        l'action, création de valeur, découvert et indépendance financière (bilan de l'état, par scénario de ventes)."""
        if bareme is None or any(r.get(k) is None or base.get(k) is None for k in ZN.values()):
            return None
        import objectif as OB
        m0, m1 = OB.marges_plateforme(base.get("previsionnel")), OB.marges_plateforme(r.get("previsionnel"))
        kw = dict(d_net=M(r["net"] - base["net"]), finance=r.get("previsionnel"))
        if len(m0) == 3 and len(m1) == 3:
            kw["d_marge_zone"] = {z: m1[z] - m0[z] for z in m0}
        else:                                                 # compte de résultat par entité non lu : résultat net de l'entité, numérateur seul
            kw["d_net_zone"] = {z: M(r[k] - base[k]) for z, k in ZN.items()}
        return float(bareme.levier(x, **kw).sum())

    def gain(r, ref_net, ref_pts):                        # en points si le barème est calculable, sinon en résultat net
        p = pts(r)
        return (p - ref_pts) > 0.2 if p is not None else r["net"] > ref_net + 1000
    log(f"\n## Étape E — finance et impôts\n\nRéférence (avec les choix de l'étape D) : résultat net {M(base['net']):.0f} M USD, "
        f"dette à court terme nouvelle {base.get('dette_ct_nouvelle')}, trésorerie de fin {base.get('tresorerie_fin')}.")
    chosen = {}
    # avec le barème, le découvert n'est plus interdit : il se paie en points (critères découvert et indépendance
    # financière, dans chaque scénario de ventes) ; en marge, l'ancienne règle « sans découvert » reste
    feasible = lambda r: True if bareme is not None else sum(r.get("dette_ct_nouvelle") or [0]) <= 0
    # prix de transfert : recherche coordonnée sur la grille 1,00 à 2,00
    tp = [k for k in o.state if k.startswith("transfer.")]
    best_net, best_pts = base["net"], 0.0
    log("\n### Prix de transfert\n\n| Champ | Valeur | Résultat net, M USD | Écart | Résultat USA / Chine / Europe | Barème, points |\n|---|---|---|---|---|---|")
    for k in tp:
        for v in (1.0, 1.1, 1.25, 1.5, 1.75, 2.0):
            r = o.evaluate({**dec, **chosen, k: v})
            if "refus" in r:
                continue
            p = pts(r)
            log(f"| {k} | {v:.2f} | {M(r['net']):.0f} | {M(r['net'] - base['net']):+.0f} | " + " / ".join(f"{M(r[z]):.0f}" if r.get(z) is not None else "?" for z in ZN.values())
                + f" | {'' if p is None else format(p, '+.2f')} |")
            if feasible(r) and gain(r, best_net, best_pts):
                best_net, chosen[k] = r["net"], v
                best_pts = p if p is not None else best_pts
    # dette à long terme : garder, rembourser la moitié, tout rembourser
    if "long.debt" in o.state:
        t = __import__("cesim.client", fromlist=["page_text"]).page_text(o.s, "finance")[0]
        import re
        m = re.search(r"Dette à long terme tour précédent ([\d ]+)", t)
        debt = float(m.group(1).replace(" ", "")) if m else 0.0
        base = {k: v for k, v in base.items()}
        log(f"\n### Dette à long terme (encours {debt / 1e6:.1f} Md USD)\n\n| Variation, k USD | Résultat net, M USD | Dette court terme nouvelle | Trésorerie de fin | Barème, points |\n|---|---|---|---|---|")
        best = (best_net, None)
        for v in sorted({0.0, -round(debt * 0.5), -debt, float(o.base["long.debt"])}):
            r = o.evaluate({**dec, **chosen, "long.debt": int(v)})
            p = pts(r)
            log(f"| {int(v)} | {M(r['net']):.0f} | {r.get('dette_ct_nouvelle')} | {r.get('tresorerie_fin')} | {'' if p is None else format(p, '+.2f')} |")
            if feasible(r) and ((p - best_pts) > 0.2 if p is not None else r["net"] > best[0] + 1000):
                best = (r["net"], int(v))
                best_pts = p if p is not None else best_pts
        if best[1] is not None:
            chosen["long.debt"], best_net = best[1], best[0]
    # transferts internes : pas de 2 Md autour de l'existant
    for k in [x for x in ("cash.us.to.asia", "cash.us.to.eu") if x in o.state]:
        v0 = float(o.base[k])
        log(f"\n### Transfert interne {k}\n\n| Montant, k USD | Résultat net, M USD | Dette court terme nouvelle | Trésorerie USA / Chine / Europe, M USD | Barème, points |\n|---|---|---|---|---|")
        best = (best_net, None)
        for v in (v0 - 4e6, v0 - 2e6, v0, v0 + 2e6, v0 + 4e6):
            r = o.evaluate({**dec, **chosen, k: int(v)})
            p = pts(r)
            tr = (r.get("previsionnel") or {}).get("tresorerie") or {}
            log(f"| {int(v)} | {M(r['net']):.0f} | {r.get('dette_ct_nouvelle')} | " + " / ".join(f"{M(tr[z]):.0f}" if tr.get(z) is not None else "?" for z in ZN) + f" | {'' if p is None else format(p, '+.2f')} |")
            if feasible(r) and ((p - best_pts) > 0.2 if p is not None else r["net"] > best[0] + 1000):
                best = (r["net"], int(v))
                best_pts = p if p is not None else best_pts
        if best[1] is not None:
            chosen[k], best_net = best[1], best[0]
    log(f"\nChoix de l'étape E : {chosen or 'rien à changer'} ; résultat net {M(best_net):.0f} M USD.")
    log("\nDividendes : non cherchés (aucune équipe n'en a versé, effet sur le cours inconnu) ; laissés à 0.")
    return chosen


# ====================================================================== étapes A et B : simulateur local
def step_AB(tour, log, n_per=25):
    import strategy as S
    from model import market, sim
    from model.panel2 import build
    d = build()
    d = d[d["round"] < tour + 1]
    params = sim.fit_params(d)
    inputs = json.load(open(ROOT / "data" / f"tour_{tour}_inputs.json"))
    B = inputs.get("behaviours", ["statu quo", "tendance", "guerre des prix", "montée en gamme", "meilleure réponse", "mélange"])
    log("\n## Étape A — offre : entrée sur une autre technologie (ordre de grandeur)\n")
    for tech in ("Électrique", "Hydrogène"):
        try:
            e = market.entry_estimate(d, inputs["growth"], tech, feat=3)
            log(f"\n{tech}, 3 équipements, concurrents inchangés :\n\n| Zone | Couverture | Vendeurs avec nous | Cellule, k unités | Notre demande à part égale |\n|---|---|---|---|---|")
            for _, r in e.iterrows():
                log(f"| {r.zone} | {r.couverture * 100:.0f} % | {r.vendeurs_avec_nous} | {r.cellule_avec_nous:.0f} | {r.notre_demande_part_egale:.0f} |")
        except Exception as ex:
            log(f"\n{tech} : estimation impossible ({ex}).")
    log("\n## Étape B — marketing : frontière gain / éloignement\n\nPrix, équipements et publicité de nos produits cherchés ensemble, dans des zones de confiance de plus en plus larges "
        "autour des décisions du tour précédent. « Bornes larges » = optimum du modèle, à ne pas jouer tel quel.\n")
    sc = S.Scenarios(d, params, inputs, B, n_per=n_per, seed=3)
    F, xs = S.frontier(sc, inputs, B, verbose=False)
    log("| Zone de confiance | Gain moyen, M USD | P10 | Pire comportement | Publicité totale | Équipements |\n|---|---|---|---|---|---|")
    for z, r in F.iterrows():
        log(f"| {z} | {r.moyenne:.0f} | {r.P10:.0f} | {r.pire_comportement:.0f} | {r.pub_totale:.0f} | {r.equipements} |")
    log("\n| Produit | " + " | ".join(xs) + " |\n|" + "---|" * (len(xs) + 1))
    for i, c in enumerate(sc.cells):
        log(f"| {c} | " + " | ".join(f"{int(x[i, 0])} / {int(x[i, 1])} / {int(x[i, 2])}" for x in xs.values()) + " |")
    gm = float((np.maximum(sc.current[:, 0] * sc.fx - sc.mc - sc.fc * sc.current[:, 1], 0) * sc.q0 / 1000).sum())
    return dict(frontier=F, strategies={k: v.tolist() for k, v in xs.items()}, gross_margin=gm, cells=list(sc.cells))


def make_bareme(tour, n_per=10, prev=None):
    """Barème de l'instructeur sur notre gamme du tour (celle de `lineup` dans les entrées, sinon celle du dernier tour).
    prev : prévisionnel de la plateforme pour la zone personnelle (oracle.previsionnel), qui cale le bilan et les
    comptes de zone ; il est aussi écrit dans data/previsionnel_tourN.json pour les recherches sans plateforme."""
    import objectif as OB
    import strategy as S
    import tour_final as TF
    from model import sim
    from model.panel2 import build
    d = build()
    d = d[d["round"] < tour + 1]
    inputs = json.load(open(ROOT / "data" / f"tour_{tour}_inputs.json"))
    sc, _, _ = TF.scenarios(d, sim.fit_params(d), inputs, n_per)
    B = OB.Bareme(sc, tour)
    if prev and prev.get("zones"):
        json.dump(prev, open(ROOT / "data" / f"previsionnel_tour{tour}.json", "w"), indent=1, ensure_ascii=False)
        B.plateforme(prev)
    return B, S.tidy(sc.current, sc.cells)


# ====================================================================== programme principal
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tour", type=int, required=True)
    ap.add_argument("--etapes", nargs="*", default=["A", "B", "D", "E"])
    ap.add_argument("--sec", action="store_true", help="sans la plateforme")
    ap.add_argument("--vpp", type=float, default=None, help="valeur d'un point de demande, M USD (défaut : marge brute simulée / 100)")
    ap.add_argument("--objectif", choices=["points", "marge"], default="points", help="points du barème de l'instructeur (défaut) ou résultat en M USD (ancienne règle)")
    a = ap.parse_args()
    steps = [s for s in a.etapes if not (a.sec and s in "DE")]
    buf = []

    def log(x):
        print(x, flush=True)
        buf.append(x)

    t0 = time.time()
    txt, unknown = lever_report(a.tour)
    log(f"# Tour {a.tour} — recherche sur l'ensemble des leviers\n\n## Étape 0 — couverture des leviers\n\n```\n{txt}\n```")
    if unknown:
        log("\n**Des champs ne sont pas classés : les traiter dans leviers.py avant de se fier à cette recherche.**")
    out, vpp = {}, a.vpp
    if "A" in steps or "B" in steps:
        out["AB"] = step_AB(a.tour, log)
        vpp = vpp or out["AB"]["gross_margin"] / 100
    if "D" in steps or "E" in steps:
        from oracle import Oracle
        with Oracle(a.tour) as o:
            b = o.evaluate({})
            if not b.get("previsionnel"):                     # état repris d'un ancien cache : comptes par entité et bilan à relire
                from oracle import previsionnel
                b["previsionnel"] = previsionnel(o.s)
            vpp = vpp or (M(b["ebitda"]) + sum(float(v) for k, v in o.base.items() if k.endswith(".adv")) / 1000) / 100
            dec = {}
            if "D" in steps:
                bareme, x0 = make_bareme(a.tour, prev=b["previsionnel"]) if a.objectif == "points" else (None, None)
                if bareme is not None:
                    log(f"\nBilan de référence ({bareme.fin['source'] if bareme.fin else 'inconnu'}) : trésorerie USA / Chine / Europe "
                        + (" / ".join(f"{v:.0f}" for v in bareme.fin["treso"]) if bareme.fin else "?") + f" M USD ; tours suivants comptés : {bareme.horizon} (poids {bareme.w_suite:.2f}).")
                    log(f"\nObjectif : points du barème de l'instructeur (model/points.py, objectif.py). Repères : 1 Md USD de coût = "
                        f"{bareme.levier(x0, d_net=-1000).sum():+.1f} point ; +1 % de demande = {bareme.levier(x0, d_demande=1).sum():+.2f} point.")
                dec, rows = step_D(o, vpp, log, bareme, x0)
                r = o.evaluate(dec)
                log(f"\n### Vérification du cumul des choix de l'étape D\n\nRésultat net {M(b['net']):.0f} -> {M(r['net']):.0f} M USD ; score ESG {r.get('score_esg')} ; "
                    f"fournisseurs requis {r.get('fournisseurs_requis')}, actifs {r.get('fournisseurs_actifs')} ; dette à court terme nouvelle {r.get('dette_ct_nouvelle')}.")
                out["D"] = dec
            if "E" in steps:
                if a.objectif == "points" and "D" not in steps:
                    bareme, x0 = make_bareme(a.tour, prev=b["previsionnel"])
                elif a.objectif != "points":
                    bareme, x0 = None, None
                out["E"] = step_E(o, dec, log, bareme, x0)
            out["appels_plateforme"] = o.calls
        log(f"\nZone personnelle restaurée. {out['appels_plateforme']} évaluations sur la plateforme.")
    log(f"\nDurée : {time.time() - t0:.0f} s.")
    (OUT / f"tour{a.tour}_recherche.md").write_text("\n".join(buf))
    json.dump({k: (v if k != "AB" else dict(strategies=v["strategies"], gross_margin=v["gross_margin"])) for k, v in out.items()},
              open(OUT / f"tour{a.tour}_recherche.json", "w"), indent=1, ensure_ascii=False, default=str)


if __name__ == "__main__":
    main()
