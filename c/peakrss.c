/* Lança um programa a partir de um processo pequeno e informa o pico de memória residente dele.
 * Uso: peakrss programa [argumentos...]
 * A saída do programa passa direto; no fim, escreve "peak_rss_kib=N" na saída de erro.
 * Por que existe: um filho criado direto pelo benchmark em Python herda, no ru_maxrss, a memória
 * do processo pai. Criado a partir deste processo mínimo, o pico medido é só o do programa. */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <sys/resource.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc < 2) { fputs("uso: peakrss programa [argumentos...]\n", stderr); return 2; }
    pid_t pid = fork();
    if (pid < 0) { perror("fork"); return 2; }
    if (pid == 0) { execvp(argv[1], argv + 1); perror("execvp"); _exit(127); }
    int status = 0;
    if (waitpid(pid, &status, 0) < 0) { perror("waitpid"); return 2; }
    struct rusage usage;
    getrusage(RUSAGE_CHILDREN, &usage);
#ifdef __APPLE__
    long kib = (long)(usage.ru_maxrss / 1024); /* macOS informa em bytes */
#else
    long kib = (long)usage.ru_maxrss;          /* Linux informa em KiB */
#endif
    fprintf(stderr, "peak_rss_kib=%ld\n", kib);
    return WIFEXITED(status) ? WEXITSTATUS(status) : 2;
}
