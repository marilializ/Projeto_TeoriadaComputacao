from .graph import Graph


def shortest_paths(graph: Graph) -> list[int | None]:
    distances: list[int | None] = [None] * graph.vertices
    distances[graph.source] = 0
    for _ in range(graph.vertices - 1):
        changed = False
        for u, v, weight in graph.edges:
            if distances[u] is None:
                continue
            candidate = distances[u] + weight
            if distances[v] is None or candidate < distances[v]:
                distances[v] = candidate
                changed = True
        if not changed:
            break
    for u, v, weight in graph.edges:
        if distances[u] is not None and (distances[v] is None or distances[u] + weight < distances[v]):
            raise ValueError("ciclo negativo alcançável pela origem")
    return distances
