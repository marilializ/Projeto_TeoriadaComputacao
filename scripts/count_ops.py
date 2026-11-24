"""Conta operações dos algoritmos (não mede tempo) nas mesmas entradas da campanha.

Os números não dependem da máquina e servem para conferir o custo esperado de cada caso:
  bf_passes            passes executados pelo Bellman-Ford (inclui o último, que só confirma; no
                       chain o laço termina em V-1 passes sem passe de confirmação)
  dij_melhorias        vezes em que o Dijkstra melhorou uma distância (inserções + decrease-keys)
  dij_decrease_keys    melhorias de vértices que já estavam no heap
  heap_trocas_c        trocas no heap binário da versão C (subidas + descidas), simuladas com a
                       mesma lógica e a mesma ordem de arestas de c/dijkstra.c
O Bellman-Ford em C e em Python percorre as arestas na ordem do arquivo, então o número de passes é o
mesmo nas duas linguagens. Uso: python3 scripts/count_ops.py [--output results/operacoes.csv]
"""

import argparse
import csv
import heapq
import math
import sys
from pathlib import Path

from generate import generate

ROOT = Path(__file__).resolve().parents[1]
SIZES = {  # os mesmos de scripts/run_all.sh
    "chain-forward": [4096, 8192, 16384, 32768, 65536, 131072, 262144, 524288],
    "random": [2048, 4096, 8192, 16384, 32768, 65536, 131072, 262144],
    "dense": [32, 64, 128, 256, 512, 1024],
    "dijkstra-worst": [32, 64, 128, 256, 512, 1024],
    "chain": [256, 512, 1024, 2048, 4096, 8192, 16384],
}


def bellman_ford_passes(vertices: int, edges: list[tuple[int, int, int]]) -> int:
    distances: list[int | None] = [None] * vertices
    distances[0] = 0
    passes = 0
    for _ in range(vertices - 1):
        passes += 1
        changed = False
        for u, v, weight in edges:
            if distances[u] is None:
                continue
            candidate = distances[u] + weight
            if distances[v] is None or candidate < distances[v]:
                distances[v] = candidate
                changed = True
        if not changed:
            break
    return passes


def dijkstra_python(vertices: int, edges: list[tuple[int, int, int]]) -> tuple[int, int, list[int | None]]:
    """Mesma lógica de python/sp/dijkstra.py, contando melhorias e decrease-keys."""
    adjacency: list[list[tuple[int, int]]] = [[] for _ in range(vertices)]
    for u, v, weight in edges:
        adjacency[u].append((v, weight))
    distances: list[int | None] = [None] * vertices
    distances[0] = 0
    heap = [(0, 0)]
    improvements = decrease_keys = 0
    while heap:
        distance, u = heapq.heappop(heap)
        if distance != distances[u]:
            continue
        for v, weight in adjacency[u]:
            candidate = distance + weight
            if distances[v] is None or candidate < distances[v]:
                improvements += 1
                decrease_keys += distances[v] is not None
                distances[v] = candidate
                heapq.heappush(heap, (candidate, v))
    return improvements, decrease_keys, distances


def dijkstra_c_swaps(vertices: int, edges: list[tuple[int, int, int]]) -> tuple[int, list[int | None]]:
    """Simula c/dijkstra.c (heap com decrease-key; lista encadeada = ordem inversa do arquivo)."""
    adjacency: list[list[tuple[int, int]]] = [[] for _ in range(vertices)]
    for u, v, weight in reversed(edges):
        adjacency[u].append((v, weight))
    infinity = math.inf
    distance = [infinity] * vertices
    position = [-1] * vertices
    nodes: list[int] = []
    swaps = 0

    def swap(a: int, b: int) -> None:
        nonlocal swaps
        nodes[a], nodes[b] = nodes[b], nodes[a]
        position[nodes[a]] = a
        position[nodes[b]] = b
        swaps += 1

    def rise(at: int) -> None:
        while at > 0:
            parent = (at - 1) // 2
            if distance[nodes[parent]] <= distance[nodes[at]]:
                break
            swap(at, parent)
            at = parent

    def sink(at: int) -> None:
        size = len(nodes)
        while True:
            left, best = 2 * at + 1, at
            right = left + 1
            if left < size and distance[nodes[left]] < distance[nodes[best]]:
                best = left
            if right < size and distance[nodes[right]] < distance[nodes[best]]:
                best = right
            if best == at:
                break
            swap(at, best)
            at = best

    distance[0] = 0
    nodes.append(0)
    position[0] = 0
    while nodes:
        u = nodes[0]
        position[u] = -2
        last = nodes.pop()
        if nodes:
            nodes[0] = last
            position[last] = 0
            sink(0)
        for v, weight in adjacency[u]:
            if position[v] == -2:
                continue
            candidate = distance[u] + weight
            if candidate >= distance[v]:
                continue
            distance[v] = candidate
            if position[v] == -1:
                position[v] = len(nodes)
                nodes.append(v)
            rise(position[v])
    return swaps, [None if d == infinity else d for d in distance]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--edges-per-vertex", type=int, default=4)
    parser.add_argument("--output", type=Path, default=ROOT / "results/operacoes.csv")
    args = parser.parse_args()
    rows = []
    for case, sizes in SIZES.items():
        for vertices in sizes:
            edges = generate(vertices, args.edges_per_vertex, args.seed, case)
            improvements, decrease_keys, expected = dijkstra_python(vertices, edges)
            swaps, c_distances = dijkstra_c_swaps(vertices, edges)
            if c_distances != expected:
                raise ValueError(f"simulação divergente em {case}, V={vertices}")
            rows.append({"case": case, "vertices": vertices, "edges": len(edges),
                         "log2_v": round(math.log2(vertices), 2),
                         "bf_passes": bellman_ford_passes(vertices, edges),
                         "dij_melhorias": improvements, "dij_decrease_keys": decrease_keys,
                         "dij_melhorias_por_v": round(improvements / vertices, 3),
                         "dij_melhorias_por_e": round(improvements / len(edges), 4),
                         "heap_trocas_c": swaps,
                         "heap_trocas_c_por_melhoria": round(swaps / improvements, 3)})
            print(f"[operações/{case}] V={vertices}, E={len(edges)}", file=sys.stderr)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(args.output)


if __name__ == "__main__":
    main()
