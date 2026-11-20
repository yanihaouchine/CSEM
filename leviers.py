"""Registre de tous les leviers de décision de la plateforme.

  python3 leviers.py N     # classe chaque champ relevé au tour N ; échoue si un champ n'est pas classé

Chaque champ de `data/docs/champs_tour_N.json` (produit par `python3 -m cesim.inputs N`) doit correspondre à une
règle ci-dessous. Un champ sans règle est une NOUVELLE FONCTIONNALITÉ du jeu : il faut décider comment la chercher
avant d'optimiser. C'est ce contrôle qui garantit qu'aucun levier n'est oublié.

Étapes de recherche (voir optimise_tout.py) :
  A offre            technologie de chaque modèle et de chaque ligne
  B marketing        prix, équipements, publicité
  C production       lignes, sous-traitance, priorités de livraison
  D discrets         fournisseurs, ESG, RH, politiques, certification, événements
  E finance          transferts, dette, prix de transfert, dividendes
  F multi-tours      R&D, licences, effectifs, usines
  estimation         saisies qui ne sont pas des décisions (elles alimentent le prévisionnel)
  hors recherche     non cherché, avec la raison
"""
import json
import re
import sys

from cesim.client import ROOT

# (motif de l'identifiant, étape, évaluateur, commentaire)
RULES = [
    (r"area\d\.tech\d\.(price|feat|adv)$", "B marketing", "demande", "prix, équipements, publicité d'un produit"),
    (r"area\d\.tech\d\.mstrat$", "B marketing", "demande (effet inconnu)", "ciblage de la stratégie marketing d'un produit (apparu en cours de tour 7 : équilibré, prix bas, équipements, image de marque, développement durable)"),
    (r"(us|asia|eu)\d\.tech$", "A offre", "demande", "technologie d'un modèle dans une zone"),
    (r"(us|asia)\.line\d\.tech$", "A offre", "plateforme", "technologie d'une ligne de production"),
    (r"area\d\.tech\d\.share\.est$", "estimation", "-", "part de marché estimée : reprise du simulateur"),
    (r"(us|asia|eu)\.growth\.prediction$", "estimation", "-", "croissance estimée : reprise des conditions de marché"),
    (r"(next\.round|round\.after)\.estimate\.\d$", "estimation", "-", "demande future estimée (page Investissements)"),
    (r"rd\.engineer\.turnover\.estimate\.\d$", "estimation", "-", "départs volontaires estimés"),
    (r"(us|asia)\.production\d$", "C production", "demande + plateforme", "part de capacité d'une ligne"),
    (r"(us|asia)\.outsource\d$", "C production", "demande + plateforme", "quantité sous-traitée"),
    (r"(us|asia)\.priority(\.\d)?$", "C production", "plateforme", "priorités de livraison"),
    (r"supplier\.\d$", "D discrets", "plateforme + demande", "fournisseur actif (coût, qualité, développement durable)"),
    (r"study\.\d$", "D discrets", "plateforme", "étude d'un fournisseur (révèle ses notes)"),
    (r"esg\.renew\.energy\.area\d$", "D discrets", "plateforme + ESG", "part d'énergie renouvelable"),
    (r"esg\.(emissions|energy|water)\.invest$", "D discrets", "plateforme + ESG", "amélioration de processus"),
    (r"esg\.recyclability(\.commit)?$", "D discrets", "plateforme + ESG", "recyclabilité et engagement"),
    (r"esg\.trn\.", "D discrets", "plateforme + ESG", "priorité de formation"),
    (r"esg2\.", "D discrets", "plateforme + ESG", "politique de travail"),
    (r"esg\.after\.sales\.(warranty|collection|protection|sharing)$", "D discrets", "plateforme + ESG", "service client (apparu au tour 8) : garantie, collecte, protection et partage des données ; effet sur le score S et la demande"),
    (r"esg\.reporting$", "D discrets", "plateforme + demande", "certification développement durable"),
    (r"esg\.(transparency\.trial|green\.loan\.gamble|battery\.bargaining|quality\.quandary|sustainable\.sourcing\.shift|suppliers\.standoff)$", "D discrets", "plateforme + ESG", "événement"),
    (r"rd\.engineer\.(salary|training)\.\d$", "D discrets", "plateforme + ESG", "salaire et budget de formation"),
    (r"inv\.liquid\.area\d\.tech\d$", "C production", "plateforme", "liquidation d'un stock (lot entier, seulement si la technologie n'est plus vendue ; apparu au tour 8)"),
    (r"esg\.after\.sales\.warranty$", "D discrets", "plateforme + demande", "service client : durée de garantie (1, 2, 3, 5 ans ; effet positif sur la demande, coût en % du chiffre d'affaires ; apparu au tour 8)"),
    (r"esg\.after\.sales\.(collection|protection|sharing)$", "D discrets", "plateforme + ESG", "service client : collecte, protection et partage des données (points Social relatifs à la moyenne des équipes ; apparu au tour 8)"),
    (r"transfer\.(us|asia)\.to\.(us|asia|eu)$", "E finance", "plateforme", "prix de transfert"),
    (r"(long\.debt|dividends|cash\.us\.to\.(asia|eu))$", "E finance", "plateforme", "dette, dividende, transfert interne"),
    (r"share\.(issue|buyback)$", "E finance", "plateforme", "émission ou rachat d'actions (apparu au tour 6)"),
    (r"rd\.engineer\.allocation\.tech\d$", "F multi-tours", "plateforme + demande", "jours-homme de R&D par technologie"),
    (r"rd\.engineer\.total\.amount\.\d$", "F multi-tours", "plateforme", "effectif de R&D"),
    (r"license\.tech\d$", "F multi-tours", "plateforme + demande", "achat de licence (équipements immédiats)"),
    (r"(us|asia)\.newplants$", "F multi-tours", "plateforme", "achat ou cession d'usines"),
    (r"license\.between\.", "hors recherche", "-", "licence entre équipes : exige un prix convenu avec l'autre équipe"),
]
ORDER = ["A offre", "B marketing", "C production", "D discrets", "E finance", "F multi-tours", "estimation", "hors recherche"]


def classify(key):
    for pat, stage, evaluator, note in RULES:
        if re.search(pat, key):
            return stage, evaluator, note
    return None


def levers(tour):
    """Liste des champs du tour : dict(key, page, kind, domain, stage, evaluator, note). stage=None si non classé."""
    sig = json.load(open(ROOT / "data" / "docs" / f"champs_tour_{tour}.json"))
    out = []
    for page, fields in sig.items():
        for key, dom in fields.items():
            c = classify(key)
            out.append(dict(key=key, page=page, kind="menu" if isinstance(dom, list) else dom, domain=dom if isinstance(dom, list) else None,
                            stage=c[0] if c else None, evaluator=c[1] if c else None, note=c[2] if c else None))
    return out


def page_of(tour):
    return {l["key"]: l["page"] for l in levers(tour)}


def report(tour):
    L = levers(tour)
    unknown = [l for l in L if l["stage"] is None]
    lines = [f"Tour {tour} : {len(L)} champs de décision"]
    for st in ORDER:
        g = [l for l in L if l["stage"] == st]
        if g:
            lines.append(f"  {st:15s} {len(g):3d}  " + ", ".join(sorted({l['note'].split(' (')[0].split(' :')[0] for l in g})))
    if unknown:
        lines.append(f"  NON CLASSÉS     {len(unknown):3d}  -> nouvelle fonctionnalité à traiter :")
        lines += [f"     {l['page']} / {l['key']} = {l['domain'] or l['kind']}" for l in unknown]
    return "\n".join(lines), unknown


if __name__ == "__main__":
    txt, unknown = report(sys.argv[1])
    print(txt)
    sys.exit(1 if unknown else 0)
