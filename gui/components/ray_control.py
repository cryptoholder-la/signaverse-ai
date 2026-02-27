import streamlit as st
import ray

def render_ray_panel():
    st.header("☁ Ray Cluster Control")

    if st.button("Start Ray"):
        ray.init()
        st.success("Ray initialized.")

    resources = ray.available_resources()
    st.json(resources)