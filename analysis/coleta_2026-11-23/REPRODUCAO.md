# Coleta de 23/11/2026

Os CSVs desta pasta são resultados reais, preservados junto de seus metadados.
Os CSVs históricos originais continuam em `bench_c/resultados/` e
`bench_c/resultados_docker/`. O checkpoint de 4/11 não foi alterado.

## Preparação e execução

Executar na raiz do repositório, no macOS, com Docker Desktop aberto. Usar um
novo destino para cada coleta, preservando esta pasta como evidência. Exemplo:

```bash
make run_docker_macos RESULT_DIR=analysis/runs/repeticao-docker
python3 analysis/run_native_polling_demo.py analysis/runs/repeticao-native
```

O alvo Make compila os cinco benchmarks do zero, aplica uma rodada de aquecimento
e dez válidas e executa uma demo dos monitores. As versões/digests estão no
Makefile. O script nativo repete somente polling, onze vezes. Logs de compilação
e da recusa do alvo Linux foram preservados em `macos-native/`; os benchmarks C
e inotify não são compatíveis com este host Darwin.

Para repetir os dois monitores com onze rodadas no mesmo container (zero é
aquecimento), o comando desta coleta foi equivalente a:

```bash
mkdir -p analysis/runs/repeticao-docker/monitor-repetitions
docker run --rm \
  -v "$PWD/henri_checkpoint_1:/src:ro" \
  -v "$PWD/analysis/runs/repeticao-docker:/out" \
  python@sha256:efd0600c261faa9939c6b248af12908f96ac5f15463657a92302b058064a1aba \
  bash -lc 'set -eu
    PIP_ROOT_USER_ACTION=ignore pip install --disable-pip-version-check --quiet inotify-simple==1.3.5
    cp -r /src /work
    cd /work
    for run in $(seq 0 10); do
      bash demo.sh /tmp/projeto-so-repeated-demo 50 > /out/monitor-repetitions/demo_run_${run}.log
      cp /tmp/poll.csv /out/monitor-repetitions/poll_run_${run}.csv
      cp /tmp/ino.csv /out/monitor-repetitions/inotify_run_${run}.csv
    done
    { uname -a; cat /etc/os-release; python3 --version; getconf PAGESIZE; } > /out/python_environment.txt'
```

A carga usa exclusivamente `/tmp` dentro do container ou diretórios temporários
no host. `demo.sh` remove o diretório recebido antes de usá-lo: não passe um
diretório com arquivos pessoais. Os arquivos CSV de saída não são a carga.

## Reconstrução dos resultados preservados

```bash
python3 analysis/build_seminar_results.py
```

O script usa a biblioteca padrão do Python, descarta `run=0`, exige dez rodadas
C por métrica e reconstrói os resumos históricos, o resumo C novo, o resumo das
repetições dos monitores e o gráfico SVG. Os dados atuais ficam no destino fixo
`analysis/coleta_2026-11-23/`. Uma nova coleta deve receber destino e identificação
próprios, sem ser misturada a estes resultados.

## Alterações necessárias à execução

- Resolvidos conflitos de merge em três arquivos P2, escolhendo os trechos
  `lowlevel` (flags extras, ampliação do loop malloc e bloco pseudoaleatório).
- No Makefile raiz, `make clean all` substitui `make` no build Docker. A primeira
  tentativa reutilizou binários existentes e terminou com `Illegal instruction`
  antes de produzir dados válidos; a coleta publicada é a execução posterior,
  com recompilação completa.
- O metadado `git_commit` identifica a base `0b45db0`; essas correções locais
  ainda não faziam parte desse commit durante a coleta.
- Os benchmarks C usam ordem fixa; não houve controle global de ruído ou
  aleatorização. O polling nativo recebe carga Python e a demo Docker recebe
  carga shell. A inicialização é por espera, sem sinal de prontidão.
- Não há CPU, latência ou perda calculável com rigor sem oráculo. Um zero na
  coluna overflow do polling é apenas ausência desse tipo de registro.

A comparação definitiva exige Linux direto e container no mesmo sistema, com
mesmo kernel, compilação e recursos equivalentes. O comando existente é
`make run_linux_comparison`, que não deve ser executado no macOS.
