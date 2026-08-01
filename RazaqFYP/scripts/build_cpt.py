"""
Module 2.1 - Conditional Probability Table (CPT) Construction

Builds P(symptom | disease) tables for each of our 8 diseases, used as the
foundation for per-malady Naive Bayes networks (per proposal Chapter 2's
"Naive Bayes Assumption" -- symptoms conditionally independent given disease).

METHODOLOGY (documented for report defensibility):
  1. PRIMARY SOURCE: empirical frequencies computed from the real 200-vignette
     IyawoBench dataset (data/raw/iyawobench_v1.csv).
  2. SMOOTHING: Laplace (add-1) smoothing applied to avoid zero-probabilities,
     which would let a single unseen symptom combination wrongly rule out a
     diagnosis with 100% certainty.
  3. DOCUMENTED EXCEPTION: cross-checking a few high-stakes values against
     published clinical literature during development surfaced a real
     discrepancy -- our dataset shows 100% stiff-neck prevalence in
     Bacterial Meningitis, but published literature (van de Beek et al.,
     cited in Medscape's meningitis clinical presentation review) puts
     classic neck-stiffness sensitivity around 30-45% in adults. Since
     stiff neck is a WHO IMCI danger sign directly driving Red-tier triage
     in our system, an inflated value here has real safety implications --
     an over-confident model could learn "if no stiff neck, probably not
     meningitis," which is clinically wrong and dangerous.
     We correct this ONE value using a weighted blend with the literature
     estimate. All other 111 disease-symptom pairs use the dataset value
     as-is.
  4. LIMITATION (state this explicitly in the report): a full literature
     cross-validation of all 112 disease-symptom probability pairs was not
     performed -- this is out of scope for a solo final-year timeline. This
     is a known limitation, not an oversight, and should be named as
     "future work" in Chapter 5.
"""
import csv
import ast
import json
from collections import defaultdict

ALL_SYMPTOMS = [
    "Fever", "Vomiting", "Headache", "Altered consciousness", "Fatigue",
    "Difficulty breathing", "Convulsions", "Loss of appetite", "Stiff neck",
    "Chest indrawing", "Joint pain", "Abdominal pain", "Diarrhoea", "Rash",
]

LAPLACE_K = 1  # smoothing pseudo-count

# Documented literature-informed correction (see module docstring)
LITERATURE_OVERRIDES = {
    ("Bacterial Meningitis", "Stiff neck"): {
        "literature_estimate": 0.40,
        "source": "Medscape meningitis clinical presentation review, citing "
                   "van de Beek et al. 696-case adult cohort: ~44% classic "
                   "triad (fever/headache/stiff neck); broader literature "
                   "range 30-45% for neck stiffness sensitivity alone.",
        "blend_weight": 0.5,  # 50/50 blend between dataset value and literature
    },
}


def load_vignettes(path="data/processed/iyawobench_train.csv"):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_cpt(rows):
    """
    Returns: {disease: {symptom: P(symptom present | disease)}}
    Also returns per-disease sample counts for transparency.
    """
    counts = defaultdict(lambda: defaultdict(int))
    totals = defaultdict(int)

    for r in rows:
        d = r["disease"]
        totals[d] += 1
        present = set(ast.literal_eval(r["symptoms"]))
        for s in ALL_SYMPTOMS:
            if s in present:
                counts[d][s] += 1

    cpt = {}
    provenance = {}
    for d in totals:
        cpt[d] = {}
        provenance[d] = {}
        n = totals[d]
        for s in ALL_SYMPTOMS:
            raw_p = (counts[d][s] + LAPLACE_K) / (n + 2 * LAPLACE_K)
            source = "dataset (Laplace-smoothed)"

            override = LITERATURE_OVERRIDES.get((d, s))
            if override:
                w = override["blend_weight"]
                raw_p = w * raw_p + (1 - w) * override["literature_estimate"]
                source = f"blended with literature ({override['source']})"

            cpt[d][s] = round(raw_p, 4)
            provenance[d][s] = source

    return cpt, provenance, dict(totals)


def main():
    rows = load_vignettes()
    cpt, provenance, sample_sizes = build_cpt(rows)

    output = {
        "cpt": cpt,
        "sample_sizes": sample_sizes,
        "provenance": provenance,
        "methodology_note": (
            "Primary source: real IyawoBench v1.0 vignette data (Laplace-"
            "smoothed). One documented literature-blended exception: "
            "Bacterial Meningitis / Stiff neck (see LITERATURE_OVERRIDES "
            "in scripts/build_cpt.py). Full literature cross-validation of "
            "all disease-symptom pairs is a stated limitation, not "
            "performed for all 112 pairs due to solo-timeline scope."
        ),
    }

    out_path = "data/processed/disease_symptom_cpt.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print("Sample sizes per disease:")
    for d, n in sorted(sample_sizes.items()):
        print(f"  {d}: n={n}")
    print(f"\nWrote {out_path}")
    print("\nExample -- Bacterial Meningitis CPT:")
    for s, p in cpt["Bacterial Meningitis"].items():
        print(f"  P({s}|Bacterial Meningitis) = {p}  [{provenance['Bacterial Meningitis'][s]}]")


if __name__ == "__main__":
    main()
