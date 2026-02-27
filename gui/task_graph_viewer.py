# gui/task_graph_viewer.py

import streamlit as st

def render_task_graph(graph):

    st.header("🧠 Task Dependency Graph")

    for node in graph.nodes:
        st.write(f"{node.name} → Depends on: {node.dependencies}")
    st.info("This graph shows the dependencies between tasks. Each task may depend on the completion of other tasks before it can be executed.")

    st.divider()