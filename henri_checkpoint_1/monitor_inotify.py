"""Monitor por inotify: o kernel avisa quando há CREATE, MODIFY ou DELETE.

Observações:
- Não é recursivo: monitora apenas o diretório informado em --path.
- Se a fila do inotify estoura (IN_Q_OVERFLOW), o kernel descarta eventos
  sem dizer quais. Registramos uma linha OVERFLOW para o oráculo contar.
- O timestamp é tirado logo após read() retornar, e vale para todos os
  eventos daquele lote.
- Requer: pip install inotify_simple
"""

import os
import time

from inotify_simple import INotify, flags

from common import EventLog, install_stop_handler, parse_args

WATCH_MASK = flags.CREATE | flags.MODIFY | flags.DELETE

def main():
    args = parse_args("Monitor de diretório por inotify.")
    stop = install_stop_handler()
    log = EventLog(args.log)

    inotify = INotify()
    inotify.add_watch(args.path, WATCH_MASK)

    try:
        while not stop.is_set():
            events = inotify.read(timeout = 200)  # ms; [] se estourar o tempo
            ts = time.monotonic_ns()
            for event in events:
                if event.mask & flags.Q_OVERFLOW:
                    log.write(ts, "OVERFLOW", "")
                    continue
                if event.mask & flags.ISDIR:
                    continue  # polling só acompanha arquivos regulares
                full_path = os.path.join(args.path, event.name)
                if event.mask & flags.CREATE:
                    log.write(ts, "CREATE", full_path)
                if event.mask & flags.MODIFY:
                    log.write(ts, "MODIFY", full_path)
                if event.mask & flags.DELETE:
                    log.write(ts, "DELETE", full_path)
    finally:
        inotify.close()
        log.close()

if __name__ == "__main__":
    main()
