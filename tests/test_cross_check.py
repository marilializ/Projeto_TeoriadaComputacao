"""As quatro implementações devem dar a mesma resposta em grafos gerados de todos os casos."""

import json
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from generate import CASES, generate, write_graph  # noqa: E402

COMMANDS = {"python": [sys.executable, "-m", "python.sp"], "c": [str(ROOT / "build/shortest_path")]}


def reference(vertices: int, edges: list[tuple[int, int, int]]) -> list[int | None]:
    """Floyd–Warshall a partir da origem 0: independente dos dois algoritmos testados."""
    inf = float("inf")
    dist = [[inf] * vertices for _ in range(vertices)]
    for i in range(vertices):
        dist[i][i] = 0
    for u, v, w in edges:
        dist[u][v] = min(dist[u][v], w)
    for k in range(vertices):
        for i in range(vertices):
            for j in range(vertices):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
    return [None if d == inf else d for d in dist[0]]


class CrossCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(["make"], cwd=ROOT, check=True, capture_output=True)

    def test_all_cases_all_implementations_agree(self):
        with tempfile.TemporaryDirectory() as directory:
            for case in CASES:
                for seed in (1, 7, 2026):
                    vertices = random.Random(seed).randint(5, 40)
                    edges = generate(vertices, 3, seed, case)
                    graph = Path(directory) / f"{case}-{seed}.txt"
                    write_graph(graph, vertices, edges)
                    expected = reference(vertices, edges)
                    for language, command in COMMANDS.items():
                        for algorithm in ("dijkstra", "bellman-ford"):
                            with self.subTest(case=case, seed=seed, language=language, algorithm=algorithm):
                                result = subprocess.run(command + [algorithm, str(graph)], cwd=ROOT, check=True,
                                                        capture_output=True, text=True)
                                self.assertEqual(json.loads(result.stdout)["distances"], expected)


if __name__ == "__main__":
    unittest.main()
