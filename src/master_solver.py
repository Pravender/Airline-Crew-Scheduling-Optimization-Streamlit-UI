# src/master_solver.py
import json
import pandas as pd
import math
import os

def solve_master_with_gurobi(pairings, flights):
    import gurobipy as gp
    from gurobipy import GRB
    m = gp.Model("crew_master")
    # mapping pairing id to flights covered
    p_ids = [p["pairing_id"] for p in pairings]
    x = m.addVars(p_ids, vtype=GRB.BINARY, name="x")
    # objective: minimize cost
    cost_map = {p["pairing_id"]: p["cost"] for p in pairings}
    m.setObjective(gp.quicksum(cost_map[p] * x[p] for p in p_ids), GRB.MINIMIZE)
    # cover each flight exactly once
    flight_ids = flights["flight_id"].tolist()
    for f in flight_ids:
        cols = [p["pairing_id"] for p in pairings if f in p["flights"]]
        if not cols:
            # no pairing covers this flight (shouldn't happen), create large penalty to force infeas
            m.addConstr(0 == 1, name=f"cover_{f}")  # infeasible
        else:
            m.addConstr(gp.quicksum(x[p] for p in cols) == 1, name=f"cover_{f}")
    m.params.OutputFlag = 1
    m.optimize()
    if m.Status == GRB.OPTIMAL or m.Status == GRB.TIME_LIMIT:
        chosen = [p for p in pairings if x[p["pairing_id"]].X > 0.5]
        return chosen, m.ObjVal
    else:
        raise RuntimeError("Gurobi failed; status " + str(m.Status))

def solve_master_with_pulp(pairings, flights):
    import pulp
    prob = pulp.LpProblem("crew_master", pulp.LpMinimize)
    p_ids = [p["pairing_id"] for p in pairings]
    x = pulp.LpVariable.dicts("x", p_ids, lowBound=0, upBound=1, cat='Binary')
    cost_map = {p["pairing_id"]: p["cost"] for p in pairings}
    prob += pulp.lpSum([cost_map[p] * x[p] for p in p_ids])
    flight_ids = flights["flight_id"].tolist()
    for f in flight_ids:
        cols = [p["pairing_id"] for p in pairings if f in p["flights"]]
        if not cols:
            prob += (0 == 1)  # infeasible
        else:
            prob += pulp.lpSum([x[p] for p in cols]) == 1
    prob.solve()
    status = pulp.LpStatus[prob.status]
    if status not in ("Optimal", "Integer Feasible"):
        print("Solver status:", status)
    chosen = [p for p in pairings if pulp.value(x[p["pairing_id"]]) > 0.5]
    obj = pulp.value(prob.objective)
    return chosen, obj

def solve_master(pairings, flights, solver="auto"):
    if solver == "gurobi":
        return solve_master_with_gurobi(pairings, flights)
    elif solver == "pulp":
        return solve_master_with_pulp(pairings, flights)
    else:
        # auto detect gurobi
        try:
            import gurobipy
            return solve_master_with_gurobi(pairings, flights)
        except Exception:
            return solve_master_with_pulp(pairings, flights)

if __name__ == "__main__":
    import json
    flights = pd.read_csv("data/flights.csv")
    with open("data/pairings.json") as f:
        pairings = json.load(f)
    chosen, obj = solve_master(pairings, flights, solver="auto")
    print("Selected pairings:", len(chosen), "obj:", obj)
    # save solution
    import os
    os.makedirs("data", exist_ok=True)
    with open("data/solution.json", "w") as f:
        json.dump({"selected": chosen, "obj": obj}, f, default=str, indent=2)
