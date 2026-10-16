"""Testa os links de site das paróquias. Uso: python3 verificar_sites.py <pasta data> <saida.jsonl> [--workers 40]
Classifica: ok · bloqueio_bot (403/429/999: o servidor responde, só barra robôs) · fora_do_ar (DNS, conexão, SSL, timeout, 4xx/5xx)."""
import sys, re, json, glob, os, requests, urllib3
from concurrent.futures import ThreadPoolExecutor
urllib3.disable_warnings()
data, out = sys.argv[1:3]
IGN = []   # --ignorar a.jsonl b.jsonl: não testa de novo os sites que já têm resultado nesses arquivos
if "--ignorar" in sys.argv:
    for a in sys.argv[sys.argv.index("--ignorar") + 1:]:
        if a.startswith("--"): break
        IGN.append(a)
W = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 40
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36", "Accept": "text/html,*/*"}
def limpa(s):
    s = s.strip().split()[0] if s.strip() else ""
    return s if re.match(r"^https?://", s, re.I) else "https://" + s.lstrip("/")
def tenta(u):
    try:
        r = requests.get(u, headers=H, timeout=(6, 10), allow_redirects=True, stream=True, verify=True)
        c = r.status_code; fin = r.url; r.close(); return c, fin, ""
    except requests.exceptions.SSLError as e: return 0, u, "ssl"
    except requests.exceptions.ConnectionError as e: return 0, u, "conexao/dns"
    except requests.exceptions.Timeout: return 0, u, "timeout"
    except Exception as e: return 0, u, type(e).__name__
def checa(s):
    base = limpa(s); cands = [base]
    if base.startswith("http://"): cands = ["https://" + base[7:], base]      # prefere https
    ultimo = (0, base, "")
    for u in cands:
        c, fin, err = tenta(u); ultimo = (c, fin, err)
        if 200 <= c < 400: return {"site": s, "status": "ok", "codigo": c, "final": fin, "tentado": u}
        if c in (401, 403, 429, 999): return {"site": s, "status": "bloqueio_bot", "codigo": c, "final": fin, "tentado": u}
    c, fin, err = ultimo
    return {"site": s, "status": "fora_do_ar", "codigo": c, "motivo": err or f"HTTP {c}", "tentado": cands[-1]}
sites = sorted({p[5] for f in glob.glob(f"{data}/[A-Z][A-Z].json") for p in json.load(open(f))["p"] if p[5]})
feitos = set()
for f in IGN + [out]:
    if os.path.exists(f): feitos |= {json.loads(l)["site"] for l in open(f)}
fila = [s for s in sites if s not in feitos]; print(len(sites), "sites;", len(fila), "a testar", flush=True)
with open(out, "a") as fo, ThreadPoolExecutor(W) as ex:
    for i, r in enumerate(ex.map(checa, fila)):
        fo.write(json.dumps(r, ensure_ascii=False) + "\n"); fo.flush()
        if i % 200 == 0: print(i, len(fila), flush=True)
