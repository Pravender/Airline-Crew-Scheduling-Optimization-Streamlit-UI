# streamlit_app/app.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


import streamlit as st
import pandas as pd
import json
from src.pairing_generator import generate_pairings
from src.master_solver import solve_master
from src.evaluator import compute_metrics
import plotly.express as px
from datetime import datetime

st.set_page_config(layout="wide", page_title="Airline Crew Scheduling")

st.title("✈️ Airline Crew Scheduling — Prototype")

st.sidebar.header("Data")
uploaded_flights = st.sidebar.file_uploader("Upload flights.csv", type=["csv"])
uploaded_crews = st.sidebar.file_uploader("Upload crews.csv", type=["csv"])
if st.sidebar.button("Generate sample data"):
    import src.data_generator as dg
    dg.save_example()
    st.sidebar.success("Generated data in /data")

st.sidebar.header("Pairing params")
max_pair_len = st.sidebar.slider("Max legs in pairing", 2, 8, 4)
max_duty = st.sidebar.slider("Max duty hours", 6, 14, 10)
min_turn = st.sidebar.slider("Min turn (min)", 20, 120, 45)

st.header("Run")
if st.button("Run full pipeline (generate pairings -> solve)"):
    if uploaded_flights:
        flights = pd.read_csv(uploaded_flights)
    else:
        flights = pd.read_csv("data/flights.csv")
    if uploaded_crews:
        crews = pd.read_csv(uploaded_crews)
    else:
        crews = pd.read_csv("data/crews.csv")
    st.info(f"Flights: {len(flights)}, Crews: {len(crews)}")
    with st.spinner("Generating pairings..."):
        pairings = generate_pairings(flights, crews,
                                     max_duty_hours=max_duty,
                                     min_turn_minutes=min_turn,
                                     max_pairing_len=max_pair_len)
    st.success(f"Generated {len(pairings)} pairings")
    if len(pairings) < 1:
        st.error("No pairings generated. Loosen params.")
    else:
        with st.spinner("Solving master..."):
            chosen, obj = solve_master(pairings, flights, solver="auto")
        st.success(f"Solved. Objective = {obj:.2f}, chosen {len(chosen)} pairings")
        solution = {"selected": chosen, "obj": obj}
        metrics = compute_metrics(solution)
        st.subheader("Key metrics")
        st.json(metrics)

        # Build roster dataframe for Gantt chart
        rows = []
        for pid, p in enumerate(chosen):
            crew_label = f"Pairing {pid}"
            for fid in p["flights"]:
                # retrieve flight info
                flight_row = flights[flights.flight_id == fid].iloc[0]
                rows.append({
                    "pairing": crew_label,
                    "flight": fid,
                    "origin": flight_row["origin"],
                    "dest": flight_row["dest"],
                    "start": pd.to_datetime(flight_row["dep_time"]),
                    "end": pd.to_datetime(flight_row["arr_time"])
                })
        df_roster = pd.DataFrame(rows)
        if not df_roster.empty:
            fig = px.timeline(df_roster, x_start="start", x_end="end", y="pairing", color="flight",
                              hover_data=["origin","dest"])
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No roster to display.")
