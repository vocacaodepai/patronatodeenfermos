"""Aplica o resultado da verificação nos dados: corrige o endereço, ou remove o site (e portanto o botão) quando não abre.
Uso: python3 aplicar_sites.py <pasta data> <sites_check.jsonl> <sites_check2.jsonl>
Regras: ok → usa o endereço que funcionou (prefere https); bloqueio_bot → mantém; recuperado → usa a variação que abriu
(minúsculas, com/sem www; NÃO aceita cair na página inicial genérica do domínio); certificado inválido ou quebrado → remove; sites com '@' (e-mail colado) → remove;
domínios à venda/estacionados → remove."""
import sys, json, glob, re, collections
data, c1, c2 = sys.argv[1:4]
novo = {}; resumo = collections.Counter()
PARK = re.compile(r"(sedo\.com|hugedomains|godaddy\.com/domains|afternic|dan\.com|bodis|parkingcrew|domainmarket|uol\.host|this domain)", re.I)
for l in open(c1):
    r = json.loads(l)
    if r["status"] in ("ok", "bloqueio_bot"):
        novo[r["site"]] = "" if PARK.search(r.get("final", "")) else r["tentado"]
for l in open(c2):
    r = json.loads(l)
    novo[r["site"]] = r["novo"] if r["status"] == "recuperado" and not r.get("so_dominio") and not PARK.search(r.get("final", "")) else ""
for f in glob.glob(f"{data}/[A-Z][A-Z].json"):
    d = json.load(open(f)); mud = 0
    for p in d["p"]:
        s = p[5]
        if not s: continue
        n = novo.get(s)
        if n is None: resumo["sem_resultado"] += 1; continue
        if "@" in n: n = ""
        if n != s: p[5] = n; mud += 1; resumo["removido" if not n else "corrigido"] += 1
        else: resumo["igual"] += 1
    json.dump(d, open(f, "w"), ensure_ascii=False, separators=(",", ":"))
print(dict(resumo))
