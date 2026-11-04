/* bench_disk.c - throughput de escrita e leitura sequencial.
 *
 * --n   = tamanho do arquivo em MiB (padrão 64)
 * --dir = diretório onde o arquivo temporário é criado (padrão /tmp)
 *
 * Modo de I/O (precisa ser declarado no relatório):
 *   - escrita: write() em blocos de 1 MiB + fsync() ao final (o fsync entra no tempo);
 *   - leitura: read() em blocos de 1 MiB depois de posix_fadvise(DONTNEED),
 *     que PEDE ao kernel para descartar o page cache. Não é garantia de cache frio.
 *
 * CUIDADO: /tmp pode ser tmpfs (RAM). O programa avisa em stderr o tipo de
 * filesystem do diretório; para medir disco de verdade use --dir em um disco real.
 */
#include "common.h"
#include <fcntl.h>
#include <sys/vfs.h>
#include <unistd.h>

#define BLOCK (1024 * 1024)

static const char *fs_name(long type) {
    switch ((unsigned long)type) {
    case 0x01021994UL: return "tmpfs";
    case 0x794c7630UL: return "overlayfs";
    case 0xEF53UL:     return "ext2/3/4";
    case 0x58465342UL: return "xfs";
    case 0x9123683EUL: return "btrfs";
    default:           return "desconhecido";
    }
}

int main(int argc, char **argv) {
    config_t cfg;
    parse_args(argc, argv, &cfg, 64);

    struct statfs sfs;
    if (statfs(cfg.dir, &sfs) == 0)
        fprintf(stderr, "dir=%s filesystem=%s (0x%lx)%s\n", cfg.dir, fs_name(sfs.f_type),
                (unsigned long)sfs.f_type,
                sfs.f_type == 0x01021994 ? "  AVISO: tmpfs fica em RAM, não mede disco" : "");

    char path[4096];
    snprintf(path, sizeof(path), "%s/bench_disk_%d.tmp", cfg.dir, (int)getpid());

    char *buf = malloc(BLOCK);
    if (!buf) { perror("malloc"); return 1; }
    memset(buf, 0xA5, BLOCK);

    volatile long sink = 0;
    print_header();
    for (int run = 0; run <= cfg.runs; run++) {
        /* ---- escrita ---- */
        int fd = open(path, O_WRONLY | O_CREAT | O_TRUNC, 0600);
        if (fd < 0) { perror("open (escrita)"); return 1; }
        uint64_t t0 = now_ns();
        for (long i = 0; i < cfg.n; i++)
            if (write(fd, buf, BLOCK) != BLOCK) { perror("write"); return 1; }
        if (fsync(fd) < 0) { perror("fsync"); return 1; }
        uint64_t t1 = now_ns();
        close(fd);
        emit("disk_seq", cfg.env, run, "write_throughput",
             (double)cfg.n / ((t1 - t0) / 1e9), "MiB/s");

        /* ---- leitura ---- */
        fd = open(path, O_RDONLY);
        if (fd < 0) { perror("open (leitura)"); return 1; }
        posix_fadvise(fd, 0, 0, POSIX_FADV_DONTNEED);
        t0 = now_ns();
        for (long i = 0; i < cfg.n; i++) {
            ssize_t r = read(fd, buf, BLOCK);
            if (r != BLOCK) { perror("read"); return 1; }
            sink += buf[0];
        }
        t1 = now_ns();
        close(fd);
        emit("disk_seq", cfg.env, run, "read_throughput",
             (double)cfg.n / ((t1 - t0) / 1e9), "MiB/s");

        unlink(path);
    }
    free(buf);
    (void)sink;   /* lê a variável só para silenciar o aviso do compilador */
    return 0;
}
