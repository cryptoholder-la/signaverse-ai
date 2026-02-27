# gui/marketplace_view.py

import streamlit as st

def render_marketplace(marketplace):

    st.header("🛒 Task Marketplace")

    active_tasks = marketplace.get_active_tasks()

    for task in active_tasks:
        st.subheader(f"Task: {task['task']}")
        bids = task.get("bids", [])

        for bid in bids:
            st.write(f"Agent: {bid['agent']} | Confidence: {bid['confidence']:.2f}")

        if bids:
            winner = max(bids, key=lambda x: x["confidence"])
            st.success(f"Winning Agent: {winner['agent']}")
        else:
            st.warning("No bids yet for this task.")

        st.divider()

    st.info("Agents can place bids on tasks to compete for execution. The agent with the highest confidence wins the task.")

    st.divider()