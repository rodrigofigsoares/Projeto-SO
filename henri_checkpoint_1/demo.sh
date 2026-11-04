#!/usr/bin/env bash
# Demonstração dos monitores: roda polling e inotify lado a lado,
# gera mudanças em dois cenários (lento e rápido) e mostra os logs.
#
# Uso (na pasta dos scripts, com o venv ativado):
#     bash demo.sh [DIRETORIO] [INTERVALO_POLLING_EM_MS]
# Exemplo:
#     bash demo.sh /tmp/teste 50
 
set -u
cd "$(dirname "$0")" || exit 1
 
DIR="${1:-/tmp/teste}"
INTERVAL="${2:-50}"
LOG_POLL="/tmp/poll.csv"
LOG_INO="/tmp/ino.csv"
 
# --- 1. Verificações ---------------------------------------------------
if ! command -v python3 >/dev/null; then
    echo "ERRO: python3 não encontrado."; exit 1
fi
if ! python3 -c "import inotify_simple" 2>/dev/null; then
    echo "ERRO: falta o pacote. Rode: pip install inotify_simple"; exit 1
fi
 
# --- 2. Preparar pasta e logs --------------------------------------------
rm -rf "$DIR" "$LOG_POLL" "$LOG_INO"
mkdir -p "$DIR"
 
# --- 3. Iniciar os monitores em segundo plano --------------------------------
python3 monitor_polling.py --path "$DIR" --log "$LOG_POLL" --interval "$INTERVAL" &
PID_POLL=$!
python3 monitor_inotify.py --path "$DIR" --log "$LOG_INO" &
PID_INO=$!
 
stop_monitors() {
    kill -TERM "$PID_POLL" "$PID_INO" 2>/dev/null
    wait "$PID_POLL" "$PID_INO" 2>/dev/null
}
trap stop_monitors EXIT
 
sleep 1   # tempo para os monitores começarem
 
# --- 4. Cenário A: mudanças lentas (com pausas) ------------------------------
echo ">> Cenário A: mudanças lentas (ambos devem ver tudo)"
echo oi    > "$DIR/lento.txt"; sleep 0.5
echo mais >> "$DIR/lento.txt"; sleep 0.5
rm "$DIR/lento.txt";           sleep 0.5
 
# --- 5. Cenário B: mudanças rápidas (sem pausas) ------------------------------
echo ">> Cenário B: arquivos criados e apagados em sequência (polling perde)"
for i in $(seq 1 20); do
    echo x > "$DIR/rapido_$i.txt"
    rm "$DIR/rapido_$i.txt"
done
sleep 0.5
 
# --- 6. Encerrar (isso grava os logs) -------------------------------------
stop_monitors
trap - EXIT
 
# --- 7. Resultados -------------------------------------------------------
contar() {
    awk -F, 'NR>1 && $2!="" {c[$2]++} END {for (k in c) printf "  %-9s %d\n", k, c[k]}' "$1" | sort
}
 
echo
echo "=== POLLING (intervalo ${INTERVAL}ms): eventos por tipo ==="
contar "$LOG_POLL"
echo "=== INOTIFY: eventos por tipo ==="
contar "$LOG_INO"
echo
echo "Logs completos: $LOG_POLL e $LOG_INO"
echo "Veja com: cat $LOG_POLL   |   cat $LOG_INO"