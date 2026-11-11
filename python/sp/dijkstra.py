import heapq

from .graph import Graph


def shortest_paths(graph: Graph) -> list[int | None]:
    if any(weight < 0 for _, _, weight in graph.edges):
        raise ValueError("Dijkstra exige pesos não negativos")
    distances: list[int | None] = [None] * graph.vertices
    distances[graph.source] = 0
    heap = [(0, graph.source)]
    while heap:
        distance, u = heapq.heappop(heap)
        if distance != distances[u]:
            continue
        for v, weight in graph.adjacency[u]:
            candidate = distance + weight
            if distances[v] is None or candidate < distances[v]:
                distances[v] = candidate
                heapq.heappush(heap, (candidate, v))
    return distances
