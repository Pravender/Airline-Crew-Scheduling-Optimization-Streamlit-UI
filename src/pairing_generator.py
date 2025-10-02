# src/pairing_generator.py
import pandas as pd
from datetime import datetime, timedelta
import itertools
import uuid

MIN_TURN_MINUTES = 45  # minimum connection time between flights
MAX_DUTY_HOURS = 10    # maximum duty length for a pairing (can be overridden)
HOTEL_COST = 200       # cost for overnight away

def parse_time(t):
    return datetime.fromisoformat(t)

def build_flight_nodes(flights_df):
    # returns flights sorted by dep_time with parsed datetimes
    df = flights_df.copy()
    df["dep_dt"] = df["dep_time"].apply(parse_time)
    df["arr_dt"] = df["arr_time"].apply(parse_time)
    return df.sort_values("dep_dt").reset_index(drop=True)

def feasible_follow(f1, f2, min_turn=MIN_TURN_MINUTES):
    # True if flight f2 can be served after f1 by same crew
    # requires arrival of f1 + min_turn <= departure of f2 and same aircraft type (simple)
    return f1["arr_dt"] + timedelta(minutes=min_turn) <= f2["dep_dt"] and f1["dest"] == f2["origin"]

def generate_pairings(flights_df, crews_df,
                      max_duty_hours=MAX_DUTY_HOURS,
                      min_turn_minutes=MIN_TURN_MINUTES,
                      max_pairing_len=6,
                      require_return_to_base=False):
    flights = build_flight_nodes(flights_df)
    flights_list = flights.to_dict("records")
    index_by_id = {f["flight_id"]: f for f in flights_list}

    pairings = []

    # For each flight as possible start, try to build lines via DFS (bounded)
    for start in flights_list:
        stack = [([start], start["dep_dt"], start["arr_dt"])]  # (flight_seq, start_time, last_arrival)
        while stack:
            seq, start_time, last_arrival = stack.pop()
            # compute duty duration
            duty_hours = (last_arrival - start_time).total_seconds() / 3600.0
            # compute cost: use average hourly crew cost (simple)
            # We'll take median hourly cost from crews
            hourly_cost = crews_df["hourly_cost"].median() if not crews_df.empty else 80.0
            cost = duty_hours * hourly_cost
            # hotel if overnight (dates differ)
            if seq[0]["dep_dt"].date() != seq[-1]["arr_dt"].date():
                cost += HOTEL_COST
            pairing_id = "P_" + uuid.uuid4().hex[:8]
            pairings.append({
                "pairing_id": pairing_id,
                "flights": [f["flight_id"] for f in seq],
                "start": seq[0]["dep_dt"],
                "end": seq[-1]["arr_dt"],
                "duty_hours": duty_hours,
                "cost": cost
            })
            # If pairing too long in time or legs, stop extending
            if duty_hours >= max_duty_hours or len(seq) >= max_pairing_len:
                continue
            # try to extend
            last = seq[-1]
            for cand in flights_list:
                if cand["dep_dt"] <= last["dep_dt"]:
                    continue
                if feasible_follow(last, cand, min_turn=min_turn_minutes):
                    new_last_arr = cand["arr_dt"]
                    new_duty_hours = (new_last_arr - start_time).total_seconds() / 3600.0
                    if new_duty_hours <= max_duty_hours:
                        new_seq = seq + [cand]
                        stack.append((new_seq, start_time, new_last_arr))
    # remove dominated duplicates by flights set (keep cheapest)
    best = {}
    for p in pairings:
        key = tuple(p["flights"])
        if key not in best or p["cost"] < best[key]["cost"]:
            best[key] = p
    result = list(best.values())
    # sort by start time
    result.sort(key=lambda x: x["start"])
    return result

if __name__ == "__main__":
    import os
    flights = pd.read_csv("data/flights.csv")
    crews = pd.read_csv("data/crews.csv")
    pairings = generate_pairings(flights, crews, max_pairing_len=5)
    import json
    os.makedirs("data", exist_ok=True)
    with open("data/pairings.json", "w") as f:
        json.dump(pairings, f, default=str, indent=2)
    print("Generated", len(pairings), "pairings -> data/pairings.json")
