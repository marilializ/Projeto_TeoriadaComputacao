"""Plot measured time and theory-normalized time from a benchmark summary CSV."""

import argparse
import csv
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summary", type=Path, help="arquivo *_summary.csv de benchmark.py")
    parser.add_argument("--output-dir", type=Path, default=Path("results/plots"))
    args = parser.parse_args()
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise SystemExit("Instale matplotlib para gerar gráficos: python3 -m pip install matplotlib") from exc
    with args.summary.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    if not rows:
        parser.error("resumo vazio")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    groups = {(row["language"], row["algorithm"]) for row in rows}
    for metric, label, filename in (
        ("mean_ns", "Tempo médio do algoritmo (ns)", "time_loglog.png"),
        ("mean_over_factor", "Tempo médio / fator teórico", "theory_ratio.png"),
    ):
        fig, ax = plt.subplots(figsize=(8, 5))
        for language, algorithm in sorted(groups):
            group = sorted((row for row in rows if row["language"] == language and row["algorithm"] == algorithm), key=lambda row: int(row["vertices"]))
            x = [int(row["vertices"]) for row in group]
            y = [float(row[metric]) for row in group]
            ax.plot(x, y, marker="o", label=f"{language} / {algorithm}")
        ax.set_xscale("log", base=2)
        if metric == "mean_ns":
            ax.set_yscale("log")
        ax.set_xlabel("Número de vértices (V)")
        ax.set_ylabel(label)
        ax.grid(True, which="both", alpha=0.3)
        ax.legend()
        fig.tight_layout()
        fig.savefig(args.output_dir / filename, dpi=160)
        plt.close(fig)
        print(args.output_dir / filename)


if __name__ == "__main__":
    main()
