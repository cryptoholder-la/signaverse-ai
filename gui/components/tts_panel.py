import streamlit as st
from services.speech.kitten_tts_service import KittenTTSService

tts = KittenTTSService()

def render_tts_panel():
    st.header("🔊 Text-to-Speech (Kitten TTS)")

    text_input = st.text_area("Enter Gloss or Text")

    if st.button("Generate Audio"):
        path = tts.synthesize(text_input)
        audio_file = open(path, "rb")
        st.audio(audio_file.read(), format="audio/wav")