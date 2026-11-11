from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Graph:
    vertices: int
    source: int
    edges: tuple[tuple[int, int, int], ...]
    adjacency: tuple[tuple[tuple[int, int], ...], ...]


def read_graph(path: str | Path) -> Graph:
    tokens = Path(path).read_text(encoding="utf-8").split()
    if len(tokens) < 3:
        raise ValueError("cabeçalho incompleto")
    try:
        values = [int(token) for token in tokens]
    except ValueError as exc:
        raise ValueError("entrada contém texto não numérico") from exc
    vertices, count, source = values[:3]
    if vertices < 1 or count < 0 or not 0 <= source < vertices:
        raise ValueError("cabeçalho inválido")
    if len(values) != 3 + 3 * count:
        raise ValueError("número de arestas diferente do cabeçalho")
    edges = []
    adjacency = [[] for _ in range(vertices)]
    for offset in range(3, len(values), 3):
        u, v, weight = values[offset:offset + 3]
        if not (0 <= u < vertices and 0 <= v < vertices and -1_000_000 <= weight <= 1_000_000):
            raise ValueError("aresta inválida")
        edges.append((u, v, weight))
        adjacency[u].append((v, weight))
    return Graph(vertices, source, tuple(edges), tuple(tuple(row) for row in adjacency))
