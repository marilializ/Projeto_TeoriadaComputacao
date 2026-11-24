CC ?= cc
CFLAGS ?= -O2 -std=c11 -Wall -Wextra -Wpedantic

all: build/shortest_path build/peakrss

build/shortest_path: c/main.c c/graph.c c/dijkstra.c c/bellman_ford.c c/graph.h c/algorithms.h
	mkdir -p build
	$(CC) $(CFLAGS) -o $@ c/main.c c/graph.c c/dijkstra.c c/bellman_ford.c

build/peakrss: c/peakrss.c
	mkdir -p build
	$(CC) $(CFLAGS) -o $@ c/peakrss.c

.PHONY: all clean test
clean:
	rm -rf build

test: build/shortest_path build/peakrss
	python3 -m unittest discover -s tests -v
