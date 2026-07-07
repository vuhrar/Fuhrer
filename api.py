# api.py
import streamlit as st
import ai_engine

def ai_call(prompt, history, system):
    return ai_engine.call_ai(
        prompt, history, system,
        preset_name=st.session_state.preset_name,
        api_key=st.session_state.api_key,
        custom_url=st.session_state.custom_url,
        custom_model=st.session_state.custom_model,
        custom_fmt=st.session_state.custom_fmt,
    )