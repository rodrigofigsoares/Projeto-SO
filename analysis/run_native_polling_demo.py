#!/usr/bin/env python3
"""Repete a carga da demo no polling nativo, preservando logs por rodada.

Não substitui o experimento Linux: inotify não está disponível no macOS.
A rodada zero é aquecimento; a demo não tem oráculo temporal nem mede CPU.
"""
import argparse
import json
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    monitor = Path(__file__).resolve().parents[1] / 'henri_checkpoint_1/monitor_polling.py'
    for run in range(11):
        with tempfile.TemporaryDirectory(prefix='projeto-so-poll-', dir='/tmp') as folder:
            log = args.output.resolve() / f'poll_run_{run}.csv'
            proc = subprocess.Popen([sys.executable, str(monitor), '--path', folder,
                                     '--log', str(log), '--interval', '50'])
            try:
                time.sleep(1)
                if proc.poll() is not None:
                    raise RuntimeError('Monitor terminou antes da carga')
                slow = Path(folder) / 'lento.txt'
                slow.write_text('oi\n'); time.sleep(.5)
                with slow.open('a') as target:
                    target.write('mais\n')
                time.sleep(.5)
                slow.unlink(); time.sleep(.5)
                for i in range(1, 21):
                    fast = Path(folder) / f'rapido_{i}.txt'
                    fast.write_text('x\n')
                    fast.unlink()
                time.sleep(.5)
            finally:
                proc.terminate()
                proc.wait(timeout=5)
            if proc.returncode:
                raise RuntimeError(f'Monitor falhou: {proc.returncode}')
    (args.output / 'metadata.json').write_text(json.dumps({
        'system': platform.platform(), 'python': sys.version,
        'execution': 'macos-native' if sys.platform == 'darwin' else 'native',
        'interval_ms': 50, 'valid_runs': 10, 'warmup': 0,
        'load': 'demo: 1 arquivo lento + 20 efêmeros; geração Python',
        'startup': 'espera fixa de 1 s; sem handshake',
        'note': 'demo Docker gera carga via shell; não comparar tempo entre ambientes',
    }, indent=2) + '\n')


if __name__ == '__main__':
    main()
