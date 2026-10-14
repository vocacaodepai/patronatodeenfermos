# Patronato de Enfermos

Site/app responsivo (PWA instalável) que indica a paróquia mais próxima de cada hospital ou clínica
(Rio, Niterói, São Gonçalo e Baixada) para pedir a Unção dos Enfermos.

## Rodar
Sem build. Basta servir a pasta: `npx http-server .` e abrir no navegador (no celular: "Adicionar à tela inicial").

## Dados (`js/data.js`)
- `HOSPITALS`: hospitais/clínicas. `paroquias: [ids]` força a indicação (curadoria); sem isso, vale a menor distância.
- `PARISHES`: paróquias com `tel`, `email`, `whatsapp`, `padre`, `verificado`.
- **A base atual é inicial**: coordenadas aproximadas e contatos ainda em branco. Valide cada item antes do lançamento.
- Tempo estimado = distância em linha reta × 1,35 a 25 km/h (apenas estimativa).

## Marca (`assets/`)
`logo.png` (logo oficial enviada pelo cliente), `logo-sm.png`, `icon-192.png`, `icon-512.png`. Cores: azul #142536, ouro #B98A3A / #F0CC85, creme #F7F1E3.
