#define _POSIX_C_SOURCE 200809L
#include "algorithms.h"
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static uint64_t nanoseconds(struct timespec t) {
    return (uint64_t)t.tv_sec * 1000000000ULL + (uint64_t)t.tv_nsec;
}
int main(int argc, char **argv) {
    if (argc != 3 || (strcmp(argv[1], "dijkstra") && strcmp(argv[1], "bellman-ford"))) {
        fprintf(stderr, "uso: %s dijkstra|bellman-ford arquivo\n", argv[0]);
        return 2;
    }
    Graph graph;
    if (graph_read(argv[2], &graph)) { fputs("grafo inválido\n", stderr); return 2; }
    int64_t *distances = malloc((size_t)graph.vertices * sizeof(int64_t));
    if (!distances) { graph_free(&graph); return 2; }
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    int status = 0;
    if (strcmp(argv[1], "dijkstra") == 0) status = dijkstra(&graph, distances);
    else status = bellman_ford(&graph, distances);
    clock_gettime(CLOCK_MONOTONIC, &end);
    if (status) {
        fputs(status == -2 ? "peso negativo incompatível ou ciclo negativo alcançável\n" : "sem memória\n", stderr);
        free(distances); graph_free(&graph); return 2;
    }
    printf("{\"algorithm\":\"%s\",\"distances\":[", argv[1]);
    for (int i = 0; i < graph.vertices; ++i) {
        if (i) putchar(',');
        if (distances[i] == DIST_INF) fputs("null", stdout);
        else printf("%" PRId64, distances[i]);
    }
    printf("],\"elapsed_ns\":%" PRIu64 "}\n", nanoseconds(end) - nanoseconds(start));
    free(distances);
    graph_free(&graph);
    return 0;
}
