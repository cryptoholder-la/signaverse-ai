import streamlit as st
import plotly.express as px
import numpy as np

def render_expert_viz(weights):
    st.header("🧠 Expert Routing")

    experts = [f"Expert {i}" for i in range(len(weights))]

    fig = px.bar(
        x=experts,
        y=weights,
        title="Expert Activation Weights"
    )

    st.plotly_chart(fig)