# Patronato de Enfermos

Site/app responsivo (PWA instalável) que indica a paróquia mais próxima de cada hospital ou clínica
(Rio, Niterói, São Gonçalo e Baixada) para pedir a Unção dos Enfermos.

## Rodar
Sem build. Basta servir a pasta: `npx http-server .` e abrir no navegador (no celular: "Adicionar à tela inicial").

## Dados (`data/`)
Gerados por `tools/` a partir de fontes abertas:
- **Hospitais e clínicas** (com internação ou centro cirúrgico): CNES, Ministério da Saúde (`dadosabertos.saude.gov.br`) — ~8.900 locais no Brasil.
- **Igrejas católicas**: Overture Maps Places (derivado de OpenStreetMap e outras fontes) — ~25 mil, ~16 mil com telefone.
- `data/<UF>.json`: hospitais do estado + as 3 paróquias mais próximas de cada um. `data/index.json`: usado no "perto de mim".

Regerar: `prep_hospitais.py` (CNES + municípios IBGE) → `build_dados.py` (+ parquet do Overture). Ver cabeçalho de cada script.
**Nomes em português:** `tools/normalizar_nomes.py` (usa o léxico `tools/lexico_ptbr.py`) traduz nomes de igrejas em inglês (Church of… → Igreja de…), restaura acentos e cedilha, corrige maiúsculas/minúsculas, expande abreviações (N. S. → Nossa Senhora, R. → Rua) e remove lixo de cadastro (" - Cdd/Rj", "/SP", "Ltda"). `build_dados.py` já o chama no fim; se você regerar os JSON de outro jeito, rode `python3 tools/normalizar_nomes.py` depois (é idempotente; `--dry --exemplos` só mostra o que mudaria). Não mexe em ids, tipo, telefones, e-mails, sites, coordenadas, distâncias nem em `data/index.json`.
`tools/curadoria.json` força paróquias específicas para um hospital (ex.: Barra D'Or → Nossa Senhora da Vitória / Península).

**Localização:** as coordenadas do CNES têm erros (ex.: Hospital Rio Mar vinha no Centro). `tools/suspeitas.py` marca ~20% como suspeitas e `tools/geocodificar.py` as corrige pelo nome/endereço no OpenStreetMap (Nominatim, 1 consulta/s). Cada local recebe um nível de precisão (exata, pela rua, pelo bairro, pelo município) e o site avisa quando não é exata. Auditoria de 250 locais não suspeitos: mediana de erro de 37 m, ~3% com erro > 3 km.

**Sites das paróquias:** `tools/verificar_sites.py` testa cada link (prefere https), `tools/verificar_sites_2.py` retesta os que falharam (minúsculas, com/sem www) e `tools/aplicar_sites.py` corrige o endereço ou remove o botão quando o site não abre ou só leva à página inicial genérica do domínio. Na 1ª varredura (4.194 sites): 2.860 abriam, 114 só barravam robôs e 1.220 falharam; depois da correção sobraram 3.060 sites distintos.

**Limitações:** distância em linha reta (tempo = estimativa); telefones e endereços podem estar desatualizados; nomes do CNES/Overture vêm com erros de acento e caixa (corrigidos por regras e léxico em `normalizar_nomes.py`, mas nomes próprios raros podem ficar sem acento); nem toda igreja do Overture é paróquia-sede.

## Marca (`assets/`)
`logo.png` (logo oficial enviada pelo cliente), `logo-sm.png`, `icon-192.png`, `icon-512.png`. Cores: azul #142536, ouro #B98A3A / #F0CC85, creme #F7F1E3.
