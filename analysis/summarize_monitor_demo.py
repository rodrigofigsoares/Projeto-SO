#!/usr/bin/env python3
"""Conta notificações nos logs da demonstração dos monitores."""

import argparse
import csv
from collections import Counter
from pathlib import Path


def count_events(path):
    with path.open(newline="") as source:
        return Counter(row["event_type"].lower() for row in csv.DictReader(source))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("polling", type=Path)
    parser.add_argument("inotify", type=Path)
    args = parser.parse_args()

    print("monitor,event_type,count")
    for monitor, path in (("polling", args.polling), ("inotify", args.inotify)):
        for event_type, count in sorted(count_events(path).items()):
            print(f"{monitor},{event_type},{count}")


if __name__ == "__main__":
    main()
