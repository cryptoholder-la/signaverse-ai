# gui/telemetry_panel.py

import streamlit as st

def render_telemetry(metrics):

    st.header("📡 Real-Time Telemetry")

    st.metric("Accuracy", metrics["accuracy"])
    st.metric("Latency (ms)", metrics["latency"])
    st.metric("Drift Score", metrics["drift_score"])

    st.divider()
    st.info("This telemetry panel provides real-time insights into the performance of the agents and the system. Accuracy indicates how well agents are completing tasks, latency measures response times, and drift score tracks changes in agent behavior over time.")
    