#ifndef ALGORITHMS_H
#define ALGORITHMS_H
#include "graph.h"
#define DIST_INF (INT64_MAX / 4)
int dijkstra(const Graph *graph, int64_t *distances);
int bellman_ford(const Graph *graph, int64_t *distances);
#endif
