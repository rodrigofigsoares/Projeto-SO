/* bench_pipe.c - ping-pong de 1 byte entre dois processos por pipes.
 *
 * Cada ida e volta envolve 4 syscalls (2 write + 2 read) e, com os dois
 * processos na mesma CPU, 2 trocas de contexto. Portanto o valor medido
 * inclui custo de comunicação e escalonamento, NÃO é um custo puro de
 * context switch (limitação já declarada no relatório).
 *
 * Os dois processos são fixados na CPU em que o pai está rodando
 * (use `taskset -c N` por fora para escolher a CPU).
 */
#include "common.h"
#include <sys/wait.h>
#include <unistd.h>

int main(int argc, char **argv) {
    config_t cfg;
    parse_args(argc, argv, &cfg, 100000);

    int p2c[2], c2p[2];   /* pai->filho e filho->pai */
    if (pipe(p2c) < 0 || pipe(c2p) < 0) { perror("pipe"); return 1; }

    int cpu = sched_getcpu();
    pin_cpu(cpu < 0 ? 0 : cpu);

    pid_t pid = fork();
    if (pid < 0) { perror("fork"); return 1; }

    if (pid == 0) {                       /* filho: devolve cada byte recebido */
        close(p2c[1]);
        close(c2p[0]);
        char b;
        while (read(p2c[0], &b, 1) == 1) {
            if (write(c2p[1], &b, 1) != 1) break;
        }
        _exit(0);
    }

    close(p2c[0]);                         /* pai */
    close(c2p[1]);
    char b = 'x';

    print_header();
    for (int run = 0; run <= cfg.runs; run++) {
        uint64_t t0 = now_ns();
        for (long i = 0; i < cfg.n; i++) {
            if (write(p2c[1], &b, 1) != 1) { perror("write"); return 1; }
            if (read(c2p[0], &b, 1) != 1)  { perror("read");  return 1; }
        }
        uint64_t t1 = now_ns();
        emit("pipe_pingpong", cfg.env, run, "time_per_roundtrip", (double)(t1 - t0) / cfg.n, "ns/roundtrip");
    }

    close(p2c[1]);                         /* EOF para o filho terminar */
    waitpid(pid, NULL, 0);
    return 0;
}
