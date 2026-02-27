import streamlit as st
from components import *

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Go To",
    [
        "Model Comparison",
        "Hyperparameter Tuning",
        "Dataset Browser",
        "Expert Routing",
        "Confusion Matrix",
        "Playback Viewer",
        "Ray Cluster"
    ]
)

if page == "Model Comparison":
    model_compare.render_model_comparison()
elif page == "Hyperparameter Tuning":
    tuning_panel.render_tuning_panel()

elif page == "TTS":
    tts_panel.render_tts_panel()
    ...