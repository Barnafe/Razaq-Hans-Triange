"""
Module 1.4 - Evaluation of the clinical entity extractor (Track A metric).

IMPORTANT NOTE ON THIS TEST SET: this is a self-authored gold-standard set
(25 sentences, hand-labeled), NOT an external clinically-validated corpus.
Be upfront about this in your report -- say "internally authored evaluation
set of 25 annotated sentences covering the project's 14-symptom vocabulary,
designed to test synonym recognition, negation, and multi-symptom sentences"
rather than implying it's an independent clinical benchmark. This is a
completely normal and defensible thing to do for a solo final year project
-- large annotated clinical corpora aren't freely available, and panels
understand that. Just don't overstate what it is.

Computes Precision / Recall / F1 for:
  1. Symptom detection (did we find the right symptom, regardless of negation)
  2. Negation classification (of symptoms found, was negation status correct)
"""
from nlp_extractor import extract_entities

# Each test case: (text, set of (symptom, is_negated) ground truth tuples)
GOLD_STANDARD = [
    ("Patient presents with fever and vomiting for 3 days, no diarrhoea, altered consciousness noted on arrival.",
     {("Fever", False), ("Vomiting", False), ("Diarrhoea", True), ("Altered consciousness", False)}),

    ("Caregiver reports mild headache and joint pain since 2 days ago. Denies chest indrawing or difficulty breathing.",
     {("Headache", False), ("Joint pain", False), ("Chest indrawing", True), ("Difficulty breathing", True)}),

    ("Child has severe convulsions and stiff neck, rapidly deteriorating over the past 6 hours.",
     {("Convulsions", False), ("Stiff neck", False)}),

    ("No fever, no vomiting. Patient reports only mild fatigue for 1 week.",
     {("Fever", True), ("Vomiting", True), ("Fatigue", False)}),

    ("Patient is febrile with abdominal pain and loss of appetite, no rash observed.",
     {("Fever", False), ("Abdominal pain", False), ("Loss of appetite", False), ("Rash", True)}),

    ("Presents with dyspnea and cyanosis-free breathing, denies seizures.",
     {("Difficulty breathing", False), ("Convulsions", True)}),

    ("Unresponsive on arrival, no history of joint pain or rash.",
     {("Altered consciousness", False), ("Joint pain", True), ("Rash", True)}),

    ("3-day history of diarrhoea and vomiting, no fever recorded, mild fatigue noted.",
     {("Diarrhoea", False), ("Vomiting", False), ("Fever", True), ("Fatigue", False)}),

    ("Patient denies headache but reports throwing up twice and stomach pain.",
     {("Headache", True), ("Vomiting", False), ("Abdominal pain", False)}),

    ("Neck stiffness and photophobia present, absent of convulsions.",
     {("Stiff neck", False), ("Convulsions", True)}),

    ("Child confused and lethargic, no chest indrawing, breathing normally.",
     {("Altered consciousness", False), ("Chest indrawing", True)}),

    ("Reports fatigue and poor appetite for two weeks, no fever or rash.",
     {("Fatigue", False), ("Loss of appetite", False), ("Fever", True), ("Rash", True)}),

    ("Severe abdominal pain with vomiting, denies diarrhoea.",
     {("Abdominal pain", False), ("Vomiting", False), ("Diarrhoea", True)}),

    ("Patient febrile, no altered consciousness, no convulsions, mild joint ache present.",
     {("Fever", False), ("Altered consciousness", True), ("Convulsions", True), ("Joint pain", False)}),

    ("Skin rash noted, no fever, no headache.",
     {("Rash", False), ("Fever", True), ("Headache", True)}),

    ("Labored breathing and chest in-drawing observed, no cough-related complaints.",
     {("Difficulty breathing", False), ("Chest indrawing", False)}),

    ("Denies fatigue, denies weakness, reports mild headache only.",
     {("Fatigue", True), ("Headache", False)}),

    ("Fits noted by caregiver, no neck stiffness, no photophobia.",
     {("Convulsions", False), ("Stiff neck", True)}),

    ("No loss of appetite, patient eating normally, mild fever present.",
     {("Loss of appetite", True), ("Fever", False)}),

    ("Confusion and drowsiness reported, denies rash or joint pain.",
     {("Altered consciousness", False), ("Rash", True), ("Joint pain", True)}),

    ("Patient vomiting repeatedly, diarrhoea for 4 days, no abdominal pain.",
     {("Vomiting", False), ("Diarrhoea", False), ("Abdominal pain", True)}),

    ("No seizures, no altered consciousness, patient alert and oriented.",
     {("Convulsions", True), ("Altered consciousness", True)}),

    ("Presents with high temperature and headache, negative for stiff neck.",
     {("Fever", False), ("Headache", False), ("Stiff neck", True)}),

    ("Mild rash on trunk, no fatigue, no loss of appetite.",
     {("Rash", False), ("Fatigue", True), ("Loss of appetite", True)}),

    ("Breathless and weak, no vomiting, no diarrhoea reported.",
     {("Difficulty breathing", False), ("Fatigue", False), ("Vomiting", True), ("Diarrhoea", True)}),
]


def evaluate():
    tp_detect = fp_detect = fn_detect = 0
    tp_negation = fn_negation = 0  # negation correctness, counted only over true positives

    for text, gold in GOLD_STANDARD:
        predicted = extract_entities(text)
        pred_symptoms = {(e.symptom, e.negated) for e in predicted}
        pred_symptom_names = {e.symptom for e in predicted}
        gold_symptom_names = {s for s, _ in gold}

        # Detection: did we find the right symptom names (ignoring negation)?
        tp_detect += len(pred_symptom_names & gold_symptom_names)
        fp_detect += len(pred_symptom_names - gold_symptom_names)
        fn_detect += len(gold_symptom_names - pred_symptom_names)

        # Negation: for symptoms correctly detected, was negation status right?
        for sym, gold_neg in gold:
            pred_match = next((e for e in predicted if e.symptom == sym), None)
            if pred_match is not None:
                if pred_match.negated == gold_neg:
                    tp_negation += 1
                else:
                    fn_negation += 1

    precision = tp_detect / (tp_detect + fp_detect) if (tp_detect + fp_detect) else 0
    recall = tp_detect / (tp_detect + fn_detect) if (tp_detect + fn_detect) else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0
    negation_accuracy = tp_negation / (tp_negation + fn_negation) if (tp_negation + fn_negation) else 0

    print(f"Test set size: {len(GOLD_STANDARD)} sentences")
    print(f"\n--- Symptom Detection ---")
    print(f"TP={tp_detect} FP={fp_detect} FN={fn_detect}")
    print(f"Precision: {precision:.3f}")
    print(f"Recall:    {recall:.3f}")
    print(f"F1-score:  {f1:.3f}")
    print(f"\n--- Negation Classification (on correctly detected symptoms) ---")
    print(f"Accuracy: {negation_accuracy:.3f}  ({tp_negation}/{tp_negation + fn_negation})")

    return {"precision": precision, "recall": recall, "f1": f1,
            "negation_accuracy": negation_accuracy}


if __name__ == "__main__":
    evaluate()
