"""
Interaction Agent (STUB) - Chapter 4.5 of proposal: "Evaluates active
prescriptions against known patient allergies and drug-drug contraindication
tables."

HONEST STATUS: this is a stub, not a production implementation. Our
vignette dataset has no medication/allergy fields, and a real interaction
table needs a licensed clinical drug-reference source. What's implemented
here is a small, clearly-labeled DEMONSTRATION table (a handful of common
antimalarial/antibiotic interactions relevant to our 8 diseases) so the
agent boundary and interface are real and testable -- but it is NOT
clinically comprehensive and must not be presented as production-ready.

If pursued further, next step is integrating a real source (e.g. an
openFDA drug interaction dataset) -- noted as future work.
"""
from rule_engine import PatientInput

# DEMONSTRATION interaction table -- NOT clinically comprehensive.
# Format: (drug_a, drug_b) -> warning message
DEMO_INTERACTIONS = {
    ("Artemether-Lumefantrine", "Halofantrine"):
        "Increased risk of QT prolongation -- avoid concurrent use.",
    ("Chloroquine", "Ampicillin"):
        "Chloroquine may reduce absorption of oral ampicillin.",
    ("Ceftriaxone", "Calcium-containing IV fluids"):
        "Risk of precipitation in neonates -- avoid concurrent IV administration.",
}

DEMO_ALLERGY_CLASSES = {
    "Penicillin allergy": ["Ampicillin", "Amoxicillin", "Ceftriaxone (cross-reactivity risk)"],
}


def interaction_agent(patient: PatientInput, active_medications: list[str] | None = None,
                       known_allergies: list[str] | None = None) -> dict:
    """
    Returns a dict of flagged interactions/allergy conflicts. Since our
    PatientInput doesn't currently carry medication/allergy fields (not in
    the source dataset), these are accepted as optional extra arguments so
    the interface is ready to wire up once that data exists.
    """
    active_medications = active_medications or []
    known_allergies = known_allergies or []

    flagged_interactions = []
    for (drug_a, drug_b), warning in DEMO_INTERACTIONS.items():
        if drug_a in active_medications and drug_b in active_medications:
            flagged_interactions.append({"drugs": [drug_a, drug_b], "warning": warning})

    flagged_allergies = []
    for allergy in known_allergies:
        conflicting = DEMO_ALLERGY_CLASSES.get(allergy, [])
        for med in active_medications:
            if med in conflicting:
                flagged_allergies.append({"allergy": allergy, "conflicting_medication": med})

    return {
        "status": "STUB -- demonstration data only, not clinically comprehensive",
        "flagged_interactions": flagged_interactions,
        "flagged_allergies": flagged_allergies,
    }
