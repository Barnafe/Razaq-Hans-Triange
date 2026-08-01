"""
Module 6.2/6.3 - Real HL7/FHIR round-trip test against the public HAPI FHIR
sandbox (https://hapi.fhir.org/baseR4).

Run this LOCALLY (needs internet, which the build sandbox doesn't have):
    cd RazaqFYP
    venv activated, requests installed (see docs/SETUP.md)
    python scripts/test_fhir_roundtrip.py

This submits a real Patient + Observation bundle representing a triage
decision, then reads it back, proving actual interoperability -- not just
correctly-shaped JSON sitting unused locally.

REMINDER: this hits a shared PUBLIC test server. Don't run this
repeatedly with real patient data (there isn't any here -- everything is
synthetic/pseudonymized), and don't rely on this server being up during
your actual defense -- see fhir_integration.py's module docstring.
"""
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend", "app", "agents"))

import requests
from fhir_integration import build_patient_resource, build_triage_observation, FHIR_BASE_URL


def submit_and_verify():
    headers = {"Content-Type": "application/fhir+json"}

    # Step 1: submit the Patient resource
    patient = build_patient_resource(pseudonym="PT-TEST-ROUNDTRIP", age_years=8, sex="F")
    resp = requests.post(f"{FHIR_BASE_URL}/Patient", json=patient, headers=headers, timeout=15)
    print(f"POST Patient -> HTTP {resp.status_code}")
    if resp.status_code not in (200, 201):
        print(f"FAILED: {resp.text[:500]}")
        return False

    created_patient = resp.json()
    patient_id = created_patient["id"]
    print(f"Created Patient with server-assigned id: {patient_id}")

    # Step 2: submit the Observation, referencing the real server-assigned patient id
    observation = build_triage_observation(
        patient_reference=f"Patient/{patient_id}",
        tier="Red",
        rationale="Test round-trip from HANS-Triage local development.",
        differential_diagnosis=[{"disease": "Bacterial Meningitis", "probability": 0.837}],
    )
    resp2 = requests.post(f"{FHIR_BASE_URL}/Observation", json=observation, headers=headers, timeout=15)
    print(f"POST Observation -> HTTP {resp2.status_code}")
    if resp2.status_code not in (200, 201):
        print(f"FAILED: {resp2.text[:500]}")
        return False

    created_obs = resp2.json()
    obs_id = created_obs["id"]
    print(f"Created Observation with server-assigned id: {obs_id}")

    # Step 3: read it back, prove round-trip
    resp3 = requests.get(f"{FHIR_BASE_URL}/Observation/{obs_id}", timeout=15)
    print(f"GET Observation/{obs_id} -> HTTP {resp3.status_code}")
    if resp3.status_code != 200:
        print(f"FAILED to read back: {resp3.text[:500]}")
        return False

    fetched = resp3.json()
    print("\nRead back from server:")
    print(json.dumps(fetched, indent=2)[:800])

    matches = fetched.get("valueString") == "Red"
    print(f"\nRound-trip verification (tier value matches what we sent): {matches}")
    return matches


if __name__ == "__main__":
    try:
        success = submit_and_verify()
        print(f"\n{'PASS' if success else 'FAIL'}: FHIR round-trip test")
    except requests.exceptions.RequestException as e:
        print(f"Network error -- the public HAPI FHIR sandbox may be down "
              f"(this happens, it's a shared public server -- see caveat in "
              f"fhir_integration.py). Error: {e}")
