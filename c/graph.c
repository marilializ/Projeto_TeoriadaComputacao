#include "graph.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void graph_free(Graph *graph) {
    free(graph->edges);
    free(graph->head);
    memset(graph, 0, sizeof(*graph));
}

int graph_read(const char *path, Graph *graph) {
    memset(graph, 0, sizeof(*graph));
    FILE *file = fopen(path, "r");
    if (!file) return -1;
    if (fscanf(file, "%d %d %d", &graph->vertices, &graph->count, &graph->source) != 3 ||
        graph->vertices < 1 || graph->count < 0 || graph->source < 0 ||
        graph->source >= graph->vertices) goto fail;
    graph->edges = calloc((size_t)graph->count ? (size_t)graph->count : 1, sizeof(Edge));
    graph->head = malloc((size_t)graph->vertices * sizeof(int));
    if (!graph->edges || !graph->head) goto fail;
    for (int i = 0; i < graph->vertices; ++i) graph->head[i] = -1;
    for (int i = 0; i < graph->count; ++i) {
        long long weight;
        Edge *edge = &graph->edges[i];
        if (fscanf(file, "%d %d %lld", &edge->u, &edge->v, &weight) != 3 ||
            edge->u < 0 || edge->u >= graph->vertices || edge->v < 0 ||
            edge->v >= graph->vertices || weight < -1000000 || weight > 1000000) goto fail;
        edge->weight = (int64_t)weight;
        edge->next = graph->head[edge->u];
        graph->head[edge->u] = i;
    }
    char extra[2];
    if (fscanf(file, " %1s", extra) == 1) goto fail;
    fclose(file);
    return 0;
fail:
    fclose(file);
    graph_free(graph);
    return -1;
}
