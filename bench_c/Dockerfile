# Dockerfile mínimo para rodar os MESMOS binários do host dentro de um container.
#
# Os binários precisam ser compilados de forma ESTÁTICA no host (assim o mesmo arquivo roda
# aqui, independente da versão da glibc da imagem, e a comparação nativo x Docker é justa):
#   make clean && make EXTRA=-static
FROM debian:bookworm-slim
WORKDIR /bench
COPY bench_syscall bench_fork bench_pipe bench_disk bench_alloc run_all.sh ./
CMD ["./run_all.sh", "docker-overlay", "10", "/tmp"]
