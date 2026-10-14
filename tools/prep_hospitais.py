"""Lê o cadastro CNES (Ministério da Saúde) e gera hospitais/clínicas normalizados.
Uso: python3 prep_hospitais.py <cnes_estabelecimentos.csv> <municipios.csv> <saida.pkl>
Fontes: CNES (dadosabertos.saude.gov.br) e municípios IBGE (kelvins/municipios-brasileiros)."""
import sys, re, pandas as pd
cnes, mun, out = sys.argv[1:4]
d = pd.read_csv(cnes, sep=";", dtype=str, low_memory=False, encoding="latin-1")
d = d[d.CO_MOTIVO_DESAB.isna()]
hosp = d.TP_UNIDADE.isin(["5", "7", "15", "62"])
flag = d.ST_ATEND_HOSPITALAR.eq("1.0")
cir = d.ST_CENTRO_CIRURGICO.eq("1.0") & d.TP_UNIDADE.isin(["4", "36", "39"])
d = d[hosp | flag | cir].copy()
d["tipo"] = d.TP_UNIDADE.map({"5": "Hospital", "7": "Hospital especializado", "15": "Unidade mista", "62": "Hospital-dia"}).fillna("Clínica")
M = pd.read_csv(mun, dtype={"codigo_ibge": str, "codigo_uf": str})
M["cod6"] = M.codigo_ibge.str[:6]
UF = {"11":"RO","12":"AC","13":"AM","14":"RR","15":"PA","16":"AP","17":"TO","21":"MA","22":"PI","23":"CE","24":"RN","25":"PB","26":"PE","27":"AL","28":"SE","29":"BA","31":"MG","32":"ES","33":"RJ","35":"SP","41":"PR","42":"SC","43":"RS","50":"MS","51":"MT","52":"GO","53":"DF"}
d = d.merge(M[["cod6", "nome", "latitude", "longitude"]], left_on="CO_IBGE", right_on="cod6", how="left")
d = d[d.nome.notna()]
d["uf"] = d.CO_UF.map(UF)
small = {"DE", "DA", "DO", "DAS", "DOS", "E", "EM", "NA", "NO", "A", "O", "AO", "PARA", "POR", "COM"}
def tc(s):
    if not isinstance(s, str): return ""
    w = re.sub(r"\s+", " ", s.strip()).title().split(" ")
    return " ".join(x.lower() if x.upper() in small and i else x for i, x in enumerate(w))
ACC = {"sao":"São","joao":"João","jose":"José","vitoria":"Vitória","conceicao":"Conceição","cardiaco":"Cardíaco","pronto":"Pronto","maternidade":"Maternidade","clinica":"Clínica","clinicas":"Clínicas","medico":"Médico","medica":"Médica","saude":"Saúde","santissima":"Santíssima","sagrada":"Sagrada","familia":"Família","ortopedico":"Ortopédico","ortopedia":"Ortopedia","pediatrico":"Pediátrico","infantil":"Infantil","universitario":"Universitário","hospitalar":"Hospitalar","oftalmologico":"Oftalmológico","psiquiatrica":"Psiquiátrica","psiquiatrico":"Psiquiátrico","santana":"Sant'Ana","antonio":"Antônio","lourenco":"Lourenço","goncalo":"Gonçalo","goncalves":"Gonçalves","luiz":"Luiz","lucia":"Lúcia","luzia":"Luzia","mario":"Mário","julio":"Júlio","candido":"Cândido","amelia":"Amélia","adventista":"Adventista","evangelico":"Evangélico","filantropico":"Filantrópico","geral":"Geral","regional":"Regional","estadual":"Estadual","municipal":"Municipal","federal":"Federal","militar":"Militar","policia":"Polícia","nossa":"Nossa","senhora":"Senhora","misericordia":"Misericórdia","caridade":"Caridade","beneficencia":"Beneficência","portuguesa":"Portuguesa","portugues":"Português","cancer":"Câncer","oncologico":"Oncológico","oncologia":"Oncologia","cirurgia":"Cirurgia","traumatologia":"Traumatologia","ginecologia":"Ginecologia","obstetricia":"Obstetrícia","pneumologia":"Pneumologia","nefrologia":"Nefrologia","cardiologia":"Cardiologia","neurologia":"Neurologia","oftalmologia":"Oftalmologia","unimed":"Unimed","ana":"Ana","helena":"Helena","benedito":"Benedito","vicente":"Vicente","paulo":"Paulo","francisco":"Francisco","camilo":"Camilo","rita":"Rita","terezinha":"Terezinha","teresa":"Teresa","tereza":"Tereza"}
def acc(s):
    return re.sub(r"[A-Za-zÀ-ÿ']+", lambda m: ACC.get(m.group(0).lower(), m.group(0)), s)
def nome_h(s):
    s = re.sub(r"^(SMS|SES|SESAU|SEMSA|FMS)\s+([A-Z]{2}\s+)?", "", str(s).strip(), flags=re.I)
    s = tc(s)
    s = re.sub(r"\b(D|O|L)'([a-z])", lambda m: m.group(1) + "'" + m.group(2).upper(), s)
    s = re.sub(r"\b(Barra|Copa|Rios|Quinta|Vila|Cidade|Nova|Rede|Estrada|Santa|Sao|São)\s+Dor\b", lambda m: m.group(1) + " D'Or", s)
    s = re.sub(r"\b(Ii|Iii|Iv|Vi|Vii|Viii|Ix)\b", lambda m: m.group(1).upper(), s)
    s = re.sub(r"\b(Ltda|Eireli|Me|Epp|Cnpj)\b\.?", "", s, flags=re.I)
    s = re.sub(r"\bHosp\b\.?", "Hospital", s, flags=re.I)
    return re.sub(r"\s+", " ", acc(s)).strip(" -")
d["nomeh"] = d.NO_FANTASIA.fillna(d.NO_RAZAO_SOCIAL).map(nome_h)
d["bairro"] = d.NO_BAIRRO.map(lambda s: acc(tc(s))).replace("", "Sem bairro informado")
lat = pd.to_numeric(d.NU_LATITUDE, errors="coerce"); lng = pd.to_numeric(d.NU_LONGITUDE, errors="coerce")
ok = lat.between(-34, 6) & lng.between(-75, -33)
d["aprox"] = ~ok
d["lat"] = lat.where(ok, d.latitude); d["lng"] = lng.where(ok, d.longitude)
def tel(s):
    if not isinstance(s, str): return ""
    n = re.sub(r"\D", "", s)
    return s.strip() if len(n) in (8, 9, 10, 11) and len(set(n)) > 1 else ""
d["tel"] = d.NU_TELEFONE.map(tel)
d["email"] = d.NO_EMAIL.fillna("").str.lower().str.strip()
d["end"] = (d.NO_LOGRADOURO.map(tc) + ", " + d.NU_ENDERECO.fillna("s/n")).str.strip(", ")
d["cidade"] = d.nome
d = d.rename(columns={"CO_CNES": "id"})[["id", "nomeh", "tipo", "uf", "cidade", "bairro", "end", "tel", "email", "lat", "lng", "aprox"]]
d = d.drop_duplicates("id")
d.to_pickle(out); print(len(d), "estabelecimentos;", int(d.aprox.sum()), "com coordenada aproximada ao município")
