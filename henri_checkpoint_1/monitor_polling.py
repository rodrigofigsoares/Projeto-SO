"""Monitor por polling: varre o diretório a cada --interval milissegundos e
compara (mtime_ns, tamanho) com a varredura anterior.

Limitações conhecidas (fazem parte dos resultados do estudo):
- Arquivo criado e apagado dentro do mesmo intervalo nunca é visto.
- Várias alterações no mesmo intervalo viram um único MODIFY.
- Criar e escrever dentro do mesmo intervalo gera só CREATE (o inotify
  gera CREATE + MODIFY). O oráculo deve levar isso em conta.
- Modificações dentro da granularidade do mtime do filesystem podem passar
  despercebidas.
"""

import os
import time
from common import EventLog, install_stop_handler, parse_args

def snapshot(path):
    """Retorna {nome: (mtime_ns, tamanho)} dos arquivos regulares."""
    snap = {}
    with os.scandir(path) as entries:
        for entry in entries:
            try:
                if not entry.is_file(follow_symlinks=False):
                    continue
                st = entry.stat(follow_symlinks=False)
            except FileNotFoundError:
                continue  # sumiu durante a varredura
            snap[entry.name] = (st.st_mtime_ns, st.st_size)
    return snap

def main():
    args = parse_args("Monitor de diretório por polling.", with_interval=True)
    stop = install_stop_handler()
    log = EventLog(args.log)

    interval_sec = args.interval / 1000.0
    previous = snapshot(args.path)
    try:
        while not stop.wait(interval_sec):
            current = snapshot(args.path)
            ts = time.monotonic_ns()  # momento em que a varredura terminou
            for name in sorted(current):
                if name not in previous:
                    log.write(ts, "CREATE", os.path.join(args.path, name))
                elif current[name] != previous[name]:
                    log.write(ts, "MODIFY", os.path.join(args.path, name))
            for name in sorted(previous):
                if name not in current:
                    log.write(ts, "DELETE", os.path.join(args.path, name))
            previous = current
    finally:
        log.close()

if __name__ == "__main__":
    main()