"""
Module 0.4 - Maps IyawoBench's native 3-level triage (REFER_NOW / REFER_TODAY /
TREAT_HERE) onto the 5-level ESI/MTS-style taxonomy used in the HANS-Triage
proposal (Red/Orange/Yellow/Green/Blue).

Mapping logic:
  REFER_NOW   -> Red if disease has CNS/danger-sign involvement
                 (Bacterial Meningitis, Cerebral Malaria) OR vitals show
                 shock (systolic < 90) / hypoxia (spo2 < 90)
              -> Orange otherwise
  REFER_TODAY -> Yellow if expected_severity == 'Severe'
              -> Green if expected_severity == 'Uncomplicated'
  TREAT_HERE  -> Blue

This preserves the dataset's real clinical judgments while expressing them
in the 5-tier scheme, rather than inventing a probability split.
"""
import csv
from collections import Counter

DANGER_SIGN_DISEASES = {"Bacterial Meningitis", "Cerebral Malaria"}

def map_to_5level(row):
    triage = row["expected_triage"]
    severity = row["expected_severity"]
    disease = row["disease"]
    spo2 = float(row["spo2"])
    systolic = float(row["systolic"])

    if triage == "REFER_NOW":
        if disease in DANGER_SIGN_DISEASES or spo2 < 90 or systolic < 90:
            return "Red"
        return "Orange"
    elif triage == "REFER_TODAY":
        return "Yellow" if severity == "Severe" else "Green"
    elif triage == "TREAT_HERE":
        return "Blue"
    raise ValueError(f"Unknown triage value: {triage}")


def main():
    in_path = "data/raw/iyawobench_v1.csv"
    out_path = "data/processed/iyawobench_v1_5level.csv"

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

    print("5-level triage distribution:")
    for tier, count in Counter(r["triage_5level"] for r in rows).most_common():
        print(f"  {tier}: {count}")
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
