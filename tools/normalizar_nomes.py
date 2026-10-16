#!/usr/bin/env python3
"""Normaliza os textos de data/<UF>.json para português do Brasil.

Uso:  python3 tools/normalizar_nomes.py [--dry] [--pasta data]

O que faz (sempre determinístico e idempotente: rodar de novo não muda nada):
  * traduz nomes em inglês de igrejas (Church of..., Parish..., St. ..., Our Lady of...);
  * restaura acentos e cedilha (Fatima -> Fátima, Conceicao -> Conceição, Icarai -> Icaraí...);
  * corrige capitalização (TUDO MAIÚSCULO / minúsculo -> Título; de/da/do em minúsculas; II, UPA, SUS em maiúsculas);
  * expande abreviações comuns (N. S. -> Nossa Senhora, Sta -> Santa, R. -> Rua, Av -> Avenida...);
  * remove lixo de cadastro no fim do nome (" - Cdd/Rj", " - PE", "/SP", " RJ", "Ltda", "Eireli"),
    sem apagar o que distingue duas igrejas de mesmo nome na mesma cidade.

Campos tratados: hospitais (nome, bairro, endereço), paróquias (nome, cidade, endereço) e lista de cidades.
NÃO altera: ids, números, telefones, e-mails, sites, coordenadas, índices, tipo, ordem, estrutura, data/index.json.
"""
import json, os, re, sys, glob, unicodedata, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lexico_ptbr import AUTO

# --------------------------------------------------------------------------------------------
# Léxico
# --------------------------------------------------------------------------------------------
MANUAL = {  # sem acento (minúsculo) -> forma correta
    "sao": "são", "mae": "mãe", "maes": "mães", "icarai": "icaraí", "visao": "visão", "servicos": "serviços",
    "servico": "serviço", "medicos": "médicos", "medicas": "médicas", "plastica": "plástica", "plasticas": "plásticas",
    "policlinica": "policlínica", "policlinicas": "policlínicas", "publico": "público", "publica": "pública",
    "publicos": "públicos", "ambulatorio": "ambulatório", "ambulatorial": "ambulatorial", "diagnostico": "diagnóstico",
    "diagnosticos": "diagnósticos", "diagnostica": "diagnóstica", "reabilitacao": "reabilitação",
    "assistencia": "assistência", "terapeutica": "terapêutica", "terapeutico": "terapêutico",
    "funcionarios": "funcionários", "cirurgica": "cirúrgica", "cirurgico": "cirúrgico", "cirurgicos": "cirúrgicos",
    "cirurgicas": "cirúrgicas", "cirurgiao": "cirurgião", "atencao": "atenção", "urgencia": "urgência",
    "urgencias": "urgências", "referencia": "referência", "oftalmologica": "oftalmológica",
    "oftalmologicas": "oftalmológicas", "oftalmologicos": "oftalmológicos", "oftalmico": "oftálmico",
    "oftalmica": "oftálmica", "clinico": "clínico", "clinicos": "clínicos", "basica": "básica", "basico": "básico",
    "aeronautica": "aeronáutica", "reproducao": "reprodução", "excelencia": "excelência", "emergencia": "emergência",
    "emergencias": "emergências", "laboratorio": "laboratório", "laboratorios": "laboratórios", "internacao": "internação",
    "hemodinamica": "hemodinâmica", "pediatrica": "pediátrica", "pediatricas": "pediátricas", "ortopedica": "ortopédica",
    "ortopedicas": "ortopédicas", "intermedica": "intermédica", "gestao": "gestão", "urologico": "urológico",
    "urologica": "urológica", "sanitario": "sanitário", "sanitaria": "sanitária", "administracao": "administração",
    "veterinaria": "veterinária", "veterinario": "veterinário", "recuperacao": "recuperação",
    "estabilizacao": "estabilização", "quimica": "química", "quimico": "químico", "estetica": "estética",
    "dependencia": "dependência", "odontologica": "odontológica", "odontologico": "odontológico",
    "neurologico": "neurológico", "neurologica": "neurológica", "infancia": "infância", "doencas": "doenças",
    "analises": "análises", "municipio": "município", "nucleo": "núcleo", "modulo": "módulo", "fundacao": "fundação",
    "associacao": "associação", "geriatrico": "geriátrico", "geriatrica": "geriátrica", "obstetrico": "obstétrico",
    "obstetrica": "obstétrica", "hematologica": "hematológica", "oncologica": "oncológica", "humanizacao": "humanização",
    "cardiologico": "cardiológico", "cardiologica": "cardiológica", "principe": "príncipe", "espirita": "espírita",
    "sirio": "sírio", "libanes": "libanês", "portugues": "português", "portuguesa": "portuguesa", "crianca": "criança",
    "criancas": "crianças", "ciencias": "ciências", "ciencia": "ciência", "pronto-socorro": "pronto-socorro",
    "endoscopica": "endoscópica", "radiologica": "radiológica", "fisica": "física", "economica": "econômica",
    "psicologica": "psicológica", "psiquiatrica": "psiquiátrica", "psiquiatrico": "psiquiátrico", "vitreo": "vítreo",
    "acao": "ação", "conceicao": "conceição", "assuncao": "assunção", "ressurreicao": "ressurreição",
    "ascencao": "ascensão", "ascensao": "ascensão", "encarnacao": "encarnação", "natalicio": "natalício",
    "embare": "embaré", "efigenia": "efigênia", "america": "américa", "botanico": "botânico",
    "jacarepagua": "jacarepaguá", "maracana": "maracanã", "tambaú": "tambaú", "ate": "até", "tambau": "tambaú",
    "cesar": "césar", "moises": "moisés", "maua": "mauá", "irma": "irmã", "grajau": "grajaú", "jaragua": "jaraguá",
    "cabula": "cabula", "agronomica": "agronômica", "caucaia": "caucaia", "iguatemi": "iguatemi", "estancia": "estância",
    "mulheres": "mulheres", "gestante": "gestante", "antonio": "antônio", "lucia": "lúcia", "tereza": "tereza",
    "luzia": "luzia", "barbara": "bárbara", "monica": "mônica", "magdalena": "madalena", "angela": "ângela",
    "veronica": "verônica", "apolonia": "apolônia", "escolastica": "escolástica", "gertrudes": "gertrudes",
    "agueda": "águeda", "ifigenia": "ifigênia", "dorotea": "dorotéia", "perpetua": "perpétua",
    "felicidade": "felicidade", "consolata": "consolata", "candelaria": "candelária", "penha": "penha",
    "salette": "salette", "sabastine": "sebastião", "joao": "joão", "jose": "josé", "luis": "luís",
    "alvaro": "álvaro", "julia": "júlia", "silverio": "silvério", "belem": "belém", "goias": "goiás",
    "fe": "fé", "ze": "zé", "cear": "cear", "pao": "pão", "alem": "além", "ceu": "céu", "tome": "tomé",
    "ines": "inês", "vo": "vó", "bras": "brás", "saude": "saúde", "familia": "família", "nazare": "nazaré",
    "coracao": "coração", "gloria": "glória", "vitoria": "vitória", "cassia": "cássia", "fatima": "fátima",
    "pilar": "pilar", "rosario": "rosário", "misericordia": "misericórdia", "perpetuo": "perpétuo",
    "paroquia": "paróquia", "santuario": "santuário", "clinica": "clínica", "clinicas": "clínicas", "medico": "médico",
    "medica": "médica", "catolica": "católica", "catolico": "católico", "basilica": "basílica",
    "emilia": "emília", "analia": "anália", "silvia": "sílvia", "lavinia": "lavínia", "sonia": "sônia",
    "marcia": "márcia", "flavia": "flávia", "katia": "kátia", "celia": "célia", "nacoes": "nações",
    "amazonia": "amazônia", "guarnicao": "guarnição", "triangulo": "triângulo", "rodoviaria": "rodoviária",
    "rodoviario": "rodoviário", "comunitaria": "comunitária", "humanitaria": "humanitária",
    "transitoria": "transitória", "ceramica": "cerâmica", "dinamica": "dinâmica", "agencia": "agência",
    "consultorio": "consultório", "universitarios": "universitários", "bancarios": "bancários",
    "milionarios": "milionários", "metalurgicos": "metalúrgicos", "miseriocordia": "misericórdia",
    "indepedencia": "independência", "mutirao": "mutirão", "mutiroes": "mutirões", "pavilhao": "pavilhão",
    "capelao": "capelão", "avancado": "avançado", "avancada": "avançada", "especializacao": "especialização", "licao": "lição", "secao": "seção", "nacao": "nação", "funcao": "função", "acao": "ação", "artesao": "artesão", "paraoquia": "paróquia", "sansao": "sansão",
}
LEX = dict(AUTO)
LEX.update(MANUAL)
# palavras que não devem receber acento (apesar de aparecerem nos léxicos)
for _k in ("sa", "pa", "pe", "se", "la", "pilar", "caucaia", "cabula", "iguatemi", "cear", "penha", "salette",
           "gertrudes", "consolata", "felicidade", "mulheres", "gestante", "luzia", "tereza", "tambaú", "portuguesa",
           "pronto-socorro", "ambulatorial"):
    LEX.pop(_k, None)

CONECT = {"de", "da", "do", "das", "dos", "e", "em", "na", "no", "nas", "nos", "com", "ao", "aos", "os", "as", "para", "por", "que"}
CONECT_BAIXA = CONECT - {"para", "por"}   # "Para"/"Por" capitalizados podem ser nomes (Rua Pará)
ROMANOS = {"II", "III", "IV", "VI", "VII", "VIII", "IX", "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII",
           "XIX", "XX", "XXI", "XXII", "XXIII", "XXIV", "XXV"}
# siglas que ficam em maiúsculas (chave em minúsculas, sem acento)
SIGLAS = set("""upa uti cti sus inca ufrj uerj uff usp unifesp unicamp hc apae caps ums cer ceo iml puc hu huap hmi samu cnbb rcc
ecc ejc ceb tlc sav smo mdm scj iecb ieclb icab ebserh cassems cnes ibge fiocruz sesa sesau hgg hpp ame ceman cemed
shis shcs shin shcn sgan sgas shln shls sqs sqn cls cln eqs eqn eqnm eqnp eqsw eqnl scs scn sepn seps srtvs srtvn sds sdn
cep qi ql qr qd lt cj br hr df ii iii ae eq sh sg sm gam""".split())
SIGLAS_FORCAR = set("ceb sav tlc mdm upa uti cti sus inca ufrj uerj uff usp unifesp unicamp apae caps ums iml puc huap hmi samu cnbb rcc "
                    "ecc ejc ebserh cassems cnes ibge hc hu".split())  # "Upa" -> "UPA" mesmo vindo em Título
UFS = "AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split()
UF_AMBIGUA = {"SE", "PE", "TO", "MA", "ES", "AL", "AM", "AC", "AP"}  # só removidas com separador
SEM_SUFIXO = {"macao", "tucao", "isao", "cesao", "lisao", "tesao"}
PREFIXO_APOSTROFO = {"sant", "santa", "d", "l"}

# --------------------------------------------------------------------------------------------
# Santos e inglês (nomes de igrejas)
# --------------------------------------------------------------------------------------------
SANTAS = set("""rita luzia lucia teresinha terezinha tereza teresa catarina margarida cecilia clara isabel ana genoveva gemma gema
barbara helena monica maria edwiges paulina joana rosa ines madalena angela apolonia dulce filomena escolastica veronica luiza
bernadete josefina auxiliadora sofia zita gertrudes brigida clotilde joaquina emilia laura marta eulalia benedita efigenia
francisca rafaela irene ifigenia elisabete julia amelia doroteia odilia perpetua quiteria flora aparecida paula
angelica cruz sara tecla teodora vitoria monica""".split())
SANTOS = set("""antonio expedito agostinho afonso amaro andre angelo inacio onofre eloi ivo eustaquio isidoro ildefonso cristo
estanislau""".split())
NOMES_EN = {"joseph": "José", "john": "João", "paul": "Paulo", "peter": "Pedro", "michael": "Miguel", "george": "Jorge",
            "francis": "Francisco", "anthony": "Antônio", "benedict": "Bento", "basil": "Basílio", "lazarus": "Lázaro",
            "sebastian": "Sebastião", "sabastine": "Sebastião", "andrew": "André", "thomas": "Tomé", "james": "Tiago",
            "charles": "Carlos", "vincent": "Vicente", "joachim": "Joaquim", "luke": "Lucas", "mark": "Marcos",
            "matthew": "Mateus", "jude": "Judas", "nicholas": "Nicolau", "augustine": "Agostinho", "mary": "Maria",
            "jose": "José", "antonio": "Antônio", "antónio": "Antônio", "lucy": "Luzia", "sebastián": "Sebastião",
            "gabriel": "Gabriel", "raphael": "Rafael", "rita": "Rita", "frances": "Francisco"}
NAO_SANTO = {"sul", "norte", "oeste", "leste", "central", "comercial", "industrial", "bueno", "marista", "oeste"}

FRASES_EN = [  # (regex, substituição) aplicadas em ordem, sem distinguir maiúsculas
    (r"\bRoman Catholic Diocese of\b", "Diocese Católica de"),
    (r"\bCatholic Diocese of\b", "Diocese Católica de"),
    (r"\bArchdiocese of\b", "Arquidiocese de"),
    (r"\bDiocesan Curia of\b", "Cúria Diocesana de"),
    (r"\bDiocese of\b", "Diocese de"),
    (r"\bMiter Diocese\b", "Mitra da Diocese"),
    (r"\bSt\.? Andrew'?s Diocese\b", "Diocese de Santo André"),
    (r"\bMinor Basilica\b", "Basílica Menor"),
    (r"\bRoman Catholic Church\b", "Igreja Católica"),
    (r"\bCatholic Church\b", "Igreja Católica"),
    (r"\bCatholic Community\b", "Comunidade Católica"),
    (r"\bRoman Catholic\b", "Católica"),
    (r"\bParish and Shrine of\b", "Paróquia e Santuário de"),
    (r"\bOur Lady of(?: the)? Aparecida\b", "Nossa Senhora Aparecida"),
    (r"\bOur Lady Aparecida\b", "Nossa Senhora Aparecida"),
    (r"\bOur Lady of (?:Fatima|Fátima)\b", "Nossa Senhora de Fátima"),
    (r"\bOur Lady Imaculada Conceição\b", "Nossa Senhora Imaculada Conceição"),
    (r"\bOur Lady of(?: the)? Immaculate Conception\b", "Nossa Senhora da Imaculada Conceição"),
    (r"\bOur Lady of Conception\b", "Nossa Senhora da Conceição"),
    (r"\bOur Lady of Divine Providence\b", "Nossa Senhora da Divina Providência"),
    (r"\bOur Lady of Providence\b", "Nossa Senhora da Providência"),
    (r"\bOur Lady of Perpetual Help\b", "Nossa Senhora do Perpétuo Socorro"),
    (r"\bOur Lady Help of Christians\b", "Nossa Senhora Auxiliadora"),
    (r"\bOur Lady of the Pillar\b", "Nossa Senhora do Pilar"),
    (r"\bOur Lady of Health\b", "Nossa Senhora da Saúde"),
    (r"\bOur Lady of Consolation\b", "Nossa Senhora da Consolação"),
    (r"\bOur Lady of the Ladder\b", "Nossa Senhora da Escada"),
    (r"\bOur Lady of Los Remedios\b", "Nossa Senhora dos Remédios"),
    (r"\bOur Lady of Candeias\b", "Nossa Senhora das Candeias"),
    (r"\bOur Lady D'Abadia\b", "Nossa Senhora d'Abadia"),
    (r"\bOur Lady of Mount Carmel\b", "Nossa Senhora do Carmo"),
    (r"\bOur Lady of Peace\b", "Nossa Senhora da Paz"),
    (r"\bOur Lady of the Rosary\b", "Nossa Senhora do Rosário"),
    (r"\bOur Lady of the Navigators\b", "Nossa Senhora dos Navegantes"),
    (r"\bOur Lady of Penha\b", "Nossa Senhora da Penha"),
    (r"\bOur Lady of Rocio\b", "Nossa Senhora do Rocio"),
    (r"\bOur Lady of Schoenstatt\b", "Nossa Senhora de Schoenstatt"),
    (r"\bOur Lady of Loreto\b", "Nossa Senhora de Loreto"),
    (r"\bOur Lady of(?: the)?\s+", "Nossa Senhora de "),
    (r"\bOur Lady\s+", "Nossa Senhora "),
    (r"\bHoly Spirit\b", "Espírito Santo"),
    (r"\bHoly Family\b", "Sagrada Família"),
    (r"\bHoly Trinity\b", "Santíssima Trindade"),
    (r"\bSacred Heart of Jesus\b", "Sagrado Coração de Jesus"),
    (r"\bImmaculate Heart of Mary\b", "Imaculado Coração de Maria"),
    (r"\bNew Work of the Heart of Mary\b", "Nova Obra do Coração de Maria"),
    (r"\bHeart of Mary\b", "Coração de Maria"),
    (r"\b(?:the )?Infant Jesus (?:of Prague|de Praga)\b", "Menino Jesus de Praga"),
    (r"\b(?:Baby|Child|Infant) Jesus\b", "Menino Jesus"),
    (r"\bChrist,? The Redeemer\b", "Cristo Redentor"),
    (r"\bChrist Liberator\b", "Cristo Libertador"),
    (r"\bChrist the King\b", "Cristo Rei"),
    (r"\bGood Shepherd\b", "Bom Pastor"),
    (r"\bMother of God\b", "Mãe de Deus"),
    (r"\bJohn Paul II\b", "João Paulo II"),
    (r"\bthe Archangel\b", "Arcanjo"),
    (r"\bthe Apostle\b", "Apóstolo"),
    (r"\bthe Baptist\b", "Batista"),
    (r"\bFrancis of Assisi\b", "Francisco de Assis"),
    (r"\bLazarus and San Roque\b", "Lázaro e São Roque"),
]
TIPOS_EN = {"church": "Igreja", "parish": "Paróquia", "chapel": "Capela", "cathedral": "Catedral", "sanctuary": "Santuário",
            "shrine": "Santuário", "basilica": "Basílica", "community": "Comunidade"}
TIPOS_PT = {"igreja", "paroquia", "catedral", "capela", "santuario", "basilica", "comunidade"}
PALAVRAS_EN = {"of": "de", "and": "e", "the": "", "catholic": "Católica", "church": "Igreja", "parish": "Paróquia",
               "chapel": "Capela", "cathedral": "Catedral", "sanctuary": "Santuário", "shrine": "Santuário",
               "basilica": "Basílica", "community": "Comunidade", "mother": "Mãe", "holy": "Santo", "saint": "São",
               "diocese": "Diocese", "minor": "Menor", "metropolitan": "Metropolitana"}

# casos pontuais que nenhuma regra geral resolve com segurança (nome original -> nome final)
EXCECOES = {
    "Parish Mother and São Francisco das Chagas Sanctuary": "Paróquia Mãe e Santuário São Francisco das Chagas",
    "Sanctuary of the Archangel Michael": "Santuário do Arcanjo Miguel",
    "Igreja Cathedral": "Igreja Catedral",
    "In Statu Viae": "In Statu Viae",
}

SEP_RE = re.compile(r"([^\W\d_]+(?:'[^\W\d_]+)*)")  # palavras (letras, com apóstrofo interno)


def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def chave(t):
    return sem_acento(t).lower()


def com_caixa(modelo, novo):
    """Aplica ao texto `novo` (minúsculo) o padrão de caixa de `modelo`."""
    if len(modelo) > 1 and modelo.isupper():
        return novo.upper()
    if modelo[:1].isupper():
        return novo[:1].upper() + novo[1:]
    return novo


def titulo(t):
    if "'" in t:
        a, b = t.split("'", 1)
        a = a if a.lower() == "d" else a[:1].upper() + a[1:].lower()
        return a + "'" + b[:1].upper() + b[1:].lower()
    return t[:1].upper() + t[1:].lower()


def genero_santo(nome):
    k = chave(nome)
    if k in SANTAS:
        return "Santa"
    if k in SANTOS:
        return "Santo"
    return "São"


# --------------------------------------------------------------------------------------------
# Etapas
# --------------------------------------------------------------------------------------------
def pre_limpeza(s):
    s = unicodedata.normalize("NFC", str(s or ""))
    s = s.replace("’", "'").replace("‘", "'").replace("´", "'").replace("`", "'")
    s = re.sub(r"d'\ufffd\??gua", "d'Água", s)
    s = re.sub(r"\bSant\s*'\s*(?=[A-Za-zÀ-ÿ])", "Sant'", s, flags=re.I)
    s = re.sub(r"\bSant\s+(?=Ann?a\b)", "Sant'", s, flags=re.I)
    s = re.sub(r"\s*([–—])\s*", " - ", s)
    s = re.sub(r"(?<=\S)-\s+(?=\S)", " - ", s)       # "Fátima- Centro" -> "Fátima - Centro"
    s = re.sub(r"(?<=\s)-(?=[A-Za-zÀ-ÿ])", "- ", s)   # " -rn" -> "- rn" (tratado depois)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def traduzir_ingles(s):
    if s in EXCECOES:
        return EXCECOES[s]
    for rx, sub in FRASES_EN:
        s = re.sub(rx, sub, s, flags=re.I)
    # tipo no fim ("X Church", "X Parish", "X Cathedral"...) vai para o começo
    m = re.search(r"^(.*?)[\s,]+(church|parish|chapel|cathedral|sanctuary|shrine|basilica|community)\s*$", s, flags=re.I)
    if m and m.group(1).strip():
        resto, tipo = m.group(1).strip(), TIPOS_EN[m.group(2).lower()]
        primeiro = chave(resto.split()[0]) if resto.split() else ""
        s = resto if primeiro in TIPOS_PT else f"{tipo} {resto}"
    # santos em inglês/espanhol: St./Saint/San + Nome
    def santo(m):
        nome = m.group(2)
        if chave(nome) in NAO_SANTO:
            return m.group(0)
        nome_pt = NOMES_EN.get(chave(nome), nome)
        return f"{genero_santo(nome_pt)} {nome_pt}"
    s = re.sub(r"\b(St\.?|Saint|San)\s+([A-Za-zÀ-ÿ]+)", santo, s)
    # palavras soltas
    def palavra(m):
        w = m.group(0)
        novo = PALAVRAS_EN.get(w.lower())
        if novo is None:
            return w
        return com_caixa(w, novo.lower()) if novo else ""
    s = re.sub(r"\b[A-Za-z]+\b", palavra, s)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\bde (Menino Jesus|Mãe de Deus|Bom Pastor|Cristo)\b", lambda m: ("do " if m.group(1) != "Mãe de Deus" else "da ") + m.group(1), s)
    return s


def expandir_abreviacoes(s, tipo, uf=""):
    if tipo == "a":
        s = re.sub(r"\bS\s*/\s*N[º°]?(?![\wÀ-ÿ])|\bSN(?![\wÀ-ÿ])|\bS\s+N(?![\wÀ-ÿ])", "S/N", s, flags=re.I)
        s = re.sub(r"(S/N)(?:\s+S/N)+", r"\1", s)
    # Nossa Senhora
    s = re.sub(r"(?<![/\w])\b(?:Nossa|Nsa|Ns|N)\.?\s*(?:Sra|Srª|Sª|Senhora|S)(?![\wÀ-ÿ])\.?", "Nossa Senhora", s, flags=re.I)
    ns2 = r"(?=\s+(?:d[aeo]s?)\b)" if tipo == "a" else r"(?=\s)"
    s = re.sub(r"\b(?:NS|NSra|Nsra|Nsa|Ns)(?![\wÀ-ÿ])\.?" + ns2, "Nossa Senhora", s)
    s = re.sub(r"\b(?:Sra|Srª|Sª)(?![\wÀ-ÿ])\.?", "Senhora", s)
    s = re.sub(r"\bSta(?![\wÀ-ÿ])\.?", "Santa", s)
    s = re.sub(r"\bSto(?![\wÀ-ÿ])\.?", "Santo", s)
    s = re.sub(r"\bPe\.\s*(?=[A-ZÀ-Ý])", "Padre ", s)
    if tipo in ("p", "h"):
        def s_ponto(m):
            return genero_santo(m.group(1)) + " " + m.group(1)
        s = re.sub(r"\bS\.\s*(?=[A-ZÀ-Ý][a-zà-ÿ]{2,})(\w+)", s_ponto, s)
        s = re.sub(r"\bMun(?:ic)?(?![\wÀ-ÿ])\.?(?=\s)", "Municipal", s)
        s = re.sub(r"\bMatern(?![\wÀ-ÿ])\.?", "Maternidade", s)
        s = re.sub(r"(?<=\be )Mat(?![\wÀ-ÿ])\.?", "Maternidade", s)
        s = re.sub(r"(?<=Hospital )Reg(?![\wÀ-ÿ])\.?", "Regional", s)
        s = re.sub(r"(?<=Hospital )Est(?:ad)?(?![\wÀ-ÿ])\.?", "Estadual", s)
        s = re.sub(r"\bHosp(?![\wÀ-ÿ])\.?", "Hospital", s)
        s = re.sub(r"\bInst(?![\wÀ-ÿ])\.?(?=\s)", "Instituto", s)
    if tipo in ("a", "b"):
        s = re.sub(r"\b(?:Pça|Pca|Prç)(?![\wÀ-ÿ])\.?", "Praça", s, flags=re.I)
        s = re.sub(r"\bJd(?![\wÀ-ÿ])\.?(?=\s)", "Jardim", s)
        s = re.sub(r"\bPq(?![\wÀ-ÿ])\.?(?=\s)", "Parque", s)
        s = re.sub(r"\bVl(?![\wÀ-ÿ])\.?(?=\s)", "Vila", s)
    if tipo == "b":
        s = re.sub(r"^St(?![\wÀ-ÿ])\.?(?=\s)", "Setor", s)
    if tipo == "a":
        s = re.sub(r"^R(?![\wÀ-ÿ])\.?(?=\s)", "Rua", s)
        s = re.sub(r"\b(?:Avn?)(?![\wÀ-ÿ])\.?(?=\s)", "Avenida", s, flags=re.I)
        s = re.sub(r"\b(?:Tv|Trav)(?![\wÀ-ÿ])\.?(?=\s)", "Travessa", s, flags=re.I)
        s = re.sub(r"\bEstr(?![\wÀ-ÿ])\.?(?=\s)", "Estrada", s, flags=re.I)
        s = re.sub(r"\bRod(?![\wÀ-ÿ])\.?(?=\s)", "Rodovia", s)
        s = re.sub(r"\bAl(?![\wÀ-ÿ])\.(?=\s)", "Alameda", s)
        s = re.sub(r"\bLgo(?![\wÀ-ÿ])\.?(?=\s)", "Largo", s, flags=re.I)
        s = re.sub(r"\bKM(?![\wÀ-ÿ])", "Km", s)
        s = re.sub(r"\bUnnamed R(?:oa)?d\b\.?", "Rua sem nome", s, flags=re.I)   # texto-padrão em inglês do Overture
        if uf in ("DF", "GO"):
            s = re.sub(r"^St(?![\wÀ-ÿ])\.?(?=\s)", "Setor", s)   # Setor (Brasília/Goiás)
    if tipo in ("a", "h"):
        s = re.sub(r"\b(Br)(?=[\s-]*\d{2,3}\b)", "BR", s)
        s = re.sub(r"\b(" + "|".join(u.capitalize() for u in UFS if u not in UF_AMBIGUA) + r")(?=[\s-]*\d{2,3}\b)",
                   lambda m: m.group(1).upper(), s)
    return s


def modo_caixa(s):
    letras = re.sub(r"[^A-Za-zÀ-ÿ]", "", s)
    if len(letras) > 3 and letras.isupper():
        return "upper"
    if letras and letras.islower():
        return "lower"
    return "mixed"


def processar_palavras(s, tipo):
    """Capitalização + acentos, palavra por palavra."""
    modo = modo_caixa(s)
    partes = SEP_RE.split(s)  # [sep, palavra, sep, palavra, ..., sep]
    palavras = list(range(1, len(partes), 2))
    primeiro = palavras[0] if palavras else None
    for i in palavras:
        t = partes[i]
        k = chave(t)
        conect = t.lower() in CONECT
        apos_digito = partes[i - 1][-1:].isdigit()
        apos_hifen = partes[i - 1] == "-"
        if k.upper() in ROMANOS and (t.isupper() or t.istitle()) and tipo != "c":
            partes[i] = k.upper()
            continue
        if k in SIGLAS_FORCAR and (t.istitle() or t.isupper()):
            partes[i] = k.upper()
            continue
        if t.isupper() and len(t) > 1:
            if conect:
                t = k.capitalize() if i == primeiro else k
            elif k in LEX:
                t = titulo(t)
            elif k in SIGLAS or len(t) <= 2 or not re.search(r"[AEIOU]", t):
                partes[i] = t
                continue
            elif modo == "mixed" and len(t) <= 4:
                partes[i] = t   # sigla curta dentro de nome em caixa mista (ex.: RCC, IEQ)
                continue
            else:
                t = titulo(t)
        elif t.islower() and not apos_digito and not apos_hifen and not conect and len(t) > 1:
            if not (tipo == "a" and modo == "mixed"):
                t = titulo(t)
        elif "'" in t and not t.isupper():
            a_, b_ = t.split("'", 1)
            t = a_ + "'" + b_[:1].upper() + b_[1:]
        if t.lower() in CONECT_BAIXA and i != primeiro and t[:1].isupper() and len(t) > 1:
            t = t.lower()
        novo = LEX.get(k) if tipo != "c" else None   # nomes de município: sem léxico (vêm do IBGE)
        if novo is None and tipo != "c" and k not in SEM_SUFIXO:
            m_ = re.match(r"^([a-z]{4,})(cao|coes|encia|ancia|encias|ancias)$", k) or re.match(r"^([a-z]{4,})(sao)$", k)
            if m_ and len(k) >= 6:
                novo = m_.group(1) + {"cao": "ção", "coes": "ções", "encia": "ência", "ancia": "ância", "encias": "ências",
                                      "ancias": "âncias", "sao": "são"}[m_.group(2)]
        if novo is not None and "'" not in t:
            t = com_caixa(t, novo)
        partes[i] = t
    return "".join(partes)


def corrigir_para(s):
    s = re.sub(r"\b(Rua|Avenida|Travessa|Praça|Alameda|Largo)\s+[Pp]ara\b(?!\s+[a-zà-ÿ])", r"\1 Pará", s)
    return re.sub(r"\b(do|no|de|em)\s+[Pp]ara\b(?!\s+(?:[a-zà-ÿ]|a\b))", lambda m: m.group(1) + " Pará", s)


def honorificos(s):
    s = re.sub(r"\b(Dra?|Profa?)(?![\wÀ-ÿ.])", lambda m: m.group(1) + ".", s)
    return s


def limpar_lixo(s, uf, agressivo=True):
    """Remove sufixos de cadastro. `agressivo=False` só faz acabamento (sem remover UF/Cdd)."""
    for _ in range(4):
        antes = s
        s = re.sub(r"[\s,;:]+$", "", s)
        s = re.sub(r"(?<=[^\s.A-Z])\.$", "", s)  # ponto final solto (mantém "S.A.")
        if agressivo:
            s = re.sub(r"\s*[-/,]\s*Cdd(?:\s*/\s*[A-Za-z]{2})?\s*$", "", s, flags=re.I)
            s = re.sub(r"\s+Cdd\s*$", "", s, flags=re.I)
            s = re.sub(r"[\s,-]+(?:Ltda|Eireli|Epp)\.?\s*$", "", s, flags=re.I)
            ufs = "|".join(UFS)
            s = re.sub(rf"\s*(?:-\s*|/\s*|,\s+|-)(?:{ufs})\.?\s*$", "", s, flags=re.I)
            m = re.search(r"^(.*\S)\s+([A-Za-z]{2})$", s)
            if m and m.group(2).upper() == uf and m.group(2).upper() not in UF_AMBIGUA and m.group(2) in (m.group(2).upper(), m.group(2).capitalize()):
                ant = chave(m.group(1).split()[-1])
                if ant in CONECT:
                    s = m.group(1) + " " + m.group(2).upper()
                else:
                    s = m.group(1)
        s = re.sub(r"\s*[-–/]\s*$", "", s)
        s = re.sub(r"\s+", " ", s).strip()
        if s == antes:
            break
    return s


def uf_maiuscula(s):
    """'de Sp' -> 'de SP' quando a sigla vem depois de de/do/da no fim."""
    return re.sub(r"(\b(?:de|do|da)\s+)(" + "|".join(u for u in UFS if u not in UF_AMBIGUA) + r")$",
                  lambda m: m.group(1) + m.group(2).upper(), s, flags=re.I)


def _normalizar_uma_vez(s, tipo, uf, agressivo=True):
    """tipo: p (nome de paróquia) · h (nome de hospital) · b (bairro) · a (endereço) · c (cidade)."""
    if not s:
        return s
    x = pre_limpeza(s)
    if tipo == "p":
        x = traduzir_ingles(x)
    x = expandir_abreviacoes(x, tipo, uf)
    x = processar_palavras(x, tipo)
    x = corrigir_para(x)
    if tipo in ("p", "h"):
        x = honorificos(x)
        x = uf_maiuscula(x) if tipo == "h" else x
    if tipo in ("p", "h", "b"):
        x = limpar_lixo(x, uf, agressivo and tipo != "b")
    x = re.sub(r"\s+", " ", x).strip()
    x = re.sub(r"\s+,", ",", x)
    return x


def normalizar(s, tipo, uf, agressivo=True):
    """Aplica o pipeline até estabilizar (garante idempotência)."""
    x = s
    for _ in range(4):
        y = _normalizar_uma_vez(x, tipo, uf, agressivo)
        if y == x:
            break
        x = y
    return x


# --------------------------------------------------------------------------------------------
# Arquivos
# --------------------------------------------------------------------------------------------
CATS = ["hospital_nome", "hospital_bairro", "hospital_endereco", "paroquia_nome", "paroquia_cidade",
        "paroquia_endereco", "cidade_lista"]


def chave_cidade(c):
    return re.sub(r"[^a-z0-9]", "", chave(c))


def processar_uf(d, estat, exemplos, globais):
    uf = d["uf"].upper()
    novo = json.loads(json.dumps(d))  # cópia profunda

    def reg(cat, antes, depois):
        if antes != depois:
            estat[cat] += 1
            exemplos[cat].append((antes, depois))

    # lista de municípios (IBGE): só espaços; paróquia.cidade: casa com a lista, senão só caixa/espaços
    novo["c"] = [re.sub(r"\s+", " ", c).strip() for c in d["c"]]
    for a, b in zip(d["c"], novo["c"]):
        reg("cidade_lista", a, b)
    locais = {chave_cidade(c): c for c in novo["c"]}

    def cidade(c):
        k = chave_cidade(c)
        if k in locais:
            return locais[k]
        if len(globais.get(k, ())) == 1:
            return next(iter(globais[k]))
        return normalizar(c, "c", uf)

    # hospitais
    chaves_h = collections.defaultdict(list)
    for i, h in enumerate(d["h"]):
        novo["h"][i][1] = normalizar(h[1], "h", uf)
        novo["h"][i][4] = normalizar(h[4], "b", uf)
        novo["h"][i][5] = normalizar(h[5], "a", uf)
        chaves_h[(h[3], novo["h"][i][1])].append(i)
    for (cid, nome), idxs in chaves_h.items():  # colisões criadas pela limpeza -> mantém o sufixo
        if len(idxs) > 1 and len({d["h"][i][1] for i in idxs}) > 1:
            for i in idxs:
                novo["h"][i][1] = normalizar(d["h"][i][1], "h", uf, agressivo=False)
    for i, h in enumerate(d["h"]):
        reg("hospital_nome", h[1], novo["h"][i][1])
        reg("hospital_bairro", h[4], novo["h"][i][4])
        reg("hospital_endereco", h[5], novo["h"][i][5])
    # paróquias
    chaves_p = collections.defaultdict(list)
    for j, p in enumerate(d["p"]):
        novo["p"][j][0] = normalizar(p[0], "p", uf)
        novo["p"][j][1] = cidade(p[1])
        novo["p"][j][2] = normalizar(p[2], "a", uf)
        chaves_p[(novo["p"][j][1], novo["p"][j][0])].append(j)
    for (cid, nome), idxs in chaves_p.items():
        if len(idxs) > 1 and len({pre_limpeza(d["p"][j][0]) for j in idxs}) > 1:
            for j in idxs:
                novo["p"][j][0] = normalizar(d["p"][j][0], "p", uf, agressivo=False)
    for j, p in enumerate(d["p"]):
        reg("paroquia_nome", p[0], novo["p"][j][0])
        reg("paroquia_cidade", p[1], novo["p"][j][1])
        reg("paroquia_endereco", p[2], novo["p"][j][2])
    return novo


def main():
    pasta = "data"
    dry = "--dry" in sys.argv
    if "--pasta" in sys.argv:
        pasta = sys.argv[sys.argv.index("--pasta") + 1]
    estat = collections.Counter()
    exemplos = collections.defaultdict(list)
    alterados = 0
    arquivos = [f for f in sorted(glob.glob(os.path.join(pasta, "*.json"))) if os.path.basename(f) != "index.json"]
    dados = {}
    globais = collections.defaultdict(set)
    for f in arquivos:
        with open(f, encoding="utf-8") as fh:
            dados[f] = json.load(fh)
        for c in dados[f]["c"]:
            globais[chave_cidade(c)].add(re.sub(r"\s+", " ", c).strip())
    for f in arquivos:
        d = dados[f]
        novo = processar_uf(d, estat, exemplos, globais)
        if novo != d:
            alterados += 1
            if not dry:
                with open(f, "w", encoding="utf-8") as fh:
                    json.dump(novo, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"arquivos alterados: {alterados}")
    for c in CATS:
        print(f"  {c}: {estat[c]}")
    print(f"  TOTAL de textos alterados: {sum(estat.values())}")
    if "--exemplos" in sys.argv:
        for c in CATS:
            print("==", c)
            for a, b in exemplos[c][:15]:
                print("  ", repr(a), "->", repr(b))


if __name__ == "__main__":
    main()
