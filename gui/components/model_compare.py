import streamlit as st
import mlflow
import plotly.express as px

def render_model_comparison():
    st.header("📊 Model Comparison")

    runs = mlflow.search_runs()

    if runs.empty:
        st.warning("No runs found.")
        return

    selected = st.multiselect(
        "Select Runs to Compare",
        runs["run_id"]
    )

    filtered = runs[runs["run_id"].isin(selected)]

    fig = px.line(
        filtered,
        x="start_time",
        y="metrics.loss",
        color="run_id",
        title="Loss Comparison"
    )

    st.plotly_chart(fig)