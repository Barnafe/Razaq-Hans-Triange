"""
Module 8.2 (prep) - Applies the same 3-level -> 5-level triage mapping
(from map_triage_5level.py) to the train and test splits separately, so
we have 5-level ground truth for both.
"""
import csv
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from map_triage_5level import map_to_5level


def process(in_path, out_path):
    with open(in_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames + ["triage_5level"]

    for row in rows:
        row["triage_5level"] = map_to_5level(row)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"{out_path}: {len(rows)} rows")


if __name__ == "__main__":
    process("data/processed/iyawobench_train.csv", "data/processed/iyawobench_train_5level.csv")
    process("data/processed/iyawobench_test.csv", "data/processed/iyawobench_test_5level.csv")
