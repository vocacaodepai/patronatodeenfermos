"""Une registros da MESMA igreja (ex.: 'Paróquia X' e 'Paróquia X - Bairro' a 12 m; 'Igreja N. S. de Fátima' e 'Santuário N. S. de Fátima'),
corrige o tipo no nome (Paróquia → Santuário/Basílica) quando o próprio perfil da igreja (site/e-mail/rede social) diz isso,
e conserta telefones sem DDD. Usado por build_dados.py, ANTES de calcular as igrejas mais próximas de cada hospital."""
import re, unicodedata, math, collections
import numpy as np

def norm(s): return re.sub(r"[^a-z0-9 ]", " ", unicodedata.normalize("NFD", str(s or "")).encode("ascii", "ignore").decode().lower())
def ascii_(s): return re.sub(r"[^a-z]", "", unicodedata.normalize("NFD", str(s or "")).encode("ascii", "ignore").decode().lower())

TIPO = {"santuario": ("santuario", 5), "basilica": ("basilica", 5), "concatedral": ("catedral", 4), "catedral": ("catedral", 4),
        "paroquia": ("paroquia", 3), "p": ("paroquia", 3), "quase": ("paroquia", 3), "matriz": ("igreja", 2), "igreja": ("igreja", 2), "capela": ("capela", 1), "comunidade": ("comunidade", 0)}
SANTO = {"nossa", "nosso", "sao", "santo", "santa", "santos", "sagrado", "sagrada", "imaculado", "imaculada", "divino", "bom", "menino", "cristo", "senhor", "senhora", "espirito"}
GEN = {"paroquia", "igreja", "santuario", "basilica", "capela", "matriz", "comunidade", "catedral", "concatedral", "de", "da", "do", "das", "dos",
       "e", "a", "o", "em", "n", "s", "sra", "par", "pessoal", "nossa", "senhora", "nosso", "senhor"}
GENERICOS = {"jesus", "maria", "senhor", "senhora", "santissimo", "santissima", "sagrado", "coracao", "divino", "espirito", "menino"}

def tipo_de(nome):
    w = norm(nome).split()
    if not w: return None, 2
    if w[0] in TIPO: return TIPO[w[0]]
    if w[0] in SANTO: return ("outro", 2)
    return None, 0        # começa por outra coisa (fraternidade, pastoral, seminário...): nunca une

def nucleo(nome, cidade=""):
    n = re.split(r"\s[-–|/]\s|,|\(", nome)[0]
    cid = {w for w in norm(cidade).split() if len(w) >= 4}                 # o nome da cidade no fim do nome não distingue igrejas
    base = [w for w in norm(n).split() if w not in GEN]
    sem_cidade = [w for w in base if w not in cid]
    return sem_cidade or base                                               # se a igreja se chama como a cidade (Santa Teresa, Mercês...), mantém

def tem_sufixo(nome): return bool(re.search(r"\s[-–|/]\s|,|\(", nome))

def km(a, b):
    r = math.radians; x = math.sin((r(b[0]) - r(a[0])) / 2) ** 2 + math.cos(r(a[0])) * math.cos(r(b[0])) * math.sin((r(b[1]) - r(a[1])) / 2) ** 2
    return 12742 * math.asin(math.sqrt(x))

def mesmo_templo(i, j, P, tp, nu):
    if tp[i][0] is None or tp[j][0] is None: return False
    ti, tj = tp[i][0], tp[j][0]
    if (ti in ("capela", "comunidade") or tj in ("capela", "comunidade")) and ti != tj: return False
    ci, cj = norm(P.cidade.iat[i]), norm(P.cidade.iat[j])
    if ci and cj and ci != cj: return False
    a, b = set(nu[i]), set(nu[j])
    if not a or not b: return False
    d = km((P.lat.iat[i], P.lng.iat[i]), (P.lat.iat[j], P.lng.iat[j]))
    ei, ej = norm(P.end.iat[i]), norm(P.end.iat[j])
    if a == b:
        if ei and ei == ej and len(ei) >= 8: return d <= 1.5          # mesmo nome e mesmo endereço (coordenadas diferentes): é a mesma igreja
        return d <= 0.40
    if (a <= b or b <= a) and min(len(a), len(b)) >= 2: return d <= 0.20
    return d <= 0.10 and len(a & b) / len(a | b) >= 0.75

def tel_valido(t): return bool(re.fullmatch(r"\+55\d{10,11}", t or ""))

def unir(P):
    """Devolve (P_sem_duplicatas, relatorio)."""
    P = P.reset_index(drop=True); n = len(P)
    tp = [tipo_de(x) for x in P.nome]; nu = [nucleo(x, c) for x, c in zip(P.nome, P.cidade)]
    grade = collections.defaultdict(list)
    for i in range(n): grade[(int(P.lat.iat[i] / 0.01), int(P.lng.iat[i] / 0.01))].append(i)
    pai = list(range(n))
    def raiz(x):
        while pai[x] != x: pai[x] = pai[pai[x]]; x = pai[x]
        return x
    for i in range(n):
        if tp[i][0] is None: continue
        gx, gy = int(P.lat.iat[i] / 0.01), int(P.lng.iat[i] / 0.01)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for j in grade.get((gx + dx, gy + dy), []):
                    if j > i and mesmo_templo(i, j, P, tp, nu): pai[raiz(j)] = raiz(i)
    grupos = collections.defaultdict(list)
    for i in range(n): grupos[raiz(i)].append(i)
    manter, rel_ex = [], []
    for r, mem in grupos.items():
        if len(mem) == 1: manter.append(mem[0]); continue
        # representante: tipo mais específico > nome sem sufixo > telefone válido > e-mail > site > nome curto
        mem.sort(key=lambda i: (-tp[i][1], tem_sufixo(P.nome.iat[i]), not tel_valido(P.tel.iat[i]), P.email.iat[i] == "", P.site.iat[i] == "", len(P.nome.iat[i])))
        rep = mem[0]
        for campo in ("tel", "email", "site", "end"):
            if not P[campo].iat[rep] or (campo == "tel" and not tel_valido(P.tel.iat[rep])):
                for o in mem[1:]:
                    v = P[campo].iat[o]
                    if v and (campo != "tel" or tel_valido(v)): P.at[rep, campo] = v; break
        manter.append(rep)
        if len(rel_ex) < 400: rel_ex.append({"mantida": P.nome.iat[rep], "unidas": [P.nome.iat[o] for o in mem[1:]], "cidade": P.cidade.iat[rep]})
    P2 = P.iloc[sorted(manter)].reset_index(drop=True)
    return P2, {"registros_antes": n, "registros_depois": len(P2), "removidos": n - len(P2), "exemplos": rel_ex}

def corrigir_tipo_pelo_perfil(P):
    """'Paróquia/Igreja/Capela X' cujo site/e-mail/rede social diz 'santuario'/'basilica' + parte distintiva do nome → 'Santuário/Basílica X'."""
    P = P.copy(); mud = []
    for i in range(len(P)):
        nome = P.nome.iat[i]; tp = tipo_de(nome)[0]
        if tp not in ("paroquia", "igreja", "capela"): continue
        if re.search(r"santu[aá]rio|bas[ií]lica", nome, re.I): continue     # o nome já diz Santuário/Basílica ("Paróquia Santuário X", "Paróquia e Santuário X")
        slug = ascii_(f"{P.site.iat[i]} {P.email.iat[i]} {P.social.iat[i] if 'social' in P else ''}")
        novo = "Santuário" if "santuario" in slug else ("Basílica" if "basilica" in slug else None)
        if not novo: continue
        dist = [w for w in nucleo(nome, P.cidade.iat[i]) if len(w) >= 6 and w not in GENERICOS]
        if not dist or not any(w in slug for w in dist): continue
        n2 = re.sub(r"^(par[oó]quia|igreja matriz|igreja|matriz|capela)\b", novo, nome, flags=re.I)
        if n2 != nome: P.at[P.index[i], "nome"] = n2; mud.append((nome, n2, P.cidade.iat[i]))
    return P, mud

def corrigir_telefones(P, ddd_por_cidade):
    """+55 + (DDD)+8/9 dígitos. Sem DDD (8/9 dígitos) → usa o DDD do município; se o número ficar inválido, o telefone é removido (botão 'ligar' não pode quebrar)."""
    P = P.copy(); corr = rem = 0
    for i in range(len(P)):
        t = P.tel.iat[i]
        if not t: continue
        dg = re.sub(r"\D", "", t)
        nac = dg[2:] if dg.startswith("55") and len(dg) >= 12 else dg
        if len(nac) in (8, 9):
            d = ddd_por_cidade.get((str(P.uf.iat[i] or "").upper(), norm(P.cidade.iat[i])))
            if d: nac = str(d) + nac
        if len(nac) in (10, 11) and not nac.startswith("0"):
            novo = "+55" + nac
            if novo != t: P.at[P.index[i], "tel"] = novo; corr += 1
        else:
            P.at[P.index[i], "tel"] = ""; rem += 1
    return P, {"telefones_corrigidos": corr, "telefones_removidos": rem}
