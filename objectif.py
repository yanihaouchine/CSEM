"""Objectif de l'optimiseur : l'espérance de nos points au barème de l'instructeur (model/points.py).

    sc = strategy.Scenarios(...)                 # scénarios de demande, inchangés
    B = objectif.Bareme(sc, tour)                # ajoute les 11 concurrents sur chaque critère
    B.score(x)                                   # espérance du total de points pour les décisions marketing x
    B.detail(x)                                  # points attendus par critère

Ce que le marketing déplace (calculé pour chaque décision testée, dans chaque scénario) :
  parts de marché par zone   nos ventes simulées / ventes totales de la zone (la part publiée se calcule sur les ventes) ;
                             la part de chaque concurrent est sa part du dernier tour (+ bruit), réduite au prorata de ce que nous prenons
  marges opérationnelles     (marge de contribution simulée de la zone - charges fixes de la zone) / chiffre d'affaires total de la zone ;
                             charges fixes et cessions internes reprises de notre dernier rapport (ou de `bareme.zones` dans les entrées)
  coûts unitaires moyens     coût de nos produits de la zone (hors équipements + équipements), pondéré par les ventes simulées
  ROE, rentabilité de l'action, création de valeur    par le résultat net : référence + (1 - impôt) x écart de marge de contribution
Ce que le bilan déplace (`Bareme.bilan`) : découvert et indépendance financière, par scénario. La trésorerie de
  chaque entité est celle du prévisionnel de la plateforme (`Bareme.plateforme`, ou `bareme.finance`), à défaut celle du
  dernier bilan ; un scénario où les ventes d'une zone manquent la vide, et ce qui passe sous zéro est du découvert.
  indépendance = fonds propres / (fonds propres + dette à long terme + découvert).
Productivité des ingénieurs : dernier coefficient + effet des priorités de formation (`productivite`, loi ajustée sur les
  12 équipes ; ni le salaire ni le budget de formation n'ont d'effet mesurable).
Tours suivants (`Bareme.suite`) : le classement général cumule les points de tous les tours. Une décision est donc notée
  aussi sur l'état qu'elle laisse : part de marché (inertie du moteur), fonds propres (ROE suivant), cours (rentabilité
  de l'action suivante), score ESG (certification ouverte au tour suivant), effets définitifs payés une seule fois.
Les autres critères (ESG, fournisseurs, certification, stocks, demande insatisfaite) ne dépendent pas du marketing : ils
entrent comme constantes, à notre valeur du dernier tour ou à celle de `bareme.nous`.
Concurrents : valeur du dernier tour + bruit mesuré sur l'historique (points.concurrents). Erreur de cette prévision en
rejeu aveugle : environ 1,5 point par critère (python3 -m model.points).

Entrées optionnelles (bloc `bareme` de data/tour_N_inputs.json) :
  "nous": {"certification": 2, "S": 3.5}      valeurs attendues de nos critères hors marketing
  "net_ref": 15517                             résultat net (M USD) du prévisionnel de la plateforme pour les décisions reconduites
  "zones": {"USA": {"fixes": 1336, "internes": 777}}   charges fixes et cessions internes de la zone, M USD
  "poids_marge": 0.1                           points par Md USD de marge, pour départager deux décisions de même espérance
  "finance": {"tresorerie": {"USA": 35735, ...}, "ventes": {...}, "dette_lt": 0, "decouvert": 0, "fp": 110462, "net": 27871}
                                               état du prévisionnel de la plateforme, M USD (sinon `Bareme.plateforme`)
  "horizon": 2                                 nombre de tours joués après celui-ci qui comptent (défaut : 10 - tour)
  "poids_suite": 0.0, "persistance": 0.5       poids d'un point d'un tour suivant (défaut 0 : la suite ne passe pas la
                                               contre-épreuve, voir `Bareme.suite`) ; part de l'effet qui survit d'un tour à l'autre
  "score_sd": 0.08                             incertitude sur notre score ESG cumulé (seuils de certification)
"""
import numpy as np
import pandas as pd

from model import market, points as P
from model.report import table

TAX = 0.215
TAX_ZONE = {"USA": 0.20, "Chine": 0.24, "Europe": 0.21}
REG = ["USA", "Chine", "Europe"]
MARKETING = [f"{k} {z}" for k in ("part", "marge", "coût unitaire") for z in REG] + ["ROE", "rentabilité de l'action", "création de valeur"]
FINANCE = ["découvert", "indépendance financière"]            # déplacés par le bilan (trésorerie de chaque entité, dette, résultat)
CERT_SEUILS = (2.75, 3.25, 4.0)                               # score ESG cumulé requis : Bronze, Argent, Or (2 points par niveau)


class Bareme:
    def __init__(self, sc, tour, seed=0, team=P.US):
        self.sc, self.team = sc, team
        opt = sc.inputs.get("bareme", {})
        self.w = float(opt.get("poids_marge", 0.1))
        self.tour = tour
        self.horizon = int(opt.get("horizon", max(0, 10 - tour)))            # tours joués après celui-ci
        self.rho = float(opt.get("persistance", 0.5))                         # part d'un effet d'état qui survit d'un tour à l'autre
        self.w1 = float(opt.get("poids_suite", 0.0)) if self.horizon >= 1 else 0.0          # poids du tour suivant
        self.w_suite = float(opt.get("poids_suite", 0.0)) * sum(self.rho ** n for n in range(self.horizon))   # tous les tours suivants
        self.score_sd = float(opt.get("score_sd", 0.08))
        idx = tour                                              # indice des derniers résultats publiés (round_k = tour k - 1)
        V = P.valeurs(idx)
        self.V = V = V[[c for c in V.columns]]
        self.crit = [c for c in V.index if not V.loc[c].isna().all()]
        self.teams = list(V.columns)
        j = self.j = self.teams.index(team)
        n = len(sc.labels)
        rng = np.random.default_rng(seed)
        X = P.concurrents(V.loc[self.crit], P.dispersion(), n, rng)
        self.riv = {c: np.delete(X[:, i, :], j, axis=1) for i, c in enumerate(self.crit)}      # (scénario, 11 concurrents)
        self.X = X                                               # (scénario, critère, 12 équipes), pour l'écart au meilleur concurrent
        self.last = V[team].to_dict()
        self.nous = {**{c: self.last[c] for c in self.crit}, **opt.get("nous", {})}
        if "productivité" in self.nous and "productivité" not in opt.get("nous", {}):
            from model.esg import TRN                            # priorités de formation saisies pour ce tour (`our_decisions`)
            od = sc.inputs.get("our_decisions") or {}
            if any(k in od for k in TRN):
                prec = formation_precedente(team)
                self.nous["productivité"] = self.last["productivité"] + productivite([od.get(k, p) for k, p in zip(TRN, prec)], prec)[0]
        # --- nos comptes du dernier tour, par zone
        cells = sc.cells
        self.zi = np.array([REG.index(c.split("|")[0]) for c in cells])
        us_last = sc.base[(sc.base["team"] == team)]
        g = lambda path: float(table(path, [idx]).loc[idx, team])
        self.fix, self.internal = np.zeros(3), np.zeros(3)
        from model.panel2 import build
        d = build()                                             # tout l'historique : le panel estime l'impact ESG des tours où il n'est plus publié
        t = d[(d["round"] == idx) & (d["team"] == team)]
        for k, z in enumerate(REG):
            ca = g(f"Compte de résultat, M USD, {z} > Chiffre d'affaires > " + ("Chiffre d'affaires" if z == "Europe" else "Chiffre d'affaires total"))
            ebit = g(f"Compte de résultat, M USD, {z} > Coûts > RÉSULTAT OPÉRATIONNEL (EBIT)")
            tz = t[t["region"] == z]
            rev, contrib = float(tz["rev"].sum()), float(tz["rev"].sum() - tz["cogs"].sum() - tz["adv"].sum())
            zo = opt.get("zones", {}).get(z, {})
            self.fix[k], self.internal[k] = zo.get("fixes", contrib - ebit), zo.get("internes", ca - rev)
        self.net_last = g("Bilan, M USD, Global > Capitaux propres > Résultat net annuel")
        self.fp_last = g("Bilan, M USD, Global > Capitaux propres > Total des capitaux propres")
        self.cv_last = self.last["création de valeur"]
        R = "Ratios et indicateurs financiers > Ratios > "
        self.cours, self.actions = g(R + "Cours de l'action à la fin du tour, USD"), g(R + "Actions sur le marché à la fin du tour, millions d'actions")
        self.contrib_last = float(t["rev"].sum() - t["cogs"].sum() - t["adv"].sum())
        self.cogs_last = float(t["cogs"].sum())
        self.net_ref = opt.get("net_ref")                        # résultat net du prévisionnel pour les décisions reconduites
        # --- bilan : trésorerie de fin de tour de chaque entité et dettes, d'après le prévisionnel de la plateforme
        # (bloc `bareme.finance`, sinon data/previsionnel_tourN.json écrit par l'oracle, sinon `Bareme.plateforme`).
        # Sans lui la trésorerie de fin de tour est inconnue (elle dépend des transferts internes) : découvert et
        # indépendance financière restent alors à leur valeur du dernier tour, et `detail` le signale.
        self.fin = None
        self._nous_saisis = set(opt.get("nous", {}))
        from cesim.client import ROOT
        fichier = ROOT / "data" / f"previsionnel_tour{tour}.json"
        if not opt.get("finance") and fichier.exists():
            import json
            prev = json.load(open(fichier))
            self.fin = self._fin(prev)
            if opt.get("zones") is None:                         # cessions internes et charges fixes du tour en cours
                for i, z in enumerate(REG):
                    if z in prev.get("zones", {}):
                        self.internal[i] = (prev["zones"][z].get("internes") or 0.0) / 1000.0
                        if prev["zones"][z].get("fixes") is not None:
                            self.fix[i] = prev["zones"][z]["fixes"] / 1000.0
        if opt.get("finance"):
            f = opt["finance"]
            self.fin = dict(treso=np.array([float(f["tresorerie"][z]) for z in REG]), ventes=(np.array([float(f["ventes"][z]) for z in REG]) if f.get("ventes") else None),
                            dette_lt=float(f.get("dette_lt", 0.0)), decouvert=float(f.get("decouvert", 0.0)),
                            fp0=(float(f["fp"]) - float(f.get("net", 0.0)) if "fp" in f else self.fp_last), source="entrées du tour")
        from model.cours import ols, panel
        T = panel()
        self.fit = ols(T[T["emission"] == 0], "d_cours", ["bpa"])["coef"]
        # --- ventes totales de chaque zone, par scénario : cellules où nous sommes (tirées) + autres cellules (prévision centrale)
        mk0 = market.forecast(sc.base, sc.inputs["growth"], method=sc.inputs.get("market_method", "mixte"))
        dl = d[d["round"] == idx] if "round" in d else d
        fill = {z: float(dl[dl["region"] == z]["sales"].sum() / max(dl[dl["region"] == z]["demand"].sum(), 1e-9)) for z in REG}
        self.total = np.zeros((n, 3))
        for k, z in enumerate(REG):
            mine = self.zi == k
            other = sum(v for c, v in mk0.items() if c.startswith(z + "|") and c not in cells)
            self.total[:, k] = (sc.z["M"][:, mine].sum(1) + other) * fill[z]
        self.share_last = np.array([self.last[f"part {z}"] for z in REG])
        self._dem_ref = sc._demand(np.asarray(sc.current, float))
        self._refresh()

    def _refresh(self):
        """Recalcule la référence (décisions reconduites), la liste des critères déplacés et les points constants
        après un changement des comptes de zone ou du bilan."""
        if hasattr(self, "ref"):
            del self.ref
        self._suite_ref = None
        ref = self.values(np.asarray(self.sc.current, float))    # nos critères avec les décisions reconduites
        ref.update(self.finance(ref))
        self.ref = ref
        # critères déplacés : ceux du marketing, et ceux du bilan quand il est connu et non saisi à la main
        self.dyn = [c for c in MARKETING + FINANCE if c in self.crit and not (c in FINANCE and (self.fin is None or c in self._nous_saisis))]
        n = len(self.sc.labels)
        self.const = pd.Series({c: self._pts(c, np.full(n, float(self.nous[c]))).mean() for c in self.crit if c not in self.dyn})
        self.const_sum = float(self.const.sum())

    def plateforme(self, prev, zones=True):
        """Cale le bilan (et les comptes de zone) sur le prévisionnel de la plateforme pour les décisions de la zone
        personnelle : prev = oracle.previsionnel(s) ou la clé « previsionnel » d'un état de l'oracle, en k USD.
        Trésorerie de chaque entité, ventes prévues, dettes, fonds propres hors résultat du tour ; avec zones=True,
        cessions internes et charges fixes du tour en cours (R&D, garantie, administration, amortissement), qui changent
        fort d'un tour à l'autre (cessions de la Chine : 21,0 Md USD au tour 7, 5,2 au tour 8)."""
        if not prev or not prev.get("zones"):
            return self
        Z, k = prev["zones"], 1000.0
        self.fin = self._fin(prev)
        if zones:
            for i, z in enumerate(REG):
                if z in Z:
                    self.internal[i] = (Z[z].get("internes") or 0.0) / k
                    if Z[z].get("fixes") is not None:
                        self.fix[i] = Z[z]["fixes"] / k
        if self.net_ref is None:
            self.net_ref = sum(Z[z]["net"] for z in REG if z in Z) / k
        self._refresh()
        return self

    def _fin(self, prev):
        """État du bilan (M USD) tiré d'un prévisionnel de la plateforme (k USD)."""
        Z, k = prev["zones"], 1000.0
        return dict(treso=np.array([(prev["tresorerie"].get(z) or 0.0) for z in REG]) / k, ventes=np.array([(Z.get(z, {}).get("ventes") or 0.0) for z in REG]) / k,
                    dette_lt=(prev.get("dette_lt") or 0.0) / k, decouvert=(prev.get("decouvert") or 0.0) / k,
                    fp0=((prev.get("fp") or 0.0) - sum(Z[z]["net"] for z in REG if z in Z)) / k if prev.get("fp") else self.fp_last, source="prévisionnel de la plateforme")

    # ------------------------------------------------------------------ nos critères pour une décision
    def values(self, x, dem=1.0, qs=None):
        """Nos critères par scénario pour les décisions x. dem : multiplicateur de la demande (scalaire ou tableau
        scénario x cellule) ; qs : (demande, ventes) déjà calculées pour x, pour éviter de rappeler le moteur."""
        sc = self.sc
        q, sales = sc._demand(x) if qs is None else qs
        q, sales = q * dem, sales * dem
        unit_cost = sc.mc + sc.fc * x[:, 1]
        rev = x[:, 0] * sc.fx * sales / 1000.0                   # M USD, (scénario, cellule)
        cogs = unit_cost[None, :] * sales / 1000.0
        out, contrib_tot = {}, 0.0
        for k, z in enumerate(REG):
            m = self.zi == k
            if not m.any():
                continue
            s, r, c = sales[:, m].sum(1), rev[:, m].sum(1), cogs[:, m].sum(1)
            contrib = r - c - np.maximum(x[m, 2], 0).sum()
            contrib_tot = contrib_tot + contrib
            out[f"part {z}"] = s / self.total[:, k] * 100
            out[f"marge {z}"] = (contrib - self.fix[k]) / (r + self.internal[k]) * 100
            out[f"coût unitaire {z}"] = c / np.maximum(s, 1e-9) * 1000
        out["_contrib"], out["_cogs"] = contrib_tot, cogs.sum(1)
        out["_rev"] = [rev[:, self.zi == k].sum(1) for k in range(3)]
        out["_cost"] = [cogs[:, self.zi == k].sum(1) + np.maximum(x[self.zi == k, 2], 0).sum() for k in range(3)]   # coût des ventes + publicité
        out["_q"], out["_sales"] = q, sales
        return out

    def bilan(self, v, fin=None):
        """Découvert et indépendance financière par scénario. La trésorerie de fin de tour de chaque entité est celle du
        bilan de référence (`fin`), corrigée de l'écart entre nos ventes simulées et les ventes que ce bilan suppose
        (la production est déjà payée : une vente manquée retire son chiffre d'affaires, net d'impôt) et du surcoût des
        décisions testées. Ce qui passe sous zéro dans une entité est une dette à court terme imprévue."""
        fin = fin or self.fin
        if fin is None:
            return {}
        ref = getattr(self, "ref", v)
        tz = np.array([TAX_ZONE[z] for z in REG])
        rev, cost = np.column_stack(v["_rev"]), np.column_stack(v["_cost"])
        ventes = fin["ventes"] if fin.get("ventes") is not None else np.column_stack(ref["_rev"]).mean(0)
        d_cost = cost.mean(0) - np.column_stack(ref["_cost"]).mean(0)
        cash = fin["treso"][None, :] + (1 - tz)[None, :] * (rev - ventes[None, :] - d_cost[None, :])
        dec = fin["decouvert"] + np.maximum(-cash, 0.0).sum(1)
        fp = fin["fp0"] + v["_net"]
        return {"découvert": dec, "indépendance financière": fp / np.maximum(fp + fin["dette_lt"] + dec, 1e-9) * 100, "_fp": fp}

    def finance(self, v):
        """ROE, rentabilité de l'action, création de valeur à partir de la marge de contribution simulée."""
        ref = getattr(self, "ref", v)
        net0 = self.net_ref if self.net_ref is not None else self.net_last + (1 - TAX) * (ref["_contrib"].mean() - self.contrib_last)
        net = net0 + (1 - TAX) * (v["_contrib"] - ref["_contrib"].mean())
        bpa = net / self.actions
        return {"ROE": net / (self.fp_last + net / 2) * 100,
                "rentabilité de l'action": (self.fit["cst"] + self.fit["bpa"] * bpa) / self.cours * 100,
                "création de valeur": self.cv_last + (net - self.net_last) / (1 - TAX) + (v["_cogs"] - self.cogs_last),
                "_net": net}

    def _pts(self, c, ours, riv=None):
        if c == "certification":
            return np.asarray(ours, float)
        s = P.SENS[c]
        r = self.riv[c] if riv is None else riv
        return 1.0 + (r * s < np.asarray(ours)[:, None] * s - 1e-9).sum(1)

    def per_scenario(self, x):
        """Points par scénario et par critère déplacé par le marketing : dict critère -> tableau (scénario,)."""
        v = self.values(np.asarray(x, float))
        v.update(self.finance(v))
        v.update(self.bilan(v))
        return self._points(v), v

    def _points(self, v, crit=None):
        """Points par scénario des critères déplacés (marketing et bilan) pour des valeurs v."""
        out = {}
        for c in (crit or self.dyn):
            if c not in v or c not in self.riv:
                continue
            riv = self.riv[c]
            if c.startswith("part "):                             # ce que nous prenons est retiré aux autres au prorata
                k = REG.index(c.split(" ", 1)[1])
                riv = riv * ((100 - v[c]) / max(100 - self.share_last[k], 1e-9))[:, None]
            out[c] = self._pts(c, v[c], riv)
        return out

    # ------------------------------------------------------------------ tours suivants : l'état laissé
    def _suivant(self, v):
        """Points du tour suivant (critères du marketing) si les décisions de référence y sont rejouées dans l'état que
        laisse v : demande de chaque produit multipliée par (demande du tour / demande de référence)^h (inertie du
        moteur, moins la pénalité de rupture), fonds propres et cours de fin de tour."""
        sc, ref = self.sc, self.ref
        q0, s0 = self._dem_ref
        m = (np.maximum(v["_q"], 1e-9) / np.maximum(ref["_q"], 1e-9)) ** sc.z["h"]
        m = m * np.exp(-sc.z["u"] * ((1 - v["_sales"] / np.maximum(v["_q"], 1e-9)) - (1 - ref["_sales"] / np.maximum(ref["_q"], 1e-9))))
        w = self.values(np.asarray(sc.current, float), dem=m, qs=(q0, s0))
        net0 = np.mean(ref["_net"])
        net1 = net0 + (1 - TAX) * (w["_contrib"] - ref["_contrib"].mean())
        fp, cours = self.fp_last + v["_net"], self.cours + self.fit["cst"] + self.fit["bpa"] * v["_net"] / self.actions
        w["ROE"] = net1 / (fp + net1 / 2) * 100
        w["rentabilité de l'action"] = (self.fit["cst"] + self.fit["bpa"] * net1 / self.actions) / np.maximum(cours, 1e-9) * 100
        w["création de valeur"] = self.cv_last + (net1 - self.net_last) / (1 - TAX) + (w["_cogs"] - self.cogs_last)
        return {c: p.mean() for c, p in self._points(w, MARKETING).items()}

    def suite(self, v):
        """Points gagnés ou perdus au tour suivant du seul fait de l'état laissé, par critère, en écart à l'état que
        laissent les décisions reconduites (zéro pour celles-ci). À multiplier par `w_suite` (tours restants).
        ÉTEINTE PAR DÉFAUT (`bareme.poids_suite` = 0). Contre-épreuve (python3 objectif.py --tour N --suite),
        points réels du tour + du tour suivant, point ±6 % : 327 avec la suite contre 332 sans au tour 5, 322 contre 334
        au tour 6. La suite pousse à céder de la marge pour de la part de marché, et le tour suivant ne le rend pas."""
        if self.w_suite <= 0:
            return {}
        if self._suite_ref is None:
            self._suite_ref = self._suivant(self.ref)
        s = self._suivant(v)
        return {c: s[c] - self._suite_ref[c] for c in s}

    def cert_suivante(self, scores=None):
        """Espérance des points de certification du tour suivant : le score ESG cumulé qui ouvre un niveau est la
        moyenne des scores E, S, G de ce tour (seuils 2,75 / 3,25 / 4,00 ; 2 points par niveau)."""
        from math import erf
        sc = {p: float((scores or {}).get(p, self.nous[p])) for p in ("E", "S", "G") if p in self.nous}
        if len(sc) < 3:
            return 0.0
        m = sum(sc.values()) / 3
        return float(sum(2 * 0.5 * (1 + erf((m - s) / (self.score_sd * 2 ** 0.5))) for s in CERT_SEUILS))

    def detail(self, x):
        """Points attendus par critère (tous les critères) et valeurs moyennes de nos critères."""
        pts, v = self.per_scenario(x)
        s = pd.concat([pd.Series({c: p.mean() for c, p in pts.items()}), self.const])
        vals = pd.Series({**{c: float(self.nous[c]) for c in self.const.index}, **{c: float(np.mean(v[c])) for c in pts}})
        D = pd.DataFrame(dict(valeur=vals, points=s)).reindex([c for c in self.crit if c in s.index])
        if self.w_suite > 0:                                   # hors total du tour : ce que l'état laissé vaut aux tours suivants
            D.loc["suite (tours suivants)"] = [np.nan, self.w_suite * sum(self.suite(v).values())]
        return D

    def score(self, x):
        """Espérance du total de points du tour + points des tours suivants dus à l'état laissé (`suite`)
        + poids_marge x marge (Md USD) pour départager."""
        pts, v = self.per_scenario(x)
        s = self.w_suite * sum(self.suite(v).values()) if self.w_suite > 0 else 0.0
        return float(sum(p.mean() for p in pts.values()) + self.const_sum + s + self.w * (v["_contrib"].mean() / 1000.0))

    def levier(self, x, d_net=0.0, d_demande=0.0, d_impacts=None, valeurs=None, d_net_zone=None, d_marge_zone=None, finance=None, durable=False):
        """Variation de nos points attendus, par critère, pour un levier hors marketing appliqué aux décisions x :
        d_net        variation du résultat net lue sur la plateforme, M USD (coût du levier) -> ROE, action, création de valeur, marges ;
        d_demande    variation de notre demande, en % -> parts de marché, marges, résultat ;
        d_impacts    {composante ESG: variation d'impact en points de %} -> scores E, S, G (loi linéaire, voir scores_esg) ;
        valeurs      {critère: nouvelle valeur} pour un effet direct (certification, fournisseurs, productivité) ;
        d_marge_zone {zone: variation de la marge opérationnelle de l'entité, en points de %}, lue sur le prévisionnel
                     (EBIT / chiffre d'affaires total, cessions internes comprises : `marges_plateforme`). C'est la mesure
                     exacte pour un prix de transfert, qui déplace à la fois le résultat et le chiffre d'affaires des entités ;
        d_net_zone   {zone: variation du résultat net de l'entité, M USD} : ancienne mesure (numérateur seul), employée
                     quand le compte de résultat par entité n'a pas été lu ;
        finance      prévisionnel de la plateforme (k USD, oracle.previsionnel) de l'état testé -> découvert et
                     indépendance financière, comparés à ceux du bilan de référence (`Bareme.plateforme`) ;
        durable      effet définitif payé une seule fois (amélioration de processus) : le coût compte pour ce tour, les
                     effets pour ce tour et les suivants (1 + w_suite).
        Lignes ajoutées au détail : « suite » (état laissé : part de marché, fonds propres, cours) et « certification
        (tour suivant) » (niveau ouvert par les scores E, S, G de ce tour)."""
        if durable and self.w_suite > 0:
            cout = self.levier(x, d_net=d_net, d_net_zone=d_net_zone, d_marge_zone=d_marge_zone, finance=finance) if (d_net or d_net_zone or d_marge_zone or finance) else pd.Series(dtype=float)
            effet = self.levier(x, d_demande=d_demande, d_impacts=d_impacts, valeurs=valeurs)
            return cout.add((1 + self.w_suite) * effet.drop("suite", errors="ignore"), fill_value=0.0).add(effet.reindex(["suite"]).dropna(), fill_value=0.0)
        x = np.asarray(x, float)
        base, v0 = self.per_scenario(x)
        v = self.values(x, 1 + d_demande / 100.0)
        if d_marge_zone:
            for z in REG:
                if f"marge {z}" in v:
                    v[f"marge {z}"] = v[f"marge {z}"] + d_marge_zone.get(z, 0.0)
            v["_contrib"] = v["_contrib"] + d_net / (1 - TAX)
        elif d_net_zone:
            for k, z in enumerate(REG):
                v[f"marge {z}"] = v[f"marge {z}"] + d_net_zone.get(z, 0.0) / (1 - TAX_ZONE[z]) / self._ca(v, k) * 100
            v["_contrib"] = v["_contrib"] + d_net / (1 - TAX)
        elif d_net:                                           # coût avant impôt, réparti entre zones au prorata du chiffre d'affaires
            w = np.array([self.sc.q0[self.zi == k].sum() for k in range(3)]); w = w / w.sum()
            for k, z in enumerate(REG):
                v[f"marge {z}"] = v[f"marge {z}"] + d_net / (1 - TAX) * w[k] / self._ca(v, k) * 100
            v["_contrib"] = v["_contrib"] + d_net / (1 - TAX)
        v.update(self.finance(v))
        v.update(self.bilan(v, self._fin(finance) if finance else None))
        new = self._points(v)
        out = {c: float(new[c].mean() - base[c].mean()) for c in base if c in new}
        if finance and self.fin is None:                       # bilan de référence inconnu : l'état testé est comparé à notre valeur du dernier tour
            for c in FINANCE:
                if c in self.riv and c in self.const.index and c not in self._nous_saisis:
                    out[c] = float(self._pts(c, v[c]).mean() - self.const[c])
        direct = dict(valeurs or {})
        if d_impacts:
            coef = scores_esg()
            for comp, dv in d_impacts.items():
                if comp in coef:
                    pil, b = coef[comp]
                    direct[pil] = direct.get(pil, float(self.nous[pil])) + b * dv
        n = len(self.sc.labels)
        for c, val in direct.items():
            if c in self.const.index:
                out[c] = float(self._pts(c, np.full(n, float(val))).mean() - self.const[c])
            elif c in base:                                   # valeur imposée à un critère du bilan (découvert, indépendance)
                out[c] = float(self._pts(c, np.full(n, float(val))).mean() - base[c].mean())
        if self.w_suite > 0:
            s0, s1 = self.suite(v0), self.suite(v)
            out["suite"] = float(self.w_suite * (sum(s1.values()) - sum(s0.values())))
        if self.w1 > 0 and any(p in direct for p in ("E", "S", "G")):
            out["certification (tour suivant)"] = float(self.w1 * (self.cert_suivante(direct) - self.cert_suivante()))
        return pd.Series(out)

    def production(self, x, quantiles=(0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.9), stock_fixe=None):
        """Quel quantile de la demande couvrir ? Pour chaque quantile : stocks et demande non servie attendus (k unités),
        leurs points, et les points financiers de l'écart de résultat (marge perdue sur la demande non servie, coût de
        portage du stock : 9 % du coût unitaire + 700 USD par unité). Le stock se revend au tour suivant : il n'est pas
        compté comme perdu. stock_fixe : stock invendable déjà en magasin (défaut : `bareme.stock_fixe` des entrées, sinon 0).
        Renvoie le tableau et le quantile au meilleur total de points."""
        x = np.asarray(x, float)
        sc = self.sc
        q, _ = sc._demand(x)
        fixe = float(sc.inputs.get("bareme", {}).get("stock_fixe", 0.0) if stock_fixe is None else stock_fixe)
        cost = sc.mc + sc.fc * x[:, 1]
        unit = np.maximum(x[:, 0] * sc.fx - cost, 0.0)
        n = len(sc.labels)
        rows = {}
        ref = None
        for ql in quantiles:
            plan = np.quantile(q, ql, axis=0)[None, :]
            unmet, stock = np.maximum(q - plan, 0), np.maximum(plan - q, 0)
            net = -((unit[None, :] * unmet).sum(1) + ((0.09 * cost + 700.0)[None, :] * stock).sum(1)) / 1000.0 * (1 - TAX)   # M USD, par scénario
            p_s = self._pts("stocks", stock.sum(1) + fixe).mean()
            p_u = self._pts("demande insatisfaite", unmet.sum(1)).mean()
            rows[ql] = dict(stock=stock.sum(1).mean(), non_servi=unmet.sum(1).mean(), pts_stock=p_s, pts_non_servi=p_u, net=net.mean())
        T = pd.DataFrame(rows).T
        best_net = T["net"].max()
        T["pts_finance"] = [self.levier(x, d_net=v - best_net).sum() for v in T["net"]]
        T["total"] = T["pts_stock"] + T["pts_non_servi"] + T["pts_finance"]
        return T, float(T["total"].idxmax())

    def ecart(self, x, nous=None, detail=False):
        """Écart entre notre total de points du tour et celui du meilleur concurrent, par scénario. Les points des
        12 équipes sont recalculés : un rang que nous prenons est perdu par l'équipe dépassée.
        nous : {critère: valeur} pour nos critères hors marketing (leviers ESG, certification...)."""
        x = np.asarray(x, float)
        v = self.values(x)
        v.update(self.finance(v))
        v.update({c: val for c, val in self.bilan(v).items() if c in self.dyn})
        X = self.X.copy()
        j = self.j
        for i, c in enumerate(self.crit):
            if c in v and not c.startswith("_"):
                if c.startswith("part "):
                    k = REG.index(c.split(" ", 1)[1])
                    X[:, i, :] = X[:, i, :] * ((100 - v[c]) / max(100 - self.share_last[k], 1e-9))[:, None]
                X[:, i, j] = v[c]
            elif c in self.nous:
                X[:, i, j] = float((nous or {}).get(c, self.nous[c]))
        tot = np.zeros((X.shape[0], X.shape[2]))
        for i, c in enumerate(self.crit):
            if c == "certification":
                tot += np.nan_to_num(X[:, i, :])
            else:
                a = np.nan_to_num(X[:, i, :] * P.SENS[c], nan=-1e18)
                tot += 1.0 + (a[:, None, :] < a[:, :, None] - 1e-9).sum(2)
        others = np.delete(tot, j, axis=1)
        e = tot[:, j] - others.max(1)
        if detail:
            best = pd.Series(others.mean(0), index=[t for t in self.teams if t != self.team]).sort_values(ascending=False)
            return dict(nous=float(tot[:, j].mean()), meilleur=float(others.max(1).mean()), ecart=float(e.mean()), p10=float(np.quantile(e, .1)), p90=float(np.quantile(e, .9)),
                        proba_60=float((e >= 60).mean()), proba_premier=float((e > 0).mean()), concurrents=best.round(1).head(4).to_dict())
        return e

    def _ca(self, v, k):
        """Chiffre d'affaires total moyen de la zone k (ventes + cessions internes), M USD, d'après les valeurs simulées."""
        return float(np.mean(v["_rev"][k]) + self.internal[k])

    def points_total(self, x):
        """Total attendu des points du tour (sans la ligne « suite », qui porte sur les tours suivants)."""
        D = self.detail(x)
        return float(D["points"].drop("suite (tours suivants)", errors="ignore").sum())


def _accepts_rounds(f):
    import inspect
    return "rounds" in inspect.signature(f).parameters


PILIERS = {"E": ["env_unites", "efficacite", "renouvelable", "recyclabilite", "processus"], "S": ["remuneration", "rotation", "formation"], "G": ["politiques", "fournisseurs"]}
_SCORES = {}


def scores_esg(verbose=False):
    """Loi linéaire score du pilier = constante + somme(coef x impact publié de la composante, en %), ajustée sur les 12
    équipes au dernier tour (résidu 0,02 à 0,04 point de score aux tours 5 à 7 des rapports). Renvoie
    {composante: (pilier, coef)} : un point d'impact vaut environ 0,045 en E, 0,10 en G, 0,12 (formation) à 0,2 (rotation) en S."""
    if not _SCORES:
        from model import esg
        df = esg.panel()
        allc = sum(PILIERS.values(), [])
        act = df[df[allc].apply(pd.to_numeric, errors="coerce").abs().sum(1) > 0]     # depuis le tour 7 les impacts publiés sont à zéro
        t = act[act["round"] == act["round"].max()]
        for pil, cols in PILIERS.items():
            X = np.column_stack([pd.to_numeric(t[c], errors="coerce").fillna(0).values for c in cols] + [np.ones(len(t))])
            y = pd.to_numeric(t[f"score_{pil}"], errors="coerce").values
            b = np.linalg.lstsq(X, y, rcond=None)[0]
            e = y - X @ b
            _SCORES.update({c: (pil, float(bi)) for c, bi in zip(cols, b)})
            _SCORES[f"_rmse_{pil}"] = (pil, float(np.sqrt((e ** 2).mean())))
    if verbose:
        print({k: (v[0], round(v[1], 3)) for k, v in _SCORES.items()})
    return _SCORES


TRN_COLS = ["trn_base", "trn_securite", "trn_sante", "trn_discrimination", "trn_ethique"]
PROD_COLS = ["on", "off", "ajout"]
_PROD = {}


def _prod_data():
    """Une ligne par (tour, équipe) depuis l'apparition des priorités de formation : variation du coefficient de
    productivité et transition des priorités (formation de base activée / retirée, autres priorités ajoutées)."""
    if "T" not in _PROD:
        from model import esg
        df = esg.panel()
        C = table("Rapport RH > Ressources humaines > Coefficient de productivité")
        rows = []
        for r in sorted(df["round"].unique()):
            a, b = df[df["round"] == r - 1].set_index("team"), df[df["round"] == r].set_index("team")
            if r not in C.index or r - 1 not in C.index or not len(a):
                continue
            for t in b.index:
                if t not in a.index:
                    continue
                f = lambda d, c: float(pd.to_numeric(d.loc[t, c], errors="coerce") or 0)
                b0, b1 = f(a, "trn_base"), f(b, "trn_base")
                o0, o1 = sum(f(a, c) for c in TRN_COLS[1:]), sum(f(b, c) for c in TRN_COLS[1:])
                rows.append(dict(r=int(r), team=t, p0=C.loc[r - 1, t], p=C.loc[r, t], dp=C.loc[r, t] - C.loc[r - 1, t],
                                 on=float(b1 > b0), off=float(b1 < b0), ajout=max(o1 - o0, 0.0)))
        _PROD["T"] = pd.DataFrame(rows).dropna()
    return _PROD["T"]


def _prod_fit(T):
    X = np.column_stack([np.ones(len(T))] + [T[c].values for c in PROD_COLS])
    return np.linalg.solve(X.T @ X + 1e-4 * np.eye(X.shape[1]), X.T @ T["dp"].values)


def formation_precedente(team=P.US):
    """Nos cinq priorités de formation du dernier tour publié (base, sécurité, santé, non-discrimination, éthique)."""
    from model import esg
    df = esg.panel()
    t = df[(df["round"] == df["round"].max()) & (df["team"] == team)].iloc[0]
    return [bool(float(t[c])) for c in TRN_COLS]


def productivite(formation, precedente=None, team=P.US):
    """Variation attendue du coefficient de productivité des ingénieurs au prochain tour, en écart à la dérive commune
    à toutes les équipes, pour les priorités de formation `formation` (5 booléens : base, sécurité, santé,
    non-discrimination, éthique) après `precedente` (défaut : les nôtres au dernier tour).
    Loi ajustée sur les 12 équipes (tours 2 à 7, 72 observations) : variation = dérive + 0,06 si la formation de base
    est activée, -0,16 si elle est retirée, -0,02 par autre priorité ajoutée. Rejeu en marche avant (`productivite_rejeu`) :
    erreur 0,041 contre 0,045 en reconduisant le coefficient, et 2,1 points de barème contre 2,6. Ni le salaire, ni le
    budget de formation, ni la rotation n'améliorent ce rejeu : ils n'entrent pas dans la loi.
    Renvoie (variation, {coefficients})."""
    prec = formation_precedente(team) if precedente is None else [bool(v) for v in precedente]
    cur = [bool(v) for v in formation]
    b = _prod_fit(_prod_data())
    coef = dict(zip(["derive"] + PROD_COLS, (float(v) for v in b)))
    d = coef["on"] * (cur[0] and not prec[0]) + coef["off"] * (prec[0] and not cur[0]) + coef["ajout"] * max(sum(cur[1:]) - sum(prec[1:]), 0)
    return float(d), coef


def productivite_rejeu(verbose=True):
    """Rejeu en marche avant de la loi de productivité : ajustée sur les tours antérieurs, jugée sur le tour suivant.
    Erreur absolue moyenne sur le coefficient et sur les points du critère (rang parmi les 12), contre la reconduite."""
    T = _prod_data()
    rk = lambda v: np.array([1 + (v < x - 1e-9).sum() for x in v])
    rows = []
    for r in sorted(T["r"].unique())[2:]:
        tr, te = T[T["r"] < r], T[T["r"] == r]
        if tr[PROD_COLS].abs().sum().sum() == 0:
            continue
        b = _prod_fit(tr)
        hat = np.column_stack([np.ones(len(te))] + [te[c].values for c in PROD_COLS]) @ b
        rows.append(dict(tour=int(r) - 1, err_loi=np.abs(te["dp"].values - hat).mean(), err_reconduit=np.abs(te["dp"].values).mean(),
                         pts_loi=np.abs(rk(te["p0"].values + hat) - rk(te["p"].values)).mean(), pts_reconduit=np.abs(rk(te["p0"].values) - rk(te["p"].values)).mean()))
    R = pd.DataFrame(rows)
    if verbose:
        print("=== Productivité des ingénieurs : loi (formation de base activée / retirée, priorités ajoutées) contre reconduite, en marche avant ===")
        print(R.round(4).to_string(index=False))
        print("moyenne :", R.drop(columns="tour").mean().round(4).to_dict(), "| loi sur tout l'historique :", {k: round(v, 3) for k, v in productivite([False] * 5, [False] * 5)[1].items()})
    return R


def marges_plateforme(prev):
    """Marge opérationnelle de chaque entité d'après le prévisionnel de la plateforme (oracle.previsionnel), en % :
    EBIT / chiffre d'affaires total, cessions internes comprises. C'est la formule du critère (écart nul au tour 7)."""
    Z = (prev or {}).get("zones") or {}
    return {z: Z[z]["ebit"] / Z[z]["ca"] * 100 for z in REG if z in Z and Z[z].get("ca") and Z[z].get("ebit") is not None}


# ------------------------------------------------------------------ contre-épreuve sur un tour passé
def contre_epreuve(tour, n_per=12, radii=(0.0, 0.06, 0.15), verbose=True, bareme=None, suivant=False, marge=True):
    """La recherche en points aurait-elle fait mieux que nos décisions réelles au tour `tour` ?
    Recherche faite avec les données d'avant le tour (comme en jeu), puis évaluée avec les décisions RÉELLES des
    concurrents, le moteur calé sur tout l'historique et les valeurs RÉELLES des concurrents sur chaque critère.
    Seuls les critères que le marketing déplace changent ; les autres gardent leurs points réels.
    bareme  : options ajoutées au bloc `bareme` des entrées (ex. {"poids_suite": 0} pour l'objectif du tour seul) ;
    suivant : ajoute `points_suivant`, nos points RÉELS du tour d'après si nous y rejouons nos décisions réelles dans
              l'état laissé (part de marché précédente, fonds propres, cours), les concurrents jouant leurs décisions réelles.
              C'est l'épreuve de `Bareme.suite` : la somme `points + points_suivant` doit monter quand la suite est comptée."""
    import json

    import strategy as S
    import tour_final as TF
    from cesim.client import ROOT
    from model import sim
    from model.panel2 import build
    d_all = build()
    idx = tour + 1
    d = d_all[d_all["round"] < idx]
    inputs = json.load(open(ROOT / "data" / f"tour_{tour}_inputs.json"))
    inputs = {k: v for k, v in inputs.items() if k not in ("lineup", "new_products", "entrants")} if tour < 7 else inputs
    inputs["bareme"] = {**inputs.get("bareme", {}), **(bareme or {})}
    sc, _, _ = TF.scenarios(d, sim.fit_params(d), inputs, n_per)
    B = Bareme(sc, tour)
    cells = sc.cells
    F, xs = S.frontier(sc, sc.inputs, sc.inputs.get("behaviours", TF.BEHAVIOURS), radii=radii, verbose=False, objectif=B.score)
    xm = S.frontier(sc, sc.inputs, sc.inputs.get("behaviours", TF.BEHAVIOURS), radii=radii, verbose=False)[1] if marge else {}

    def monde(i):
        """Lignes réelles du tour d'indice i, prêtes pour sim.simulate_round, et taille réelle de chaque cellule."""
        t = d_all[d_all["round"] == i].copy()
        t["cell"] = t["region"] + "|" + t["tech"]
        t["fx"] = np.where(t["sales"] > 0, t["rev"] / (t["sales"] * t["price"]) * 1000, np.nan)
        t["fx"] = t.groupby("region")["fx"].transform(lambda v: v.fillna(v.median()))
        t["unit_cost"] = np.where(t["sales"] > 0, t["cogs"] / t["sales"] * 1000, 0) - t["feat"] * t["region"].map(sim.FEAT_COST)
        return t, t.groupby("cell")["demand"].sum().to_dict()

    def comptes(s):
        s["sales_s"] = s["sim_demand"] * s["fill"].fillna(1)
        s["rev_s"] = s["price"] * s["fx"] * s["sales_s"] / 1000
        s["cogs_s"] = (s["unit_cost"] + s["feat"] * s["region"].map(sim.FEAT_COST)) * s["sales_s"] / 1000
        return s
    # --- monde réel du tour
    params = sim.fit_params(d_all[d_all["round"] <= idx])
    t, markets = monde(idx)
    us = (t["team"] == P.US).values
    V = P.valeurs(idx)
    real_pts = P.points(V)
    g = lambda path: float(table(path, [idx]).loc[idx, P.US])
    cur = t[us].set_index("cell")
    played = np.column_stack([cur.reindex(cells)[k].values for k in ("price", "feat", "adv")])

    def world(x):
        f = t.copy()
        for c, v in zip(cells, x):
            m = us & (f["cell"] == c).values
            if m.sum() and not np.isnan(v[0]):
                f.loc[m, ["price", "feat", "adv"]] = v
        return comptes(sim.simulate_round(f, params, markets, supply={}))

    def points_reels(V, i, s, s0, d_net_avant=0.0):
        """Points réels du tour d'indice i si le monde simulé s remplace le monde simulé de référence s0 (nos décisions
        réelles). d_net_avant : écart de résultat net déjà acquis au tour précédent (fonds propres et cours de départ)."""
        g = lambda path: float(table(path, [i]).loc[i, P.US])
        o, o0 = s[s["team"] == P.US], s0[s0["team"] == P.US]
        W = V.copy()
        d_contrib = float((o["rev_s"] - o["cogs_s"] - o["adv"]).sum() - (o0["rev_s"] - o0["cogs_s"] - o0["adv"]).sum())
        for z in REG:
            sz, oz, o0z = s[s["region"] == z], o[o["region"] == z], o0[o0["region"] == z]
            W.loc[f"part {z}"] = sz.groupby("team")["sales_s"].sum() / sz["sales_s"].sum() * 100
            ca = g(f"Compte de résultat, M USD, {z} > Chiffre d'affaires > " + ("Chiffre d'affaires" if z == "Europe" else "Chiffre d'affaires total"))
            ebit = g(f"Compte de résultat, M USD, {z} > Coûts > RÉSULTAT OPÉRATIONNEL (EBIT)")
            dz = float((oz["rev_s"] - oz["cogs_s"] - oz["adv"]).sum() - (o0z["rev_s"] - o0z["cogs_s"] - o0z["adv"]).sum())
            W.loc[f"marge {z}", P.US] = (ebit + dz) / (ca + float(oz["rev_s"].sum() - o0z["rev_s"].sum())) * 100
            W.loc[f"coût unitaire {z}", P.US] = V.loc[f"coût unitaire {z}", P.US] + float(oz["cogs_s"].sum() / max(oz["sales_s"].sum(), 1e-9) - o0z["cogs_s"].sum() / max(o0z["sales_s"].sum(), 1e-9)) * 1000
        net = g("Bilan, M USD, Global > Capitaux propres > Résultat net annuel")
        fp = g("Bilan, M USD, Global > Capitaux propres > Total des capitaux propres")
        R = "Ratios et indicateurs financiers > Ratios > "
        cours, n_act = g(R + "Cours de l'action à la fin du tour, USD"), g(R + "Actions sur le marché à la fin du tour, millions d'actions")
        dn = (1 - TAX) * d_contrib
        W.loc["ROE", P.US] = V.loc["ROE", P.US] * (net + dn) / net * (fp - net / 2) / (fp - net / 2 + d_net_avant + dn / 2)
        r0 = V.loc["rentabilité de l'action", P.US] / 100                         # cours de départ et d'arrivée décalés par les résultats acquis
        c0 = cours / (1 + r0)
        W.loc["rentabilité de l'action", P.US] = ((cours + B.fit["bpa"] * (d_net_avant + dn) / n_act) / (c0 + B.fit["bpa"] * d_net_avant / n_act) - 1) * 100
        W.loc["création de valeur", P.US] = V.loc["création de valeur", P.US] + d_contrib + float(o["cogs_s"].sum() - o0["cogs_s"].sum())
        return P.points(W)[P.US], dn

    s0 = world(played)
    o0 = s0[s0["team"] == P.US]
    world2 = None
    if suivant and (d_all["round"] == idx + 1).any():
        t2, markets2 = monde(idx + 1)
        params2 = sim.fit_params(d_all[d_all["round"] <= idx + 1])
        us2, V2 = (t2["team"] == P.US).values, P.valeurs(idx + 1)

        def world2(s):
            """Tour d'après, décisions réelles de tous, notre part précédente remplacée par celle que laisse s."""
            f = t2.copy()
            a, b = s[s["team"] == P.US].groupby("cell")["sim_demand"].sum(), s0[s0["team"] == P.US].groupby("cell")["sim_demand"].sum()
            f.loc[us2, "p_share"] = f.loc[us2, "p_share"] * f.loc[us2, "cell"].map(a / b.replace(0, np.nan)).fillna(1.0)
            return comptes(sim.simulate_round(f, params2, markets2, supply={}))
        s20 = world2(s0)
    rows = {}
    for name, x in {"joué": played, **{f"points {k}": v for k, v in xs.items() if k != "reconduit"}, **{f"marge {k}": v for k, v in xm.items() if k != "reconduit"}}.items():
        s = world(np.array(x, float))
        o = s[s["team"] == P.US]
        pts, dn = points_reels(V, idx, s, s0)
        rows[name] = dict(points=float(pts.sum()), marge=float((o["rev_s"] - o["cogs_s"] - o["adv"]).sum()), prevu=B.points_total(S.tidy(np.array(x, float), cells)),
                          **{c: float(pts[c]) for c in MARKETING if c in pts.index and not np.isnan(pts[c])})
        if world2 is not None:
            rows[name]["points_suivant"] = float(points_reels(V2, idx + 1, world2(s), s20, d_net_avant=dn)[0].sum())
            rows[name]["deux_tours"] = rows[name]["points"] + rows[name]["points_suivant"]
    T = pd.DataFrame(rows).T
    if verbose:
        pd.set_option("display.width", 250)
        print(f"=== Contre-épreuve du tour {tour} : points RÉELS (concurrents réels) de chaque décision ; total publié {real_pts[P.US].sum():.0f} ===")
        print(T.round(1).T.to_string())
    return T


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--tour", type=int, required=True, help="tour passé à rejouer")
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--suite", action="store_true", help="épreuve des tours suivants : objectif avec et sans `suite`, points réels du tour et du tour d'après")
    ap.add_argument("--productivite", action="store_true", help="rejeu en marche avant de la loi de productivité des ingénieurs")
    a = ap.parse_args()
    if a.productivite:
        productivite_rejeu()
    elif a.suite:
        for nom, opt in (("avec la suite", {}), ("tour seul", {"poids_suite": 0})):
            print(f"\n##### objectif : {nom}")
            contre_epreuve(a.tour, a.n, bareme=opt, suivant=True, marge=False)
    else:
        contre_epreuve(a.tour, a.n)
