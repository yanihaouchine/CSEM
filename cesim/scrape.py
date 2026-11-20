"""Télécharge les résultats (Excel + page imprimable) de chaque tour."""
import json
import re
import sys

from bs4 import BeautifulSoup

from cesim.client import BASE, ROOT, session

RAW = ROOT / "data" / "raw"


def fetch_round(s, idx):
    r = s.get(BASE + "/ul/Results?sim=gc&panel=overview")
    m = re.search(r"'\./(Results\?\d+-1\.0-panel-round~select&sim=gc&panel=overview&panel:round-select=)'", r.text)
    r = s.get(BASE + "/ul/" + m.group(1) + str(idx))
    sel = re.search(r'<option selected="selected" value="(\d+)">([^<]+)</option>\s*(?:</select>)?', r.text[r.text.find("round-select"):])
    m = re.search(r"'\./(Results\?\d+--panel-download_to_excel&sim=gc&panel=overview)'", r.text)
    x = s.get(BASE + "/ul/" + m.group(1))
    ext = "xlsx" if x.content[:2] == b"PK" else "xls"
    (RAW / f"round_{idx}.{ext}").write_bytes(x.content)
    p = s.get(BASE + "/results/PrintablePage")
    (RAW / f"round_{idx}.html").write_text(p.text)
    rows = [[td.get_text(" ", strip=True).replace("\xa0", " ") for td in tr.find_all("td")] for tr in BeautifulSoup(p.text, "html.parser").find_all("tr")]
    json.dump(rows, open(RAW / f"round_{idx}.json", "w"), ensure_ascii=False)
    return sel.group(2) if sel else None, len(x.content), x.headers.get("content-type"), len(p.text)


def n_rounds(s):
    """Nombre d'entrées du sélecteur de tour (situation initiale comprise)."""
    r = s.get(BASE + "/ul/Results?sim=gc&panel=overview")
    sel = BeautifulSoup(r.text, "html.parser").find("select", attrs={"name": "panel:round-select"})
    return len(sel.find_all("option"))


if __name__ == "__main__":
    s = session()
    n = n_rounds(s)
    todo = [int(a) for a in sys.argv[1:]] or [i for i in range(n) if not (RAW / f"round_{i}.json").exists()]
    for idx in todo:
        print(idx, fetch_round(s, idx))
    if todo and todo[-1] != n - 1:
        fetch_round(s, n - 1)  # laisser la session sur le dernier tour
    print("tours disponibles :", n)
