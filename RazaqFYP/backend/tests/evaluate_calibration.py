"""
Module 8.4 - Expected Calibration Error (ECE), per the proposal's own
definition (Chapter 1.9): "the difference between a model's predicted
confidence scores and its actual predictive accuracy."

Uses the Bayesian diagnosis engine's top-prediction probability as its
"confidence," checked against whether that prediction was actually
correct, on the HELD-OUT test set (same split as Module 8.2 -- the model
never saw these during CPT construction).

Bins predictions into confidence deciles, computes the weighted average
gap between confidence and actual accuracy per bin -- a well-calibrated
model's "80% confident" predictions should be right about 80% of the time.
"""
import sys
import os
import csv
import ast

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app", "agents"))
from bayesian_diagnosis import diagnose, load_cpt, ALL_SYMPTOMS

N_BINS = 5  # kept small given only 40 test examples -- more bins would be too sparse


def load_test_vignettes(path="data/processed/iyawobench_test_5level.csv"):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    cpt = load_cpt()
    rows = load_test_vignettes()

    predictions = []  # (confidence, correct)
    for row in rows:
        symptoms = set(ast.literal_eval(row["symptoms"]))
        results = diagnose(symptoms, cpt, ALL_SYMPTOMS)
        top_disease, top_prob = results[0]
        correct = (top_disease == row["disease"])
        predictions.append((top_prob, correct))

    bin_edges = [i / N_BINS for i in range(N_BINS + 1)]
    bins = [[] for _ in range(N_BINS)]
    for conf, correct in predictions:
        bin_idx = min(int(conf * N_BINS), N_BINS - 1)
        bins[bin_idx].append((conf, correct))

    print(f"Test set size: {len(predictions)}")
    print(f"Overall top-1 diagnosis accuracy: {sum(c for _, c in predictions)/len(predictions)*100:.1f}%\n")

    ece = 0.0
    total_n = len(predictions)
    for i, bucket in enumerate(bins):
        if not bucket:
            print(f"Bin [{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}): empty")
            continue
        avg_conf = sum(c for c, _ in bucket) / len(bucket)
        avg_acc = sum(1 for _, correct in bucket if correct) / len(bucket)
        gap = abs(avg_conf - avg_acc)
        ece += (len(bucket) / total_n) * gap
        print(f"Bin [{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}): n={len(bucket)}, "
              f"avg_confidence={avg_conf:.3f}, avg_accuracy={avg_acc:.3f}, gap={gap:.3f}")

    print(f"\nExpected Calibration Error (ECE): {ece:.4f}")
    print("Lower is better (0 = perfectly calibrated).")
    print("\nHONEST NOTE: only 40 test examples split across 5 bins means some")
    print("bins have very few samples -- treat this as an illustrative first")
    print("measurement, not a statistically tight estimate. Worth revisiting")
    print("if the dataset grows.")


if __name__ == "__main__":
    main()
