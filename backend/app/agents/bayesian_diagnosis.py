"""
Module 2.1 (continued) - Per-Malady Bayesian Inference Engine

Implements Naive Bayes inference: given a set of present/absent symptoms,
compute P(disease | symptoms) for each of our 8 diseases, ranked by
probability. This matches the proposal's stated theoretical framework
(Chapter 2.3): "Naive Bayes Assumption... all symptom and vital nodes are
assumed to be conditionally independent given the presence of the root
pathology."

PRIOR CHOICE (documented): we use a UNIFORM prior across the 8 diseases
(each disease starts at 1/8 probability before evidence), NOT the raw
sample proportions from our 200-vignette dataset. This is deliberate --
our dataset's disease mix (e.g. 47 Uncomplicated Malaria vs 10 Cerebral
Malaria) reflects how the vignette set was constructed for triage-label
balance, NOT real-world disease prevalence in a Nigerian PHC population.
Using it as a prior would silently bias the model toward whichever disease
happens to be over-represented in our sample. A uniform prior is the more
defensible, honest default until real epidemiological prevalence data is
available (noted as a future work item).

Implemented in pure Python (no pgmpy) so it runs anywhere without install
dependencies, and so every step is traceable for the auditable-decision-
trail requirement in the proposal.
"""
import json
import os
from math import log, exp

# Anchor to this file's location, not the process's working directory --
# this file is at backend/app/agents/bayesian_diagnosis.py, so the project
# root is 3 levels up. This fixes a real bug found during live testing:
# the old relative path only worked if the server happened to be started
# from the project root, but our setup instructions have you `cd app`
# first before running uvicorn, which broke it in the field.
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_DEFAULT_CPT_PATH = os.path.join(_PROJECT_ROOT, "data", "processed", "disease_symptom_cpt.json")


def load_cpt(path=None):
    path = path or _DEFAULT_CPT_PATH
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["cpt"]


def diagnose(present_symptoms: set[str], cpt: dict, all_symptoms: list[str]) -> list[tuple[str, float]]:
    """
    present_symptoms: set of symptom names confirmed present.
    Symptoms in all_symptoms NOT in present_symptoms are treated as absent
    (explicit closed-world assumption -- documented, since our intake is
    checkbox-based per the supervisor's UI design, absence of a checked box
    genuinely means "not reported present").

    Returns list of (disease, posterior_probability) sorted descending.
    """
    diseases = list(cpt.keys())
    log_scores = {}

    for d in diseases:
        # uniform prior
        log_p = log(1.0 / len(diseases))
        for s in all_symptoms:
            p_present = cpt[d][s]
            if s in present_symptoms:
                log_p += log(p_present)
            else:
                log_p += log(1 - p_present)
        log_scores[d] = log_p

    # normalize via log-sum-exp for numerical stability
    max_log = max(log_scores.values())
    exp_scores = {d: exp(lp - max_log) for d, lp in log_scores.items()}
    total = sum(exp_scores.values())
    posteriors = {d: v / total for d, v in exp_scores.items()}

    return sorted(posteriors.items(), key=lambda x: -x[1])


ALL_SYMPTOMS = [
    "Fever", "Vomiting", "Headache", "Altered consciousness", "Fatigue",
    "Difficulty breathing", "Convulsions", "Loss of appetite", "Stiff neck",
    "Chest indrawing", "Joint pain", "Abdominal pain", "Diarrhoea", "Rash",
]


if __name__ == "__main__":
    cpt = load_cpt()

    test_cases = [
        ("Classic meningitis presentation",
         {"Fever", "Headache", "Stiff neck", "Altered consciousness"}),

        ("Classic severe pneumonia",
         {"Fever", "Difficulty breathing", "Chest indrawing"}),

        ("Classic uncomplicated malaria",
         {"Fever", "Headache", "Joint pain"}),

        ("Classic typhoid",
         {"Fever", "Abdominal pain", "Diarrhoea", "Loss of appetite"}),
    ]

    for label, symptoms in test_cases:
        print(f"\n--- {label} ---")
        print(f"Symptoms: {symptoms}")
        results = diagnose(symptoms, cpt, ALL_SYMPTOMS)
        for disease, prob in results[:3]:
            print(f"  {disease}: {prob:.3f}")
