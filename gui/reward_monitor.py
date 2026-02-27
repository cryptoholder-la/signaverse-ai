# gui/reward_monitor.py

import streamlit as st

def render_rewards(reward_engine):

    st.header("🏆 Agent Reward Monitor")

    scores = reward_engine.scores

    for agent, score in scores.items():
        st.write(f"{agent}: {score:.2f}")

    st.divider()
    st.info("This monitor displays the current reward scores for each agent based on their performance. Higher scores indicate better performance in completing tasks and achieving goals.")
    