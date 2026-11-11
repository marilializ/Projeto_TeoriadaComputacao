CC ?= cc
CFLAGS ?= -O2 -std=c11 -Wall -Wextra -Wpedantic

build/shortest_path: c/main.c c/graph.c c/dijkstra.c c/bellman_ford.c c/graph.h c/algorithms.h
	mkdir -p build
	$(CC) $(CFLAGS) -o $@ c/main.c c/graph.c c/dijkstra.c c/bellman_ford.c

.PHONY: clean test
clean:
	rm -rf build

test: build/shortest_path
	python3 -m unittest discover -s tests -v
