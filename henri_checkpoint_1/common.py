"""Código compartilhado pelos monitores de polling e inotify (Parte B).

Contrato do log (CSV, uma linha por evento detectado):
    ts_detect_ns,event_type,path

- ts_detect_ns: time.monotonic_ns() no momento em que o monitor detecta o evento
  (relógio monotônico, em nanossegundos; o gerador de carga deve usar o mesmo).
- event_type: CREATE, MODIFY, DELETE ou OVERFLOW (só no inotify).
- path: caminho completo do arquivo (vazio em OVERFLOW).
"""

import argparse
import csv
import os
import signal
import sys
import threading

HEADER = ["ts_detect_ns", "event_type", "path"]

def parse_args(description, with_interval=False):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--path", required=True, help="diretório monitorado (não recursivo)")
    parser.add_argument("--log", required=True, help="arquivo CSV de saída (ideal: fora do --path)")
    if with_interval:
        parser.add_argument("--interval", type=float, default=50.0,
            help="intervalo entre varreduras, em milissegundos (padrão: 50.0)")
    args = parser.parse_args()

    if not os.path.isdir(args.path):
        parser.error(f"--path não é um diretório: {args.path}")
    if with_interval and args.interval <= 0:
        parser.error("--interval deve ser maior que zero")

    # Evita que o próprio log gere eventos no diretório monitorado.
    log_dir = os.path.dirname(os.path.abspath(args.log))
    if os.path.abspath(args.path) == log_dir:
        print("AVISO: o log está dentro do diretório monitorado e vai "
              "gerar eventos; prefira outro local.", file=sys.stderr)
    return args

class EventLog:
    """Escreve o CSV com buffer, para não distorcer a medição."""

    def __init__(self, filename):
        self._file = open(filename, "w", newline="", buffering=1 << 16)
        self._writer = csv.writer(self._file, lineterminator="\n")
        self._writer.writerow(HEADER)

    def write(self, ts_ns, event_type, path):
        self._writer.writerow((ts_ns, event_type, path))

    def close(self):
        self._file.flush()
        self._file.close()

def install_stop_handler():
    """Retorna um Event que é sinalizado em SIGINT/SIGTERM."""
    stop = threading.Event()

    handler = lambda *_: stop.set()

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)
    return stop
