"""
Module 8.2 - Stratified 80/20 train/test split, by disease, so every
class is represented in both sets despite small per-class counts (e.g.
Cerebral Malaria has only 10 total examples). Fixed random seed for
reproducibility.

This directly fixes the honesty caveat flagged back in Phase 2: our CPTs
and tier distributions were being built AND evaluated on the same 200
vignettes. From here on, training data and test data are strictly
separate.
"""
import csv
import random
from collections import defaultdict

random.seed(42)


def main():
    with open("data/raw/iyawobench_v1.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    by_disease = defaultdict(list)
    for r in rows:
        by_disease[r["disease"]].append(r)

    train_rows, test_rows = [], []
    for disease, group in by_disease.items():
        shuffled = group[:]
        random.shuffle(shuffled)
        n_test = max(1, round(len(shuffled) * 0.2))  # at least 1 test example per class
        test_rows.extend(shuffled[:n_test])
        train_rows.extend(shuffled[n_test:])

    with open("data/processed/iyawobench_train.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(train_rows)

    with open("data/processed/iyawobench_test.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(test_rows)

    print(f"Train: {len(train_rows)} rows, Test: {len(test_rows)} rows")
    print("\nPer-disease split:")
    for disease in by_disease:
        n_train = sum(1 for r in train_rows if r["disease"] == disease)
        n_test = sum(1 for r in test_rows if r["disease"] == disease)
        print(f"  {disease}: train={n_train}, test={n_test}")


if __name__ == "__main__":
    main()
