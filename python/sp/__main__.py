import argparse
import json
import time

from . import bellman_ford, dijkstra
from .graph import read_graph


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("algorithm", choices=["dijkstra", "bellman-ford"])
    parser.add_argument("graph")
    args = parser.parse_args()
    graph = read_graph(args.graph)
    function = dijkstra.shortest_paths if args.algorithm == "dijkstra" else bellman_ford.shortest_paths
    start = time.perf_counter_ns()
    distances = function(graph)
    elapsed = time.perf_counter_ns() - start
    print(json.dumps({"algorithm": args.algorithm, "distances": distances, "elapsed_ns": elapsed}))


if __name__ == "__main__":
    main()
