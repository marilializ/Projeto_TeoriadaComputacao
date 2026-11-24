"""Mede o pico de memória residente (bônus) das quatro implementações, com processos limpos.

Cada programa é iniciado por build/peakrss, um lançador mínimo em C; assim o pico medido não
herda a memória deste script. Para cada tamanho mede-se o programa com o grafo e, como base,
com um grafo vazio (1 vértice): a diferença é a memória que cresce com a entrada.

Uso: python3 scripts/memory.py [--case random] [--sizes ...] [--repeats 3]
Saída: results/memory.csv
"""

import argparse
import csv
import re
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

from generate import CASES, generate, write_graph

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "build/peakrss"
PROGRAMS = [(language, algorithm) for language in ("python", "c") for algorithm in ("dijkstra", "bellman-ford")]


def peak_kib(language: str, algorithm: str, graph: Path) -> int:
    program = [sys.executable, "-m", "python.sp"] if language == "python" else [str(ROOT / "build/shortest_path")]
    result = subprocess.run([str(LAUNCHER)] + program + [algorithm, str(graph)], cwd=ROOT,
                            capture_output=True, text=True)
    match = re.search(r"peak_rss_kib=(\d+)", result.stderr)
    if result.returncode != 0 or not match:
        raise RuntimeError(f"{language}/{algorithm} falhou: {result.stderr.strip()}")
    return int(match.group(1))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--case", choices=CASES, default="random")
    parser.add_argument("--sizes", nargs="+", type=int,
                        default=[2048, 4096, 8192, 16384, 32768, 65536, 131072, 262144])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--edges-per-vertex", type=int, default=4)
    parser.add_argument("--output", type=Path, default=ROOT / "results/memory.csv")
    args = parser.parse_args()
    if not LAUNCHER.is_file() or not (ROOT / "build/shortest_path").is_file():
        parser.error("compile primeiro com make")
    rows = []
    with tempfile.TemporaryDirectory() as temporary:
        empty = Path(temporary) / "vazio.txt"
        empty.write_text("1 0 0\n", encoding="utf-8")
        baseline = {(lang, alg): statistics.median(peak_kib(lang, alg, empty) for _ in range(args.repeats))
                    for lang, alg in PROGRAMS}
        for vertices in args.sizes:
            edges = generate(vertices, args.edges_per_vertex, args.seed, args.case)
            graph = Path(temporary) / f"v{vertices}.txt"
            write_graph(graph, vertices, edges)
            for language, algorithm in PROGRAMS:
                peak = statistics.median(peak_kib(language, algorithm, graph) for _ in range(args.repeats))
                base = baseline[(language, algorithm)]
                rows.append({"case": args.case, "vertices": vertices, "edges": len(edges),
                             "language": language, "algorithm": algorithm,
                             "peak_rss_kib": peak, "baseline_kib": base, "net_kib": peak - base,
                             "net_bytes_per_v_plus_e": round((peak - base) * 1024 / (vertices + len(edges)), 1)})
            print(f"[memória/{args.case}] V={vertices}, E={len(edges)}", file=sys.stderr)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(args.output)


if __name__ == "__main__":
    main()
