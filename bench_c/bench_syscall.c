/* bench_syscall.c - custo de uma syscall (getpid em loop).
 *
 * Usamos syscall(SYS_getpid) para garantir que a chamada vai ao kernel
 * (algumas versões da glibc já fizeram cache do PID). O resultado é somado
 * em uma variável volatile para o compilador não eliminar o loop.
 */
#include "common.h"
#include <sys/syscall.h>
#include <unistd.h>

int main(int argc, char **argv) {
    config_t cfg;
    parse_args(argc, argv, &cfg, 1000000);

    volatile long sink = 0;
    print_header();
    for (int run = 0; run <= cfg.runs; run++) {
        uint64_t t0 = now_ns();
        for (long i = 0; i < cfg.n; i++)
            sink += syscall(SYS_getpid);
        uint64_t t1 = now_ns();
        emit("syscall_getpid", cfg.env, run, "time_per_op", (double)(t1 - t0) / cfg.n, "ns/op");
    }
    (void)sink;   /* lê a variável só para silenciar o aviso do compilador */
    return 0;
}
