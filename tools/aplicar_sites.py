"""Aplica o resultado da verificação nos dados: corrige o endereço, ou remove o site (e portanto o botão) quando não abre.
Uso: python3 aplicar_sites.py <pasta data> [--r1 a.jsonl b.jsonl ...] [--r2 c.jsonl ...] [--confirma d.jsonl ...]
 --r1       saídas de verificar_sites.py (1ª rodada; vários arquivos são somados)
 --r2       saídas de verificar_sites_2.py (retestes dos que falharam)
 --confirma saídas de uma verificação de confirmação (mesmo formato da 1ª rodada, sobre os endereços já corrigidos)
Regras: ok → usa o endereço que funcionou (prefere https); bloqueio_bot → mantém; recuperado → usa a variação que abriu
(minúsculas, com/sem www; NÃO aceita cair na página inicial genérica do domínio); certificado inválido ou quebrado → remove; sites com '@' (e-mail colado) → remove;
domínios à venda/estacionados → remove.
Confirmação: se cobre o site, manda ela: ok/bloqueio_bot → mantém; fora_do_ar → remove. Se não cobre, vale o resultado das rodadas anteriores.
Sites sem nenhum resultado ficam como estão (e são contados em "sem_resultado")."""
import sys, json, glob, re, collections
if len(sys.argv) < 2: sys.exit(__doc__)
data = sys.argv[1]; grupos = {"--r1": [], "--r2": [], "--confirma": []}; cur = None
for a in sys.argv[2:]:
    if a in grupos: cur = a
    elif cur: grupos[cur].append(a)
    else: sys.exit(__doc__)
def linhas(fs):
    for f in fs:
        for l in open(f):
            if l.strip(): yield json.loads(l)
novo = {}; resumo = collections.Counter()
PARK = re.compile(r"(sedo\.com|hugedomains|godaddy\.com/domains|afternic|dan\.com|bodis|parkingcrew|domainmarket|uol\.host|this domain|//ww\d+\.)", re.I)
for r in linhas(grupos["--r1"]):
    if r["status"] in ("ok", "bloqueio_bot"):
        novo[r["site"]] = "" if PARK.search(r.get("final", "")) else r["tentado"]
for r in linhas(grupos["--r2"]):
    novo[r["site"]] = r["novo"] if r["status"] == "recuperado" and not r.get("so_dominio") and not PARK.search(r.get("final", "")) else ""
conf = {}
for r in linhas(grupos["--confirma"]):
    conf[r["site"]] = "" if r["status"] == "fora_do_ar" or PARK.search(r.get("final", "")) else r["site"]
for f in glob.glob(f"{data}/[A-Z][A-Z].json"):
    d = json.load(open(f))
    for p in d["p"]:
        s = p[5]
        if not s: continue
        n = novo.get(s); resultado = n is not None
        if n is None: n = s
        if n and (n in conf or s in conf):
            if (conf[n] if n in conf else conf[s]) == "": n = ""
            resultado = True
        if not resultado: resumo["sem_resultado"] += 1; continue
        if "@" in n: n = ""
        if n != s: p[5] = n; resumo["removido" if not n else "corrigido"] += 1
        else: resumo["igual"] += 1
    json.dump(d, open(f, "w"), ensure_ascii=False, separators=(",", ":"))
print(dict(resumo))
