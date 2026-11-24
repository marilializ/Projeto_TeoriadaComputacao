"""Gera gráficos e tabelas a partir dos arquivos *_summary.csv produzidos por benchmark.py.

Para cada caso (random, chain, chain-forward, dense):
  <caso>_tempo.png        tempo medido x curva teórica (log-log), Dijkstra x Bellman-Ford, um painel por linguagem
  <caso>_razao.png        T(n)/f(n) -- deve tender a uma constante quando f é a complexidade correta
  <caso>_python_vs_c.png  quantas vezes o Python é mais lento que o C, por algoritmo
Além disso:
  casos_<algoritmo>.png   o mesmo algoritmo nos vários casos (melhor, médio, pior)
  memoria.png             pico de memória x V+E (bônus), a partir de results/memory.csv
  tabelas.md              tabelas em Markdown para colar no relatório
"""

import argparse
import csv
import statistics
from collections import defaultdict
from pathlib import Path

ALGORITHMS = ("dijkstra", "bellman-ford")
LANGUAGES = ("c", "python")
NAMES = {"dijkstra": "Dijkstra (heap)", "bellman-ford": "Bellman-Ford", "c": "C", "python": "Python"}
COLORS = {"dijkstra": "#2a6fdb", "bellman-ford": "#d9480f"}
CASE_ORDER = ["chain-forward", "random", "dense", "chain", "disconnected"]
CASE_LABELS = {"random": "random (caso médio)", "chain": "chain (pior caso do BF)",
               "chain-forward": "chain-forward (melhor caso do BF)", "dense": "dense (grafo completo)",
               "disconnected": "disconnected"}
FACTOR_LABELS = {
    ("dijkstra", "chain"): "V+E", ("dijkstra", "chain-forward"): "V+E",
    ("dijkstra", "random"): "(V+E)·log V", ("dijkstra", "dense"): "(V+E)·log V",
    ("bellman-ford", "chain"): "V·E", ("bellman-ford", "chain-forward"): "E",
    ("bellman-ford", "random"): "E·log V", ("bellman-ford", "dense"): "E",
}


def load(directory: Path) -> dict[str, list[dict]]:
    by_case: dict[str, list[dict]] = defaultdict(list)
    for path in sorted(directory.glob("*_summary.csv")):
        with path.open(newline="", encoding="utf-8") as source:
            for row in csv.DictReader(source):
                for key in ("vertices", "edges", "repeats"):
                    row[key] = int(row[key])
                for key in ("mean_ns", "stdev_ns", "bound_factor", "mean_over_bound", "case_factor",
                            "mean_over_case"):
                    if key in row and row[key] != "":
                        row[key] = float(row[key])
                by_case[row["case"]].append(row)
    return by_case


def series(rows: list[dict], language: str, algorithm: str) -> list[dict]:
    return sorted((r for r in rows if r["language"] == language and r["algorithm"] == algorithm),
                  key=lambda r: r["vertices"])


def plot_case(plt, case: str, rows: list[dict], output: Path) -> list[Path]:
    files = []
    # 1) tempo medido x teoria, um painel por linguagem
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
    for ax, language in zip(axes, LANGUAGES):
        for algorithm in ALGORITHMS:
            data = series(rows, language, algorithm)
            if not data:
                continue
            x = [r["vertices"] for r in data]
            y = [r["mean_ns"] / 1e6 for r in data]
            err = [r["stdev_ns"] / 1e6 for r in data]
            ax.errorbar(x, y, yerr=err, marker="o", capsize=3, color=COLORS[algorithm],
                        label=f"{NAMES[algorithm]} medido")
            constant = statistics.median(r["mean_over_case"] for r in data)
            ax.plot(x, [constant * r["case_factor"] / 1e6 for r in data], linestyle="--",
                    color=COLORS[algorithm], alpha=0.6,
                    label=f"c·{FACTOR_LABELS.get((algorithm, case), 'f(n)')}")
        ax.set_xscale("log", base=2)
        ax.set_yscale("log")
        ax.set_title(NAMES[language])
        ax.set_xlabel("Número de vértices V")
        ax.grid(True, which="both", alpha=0.3)
        ax.legend(fontsize=8)
    axes[0].set_ylabel("Tempo médio (ms, escala log)")
    fig.suptitle(f"Tempo medido × teórico — {CASE_LABELS.get(case, case)}")
    fig.tight_layout()
    files.append(output / f"{case}_tempo.png")
    fig.savefig(files[-1], dpi=160)
    plt.close(fig)

    # 2) razão T(n)/f(n): uma linha por algoritmo, uma coluna por linguagem (escalas independentes)
    fig, axes = plt.subplots(2, 2, figsize=(12, 7.5))
    for row, algorithm in zip(axes, ALGORITHMS):
        for ax, language in zip(row, LANGUAGES):
            data = series(rows, language, algorithm)
            if data:
                ax.plot([r["vertices"] for r in data], [r["mean_over_case"] for r in data], marker="o",
                        color=COLORS[algorithm])
            ax.set_xscale("log", base=2)
            ax.set_ylim(bottom=0)
            ax.set_title(f"{NAMES[algorithm]} em {NAMES[language]}: T(n) / {FACTOR_LABELS.get((algorithm, case), 'f(n)')}",
                         fontsize=10)
            ax.set_xlabel("Número de vértices V")
            ax.set_ylabel("ns por unidade de f(n)")
            ax.grid(True, alpha=0.3)
    fig.suptitle(f"Razão tempo/teoria — {CASE_LABELS.get(case, case)} (constante ⇒ f(n) correto)")
    fig.tight_layout()
    files.append(output / f"{case}_razao.png")
    fig.savefig(files[-1], dpi=160)
    plt.close(fig)

    # 3) Python / C
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for algorithm in ALGORITHMS:
        c_rows = {r["vertices"]: r for r in series(rows, "c", algorithm)}
        py_rows = series(rows, "python", algorithm)
        x = [r["vertices"] for r in py_rows if r["vertices"] in c_rows]
        y = [r["mean_ns"] / c_rows[r["vertices"]]["mean_ns"] for r in py_rows if r["vertices"] in c_rows]
        ax.plot(x, y, marker="o", color=COLORS[algorithm], label=NAMES[algorithm])
    ax.set_xscale("log", base=2)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Número de vértices V")
    ax.set_ylabel("Tempo Python / tempo C")
    ax.set_title(f"Python × C — {CASE_LABELS.get(case, case)}")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    files.append(output / f"{case}_python_vs_c.png")
    fig.savefig(files[-1], dpi=160)
    plt.close(fig)
    return files


def plot_cases(plt, by_case: dict[str, list[dict]], output: Path) -> list[Path]:
    files = []
    cases = [c for c in CASE_ORDER if c in by_case]
    for algorithm in ALGORITHMS:
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
        for ax, language in zip(axes, LANGUAGES):
            for case in cases:
                data = series(by_case[case], language, algorithm)
                if data:
                    ax.plot([r["edges"] for r in data], [r["mean_ns"] / 1e6 for r in data], marker="o",
                            label=CASE_LABELS.get(case, case))
            ax.set_xscale("log")
            ax.set_yscale("log")
            ax.set_title(NAMES[language])
            ax.set_xlabel("Número de arestas E (escala log)")
            ax.grid(True, which="both", alpha=0.3)
            ax.legend(fontsize=8)
        axes[0].set_ylabel("Tempo médio (ms, escala log)")
        fig.suptitle(f"{NAMES[algorithm]} em cada caso")
        fig.tight_layout()
        files.append(output / f"casos_{algorithm}.png")
        fig.savefig(files[-1], dpi=160)
        plt.close(fig)
    return files


def plot_memory(plt, directory: Path, output: Path) -> list[Path]:
    """Pico de memória (menos a base do interpretador/programa vazio) x V+E, de results/memory.csv."""
    path = directory / "memory.csv"
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    for r in rows:
        for key in ("vertices", "edges", "net_kib"):
            r[key] = int(float(r[key]))
    fig, ax = plt.subplots(figsize=(8, 5))
    for language, style in zip(LANGUAGES, ("-", "--")):
        for algorithm in ALGORITHMS:
            data = sorted((r for r in rows if r["language"] == language and r["algorithm"] == algorithm),
                          key=lambda r: r["vertices"])
            ax.plot([r["vertices"] + r["edges"] for r in data], [max(r["net_kib"], 1) / 1024 for r in data],
                    marker="o", linestyle=style, color=COLORS[algorithm],
                    label=f"{NAMES[language]} / {NAMES[algorithm]}")
    ref = sorted({r["vertices"] + r["edges"] for r in rows})
    c_rows = [r for r in rows if r["language"] == "c" and r["algorithm"] == "dijkstra"]
    anchor = max(c_rows, key=lambda r: r["vertices"])
    scale = anchor["net_kib"] / 1024 / (anchor["vertices"] + anchor["edges"])
    ax.plot(ref, [scale * x for x in ref], color="grey", linestyle=":", label="referência linear c·(V+E)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("V + E (escala log)")
    ax.set_ylabel("Pico de memória acima da base (MiB, escala log)")
    ax.set_title(f"Memória × tamanho da entrada — {CASE_LABELS.get(rows[0]['case'], rows[0]['case'])}")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    out = output / "memoria.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return [out]


def ms(value: float) -> str:
    """Nanossegundos -> milissegundos, com casas decimais conforme a grandeza (sem separador de milhar)."""
    value /= 1e6
    if value < 1:
        return f"{value:.3f}"
    if value < 100:
        return f"{value:.2f}"
    return f"{value:.0f}"


def tables(by_case: dict[str, list[dict]]) -> str:
    lines = ["# Tabelas de resultados", "",
             "Tempo médio ± desvio padrão em **milissegundos**; `T/f` = tempo (ns) dividido pelo custo esperado do caso; "
             "`Py/C` = tempo Python ÷ tempo C.", ""]
    for case in [c for c in CASE_ORDER if c in by_case]:
        rows = by_case[case]
        lines += [f"## {CASE_LABELS.get(case, case)}", "",
                  f"f(n): Dijkstra = {FACTOR_LABELS.get(('dijkstra', case), '?')}, "
                  f"Bellman-Ford = {FACTOR_LABELS.get(('bellman-ford', case), '?')}", "",
                  "| V | E | Dijkstra C | Dijkstra Py | BF C | BF Py | T/f Dij C | T/f BF C | Py/C Dij | Py/C BF |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
        for vertices in sorted({r["vertices"] for r in rows}):
            get = {(r["language"], r["algorithm"]): r for r in rows if r["vertices"] == vertices}
            cells = [str(vertices), str(get[("c", "dijkstra")]["edges"])]
            for language, algorithm in (("c", "dijkstra"), ("python", "dijkstra"), ("c", "bellman-ford"), ("python", "bellman-ford")):
                r = get[(language, algorithm)]
                cells.append(f"{ms(r['mean_ns'])} ± {ms(r['stdev_ns'])}")
            cells.append(f"{get[('c', 'dijkstra')]['mean_over_case']:.3g}")
            cells.append(f"{get[('c', 'bellman-ford')]['mean_over_case']:.3g}")
            for algorithm in ALGORITHMS:
                cells.append(f"{get[('python', algorithm)]['mean_ns'] / get[('c', algorithm)]['mean_ns']:.1f}×")
            lines.append("| " + " | ".join(cells) + " |")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("results", type=Path, nargs="?", default=Path("results"),
                        help="pasta com os arquivos *_summary.csv (padrão: results)")
    parser.add_argument("--output-dir", type=Path, default=None, help="padrão: <results>/plots")
    args = parser.parse_args()
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise SystemExit("Instale matplotlib: sudo apt install python3-matplotlib (Ubuntu/WSL) "
                         "ou python3 -m pip install matplotlib (macOS)") from exc
    by_case = load(args.results)
    if not by_case:
        parser.error(f"nenhum *_summary.csv em {args.results}")
    output = args.output_dir or args.results / "plots"
    output.mkdir(parents=True, exist_ok=True)
    files = []
    for case in [c for c in CASE_ORDER if c in by_case]:
        files += plot_case(plt, case, by_case[case], output)
    files += plot_cases(plt, by_case, output)
    files += plot_memory(plt, args.results, output)
    table_path = args.results / "tabelas.md"
    table_path.write_text(tables(by_case), encoding="utf-8")
    files.append(table_path)
    for path in files:
        print(path)


if __name__ == "__main__":
    main()
