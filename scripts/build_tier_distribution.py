"""
Module 2.3 (prep) - Builds P(triage_tier | disease) from real vignette
outcomes, used by the hybrid engine to convert a Bayesian diagnosis into a
suggested triage tier before the rule-floor safety net is applied.
"""
import csv
import json
from collections import defaultdict, Counter

TIERS = ["Blue", "Green", "Yellow", "Orange", "Red"]


def main():
    with open("data/processed/iyawobench_train_5level.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    counts = defaultdict(Counter)
    for r in rows:
        counts[r["disease"]][r["triage_5level"]] += 1

    dist = {}
    for disease, counter in counts.items():
        total = sum(counter.values())
        # Laplace smoothing across all 5 tiers so an unseen tier isn't impossible
        dist[disease] = {
            tier: round((counter.get(tier, 0) + 1) / (total + len(TIERS)), 4)
            for tier in TIERS
        }

    with open("data/processed/disease_tier_distribution.json", "w", encoding="utf-8") as f:
        json.dump(dist, f, indent=2)

    for d, td in dist.items():
        print(d, td)


if __name__ == "__main__":
    main()
