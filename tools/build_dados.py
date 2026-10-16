"""Gera data/<UF>.json e data/index.json (hospitais + as N_IGREJAS paróquias mais próximas de cada um).
Uso: python3 build_dados.py <hosp.pkl> <ov_br.parquet> <municipios.csv> <pasta_saida>"""
import sys, re, json, os, numpy as np, pandas as pd, duckdb, unicodedata
N_IGREJAS = int(os.environ.get("N_IGREJAS", 5))   # vínculos por hospital
PEN_CAPELA = 3.0     # km a mais no ranking: capela/oratório/comunidade/casa (o padre costuma vir da paróquia-sede)
PEN_NAO_PAROQUIA = 6.0   # km a mais: pastoral, grupo de oração, movimento, seminário, colégio... (só entram se não houver melhor)
DUP_M = 300          # mesmo nome normalizado a menos de 300 m = duplicata
hp, ovp, munp, out = sys.argv[1:5]
geo_files = sys.argv[5:]   # opcional: geo_fix.jsonl (saída de geocodificar.py)
os.makedirs(out, exist_ok=True)
norm = lambda s: re.sub(r"[^a-z0-9 ]", " ", unicodedata.normalize("NFD", str(s or "")).encode("ascii", "ignore").decode().lower())
H = pd.read_pickle(hp).reset_index(drop=True)
# ---- precisão da localização: 0 exata · 1 pela rua · 2 pelo bairro · 3 pelo município ----
H["pr"] = np.where(H.aprox, 3, 0)
geo = {}
for gf in geo_files:
    for l in open(gf):
        g = json.loads(l)
        if "lat" in g: geo[g["id"]] = g
for i, r in H.iterrows():
    g = geo.get(r.id)
    if g and g["metodo"] in ("nome", "endereco"): H.loc[i, ["lat", "lng", "pr"]] = [g["lat"], g["lng"], 0]
    elif g: H.loc[i, ["lat", "lng", "pr"]] = [g["lat"], g["lng"], 1]
if "suspeita" in H:
    ruim = H.suspeita & ~H.id.isin(geo) & (H.fora_do_bairro | H.ponto_repetido | H.longe_cidade)
    bons = H[~H.suspeita & (H.pr == 0)].groupby("chave")[["lat", "lng"]].median().join(H[~H.suspeita & (H.pr == 0)].groupby("chave").id.count().rename("n"))
    for i, r in H[ruim].iterrows():
        if r.chave in bons.index and bons.loc[r.chave, "n"] >= 2: H.loc[i, ["lat", "lng", "pr"]] = [bons.loc[r.chave, "lat"], bons.loc[r.chave, "lng"], 2]
        else: H.loc[i, ["lat", "lng", "pr"]] = [r.clat, r.clng, 3]
print("precisão:", H.pr.value_counts().sort_index().to_dict())

# ---- paróquias ----
P = duckdb.sql(f"select * from '{ovp}'").df()
cat = P.cat.eq("roman_catholic_place_of_worship")
nome_cat = P.nome.fillna("").map(norm).str.contains(r"\b(paroquia|catedral|basilica|santuario|igreja catolica|matriz)\b", regex=True)
nao = P.nome.fillna("").map(norm).str.contains(r"assembleia|batista|universal|presbiter|adventista|evangel|metodista|congregacao crista|testemunha|luterana|mórmon|mormon|reino de deus|catedral do reino", regex=True)
P = P[(cat | P.cat.eq("religious_organization")) & ~nao & P.nome.notna()].copy()   # registros "religious_organization" só ficam se tiverem marca católica clara (abaixo)
P = P[P.lat.between(-34, 6) & P.lng.between(-75, -33)]

# ---- só Igreja Católica Apostólica ROMANA: tira ICAB, ortodoxas, anglicanas, independentes etc. (tools/exclusoes_nao_romanas.json) ----
_cfg = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "exclusoes_nao_romanas.json"))); _rx = _cfg["grupos"]
_tn = P.nome.fillna("").map(norm); _ts = P.site.fillna("").map(norm)
_fora = pd.Series(False, index=P.index); _contagem = {}
for _g, _r in _rx.items():
    _m = pd.Series(False, index=P.index)
    for _p in _r.get("nome", []): _m |= _tn.str.contains(_p, regex=True)
    for _p in _r.get("site", []): _m |= _ts.str.contains(_p, regex=True)
    _contagem[_g] = int((_m & ~_fora).sum()); _fora |= _m
# ---- exige sinal de que é católica romana (a regra é "só entra com evidência", não só "sai o que achamos errado") ----
_ex = _cfg["exigir_sinal_catolico"]; _te = P.email.fillna("").map(norm)
_sinal = _tn.str.contains(_ex["nome"], regex=True)   # o NOME precisa indicar igreja/devoção católica; site de diocese sozinho não basta (evita Pascom, CNBB, cúrias, residências)
_ro = P.cat.eq("religious_organization")
_ro_ok = ~_ro | (_tn.str.contains(_ex["religious_organization_exige_nome"], regex=True) & _tn.str.contains(_ex["religious_organization_exige_santo"], regex=True))
_m1 = ~_fora & ~_sinal; _contagem["Sem nenhum sinal de igreja católica no nome/site"] = int(_m1.sum()); _fora |= _m1
_m2 = ~_fora & ~_ro_ok; _contagem["Registro genérico da fonte (religious_organization) sem marca católica clara"] = int(_m2.sum()); _fora |= _m2
print("não romanas retiradas da base:", int(_fora.sum()), "de", len(P), _contagem)
json.dump({"total_antes": len(P), "retiradas": int(_fora.sum()), "por_grupo": _contagem, "exemplos": {g: [] for g in _rx}}, open(os.path.join(os.environ.get("TMPDIR", "/tmp"), "retiradas_nao_romanas.json"), "w"), ensure_ascii=False)
P = P[~_fora].copy()
def tc(s):
    s = re.sub(r"\s+", " ", str(s)).strip()
    if s.isupper() or s.islower():
        s = s.title(); s = re.sub(r"\b(De|Da|Do|Das|Dos|E)\b", lambda m: m.group(1).lower(), s)
    return s
P["nome"] = P.nome.map(tc)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from normalizar_nomes import normalizar as _norm_pt          # nomes em português ANTES de procurar duplicatas ("Church of X" = "Igreja de X")
P["nome"] = [_norm_pt(n, "p", str(u or "").upper()) for n, u in zip(P.nome, P.uf)]
P["k"] = P.nome.map(norm) + P.lat.round(3).astype(str) + P.lng.round(3).astype(str)  # ~100 m
P = P.sort_values("tel", na_position="last").drop_duplicates("k").reset_index(drop=True)
for c in ["tel", "email", "site", "end", "cidade"]: P[c] = P[c].fillna("")
print(len(P), "paróquias/igrejas católicas;", int((P.tel != "").sum()), "com telefone;", int((P.site != "").sum()), "com site")

# ---- remove quase-duplicatas: mesmo nome normalizado a menos de DUP_M metros (fica a que tem telefone/site) ----
P["nn"] = P.nome.map(norm).str.split().str.join(" ")
P["ord"] = (P.tel == "").astype(int) + (P.site == "").astype(int) * 0.5
drop = set()
for _, g in P.sort_values("ord").groupby("nn"):
    if len(g) < 2: continue
    mant = []
    for j, la, lo in zip(g.index, g.lat, g.lng):
        if any(12742000 * np.arcsin(np.sqrt(np.sin(np.radians(la - a_) / 2) ** 2 + np.cos(np.radians(la)) * np.cos(np.radians(a_)) * np.sin(np.radians(lo - b_) / 2) ** 2)) < DUP_M for a_, b_ in mant): drop.add(j)
        else: mant.append((la, lo))
P = P.drop(index=list(drop)).reset_index(drop=True)
print(len(drop), "quase-duplicatas removidas;", len(P), "restam")

# ---- une a MESMA igreja cadastrada mais de uma vez; corrige Paróquia→Santuário/Basílica pelo perfil; conserta telefones sem DDD ----
import unir_duplicatas as _ud
for c in ["tel", "email", "site", "end", "cidade", "social"]:
    if c in P: P[c] = P[c].fillna("")
P, _rel_u = _ud.unir(P)
P, _mud = _ud.corrigir_tipo_pelo_perfil(P)
_UF = {"11":"RO","12":"AC","13":"AM","14":"RR","15":"PA","16":"AP","17":"TO","21":"MA","22":"PI","23":"CE","24":"RN","25":"PB","26":"PE","27":"AL","28":"SE","29":"BA","31":"MG","32":"ES","33":"RJ","35":"SP","41":"PR","42":"SC","43":"RS","50":"MS","51":"MT","52":"GO","53":"DF"}
_mun = pd.read_csv(munp, dtype={"codigo_ibge": str, "codigo_uf": str}); _ddd = {(_UF.get(r.codigo_uf, ""), norm(r.nome)): int(r.ddd) for r in _mun.itertuples()}
P, _rel_t = _ud.corrigir_telefones(P, _ddd)
print("igrejas duplicadas unidas:", _rel_u["removidos"], "| rótulo corrigido para Santuário/Basílica:", len(_mud), "|", _rel_t)
json.dump({"unir": _rel_u, "rotulo": _mud, "telefones": _rel_t}, open(os.environ.get("REL_UNIR", "/tmp/relatorio_unir.json"), "w"), ensure_ascii=False)

# ---- as N_IGREJAS mais próximas ----
R = np.radians
plat, plng = R(P.lat.values), R(P.lng.values)
nn = P.nn
pen = nn.str.contains(r"\b(?:capela|oratorio|comunidade|casa)\b", regex=True).values * PEN_CAPELA
pen = pen + nn.str.contains(r"\b(?:pastoral|pastorais|grupo|terco|juventude|ministerio|paroquianos|diocese|curia|mitra|movimento|seminario|seminarista|colegio|escola|missao|missoes|renovacao carismatica|retiro|cursilho|legiao de maria|apostolado|associacao|fundacao|centro de formacao|casa de retiro)\b", regex=True).values * PEN_NAO_PAROQUIA
cur = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "curadoria.json")))
K = 80
near = []
for i in range(0, len(H), 400):
    b = H.iloc[i:i + 400]; la, lo = R(b.lat.values)[:, None], R(b.lng.values)[:, None]
    a = np.sin((plat - la) / 2) ** 2 + np.cos(la) * np.cos(plat) * np.sin((plng - lo) / 2) ** 2
    D = 12742 * np.arcsin(np.sqrt(a))
    idx = np.argpartition(D + pen, K, axis=1)[:, :K]
    for r in range(len(b)):
        cand = sorted(idx[r], key=lambda j: D[r, j] + pen[j]); row = [[int(j), round(float(D[r, j]), 2), 0] for j in cand]
        nm = norm(b.iloc[r].nomeh)
        for rule in cur:
            if re.search(rule["hospital"], nm):
                forced = []
                for pat in rule["paroquias"]:
                    m = [j for j in np.where(D[r] <= rule["raio_km"])[0] if pat in norm(P.nome[j])]
                    if m: j = min(m, key=lambda j: D[r, j]); forced.append([int(j), round(float(D[r, j]), 2), 1])
                row = forced + [x for x in row if x[0] not in [f[0] for f in forced]]
        # escolhe pelas pontuações (distância + penalidades), mas mostra em ordem de distância; curadoria (c=1) vai na frente
        nf = sum(1 for x in row if x[2] == 1)
        near.append(row[:nf] + sorted(row[nf:N_IGREJAS], key=lambda x: x[1]))
H["par"] = near

# ---- saída por estado ----
M = pd.read_csv(munp, dtype={"codigo_ibge": str})
idx = []
for uf, g in H.groupby("uf"):
    used = sorted({p[0] for r in g.par for p in r}); remap = {j: n for n, j in enumerate(used)}
    cidades = sorted(g.cidade.unique()); ci = {c: n for n, c in enumerate(cidades)}
    h = [[r.id, r.nomeh, r.tipo, ci[r.cidade], r.bairro, r.end, r.tel, r.email, round(r.lat, 5), round(r.lng, 5), int(r.pr), [[remap[p[0]], p[1], p[2]] for p in r.par]] for r in g.itertuples()]
    p = [[P.nome[j], P.cidade[j], P.end[j], P.tel[j], P.email[j], P.site[j], round(P.lat[j], 5), round(P.lng[j], 5)] for j in used]
    json.dump({"uf": uf, "c": cidades, "h": h, "p": p}, open(f"{out}/{uf}.json", "w"), ensure_ascii=False, separators=(",", ":"))
    for c, gg in g.groupby("cidade"): idx.append([uf, round(gg.lat.mean(), 3), round(gg.lng.mean(), 3)])
    print(uf, len(h), "locais,", len(p), "paróquias,", os.path.getsize(f"{out}/{uf}.json") // 1024, "KB")
json.dump(idx, open(f"{out}/index.json", "w"), separators=(",", ":"))

# ---- nomes em português do Brasil (acentos, tradução de nomes em inglês, caixa, lixo de cadastro) ----
import subprocess
subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "normalizar_nomes.py"), "--pasta", out], check=True)
