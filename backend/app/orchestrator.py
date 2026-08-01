"""
Module 3.2/3.3 - Agent Orchestrator

Coordinates the individual agents (Symptom, Diagnosis+Triage, Interaction,
Chat) into one pipeline, with ERROR ISOLATION: if one agent fails, the
others still run and the orchestrator returns a partial result with the
failure clearly flagged, rather than crashing the whole request. This
directly implements the proposal's Chapter 3.8 requirement: "a database
issue in one module does not cause a total collapse of core triage
routing."

Agent boundaries (per proposal Chapter 4.5), and their current status:
  - Symptom Agent      -> agents/nlp_extractor.py            [IMPLEMENTED]
  - Diagnosis Agent     -> agents/bayesian_diagnosis.py        [IMPLEMENTED]
  - Triage Agent        -> agents/triage_agent.py              [IMPLEMENTED]
  - Interaction Agent   -> agents/interaction_agent.py         [STUB -- see note below]
  - Chat Agent          -> agents/chat_agent.py                [STUB -- see note below]
  - Vision Agent        -> Phase 5, not yet built

STUB NOTE: Interaction Agent and Chat Agent are implemented as clearly
labeled stubs, not full implementations, for honest reasons:
  - Interaction Agent needs a real drug-allergy/interaction reference
    dataset, which our vignette data does not include (no medication
    fields). A production version would need a licensed interaction
    database (e.g. from a drug reference API) -- out of scope to fake here.
  - Chat Agent is designed to call the Claude API, which requires an API
    key you'd hold locally -- it can't be exercised in this build
    environment (no internet/key here). The interface is built and ready;
    you'll supply your own key when running locally (see SETUP.md).
Both stubs return clearly marked placeholder output rather than silently
pretending to be real, so nobody mistakes stub output for a real result.
"""
from dataclasses import dataclass, field
from typing import Any

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))

from rule_engine import PatientInput
from triage_agent import triage_agent
from interaction_agent import interaction_agent
from chat_agent import chat_agent


@dataclass
class OrchestratorResult:
    triage_output: dict | None = None
    interaction_output: dict | None = None
    chat_output: dict | None = None
    errors: dict[str, str] = field(default_factory=dict)

    @property
    def had_partial_failure(self) -> bool:
        return len(self.errors) > 0


def run_pipeline(patient: PatientInput, chat_message: str | None = None) -> OrchestratorResult:
    """
    Runs all agents. Each is wrapped individually so a failure in one
    (simulated below in tests) does not prevent the others from running --
    this is the isolation property the proposal requires.
    """
    result = OrchestratorResult()

    # --- Triage Agent (core, must succeed for the response to be useful) ---
    try:
        result.triage_output = triage_agent(patient)
    except Exception as e:
        result.errors["triage_agent"] = f"{type(e).__name__}: {e}"

    # --- Interaction Agent (stub; isolated so its failure never blocks triage) ---
    try:
        result.interaction_output = interaction_agent(patient)
    except Exception as e:
        result.errors["interaction_agent"] = f"{type(e).__name__}: {e}"

    # --- Chat Agent (stub; isolated so its failure never blocks triage) ---
    try:
        result.chat_output = chat_agent(chat_message)
    except Exception as e:
        result.errors["chat_agent"] = f"{type(e).__name__}: {e}"

    return result


if __name__ == "__main__":
    import json

    patient = PatientInput(
        symptoms={"Fever", "Headache", "Stiff neck", "Altered consciousness"},
        temperature=39.5, heart_rate=130, respiratory_rate=28,
        systolic=95, diastolic=60, spo2=92, age_years=8,
    )

    print("=== Normal run (all agents healthy) ===")
    result = run_pipeline(patient, chat_message="My child has a stiff neck and fever")
    print(f"Triage tier: {result.triage_output['urgency_classification']['tier']}")
    print(f"Interaction output: {result.interaction_output}")
    print(f"Chat output: {result.chat_output}")
    print(f"Errors: {result.errors}")

    print("\n=== Isolation test: simulate a broken Interaction Agent ===")

    def broken_interaction_agent(patient, active_medications=None, known_allergies=None):
        raise RuntimeError("Simulated database connection failure")

    # Direct module-level reassignment (this block is at module scope, not
    # inside a function, so this correctly rebinds the name that run_pipeline
    # looks up as a global at call time)
    original = interaction_agent
    interaction_agent = broken_interaction_agent

    result2 = run_pipeline(patient, chat_message="test")
    print(f"Triage tier STILL computed: {result2.triage_output['urgency_classification']['tier']}")
    print(f"Interaction agent failed as expected: {result2.errors.get('interaction_agent')}")
    print(f"had_partial_failure: {result2.had_partial_failure}")
    print("\n^ This proves the isolation property: Interaction Agent crashing")
    print("  did NOT prevent the Triage Agent from completing successfully.")

    interaction_agent = original
