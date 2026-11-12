"""Casos específicos de Dijkstra, executados em Python e C."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DijkstraTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(["make"], cwd=ROOT, check=True, capture_output=True)

    def run_both(self, graph_text: str, expected: list[int | None]) -> None:
        with tempfile.TemporaryDirectory() as directory:
            graph = Path(directory) / "graph.txt"
            graph.write_text(graph_text, encoding="utf-8")
            commands = {
                "Python": [sys.executable, "-m", "python.sp"],
                "C": [str(ROOT / "build/shortest_path")],
            }
            for language, command in commands.items():
                with self.subTest(language=language):
                    result = subprocess.run(
                        command + ["dijkstra", str(graph)],
                        cwd=ROOT,
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(json.loads(result.stdout)["distances"], expected)

    def test_source_other_than_zero_and_cheaper_indirect_path(self):
        self.run_both(
            "4 4 2\n"
            "2 0 5\n"
            "2 1 2\n"
            "1 0 1\n"
            "0 3 4\n",
            [3, 2, 0, 7],
        )

    def test_zero_weight_cycle_and_equal_cost_paths(self):
        self.run_both(
            "3 4 0\n"
            "0 1 0\n"
            "1 1 0\n"
            "1 2 2\n"
            "0 2 2\n",
            [0, 0, 2],
        )

    def test_negative_edge_is_rejected_even_if_unreachable(self):
        graph_text = "4 2 0\n0 1 3\n2 3 -1\n"
        with tempfile.TemporaryDirectory() as directory:
            graph = Path(directory) / "graph.txt"
            graph.write_text(graph_text, encoding="utf-8")
            commands = {
                "Python": [sys.executable, "-m", "python.sp"],
                "C": [str(ROOT / "build/shortest_path")],
            }
            for language, command in commands.items():
                with self.subTest(language=language):
                    result = subprocess.run(
                        command + ["dijkstra", str(graph)],
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
