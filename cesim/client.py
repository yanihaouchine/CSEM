"""Client minimal pour la plateforme Cesim (session authentifiée).

Identifiants : variables d'environnement CESIM_USER et CESIM_PASSWORD, sinon le fichier `identifiant.md`
(lignes `adresse_mail : ...` et `mdp : ...`), qui n'est pas suivi par git. CESIM_ZONE est le nom affiché sur
la zone de décisions personnelle : les programmes refusent d'écrire ailleurs.
"""
import os
import pickle
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://bordeaux-inp.cesim.com"
COOKIES = ROOT / "data" / ".cookies.pkl"
ZONE = os.environ.get("CESIM_ZONE", "Yani")


def _creds():
    if os.environ.get("CESIM_USER") and os.environ.get("CESIM_PASSWORD"):
        return os.environ["CESIM_USER"], os.environ["CESIM_PASSWORD"]
    txt = (ROOT / "identifiant.md").read_text()
    u = re.search(r"adresse_mail\s*:\s*(\S+)", txt).group(1)
    p = re.search(r"mdp\s*:\s*(\S+)", txt).group(1)
    return u, p


def session():
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0"
    if COOKIES.exists():
        s.cookies.update(pickle.loads(COOKIES.read_bytes()))
        r = s.get(BASE + "/ul/Home?sim=gc", allow_redirects=False)
        if r.status_code == 200 and "Déconnexion" in r.text:
            return s
        s.cookies.clear()
    s.get(BASE + "/?locale=fr_FR")
    u, p = _creds()
    r = s.post(BASE + "/auth/login", data={"redirect": "", "u": u, "p": p})
    assert "Déconnexion" in r.text, "login échoué"
    COOKIES.write_bytes(pickle.dumps(s.cookies.get_dict()))
    return s


def soup(html):
    return BeautifulSoup(html, "html.parser")


def page_text(s, panel, kind="Decisions"):
    """Texte d'une page, avec les champs de saisie annotés [IN nom=valeur]."""
    r = s.get(f"{BASE}/ul/{kind}?sim=gc&panel={panel}")
    sp = soup(r.text)
    main = sp.body
    for sc in main.find_all(["script", "style", "nav"]):
        sc.decompose()
    for i in main.find_all(["input", "select"]):
        if i.name == "select":
            sel = [o.get_text(strip=True) for o in i.find_all("option") if o.get("selected") is not None]
            opts = [o.get_text(strip=True) for o in i.find_all("option")]
            i.replace_with(f" [SEL={sel} parmi {opts[:9]}] ")
        elif i.get("type") != "hidden":
            flag = " COCHÉ" if i.get("checked") is not None else ""
            i.replace_with(f" [IN={i.get('value')}{flag}] ")
    t = main.get_text(" ", strip=True).replace("\xa0", " ")
    a = t.rfind("RÉSULTAT NET ANNUEL")
    b = t.find("Détails de la session")
    return t[a:b], r.text


def _ajax_map(html):
    """decidx -> (url, id du champ) pour tous les champs de la page."""
    out = {}
    for m in re.finditer(r'Wicket\.Ajax\.ajax\(\{"u":"\./([^"]+)","m":"POST","c":"(\w+)","ep":\[\{"name":"decidx","value":"([^"]+)"\}\]', html):
        out[m.group(3)] = (m.group(1), m.group(2))
    return out


def fields(s, panel):
    """Valeurs actuelles des champs de décision d'une page : decidx -> valeur."""
    r = s.get(f"{BASE}/ul/Decisions?sim=gc&panel={panel}")
    sp = soup(r.text)
    amap = _ajax_map(r.text)
    vals = {}
    for k, (url, cid) in amap.items():
        el = sp.find(id=cid)
        if el is None:
            continue
        if el.name == "select":
            o = el.find("option", selected=True)
            vals[k] = (o.get("value"), o.get_text(strip=True)) if o else None
        else:
            vals[k] = el.get("value")
    return vals, amap, r.text


def set_decision(s, panel, decidx, value):
    """Modifie un champ dans la zone de décision ACTIVE (zone personnelle) et vérifie."""
    vals, amap, _ = fields(s, panel)
    url, cid = amap[decidx]
    old = vals[decidx]
    name = soup(_).find(id=cid).get("name")
    r = s.post(f"{BASE}/ul/{url}", data={name: str(value), "decidx": decidx, "dvalx": str(value), "exvalx": old if isinstance(old, str) else old[0]},
               headers={"Wicket-Ajax": "true", "Wicket-Ajax-BaseURL": f"ul/Decisions?sim=gc&panel={panel}", "X-Requested-With": "XMLHttpRequest",
                        "Wicket-FocusedElementId": cid})
    new = fields(s, panel)[0][decidx]
    return old, new, r.status_code


def forecast(s):
    """Prévisionnel financier global (k USD) affiché en tête des pages de décisions."""
    r = s.get(f"{BASE}/ul/Decisions?sim=gc&panel=tax")
    t = soup(r.text).body.get_text(" ", strip=True).replace("\xa0", " ")
    out = {}
    for lab, key in [("Dernier tour Chiffre d'affaires", "ca"), ("(EBITDA)", "ebitda"), ("(EBIT)", "ebit"), ("RÉSULTAT NET ANNUEL", "net")]:
        m = re.search(re.escape(lab) + r"\s+(-?\d{1,3}(?: \d{3})*)\s", t)
        out[key] = int(m.group(1).replace(" ", "")) if m else None
    return out


def active_zone(s):
    r = s.get(f"{BASE}/ul/Home?sim=gc")
    t = soup(r.text).body.get_text(" ", strip=True)
    m = re.search(r"Zone de décisions:\s*(.*?)\s*Dernières modifications", t)
    return m.group(1) if m else None


def set_checkbox(s, panel, decidx, checked):
    """Coche ou décoche une case de décision dans la zone active ; renvoie (avant, après)."""
    r = s.get(f"{BASE}/ul/Decisions?sim=gc&panel={panel}")
    amap = _ajax_map_any(r.text)
    url, cid = amap[decidx]
    el = soup(r.text).find(id=cid)
    old = el.get("checked") is not None
    if old == checked:
        return old, old
    data = {"decidx": decidx, "dvalx": "true" if checked else "false", "exvalx": "true" if old else "false"}
    if checked:
        data[el.get("name")] = "on"
    s.post(f"{BASE}/ul/{url}", data=data, headers={"Wicket-Ajax": "true", "Wicket-Ajax-BaseURL": f"ul/Decisions?sim=gc&panel={panel}",
                                                   "X-Requested-With": "XMLHttpRequest"})
    r = s.get(f"{BASE}/ul/Decisions?sim=gc&panel={panel}")
    amap = _ajax_map_any(r.text)
    new = soup(r.text).find(id=amap[decidx][1]).get("checked") is not None
    return old, new


def _ajax_map_any(html):
    out = {}
    for m in re.finditer(r'Wicket\.Ajax\.ajax\(\{"u":"\./([^"]+)",(?:"m":"POST",)?"c":"(\w+)","ep":\[\{"name":"decidx","value":"([^"]+)"\}\]', html):
        out[m.group(3)] = (m.group(1), m.group(2))
    return out
