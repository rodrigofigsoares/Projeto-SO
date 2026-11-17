#!/usr/bin/env python3
"""Compara as médias de uma coleta Linux nativa e uma coleta Docker."""

import argparse
import csv
from pathlib import Path


KEY_FIELDS = ("benchmark", "metric", "unit")
OUTPUT_HEADER = [
    "benchmark",
    "metric",
    "unit",
    "native_mean",
    "docker_mean",
    "docker_native_ratio",
    "relative_difference_pct",
]


def read_summary(path):
    with path.open(newline="") as source:
        rows = list(csv.DictReader(source))
    return {tuple(row[field] for field in KEY_FIELDS): row for row in rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("native", type=Path, help="resumo da execução nativa")
    parser.add_argument("docker", type=Path, help="resumo da execução Docker")
    parser.add_argument("output", type=Path, help="CSV comparativo")
    args = parser.parse_args()

    native = read_summary(args.native)
    docker = read_summary(args.docker)
    if native.keys() != docker.keys():
        missing_docker = sorted(native.keys() - docker.keys())
        missing_native = sorted(docker.keys() - native.keys())
        raise ValueError(
            "métricas diferentes entre as coletas; "
            f"ausentes no Docker={missing_docker}, ausentes no nativo={missing_native}"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as target:
        writer = csv.writer(target, lineterminator="\n")
        writer.writerow(OUTPUT_HEADER)
        for benchmark, metric, unit in sorted(native):
            key = (benchmark, metric, unit)
            native_mean = float(native[key]["mean"])
            docker_mean = float(docker[key]["mean"])
            ratio = docker_mean / native_mean
            difference = (ratio - 1.0) * 100.0
            writer.writerow(
                (
                    benchmark,
                    metric,
                    unit,
                    f"{native_mean:.3f}",
                    f"{docker_mean:.3f}",
                    f"{ratio:.6f}",
                    f"{difference:.3f}",
                )
            )


if __name__ == "__main__":
    main()
