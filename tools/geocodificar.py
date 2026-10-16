"""Corrige coordenadas suspeitas usando Nominatim (OpenStreetMap), 1 consulta/s, com retomada.
Uso: python3 geocodificar.py susp.pkl saida.jsonl [--amostra N]   (--amostra: audita N locais NÃO suspeitos)"""
import sys, re, json, time, os, unicodedata, requests, pandas as pd
src, out = sys.argv[1:3]
amostra = int(sys.argv[sys.argv.index("--amostra") + 1]) if "--amostra" in sys.argv else 0
H = pd.read_pickle(src)
S = H[~H.suspeita].sample(amostra, random_state=7) if amostra else H[H.suspeita]
norm = lambda s: re.sub(r"[^a-z0-9 ]", " ", unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode().lower())
STOP = set("hospital clinica clinicas de da do das dos e municipal estadual federal geral regional unidade mista santa sao nossa senhora casa saude centro instituto fundacao pronto socorro maternidade ltda".split())
sig = lambda s: {w for w in norm(s).split() if w not in STOP and len(w) > 2}
done = set()
if os.path.exists(out):
    for l in open(out): done.add(json.loads(l)["id"])
ses = requests.Session(); ses.headers["User-Agent"] = "PatronatoDeEnfermos/1.0 (+https://github.com/vocacaodepai/patronatodeenfermos)"
last = [0]
def get(params):
    w = 1.1 - (time.time() - last[0]); w > 0 and time.sleep(w)
    for t in range(4):
        try:
            r = ses.get("https://nominatim.openstreetmap.org/search", params=dict(params, format="jsonv2", countrycodes="br", addressdetails=1, limit=5), timeout=30); last[0] = time.time()
            if r.status_code == 200: return r.json()
            time.sleep(5 * (t + 1))
        except Exception: time.sleep(5 * (t + 1))
    return []
f = open(out, "a")
for n, r in enumerate(S.itertuples()):
    if r.id in done: continue
    vb = f"{r.clng-.3},{r.clat+.3},{r.clng+.3},{r.clat-.3}"
    res = None
    for c in get({"q": f"{r.nomeh}, {r.cidade}", "viewbox": vb, "bounded": 1}):
        if c.get("category") in ("amenity", "healthcare") and sig(r.nomeh) & sig(c.get("name", "")):
            res = (c, "nome"); break
    if not res and r.end:
        m = re.match(r"(.*?),\s*(\S+)$", r.end); rua, num = (m.group(1), m.group(2)) if m else (r.end, "")
        for c in get({"street": f"{num} {rua}".strip(), "city": r.cidade, "state": r.uf, "viewbox": vb, "bounded": 1}):
            ad = c.get("address", {})
            if not (sig(rua) & sig(ad.get("road", "") + " " + c.get("name", ""))): continue
            hn = norm(ad.get("house_number", "")).strip()
            res = (c, "endereco" if num and hn == norm(num).strip() else "rua"); break
    rec = {"id": r.id, "cnes": [r.lat, r.lng]}
    if res: rec.update(lat=float(res[0]["lat"]), lng=float(res[0]["lon"]), metodo=res[1], achado=res[0].get("display_name", "")[:140])
    f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush()
    if n % 50 == 0: print(n, len(S), flush=True)
