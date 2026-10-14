// BASE INICIAL — coordenadas aproximadas e telefones ainda NÃO levantados.
// Preencha `tel`, `email`, `whatsapp`, `padre` e marque `verificado: true` ao confirmar cada paróquia.
// `paroquias` em um hospital força a ordem de indicação (curadoria); sem ela, vale a distância.
window.PARISHES = [
  // Rio — Centro e Zona Sul
  { id: "catedral-rio", nome: "Catedral Metropolitana de São Sebastião", bairro: "Centro", cidade: "Rio de Janeiro", lat: -22.9111, lng: -43.1807 },
  { id: "candelaria", nome: "Igreja de Nossa Senhora da Candelária", bairro: "Centro", cidade: "Rio de Janeiro", lat: -22.9006, lng: -43.1766 },
  { id: "gloria", nome: "Paróquia Nossa Senhora da Glória do Outeiro", bairro: "Glória", cidade: "Rio de Janeiro", lat: -22.9209, lng: -43.1766 },
  { id: "sao-joao-botafogo", nome: "Paróquia São João Batista", bairro: "Botafogo", cidade: "Rio de Janeiro", lat: -22.9498, lng: -43.1857 },
  { id: "copacabana", nome: "Paróquia Nossa Senhora de Copacabana", bairro: "Copacabana", cidade: "Rio de Janeiro", lat: -22.9697, lng: -43.1869 },
  { id: "paz-ipanema", nome: "Paróquia Nossa Senhora da Paz", bairro: "Ipanema", cidade: "Rio de Janeiro", lat: -22.9846, lng: -43.2026 },
  { id: "sao-jose-lagoa", nome: "Paróquia São José da Lagoa", bairro: "Lagoa", cidade: "Rio de Janeiro", lat: -22.9690, lng: -43.2100 },
  { id: "conceicao-gavea", nome: "Paróquia Nossa Senhora da Conceição da Gávea", bairro: "Gávea", cidade: "Rio de Janeiro", lat: -22.9780, lng: -43.2330 },
  // Rio — Zona Norte
  { id: "santo-afonso", nome: "Paróquia Santo Afonso", bairro: "Tijuca", cidade: "Rio de Janeiro", lat: -22.9261, lng: -43.2323 },
  { id: "sao-francisco-xavier", nome: "Paróquia São Francisco Xavier", bairro: "Maracanã", cidade: "Rio de Janeiro", lat: -22.9157, lng: -43.2330 },
  { id: "sao-cristovao", nome: "Paróquia de São Cristóvão", bairro: "São Cristóvão", cidade: "Rio de Janeiro", lat: -22.8995, lng: -43.2215 },
  { id: "penha", nome: "Igreja de Nossa Senhora da Penha", bairro: "Penha", cidade: "Rio de Janeiro", lat: -22.8412, lng: -43.2790 },
  { id: "meier", nome: "Paróquia do Méier (Matriz)", bairro: "Méier", cidade: "Rio de Janeiro", lat: -22.9015, lng: -43.2790 },
  { id: "madureira", nome: "Paróquia de Madureira (Matriz)", bairro: "Madureira", cidade: "Rio de Janeiro", lat: -22.8730, lng: -43.3380 },
  // Rio — Zona Oeste e Barra
  { id: "vitoria-barra", nome: "Paróquia Nossa Senhora da Vitória", bairro: "Barra da Tijuca", cidade: "Rio de Janeiro", lat: -23.0000, lng: -43.3650 },
  { id: "antonio-peninsula", nome: "Paróquia Santo Antônio (Península)", bairro: "Barra da Tijuca", cidade: "Rio de Janeiro", lat: -23.0020, lng: -43.3750 },
  { id: "jacarepagua", nome: "Paróquia de Jacarepaguá (Matriz)", bairro: "Jacarepaguá", cidade: "Rio de Janeiro", lat: -22.9340, lng: -43.3450 },
  { id: "bangu", nome: "Paróquia de Bangu (Matriz)", bairro: "Bangu", cidade: "Rio de Janeiro", lat: -22.8760, lng: -43.4650 },
  { id: "realengo", nome: "Paróquia de Realengo (Matriz)", bairro: "Realengo", cidade: "Rio de Janeiro", lat: -22.8800, lng: -43.4290 },
  { id: "campo-grande", nome: "Paróquia de Campo Grande (Matriz)", bairro: "Campo Grande", cidade: "Rio de Janeiro", lat: -22.9040, lng: -43.5600 },
  // Niterói e São Gonçalo
  { id: "catedral-niteroi", nome: "Catedral de São João Batista", bairro: "Centro", cidade: "Niterói", lat: -22.8960, lng: -43.1240 },
  { id: "icarai", nome: "Paróquia de Icaraí (Matriz)", bairro: "Icaraí", cidade: "Niterói", lat: -22.9070, lng: -43.1110 },
  { id: "barreto", nome: "Paróquia do Barreto (Matriz)", bairro: "Barreto", cidade: "Niterói", lat: -22.8760, lng: -43.1290 },
  { id: "charitas", nome: "Paróquia de Charitas / São Francisco", bairro: "Charitas", cidade: "Niterói", lat: -22.9300, lng: -43.1020 },
  { id: "sao-goncalo", nome: "Paróquia de São Gonçalo (Matriz)", bairro: "Centro", cidade: "São Gonçalo", lat: -22.8270, lng: -43.0530 },
  // Baixada Fluminense
  { id: "catedral-caxias", nome: "Catedral de Santo Antônio", bairro: "Centro", cidade: "Duque de Caxias", lat: -22.7860, lng: -43.3110 },
  { id: "catedral-ni", nome: "Catedral de Santo Antônio", bairro: "Centro", cidade: "Nova Iguaçu", lat: -22.7590, lng: -43.4510 },
  { id: "sao-joao-meriti", nome: "Paróquia de São João de Meriti (Matriz)", bairro: "Centro", cidade: "São João de Meriti", lat: -22.8040, lng: -43.3720 },
  { id: "nilopolis", nome: "Paróquia de Nilópolis (Matriz)", bairro: "Centro", cidade: "Nilópolis", lat: -22.8070, lng: -43.4240 },
  { id: "belford-roxo", nome: "Paróquia de Belford Roxo (Matriz)", bairro: "Centro", cidade: "Belford Roxo", lat: -22.7640, lng: -43.3990 },
].map(p => Object.assign({ tel: "", email: "", whatsapp: "", padre: "", verificado: false }, p));

window.HOSPITALS = [
  // Rio — Centro e Zona Sul
  { id: "h-santa-casa", nome: "Santa Casa da Misericórdia do Rio de Janeiro", bairro: "Centro", cidade: "Rio de Janeiro", regiao: "Rio · Centro", lat: -22.9140, lng: -43.1720 },
  { id: "h-souza-aguiar", nome: "Hospital Municipal Souza Aguiar", bairro: "Centro", cidade: "Rio de Janeiro", regiao: "Rio · Centro", lat: -22.9115, lng: -43.1895 },
  { id: "h-inca", nome: "INCA — Instituto Nacional de Câncer (Cruz Vermelha)", bairro: "Centro", cidade: "Rio de Janeiro", regiao: "Rio · Centro", lat: -22.9097, lng: -43.1925 },
  { id: "h-samaritano", nome: "Hospital Samaritano", bairro: "Botafogo", cidade: "Rio de Janeiro", regiao: "Rio · Zona Sul", lat: -22.9490, lng: -43.1895 },
  { id: "h-procardiaco", nome: "Hospital Pró-Cardíaco", bairro: "Botafogo", cidade: "Rio de Janeiro", regiao: "Rio · Zona Sul", lat: -22.9525, lng: -43.1850 },
  { id: "h-copa-dor", nome: "Hospital Copa D'Or", bairro: "Copacabana", cidade: "Rio de Janeiro", regiao: "Rio · Zona Sul", lat: -22.9663, lng: -43.1914 },
  { id: "h-copa-star", nome: "Hospital Copa Star", bairro: "Copacabana", cidade: "Rio de Janeiro", regiao: "Rio · Zona Sul", lat: -22.9668, lng: -43.1920 },
  { id: "h-sao-lucas", nome: "Hospital São Lucas", bairro: "Copacabana", cidade: "Rio de Janeiro", regiao: "Rio · Zona Sul", lat: -22.9690, lng: -43.1910 },
  { id: "h-lagoa", nome: "Hospital Federal da Lagoa", bairro: "Lagoa", cidade: "Rio de Janeiro", regiao: "Rio · Zona Sul", lat: -22.9660, lng: -43.2150 },
  { id: "h-ipanema", nome: "Hospital Federal de Ipanema", bairro: "Ipanema", cidade: "Rio de Janeiro", regiao: "Rio · Zona Sul", lat: -22.9850, lng: -43.2100 },
  { id: "h-miguel-couto", nome: "Hospital Municipal Miguel Couto", bairro: "Gávea", cidade: "Rio de Janeiro", regiao: "Rio · Zona Sul", lat: -22.9830, lng: -43.2290 },
  // Rio — Zona Norte
  { id: "h-quinta-dor", nome: "Hospital Quinta D'Or", bairro: "São Cristóvão", cidade: "Rio de Janeiro", regiao: "Rio · Zona Norte", lat: -22.9005, lng: -43.2223 },
  { id: "h-andarai", nome: "Hospital Federal do Andaraí", bairro: "Andaraí", cidade: "Rio de Janeiro", regiao: "Rio · Zona Norte", lat: -22.9250, lng: -43.2490 },
  { id: "h-gaffree", nome: "Hospital Universitário Gaffrée e Guinle", bairro: "Tijuca", cidade: "Rio de Janeiro", regiao: "Rio · Zona Norte", lat: -22.9260, lng: -43.2310 },
  { id: "h-pedro-ernesto", nome: "Hospital Universitário Pedro Ernesto (UERJ)", bairro: "Vila Isabel", cidade: "Rio de Janeiro", regiao: "Rio · Zona Norte", lat: -22.9120, lng: -43.2530 },
  { id: "h-badim", nome: "Hospital Badim", bairro: "Maracanã", cidade: "Rio de Janeiro", regiao: "Rio · Zona Norte", lat: -22.9150, lng: -43.2330 },
  { id: "h-salgado-filho", nome: "Hospital Municipal Salgado Filho", bairro: "Méier", cidade: "Rio de Janeiro", regiao: "Rio · Zona Norte", lat: -22.9020, lng: -43.2760 },
  { id: "h-bonsucesso", nome: "Hospital Federal de Bonsucesso", bairro: "Bonsucesso", cidade: "Rio de Janeiro", regiao: "Rio · Zona Norte", lat: -22.8710, lng: -43.2530 },
  { id: "h-clementino", nome: "Hospital Universitário Clementino Fraga Filho (UFRJ)", bairro: "Ilha do Fundão", cidade: "Rio de Janeiro", regiao: "Rio · Zona Norte", lat: -22.8570, lng: -43.2280 },
  { id: "h-getulio", nome: "Hospital Estadual Getúlio Vargas", bairro: "Penha", cidade: "Rio de Janeiro", regiao: "Rio · Zona Norte", lat: -22.8420, lng: -43.2800 },
  // Rio — Barra, Jacarepaguá e Zona Oeste
  { id: "h-barra-dor", nome: "Hospital Barra D'Or", bairro: "Barra da Tijuca", cidade: "Rio de Janeiro", regiao: "Rio · Barra e Jacarepaguá", lat: -22.9951, lng: -43.3689, paroquias: ["vitoria-barra", "antonio-peninsula"] },
  { id: "h-rios-dor", nome: "Hospital Rios D'Or", bairro: "Barra da Tijuca", cidade: "Rio de Janeiro", regiao: "Rio · Barra e Jacarepaguá", lat: -22.9972, lng: -43.3600 },
  { id: "h-unimed-barra", nome: "Hospital Unimed-Rio (Barra)", bairro: "Barra da Tijuca", cidade: "Rio de Janeiro", regiao: "Rio · Barra e Jacarepaguá", lat: -23.0020, lng: -43.3580 },
  { id: "h-perinatal", nome: "Perinatal Barra", bairro: "Barra da Tijuca", cidade: "Rio de Janeiro", regiao: "Rio · Barra e Jacarepaguá", lat: -22.9990, lng: -43.3660 },
  { id: "h-lourenco-jorge", nome: "Hospital Municipal Lourenço Jorge", bairro: "Barra da Tijuca", cidade: "Rio de Janeiro", regiao: "Rio · Barra e Jacarepaguá", lat: -22.9990, lng: -43.3700 },
  { id: "h-cardoso-fontes", nome: "Hospital Federal Cardoso Fontes", bairro: "Jacarepaguá", cidade: "Rio de Janeiro", regiao: "Rio · Barra e Jacarepaguá", lat: -22.9390, lng: -43.3390 },
  { id: "h-albert-schweitzer", nome: "Hospital Municipal Albert Schweitzer", bairro: "Realengo", cidade: "Rio de Janeiro", regiao: "Rio · Zona Oeste", lat: -22.8780, lng: -43.4440 },
  { id: "h-rocha-faria", nome: "Hospital Municipal Rocha Faria", bairro: "Campo Grande", cidade: "Rio de Janeiro", regiao: "Rio · Zona Oeste", lat: -22.9086, lng: -43.5720 },
  // Niterói e São Gonçalo
  { id: "h-antonio-pedro", nome: "Hospital Universitário Antônio Pedro (UFF)", bairro: "Centro", cidade: "Niterói", regiao: "Niterói e São Gonçalo", lat: -22.8975, lng: -43.1250 },
  { id: "h-icarai", nome: "Hospital Icaraí", bairro: "Icaraí", cidade: "Niterói", regiao: "Niterói e São Gonçalo", lat: -22.9050, lng: -43.1100 },
  { id: "h-orencio", nome: "Hospital Orêncio de Freitas", bairro: "Barreto", cidade: "Niterói", regiao: "Niterói e São Gonçalo", lat: -22.8800, lng: -43.1300 },
  { id: "h-azevedo-lima", nome: "Hospital Estadual Azevedo Lima", bairro: "Fonseca", cidade: "Niterói", regiao: "Niterói e São Gonçalo", lat: -22.8850, lng: -43.1000 },
  { id: "h-oceanico", nome: "Hospital Oceânico", bairro: "Charitas", cidade: "Niterói", regiao: "Niterói e São Gonçalo", lat: -22.9300, lng: -43.0980 },
  { id: "h-alberto-torres", nome: "Hospital Estadual Alberto Torres", bairro: "Colubandê", cidade: "São Gonçalo", regiao: "Niterói e São Gonçalo", lat: -22.8520, lng: -43.0650 },
  // Baixada Fluminense
  { id: "h-adao-pereira", nome: "Hospital Estadual Adão Pereira Nunes", bairro: "Saracuruna", cidade: "Duque de Caxias", regiao: "Baixada Fluminense", lat: -22.6820, lng: -43.2740 },
  { id: "h-moacyr-carmo", nome: "Hospital Municipal Moacyr do Carmo", bairro: "Centro", cidade: "Duque de Caxias", regiao: "Baixada Fluminense", lat: -22.7850, lng: -43.3070 },
  { id: "h-geral-ni", nome: "Hospital Geral de Nova Iguaçu", bairro: "Centro", cidade: "Nova Iguaçu", regiao: "Baixada Fluminense", lat: -22.7580, lng: -43.4600 },
  { id: "h-posse", nome: "Hospital da Posse", bairro: "Posse", cidade: "Nova Iguaçu", regiao: "Baixada Fluminense", lat: -22.7620, lng: -43.4500 },
  { id: "h-meriti", nome: "Hospital Municipal de São João de Meriti", bairro: "Centro", cidade: "São João de Meriti", regiao: "Baixada Fluminense", lat: -22.8040, lng: -43.3720 },
  { id: "h-belford", nome: "Hospital Municipal de Belford Roxo", bairro: "Centro", cidade: "Belford Roxo", regiao: "Baixada Fluminense", lat: -22.7640, lng: -43.3990 },
];
