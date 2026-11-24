# Progresso do projeto — Caminho mínimo (Dijkstra × Bellman-Ford)

Atualizado em 24/11/2026. Entrega: **24/11 às 23:59**. Apresentações: 25/11 e 30/11.

## 1. Estado atual

- As 4 implementações (Dijkstra e Bellman-Ford, em C e Python) funcionam e estão testadas: **16 testes passando** (Linux/WSL e macOS).
- Ambiente de medição: **WSL (Ubuntu 24.04)**, Python 3.12.3, `cc -O2 -std=c11`.
- O repositório também roda no macOS. Os arquivos no GitHub usam final de linha LF.
  - Atenção: um clone feito pelo Git do **Windows** converte tudo para CRLF. Para rodar no WSL, clone dentro do próprio WSL (`cd ~ && git clone ...`).

## 2. O que mudou hoje

| Arquivo | Mudança | Motivo |
|---|---|---|
| `scripts/generate.py` | o caso `random` agora embaralha a ordem das arestas (`rng.shuffle`, com a mesma semente) | antes, a cadeia `0→1→2…` vinha sempre primeiro e em ordem direta, o que é um viés |
| `scripts/generate.py` | novo caso `chain-forward`: fila `0→1→…→V-1` em ordem direta | melhor caso explícito do Bellman-Ford |
| `scripts/benchmark.py` | aceita `--case chain-forward` | — |
| `tests/test_generator.py` | novo teste `test_chain_forward_order` | garante a ordem `(0,1),(1,2),…` |

## 3. Benchmark preliminar (não é a campanha final)

Caso `random`, 4 arestas por vértice, 15 repetições, **antes** do embaralhamento. Os valores são `T / f(n)`, com `f_D = (V+E)·log₂V` e `f_B = V·E`.

| V | Dijkstra C | Dijkstra Py | Bellman-Ford C | Bellman-Ford Py |
|---|---|---|---|---|
| 32 | 3,37 | 29,0 | 0,414 | 7,24 |
| 128 | 2,78 | 21,8 | 0,136 | 3,15 |
| 512 | 2,17 | 21,6 | 0,043 | 1,18 |
| 1024 | 2,94 | 17,2 | 0,021 | 0,57 |

O que observamos:
- **Dijkstra:** a razão fica aproximadamente constante, o que é consistente com Θ((V+E) log V).
- **Bellman-Ford:** a razão cai cerca de 20×. Em grafos aleatórios ele fica muito abaixo de V·E, e em C foi até mais rápido que o Dijkstra.
- **Python × C:** o Python foi de 6 a 10× mais lento no Dijkstra e de 17 a 26× mais lento no Bellman-Ford.
- O Dijkstra em C leva ~2,7 µs com V=32, o que é ruído. **Os tamanhos da campanha final precisam ser maiores.**

## 4. Análise de casos (base para os itens 2 e 3 do relatório)

### Bellman-Ford
O algoritmo para cedo quando um passe inteiro não altera nenhuma distância (`if (!changed) break`). O número de passes é limitado pelo **número de saltos do caminho mínimo mais longo**, e cada passe faz a distância avançar pelo menos um salto.

Exemplo com a fila `0→1→2→3→4`:
- **ordem direta** `(0,1),(1,2),(2,3),(3,4)`: as distâncias se propagam pela fila inteira em 1 passe, e o passe 2 só confirma → **Θ(E)**;
- **ordem reversa** `(3,4),(2,3),(1,2),(0,1)`: cada passe avança só um vértice → V−1 passes → **Θ(V·E)**.

Passes medidos no caso `random`:

| V | ordem antiga | embaralhada | `chain` |
|---|---|---|---|
| 32 | 4 | 5 | 31 |
| 1024 | 8 | 11 | 1023 |
| 65536 | 14 | 15 | 65535 |

Conclusão: em grafo aleatório esparso, os caminhos mínimos têm poucos saltos (crescem como ~log V). Por isso o caso médio fica perto de **E·log V**, muito abaixo do pior caso O(V·E). **No Bellman-Ford, o que define melhor e pior caso é a combinação de caminhos longos (em saltos) com a ordem das arestas.**

### Dijkstra
O custo vem do heap: V extrações e até E melhorias de distância (`rise`), cada uma custando O(log V).
- **Fila (`chain` / `chain-forward`):** o heap nunca passa de 1 elemento, então as operações custam O(1) → **Θ(V+E)**. O log desaparece.
- **Grafo completo (`dense`):** V−1 vértices entram no heap de uma vez e E ≈ V². No pior caso, cada aresta melhora uma distância → **O(V² log V)**.
  - Nesse cenário, o Dijkstra sem heap (com vetor) custa O(V²) e é melhor. O heap compensa em grafos **esparsos**. Isso entra no item 4 (aplicabilidade).
- **Python × C:** o Python usa lazy deletion, com o heap chegando a até E entradas, o que dá O(E log E). Como E ≤ V², vale log E ≤ 2 log V, então O(E log E) = O(E log V). Muda só a constante, não a classe.

### Resumo dos casos

| Caso | Dijkstra | Bellman-Ford |
|---|---|---|
| `chain-forward` | Θ(V+E) | **melhor**: Θ(E), 2 passes |
| `chain` | Θ(V+E) | **pior**: Θ(V·E), V−1 passes |
| `random` | médio: ~(V+E) log V | médio: ~E·log V |
| `dense` | ~Θ(E) com pesos aleatórios (poucas melhorias) | ~Θ(E), 3 a 5 passes |
| `dijkstra-worst` | **pior**: Θ(E·log V) = Θ((V+E) log V) | Θ(V+E), 2 passes |

Ressalva: com pesos aleatórios, o `dense` não força que toda aresta melhore uma distância. Em `results/operacoes.csv`, com V = 1024 só 4.790 das 1.047.552 arestas (0,5%) melhoram alguma distância, ~4,7·V, o que bate com o resultado de Noshita (1985): com pesos aleatórios, o número esperado de decrease-keys é O(V·log(E/V)). Por isso a razão T/((V+E) log V) cai no `dense`.

**Pior caso forçado do Dijkstra (24/11): caso `dijkstra-worst`.** DAG completo com pesos w(i, i+1) = 1 e w(i, j) = 1 + R(i+1) + (j−i−2), R(k) = 1 + (V−1−k)(V−k)/2. Resultado: d(i) = i, os vértices saem na ordem 0, 1, …, V−1 e, ao processar i, cada novo valor é menor que todos os que estão no heap. Em C (arestas percorridas na ordem inversa do arquivo) cada aresta é um decrease-key que sobe até a raiz; em Python cada aresta vira um push e um pop. Contagens: uma melhoria por aresta e trocas no heap do C por melhoria = 3,5; 4,5; 5,4; 6,4; 7,4; 8,4 para log₂V = 5…10, ou seja Θ(E·log V). O Bellman–Ford faz só 2 passes nessa entrada (arestas em ordem topológica).

## 5. Pendências

Feito em 23/11:
- [x] Tamanhos da campanha final, separados por caso (`scripts/run_all.sh`).
- [x] Script de ambiente (`scripts/environment.py`), funcionando em Linux, WSL e macOS.
- [x] Gráficos: teórico × medido, algoritmo × algoritmo, Python × C, casos de cada algoritmo e memória; tabelas em `results/tabelas.md`.
- [x] Teste cruzado das 4 implementações contra Floyd–Warshall em todos os casos (`tests/test_cross_check.py`).
- [x] Bônus: pico de memória por execução (`maxrss_kib`).

Falta:
- [x] Rodar `sh scripts/run_all.sh` na máquina final (WSL, 23/11) e guardar `results/`.
- [ ] Relatório em PDF: versão corrigida redigida em 24/11; falta cada integrante completar as contribuições e exportar.
- [ ] Slides (até 7 min, todos apresentam).
- [x] Pior caso forçado do Dijkstra (`dijkstra-worst`), medido no macOS em `results/macos/` (24/11).
- [x] Contagem de operações (`scripts/count_ops.py`, `results/operacoes.csv`) (24/11).
- [x] Correção da compilação no macOS (`c/peakrss.c`) (24/11).
- [ ] (Opcional) medir o `dijkstra-worst` também na máquina WSL; `.gitattributes`.

## 6. Uso de IA (anotar para a declaração no relatório)

Claude (Anthropic) foi usado em 21/11 para: revisar o repositório em relação ao enunciado, explicar os melhores e piores casos de cada algoritmo, sugerir o embaralhamento do caso `random`, o caso `chain-forward` e seu teste, e organizar este resumo. Em 23/11: escrever os scripts de ambiente, campanha completa (`run_all.sh`), gráficos/tabelas, medição de memória e o teste cruzado, e atualizar o README. Em 24/11: revisar o código e o relatório contra o enunciado, corrigir a compilação no macOS (`c/peakrss.c`), construir e testar a entrada de pior caso do Dijkstra (`dijkstra-worst`), escrever `scripts/count_ops.py`, medir o novo caso no macOS e redigir a versão corrigida do relatório.
