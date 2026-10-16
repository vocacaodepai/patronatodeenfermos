"""2ª rodada para os sites 'fora_do_ar' de verificar_sites.py: tenta variações antes de dar o link como quebrado.
Uso: python3 verificar_sites_2.py <saida_da_1a_rodada.jsonl> <saida2.jsonl>"""
import sys, re, json, os, requests, urllib3
from urllib.parse import urlsplit, urlunsplit
from concurrent.futures import ThreadPoolExecutor
urllib3.disable_warnings()
ent, out = sys.argv[1:3]
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36", "Accept": "text/html,*/*"}
def get(u, t=(8, 18), verify=True):
    try:
        r = requests.get(u, headers=H, timeout=t, allow_redirects=True, stream=True, verify=verify); c, fin = r.status_code, r.url; r.close(); return c, fin
    except Exception: return 0, u
def variantes(s):
    u = s.strip().split()[0]
    if not re.match(r"^https?://", u, re.I): u = "https://" + u.lstrip("/")
    p = urlsplit(u); host = p.netloc.lower(); semwww = host[4:] if host.startswith("www.") else host
    hosts = [host] + ([semwww] if semwww != host else []) + (["www." + host] if not host.startswith("www.") else [])
    caminhos = [p.path or "/"] + (["/"] if (p.path or "/") != "/" else [])
    for cam in caminhos:
        for h in hosts:
            for esq in ("https", "http"):
                yield urlunsplit((esq, h, cam, p.query if cam == p.path else "", "")), cam != (p.path or "/")
def checa(r):
    s = r["site"]; visto = set()
    for u, so_raiz in variantes(s):
        if u in visto: continue
        visto.add(u); c, fin = get(u)
        if 200 <= c < 400: return {"site": s, "status": "recuperado", "novo": u, "final": fin, "codigo": c, "so_dominio": so_raiz}
        if c in (401, 403, 429, 999): return {"site": s, "status": "recuperado", "novo": u, "final": fin, "codigo": c, "so_dominio": so_raiz, "bloqueio_bot": True}
    # certificado inválido: abre com aviso do navegador → melhor não oferecer
    for u, so_raiz in list(variantes(s))[:2]:
        c, fin = get(u, verify=False)
        if 200 <= c < 400: return {"site": s, "status": "certificado_invalido", "tentado": u, "codigo": c}
    return {"site": s, "status": "quebrado", "motivo_1a": r.get("motivo")}
falhos = [json.loads(l) for l in open(ent) if json.loads(l)["status"] == "fora_do_ar"]
feitos = set()
if os.path.exists(out): feitos = {json.loads(l)["site"] for l in open(out)}
fila = [x for x in falhos if x["site"] not in feitos]; print(len(falhos), "falhos;", len(fila), "a retestar", flush=True)
with open(out, "a") as fo, ThreadPoolExecutor(40) as ex:
    for i, r in enumerate(ex.map(checa, fila)):
        fo.write(json.dumps(r, ensure_ascii=False) + "\n"); fo.flush()
        if i % 100 == 0: print(i, len(fila), flush=True)
