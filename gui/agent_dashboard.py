import streamlit as st

st.title("Autonomous Agent Control Center")

st.sidebar.header("Agents")

selected = st.selectbox(
    "Select Agent",
    ["MetaAgent", "DataAgent", "TrainingAgent"]
)

st.write("Reward Score:", 125.4)
st.write("Confidence Level:", 0.87)
st.write("Recent Tasks:")
st.table([
    {"task": "retrain_model", "status": "completed"},
    {"task": "analyze_confusion", "status": "completed"}
])