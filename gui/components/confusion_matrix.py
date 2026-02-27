import streamlit as st
import plotly.figure_factory as ff
import numpy as np

def render_confusion_matrix(cm, labels):
    fig = ff.create_annotated_heatmap(
        z=cm,
        x=labels,
        y=labels
    )
    st.plotly_chart(fig)