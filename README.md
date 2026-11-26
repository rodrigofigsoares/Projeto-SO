# Quanto custa a abstração?

**Medindo containers e monitoramento de arquivos no Linux**

Seminário INF0336 — Sistemas Operacionais, UFG. Professor Aldo Díaz. Apresentação em 26/11/2026.

## Equipe e apresentações

- 202003564 — GABRIEL FREITAS DOS REIS
- 202401787 — HENRIQUE SIQUEIRA DE MAGALHAES
- 202401795 — JÚLIA MANCINE OLIVEIRA E CARVALHO
- 202401826 - RODRIGO DE FIGUEIREDO SOARES

## Resumo

O estudo investiga o custo de operações do sistema operacional em Docker e compara polling com `inotify` no monitoramento de arquivos. Foram analisados cinco benchmarks em C e demonstrações com monitores Python, com dez rodadas válidas por condição. Nos CSVs históricos do grupo, os tempos de `fork + wait` e `getpid` foram 2,025% e 38,656% maiores no Docker, respectivamente. Na demonstração em container, `inotify` registrou 21 criações por rodada, enquanto polling de 50 ms registrou 1,2 em média. A diferença de configuração no Linux histórico limita a atribuição das diferenças ao Docker.

## Introdução

Containers isolam processos e facilitam a reprodução de ambientes. Monitores de arquivos sustentam rotinas de sincronização, desenvolvimento e observabilidade. O custo desses recursos pode influenciar a escolha de como executar e monitorar uma aplicação.

Felter et al. [1] mostram que o desempenho relativo de Docker e KVM varia com a carga, motivando a análise por operação. A fila do `inotify` pode agrupar notificações idênticas e sinaliza saturação com `IN_Q_OVERFLOW` [2]. OverlayFS pode copiar arquivos preexistentes para a camada gravável (*copy-up*), enquanto volumes armazenam dados fora dessa camada [3, 4]. Mytkowicz et al. [5] mostram que a configuração experimental pode introduzir viés. Georges et al. [6] discutem como descrever a variabilidade com repetições e intervalos de confiança.

### Perguntas de pesquisa

1. Quanto Docker altera o custo de syscall, criação de processos, comunicação por pipe, I/O e alocação em relação ao Linux nativo?
2. Como polling e `inotify` se comparam em CPU, latência e operações não observadas sob carga crescente?
3. Como o monitoramento varia entre a camada gravável do container, bind mount e volume Docker?

### Hipóteses registradas antes das medições

- CPU e memória: overhead próximo de zero, pois o container compartilha o kernel do host.
- Syscalls e I/O de disco: possível diferença por causa de overlayfs, seccomp e limites de cgroups.
- `inotify`: menos CPU e menor latência que polling, mas com risco de perda de eventos sob carga alta (`IN_Q_OVERFLOW`).
- Dentro de container: latência/perda podem variar entre overlay, bind mount e volume.

## Metodologia

O grupo gerou os CSVs com benchmarks em C (`-O2`, `CLOCK_MONOTONIC`) e monitores em Python. Cada condição analisada tem dez rodadas após descarte da rodada de aquecimento (`run=0`). As rodadas válidas foram mantidas integralmente. O [checkpoint](docs/relatorio/checkpoint-1.md) registra o protocolo original e a [reprodução da coleta](analysis/coleta_2026-11-23/REPRODUCAO.md) detalha comandos, parâmetros e análise.

- **Linux histórico, 11/11.** Ryzen 7 5825U, x86-64 e Btrfs. A coleta nativa usou kernel `7.3.0-4-cachyos` e afinidade na CPU 2. O container com bind mount usou kernel `7.3.3-1-cachyos`, tinha uma CPU visível e não tinha afinidade registrada. A equivalência de compiladores e binários ficou sem confirmação. [CSV nativo](bench_c/resultados/native.csv) · [CSV Docker](bench_c/resultados_docker/docker-bind.csv).
- **Docker Desktop e macOS, 23/11.** Os cinco benchmarks C rodaram na VM Linux ARM64 e o disco foi medido em OverlayFS. Polling e `inotify` rodaram na camada gravável do container. O macOS executou apenas polling nativo. [Ambiente Docker](analysis/coleta_2026-11-23/docker-desktop/metadata.txt) · [Logs do macOS](analysis/coleta_2026-11-23/macos-native/).

### Cargas e critérios de avaliação

Em cada rodada no Docker Desktop foram executados 1 milhão de chamadas a `getpid`, 2 mil ciclos de `fork + wait` e 100 mil idas e voltas por pipe. O teste de disco usou um arquivo de 64 MiB e incluiu `fsync` na escrita. O teste de alocação distinguiu `malloc/free`, mapeamento com `mmap` e mapeamento com acesso às páginas. O pipe mede comunicação e escalonamento em conjunto.

Cada demonstração cria, altera e apaga um arquivo com pausas de 500 ms e depois cria e apaga outros 20 sem pausa. Polling verifica tamanho e `mtime` a cada 50 ms. Os logs contabilizam notificações por tipo e registram overflow quando sinalizado pelo `inotify`.

As métricas C são tempo por operação, página ou ida e volta no pipe e throughput em MiB/s. Os resumos calculam média, desvio padrão amostral e IC de 95% da média a partir dos valores por rodada. O gráfico usa `100 × (média Docker / média nativa − 1)`. CPU, latência e perda de operações ficam pendentes de coleta com carga controlada e log-oráculo.

O protocolo completo prevê cargas de 10, 100, 1.000 e 10.000 operações/s e polling a cada 50 e 1.000 ms. O log-oráculo deve registrar as operações realizadas com timestamps monotônicos para associá-las às notificações, medir o atraso de detecção e identificar operações sem correspondência.

### Reprodução

No macOS, `make run_docker_macos` executa os benchmarks e a demonstração em container. `python3 analysis/build_seminar_results.py` reconstrói os resumos a partir dos dados preservados. Para uma nova comparação no mesmo Linux, o alvo é `make run_linux_comparison`. [Procedimento completo](analysis/coleta_2026-11-23/REPRODUCAO.md).

![Fluxograma das fases do projeto](docs/relatorio/fluxograma.svg)

## Resultados

### Benchmarks em C

![Diferença entre médias no Linux histórico, por métrica](analysis/coleta_2026-11-23/historical_comparison.svg)

No Linux histórico, `getpid` levou 38,656% mais tempo e `fork + wait`, 2,025% mais tempo. O throughput de escrita foi 95,921% maior no Docker. A execução no Docker Desktop caracteriza a VM Linux ARM64. [Comparação histórica](analysis/coleta_2026-11-23/linux-historico/comparison.csv) · [CSV e estatísticas do Docker Desktop](analysis/coleta_2026-11-23/docker-desktop/).

Média ± desvio padrão na VM Linux do Docker Desktop, com dez rodadas válidas.

| Benchmark | Média ± DP | Unidade |
|---|---:|---|
| malloc/free (64 B) | 9,040 ± 0,577 | ns/op |
| mmap/munmap (4 MiB) | 1.015,162 ± 40,055 | ns/op |
| mmap com acesso às páginas | 60,275 ± 4,371 | ns/página |
| Leitura sequencial | 5.096,167 ± 624,932 | MiB/s |
| Escrita sequencial | 1.100,786 ± 195,674 | MiB/s |
| fork + wait | 98.728,069 ± 26.178,993 | ns/op |
| Ida e volta por pipe | 9.461,325 ± 1.450,347 | ns/ida e volta |
| getpid | 122,604 ± 6,208 | ns/op |

[Resumo do Docker Desktop com IC de 95%](analysis/coleta_2026-11-23/docker-desktop/benchmarks_summary.csv).

### Monitoramento

Média de notificações por rodada em dez rodadas válidas por condição.

| Ambiente | Monitor | Criação | Modificação | Remoção | Overflow |
|---|---|---:|---:|---:|---|
| macOS nativo | Polling | 1,1 | 1,0 | 1,1 | Não se aplica |
| Docker Desktop | Polling | 1,2 | 1,0 | 1,2 | Não se aplica |
| Docker Desktop | `inotify` | 21,0 | 22,0 | 21,0 | 0 |

[Resumo por condição com desvio padrão e IC](analysis/coleta_2026-11-23/monitor_repetitions_summary.csv).

## Discussão

Os tempos históricos de alocação foram menores no Docker e os de syscall foram maiores. Com kernels e configurações de CPU distintos entre as coletas, a hipótese de overhead próximo de zero para CPU e memória permanece em aberto. A variação por operação é coerente com a necessidade de avaliar cada carga separadamente [1]. As repetições quantificam a variabilidade [6], enquanto kernel, afinidade e ordem fixa podem introduzir viés [5]. No teste de disco, cache e armazenamento virtualizado também podem afetar o throughput.

A rotina de leitura solicita ao sistema o descarte das páginas em cache antes da medição. Como essa solicitação pode ser ignorada, a média de 5.096 MiB/s na VM caracteriza a leitura nas condições do teste, com possível influência de cache e armazenamento virtualizado. A comparação de armazenamento também deve distinguir arquivos criados na camada gravável de arquivos já presentes na imagem, cuja alteração pode acionar `copy-up` [3].

A maioria dos arquivos efêmeros desapareceu entre varreduras do polling. O `inotify` registrou as 21 criações e remoções, com zero registros de overflow nessa carga. Um log-oráculo permitiria parear operações e notificações, levando em conta o agrupamento de eventos [2]. A hipótese sobre CPU, latência e overflow sob carga alta segue pendente. A hipótese sobre armazenamento exige repetir o monitoramento em overlay, bind mount e volume [3, 4], com a mesma carga e os mesmos intervalos em cada montagem.

## Conclusão

Os benchmarks mostram diferenças por operação nos CSVs históricos, com evidência insuficiente para sustentar uma faixa geral de overhead de 2% a 5%. Na demonstração, `inotify` observou mais arquivos de vida curta que polling de 50 ms. A comparação em um mesmo Linux e a medição de CPU, latência e perda sob carga controlada completariam os objetivos do estudo.

## Referências

[1] FELTER, Wes; FERREIRA, Alexandre; RAJAMONY, Ram; RUBIO, Juan. **An updated performance comparison of virtual machines and Linux containers**. In: IEEE INTERNATIONAL SYMPOSIUM ON PERFORMANCE ANALYSIS OF SYSTEMS AND SOFTWARE (ISPASS), 2015. [S. l.]: IEEE, 2015. Disponível em: [publicação](https://research.ibm.com/publications/an-updated-performance-comparison-of-virtual-machines-and-linux-containers). Acesso em: 23 nov. 2026.

[2] LINUX MAN-PAGES PROJECT. **inotify(7): Linux manual page**. [S. l.], [s. d.]. Disponível em: [publicação](https://man7.org/linux/man-pages/man7/inotify.7.html). Acesso em: 23 nov. 2026.

[3] BROWN, Neil. **Overlay Filesystem**. The Linux Kernel documentation. [S. l.], [s. d.]. Disponível em: [publicação](https://www.kernel.org/doc/html/latest/filesystems/overlayfs.html). Acesso em: 23 nov. 2026.

[4] DOCKER INC. **Volumes**. Docker Docs. [S. l.], [s. d.]. Disponível em: [publicação](https://docs.docker.com/engine/storage/volumes/). Acesso em: 23 nov. 2026.

[5] MYTKOWICZ, Todd; DIWAN, Amer; HAUSWIRTH, Matthias; SWEENEY, Peter F. **Producing wrong data without doing anything obviously wrong!** In: INTERNATIONAL CONFERENCE ON ARCHITECTURAL SUPPORT FOR PROGRAMMING LANGUAGES AND OPERATING SYSTEMS, 14., 2009, Washington, DC. Proceedings [...]. New York: ACM, 2009. p. 265–276. DOI: https://doi.org/10.1145/1508244.1508275. Disponível em: [publicação](https://sape.inf.usi.ch/publications/asplos09.html). Acesso em: 23 nov. 2026.

[6] GEORGES, Andy; BUYTAERT, Dries; EECKHOUT, Lieven. **Statistically rigorous Java performance evaluation**. In: ACM SIGPLAN CONFERENCE ON OBJECT-ORIENTED PROGRAMMING SYSTEMS AND APPLICATIONS, 2007, Montreal. Proceedings [...]. New York: ACM, 2007. p. 57–76. DOI: https://doi.org/10.1145/1297027.1297033. Disponível em: [publicação](https://users.elis.ugent.be/~leeckhou/papers/oopsla07-stat.pdf). Acesso em: 23 nov. 2026.
