"""Aplica tools/ajustes_manuais.json sobre data/<UF>.json (idempotente):
 - contatos: preenche telefone/e-mail/site de uma paróquia (só campos vazios, ou todos se "sobrescrever": true);
 - indicacoes: coloca paróquias indicadas na frente da lista de um hospital (marca curadoria=1).
Uso: python3 aplicar_ajustes.py <pasta data>"""
import sys, json, os, math
pasta = sys.argv[1]; cfg = json.load(open(os.path.join(os.path.dirname(__file__), "ajustes_manuais.json")))
por_uf = {}
for c in cfg.get("contatos", []): por_uf.setdefault(c["uf"], {"c": [], "i": []})["c"].append(c)
for i in cfg.get("indicacoes", []): por_uf.setdefault(i["uf"], {"c": [], "i": []})["i"].append(i)
for uf, a in por_uf.items():
    f = os.path.join(pasta, f"{uf}.json"); d = json.load(open(f)); mudou = 0
    for c in a["c"]:
        achou = [p for p in d["p"] if p[0] == c["nome"] and p[1] == c["cidade"]]
        if not achou: print("!! paróquia não encontrada:", c["nome"]); continue
        for p in achou:
            for campo, idx in (("tel", 3), ("email", 4), ("site", 5)):
                if c.get(campo) and (c.get("sobrescrever") or not p[idx]) and p[idx] != c[campo]: p[idx] = c[campo]; mudou += 1
    for ind in a["i"]:
        h = next((x for x in d["h"] if x[0] == ind["hospital_id"]), None)
        if not h: print("!! hospital não encontrado:", ind["hospital_id"]); continue
        if ind.get("nome") and h[1] != ind["nome"]: h[1] = ind["nome"]; mudou += 1
        if ind.get("bairro") and h[4] != ind["bairro"]: h[4] = ind["bairro"]; mudou += 1
        forcadas = []
        for nome in ind["paroquias"]:
            idxs = [i for i, p in enumerate(d["p"]) if p[0] == nome and p[1] == d["c"][h[3]]]
            if not idxs: print("!! paróquia da indicação não encontrada:", nome); continue
            dist = lambda p: 12742 * math.asin(math.sqrt(math.sin(math.radians(p[6] - h[8]) / 2) ** 2 + math.cos(math.radians(h[8])) * math.cos(math.radians(p[6])) * math.sin(math.radians(p[7] - h[9]) / 2) ** 2))
            i = min(idxs, key=lambda i: dist(d["p"][i])); forcadas.append([i, round(dist(d["p"][i]), 2), 1])
        novo = (forcadas + [x for x in h[11] if x[0] not in [y[0] for y in forcadas]])[:3]
        if novo != h[11]: h[11] = novo; mudou += 1
    json.dump(d, open(f, "w"), ensure_ascii=False, separators=(",", ":")); print(uf, "ajustes aplicados:", mudou)
