#!/usr/bin/env bash
# Regera data/*.json do zero, com todas as etapas na ordem certa.
# Uso: tools/gerar_tudo.sh [pasta_com_entradas] [pasta_saida]     (padrões: /tmp/claude-0/data  e  data/)
# Entradas esperadas (não vão para o git): susp.pkl, ov_br.parquet, mun.csv, geo_fix.jsonl e os resultados
# da verificação de sites (sites_check.jsonl, sites_check2.jsonl, sites_confirma.jsonl).
# Variáveis: N_IGREJAS (padrão 5) = vínculos por hospital; VERIFICAR_NOVOS=1 testa (na internet) os sites
# que ainda não têm resultado e grava em sites_check_novos.jsonl / sites_check_novos2.jsonl.
set -euo pipefail
cd "$(dirname "$0")/.."
IN="${1:-/tmp/claude-0/data}"; OUT="${2:-data}"
export N_IGREJAS="${N_IGREJAS:-5}"

# 1) hospitais + paróquias mais próximas (já chama normalizar_nomes.py no fim) — recria data/index.json também
python3 tools/build_dados.py "$IN/susp.pkl" "$IN/ov_br.parquet" "$IN/mun.csv" "$OUT" "$IN/geo_fix.jsonl"
# 2) normalização dos nomes em português (idempotente; build_dados já rodou, repetir é inofensivo)
python3 tools/normalizar_nomes.py --pasta "$OUT"
# 3) contatos e indicações manuais (ex.: Catedral de Niterói no Hospital de Clínicas do Ingá)
python3 tools/aplicar_ajustes.py "$OUT"
# 4) sites: verifica os que ainda não têm resultado (opcional) e aplica todas as rodadas + a confirmação
R1=("$IN/sites_check.jsonl"); R2=("$IN/sites_check2.jsonl")
if [ "${VERIFICAR_NOVOS:-0}" = "1" ]; then
  python3 tools/verificar_sites.py "$OUT" "$IN/sites_check_novos.jsonl" --ignorar "$IN/sites_check.jsonl" "$IN/sites_confirma.jsonl"
  python3 tools/verificar_sites_2.py "$IN/sites_check_novos.jsonl" "$IN/sites_check_novos2.jsonl"
fi
[ -f "$IN/sites_check_novos.jsonl" ] && R1+=("$IN/sites_check_novos.jsonl")
[ -f "$IN/sites_check_novos2.jsonl" ] && R2+=("$IN/sites_check_novos2.jsonl")
python3 tools/aplicar_sites.py "$OUT" --r1 "${R1[@]}" --r2 "${R2[@]}" --confirma "$IN/sites_confirma.jsonl"
