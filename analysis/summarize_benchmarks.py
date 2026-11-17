#!/usr/bin/env python3
"""Resume as rodadas válidas dos microbenchmarks em C.

A rodada zero é aquecimento e não entra nas estatísticas. Como o protocolo
atual usa dez rodadas válidas, o IC 95% usa a distribuição t de Student com
9 graus de liberdade (valor crítico 2,262).
"""

import argparse
import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path


T_CRITICAL_95_DF9 = 2.262
OUTPUT_HEADER = [
    "benchmark",
    "metric",
    "n",
    "mean",
    "stddev",
    "ci95_low",
    "ci95_high",
    "unit",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Descarta run=0 e calcula média, desvio padrão e IC 95%."
    )
    parser.add_argument("input", type=Path, help="CSV bruto dos benchmarks")
    parser.add_argument("output", type=Path, help="CSV de resumo")
    return parser.parse_args()


def main():
    args = parse_args()
    groups = defaultdict(list)

    with args.input.open(newline="") as source:
        for row in csv.DictReader(source):
            if int(row["run"]) == 0:
                continue
            key = (row["benchmark"], row["metric"], row["unit"])
            groups[key].append(float(row["value"]))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as target:
        writer = csv.writer(target, lineterminator="\n")
        writer.writerow(OUTPUT_HEADER)
        for (benchmark, metric, unit), values in sorted(groups.items()):
            if len(values) != 10:
                raise ValueError(
                    f"{benchmark}/{metric}: esperadas 10 rodadas válidas, "
                    f"encontradas {len(values)}"
                )
            mean = statistics.mean(values)
            stddev = statistics.stdev(values)
            margin = T_CRITICAL_95_DF9 * stddev / math.sqrt(len(values))
            writer.writerow(
                (
                    benchmark,
                    metric,
                    len(values),
                    f"{mean:.3f}",
                    f"{stddev:.3f}",
                    f"{mean - margin:.3f}",
                    f"{mean + margin:.3f}",
                    unit,
                )
            )


if __name__ == "__main__":
    main()
