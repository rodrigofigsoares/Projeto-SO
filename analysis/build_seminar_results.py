#!/usr/bin/env python3
"""Reconstrói resumos e gráfico descritivo dos CSVs usados no README."""
import csv
import math
import statistics
import subprocess
import sys
from collections import Counter
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'analysis/coleta_2026-11-23'
LABELS = {
    'alloc_malloc_free_64B': 'malloc/free 64 B',
    'alloc_mmap_munmap_4MiB': 'mmap/munmap 4 MiB',
    'alloc_mmap_touch_4MiB': 'mmap + toque nas páginas',
    'fork_wait': 'fork + wait', 'pipe_pingpong': 'pipe ida e volta',
    'syscall_getpid': 'getpid',
}


def rows(path):
    with path.open(newline='') as source:
        return list(csv.DictReader(source))


def main():
    historical = OUT / 'linux-historico'
    for name, raw in [('native', 'bench_c/resultados/native.csv'),
                      ('docker', 'bench_c/resultados_docker/docker-bind.csv')]:
        subprocess.run([sys.executable, str(ROOT / 'analysis/summarize_benchmarks.py'),
                        str(ROOT / raw), str(historical / f'{name}_summary.csv')], check=True)
    subprocess.run([sys.executable, str(ROOT / 'analysis/compare_benchmarks.py'),
                    str(historical / 'native_summary.csv'), str(historical / 'docker_summary.csv'),
                    str(historical / 'comparison.csv')], check=True)
    subprocess.run([sys.executable, str(ROOT / 'analysis/summarize_benchmarks.py'),
                    str(OUT / 'docker-desktop/benchmarks_raw.csv'),
                    str(OUT / 'docker-desktop/benchmarks_summary.csv')], check=True)
    # Ausência de um tipo de evento conta como zero, inclusive overflow.
    conditions = [('macos-native', 'polling', OUT / 'macos-native', 'poll'),
                  ('docker-desktop', 'polling', OUT / 'docker-desktop/monitor-repetitions', 'poll'),
                  ('docker-desktop', 'inotify', OUT / 'docker-desktop/monitor-repetitions', 'inotify')]
    with (OUT / 'monitor_repetitions_summary.csv').open('w', newline='') as target:
        writer = csv.writer(target)
        writer.writerow(['environment', 'monitor', 'event_type', 'n', 'mean', 'stddev',
                         'ci95_low', 'ci95_high', 'min', 'max'])
        for env, monitor, folder, prefix in conditions:
            counts = [Counter(r['event_type'].lower() for r in rows(folder / f'{prefix}_run_{run}.csv'))
                      for run in range(1, 11)]
            for kind in ['create', 'modify', 'delete', 'overflow']:
                values = [c[kind] for c in counts]
                mean, sd = statistics.mean(values), statistics.stdev(values)
                margin = 2.262 * sd / math.sqrt(10)
                writer.writerow([env, monitor, kind, 10, mean, sd, mean-margin,
                                 mean+margin, min(values), max(values)])
    data = rows(historical / 'comparison.csv')
    # SVG vetorial simples; o eixo representa diferenças de médias, sem inferência causal.
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="510" viewBox="0 0 1080 510">',
           '<rect width="1080" height="510" fill="white"/>',
           '<g font-family="sans-serif" fill="#172b4d">',
           '<text x="24" y="35" font-size="22">Diferença das médias: Docker / nativo − 1 (%)</text>',
           '<text x="24" y="62" font-size="14">CSVs históricos de 11/11: kernels e configurações de CPU diferentes.</text>',
           '<text x="24" y="84" font-size="14">Comparação descritiva; não estima o overhead isolado do container.</text>']
    x0, scale = 440, 4.6
    for tick in [-20, 0, 20, 40, 60, 80, 100]:
        x = x0 + scale * tick
        svg += [f'<path d="M{x} 112 V435" stroke="#dce3ea"/>',
                f'<text x="{x}" y="458" text-anchor="middle" font-size="13">{tick}%</text>']
    for i, r in enumerate(data):
        label = LABELS.get(r['benchmark'], 'Disco: ' + r['metric'].replace('_throughput', ''))
        value = float(r['relative_difference_pct']); y = 124+i*39
        left = x0 + min(value, 0)*scale
        svg += [f'<text x="24" y="{y+19}" font-size="15">{escape(label)}</text>',
                f'<rect x="{left}" y="{y}" width="{abs(value)*scale}" height="26" fill="#4276b8"/>',
                f'<text x="{x0+max(value,0)*scale+8}" y="{y+19}" font-size="14">{value:+.2f}%</text>']
    svg += ['<text x="24" y="493" font-size="13">Tempo: positivo = mais lento. Throughput de disco: positivo = mais rápido. n = 10 por condição; run=0 excluído.</text>', '</g></svg>']
    (OUT / 'historical_comparison.svg').write_text('\n'.join(svg)+'\n')


if __name__ == '__main__':
    main()
