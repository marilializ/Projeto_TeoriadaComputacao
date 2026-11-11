"""Run the four programs on identical inputs; store raw and summary CSV files."""

import argparse
import csv
import json
import math
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

from generate import generate, write_graph

ROOT = Path(__file__).resolve().parents[1]
PROGRAMS = [(language, algorithm) for language in ("python", "c") for algorithm in ("dijkstra", "bellman-ford")]


def run(language: str, algorithm: str, graph: Path) -> dict:
    command = ([sys.executable, "-m", "python.sp"] if language == "python" else [str(ROOT / "build/shortest_path")])
    result = subprocess.run(command + [algorithm, str(graph)], cwd=ROOT, check=True, text=True, capture_output=True)
    data = json.loads(result.stdout)
    if data["algorithm"] != algorithm or not isinstance(data["elapsed_ns"], int):
        raise ValueError("saída inválida")
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[32, 64, 128, 256, 512, 1024])
    parser.add_argument("--repeats", type=int, default=15)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--case", choices=["random", "chain", "disconnected", "dense"], default="random")
    parser.add_argument("--edges-per-vertex", type=int, default=4)
    parser.add_argument("--output", type=Path, default=ROOT / "results/benchmark.csv")
    args = parser.parse_args()
    if len(args.sizes) < 6 or any(a >= b for a, b in zip(args.sizes, args.sizes[1:])):
        parser.error("use pelo menos seis tamanhos crescentes")
    if not 15 <= args.repeats <= 30:
        parser.error("o enunciado exige de 15 a 30 repetições")
    if not (ROOT / "build/shortest_path").is_file():
        parser.error("compile C primeiro com make")
    rows = []
    with tempfile.TemporaryDirectory() as temporary:
        for vertices in args.sizes:
            edges = generate(vertices, args.edges_per_vertex, args.seed, args.case)
            graph_path = Path(temporary) / f"v{vertices}.txt"
            write_graph(graph_path, vertices, edges)
            for repetition in range(1, args.repeats + 1):
                expected = None
                # Rotate ordering to reduce systematic effects from background load.
                programs = PROGRAMS[(repetition - 1) % 4:] + PROGRAMS[:(repetition - 1) % 4]
                for language, algorithm in programs:
                    data = run(language, algorithm, graph_path)
                    if len(data["distances"]) != vertices:
                        raise ValueError("comprimento de resposta inválido")
                    if expected is None:
                        expected = data["distances"]
                    elif data["distances"] != expected:
                        raise ValueError(f"divergência em V={vertices}, repetição={repetition}, {language}/{algorithm}")
                    rows.append({"seed": args.seed, "case": args.case, "vertices": vertices,
                                 "edges": len(edges), "language": language, "algorithm": algorithm,
                                 "repetition": repetition, "elapsed_ns": data["elapsed_ns"]})
            print(f"V={vertices}, E={len(edges)}: {args.repeats} repetições verificadas", file=sys.stderr)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with args.output.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fields)
        writer.writeheader()
        writer.writerows(rows)
    summary_path = args.output.with_name(args.output.stem + "_summary.csv")
    with summary_path.open("w", newline="", encoding="utf-8") as output:
        fields = ["seed", "case", "vertices", "edges", "language", "algorithm", "repeats", "mean_ns", "stdev_ns", "theory_factor", "mean_over_factor"]
        writer = csv.DictWriter(output, fields)
        writer.writeheader()
        for vertices in args.sizes:
            for language, algorithm in PROGRAMS:
                group = [r for r in rows if r["vertices"] == vertices and r["language"] == language and r["algorithm"] == algorithm]
                samples = [r["elapsed_ns"] for r in group]
                edge_count = group[0]["edges"]
                factor = ((vertices + edge_count) * math.log2(vertices) if algorithm == "dijkstra" else vertices * edge_count)
                writer.writerow({"seed": args.seed, "case": args.case, "vertices": vertices,
                                 "edges": edge_count, "language": language, "algorithm": algorithm,
                                 "repeats": len(samples), "mean_ns": statistics.mean(samples),
                                 "stdev_ns": statistics.stdev(samples), "theory_factor": factor,
                                 "mean_over_factor": statistics.mean(samples) / factor})
    print(args.output)
    print(summary_path)


if __name__ == "__main__":
    main()
