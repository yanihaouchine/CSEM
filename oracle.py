"""Applique un jeu de décisions dans la zone personnelle et lit le prévisionnel de la plateforme."""
import json
import sys

from cesim.client import ROOT, ZONE, active_zone, fields, forecast, session, set_decision

PANELS = {"area1": "marketingusa", "area2": "marketingasia", "area3": "marketingeurope"}


def panel_of(k):
    if k.endswith("share.est") or "growth" in k:
        return "demand"
    return PANELS[k.split(".")[0]]


def norm(v):
    return str(v).replace("\xa0", "").replace(" ", "")


def apply(s, dec):
    assert ZONE in active_zone(s), "la zone active n'est pas la zone personnelle"
    cache = {}
    for k, v in dec.items():
        p = panel_of(k)
        if p not in cache:
            cache[p] = fields(s, p)[0]
        if float(norm(cache[p][k])) == float(v):
            continue
        old, new, code = set_decision(s, p, k, v)
        ok = float(norm(new)) == float(v)
        print(f"  {k}: {norm(old)} -> {norm(new)} {'OK' if ok else 'ÉCHEC'}")
        assert ok, (k, old, new, code)
    return forecast(s)


if __name__ == "__main__":
    s = session()
    name = sys.argv[1]
    dec = json.load(open(ROOT / "data" / "variantes.json"))[name]
    print(name, apply(s, dec))


# ====================================================================== calculateur généralisé (tous les leviers)
import hashlib
import re
import time

from cesim.client import BASE, _ajax_map_any, page_text, set_checkbox, soup


def _num(txt):
    return float(txt.replace("\xa0", "").replace(" ", ""))


def page_state(s, panel):
    """État de tous les champs d'une page : clé -> dict(kind, value[, options])."""
    html = s.get(f"{BASE}/ul/Decisions?sim=gc&panel={panel}").text
    sp, out = soup(html), {}
    for key, (_, cid) in _ajax_map_any(html).items():
        el = sp.find(id=cid)
        if el is None:
            continue
        if el.name == "select":
            opts = [(o.get("value"), o.get_text(strip=True), o.get("selected") is not None) for o in el.find_all("option")]
            out[key] = dict(kind="menu", value=next((t for _, t, sel in opts if sel), ""), options={t: v for v, t, _ in opts})
        elif el.get("type") == "checkbox":
            out[key] = dict(kind="case", value=el.get("checked") is not None)
        else:
            out[key] = dict(kind="saisie", value=norm(el.get("value") or ""))
    return out


class Refus(Exception):
    """La plateforme refuse une valeur (condition non remplie, par exemple un score ESG minimal)."""


def set_select(s, panel, key, optvalue):
    """Choisit une option d'un menu (par sa valeur interne) dans la zone active. Renvoie le message de refus éventuel."""
    html = s.get(f"{BASE}/ul/Decisions?sim=gc&panel={panel}").text
    url, cid = _ajax_map_any(html)[key]
    el = soup(html).find(id=cid)
    data = {el.get("name"): str(optvalue), "decidx": key, "dvalx": str(optvalue), "exvalx": el.get("data-exvalx", "")}
    r = s.post(f"{BASE}/ul/{url}", data=data, headers={"Wicket-Ajax": "true", "Wicket-Ajax-BaseURL": f"ul/Decisions?sim=gc&panel={panel}",
                                                     "X-Requested-With": "XMLHttpRequest", "Wicket-FocusedElementId": cid})
    m = re.search(r"Close\s*-->\s*(.*?)\]\]>", re.sub(r"<[^>]+>", " ", r.text), re.S)
    return re.sub(r"\s+", " ", m.group(1)).replace("&#039;", "'").strip() if m else ""


def same(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return bool(a) == bool(b)
    try:
        return abs(float(norm(a)) - float(norm(b))) < 1e-6
    except (TypeError, ValueError):
        return str(a) == str(b)


ENTITES = {"2": "USA", "3": "Chine", "4": "Europe"}


def previsionnel(s):
    """Prévisionnel financier détaillé (onglets de la page Impôts), en k USD : compte de résultat de chaque entité
    (ventes, cessions internes, chiffre d'affaires total, EBIT, résultat net), bilan global (fonds propres, dettes à
    long et à court terme) et trésorerie de chaque entité, ratios (ROE, bénéfice par action). Lecture seule : un
    onglet ne modifie aucune décision et la page revient à la vue globale au rechargement.
    C'est la source exacte des critères « marge opérationnelle » (EBIT / chiffre d'affaires total de l'entité, cessions
    internes comprises), « découvert » et « indépendance financière »."""
    r = s.get(f"{BASE}/ul/Decisions?sim=gc&panel=tax")
    urls = {(c, t): u for u, c, t in re.findall(r'"u":"\./(Decisions\?[^"]*projections-top~ctrl-(\d)-tabs-(\d)-l[^"]*)"', r.text)}
    H = {"Wicket-Ajax": "true", "Wicket-Ajax-BaseURL": "ul/Decisions?sim=gc&panel=tax", "X-Requested-With": "XMLHttpRequest"}

    def tab(c, t):
        if (c, t) not in urls:
            return ""
        a = s.get(f"{BASE}/ul/{urls[(c, t)]}", headers=H)
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", a.text)).replace("\xa0", " ").replace("&#039;", "'").replace("&amp;", "&")

    def num(label, txt, dec=False):
        # montants : entiers par groupes de trois chiffres ; le « ∆ % » qui suit a une décimale et ne doit pas s'y coller
        # (« 38 207 449 121.0 » = 38 207 449 puis +121,0 %)
        pat = r"\s+(-?\d+(?:\.\d+)?)(?=\s)" if dec else r"\s+(-?\d{1,3}(?: \d{3})*)(?![\d.])"
        m = re.search(re.escape(label) + pat, txt)
        return _num(m.group(1)) if m else None

    out = {"zones": {}, "tresorerie": {}}
    for t, z in ENTITES.items():
        cr = tab("1", t)
        if not cr:
            continue
        ventes = num("Revenus générés par les ventes", cr)
        if ventes is None:                                   # l'Europe ne produit pas : une seule ligne « Chiffre d'affaires »
            ventes = num("Dernier tour Chiffre d'affaires", cr)
        internes = num("Revenus générés par les prix de transferts (ou prix de cessions internes)", cr) or 0.0
        total = num("Total revenus", cr)
        # charges de l'entité qui ne suivent pas ses ventes : R&D, garantie et collecte de données, administration, amortissement
        fixes = sum(num(lab, cr) or 0.0 for lab in ("R&D", "Garantie et collecte de données", "Administration", "Amortissement des immobilisations"))
        out["zones"][z] = dict(ventes=ventes, internes=internes, ca=total if total is not None else ventes, fixes=fixes,
                               ebit=num("RÉSULTAT OPÉRATIONNEL (EBIT)", cr), net=num("RÉSULTAT NET ANNUEL", cr))
        out["tresorerie"][z] = num("Trésorerie et équivalents", tab("2", t))
    b = tab("2", "1")
    out["fp"], out["dette_lt"], out["decouvert"] = num("Total des capitaux propres", b), num("Dettes à long terme", b) or 0.0, num("Dettes à court terme (imprévue)", b) or 0.0
    ra = tab("3", "1")
    out["roe"], out["bpa"] = num("Rentabilité des fonds propres (ROE), %", ra, True), num("Bénéfice par action (EPS), USD", ra, True)
    return out


def read_state(s, pages=("tax", "finance", "procurement", "inventory", "marketingcertifications", "hr"), detail=True):
    """Indicateurs du prévisionnel : résultat net (total et par entité), trésorerie, dette à court terme,
    fournisseurs requis, stocks finaux et demande non servie, score ESG cumulé, jours-homme libres.
    detail : ajoute `previsionnel` (comptes par entité, bilan, ratios), 8 lectures de plus par état."""
    out = {}
    grab = lambda pat, t: [_num(x) for x in re.findall(pat + r"\s+(-?\d{1,3}(?: \d{3})*(?:\.\d+)?)", t)]
    for p in pages:
        t, _ = page_text(s, p)
        if p == "tax":
            out.update(forecast(s))
            m = re.search(r"RÉSULTAT NET ANNUEL((?:\s+-?\d[\d ]*?(?=\s+-?\d|\s+[A-Za-zÀ-ÿ])){1,4})", t)
            nums = re.findall(r"-?\d{1,3}(?: \d{3})*", t[:120])
            if len(nums) >= 4:
                out["net_usa"], out["net_chine"], out["net_europe"] = [int(x.replace(" ", "")) for x in nums[:3]]
            if detail:
                try:
                    out["previsionnel"] = previsionnel(s)
                except Exception as e:                       # la lecture détaillée ne doit jamais faire échouer une évaluation
                    out["previsionnel_erreur"] = str(e)
        elif p == "finance":
            out["dette_ct_nouvelle"] = grab(r"Nouvelles dettes à court terme contractées", t)
            out["tresorerie_fin"] = grab(r"Trésorerie \(fin de l'année/ du tour\)", t)
        elif p == "procurement":
            v = grab(r"Nombre de fournisseurs requis", t)
            out["fournisseurs_requis"] = v[0] if v else None
            out["fournisseurs_actifs"] = len(re.findall(r"\[IN=None COCHÉ\] (?!Demander)", t.split("Sélection des fournisseurs")[-1])) if "Sélection" in t else None
            v = grab(r"Coût moyen par composant, USD", t)
            out["cout_composant"] = v[0] if v else None
        elif p == "inventory":
            m = re.search(r"Total (Thermique.*?)Gestion des stocks", t)
            if m:
                for tech, a, b, c, d, e in re.findall(r"(Thermique|Hybride|Électrique|Hydrogène) ([\d ]+?) ([\d ]+?) ([\d ]+?) ([\d ]+?) / ([\d ]+?)(?= [A-ZÉ]|$)", m.group(1).strip()):
                    out[f"stock_final_{tech}"], out[f"non_servi_{tech}"] = _num(c), _num(e)
        elif p == "marketingcertifications":
            v = grab(r"Votre score ESG cumulé actuel", t)
            out["score_esg"] = v[0] if v else None
        elif p == "hr":
            a, b = grab(r"Total Jours-homme disponibles", t), grab(r"Total Jours-homme alloués", t)
            out["jours_homme_libres"] = (a[0] - b[0]) if a and b else None
    return out


class Oracle:
    """Prévisionnel de la plateforme comme calculateur : on saisit des décisions dans la zone personnelle,
    on relit les indicateurs, on restaure. Les décisions de l'équipe ne sont jamais touchées.

        with Oracle(tour) as o:
            base = o.evaluate({})
            r = o.evaluate({"esg.water.invest": True})
    """

    def __init__(self, tour, pages=None, pause=0.15, verbose=False):
        from leviers import levers
        self.tour, self.pause, self.verbose = tour, pause, verbose
        self.s = session()
        assert ZONE in active_zone(self.s), "la zone active n'est pas la zone personnelle"
        self.page = {l["key"]: l["page"] for l in levers(tour)}
        self.pages = pages or sorted(set(self.page.values()))
        self.state = {}
        for p in self.pages:
            st = page_state(self.s, p)
            self.state.update(st)
            self.page.update({k: p for k in st})          # la page réelle fait foi (champs apparus depuis le relevé)
        self.base = {k: v["value"] for k, v in self.state.items()}
        self.cur = dict(self.base)
        self.cache_file = ROOT / "data" / f"oracle_cache_tour{tour}.json"
        sig = hashlib.md5(json.dumps(self.base, sort_keys=True, default=str).encode()).hexdigest()
        c = json.load(open(self.cache_file)) if self.cache_file.exists() else {}
        self.cache = c.get("evals", {}) if c.get("base") == sig else {}
        self.sig, self.calls = sig, 0
        json.dump(self.base, open(ROOT / "data" / f"zone_tour{tour}_avant_recherche.json", "w"), indent=1, ensure_ascii=False, default=str)

    # -- saisie d'un champ, quel que soit son type
    def _set(self, key, value):
        p = self.page[key]
        st = page_state(self.s, p)
        for _ in range(4):                      # la page est parfois rendue sans ses champs juste après une saisie : on réessaie
            if key in st:
                break
            time.sleep(1.0)
            self.s = session()
            st = page_state(self.s, p)
        if key not in st:
            raise KeyError(f"{key} absent de la page {p}")
        f = st[key]
        if same(f["value"], value):
            self.cur[key] = f["value"]
            return
        msg = ""
        if f["kind"] == "case":
            set_checkbox(self.s, p, key, bool(value))
        elif f["kind"] == "menu":
            msg = set_select(self.s, p, key, f["options"][value])
        else:
            set_decision(self.s, p, key, value)
        time.sleep(self.pause)
        st = page_state(self.s, p)
        for _ in range(4):
            if key in st:
                break
            time.sleep(1.0)
            st = page_state(self.s, p)
        new = st[key]["value"]
        self.cur[key] = new
        if not same(new, value):
            raise Refus(f"{key} = {value} refusé par la plateforme" + (f" : {msg}" if msg else f" (valeur restée à {new})"))
        self.cur[key] = new
        if self.verbose:
            print(f"    {key}: {f['value']} -> {new}")

    def apply(self, dec):
        """Met la zone dans l'état « base + dec » (ne saisit que ce qui diffère de l'état courant)."""
        target = {**self.base, **dec}
        for k, v in target.items():
            if k in self.cur and not same(self.cur[k], v):
                self._set(k, v)

    def evaluate(self, dec, pages=None):
        key = json.dumps(dec, sort_keys=True, ensure_ascii=False, default=str) + ("|" + ",".join(pages) if pages else "")
        if key in self.cache:
            return self.cache[key]
        try:
            self.apply(dec)
        except Refus as e:
            self.cache[key] = dict(refus=str(e))
            return self.cache[key]
        r = read_state(self.s, pages) if pages else read_state(self.s)
        self.calls += 1
        self.cache[key] = r
        json.dump(dict(base=self.sig, evals=self.cache), open(self.cache_file, "w"), ensure_ascii=False)
        return r

    def refresh(self):
        """Relit toutes les pages : à appeler après un changement de technologie, qui fait apparaître de nouveaux champs
        (les champs d'un produit s'appellent areaN.techK.* avec K = 1 Thermique, 2 Hybride, 3 Électrique, 4 Hydrogène)."""
        for p in self.pages:
            st = page_state(self.s, p)
            self.state.update(st)
            self.page.update({k: p for k in st})
            for k, v in st.items():
                self.cur[k] = v["value"]
                self.base.setdefault(k, v["value"])
        return self

    def commit(self, dec):
        """Saisit `dec` et le garde : ces valeurs deviennent la nouvelle base (elles ne seront pas restaurées)."""
        self.apply(dec)
        for k in dec:
            self.base[k] = self.cur[k]
        self.cache = {}
        self.sig = hashlib.md5(json.dumps(self.base, sort_keys=True, default=str).encode()).hexdigest()

    def resync(self, target=None, passes=3):
        """Relit toute la zone et remet chaque champ à la valeur de `target` (défaut : la base). Nécessaire quand une
        saisie en modifie d'autres par ricochet (changer la technologie d'un modèle remet son marketing à zéro)."""
        target = dict(self.base if target is None else target)
        for _ in range(passes):
            actual = {}
            for p in self.pages:
                actual.update({k: v["value"] for k, v in page_state(self.s, p).items()})
            diff = [k for k in target if k in actual and not same(actual[k], target[k])]
            self.cur.update(actual)
            if not diff:
                return []
            # les menus d'abord (ils conditionnent les autres champs), puis le reste
            for k in sorted(diff, key=lambda k: 0 if self.state.get(k, {}).get("kind") == "menu" else 1):
                try:
                    self._set(k, target[k])
                except (Refus, KeyError) as e:
                    print("  resync :", e)
        return diff

    def restore(self):
        self.apply({})
        left = self.resync()
        if left:
            print("ATTENTION : champs non restaurés :", left)
        return forecast(self.s)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        try:
            self.restore()
        except Exception as e:           # ne masque pas l'erreur d'origine, mais la signale
            print("ATTENTION : restauration de la zone incomplète :", e)
        return False
