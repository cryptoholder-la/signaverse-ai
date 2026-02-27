import streamlit as st
import os

def render_dataset_browser():
    st.header("📁 Dataset Browser")

    files = os.listdir("dataset/v1")

    selected = st.selectbox("Select Sample", files)

    if selected.endswith(".mp4"):
        st.video(f"dataset/v1/{selected}")
    else:
        st.text("Preview not supported.")

    st.download_button("Download Sample", f"dataset/v1/{selected}") 

    if st.button("Delete Sample"):
        os.remove(f"dataset/v1/{selected}")
        st.success("Sample Deleted.")   

    if st.button("Clear Dataset"):
        for file in os.listdir("dataset/v1"):
            os.remove(f"dataset/v1/{file}")
        st.success("Dataset Cleared.")  

    if st.button("Create New Version"):
        os.makedirs("dataset/v2", exist_ok=True)
        for file in os.listdir("dataset/v1"):
            os.rename(f"dataset/v1/{file}", f"dataset/v2/{file}")
        st.success("New Version Created.")

    if st.button("Delete Old Version"):
        os.makedirs("dataset/v1", exist_ok=True)
        for file in os.listdir("dataset/v2"):
            os.rename(f"dataset/v2/{file}", f"dataset/v1/{file}")
        st.success("Old Version Deleted.")




      #  landmark scatterplotting

      #  landmark heatmap

      #  frame heatmap

      #  frame scatterplot

      #  dataset versioning