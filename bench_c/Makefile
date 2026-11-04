# Makefile dos micro-benchmarks (P2). Mesmas flags em TODOS os ambientes.
CC     = gcc
CFLAGS = -O2 -Wall -Wextra -std=gnu11 -D_GNU_SOURCE
BINS   = bench_syscall bench_fork bench_pipe bench_disk bench_alloc

all: $(BINS)

%: %.c common.h
	$(CC) $(CFLAGS) -o $@ $<

clean:
	rm -f $(BINS)

.PHONY: all clean
