#include "algorithms.h"
#include <stdlib.h>

typedef struct { int *nodes, *position, size; int64_t *distance; } Heap;

static void swap(Heap *heap, int a, int b) {
    int x = heap->nodes[a], y = heap->nodes[b];
    heap->nodes[a] = y; heap->nodes[b] = x;
    heap->position[x] = b; heap->position[y] = a;
}
static void rise(Heap *heap, int at) {
    while (at > 0) {
        int parent = (at - 1) / 2;
        if (heap->distance[heap->nodes[parent]] <= heap->distance[heap->nodes[at]]) break;
        swap(heap, at, parent);
        at = parent;
    }
}
static void sink(Heap *heap, int at) {
    for (;;) {
        int left = 2 * at + 1, right = left + 1, best = at;
        if (left < heap->size && heap->distance[heap->nodes[left]] < heap->distance[heap->nodes[best]]) best = left;
        if (right < heap->size && heap->distance[heap->nodes[right]] < heap->distance[heap->nodes[best]]) best = right;
        if (best == at) break;
        swap(heap, at, best);
        at = best;
    }
}
int dijkstra(const Graph *graph, int64_t *distances) {
    for (int i = 0; i < graph->count; ++i)
        if (graph->edges[i].weight < 0) return -2;
    Heap heap = {0};
    heap.nodes = malloc((size_t)graph->vertices * sizeof(int));
    heap.position = malloc((size_t)graph->vertices * sizeof(int));
    if (!heap.nodes || !heap.position) { free(heap.nodes); free(heap.position); return -1; }
    heap.distance = distances;
    for (int i = 0; i < graph->vertices; ++i) {
        distances[i] = DIST_INF;
        heap.position[i] = -1;
    }
    distances[graph->source] = 0;
    heap.nodes[0] = graph->source;
    heap.position[graph->source] = 0;
    heap.size = 1;
    while (heap.size) {
        int u = heap.nodes[0];
        heap.position[u] = -2;
        --heap.size;
        if (heap.size) {
            heap.nodes[0] = heap.nodes[heap.size];
            heap.position[heap.nodes[0]] = 0;
            sink(&heap, 0);
        }
        for (int i = graph->head[u]; i != -1; i = graph->edges[i].next) {
            const Edge *edge = &graph->edges[i];
            int v = edge->v;
            if (heap.position[v] == -2) continue;
            int64_t candidate = distances[u] + edge->weight;
            if (candidate >= distances[v]) continue;
            distances[v] = candidate;
            if (heap.position[v] == -1) {
                heap.position[v] = heap.size;
                heap.nodes[heap.size++] = v;
            }
            rise(&heap, heap.position[v]);
        }
    }
    free(heap.nodes);
    free(heap.position);
    return 0;
}
