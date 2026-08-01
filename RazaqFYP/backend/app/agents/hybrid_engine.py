"""
Module 2.3 - Hybrid Diagnostic + Triage Engine

Combines three pieces built so far into one final decision:
  1. Bayesian diagnosis (bayesian_diagnosis.py)      -> probability-ranked
     differential diagnosis
  2. Disease -> tier distribution (from real outcomes) -> converts the
     differential into a probability-weighted suggested triage tier
  3. Rule engine floor (rule_engine.py)               -> hard safety-net
     minimum tier, based on WHO IMCI danger signs

FINAL RULE: final_tier = max(rule_floor, bayesian_suggested_tier), using
urgency ordering. This means the rule layer can only push the outcome to
be MORE urgent than what the probabilistic model suggests, never less --
matching the proposal's "safety-first conservative bias" requirement.

SUGGESTED-TIER CALCULATION: rather than picking the single most likely
tier (argmax), we use an urgency-biased approach: compute the expected
tier as a weighted sum across differentials, then round UP (ceiling) to
the nearest tier rather than to the nearest. This deliberately errs toward
over-triage rather than under-triage when the model is uncertain --
consistent with the "safety-first" principle stated throughout the
proposal (better to over-triage a low-risk patient than under-triage a
high-risk one).
"""
import json
import math
import os
from bayesian_diagnosis import diagnose, load_cpt, ALL_SYMPTOMS
from rule_engine import rule_floor_tier, PatientInput, TIER_ORDER

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_DEFAULT_TIER_DIST_PATH = os.path.join(_PROJECT_ROOT, "data", "processed", "disease_tier_distribution.json")


def load_tier_distribution(path=None):
    path = path or _DEFAULT_TIER_DIST_PATH
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def bayesian_suggested_tier(disease_posteriors: list[tuple[str, float]], tier_dist: dict) -> str:
    """
    Computes a probability-weighted expected urgency score across all
    candidate diseases, then rounds UP to the nearest tier (safety bias).
    """
    tier_index = {t: i for i, t in enumerate(TIER_ORDER)}
    expected_score = 0.0

    for disease, disease_prob in disease_posteriors:
        dist = tier_dist.get(disease, {})
        for tier, tier_prob in dist.items():
            expected_score += disease_prob * tier_prob * tier_index[tier]

    ceiling_index = min(math.ceil(expected_score), len(TIER_ORDER) - 1)
    return TIER_ORDER[ceiling_index]


def run_hybrid_triage(patient: PatientInput) -> dict:
    cpt = load_cpt()
    tier_dist = load_tier_distribution()

    posteriors = diagnose(patient.symptoms, cpt, ALL_SYMPTOMS)
    bayes_tier = bayesian_suggested_tier(posteriors, tier_dist)
    rule_tier, rule_reasons = rule_floor_tier(patient)

    final_tier = TIER_ORDER[max(TIER_ORDER.index(bayes_tier), TIER_ORDER.index(rule_tier))]

    return {
        "final_tier": final_tier,
        "bayesian_suggested_tier": bayes_tier,
        "rule_floor_tier": rule_tier,
        "rule_reasons": rule_reasons,
        "differential_diagnosis": posteriors[:3],
        "decision_trail": (
            f"Bayesian model suggested '{bayes_tier}' based on differential "
            f"diagnosis. Rule engine floor was '{rule_tier}'"
            + (f" (triggered by: {'; '.join(rule_reasons)})" if rule_reasons else " (no rules triggered)")
            + f". Final tier = max(both) = '{final_tier}'."
        ),
    }


if __name__ == "__main__":
    test_cases = [
        ("Classic meningitis, high-risk vitals", PatientInput(
            symptoms={"Fever", "Headache", "Stiff neck", "Altered consciousness"},
            temperature=39.5, heart_rate=130, respiratory_rate=28,
            systolic=95, diastolic=60, spo2=92, age_years=8)),

        ("Uncomplicated malaria, stable vitals", PatientInput(
            symptoms={"Fever", "Headache", "Joint pain"},
            temperature=38.0, heart_rate=88, respiratory_rate=18,
            systolic=112, diastolic=74, spo2=98, age_years=22)),

        ("Ambiguous: mild symptoms but dangerously low SpO2", PatientInput(
            symptoms={"Fatigue"},
            temperature=37.3, heart_rate=95, respiratory_rate=20,
            systolic=105, diastolic=68, spo2=84, age_years=60)),
    ]

    for label, patient in test_cases:
        print(f"\n=== {label} ===")
        result = run_hybrid_triage(patient)
        print(f"FINAL TIER: {result['final_tier']}")
        print(f"Top differentials: {result['differential_diagnosis']}")
        print(f"Decision trail: {result['decision_trail']}")
