"""Enregistre la zone personnelle comme décisions de l'équipe, puis vérifie."""
import re
import sys

from cesim.client import BASE, ROOT, ZONE, active_zone, page_text, session

H = {"Wicket-Ajax": "true", "Wicket-Ajax-BaseURL": "ul/Decisions?sim=gc&panel=decisionchecklist", "X-Requested-With": "XMLHttpRequest"}


def state(s):
    t, h = page_text(s, "decisionchecklist")
    i = t.find("Résultat, k USD")
    nums = re.findall(r"-?\d{1,3}(?: \d{3})+", t[i:i + 90])
    return nums, h, t


def main(tag):
    s = session()
    assert ZONE in active_zone(s), "zone active inattendue"
    nums, h, t = state(s)
    print("avant  (équipe, puis zones personnelles) :", nums[:4])
    (ROOT / "data" / f"decisions_{tag}_avant_enregistrement.txt").write_text(t)
    m = re.search(r'"u":"\./(Decisions\?\d+-1\.0-panel-content-saverow-saveRepeat-1-saveOther&sim=gc&panel=decisionchecklist)"', h)
    r = s.get(BASE + "/ul/" + m.group(1), headers=H)
    assert "en tant que décisions" in r.text, "confirmation inattendue"
    bid = re.search(r'decision-save__button" id="(\w+)">Oui</button>', r.text).group(1)
    seg = r.text[r.text.find(f"Wicket.Event.add('{bid}'"):][:600]
    url = re.search(r"window\.location\.href='\./([^']+)'", seg).group(1)
    s.get(BASE + "/ul/" + url)
    nums, h, t = state(s)
    (ROOT / "data" / f"decisions_{tag}_equipe.txt").write_text(t)
    ok = nums[0] == nums[1]
    print("après  (équipe, puis zones personnelles) :", nums[:4], "| ENREGISTRÉ" if ok else "| ÉCHEC")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main(sys.argv[1] if len(sys.argv) > 1 else "tour") else 1)
