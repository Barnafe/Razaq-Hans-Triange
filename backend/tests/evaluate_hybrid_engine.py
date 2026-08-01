"""
Module 8.2 - Evaluation of the hybrid engine against a HELD-OUT test set
(Module 2.5's original version tested against the same data used to build
the CPTs -- this version fixes that).

Computes the Track B metrics specified in the proposal (Chapter 3.7):
  - Under-triage rate: predicted tier LESS urgent than the real expected
    tier (the dangerous direction -- a genuinely urgent patient is told
    they can wait)
  - Over-triage rate: predicted tier MORE urgent than expected (costly,
    but safe -- consistent with the "safety-first conservative bias")
  - Quadratic Weighted Kappa (QWK): agreement between predicted and actual
    tier, penalizing large misses (e.g. Blue vs Red) far more than small
    ones (e.g. Yellow vs Orange)

METHODOLOGY: a stratified 80/20 train/test split (scripts/train_test_split.py,
fixed seed 42) was built by disease, so every class -- including Cerebral
Malaria with only 10 total examples -- is represented in both sets. CPTs
(scripts/build_cpt.py) and the disease->tier distribution
(scripts/build_tier_distribution.py) were rebuilt using ONLY the 160
training vignettes. This script evaluates against the 40 TEST vignettes,
which the model has never seen in any form. This is now a genuine
held-out evaluation, not a self-consistency check.

HONEST LIMITATION STILL WORTH STATING: 40 test examples (as few as 2 for
Cerebral Malaria) is a small test set -- individual misclassifications
move the metrics substantially. Results here are a real, defensible signal
of performance, not a precise population estimate. A larger dataset would
give tighter confidence intervals -- noted as future work.
"""
import csv
import ast
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app", "agents"))
from triage_agent import triage_agent
from rule_engine import PatientInput, TIER_ORDER

TIER_INDEX = {t: i for i, t in enumerate(TIER_ORDER)}


def load_test_vignettes(path="data/processed/iyawobench_test_5level.csv"):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def row_to_patient(row) -> PatientInput:
    return PatientInput(
        symptoms=set(ast.literal_eval(row["symptoms"])),
        temperature=float(row["temperature"]),
        heart_rate=float(row["heartRate"]),
        respiratory_rate=float(row["respiratoryRate"]),
        systolic=float(row["systolic"]),
        diastolic=float(row["diastolic"]),
        spo2=float(row["spo2"]),
        age_years=float(row["patientAge"]) if row["patientAgeUnit"] == "years" else float(row["patientAge"]) / 12,
    )


def quadratic_weighted_kappa(actual: list[int], predicted: list[int], n_classes: int) -> float:
    """Pure-Python QWK implementation (no sklearn dependency)."""
    O = [[0] * n_classes for _ in range(n_classes)]
    for a, p in zip(actual, predicted):
        O[a][p] += 1

    act_hist = [0] * n_classes
    pred_hist = [0] * n_classes
    for a in actual:
        act_hist[a] += 1
    for p in predicted:
        pred_hist[p] += 1

    N = len(actual)
    W = [[((i - j) ** 2) / ((n_classes - 1) ** 2) for j in range(n_classes)] for i in range(n_classes)]
    E = [[act_hist[i] * pred_hist[j] / N for j in range(n_classes)] for i in range(n_classes)]

    num = sum(W[i][j] * O[i][j] for i in range(n_classes) for j in range(n_classes))
    den = sum(W[i][j] * E[i][j] for i in range(n_classes) for j in range(n_classes))

    return 1 - (num / den) if den != 0 else 0.0


def evaluate():
    rows = load_test_vignettes()

    actual_tiers = []
    predicted_tiers = []
    under_triage_count = 0
    over_triage_count = 0
    exact_match = 0

    mismatches = []

    for row in rows:
        patient = row_to_patient(row)
        result = triage_agent(patient)
        predicted = result["urgency_classification"]["tier"]
        actual = row["triage_5level"]

        actual_idx = TIER_INDEX[actual]
        predicted_idx = TIER_INDEX[predicted]

        actual_tiers.append(actual_idx)
        predicted_tiers.append(predicted_idx)

        if predicted_idx == actual_idx:
            exact_match += 1
        elif predicted_idx < actual_idx:
            under_triage_count += 1
            mismatches.append((row["vignette_id"], row["disease"], actual, predicted, "UNDER"))
        else:
            over_triage_count += 1
            mismatches.append((row["vignette_id"], row["disease"], actual, predicted, "OVER"))

    n = len(rows)
    qwk = quadratic_weighted_kappa(actual_tiers, predicted_tiers, len(TIER_ORDER))

    print(f"Total vignettes evaluated: {n}")
    print(f"Exact tier match: {exact_match}/{n} ({exact_match/n*100:.1f}%)")
    print(f"Under-triage rate: {under_triage_count}/{n} ({under_triage_count/n*100:.1f}%)  <- SAFETY-CRITICAL METRIC")
    print(f"Over-triage rate: {over_triage_count}/{n} ({over_triage_count/n*100:.1f}%)")
    print(f"Quadratic Weighted Kappa: {qwk:.3f}")

    print(f"\n--- Under-triage cases (most important to review) ---")
    under_cases = [m for m in mismatches if m[4] == "UNDER"]
    for vid, disease, actual, predicted, _ in under_cases[:15]:
        print(f"  {vid} ({disease}): actual={actual}, predicted={predicted}")
    if len(under_cases) > 15:
        print(f"  ... and {len(under_cases) - 15} more")

    return {
        "n": n, "exact_match": exact_match, "under_triage": under_triage_count,
        "over_triage": over_triage_count, "qwk": qwk,
    }


if __name__ == "__main__":
    evaluate()

# NOTE FOR FINAL REPORT (Phase 8 -- DONE):
# This now evaluates against a genuine held-out test set (see module
# docstring). These ARE reportable Track B numbers -- caveat the small
# test set size (40 examples, as few as 2 per class for Cerebral Malaria)
# honestly rather than presenting them as precise.
