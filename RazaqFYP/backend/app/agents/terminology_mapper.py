"""
Module 1.3 - Standard Terminology Mapping

Maps our 14-symptom canonical vocabulary to SNOMED CT concept IDs, so
extracted entities carry standardized codes (satisfies proposal Objective 1:
"map symptoms to standardized medical terminologies").

Provenance / confidence notes:
  - Codes marked VERIFIED were cross-checked against SNOMED International's
    own published implementation guide (docs.snomed.org) and/or NCBO
    BioPortal during this session.
  - Codes marked "recall, recommend re-verifying" are commonly-cited codes
    from general medical informatics knowledge but were NOT independently
    re-confirmed against a live SNOMED browser in this session. Before
    citing these in your final report, cross-check them at
    https://browser.ihtsdotools.org/ (free SNOMED CT browser) -- takes
    seconds per code and closes any doubt for your defense.
"""

SNOMED_MAPPING = {
    "Fever":                   {"code": "386661006", "term": "Fever (finding)", "status": "VERIFIED"},
    "Vomiting":                {"code": "249497008", "term": "Vomiting symptom (finding)", "status": "VERIFIED"},
    "Headache":                {"code": "25064002",  "term": "Headache (finding)", "status": "VERIFIED"},
    "Altered consciousness":   {"code": "3006004",   "term": "Disturbance of consciousness (finding)", "status": "VERIFIED"},
    "Fatigue":                 {"code": "84229001",  "term": "Fatigue (finding)", "status": "VERIFIED"},
    "Difficulty breathing":    {"code": "267036007", "term": "Dyspnea (finding)", "status": "VERIFIED"},
    "Convulsions":             {"code": "91175000",  "term": "Seizure (finding)", "status": "VERIFIED"},
    "Loss of appetite":        {"code": "79890006",  "term": "Loss of appetite (finding)", "status": "VERIFIED"},
    "Stiff neck":              {"code": "41415008",  "term": "Neck stiffness (finding)", "status": "RECALL - reverify"},
    "Chest indrawing":         {"code": "248567008", "term": "Indrawing of ribs during respiration (finding)", "status": "VERIFIED"},
    "Joint pain":              {"code": "57676002",  "term": "Joint pain (finding)", "status": "VERIFIED"},
    "Abdominal pain":          {"code": "21522001",  "term": "Abdominal pain (finding)", "status": "RECALL - reverify"},
    "Diarrhoea":                {"code": "62315008",  "term": "Diarrhea (finding)", "status": "VERIFIED"},
    "Rash":                    {"code": "271807003", "term": "Eruption of skin (disorder)", "status": "VERIFIED"},
}


def map_to_snomed(canonical_symptom: str) -> dict:
    """Look up SNOMED CT code info for a canonical symptom name."""
    entry = SNOMED_MAPPING.get(canonical_symptom)
    if entry is None:
        return {"code": None, "term": None, "status": "NOT_MAPPED"}
    return entry


if __name__ == "__main__":
    from nlp_extractor import extract_entities

    text = ("Child has severe convulsions and stiff neck, rapidly "
            "deteriorating over the past 6 hours.")
    print(f"Input: {text}\n")
    for ent in extract_entities(text):
        snomed = map_to_snomed(ent.symptom)
        flag = "NEGATED" if ent.negated else "present"
        print(f"[{flag}] {ent.symptom} -> SNOMED {snomed['code']} "
              f"({snomed['term']}) [{snomed['status']}]")
