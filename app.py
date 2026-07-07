# app.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

import ui
import api
import tools
import ai_engine
import storage
from legal_tools_advanced import legal_classifier, legal_search, rebuttal_generator, document_generator, entitlements_calculator, deadlines_tracker, slip_detector, case_analyzer, info_extractor
from legal_database import get_legal_database

st.set_page_config(
    page_title="Führer",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown(ui.CSS, unsafe_allow_html=True)

_saved = storage.load_settings()
_defaults = {
    "persona": None,
    "active_tool": None,
    "active_nav": "chat",
    "current_sid": None,
    "current_msgs": [],
    "docs_text": [],
    "preset_name": _saved.get("preset_name", list(ai_engine.PRESETS.keys())[0]),
    "api_key": _saved.get("api_key", ""),
    "custom_url": _saved.get("custom_url", ""),
    "custom_model": _saved.get("custom_model", ""),
    "custom_fmt": _saved.get("custom_fmt", "openai"),
    "pending_input": "",
    "show_panel": None,
    "selected_tool": None,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

corner_col = st.columns([8, 1])[1]
with corner_col:
    if st.button("⚙️", key="corner_settings"):
        st.session_state.show_panel = (
            None if st.session_state.show_panel == "settings_full" else "settings_full"
        )
        st.rerun()

st.markdown("<div class='app-title'>Führer</div>", unsafe_allow_html=True)
st.markdown("<p class='sub-text' style='text-align:center;margin-top:-10px;'>النظام القانوني الذكي للقانون العمالي السعودي</p>",
            unsafe_allow_html=True)

if st.session_state.show_panel == "settings_full":
    # (يمكن نقل هذا القسم إلى ui لاحقاً، لكنه موجود هنا كما في الأصل)
    st.markdown("<div class='section-title'>الإعدادات والاتصال</div>", unsafe_allow_html=True)
    tabs = st.tabs(["الاتصال بالخادم", "لوحة التحكم", "بيانات الجلسة"])
    with tabs[0]:
        new_preset = st.selectbox("النموذج", list(ai_engine.PRESETS.keys()),
            index=list(ai_engine.PRESETS.keys()).index(st.session_state.preset_name)
            if st.session_state.preset_name in ai_engine.PRESETS else 0)
        st.session_state.preset_name = new_preset
        if new_preset == "⚙️ مخصص":
            st.session_state.custom_url = st.text_input("رابط API", value=st.session_state.custom_url)
            st.session_state.custom_model = st.text_input("النموذج", value=st.session_state.custom_model)
            st.session_state.custom_fmt = st.selectbox("الصيغة", ["openai", "gemini", "anthropic", "huggingface"])
        st.session_state.api_key = st.text_input("مفتاح API", value=st.session_state.api_key, type="password")
        key_ok = bool(st.session_state.api_key.strip())
        preset_info = ai_engine.get_preset_info(new_preset)
        if preset_info.get("requires_key", True):
            st.markdown(f"""<div class='alert {"ok" if key_ok else "danger"}'>
                {'✅ مفتاح API مدخَل' if key_ok else '❌ لم يتم إدخال مفتاح API'}</div>""", unsafe_allow_html=True)
        else:
            st.markdown("<div class='alert info'>ℹ️ هذا النموذج لا يتطلب مفتاح API</div>", unsafe_allow_html=True)
        if st.button("حفظ إعدادات الاتصال"):
            storage.save_settings({
                "preset_name": st.session_state.preset_name,
                "custom_url": st.session_state.custom_url,
                "custom_model": st.session_state.custom_model,
                "custom_fmt": st.session_state.custom_fmt,
            })
            st.success("✅ تم حفظ الإعدادات")
    with tabs[1]:
        sessions = storage.list_sessions()
        cases = storage.list_cases()
        st.markdown(f"""<div class='stat-grid'>
            <div class='stat-box'><div class='v'>{len(sessions)}</div><div class='l'>الجلسات</div></div>
            <div class='stat-box'><div class='v'>{len(cases)}</div><div class='l'>القضايا</div></div>
            <div class='stat-box'><div class='v'>{len(st.session_state.current_msgs)}</div><div class='l'>رسائل الجلسة</div></div>
            <div class='stat-box'><div class='v'>{len(st.session_state.docs_text)}</div><div class='l'>مستندات</div></div>
        </div>""", unsafe_allow_html=True)
    with tabs[2]:
        if st.button("🗑️ مسح جميع الجلسات"):
            if storage.clear_all_sessions():
                st.session_state.current_sid = None
                st.session_state.current_msgs = []
                st.success("✅ تم مسح جميع الجلسات")
                st.rerun()
    st.markdown("---")

if st.session_state.persona is None:
    ui.render_persona_selection()
else:
    ui.render_nav_bar()
    ui.render_persona_badge()
    nav = st.session_state.active_nav

    if nav == "chat":
        ui.render_chat()
    elif nav == "tools":
        ui.render_tools()
    elif nav == "sessions":
        ui.render_sessions()
    elif nav == "analysis":
        ui.render_analysis()
    elif nav == "cases":
        ui.render_cases()
    elif nav == "switch":
        st.session_state.persona = None
        st.session_state.active_nav = "chat"
        st.session_state.current_sid = None
        st.session_state.current_msgs = []
        st.rerun()