import streamlit as st

def render_playback(video_path, prediction):
    st.header("🎥 Sign Playback Viewer")

    st.video(video_path)
    st.write("Predicted Gloss:", prediction)