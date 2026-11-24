#!/bin/sh
# Campanha completa: compila, testa, registra o ambiente, mede os 4 casos e gera gráficos/tabelas.
# Uso (na raiz do projeto):   sh scripts/run_all.sh
# Funciona em Linux, WSL e macOS. Leva ~10-20 min; deixe o computador sem outras cargas.
set -eu
cd "$(dirname "$0")/.."

REPEATS=${REPEATS:-15}
SEED=${SEED:-2026}

echo "== Compilando e testando"
make
make test

echo "== Ambiente"
python3 scripts/environment.py --output results/environment.json

# Tamanhos por caso (escala geométrica, >= 6 tamanhos):
#  random / chain-forward: grafos esparsos, cabem tamanhos grandes
#  chain: pior caso do Bellman-Ford, Θ(V²) aqui (E = V-1); Python fica lento acima de 16384
#  dense: grafo completo, E = V(V-1); 1024 já são ~1 milhão de arestas
run_case() {
    case_name=$1
    shift
    echo "== Caso $case_name: V = $*"
    python3 scripts/benchmark.py --case "$case_name" --sizes "$@" \
        --repeats "$REPEATS" --seed "$SEED" --edges-per-vertex 4 \
        --output "results/$case_name.csv"
}

run_case random        2048 4096 8192 16384 32768 65536 131072 262144
run_case chain-forward 4096 8192 16384 32768 65536 131072 262144 524288
run_case chain         256 512 1024 2048 4096 8192 16384
run_case dense         32 64 128 256 512 1024

echo "== Memória (bônus): processos limpos via build/peakrss"
python3 scripts/memory.py --case random --output results/memory.csv

echo "== Gráficos e tabelas"
python3 scripts/plot.py results

echo "== Pronto: veja results/plots/ e results/tabelas.md"
