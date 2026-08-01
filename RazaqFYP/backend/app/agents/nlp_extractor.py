"""
Module 1.1-1.2 - Clinical Entity Extraction (rule/dictionary-based)

Extracts symptoms, negation status, duration, and severity qualifiers from
free-text clinical descriptions. Pure Python, no external ML dependencies --
chosen deliberately over BioMistral-7B (proposal's original spec) because:
  1. This machine has no GPU to run a 7B-parameter model at usable speed
  2. Our actual symptom vocabulary is closed/known (14 symptoms, see
     data/raw/iyawobench_v1.csv), so a dictionary approach achieves
     comparable accuracy at a fraction of the complexity
  3. The supervisor's own UI design references show checkbox-based symptom
     entry as the primary input path -- this extractor exists to handle
     free-text edge cases (e.g. a "notes" or "additional details" field),
     not as the system's main intake method

This is intentionally simple and auditable -- every extraction decision can
be traced to an explicit rule, which also satisfies the "auditable decision
trail" requirement from the proposal's significance section.
"""
import re
from dataclasses import dataclass, field
from typing import Optional


# Canonical symptom -> surface form synonyms (derived from real dataset vocabulary)
SYMPTOM_LEXICON = {
    "Fever": ["fever", "febrile", "high temperature", "hot to touch", "pyrexia"],
    "Vomiting": ["vomiting", "vomited", "throwing up", "emesis"],
    "Headache": ["headache", "head pain", "head ache"],
    "Altered consciousness": [
        "altered consciousness", "unconscious", "unresponsive", "confused",
        "confusion", "lethargic", "drowsy", "not alert", "reduced consciousness",
    ],
    "Fatigue": ["fatigue", "tiredness", "weakness", "weak", "malaise", "lethargy"],
    "Difficulty breathing": [
        "difficulty breathing", "shortness of breath", "breathless",
        "dyspnea", "dyspnoea", "labored breathing", "laboured breathing",
    ],
    "Convulsions": ["convulsions", "convulsing", "seizure", "seizures", "fits"],
    "Loss of appetite": ["loss of appetite", "poor appetite", "not eating", "anorexia"],
    "Stiff neck": ["stiff neck", "neck stiffness", "nuchal rigidity"],
    "Chest indrawing": ["chest indrawing", "chest in-drawing", "subcostal retraction"],
    "Joint pain": ["joint pain", "arthralgia", "joint ache", "aching joints"],
    "Abdominal pain": ["abdominal pain", "stomach pain", "stomach ache", "belly pain"],
    "Diarrhoea": ["diarrhoea", "diarrhea", "loose stool", "loose stools"],
    "Rash": ["rash", "skin rash", "spots on skin"],
}

NEGATION_CUES = [
    "no", "not", "denies", "denied", "without", "absent", "negative for",
    "no history of", "no signs of", "no evidence of", "ruled out", "free of",
]

# Words that mark severity/degree
SEVERITY_QUALIFIERS = {
    "mild": ["mild", "slight", "minor"],
    "moderate": ["moderate"],
    "severe": ["severe", "intense", "extreme", "worsening", "rapidly deteriorating",
               "profound", "marked"],
}

DURATION_PATTERN = re.compile(
    r"(?:for|since|over|lasting)?\s*"
    r"(\d+)\s*"
    r"(day|days|week|weeks|hour|hours|month|months)\b"
    r"(?:\s+ago)?",
    re.IGNORECASE,
)

NEGATION_WINDOW = 6  # max words between a negation cue and the symptom it negates

# Conjunctions that reset negation scope, same as punctuation (e.g. "denies
# headache BUT reports vomiting" -- "but" should stop "denies" from reaching
# "vomiting")
SCOPE_RESET_WORDS = [" but ", " however ", " although "]


@dataclass
class ExtractedSymptom:
    symptom: str
    negated: bool
    matched_text: str
    duration: Optional[str] = None
    severity: Optional[str] = None


def _find_negation(text: str, char_pos: int) -> bool:
    """
    Check if a negation cue appears within NEGATION_WINDOW words before the
    symptom, WITHOUT crossing a clause boundary (comma, period, semicolon).
    This prevents "no diarrhoea, altered consciousness noted" from
    incorrectly negating "altered consciousness".
    """
    # Find the start of the current clause (nearest boundary before char_pos)
    clause_start = 0
    for punct in [",", ".", ";"]:
        idx = text.rfind(punct, 0, char_pos)
        if idx > clause_start:
            clause_start = idx + 1
    for word in SCOPE_RESET_WORDS:
        idx = text.rfind(word, 0, char_pos)
        if idx > clause_start:
            clause_start = idx + len(word)

    clause_text = text[clause_start:char_pos].lower()
    clause_tokens = clause_text.split()
    preceding = " ".join(clause_tokens[-NEGATION_WINDOW:]) if clause_tokens else ""
    return any(cue in preceding for cue in NEGATION_CUES)


def _find_nearby_duration(text: str, match_start: int, match_end: int, span: int = 60) -> Optional[str]:
    """Look for a duration expression near the symptom mention."""
    window = text[max(0, match_start - span): match_end + span]
    m = DURATION_PATTERN.search(window)
    if m:
        return f"{m.group(1)} {m.group(2)}"
    return None


def _find_nearby_severity(text: str, match_start: int, match_end: int, span: int = 40) -> Optional[str]:
    """Look for a severity qualifier near the symptom mention."""
    window = text[max(0, match_start - span): match_end + span].lower()
    for level, words in SEVERITY_QUALIFIERS.items():
        if any(w in window for w in words):
            return level
    return None


def extract_entities(text: str) -> list[ExtractedSymptom]:
    """
    Main entry point. Takes free-text clinical description, returns a list
    of ExtractedSymptom objects -- one per symptom mention found.
    """
    results = []
    text_lower = text.lower()

    for canonical, synonyms in SYMPTOM_LEXICON.items():
        for syn in synonyms:
            for m in re.finditer(re.escape(syn.lower()), text_lower):
                start_char, end_char = m.start(), m.end()

                negated = _find_negation(text, start_char)
                duration = _find_nearby_duration(text, start_char, end_char)
                severity = _find_nearby_severity(text, start_char, end_char)

                results.append(ExtractedSymptom(
                    symptom=canonical,
                    negated=negated,
                    matched_text=text[start_char:end_char],
                    duration=duration,
                    severity=severity,
                ))
                break  # only take first synonym match per symptom per sentence pass

    return results


if __name__ == "__main__":
    test_cases = [
        "Patient presents with fever and vomiting for 3 days, no diarrhoea, "
        "altered consciousness noted on arrival.",

        "Caregiver reports mild headache and joint pain since 2 days ago. "
        "Denies chest indrawing or difficulty breathing.",

        "Child has severe convulsions and stiff neck, rapidly deteriorating "
        "over the past 6 hours.",

        "No fever, no vomiting. Patient reports only mild fatigue for 1 week.",
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"\n--- Test case {i} ---")
        print(f"Input: {case}")
        for ent in extract_entities(case):
            flag = "NEGATED" if ent.negated else "present"
            print(f"  [{flag}] {ent.symptom} (matched: '{ent.matched_text}', "
                  f"duration: {ent.duration}, severity: {ent.severity})")
