"""Gera data/<UF>.json e data/index.json (hospitais + 3 paróquias mais próximas de cada um).
Uso: python3 build_dados.py <hosp.pkl> <ov_br.parquet> <municipios.csv> <pasta_saida>"""
import sys, re, json, os, numpy as np, pandas as pd, duckdb, unicodedata
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
nao = P.nome.fillna("").map(norm).str.contains(r"assembleia|batista|universal|presbiter|adventista|evangel|metodista|congregacao crista|testemunha|luterana|mórmon|mormon|reino de deus", regex=True)
P = P[(cat | (P.cat.eq("religious_organization") & nome_cat)) & ~nao & P.nome.notna()].copy()
P = P[P.lat.between(-34, 6) & P.lng.between(-75, -33)]
def tc(s):
    s = re.sub(r"\s+", " ", str(s)).strip()
    if s.isupper() or s.islower():
        s = s.title(); s = re.sub(r"\b(De|Da|Do|Das|Dos|E)\b", lambda m: m.group(1).lower(), s)
    return s
P["nome"] = P.nome.map(tc)
P["k"] = P.nome.map(norm) + P.lat.round(3).astype(str) + P.lng.round(3).astype(str)  # ~100 m
P = P.sort_values("tel", na_position="last").drop_duplicates("k").reset_index(drop=True)
for c in ["tel", "email", "site", "end", "cidade"]: P[c] = P[c].fillna("")
print(len(P), "paróquias/igrejas católicas;", int((P.tel != "").sum()), "com telefone;", int((P.site != "").sum()), "com site")

# ---- 3 mais próximas ----
R = np.radians
plat, plng = R(P.lat.values), R(P.lng.values)
# capelas/comunidades pesam 3 km a mais no ranking (um padre costuma vir da paróquia-sede)
pen = P.nome.map(norm).str.contains(r"\b(capela|oratorio|comunidade|casa)\b", regex=True).values * 3.0
cur = json.load(open(os.path.join(os.path.dirname(__file__), "curadoria.json")))
near = []
for i in range(0, len(H), 400):
    b = H.iloc[i:i + 400]; la, lo = R(b.lat.values)[:, None], R(b.lng.values)[:, None]
    a = np.sin((plat - la) / 2) ** 2 + np.cos(la) * np.cos(plat) * np.sin((plng - lo) / 2) ** 2
    D = 12742 * np.arcsin(np.sqrt(a))
    idx = np.argpartition(D + pen, 3, axis=1)[:, :3]
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
                row = row[:3]
        near.append(row)
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
