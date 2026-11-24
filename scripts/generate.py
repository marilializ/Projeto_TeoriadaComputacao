"""Generate reproducible directed graphs in the shared text format."""

import argparse
import random
from pathlib import Path

CASES = ["random", "chain", "chain-forward", "disconnected", "dense", "dijkstra-worst"]
MAX_WEIGHT = 1_000_000


def dijkstra_worst(vertices: int) -> list[tuple[int, int, int]]:
    """Pior caso do Dijkstra com heap: DAG completo (E = V(V-1)/2) em que TODA aresta melhora uma distância.

    Pesos: w(i, i+1) = 1 e w(i, j) = 1 + R(i+1) + (j - i - 2) para j >= i+2, com R(k) = 1 + (V-1-k)(V-k)/2.
    Assim d(i) = i e os vértices saem do heap na ordem 0, 1, ..., V-1. Ao processar i, cada novo valor
    d(i) + w(i, j) é menor que todos os que já estão no heap:
      - em C, a lista encadeada percorre as arestas de i na ordem inversa do arquivo (j = V-1, ..., i+1),
        então cada melhoria é um decrease-key que sobe até a raiz: Θ(log V);
      - em Python, cada aresta vira um push e, depois, um pop no heap: Θ(log V) cada.
    Total: Θ(E log V) = Θ((V+E) log V). Os pesos não dependem da semente.
    """
    largest = (vertices - 2) * (vertices - 1) // 2 + vertices - 1  # w(0, V-1)
    if largest > MAX_WEIGHT:
        raise ValueError(f"dijkstra-worst: V={vertices} gera peso {largest} > {MAX_WEIGHT}; use V <= 1414")

    def gap(k: int) -> int:
        return 1 + (vertices - 1 - k) * (vertices - k) // 2

    return [(i, j, 1 if j == i + 1 else 1 + gap(i + 1) + (j - i - 2))
            for i in range(vertices) for j in range(i + 1, vertices)]


def generate(vertices: int, edges_per_vertex: int, seed: int, case: str) -> list[tuple[int, int, int]]:
    if vertices < 2 or edges_per_vertex < 1:
        raise ValueError("vertices >= 2 e edges-per-vertex >= 1 são necessários")
    if case not in CASES:
        raise ValueError("caso desconhecido")
    rng = random.Random(seed)
    if case == "chain":
        return [(u, u + 1, rng.randint(1, 100)) for u in range(vertices - 2, -1, -1)]
    if case == "chain-forward":
        return [(u, u + 1, rng.randint(1, 100)) for u in range(vertices - 1)]
    if case == "disconnected":
        return [(u, u + 1, rng.randint(1, 100)) for u in range(vertices // 2 - 2, -1, -1)]
    if case == "dense":
        return [(u, v, rng.randint(1, 100)) for u in range(vertices) for v in range(vertices) if u != v]
    if case == "dijkstra-worst":
        return dijkstra_worst(vertices)
    maximum = vertices * (vertices - 1)
    target = min(maximum, max(vertices - 1, vertices * edges_per_vertex))
    used = {(u, u + 1) for u in range(vertices - 1)}
    edges = [(u, u + 1, rng.randint(1, 100)) for u in range(vertices - 1)]
    while len(edges) < target:
        u = rng.randrange(vertices)
        v = rng.randrange(vertices)
        if u == v or (u, v) in used:
            continue
        used.add((u, v))
        edges.append((u, v, rng.randint(1, 100)))
    rng.shuffle(edges)  # ordem aleatória: remove o viés da cadeia em ordem direta
    return edges


def write_graph(path: Path, vertices: int, edges: list[tuple[int, int, int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as output:
        output.write(f"{vertices} {len(edges)} 0\n")
        for u, v, weight in edges:
            output.write(f"{u} {v} {weight}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vertices", type=int, required=True)
    parser.add_argument("--edges-per-vertex", type=int, default=4)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--case", choices=CASES, default="random")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_graph(args.output, args.vertices, generate(args.vertices, args.edges_per_vertex, args.seed, args.case))


if __name__ == "__main__":
    main()
