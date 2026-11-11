#!/usr/bin/env bash
# run_all.sh - roda os 5 benchmarks e junta tudo em um único CSV.
#
# Uso:   ./run_all.sh [ENV] [RUNS] [DIR_DISCO]
#   ENV        rótulo do ambiente (padrão: native). Ex.: native, docker-overlay, docker-bind
#   RUNS       rodadas válidas por benchmark, além da rodada 0 de aquecimento (padrão: 10)
#   DIR_DISCO  onde o bench_disk cria o arquivo temporário (padrão: /tmp)
#
# Variáveis opcionais:
#   CPU=2      fixa tudo na CPU 2 usando taskset
#   OUT=...    caminho do CSV de saída (padrão: resultados/ENV.csv)
#
# Gera também resultados/ENV.info.txt com os dados do ambiente (kernel, CPU, filesystem...).
set -euo pipefail

ENV_NAME="${1:-native}"
RUNS="${2:-10}"
DISK_DIR="${3:-/tmp}"

cd "$(dirname "$0")"
mkdir -p resultados
OUT="${OUT:-resultados/${ENV_NAME}.csv}"
INFO="resultados/${ENV_NAME}.info.txt"

# Compila só se houver Makefile e make disponíveis (dentro do container os binários já vêm prontos).
if [ -f Makefile ] && command -v make >/dev/null 2>&1; then
    make -s
fi

PREFIX=""
if [ -n "${CPU:-}" ]; then
    PREFIX="taskset -c ${CPU}"
fi

# ---- informações do ambiente (exigidas pelo Agents.md) ----
{
    echo "env: ${ENV_NAME}"
    echo "data: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "runs: ${RUNS}   cpu_fixada: ${CPU:-nao}"
    echo "kernel: $(uname -a)"
    echo "cpu: $(grep -m1 'model name' /proc/cpuinfo 2>/dev/null | cut -d: -f2- | sed 's/^ //')"
    echo "nucleos_visiveis: $(nproc)"
    echo "thp: $(cat /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null || echo indisponivel)"
    echo "gcc: $(gcc --version 2>/dev/null | head -1 || true)"
    echo "disk_dir: ${DISK_DIR}"
    echo "filesystem_do_disk_dir: $(df -T "${DISK_DIR}" 2>/dev/null | tail -1 || echo indisponivel)"
} > "${INFO}"

# ---- execução ----
echo "benchmark,env,run,metric,value,unit" > "${OUT}"
for b in bench_syscall bench_fork bench_pipe bench_alloc; do
    echo ">> ${b}" >&2
    ${PREFIX} ./${b} --env "${ENV_NAME}" --runs "${RUNS}" | tail -n +2 >> "${OUT}"
done
echo ">> bench_disk (dir=${DISK_DIR})" >&2
${PREFIX} ./bench_disk --env "${ENV_NAME}" --runs "${RUNS}" --dir "${DISK_DIR}" | tail -n +2 >> "${OUT}"

echo "ok: ${OUT}  (linhas: $(($(wc -l < "${OUT}") - 1)))  info: ${INFO}" >&2
