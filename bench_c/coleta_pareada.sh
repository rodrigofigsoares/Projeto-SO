#!/usr/bin/env bash
# coleta_pareada.sh - coleta ALTERNADA em blocos, com 4 ambientes:
#   N = native            processo comum no terminal, fixado com taskset
#   D = docker-bind       container com a configuração padrão (seccomp ligado)
#   S = docker-noseccomp  container com --security-opt seccomp=unconfined
#   C = native-scope      processo nativo (root) dentro de um scope raso do systemd, só com
#                         AllowedCPUs (mesma posição na hierarquia de cgroups do container, sem
#                         namespaces nem seccomp). É o baseline JUSTO para comparar com D e S.
#
# Uso:   ./coleta_pareada.sh [BLOCOS] [RODADAS] [CPU]
#   BLOCOS    nº de blocos; cada bloco roda os 4 ambientes uma vez   (padrão: 8)
#   RODADAS   rodadas válidas por benchmark, além da rodada 0         (padrão: 10)
#   CPU       núcleo do nativo (taskset) e do container (--cpuset-cpus)   (padrão: 2)
#
# Variáveis opcionais:
#   DOCKER="sudo docker"   comando do Docker (padrão: detecta 'docker' ou 'sudo docker')
#   NAO_REBUILD=1          não recompila nem reconstrói a imagem (só se tiver certeza)
#   PAUSA=5                segundos de pausa entre execuções
#   SAIDA=pasta            pasta de saída (padrão: resultados/pareado_AAAAMMDD_HHMMSS)
#
# O que o script faz:
#   1. compila os binários (estáticos) e reconstrói a imagem Docker;
#   2. confere por hash que host e container têm os MESMOS binários e o MESMO run_all.sh;
#   3. avisa se a máquina não está em modo desempenho / na tomada;
#   4. roda os blocos, variando a ordem dos ambientes entre blocos (desenho de Williams para
#      4 ambientes: cada ambiente vem logo depois de cada um dos outros o mesmo nº de vezes;
#      use BLOCOS múltiplo de 4), para a deriva da máquina não favorecer um deles;
#   5. guarda tudo em SAIDA/b1, SAIDA/b2, ... para o analisar_pares.py.
set -euo pipefail

BLOCOS="${1:-8}"
RODADAS="${2:-10}"
CPU="${3:-2}"
PAUSA="${PAUSA:-5}"
IMAGEM="bench-c"
BINS="bench_syscall bench_fork bench_pipe bench_disk bench_alloc"

cd "$(dirname "$0")"
SAIDA="${SAIDA:-resultados/pareado_$(date +%Y%m%d_%H%M%S)}"

# ---- Docker acessível? ----
if [ -z "${DOCKER:-}" ]; then
    if docker info >/dev/null 2>&1; then
        DOCKER="docker"
    elif sudo docker info >/dev/null 2>&1; then
        DOCKER="sudo docker"
    else
        echo "ERRO: não consegui falar com o Docker (daemon desligado ou sem permissão)." >&2
        echo "      Tente: sudo systemctl start docker" >&2
        exit 1
    fi
fi
echo ">> Docker: ${DOCKER}" >&2

# ---- 1. compila e reconstrói a imagem ----
if [ "${NAO_REBUILD:-0}" != 1 ]; then
    echo ">> compilando (estático)..." >&2
    make -s clean
    make -s EXTRA=-static
    echo ">> reconstruindo a imagem ${IMAGEM}..." >&2
    ${DOCKER} build -q -t "${IMAGEM}" . >/dev/null
fi

# ---- 2. mesmos binários e mesmo script no host e no container? ----
# shellcheck disable=SC2086
host_hashes="$(sha256sum ${BINS} run_all.sh)"
# shellcheck disable=SC2086
cont_hashes="$(${DOCKER} run --rm "${IMAGEM}" sha256sum ${BINS} run_all.sh)"
if [ "${host_hashes}" != "${cont_hashes}" ]; then
    echo "ERRO: host e container NÃO têm os mesmos arquivos. Diferenças:" >&2
    diff <(echo "${host_hashes}") <(echo "${cont_hashes}") >&2 || true
    echo "Reconstrua a imagem (rode sem NAO_REBUILD) e confira se o run_all.sh está atualizado." >&2
    exit 1
fi
echo ">> hashes iguais no host e no container (binários + run_all.sh)" >&2

if ! command -v systemd-run >/dev/null 2>&1; then
    echo "ERRO: systemd-run não encontrado (necessário para o ambiente native-scope)." >&2
    exit 1
fi

# ---- 3. condições da máquina ----
gov="$(cat "/sys/devices/system/cpu/cpu${CPU}/cpufreq/scaling_governor" 2>/dev/null || echo indisponivel)"
perfil="$(powerprofilesctl get 2>/dev/null || echo indisponivel)"
echo ">> governor da CPU ${CPU}: ${gov} | perfil de energia: ${perfil}" >&2
if [ "${perfil}" != "performance" ] && [ "${perfil}" != "indisponivel" ]; then
    echo "AVISO: perfil de energia não é 'performance'. Sugestão: powerprofilesctl set performance" >&2
fi
if ls /sys/class/power_supply/A*/online >/dev/null 2>&1 && ! grep -q 1 /sys/class/power_supply/A*/online; then
    echo "AVISO: o notebook parece estar na bateria. Ligue na tomada." >&2
fi

# ---- 4. pastas ----
mkdir -p "${SAIDA}" resultados
CRIOU_DADOS=0
if [ ! -d bench_data ]; then
    mkdir -p bench_data
    CRIOU_DADOS=1
fi
limpar() {
    if [ "${CRIOU_DADOS}" = 1 ]; then rmdir bench_data 2>/dev/null || true; fi
}
trap limpar EXIT

rodar() {   # $1 = N|D|S   $2 = número do bloco
    local amb nome
    amb="$1"
    case "${amb}" in
        N)  nome="native"
            CPU="${CPU}" ./run_all.sh native "${RODADAS}" "${PWD}/bench_data" ;;
        D)  nome="docker-bind"
            ${DOCKER} run --rm --cpuset-cpus="${CPU}" \
                -v "${PWD}/resultados:/bench/resultados" -v "${PWD}/bench_data:/data" \
                "${IMAGEM}" ./run_all.sh docker-bind "${RODADAS}" /data ;;
        C)  nome="native-scope"
            # sem CPU= de propósito: a fixação vem só do AllowedCPUs (cpuset), como no container
            sudo systemd-run --scope --quiet -p AllowedCPUs="${CPU}" \
                ./run_all.sh native-scope "${RODADAS}" "${PWD}/bench_data" ;;
        S)  nome="docker-noseccomp"
            ${DOCKER} run --rm --cpuset-cpus="${CPU}" --security-opt seccomp=unconfined \
                -v "${PWD}/resultados:/bench/resultados" -v "${PWD}/bench_data:/data" \
                "${IMAGEM}" ./run_all.sh docker-noseccomp "${RODADAS}" /data ;;
        *)  echo "ambiente desconhecido: ${amb}" >&2; exit 2 ;;
    esac
    mkdir -p "${SAIDA}/b$2"
    mv "resultados/${nome}.csv" "resultados/${nome}.info.txt" "${SAIDA}/b$2/"
}

# ---- 5. blocos alternados (desenho de Williams, 4 ambientes) ----
ORDENS=("N D C S" "D S N C" "S C D N" "C N S D")
{
    echo "inicio: $(date -u +%Y-%m-%dT%H:%M:%SZ)  blocos=${BLOCOS} rodadas=${RODADAS} cpu=${CPU}"
    echo "governor=${gov} perfil=${perfil}"
} > "${SAIDA}/ordem.txt"

for ((b = 1; b <= BLOCOS; b++)); do
    ordem="${ORDENS[$(( (b - 1) % 4 ))]}"
    echo "=== bloco ${b}/${BLOCOS}  ordem: ${ordem}  ($(date +%H:%M:%S))" >&2
    echo "b${b}: ${ordem}  $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "${SAIDA}/ordem.txt"
    for amb in ${ordem}; do
        echo "-- ${amb}" >&2
        rodar "${amb}" "${b}"
        sleep "${PAUSA}"
    done
done

echo "" >&2
echo "pronto: ${SAIDA}" >&2
echo "analise: python3 analisar_pares.py ${SAIDA}" >&2
