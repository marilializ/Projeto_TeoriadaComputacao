import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CorrectnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(["make"], cwd=ROOT, check=True, capture_output=True)

    def check_all(self, graph: Path, expected: list[int | None]) -> None:
        for language in ("python", "c"):
            for algorithm in ("dijkstra", "bellman-ford"):
                with self.subTest(language=language, algorithm=algorithm):
                    command = ([sys.executable, "-m", "python.sp"] if language == "python" else [str(ROOT / "build/shortest_path")])
                    result = subprocess.run(command + [algorithm, str(graph)], cwd=ROOT, check=True, capture_output=True, text=True)
                    data = json.loads(result.stdout)
                    self.assertEqual(data["distances"], expected)
                    self.assertGreaterEqual(data["elapsed_ns"], 0)

    def test_known_graph(self):
        self.check_all(ROOT / "data/fixtures/basic.txt", [0, 4, 3, 6, 13])

    def test_unreachable(self):
        self.check_all(ROOT / "data/fixtures/disconnected.txt", [0, 4, None, None, None])

    def test_zero_weight_parallel_edges(self):
        with tempfile.TemporaryDirectory() as directory:
            graph = Path(directory) / "graph.txt"
            graph.write_text("4 5 0\n0 1 10\n0 1 0\n1 2 2\n0 2 9\n2 3 0\n", encoding="utf-8")
            self.check_all(graph, [0, 0, 2, 2])

    def test_negative_weight_bellman_ford(self):
        with tempfile.TemporaryDirectory() as directory:
            graph = Path(directory) / "graph.txt"
            graph.write_text("4 4 0\n0 1 5\n0 2 2\n1 3 -4\n2 3 1\n", encoding="utf-8")
            for language in ("python", "c"):
                command = ([sys.executable, "-m", "python.sp"] if language == "python" else [str(ROOT / "build/shortest_path")])
                result = subprocess.run(command + ["bellman-ford", str(graph)], cwd=ROOT, check=True, capture_output=True, text=True)
                self.assertEqual(json.loads(result.stdout)["distances"], [0, 5, 2, 1])
                rejected = subprocess.run(command + ["dijkstra", str(graph)], cwd=ROOT, capture_output=True, text=True)
                self.assertNotEqual(rejected.returncode, 0)

    def test_reachable_negative_cycle_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            graph = Path(directory) / "graph.txt"
            graph.write_text("3 3 0\n0 1 1\n1 2 -2\n2 1 -2\n", encoding="utf-8")
            for language in ("python", "c"):
                command = ([sys.executable, "-m", "python.sp"] if language == "python" else [str(ROOT / "build/shortest_path")])
                result = subprocess.run(command + ["bellman-ford", str(graph)], cwd=ROOT, capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")

    def test_unreachable_negative_cycle_does_not_affect_source(self):
        with tempfile.TemporaryDirectory() as directory:
            graph = Path(directory) / "graph.txt"
            graph.write_text("4 3 0\n0 1 2\n2 3 -3\n3 2 -3\n", encoding="utf-8")
            for language in ("python", "c"):
                command = ([sys.executable, "-m", "python.sp"] if language == "python" else [str(ROOT / "build/shortest_path")])
                result = subprocess.run(command + ["bellman-ford", str(graph)], cwd=ROOT, check=True, capture_output=True, text=True)
                self.assertEqual(json.loads(result.stdout)["distances"], [0, 2, None, None])


if __name__ == "__main__":
    unittest.main()
