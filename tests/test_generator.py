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


if __name__ == "__main__":
    unittest.main()
