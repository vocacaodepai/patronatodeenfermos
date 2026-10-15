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
`tools/curadoria.json` força paróquias específicas para um hospital (ex.: Barra D'Or → Nossa Senhora da Vitória / Península).

**Localização:** as coordenadas do CNES têm erros (ex.: Hospital Rio Mar vinha no Centro). `tools/suspeitas.py` marca ~20% como suspeitas e `tools/geocodificar.py` as corrige pelo nome/endereço no OpenStreetMap (Nominatim, 1 consulta/s). Cada local recebe um nível de precisão (exata, pela rua, pelo bairro, pelo município) e o site avisa quando não é exata. Auditoria de 250 locais não suspeitos: mediana de erro de 37 m, ~3% com erro > 3 km.

**Limitações:** distância em linha reta (tempo = estimativa); telefones e endereços podem estar desatualizados; nomes do CNES vêm sem acento (restaurados parcialmente); nem toda igreja do Overture é paróquia-sede.

## Marca (`assets/`)
`logo.png` (logo oficial enviada pelo cliente), `logo-sm.png`, `icon-192.png`, `icon-512.png`. Cores: azul #142536, ouro #B98A3A / #F0CC85, creme #F7F1E3.
