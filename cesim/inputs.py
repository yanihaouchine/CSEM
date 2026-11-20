"""Relevé de début de tour : toutes les pages de décision, la couverture du réseau et les nouveautés.

  python3 -m cesim.inputs N            # tout enregistrer pour le tour N
  python3 -m cesim.inputs N rnd events # seulement certaines pages (affichage)

Produit :
  data/docs/pages_tour_N.txt      texte de chaque page de décision (champs annotés [IN=...], [SEL=...])
  data/docs/conditions_tourN.txt  conditions de marché
  data/couverture_tour_N.json     couverture du réseau par technologie, zone et tour (tours futurs compris)
  data/docs/champs_tour_N.json    liste des pages, des champs et des options ; comparée au tour précédent,
                                  elle signale les NOUVELLES FONCTIONNALITÉS (pages, champs, options apparus)
  data/docs/annonces_tour_N.json  ce que l'instructeur publie HORS des pages de décision : forum de session, tâches de la
                                  page d'accueil, documents de la page Manuels (les nouveaux sont téléchargés dans
                                  data/docs/manuels/). C'est là que sont annoncés l'interdiction d'une technologie ou un
                                  nouveau classement.

  python3 -m cesim.inputs N annonces   # seulement les annonces (forum, tâches, Manuels)
"""
import json
import re
import sys

from cesim.client import BASE, ROOT, _ajax_map_any, page_text, session, soup

# Pages connues. Le plan du site fait foi : toute page absente d'ici est relevée quand même et signalée.
PANELS = ["marketconditions", "events", "demand", "production", "inventory", "investments", "procurement", "environmentalimpact",
          "hr", "hrtraining", "hrlabor", "rnd", "marketingusa", "marketingasia", "marketingeurope", "marketingaftersales", "marketingcertifications", "marketingaftersales",
          "logistics", "tax", "finance", "decisionchecklist"]
DOCS = ROOT / "data" / "docs"


def site_panels(s):
    """Pages de décision listées par le plan du site, dans l'ordre."""
    sp = soup(s.get(f"{BASE}/ul/SiteMap?sim=gc").text)
    out = []
    for a in sp.find_all("a"):
        h = a.get("href") or ""
        m = re.search(r"Decisions\?.*panel=(\w+)", h)
        if m and m.group(1) not in out and m.group(1) != "tutorial":
            out.append(m.group(1))
    return out


def signature(html):
    """Champs de décision d'une page : identifiant -> liste d'options (menu) ou "saisie"."""
    sp, out = soup(html), {}
    for key, (_, cid) in _ajax_map_any(html).items():
        el = sp.find(id=cid)
        if el is None:
            continue
        out[key] = [o.get_text(strip=True) for o in el.find_all("option")] if el.name == "select" else ("case" if el.get("type") == "checkbox" else "saisie")
    return out


def coverage(s=None, tour=None):
    """Graphique « Réseau de stations » de la page Demande : couverture (%) de chaque technologie par zone,
    tours 0 à 12 (les tours FUTURS sont annoncés). Enregistré dans data/couverture_tour_N.json."""
    s = s or session()
    h = s.get(f"{BASE}/ul/Decisions?sim=gc&panel=demand").text
    out = {}
    for key, reg in [("USA", "USA"), ("Asia", "Chine"), ("EU", "Europe")]:
        m = re.search(r'Chart\.create\("demand\.coverage\.%s\.chart", "msline", (\{.*?\}), "cc-demand-coverage-%s-chart"\)' % (key, key), h, re.S)
        j = json.loads(m.group(1))
        labels = [int(c["label"]) for c in j["categories"][0]["category"] if "label" in c]
        out[reg] = {d["seriesname"]: dict(zip(labels, [x["value"] for x in d["data"]])) for d in j["dataset"]}
    if tour is not None:
        json.dump(out, open(ROOT / "data" / f"couverture_tour_{tour}.json", "w"), indent=1, ensure_ascii=False)
    return out


def novelties(tour, sig):
    """Ce qui est apparu ou a changé depuis le dernier relevé antérieur (pages, champs, options de menu)."""
    prev = sorted((int(f.stem.split("_")[-1]), f) for f in DOCS.glob("champs_tour_*.json") if int(f.stem.split("_")[-1]) < int(tour))
    if not prev:
        return ["(pas de relevé antérieur : rien à comparer)"]
    old = json.load(open(prev[-1][1]))
    out = []
    for p, fields in sig.items():
        if p not in old:
            out.append(f"NOUVELLE PAGE : {p} ({len(fields)} champs)")
            continue
        for k, v in fields.items():
            if k not in old[p]:
                out.append(f"nouveau champ : {p} / {k} = {v}")
            elif isinstance(v, list) and v != old[p][k]:
                plus = [o for o in v if o not in old[p][k]]
                moins = [o for o in old[p][k] if o not in v]
                out.append(f"options modifiées : {p} / {k} : +{plus} -{moins}")
        for k in old[p]:
            if k not in fields:
                out.append(f"champ disparu : {p} / {k}")
    for p in old:
        if p not in sig:
            out.append(f"page disparue : {p}")
    return out or [f"(aucun changement de champ ni d'option depuis le tour {prev[-1][0]})"]


def coverage_changes(tour, cov):
    """Écarts entre la couverture relevée ce tour et celle du relevé précédent (le scénario peut la réviser)."""
    prev = sorted((int(f.stem.split("_")[-1]), f) for f in (ROOT / "data").glob("couverture_tour_*.json") if int(f.stem.split("_")[-1]) < int(tour))
    if not prev:
        return []
    old = json.load(open(prev[-1][1]))
    return [f"couverture révisée : {reg} {tech} tour {k} : {old[reg][tech][str(k)]} -> {v}"
            for reg, t in cov.items() for tech, s in t.items() for k, v in s.items() if old.get(reg, {}).get(tech, {}).get(str(k)) not in (None, v)]


def announcements(s=None, tour=None, download=True):
    """Annonces de l'instructeur hors pages de décision : messages du forum de session (ceux de l'instructeur sont
    marqués), tâches de la page d'accueil, documents de la page Manuels. Enregistré dans data/docs/annonces_tour_N.json.
    Un document dont le titre n'existait pas au relevé précédent est téléchargé dans data/docs/manuels/."""
    s = s or session()
    sp = soup(s.get(f"{BASE}/ul/CourseForum?sim=gc").text)
    posts = []
    for d in sp.find_all("div", class_="original-post"):
        name, title, text = d.find(class_="forum-post-item__name"), d.find(class_="forum-post-details__title"), d.find(class_="forum-post-details__text")
        body = " ".join(dict.fromkeys(x.get_text(" ", strip=True) for x in d.find_all("p") if "forum-post-item" not in " ".join(x.get("class") or [])))
        posts.append(dict(id=d.get("id"), auteur=name.get_text(strip=True) if name else "", instructeur="original-post--instructor" in d.get("class", []),
                          titre=title.get_text(" ", strip=True) if title else "", texte=(body or (text.get_text(" ", strip=True) if text else "")).replace("\xa0", " ")))
    home = soup(s.get(f"{BASE}/ul/Home?sim=gc").text).body.get_text(" ", strip=True).replace("\xa0", " ")
    a, b = home.find("Tâches"), home.find("Messages Plus")
    h = s.get(f"{BASE}/ul/Reading?sim=gc").text
    docs = []
    for title, note, bid in re.findall(r'instructor-panel-item__title">([^<]*)</h3>\s*<p class="instructor-panel-item__text">([^<]*)</p>.*?<button[^>]*id="(\w+)"', h, re.S):
        m = re.search(r"Wicket\.Event\.add\('%s', 'click'.*?window\.location\.href='\./([^']+)'" % bid, h, re.S)
        import html as _html
        title, note = _html.unescape(title), _html.unescape(note)
        docs.append(dict(titre=title.strip(), note=note.strip(), url=m.group(1).replace("&amp;", "&") if m else None))
    out = dict(forum=posts, taches=home[a:b].strip() if 0 <= a < b else "", manuels=docs)
    if tour is not None:
        prev = _previous("annonces", tour)
        known = {d["titre"] for d in json.load(open(prev[1]))["manuels"]} if prev else None
        if download:
            (DOCS / "manuels").mkdir(exist_ok=True)
            for d in docs:
                if d["url"] and (known is None or d["titre"] not in known):
                    r = s.get(f"{BASE}/ul/{d['url']}")
                    ext = {b"%PDF": "pdf", b"PK\x03\x04": "xlsx"}.get(r.content[:4], "bin")
                    d["fichier"] = f"manuels/{re.sub(r'[^0-9A-Za-zÀ-ÿ]+', '_', d['titre']).strip('_')}.{ext}"
                    (DOCS / d["fichier"]).write_bytes(r.content)
        json.dump({**out, "manuels": [{k: v for k, v in d.items() if k != "url"} for d in docs]},
                  open(DOCS / f"annonces_tour_{tour}.json", "w"), indent=1, ensure_ascii=False)
    return out


def _previous(kind, tour):
    """Dernier relevé `kind`_tour_K.json antérieur au tour : (K, fichier), ou None."""
    prev = sorted((int(f.stem.split("_")[-1]), f) for f in DOCS.glob(f"{kind}_tour_*.json") if int(f.stem.split("_")[-1]) < int(tour))
    return prev[-1] if prev else None


def announcement_changes(tour, ann, prev=None):
    """Annonces apparues depuis le relevé précédent : messages du forum, documents de la page Manuels, tâches."""
    prev = prev or _previous("annonces", tour)
    if not prev:
        return ["(annonces : pas de relevé antérieur, tout est listé)"] + [f"message : {p['auteur']} — {p['titre']} : {p['texte'][:300]}" for p in ann["forum"] if p["instructeur"]]
    old = json.load(open(prev[1]))
    seen, docs = {p["id"] for p in old["forum"]}, {d["titre"] for d in old["manuels"]}
    out = [f"NOUVEAU MESSAGE {'DE L INSTRUCTEUR' if p['instructeur'] else 'd un étudiant (pas une règle du jeu)'} : {p['auteur']} — {p['titre']} : {p['texte'][:400]}"
           for p in ann["forum"] if p["id"] not in seen]
    out += [f"NOUVEAU DOCUMENT (page Manuels) : {d['titre']} {d.get('note', '')} -> data/docs/{d.get('fichier', '?')}" for d in ann["manuels"] if d["titre"] not in docs]
    if ann["taches"] != old.get("taches"):
        out.append(f"tâches de la page d'accueil modifiées : {ann['taches']}")
    return out


if __name__ == "__main__":
    s = session()
    tour = sys.argv[1]
    only = sys.argv[2:]
    if only == ["annonces"]:
        prev = _previous("annonces", tour)
        print("\n".join(announcement_changes(tour, announcements(s, tour), prev) or ["(aucune annonce nouvelle)"]))
        sys.exit()
    listed = site_panels(s)
    unknown = [p for p in listed if p not in PANELS]
    out, sig = [], {}
    for p in (only or PANELS + unknown):
        t, html = page_text(s, p)
        out.append(f"===== {p}\n{t}")
        sig[p] = signature(html)
    print("\n\n".join(out))
    if not only:
        (DOCS / f"pages_tour_{tour}.txt").write_text("\n\n".join(out))
        (DOCS / f"conditions_tour{tour}.txt").write_text(out[0].split("\n", 1)[1])
        cov = coverage(s)
        prev_ann = _previous("annonces", tour)
        news = ([f"PAGE INCONNUE DU SCRIPT : {p}" for p in unknown] + novelties(tour, sig) + coverage_changes(tour, cov)
                + announcement_changes(tour, announcements(s, tour), prev_ann))
        json.dump(sig, open(DOCS / f"champs_tour_{tour}.json", "w"), indent=1, ensure_ascii=False)
        json.dump(cov, open(ROOT / "data" / f"couverture_tour_{tour}.json", "w"), indent=1, ensure_ascii=False)
        print("\n===== NOUVEAUTÉS DEPUIS LE DERNIER RELEVÉ")
        print("\n".join(news))
