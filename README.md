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
`logo-mark.svg`, `logo-full.svg`, `icon-192.png`, `icon-512.png`. Cores: azul #14244A, ouro #B58A2E, roxo litúrgico #4A2270, creme #FBF7EE.
