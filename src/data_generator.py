# src/data_generator.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def generate_airports(num_airports=6):
    # Simple airport codes like A0, A1...
    airports = [f"A{i}" for i in range(num_airports)]
    return airports

def random_time_slots(start_date="2025-10-01", num_flights=80, span_hours=24, seed=1):
    np.random.seed(seed)
    base = datetime.fromisoformat(start_date + "T00:00:00")
    times = [base + timedelta(hours=float(np.random.rand() * span_hours)) for _ in range(num_flights)]
    return times

def generate_flights(num_airports=6, num_flights=80, start_date="2025-10-01"):
    airports = generate_airports(num_airports)
    dep_times = random_time_slots(start_date, num_flights)
    rows = []
    for i in range(num_flights):
        orig = np.random.choice(airports)
        dest = np.random.choice([a for a in airports if a != orig])
        dep = dep_times[i]
        # flight duration between 0.5 - 3 hours
        dur = timedelta(minutes=int(30 + np.random.rand()*150))
        arr = dep + dur
        flight_id = f"F{i:04d}"
        aircraft = "A320"  # simplify single fleet
        rows.append({
            "flight_id": flight_id,
            "origin": orig,
            "dest": dest,
            "dep_time": dep.isoformat(),
            "arr_time": arr.isoformat(),
            "aircraft": aircraft
        })
    df = pd.DataFrame(rows).sort_values("dep_time").reset_index(drop=True)
    return df

def generate_crews(num_crews=20, bases=None):
    if bases is None:
        bases = ["A0"]  # default base
    rows = []
    for i in range(num_crews):
        crew_id = f"C{i:03d}"
        base = np.random.choice(bases)
        rows.append({
            "crew_id": crew_id,
            "base": base,
            "max_duty_hours": 10.0,   # example
            "hourly_cost": 80.0      # example cost per duty-hour
        })
    return pd.DataFrame(rows)

def save_example(output_dir="data", num_airports=6, num_flights=80, num_crews=20):
    os.makedirs(output_dir, exist_ok=True)
    flights = generate_flights(num_airports, num_flights)
    flights.to_csv(os.path.join(output_dir, "flights.csv"), index=False)
    crews = generate_crews(num_crews, bases=[f"A{i}" for i in range(num_airports)])
    crews.to_csv(os.path.join(output_dir, "crews.csv"), index=False)
    print("Saved flights.csv and crews.csv to", output_dir)
    return flights, crews

if __name__ == "__main__":
    save_example()
