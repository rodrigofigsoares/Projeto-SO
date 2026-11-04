/* bench_fork.c - custo de fork + wait.
 *
 * O filho sai imediatamente com _exit(0). Mede o ciclo completo
 * criar processo -> filho terminar -> pai coletar (waitpid).
 * O custo do fork depende do tamanho do espaço de endereço do pai;
 * aqui o processo é pequeno e igual em todos os ambientes.
 */
#include "common.h"
#include <sys/wait.h>
#include <unistd.h>

int main(int argc, char **argv) {
    config_t cfg;
    parse_args(argc, argv, &cfg, 2000);

    print_header();
    for (int run = 0; run <= cfg.runs; run++) {
        uint64_t t0 = now_ns();
        for (long i = 0; i < cfg.n; i++) {
            pid_t pid = fork();
            if (pid < 0) { perror("fork"); return 1; }
            if (pid == 0) _exit(0);
            if (waitpid(pid, NULL, 0) < 0) { perror("waitpid"); return 1; }
        }
        uint64_t t1 = now_ns();
        emit("fork_wait", cfg.env, run, "time_per_op", (double)(t1 - t0) / cfg.n, "ns/op");
    }
    return 0;
}
