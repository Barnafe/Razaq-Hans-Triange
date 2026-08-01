"""
Module 8.3 - Latency benchmarking against the proposal's stated
non-functional requirement (Chapter 4.2): "End-to-end system response
times must remain below 2.5 seconds."

Measures the full hybrid pipeline (Bayesian diagnosis + rule engine +
triage agent formatting) end-to-end, run many times to get a stable
distribution rather than a single noisy measurement.
"""
import sys
import os
import time
import statistics

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app", "agents"))
from triage_agent import triage_agent
from rule_engine import PatientInput

N_RUNS = 500

test_patient = PatientInput(
    symptoms={"Fever", "Headache", "Stiff neck", "Altered consciousness"},
    temperature=39.5, heart_rate=130, respiratory_rate=28,
    systolic=95, diastolic=60, spo2=92, age_years=8,
)


def main():
    latencies_ms = []
    for _ in range(N_RUNS):
        start = time.perf_counter()
        triage_agent(test_patient)
        elapsed_ms = (time.perf_counter() - start) * 1000
        latencies_ms.append(elapsed_ms)

    latencies_ms.sort()
    mean = statistics.mean(latencies_ms)
    median = statistics.median(latencies_ms)
    p95 = latencies_ms[int(len(latencies_ms) * 0.95)]
    p99 = latencies_ms[int(len(latencies_ms) * 0.99)]
    worst = max(latencies_ms)

    print(f"Runs: {N_RUNS}")
    print(f"Mean latency:   {mean:.3f} ms")
    print(f"Median latency: {median:.3f} ms")
    print(f"P95 latency:    {p95:.3f} ms")
    print(f"P99 latency:    {p99:.3f} ms")
    print(f"Worst latency:  {worst:.3f} ms")
    print(f"\nProposal requirement: < 2500 ms end-to-end")
    print(f"Result: {'PASS' if p99 < 2500 else 'FAIL'} (P99 = {p99:.3f} ms)")
    print(f"\nNOTE: this measures the diagnostic/triage CORE only (pure Python,")
    print(f"no network). Real end-to-end latency in production would also")
    print(f"include HTTP overhead, database writes, and network round-trip --")
    print(f"this number is a lower bound / best case, not the full picture.")


if __name__ == "__main__":
    main()
