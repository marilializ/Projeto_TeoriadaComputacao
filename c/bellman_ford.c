#include "algorithms.h"

int bellman_ford(const Graph *graph, int64_t *distances) {
    for (int i = 0; i < graph->vertices; ++i) distances[i] = DIST_INF;
    distances[graph->source] = 0;
    for (int pass = 1; pass < graph->vertices; ++pass) {
        int changed = 0;
        for (int i = 0; i < graph->count; ++i) {
            const Edge *edge = &graph->edges[i];
            if (distances[edge->u] == DIST_INF) continue;
            int64_t candidate = distances[edge->u] + edge->weight;
            if (candidate < distances[edge->v]) {
                distances[edge->v] = candidate;
                changed = 1;
            }
        }
        if (!changed) break;
    }
    for (int i = 0; i < graph->count; ++i) {
        const Edge *edge = &graph->edges[i];
        if (distances[edge->u] != DIST_INF && distances[edge->u] + edge->weight < distances[edge->v])
            return -2;
    }
    return 0;
}
