/* bench_alloc.c - custo de alocação de memória, separando alocar de tocar.
 *
 * Três medidas por rodada:
 *   malloc_free_64B  : malloc+free de 64 B (quase sempre resolvido em espaço de usuário)
 *   mmap_munmap_4MiB : mmap+munmap de 4 MiB SEM tocar nas páginas (só o custo da syscall)
 *   mmap_touch_4MiB  : mmap + escrever 1 byte por página + munmap (inclui page faults),
 *                      reportado em ns por página
 *
 * --n = iterações base: o malloc roda n*25 (é barato, precisa de um loop longo para sair do
 *        ruído) e os testes de mmap rodam n/50 (são bem mais caros).
 * O ponteiro é volatile e há escrita nele para o compilador não remover o par malloc/free.
 */
#include "common.h"
#include <sys/mman.h>
#include <unistd.h>

#define MAP_SIZE (4UL * 1024 * 1024)

int main(int argc, char **argv) {
    config_t cfg;
    parse_args(argc, argv, &cfg, 200000);

    long n_malloc = cfg.n * 25;
    long n_map = cfg.n / 50;
    if (n_map < 1) n_map = 1;
    long page = sysconf(_SC_PAGESIZE);
    long pages = MAP_SIZE / page;

    print_header();
    for (int run = 0; run <= cfg.runs; run++) {
        uint64_t t0, t1;

        t0 = now_ns();
        for (long i = 0; i < n_malloc; i++) {
            void *volatile p = malloc(64);
            if (!p) { perror("malloc"); return 1; }
            *(volatile char *)p = 1;
            free(p);
        }
        t1 = now_ns();
        emit("alloc_malloc_free_64B", cfg.env, run, "time_per_op", (double)(t1 - t0) / n_malloc, "ns/op");

        t0 = now_ns();
        for (long i = 0; i < n_map; i++) {
            void *volatile p = mmap(NULL, MAP_SIZE, PROT_READ | PROT_WRITE,
                                    MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
            if (p == MAP_FAILED) { perror("mmap"); return 1; }
            munmap(p, MAP_SIZE);
        }
        t1 = now_ns();
        emit("alloc_mmap_munmap_4MiB", cfg.env, run, "time_per_op", (double)(t1 - t0) / n_map, "ns/op");

        t0 = now_ns();
        for (long i = 0; i < n_map; i++) {
            char *p = mmap(NULL, MAP_SIZE, PROT_READ | PROT_WRITE,
                           MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
            if (p == MAP_FAILED) { perror("mmap"); return 1; }
            for (long j = 0; j < pages; j++)
                ((volatile char *)p)[j * page] = 1;
            munmap(p, MAP_SIZE);
        }
        t1 = now_ns();
        emit("alloc_mmap_touch_4MiB", cfg.env, run, "time_per_page",
             (double)(t1 - t0) / ((double)n_map * pages), "ns/page");
    }
    return 0;
}
