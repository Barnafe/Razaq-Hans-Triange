"""
Module 2.2 - Deterministic Rule Layer (Safety Floor)

Encodes WHO IMCI / Surviving Sepsis danger-sign rules as deterministic
"if-then" gates that set a MINIMUM triage tier, independent of what the
Bayesian diagnosis engine concludes. This directly implements the
proposal's "safety-first conservative bias" (Chapter 4.2) and mirrors the
Schmitt-Thompson-style deterministic protocols described in Chapter 2.4.

WHY A SEPARATE RULE LAYER (not just trusting the Bayesian output):
A probabilistic model can, in principle, output a low-urgency diagnosis
even when a single danger sign is present, if other evidence is weak. In a
clinical safety system that is unacceptable -- a patient with convulsions
should never be triaged as anything less than urgent, regardless of what
a probability score says. The rule layer acts as a hard floor: the final
triage tier is `max(rule_floor, bayesian_suggested_tier)` in urgency (see
Module 2.3), so probabilistic reasoning can only make things MORE urgent
than the rules require, never less.

Rules are sourced from WHO IMCI (2014) danger-sign criteria and Surviving
Sepsis Campaign (2021) red-flag vitals, matching the guideline references
already present in the source dataset (see data/raw/iyawobench_v1.csv
'guidelines' column).
"""
from dataclasses import dataclass


TIER_ORDER = ["Blue", "Green", "Yellow", "Orange", "Red"]  # ascending urgency


@dataclass
class PatientInput:
    symptoms: set[str]
    temperature: float
    heart_rate: float
    respiratory_rate: float
    systolic: float
    diastolic: float
    spo2: float
    age_years: float
    has_vision_red_flag: bool = False  # set by Vision Agent (Module 5.3), see vision_agent.py


def rule_floor_tier(patient: PatientInput) -> tuple[str, list[str]]:
    """
    Returns (minimum_tier, list_of_triggered_rule_reasons).
    If no rule triggers, returns ("Blue", []) -- i.e. no floor imposed
    beyond the baseline tier.
    """
    triggered = []
    floor = "Blue"

    def escalate(tier, reason):
        nonlocal floor
        if TIER_ORDER.index(tier) > TIER_ORDER.index(floor):
            floor = tier
        triggered.append(reason)

    # --- RED: immediate life-threatening danger signs (WHO IMCI) ---
    if "Convulsions" in patient.symptoms:
        escalate("Red", "Convulsions present (WHO IMCI danger sign)")
    if "Altered consciousness" in patient.symptoms:
        escalate("Red", "Altered consciousness present (WHO IMCI danger sign)")
    if patient.spo2 < 90:
        escalate("Red", f"SpO2 {patient.spo2}% < 90% (hypoxia)")
    if patient.systolic < 90:
        escalate("Red", f"Systolic BP {patient.systolic} < 90 mmHg (possible shock)")
    if patient.respiratory_rate > 0 and patient.age_years < 5 and patient.respiratory_rate >= 70:
        escalate("Red", f"Respiratory rate {patient.respiratory_rate} >= 70 in child under 5 (severe distress)")

    # --- ORANGE: very urgent, WHO IMCI "referral" signs ---
    if "Stiff neck" in patient.symptoms:
        escalate("Orange", "Stiff neck present (possible meningitis)")
    if "Chest indrawing" in patient.symptoms:
        escalate("Orange", "Chest indrawing present (WHO IMCI danger sign)")
    if patient.temperature >= 39.5:
        escalate("Orange", f"Temperature {patient.temperature}C >= 39.5C (high fever)")
    if patient.heart_rate >= 130:
        escalate("Orange", f"Heart rate {patient.heart_rate} >= 130 bpm (tachycardia)")
    if patient.has_vision_red_flag:
        escalate("Orange", "Vision Agent flagged significant redness/inflammation "
                            "(NOTE: heuristic, uncalibrated threshold -- see "
                            "vision_agent.py limitations -- correlate clinically)")

    # --- YELLOW: urgent but not immediately life-threatening ---
    if "Difficulty breathing" in patient.symptoms:
        escalate("Yellow", "Difficulty breathing reported")
    if patient.temperature >= 38.5:
        escalate("Yellow", f"Temperature {patient.temperature}C >= 38.5C (fever)")

    return floor, triggered


if __name__ == "__main__":
    test_cases = [
        ("Child with convulsions", PatientInput(
            symptoms={"Convulsions", "Fever"}, temperature=39.0, heart_rate=140,
            respiratory_rate=30, systolic=100, diastolic=60, spo2=95, age_years=3)),

        ("Adult with low SpO2, no obvious symptoms flagged", PatientInput(
            symptoms={"Fatigue"}, temperature=37.5, heart_rate=90,
            respiratory_rate=18, systolic=110, diastolic=70, spo2=85, age_years=45)),

        ("Mild uncomplicated case", PatientInput(
            symptoms={"Joint pain", "Headache"}, temperature=37.8, heart_rate=85,
            respiratory_rate=16, systolic=115, diastolic=75, spo2=98, age_years=25)),

        ("Stiff neck only, normal vitals", PatientInput(
            symptoms={"Stiff neck"}, temperature=37.2, heart_rate=80,
            respiratory_rate=16, systolic=118, diastolic=76, spo2=99, age_years=30)),
    ]

    for label, patient in test_cases:
        tier, reasons = rule_floor_tier(patient)
        print(f"\n--- {label} ---")
        print(f"Rule floor: {tier}")
        for r in reasons:
            print(f"  - {r}")
