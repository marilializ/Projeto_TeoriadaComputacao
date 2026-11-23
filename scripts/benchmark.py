"""Run the four programs on identical inputs; store raw and summary CSV files.

Mede, para cada execução:
  * elapsed_ns  -- tempo só da função do algoritmo (medido dentro do programa);
  * maxrss_kib  -- pico de memória residente do processo inteiro (bônus de memória).
"""

import argparse
import csv
import json
import math
import os
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

from generate import CASES, generate, write_graph

ROOT = Path(__file__).resolve().parents[1]
PROGRAMS = [(language, algorithm) for language in ("python", "c") for algorithm in ("dijkstra", "bellman-ford")]


def bound_factor(algorithm: str, vertices: int, edges: int) -> float:
    """Limite superior do enunciado: O((V+E) log V) e O(V·E)."""
    if algorithm == "dijkstra":
        return (vertices + edges) * math.log2(vertices)
    return vertices * edges


def case_factor(algorithm: str, case: str, vertices: int, edges: int) -> float:
    """Custo esperado para o caso gerado (ver docs/progresso.md, seção 4).

    Dijkstra: nas filas o heap nunca passa de 1 elemento -> Θ(V+E).
    Bellman-Ford: custo = (número de passes) x E.
      chain          -> V-1 passes        -> V·E   (pior caso)
      chain-forward  -> 2 passes          -> E     (melhor caso)
      random         -> ~log V passes     -> E·log V
      dense          -> poucos passes, ~constante -> E
    """
    if algorithm == "dijkstra":
        if case in ("chain", "chain-forward"):
            return vertices + edges
        return (vertices + edges) * math.log2(vertices)
    if case == "chain":
        return vertices * edges
    if case == "random":
        return edges * math.log2(vertices)
    return edges


def run_with_memory(language: str, algorithm: str, graph: Path) -> tuple[dict, int]:
    """Executa o programa e devolve (saída JSON, pico de memória em KiB)."""
    command = ([sys.executable, "-m", "python.sp"] if language == "python" else [str(ROOT / "build/shortest_path")])
    with tempfile.TemporaryFile(mode="w+") as out, tempfile.TemporaryFile(mode="w+") as err:
        process = subprocess.Popen(command + [algorithm, str(graph)], cwd=ROOT, text=True, stdout=out, stderr=err)
        _, status, usage = os.wait4(process.pid, 0)
        process.returncode = os.waitstatus_to_exitcode(status)
        out.seek(0)
        err.seek(0)
        if process.returncode != 0:
            raise RuntimeError(f"{language}/{algorithm} falhou: {err.read().strip()}")
        data = json.loads(out.read())
    if data["algorithm"] != algorithm or not isinstance(data["elapsed_ns"], int):
        raise ValueError("saída inválida")
    # ru_maxrss: KiB no Linux, bytes no macOS.
    maxrss_kib = usage.ru_maxrss // 1024 if sys.platform == "darwin" else usage.ru_maxrss
    return data, maxrss_kib


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sizes", nargs="+", type=int, default=[32, 64, 128, 256, 512, 1024])
    parser.add_argument("--repeats", type=int, default=15)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--case", choices=CASES, default="random")
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
                # Rotaciona a ordem dos programas para reduzir efeitos sistemáticos de carga de fundo.
                programs = PROGRAMS[(repetition - 1) % 4:] + PROGRAMS[:(repetition - 1) % 4]
                for language, algorithm in programs:
                    data, maxrss_kib = run_with_memory(language, algorithm, graph_path)
                    if len(data["distances"]) != vertices:
                        raise ValueError("comprimento de resposta inválido")
                    if expected is None:
                        expected = data["distances"]
                    elif data["distances"] != expected:
                        raise ValueError(f"divergência em V={vertices}, repetição={repetition}, {language}/{algorithm}")
                    rows.append({"seed": args.seed, "case": args.case, "vertices": vertices,
                                 "edges": len(edges), "language": language, "algorithm": algorithm,
                                 "repetition": repetition, "elapsed_ns": data["elapsed_ns"],
                                 "maxrss_kib": maxrss_kib})
            print(f"[{args.case}] V={vertices}, E={len(edges)}: {args.repeats} repetições verificadas", file=sys.stderr)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary_path = args.output.with_name(args.output.stem + "_summary.csv")
    fields = ["seed", "case", "vertices", "edges", "language", "algorithm", "repeats",
              "mean_ns", "stdev_ns", "bound_factor", "mean_over_bound", "case_factor", "mean_over_case",
              "mean_maxrss_kib"]
    with summary_path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fields)
        writer.writeheader()
        for vertices in args.sizes:
            for language, algorithm in PROGRAMS:
                group = [r for r in rows if r["vertices"] == vertices and r["language"] == language and r["algorithm"] == algorithm]
                samples = [r["elapsed_ns"] for r in group]
                edge_count = group[0]["edges"]
                mean = statistics.mean(samples)
                bound = bound_factor(algorithm, vertices, edge_count)
                expected = case_factor(algorithm, args.case, vertices, edge_count)
                writer.writerow({"seed": args.seed, "case": args.case, "vertices": vertices,
                                 "edges": edge_count, "language": language, "algorithm": algorithm,
                                 "repeats": len(samples), "mean_ns": mean,
                                 "stdev_ns": statistics.stdev(samples),
                                 "bound_factor": bound, "mean_over_bound": mean / bound,
                                 "case_factor": expected, "mean_over_case": mean / expected,
                                 "mean_maxrss_kib": statistics.mean(r["maxrss_kib"] for r in group)})
    print(args.output)
    print(summary_path)


if __name__ == "__main__":
    main()
