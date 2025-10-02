# src/evaluator.py
import pandas as pd
import json
from datetime import datetime
def load_solution(sol_path="data/solution.json"):
    with open(sol_path) as f:
        sol = json.load(f)
    return sol

def compute_metrics(solution):
    sel = solution["selected"]
    total_cost = sum(p["cost"] for p in sel)
    n_pairings = len(sel)
    avg_duty = sum(p["duty_hours"] for p in sel) / max(1, n_pairings)
    flights_covered = sum(len(p["flights"]) for p in sel)
    return {
        "total_cost": total_cost,
        "pairings_selected": n_pairings,
        "avg_duty_hours": avg_duty,
        "flights_covered": flights_covered
    }

if __name__ == "__main__":
    sol = load_solution()
    metrics = compute_metrics(sol)
    print(metrics)
