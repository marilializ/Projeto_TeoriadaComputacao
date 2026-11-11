# Caminho mínimo — Teoria da Computação

Base reproduzível para comparar Dijkstra com heap e Bellman–Ford em Python 3 e C11. As quatro implementações recebem **o mesmo grafo dirigido e a mesma origem**. O PDF do enunciado foi consultado; `sources/` permanece intacto.

## Arquitetura e contrato

| Caminho | Função |
|---|---|
| `python/sp/` | Leitor, estruturas e algoritmos em Python |
| `c/` | Leitor, estruturas e algoritmos em C11 |
| `scripts/generate.py` | Grafos determinísticos |
| `scripts/benchmark.py` e `scripts/plot.py` | Medições, resumo CSV e gráficos |
| `tests/` e `data/fixtures/` | Corretude e entradas conhecidas |
| `analysis/` | Roteiro do relatório e interpretação |

Entrada em texto: primeira linha `V E origem`; depois, exatamente `E` linhas `u v peso`. Vértices são inteiros de `0` a `V-1`, arestas são **dirigidas**, pesos são inteiros de `-1000000` a `1000000`, e a origem deve existir. Arestas paralelas são aceitas. **A comparação das quatro implementações usa somente pesos não negativos**, pois Dijkstra rejeita qualquer peso negativo. Bellman–Ford aceita pesos negativos e rejeita ciclos negativos alcançáveis pela origem; esses casos são testados separadamente. Ciclos negativos inalcançáveis não afetam o resultado da origem. Vértices inalcançáveis têm distância `null` no JSON. O resultado é a lista de distâncias a partir da origem; predecessores e reconstrução de caminhos não fazem parte do contrato inicial.

Cada execução escreve uma linha JSON com `algorithm`, `distances` e `elapsed_ns`. A ordem das distâncias é a ordem dos vértices. `elapsed_ns` é medido em volta **apenas da função do algoritmo**, depois da leitura e antes da serialização. Em erro de entrada, o programa termina com código diferente de zero. Cada algoritmo tem seu próprio arquivo; os leitores/estruturas são compartilhados dentro da linguagem.

## Compilar, executar e testar

Requisitos: Python 3.10+ e compilador C11 com `clock_gettime` (macOS ou Linux). Na raiz do projeto:

```sh
make
make test
python3 scripts/generate.py --vertices 32 --edges-per-vertex 4 --seed 2026 --case random --output /tmp/grafo.txt
python3 -m python.sp dijkstra /tmp/grafo.txt
python3 -m python.sp bellman-ford /tmp/grafo.txt
./build/shortest_path dijkstra /tmp/grafo.txt
./build/shortest_path bellman-ford /tmp/grafo.txt
```

`make clean` remove o executável gerado. Os testes comparam as quatro respostas com resultados conhecidos, inclusive vértices inalcançáveis, arestas paralelas e pesos zero. Testes exclusivos de Bellman–Ford cobrem pesos negativos e ciclos negativos.

## Experimentos

```sh
python3 scripts/benchmark.py --sizes 32 64 128 256 512 1024 --repeats 15 --seed 2026 --case random --edges-per-vertex 4 --output results/random.csv
```

O script cria **uma entrada por tamanho**, executa as quatro versões sobre o mesmo arquivo, confere as distâncias em cada repetição e grava `results/random.csv` com cada tempo e `results/random_summary.csv` com média e desvio padrão amostral. A tabela resumida inclui fatores teóricos e a razão `tempo/fator`. Não há medições pré-preenchidas. Execute a campanha final em **um computador**, sem outras cargas intensas, e registre CPU, RAM, sistema operacional, versões de Python/compilador e flags (`-O2 -std=c11`). Os seis tamanhos padrão crescem geometricamente; aumente-os se os tempos forem pequenos demais. Para uma análise mais robusta, repita toda a campanha e preserve os dados brutos.

Para gerar dois gráficos PNG após a campanha, instale a dependência opcional e rode:

```sh
python3 -m pip install -r requirements-plot.txt
python3 scripts/plot.py results/random_summary.csv --output-dir results/plots
```

Os casos do gerador são `random`, `chain`, `disconnected` e `dense`. `chain` põe arestas em ordem reversa e força vários passes do Bellman–Ford; `disconnected` testa inalcançáveis; `dense` acentua o custo por arestas. Não rotule um caso como melhor ou pior universal sem justificar a implementação e a ordem das arestas. Compare teoria e medição com gráfico log-log ou com `T/f(V,E)`, usando `f_D=(V+E)log₂(V)` e `f_B=VE` para as instâncias simples geradas. A implementação Python do heap usa entradas repetidas e descarte de entradas obsoletas; em grafos arbitrários com muitas arestas paralelas, seu limite é `O(E log E)`; o heap C permite diminuir chaves e tem o limite `O((V+E) log V)` pedido no enunciado. Discutam essa diferença na análise.

O problema vizinho indicado no PDF é o **caminho simples mais longo (NP-difícil)**. A discussão é teórica, sem implementação.

