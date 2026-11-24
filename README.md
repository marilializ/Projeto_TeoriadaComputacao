# Caminho mínimo — Teoria da Computação

Base reproduzível para comparar Dijkstra com heap e Bellman–Ford em Python 3 e C11. As quatro implementações recebem **o mesmo grafo dirigido e a mesma origem**. O PDF do enunciado foi consultado para definir o escopo e a metodologia.

## Arquitetura e contrato

| Caminho | Função |
|---|---|
| `python/sp/` | Leitor, estruturas e algoritmos em Python |
| `c/` | Leitor, estruturas e algoritmos em C11 |
| `scripts/generate.py` | Grafos determinísticos |
| `scripts/benchmark.py` | Medição de tempo das 4 versões sobre as mesmas entradas |
| `scripts/memory.py` e `c/peakrss.c` | Medição de pico de memória (bônus) com processos limpos |
| `scripts/plot.py` | Gráficos e tabelas a partir dos resultados |
| `scripts/environment.py` | Registro do ambiente de execução |
| `scripts/run_all.sh` | Campanha completa em um comando |
| `docs/progresso.md` | Análise de casos e anotações para o relatório |
| `tests/` e `data/fixtures/` | Corretude e entradas conhecidas |
| `results/` | Resultados da campanha final (dados brutos, resumos, gráficos, ambiente) |

Entrada em texto: primeira linha `V E origem`; depois, exatamente `E` linhas `u v peso`. Vértices são inteiros de `0` a `V-1`, arestas são **dirigidas**, pesos são inteiros de `-1000000` a `1000000`, e a origem deve existir. Arestas paralelas são aceitas. **A comparação das quatro implementações usa somente pesos não negativos**, pois Dijkstra rejeita qualquer peso negativo. Bellman–Ford aceita pesos negativos e rejeita ciclos negativos alcançáveis pela origem; esses casos são testados separadamente. Ciclos negativos inalcançáveis não afetam o resultado da origem. Vértices inalcançáveis têm distância `null` no JSON. O resultado é a lista de distâncias a partir da origem; predecessores e reconstrução de caminhos não fazem parte do contrato inicial.

Cada execução escreve uma linha JSON com `algorithm`, `distances` e `elapsed_ns`. A ordem das distâncias é a ordem dos vértices. `elapsed_ns` é medido em volta **apenas da função do algoritmo**, depois da leitura e antes da serialização. Em erro de entrada, o programa termina com código diferente de zero. Cada algoritmo tem seu próprio arquivo; os leitores/estruturas são compartilhados dentro da linguagem.

## Compilar, executar e testar

Requisitos: Python 3.10+ e compilador C11 com `clock_gettime`. Funciona em **Linux, WSL e macOS**.

> **Windows:** use o WSL e clone o repositório *dentro* do WSL (`cd ~ && git clone ...`). Um clone feito pelo Git do Windows converte os arquivos para CRLF.

Na raiz do projeto:

```sh
make
make test
python3 scripts/generate.py --vertices 32 --edges-per-vertex 4 --seed 2026 --case random --output /tmp/grafo.txt
python3 -m python.sp dijkstra /tmp/grafo.txt
python3 -m python.sp bellman-ford /tmp/grafo.txt
./build/shortest_path dijkstra /tmp/grafo.txt
./build/shortest_path bellman-ford /tmp/grafo.txt
```

`make clean` remove os executáveis (`build/`). Os testes comparam as quatro respostas com resultados conhecidos (inalcançáveis, arestas paralelas, pesos zero), testam pesos e ciclos negativos no Bellman–Ford e, em `test_cross_check.py`, comparam as quatro implementações com Floyd–Warshall em grafos gerados de todos os casos.

## Reproduzir a campanha completa

Instale o matplotlib (só para os gráficos):

```sh
sudo apt install python3-matplotlib      # Ubuntu / WSL
python3 -m pip install -r requirements-plot.txt   # macOS
```

Depois, com o computador sem outras cargas:

```sh
sh scripts/run_all.sh
```

O script compila, roda os testes, grava o ambiente em `results/environment.json` (CPU, RAM, SO, versões, flags e commit), mede o tempo dos quatro casos com 15 repetições e semente 2026, mede a memória (`results/memory.csv`) e gera `results/plots/*.png` e `results/tabelas.md`. Leva de 10 a 20 minutos. `REPEATS=30 sh scripts/run_all.sh` muda o número de repetições.

| Caso | Grafo | Tamanhos (V) | Papel na análise |
|---|---|---|---|
| `random` | ~4 arestas por vértice, ordem embaralhada | 2048 … 262144 | caso médio dos dois |
| `chain-forward` | fila `0→1→…` em ordem direta | 4096 … 524288 | melhor caso do Bellman–Ford (2 passes, Θ(E)); Dijkstra Θ(V+E) |
| `chain` | fila em ordem reversa | 256 … 16384 | pior caso do Bellman–Ford (V−1 passes, Θ(V·E)); Dijkstra Θ(V+E) |
| `dense` | grafo completo, E = V(V−1) | 32 … 1024 | caso mais pesado do Dijkstra com heap |

Cada execução é verificada (as quatro respostas precisam ser iguais). `results/<caso>.csv` guarda cada tempo e `results/<caso>_summary.csv` guarda média, desvio padrão amostral e duas razões:

- `mean_over_bound`: tempo ÷ limite do enunciado, `(V+E)·log₂V` para Dijkstra e `V·E` para Bellman–Ford;
- `mean_over_case`: tempo ÷ custo esperado **do caso** (tabela abaixo). Deve tender a uma constante quando a análise está certa.

| | chain-forward | random | dense | chain |
|---|---|---|---|---|
| Dijkstra | V+E | (V+E)·log V | (V+E)·log V | V+E |
| Bellman–Ford | E | E·log V | E | V·E |

Gráficos gerados por caso: `<caso>_tempo.png` (medido × curva teórica, Dijkstra × Bellman–Ford, um painel por linguagem), `<caso>_razao.png` (T/f) e `<caso>_python_vs_c.png`. Também: `casos_<algoritmo>.png` (melhor/médio/pior) e `memoria.png` (pico de memória × V+E, bônus). A análise dos casos está em `docs/progresso.md`.

> `plot.py` lê **todos** os `*_summary.csv` da pasta indicada. Guarde medições de teste fora de `results/` para não misturá-las com a campanha final.

`elapsed_ns` mede apenas a função do algoritmo, depois da leitura e antes da serialização. Não há JIT (CPython e C compilado), então não há aquecimento.

**Memória (bônus):** `scripts/memory.py` grava `results/memory.csv` com o pico de memória residente de cada programa, medido por `build/peakrss` (lançador mínimo em C, `c/peakrss.c`). O lançador existe porque um filho criado direto pelo benchmark em Python herda, no `ru_maxrss`, a memória do processo pai. A coluna `net_kib` desconta a base (o mesmo programa com um grafo vazio). Os arquivos `*_summary.csv` da campanha de 23/11 ainda trazem uma coluna `mean_maxrss_kib` medida do jeito antigo: ela está **contaminada** por esse efeito e não deve ser usada.

A implementação Python do heap usa entradas repetidas com descarte das obsoletas, com limite `O(E log E)`; como `E ≤ V²`, isso é `O(E log V)`, a mesma classe da versão C com decrease-key `O((V+E) log V)`.

O problema vizinho indicado no PDF é o **caminho simples mais longo (NP-difícil)**. A discussão é teórica, sem implementação.

## Resultados da campanha final

Medidos em 23/11/2026 num Intel Core i5-1334U (7,6 GiB de RAM), Ubuntu 24.04 no WSL2, Python 3.12.3 e gcc 13.3 com `-O2`, no commit `9147fe0`. Os dados estão em `results/`, com resumo em `results/tabelas.md` e gráficos em `results/plots/`. A análise completa está no relatório da equipe.
