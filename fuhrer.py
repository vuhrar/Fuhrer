# app.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

import ai_engine
import analysis_engine
import legal_tools
import file_processing
import storage
from legal_tools_advanced import (
    legal_classifier, legal_search, rebuttal_generator,
    document_generator, entitlements_calculator,
    deadlines_tracker, slip_detector, case_analyzer, info_extractor
)
from legal_database import get_legal_database

# استيراد وحداتنا المقسمة
import ui
import api
import tools

st.set_page_config(
    page_title="Führer — النظام القانوني الذكي",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# تطبيق CSS
st.markdown(ui.CSS, unsafe_allow_html=True)

# تهيئة الحالة
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
    "connection_status": "unknown", # unknown, connected, failed
    "connection_msg": "",
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# مؤشر الحالة وزر الإعدادات
status_col, corner_col = st.columns([8, 1])
with status_col:
    conn_status = st.session_state.get("connection_status", "unknown")
    if conn_status == "connected":
        st.markdown("<span style='color:#4ade80;font-size:0.8rem;float:left;margin-top:10px;'>🟢 متصل</span>", unsafe_allow_html=True)
    elif conn_status == "failed":
        st.markdown("<span style='color:#f87171;font-size:0.8rem;float:left;margin-top:10px;'>🔴 خطأ اتصال</span>", unsafe_allow_html=True)
with corner_col:
    if st.button("⚙️", key="corner_settings"):
        st.session_state.show_panel = (
            None if st.session_state.show_panel == "settings_full" else "settings_full"
        )
        st.rerun()

# اسم التطبيق
st.markdown("<div class='app-title'>Führer</div>", unsafe_allow_html=True)
st.markdown("<p class='sub-text' style='text-align:center;margin-top:-10px;'>النظام القانوني الذكي للقانون العمالي السعودي</p>",
            unsafe_allow_html=True)

# لوحة الإعدادات (نفس الأصل)
if st.session_state.show_panel == "settings_full":
    st.markdown("<div class='section-title'>الإعدادات والاتصال</div>", unsafe_allow_html=True)
    tabs = st.tabs(["الاتصال بالخادم", "لوحة التحكم", "بيانات الجلسة", "📄 رفع المستندات"])
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
        
        # إظهار حالة الاتصال الحالية
        status = st.session_state.connection_status
        if status == "connected":
            st.markdown("<div class='alert success fade-in'>🟢 متصل: الخادم يستجيب بشكل صحيح</div>", unsafe_allow_html=True)
        elif status == "failed":
            st.markdown(f"<div class='alert danger fade-in'>🔴 غير متصل: {st.session_state.connection_msg}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='alert info'>⚪ حالة الاتصال: لم يتم الاختبار بعد</div>", unsafe_allow_html=True)

        if st.button("🔌 اختبار وربط الاتصال", use_container_width=True):
            with st.spinner("جاري اختبار الاتصال بالخادم..."):
                ok, msg = ai_engine.test_connection(
                    st.session_state.preset_name,
                    st.session_state.api_key,
                    st.session_state.custom_url,
                    st.session_state.custom_model,
                    st.session_state.custom_fmt
                )
                st.session_state.connection_status = "connected" if ok else "failed"
                st.session_state.connection_msg = msg
                
                if ok:
                    storage.save_settings({
                        "preset_name": st.session_state.preset_name,
                        "custom_url": st.session_state.custom_url,
                        "custom_model": st.session_state.custom_model,
                        "custom_fmt": st.session_state.custom_fmt,
                        "api_key": st.session_state.api_key # حفظ المفتاح محلياً للسهولة
                    })
                    st.toast("✅ تم الاتصال وحفظ الإعدادات", icon="🚀")
                st.rerun()
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
    with tabs[3]:
        new_docs = file_processing.render_file_upload_widget()
        if new_docs:
            st.session_state.docs_text = new_docs
            st.success(f"✅ تم تحميل {len(new_docs)} مستند، سيتم استخدامها في المحادثات")
        if st.session_state.docs_text:
            if st.button("🗑️ مسح المستندات", key="clear_docs"):
                st.session_state.docs_text = []
                st.rerun()
    st.markdown("---")

# شاشة اختيار الشخصية
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
