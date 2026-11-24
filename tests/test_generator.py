import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from generate import generate  # noqa: E402


class GeneratorTests(unittest.TestCase):
    def test_same_seed_same_edges(self):
        self.assertEqual(generate(20, 4, 2026, "random"), generate(20, 4, 2026, "random"))

    def test_random_has_no_duplicate_arcs(self):
        edges = generate(20, 4, 2026, "random")
        self.assertEqual(len({(u, v) for u, v, _ in edges}), len(edges))

    def test_chain_order_for_bellman_ford(self):
        edges = generate(5, 4, 2026, "chain")
        self.assertEqual([(u, v) for u, v, _ in edges], [(3, 4), (2, 3), (1, 2), (0, 1)])


    def test_chain_forward_order(self):
        edges = generate(5, 4, 2026, "chain-forward")
        self.assertEqual([(u, v) for u, v, _ in edges], [(0, 1), (1, 2), (2, 3), (3, 4)])

    def test_dijkstra_worst_every_edge_is_a_decrease_to_the_heap_top(self):
        """Na ordem em que o C percorre as arestas (inversa do arquivo), cada aresta melhora a
        distância do destino para um valor menor que o de todos os vértices ainda abertos."""
        vertices = 30
        edges = generate(vertices, 4, 2026, "dijkstra-worst")
        self.assertEqual(len(edges), vertices * (vertices - 1) // 2)
        adjacency = [[] for _ in range(vertices)]
        for u, v, weight in reversed(edges):
            adjacency[u].append((v, weight))
        distance = {0: 0}
        opened, closed = {0}, set()
        while opened:
            u = min(opened, key=lambda x: (distance[x], x))
            opened.remove(u)
            closed.add(u)
            for v, weight in adjacency[u]:
                self.assertNotIn(v, closed)
                candidate = distance[u] + weight
                self.assertLess(candidate, distance.get(v, float("inf")))
                others = [distance[x] for x in opened if x != v]
                self.assertTrue(all(candidate < d for d in others))
                distance[v] = candidate
                opened.add(v)
        self.assertEqual([distance[v] for v in range(vertices)], list(range(vertices)))

    def test_dijkstra_worst_weights_within_input_limits(self):
        self.assertLessEqual(max(w for _, _, w in generate(1024, 4, 2026, "dijkstra-worst")), 1_000_000)
        self.assertLessEqual(max(w for _, _, w in generate(1414, 4, 2026, "dijkstra-worst")), 1_000_000)
        with self.assertRaises(ValueError):
            generate(1415, 4, 2026, "dijkstra-worst")


if __name__ == "__main__":
    unittest.main()
