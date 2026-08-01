"""
Module 2.4 - Triage Agent: formats the hybrid engine's raw output into the
structured payload specified in the proposal (Chapter 4.7 Output Design):
  - 5-level color-coded urgency classification with explainable rationale
  - Probability-ranked differential diagnosis list
  - Immediate red-flag alerts
  - Suggested care setting pathway
"""
from hybrid_engine import run_hybrid_triage
from rule_engine import PatientInput

TIER_META = {
    "Red":    {"label": "Immediate",  "max_wait": "0 minutes",   "pathway": "Emergency Resus"},
    "Orange": {"label": "Very Urgent", "max_wait": "10 minutes",  "pathway": "Emergency Resus"},
    "Yellow": {"label": "Urgent",     "max_wait": "60 minutes",  "pathway": "Urgent Care"},
    "Green":  {"label": "Standard",   "max_wait": "120 minutes", "pathway": "Urgent Care"},
    "Blue":   {"label": "Non-Urgent", "max_wait": "240 minutes", "pathway": "Outpatient Home Care"},
}

# Red-flag alert labels for specific danger-sign combinations
RED_FLAG_RULES = [
    (lambda p: "Altered consciousness" in p.symptoms or "Convulsions" in p.symptoms,
     "NEUROLOGICAL DANGER SIGN"),
    (lambda p: p.spo2 < 90, "HYPOXIA ALERT"),
    (lambda p: p.systolic < 90, "SHOCK ALERT"),
    (lambda p: "Stiff neck" in p.symptoms, "POSSIBLE MENINGITIS"),
]


def triage_agent(patient: PatientInput) -> dict:
    result = run_hybrid_triage(patient)
    tier = result["final_tier"]
    meta = TIER_META[tier]

    red_flags = [label for check, label in RED_FLAG_RULES if check(patient)]

    return {
        "urgency_classification": {
            "tier": tier,
            "label": meta["label"],
            "max_recommended_wait": meta["max_wait"],
            "rationale": result["decision_trail"],
        },
        "differential_diagnosis": [
            {"disease": d, "probability": round(p, 3)}
            for d, p in result["differential_diagnosis"]
        ],
        "red_flag_alerts": red_flags,
        "suggested_care_pathway": meta["pathway"],
    }


if __name__ == "__main__":
    import json

    patient = PatientInput(
        symptoms={"Fever", "Headache", "Stiff neck", "Altered consciousness"},
        temperature=39.5, heart_rate=130, respiratory_rate=28,
        systolic=95, diastolic=60, spo2=92, age_years=8,
    )
    output = triage_agent(patient)
    print(json.dumps(output, indent=2))
