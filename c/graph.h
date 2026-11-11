#ifndef GRAPH_H
#define GRAPH_H
#include <stdint.h>

typedef struct { int u, v; int64_t weight; int next; } Edge;
typedef struct { int vertices, count, source; Edge *edges; int *head; } Graph;
int graph_read(const char *path, Graph *graph);
void graph_free(Graph *graph);
#endif
