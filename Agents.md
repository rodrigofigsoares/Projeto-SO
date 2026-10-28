# AGENTS.md — Contexto do projeto

> Leia este arquivo inteiro antes de escrever código. Ele descreve o projeto, as regras, a estrutura do repositório e **quem é dono de cada parte**. Se o usuário disser qual papel ele ocupa (P1–P4), trabalhe apenas dentro do escopo daquele papel, a menos que ele peça o contrário.

## 1. Visão geral

**Título:** *Quanto custa a abstração? Medindo containers e monitoramento de arquivos no Linux*

**Contexto acadêmico:** seminário (avaliação A02) da disciplina **INF0336 – Sistemas Operacionais**, UFG (Instituto de Informática), prof. Aldo Díaz. Grupo de 4 pessoas. Apresentação final em **26/11/2026**.

**O que o professor espera do seminário** (roteiro oficial):
- O que será estudado e como.
- Por que o objeto de estudo importa.
- Quais perguntas serão respondidas.
- Como os dados serão coletados e analisados (ou quais datasets).
- Discussão de **resultados esperados vs. resultados reais**.

**Stack exigida pela disciplina:** C, Git, Docker, VSCode (Jupyter/Colab também aparecem nos slides). Python é aceitável para os monitores, análise e gráficos.

**Ideia central:** o SO oferece abstrações (containers, notificações de arquivo) e elas têm custo. Medimos quanto custa, onde, e quando vale a pena.

## 2. Perguntas de pesquisa

1. **(Parte A)** Quanto overhead um container Docker adiciona a operações básicas do SO (syscall, `fork`, context switch, I/O de disco, alocação de memória) em relação à execução nativa?
2. **(Parte B)** `inotify` vs. polling: como se comparam em uso de CPU, latência de detecção e perda de eventos sob carga crescente?
3. **(Parte C, a ponte)** O comportamento do monitoramento de arquivos muda dentro de um container, dependendo de onde o diretório está (overlayfs, bind mount, volume Docker)?

## 3. Hipóteses (registrar ANTES de medir)

- CPU e memória: overhead próximo de zero (o container compartilha o kernel do host).
- Syscalls e I/O de disco: possível diferença por causa de overlayfs, seccomp e limites de cgroups.
- `inotify`: menos CPU e menor latência que polling, mas com risco de **perda de eventos** sob carga alta (`IN_Q_OVERFLOW`).
- Dentro de container: latência/perda podem variar entre overlay, bind mount e volume.

Os resultados reais serão comparados com estas hipóteses no relatório. **Não edite as hipóteses depois de ver os dados**; se algo for revisado, registre como nota separada.

## 4. Os 4 papéis

| Papel | Foco | Dono de |
|---|---|---|
| **P1 — QA / Avaliação** (GabrielFRails) | Metodologia, gerador de carga, oráculo de eventos, análise estatística, validação | `loadgen/`, `analysis/`, `docs/metodologia.md` |
| **P2 — Baixo nível ("hardcore")** | Benchmarks em C, observação do kernel por dentro | `bench_c/`, `kernel_probe/` |
| **P3 — Monitores (Python)** | Implementação de polling e inotify | `monitors/` |
| **P4 — Infra / Automação** | Docker, orquestração dos experimentos, coleta, gráficos | `docker/`, `scripts/`, `results/` (estrutura), `plots/` |

### P1 — QA / Avaliação

Responsável por garantir que os números sejam **confiáveis e interpretáveis**.

- **Gerador de carga** (`loadgen/`): cria, altera e apaga arquivos em taxas configuráveis (10, 100, 1.000, 10.000 eventos/s). Grava um **log de verdade** (oráculo) com timestamp de cada operação.
- **Oráculo e métricas de confiabilidade:** compara o log do gerador com o log de cada monitor para calcular eventos perdidos, duplicados e latência de detecção.
- **Plano de testes e metodologia** (`docs/metodologia.md`): número de repetições (mínimo 10), descarte da primeira rodada (cache frio), média, desvio padrão, intervalo de confiança, tratamento de outliers.
- **Análise** (`analysis/`): scripts/notebooks que leem os CSVs em `results/` e produzem as tabelas de esperado vs. real.
- **Validação cruzada:** revisar se os benchmarks de P2 e os monitores de P3 medem o que dizem medir (ex.: o loop não foi otimizado pelo compilador, o timer tem resolução suficiente).
- *Extra (se sobrar tempo):* testes automatizados dos próprios componentes (smoke tests, CI no GitHub Actions).

### P2 — Baixo nível ("hardcore")

Responsável por tudo que toca o kernel de perto. Esta é a parte que substitui a ideia original de "construir um kernel": em vez de escrever um, **observamos o kernel por dentro**.

- **Micro-benchmarks em C** (`bench_c/`), cada um um executável independente que imprime CSV em stdout:
  - `getpid` em loop (custo de syscall)
  - `fork` + `wait`
  - context switch (dois processos trocando bytes por `pipe`)
  - throughput de leitura/escrita sequencial em disco (com `O_DIRECT` ou `fsync` quando relevante)
  - alocação de memória (`malloc` e `mmap`)
- **Observação do kernel** (`kernel_probe/`): uso de `strace -c`, `perf stat`, `/proc/<pid>/` e, opcionalmente, **eBPF/bpftrace** para ver syscalls e eventos de `inotify` por dentro.
- **Opcional:** versão em C do monitor `inotify` (para comparar com a versão Python do P3 e isolar o custo da linguagem).
- Cuidados: usar `clock_gettime(CLOCK_MONOTONIC)`, evitar que o compilador elimine o loop (`volatile`/barreiras), compilar sempre com as mesmas flags (`-O2`), fixar CPU com `taskset` quando possível.

### P3 — Monitores (Python)

Responsável pelos dois monitores de diretório, com a **mesma interface** para que P1 e P4 possam rodá-los de forma intercambiável.

- **`monitors/polling.py`:** varre o diretório a cada `--interval` ms comparando `mtime`/tamanho (e hash opcional).
- **`monitors/inotify_mon.py`:** usa `inotify_simple` ou `watchdog`; deve tratar e **registrar `IN_Q_OVERFLOW`**.
- **Interface comum (CLI):**
  ```
  python monitors/<nome>.py --path <dir> --log <arquivo.csv> [--interval <ms>]
  ```
- **Formato do log de eventos** (CSV, uma linha por evento detectado):
  ```
  ts_detect_ns,event_type,path
  ```
  onde `ts_detect_ns` vem de `time.monotonic_ns()` e `event_type` ∈ {`create`, `modify`, `delete`, `overflow`}.
- Medir o **próprio uso de CPU** do monitor (por exemplo com `psutil` ou lendo `/proc/self/stat`) e gravar em um arquivo separado.

### P4 — Infra / Automação

Responsável por tornar tudo **reprodutível com um comando**.

- **`docker/`:** Dockerfile(s) para benchmarks e monitores; `docker-compose.yml` se necessário. Imagem base fixa (ex.: `ubuntu:24.04`) e versões pinadas.
- **Parte C:** configurar os três cenários de diretório monitorado: camada overlay do container, bind mount do host e volume Docker.
- **`scripts/`:** `run_all.sh` (ou similar) que executa as combinações ambiente × teste × repetições e escreve os resultados em `results/`.
- **Coleta de dados:** padronizar nomes de arquivo e metadados (ambiente, kernel, CPU, data, commit do Git) junto de cada execução.
- **`plots/`:** gráficos finais (barras com desvio padrão, latência vs. carga, perda de eventos vs. carga), em colaboração com P1, que valida a estatística.
- **Padronização do ambiente:** documentar em `docs/ambiente.md` a máquina de teste. Docker no Windows/Mac roda dentro de uma VM Linux, o que contamina o "nativo". O ideal é Linux real, ou WSL2/VM com isso **declarado explicitamente** no relatório.

## 5. Estrutura do repositório

```
.
├── AGENTS.md                  # este arquivo
├── README.md
├── bench_c/                   # P2
│   ├── Makefile
│   └── *.c
├── kernel_probe/              # P2
├── monitors/                  # P3
│   ├── polling.py
│   └── inotify_mon.py
├── loadgen/                   # P1
├── analysis/                  # P1
├── docker/                    # P4
├── scripts/                   # P4
├── results/                   # saída bruta (CSV), organizada por data/ambiente
├── plots/                     # P4 (validado por P1)
└── docs/
    ├── metodologia.md         # P1
    ├── ambiente.md            # P4
    └── relatorio/             # todos
```

## 6. Contratos entre componentes

Para que as partes se encaixem sem retrabalho:

- **Benchmarks de C (P2):** imprimem em stdout, CSV com cabeçalho:
  `benchmark,env,run,metric,value,unit`
- **Gerador de carga (P1):** grava o oráculo em CSV: `ts_ns,op,path` com `op` ∈ {`create`, `modify`, `delete`}. Argumentos: `--path`, `--rate`, `--duration`, `--log`.
- **Monitores (P3):** formato descrito na seção do P3.
- **Resultados (P4):** `results/<YYYY-MM-DD>/<env>/<experimento>/run_<n>.csv`, onde `env` ∈ {`native`, `docker-overlay`, `docker-bind`, `docker-volume`, `vm` (opcional)}.
- **Relógio:** todos usam relógio monotônico em nanossegundos. Gerador e monitor rodam na mesma máquina, então os timestamps são comparáveis. Registre a diferença entre `CLOCK_MONOTONIC` (C) e `time.monotonic_ns()` (Python): no Linux ambos usam a mesma base.

## 7. Cronograma (apresentação final em 26/11/2026)

| Semana | Entregas |
|---|---|
| 1 | Perguntas e hipóteses fechadas; repositório e ambiente Docker prontos |
| 2 | Benchmarks (P2) e monitores (P3) funcionando; gerador de carga (P1) funcionando |
| 3 | Rodar experimentos com repetições; Parte C |
| 4 | Análise, gráficos, esperado vs. real |
| 5 | Relatório, slides e ensaio |

**Corte de escopo se apertar:** reduzir a Parte A a 3 benchmarks e a Parte C a 2 tipos de montagem. O núcleo é **Parte B + Parte C**.

## 8. Regras para o agente de IA

1. **Respeite o dono de cada diretório.** Não reescreva código de outro papel sem o usuário pedir; sugira a mudança.
2. **Reprodutibilidade primeiro.** Tudo roda por script, sem passos manuais não documentados. Versões pinadas.
3. **Não invente resultados.** Nunca preencha tabelas, gráficos ou o relatório com números fictícios. Se não há dados, deixe um marcador `TODO`.
4. **Medição honesta.** Alerte sempre que um benchmark possa estar enviesado (otimização do compilador, cache quente, ambiente em VM, barulho de outros processos).
5. **Mantenha o código simples e legível.** É um trabalho acadêmico: o grupo precisa **entender e explicar** cada linha na apresentação. Prefira clareza a sofisticação.
6. **Comentários e documentação em português.** Nomes de identificadores em inglês, termos técnicos (overhead, syscall, inotify) em inglês.
7. **Commits pequenos** e mensagens descritivas; trabalhe em branches por papel (`p1-qa`, `p2-lowlevel`, `p3-monitors`, `p4-infra`).
8. **Integridade acadêmica.** O plano da disciplina exige que o uso de IA generativa siga o Guia de Integridade Acadêmica da UFG (uso ético, crítico, transparente e responsável). Quando o código for gerado com ajuda de IA, o grupo registra isso em `docs/uso-de-ia.md`.
9. **Segurança.** Rode experimentos de carga apenas em diretórios temporários (`/tmp/...`), nunca em diretórios do usuário. Não use `sudo` sem avisar o motivo.

## 9. Apresentação ao professor (resumo em 6 orações)

1. Nosso tema é *"Quanto custa a abstração? Medindo containers e monitoramento de arquivos no Linux"*, que estuda o custo de duas abstrações oferecidas pelo sistema operacional.
2. Vamos medir o overhead dos containers Docker em operações básicas do SO, como syscalls, criação de processos, troca de contexto, I/O de disco e memória, comparando com a execução nativa.
3. Também vamos comparar o monitoramento de arquivos com `inotify` e com polling, avaliando CPU, latência e perda de eventos sob carga crescente, inclusive dentro de containers.
4. Containers e monitoramento de eventos estão presentes em cloud, CI/CD, segurança e observabilidade, e saber onde está o custo ajuda a decidir quando vale a pena usá-los.
5. Vamos usar micro-benchmarks em C e monitores em Python, com um gerador de carga como referência para contar eventos perdidos, repetindo cada teste para reportar média e desvio padrão.
6. O tema cobre virtualização, sistemas de arquivos, I/O e escalonamento, usa a stack da disciplina (C, Docker e Git) e permite comparar resultados esperados com resultados reais.

## 10. Primeiros passos sugeridos para o agente

1. Criar a estrutura de pastas da seção 5 com `README.md` e `.gitignore` (ignorar binários e `results/` brutos pesados).
2. Criar `bench_c/Makefile` com flags padronizadas e um primeiro benchmark (`getpid` em loop) que siga o contrato de CSV.
3. Criar `docker/Dockerfile` base que compile e rode os benchmarks.
4. Criar o esqueleto de `loadgen/` e dos dois monitores seguindo a interface comum.
5. Criar `docs/metodologia.md` com o protocolo de medição (repetições, descarte, estatística).