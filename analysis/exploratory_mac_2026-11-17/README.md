# Resultados exploratórios no Mac — 17/11/2026

Estes dados servem como evidência concreta para o checkpoint de 19/11/2026.
Eles **não** respondem ainda à pergunta de overhead entre Linux nativo e
container, pois o Docker Desktop executa os containers dentro de uma VM Linux.

## Ambiente

- Host: MacBook Air (2020), Apple M1, 8 núcleos e 8 GB de memória.
- Host OS: macOS 15.6.1 (Darwin 24.6.0), ARM64.
- Docker Desktop: 4.37.2; engine 27.4.0.
- Container: Debian 12, kernel LinuxKit 6.10.14, ARM64, 8 CPUs e cerca de 4 GB.
- Compilador: imagem `gcc:14-bookworm`.
- Commit medido: `9b6a7414de4cb41654a72177a33c6b6a939ec041`.
- Rodadas: uma de aquecimento (`run=0`) e dez válidas (`run=1..10`).

Não foram registradas informações identificadoras do equipamento, como número
de série ou UUID.

## Microbenchmarks

O resumo foi calculado com média amostral, desvio padrão amostral e IC 95% pela
distribuição t de Student (9 graus de liberdade, valor crítico 2,262).

| Benchmark/métrica | Média | Desvio padrão | IC 95% |
|---|---:|---:|---:|
| `getpid` via syscall | 119,352 ns/op | 1,507 | [118,274; 120,429] |
| `fork` + `wait` | 84.096,583 ns/op | 8.994,491 | [77.662,759; 90.530,407] |
| pipe ping-pong | 8.507,331 ns/roundtrip | 136,812 | [8.409,468; 8.605,194] |
| escrita sequencial + `fsync` | 832,828 MiB/s | 223,338 | [673,074; 992,583] |
| leitura sequencial | 4.727,434 MiB/s | 474,828 | [4.387,787; 5.067,082] |
| `malloc` + `free` de 64 B | 8,661 ns/op | 0,054 | [8,622; 8,699] |
| `mmap` + `munmap` de 4 MiB | 981,082 ns/op | 30,523 | [959,249; 1.002,915] |
| `mmap` + toque nas páginas | 61,962 ns/página | 6,586 | [57,251; 66,673] |

O teste de disco usou `/tmp` dentro da camada `overlayfs`. A leitura muito alta
provavelmente reflete page cache e armazenamento virtualizado; o
`posix_fadvise(DONTNEED)` é apenas uma solicitação ao kernel, não uma garantia de
cache frio. Portanto, esses números não devem ser chamados de desempenho do SSD
do Mac.

## Demonstração polling × inotify

A demo aplicou três operações lentas a um arquivo e depois criou e apagou 20
arquivos sem pausa. Com polling a cada 50 ms:

| Monitor | Create | Modify | Delete | Total de notificações |
|---|---:|---:|---:|---:|
| polling | 1 | 1 | 1 | 3 |
| inotify | 21 | 22 | 21 | 64 |

O polling não observou os 20 arquivos de vida curta porque eles foram criados e
apagados entre duas varreduras. O total do inotify não deve ser comparado
diretamente com “operações semânticas”: uma criação que também escreve conteúdo
pode gerar notificações `CREATE` e `MODIFY` separadas.

Esta demo é qualitativa. Ainda faltam o gerador de carga com log-oráculo e o
pareamento entre operação e detecção para calcular perda e latência de forma
rigorosa.

## Reprodução do resumo

Para repetir toda a coleta no Mac, com o Docker Desktop aberto, execute na raiz
do repositório:

```bash
make run_docker_macos
```

Cada execução cria uma pasta datada em `analysis/runs/`. Apesar do nome do
alvo, no macOS ele usa automaticamente a VM Linux do Docker Desktop, pois os
benchmarks atuais e o inotify não são portáveis para o kernel Darwin.

Também é possível apenas refazer os resumos dos dados deste checkpoint:

```bash
python3 analysis/summarize_benchmarks.py \
  analysis/exploratory_mac_2026-11-17/data/benchmarks_raw.csv \
  analysis/exploratory_mac_2026-11-17/benchmarks_summary.csv

python3 analysis/summarize_monitor_demo.py \
  analysis/exploratory_mac_2026-11-17/data/poll.csv \
  analysis/exploratory_mac_2026-11-17/data/inotify.csv
```

## Mensagem recomendada para o checkpoint

> Já temos cinco microbenchmarks compilando e produzindo CSV no Linux do Docker
> Desktop, com aquecimento, dez repetições e resumo estatístico. Também temos uma
> demonstração concreta em que polling de 50 ms não vê arquivos criados e
> apagados entre varreduras, enquanto inotify recebe as notificações do kernel.
> Estes resultados são exploratórios no Mac e ainda não são a comparação final
> de overhead, porque o Docker Desktop inclui uma VM Linux. O próximo passo é
> adicionar o oráculo para medir perda e latência e repetir em Linux nativo.
