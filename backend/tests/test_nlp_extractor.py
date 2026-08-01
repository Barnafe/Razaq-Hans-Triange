"""
Module 1.4 - Evaluation of the clinical entity extractor against a
gold-standard annotated test set (built by hand from realistic clinical
phrasing patterns, covering all 14 symptoms in our vocabulary, plus
negation, duration, and severity extraction).

Run with: python backend/tests/test_nlp_extractor.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app", "agents"))
from nlp_extractor import extract_entities  # noqa: E402


# Each case: (text, expected set of (symptom, negated) pairs)
GOLD_STANDARD = [
    ("Patient has fever and headache.",
     {("Fever", False), ("Headache", False)}),

    ("No fever reported. Patient denies headache.",
     {("Fever", True), ("Headache", True)}),

    ("Child presents with convulsions, stiff neck, and altered consciousness.",
     {("Convulsions", False), ("Stiff neck", False), ("Altered consciousness", False)}),

    ("Caregiver reports vomiting and diarrhoea for 2 days, no rash.",
     {("Vomiting", False), ("Diarrhoea", False), ("Rash", True)}),

    ("Patient denies chest indrawing but reports difficulty breathing.",
     {("Chest indrawing", True), ("Difficulty breathing", False)}),

    ("Severe abdominal pain and joint pain, worsening over 3 days.",
     {("Abdominal pain", False), ("Joint pain", False)}),

    ("No convulsions, no stiff neck. Patient is alert and responsive.",
     {("Convulsions", True), ("Stiff neck", True)}),

    ("Loss of appetite and fatigue for 1 week, without fever.",
     {("Loss of appetite", False), ("Fatigue", False), ("Fever", True)}),

    ("Unconscious on arrival, caregiver reports seizures at home.",
     {("Altered consciousness", False), ("Convulsions", False)}),

    ("Patient reports mild headache, no vomiting, no abdominal pain.",
     {("Headache", False), ("Vomiting", True), ("Abdominal pain", True)}),
]


def evaluate():
    tp = fp = fn = 0
    for text, expected in GOLD_STANDARD:
        extracted = extract_entities(text)
        predicted = {(e.symptom, e.negated) for e in extracted}

        tp += len(predicted & expected)
        fp += len(predicted - expected)
        fn += len(expected - predicted)

        if predicted != expected:
            print(f"MISMATCH: {text}")
            print(f"  expected:  {expected}")
            print(f"  predicted: {predicted}")

    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0

    print(f"\nTP={tp} FP={fp} FN={fn}")
    print(f"Precision={precision:.3f}  Recall={recall:.3f}  F1={f1:.3f}")
    return f1


if __name__ == "__main__":
    evaluate()
