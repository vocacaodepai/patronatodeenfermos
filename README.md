# Patronato de Enfermos

Site/app responsivo (PWA instalável) que indica a paróquia mais próxima de cada hospital ou clínica
(Rio, Niterói, São Gonçalo e Baixada) para pedir a Unção dos Enfermos.

## Rodar
Sem build. Basta servir a pasta: `npx http-server .` e abrir no navegador (no celular: "Adicionar à tela inicial").

## Dados (`data/`)
Gerados por `tools/` a partir de fontes abertas:
- **Hospitais e clínicas** (com internação ou centro cirúrgico): CNES, Ministério da Saúde (`dadosabertos.saude.gov.br`) — ~8.900 locais no Brasil.
- **Igrejas católicas**: Overture Maps Places (derivado de OpenStreetMap e outras fontes) — ~25 mil, ~16 mil com telefone.
- `data/<UF>.json`: hospitais do estado + as 5 paróquias mais próximas de cada um (`N_IGREJAS` em `build_dados.py`). `data/index.json`: usado no "perto de mim".

Regerar tudo, na ordem certa: `tools/gerar_tudo.sh [pasta_das_entradas] [pasta_saida]` (padrões `/tmp/claude-0/data` e `data/`). Etapas: `prep_hospitais.py` (CNES + municípios IBGE, feito antes e guardado em `hosp.pkl`/`susp.pkl`) → `build_dados.py` (+ parquet do Overture e `geo_fix.jsonl` das coordenadas corrigidas; chama `normalizar_nomes.py`) → `normalizar_nomes.py` → `aplicar_ajustes.py` (contatos e indicações de `ajustes_manuais.json`) → `aplicar_sites.py` (resultados de `sites_check*.jsonl`, `sites_check2*.jsonl` e `sites_confirma.jsonl`). Com `VERIFICAR_NOVOS=1` testa antes, pela internet, os sites que ainda não têm resultado (`verificar_sites.py --ignorar ...` e `verificar_sites_2.py`, gravando `sites_check_novos*.jsonl`). Se rodar só parte das etapas, as correções das outras se perdem.
**Ranking das igrejas:** distância em linha reta + penalidade de 3 km para capela/oratório/comunidade/casa e de 6 km para registros que não são paróquia (pastoral, grupo, terço, movimento, seminário, colégio, missão, retiro, diocese/cúria etc.), que só aparecem se não houver coisa melhor; quase-duplicatas (mesmo nome a menos de 300 m) são unidas; sempre 5 vínculos distintos, mesmo que seja preciso ir mais longe (o app avisa acima de 10 km). Depois de escolhidas, as igrejas são mostradas por distância crescente; as de curadoria (`curadoria.json`, `ajustes_manuais.json`) vão na frente.
**Nomes em português:** `tools/normalizar_nomes.py` (usa o léxico `tools/lexico_ptbr.py`) traduz nomes de igrejas em inglês (Church of… → Igreja de…), restaura acentos e cedilha, corrige maiúsculas/minúsculas, expande abreviações (N. S. → Nossa Senhora, R. → Rua) e remove lixo de cadastro (" - Cdd/Rj", "/SP", "Ltda"). `build_dados.py` já o chama no fim; se você regerar os JSON de outro jeito, rode `python3 tools/normalizar_nomes.py` depois (é idempotente; `--dry --exemplos` só mostra o que mudaria). Não mexe em ids, tipo, telefones, e-mails, sites, coordenadas, distâncias nem em `data/index.json`.
`tools/curadoria.json` força paróquias específicas para um hospital (ex.: Barra D'Or → Nossa Senhora da Vitória / Península).

**Localização:** as coordenadas do CNES têm erros (ex.: Hospital Rio Mar vinha no Centro). `tools/suspeitas.py` marca ~20% como suspeitas e `tools/geocodificar.py` as corrige pelo nome/endereço no OpenStreetMap (Nominatim, 1 consulta/s). Cada local recebe um nível de precisão (exata, pela rua, pelo bairro, pelo município) e o site avisa quando não é exata. Auditoria de 250 locais não suspeitos: mediana de erro de 37 m, ~3% com erro > 3 km.

**Sites das paróquias:** `tools/verificar_sites.py` testa cada link (prefere https), `tools/verificar_sites_2.py` retesta os que falharam (minúsculas, com/sem www) e `tools/aplicar_sites.py` corrige o endereço ou remove o botão quando o site não abre ou só leva à página inicial genérica do domínio. Na 1ª varredura (4.194 sites): 2.860 abriam, 114 só barravam robôs e 1.220 falharam; depois da correção sobraram 3.060 sites distintos.

**Só Igreja Católica Apostólica Romana:** `tools/exclusoes_nao_romanas.json` define as regras. Uma igreja só entra se a fonte a classificar como católica romana e o NOME indicar igreja/devoção católica; saem ICAB, ortodoxas, anglicanas, independentes, outras religiões e denominações (umbanda, espiritismo, evangélicas, pentecostais etc.) e perfis que não são a igreja (Pascom, cúrias, grupos). "Região/Residência Episcopal" e "São Pio X" não são confundidos.

**Igrejas duplicadas e nomes:** `tools/unir_duplicatas.py` une registros da mesma igreja (mesmo nome/endereço ou poucos metros de distância; escolhe o tipo mais específico: Santuário, Basílica, Catedral), corrige "Paróquia" para "Santuário/Basílica" quando o próprio perfil da igreja diz isso, e conserta telefones sem DDD (remove os inválidos). Entidades que não são igrejas (diocese, vicariato, secretaria, salão, pastoral, Pascom...) saem da base.

**Limitações:** distância em linha reta (tempo = estimativa); telefones e endereços podem estar desatualizados; nomes do CNES/Overture vêm com erros de acento e caixa (corrigidos por regras e léxico em `normalizar_nomes.py`, mas nomes próprios raros podem ficar sem acento); nem toda igreja do Overture é paróquia-sede.

## Marca (`assets/`)
`logo.png` (logo oficial enviada pelo cliente), `logo-sm.png`, `icon-192.png`, `icon-512.png`. Cores: azul #142536, ouro #B98A3A / #F0CC85, creme #F7F1E3.
