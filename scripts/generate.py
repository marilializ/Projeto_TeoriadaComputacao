"""Generate reproducible directed graphs in the shared text format."""

import argparse
import random
from pathlib import Path


def generate(vertices: int, edges_per_vertex: int, seed: int, case: str) -> list[tuple[int, int, int]]:
    if vertices < 2 or edges_per_vertex < 1:
        raise ValueError("vertices >= 2 e edges-per-vertex >= 1 são necessários")
    if case not in {"random", "chain", "disconnected", "dense"}:
        raise ValueError("caso desconhecido")
    rng = random.Random(seed)
    if case == "chain":
        return [(u, u + 1, rng.randint(1, 100)) for u in range(vertices - 2, -1, -1)]
    if case == "disconnected":
        return [(u, u + 1, rng.randint(1, 100)) for u in range(vertices // 2 - 2, -1, -1)]
    if case == "dense":
        return [(u, v, rng.randint(1, 100)) for u in range(vertices) for v in range(vertices) if u != v]
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
    parser.add_argument("--case", choices=["random", "chain", "disconnected", "dense"], default="random")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_graph(args.output, args.vertices, generate(args.vertices, args.edges_per_vertex, args.seed, args.case))


if __name__ == "__main__":
    main()
