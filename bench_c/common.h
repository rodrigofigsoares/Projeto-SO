/* common.h - utilitários compartilhados pelos micro-benchmarks (P2).
 *
 * Contrato de saída (ver Agents.md, seção 6): CSV em stdout com cabeçalho
 *   benchmark,env,run,metric,value,unit
 *
 * Convenção de rodadas: a rodada 0 é SEMPRE o aquecimento (warm-up) e deve
 * ser descartada na análise. As rodadas 1..N são as válidas.
 */
#ifndef COMMON_H
#define COMMON_H

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sched.h>

/* Relógio monotônico em nanossegundos (mesma base do time.monotonic_ns() do Python no Linux). */
static inline uint64_t now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec;
}

typedef struct {
    const char *env;   /* nome do ambiente: native, docker-overlay, ... */
    int runs;          /* número de rodadas válidas (além da rodada 0 de aquecimento) */
    long n;            /* tamanho da carga: iterações (ou MiB, no benchmark de disco) */
    const char *dir;   /* diretório de trabalho (só usado pelo benchmark de disco) */
} config_t;

static inline void usage(const char *prog) {
    fprintf(stderr, "uso: %s [--env NOME] [--runs N] [--n N] [--dir DIR]\n", prog);
    exit(2);
}

/* Lê os argumentos de linha de comando. default_n é o valor de --n se não for informado. */
static inline void parse_args(int argc, char **argv, config_t *cfg, long default_n) {
    cfg->env = "native";
    cfg->runs = 10;
    cfg->n = default_n;
    cfg->dir = "/tmp";
    for (int i = 1; i < argc; i++) {
        if (i + 1 >= argc) usage(argv[0]);
        if (strcmp(argv[i], "--env") == 0)       cfg->env = argv[++i];
        else if (strcmp(argv[i], "--runs") == 0) cfg->runs = atoi(argv[++i]);
        else if (strcmp(argv[i], "--n") == 0)    cfg->n = atol(argv[++i]);
        else if (strcmp(argv[i], "--dir") == 0)  cfg->dir = argv[++i];
        else usage(argv[0]);
    }
    if (cfg->runs < 1 || cfg->n < 1) usage(argv[0]);
}

static inline void print_header(void) {
    puts("benchmark,env,run,metric,value,unit");
}

static inline void emit(const char *bench, const char *env, int run,
                        const char *metric, double value, const char *unit) {
    printf("%s,%s,%d,%s,%.3f,%s\n", bench, env, run, metric, value, unit);
    fflush(stdout);
}

/* Fixa o processo na CPU informada (herdada pelos filhos). Falha só gera aviso. */
static inline void pin_cpu(int cpu) {
    cpu_set_t set;
    CPU_ZERO(&set);
    CPU_SET(cpu, &set);
    if (sched_setaffinity(0, sizeof(set), &set) != 0)
        perror("aviso: sched_setaffinity falhou (seguindo sem fixar CPU)");
}

#endif
