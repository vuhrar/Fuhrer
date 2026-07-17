# fuhrer.py - المنصة القانونية الاحترافية الموحدة
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
import ui
import api
import tools

st.set_page_config(
    page_title="FÜHRER — المنصة القانونية الاحترافية",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# تطبيق التنسيق الاحترافي
st.markdown(ui.CSS, unsafe_allow_html=True)

# تهيئة حالة الجلسة
_saved = storage.load_settings()
_defaults = {
    "persona": None,
    "active_nav": "chat",
    "current_sid": None,
    "current_msgs": [],
    "docs_text": [],
    "preset_name": _saved.get("preset_name", "Führer Law Brain (Qwen 0.6B) 🧠"),
    "api_key": _saved.get("api_key", ""),
    "custom_url": _saved.get("custom_url", ""),
    "custom_model": _saved.get("custom_model", ""),
    "custom_fmt": _saved.get("custom_fmt", "openai"),
    "show_panel": None,
    "selected_tool": None,
    "connection_status": "unknown",
    "connection_msg": "",
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# شريط الحالة العلوي
status_col, corner_col = st.columns([10, 1])
with status_col:
    conn_status = st.session_state.get("connection_status", "unknown")
    if conn_status == "connected":
        st.markdown("<span style='color:#4ade80;font-size:0.8rem;float:left;margin-top:10px;'>🟢 النظام متصل</span>", unsafe_allow_html=True)
    elif conn_status == "failed":
        st.markdown("<span style='color:#f87171;font-size:0.8rem;float:left;margin-top:10px;'>🔴 خطأ في الربط</span>", unsafe_allow_html=True)
with corner_col:
    if st.button("⚙️", key="settings_icon"):
        st.session_state.show_panel = None if st.session_state.show_panel == "full" else "full"
        st.rerun()

# واجهة الإعدادات الاحترافية
if st.session_state.show_panel == "full":
    with st.container():
        st.markdown("<div class='section-title'>⚙️ إعدادات المنصة والربط التقني</div>", unsafe_allow_html=True)
        t1, t2, t3 = st.tabs(["الربط مع الخادم", "المستندات القانونية", "إدارة النظام"])
        
        with t1:
            col_a, col_b = st.columns(2)
            with col_a:
                st.session_state.preset_name = st.selectbox("مزود الذكاء الاصطناعي", list(ai_engine.PRESETS.keys()), 
                    index=list(ai_engine.PRESETS.keys()).index(st.session_state.preset_name) if st.session_state.preset_name in ai_engine.PRESETS else 0)
                st.session_state.api_key = st.text_input("مفتاح API", value=st.session_state.api_key, type="password")
            with col_b:
                if st.session_state.preset_name == "⚙️ مخصص":
                    st.session_state.custom_url = st.text_input("رابط API المخصص", value=st.session_state.custom_url)
                    st.session_state.custom_model = st.text_input("اسم النموذج المخصص", value=st.session_state.custom_model)
            
            if st.button("🔌 اختبار وتفعيل الربط", use_container_width=True):
                with st.spinner("جاري التحقق من استجابة الخادم..."):
                    ok, msg = ai_engine.test_connection(st.session_state.preset_name, st.session_state.api_key, 
                        st.session_state.custom_url, st.session_state.custom_model, st.session_state.custom_fmt)
                    st.session_state.connection_status = "connected" if ok else "failed"
                    st.session_state.connection_msg = msg
                    if ok:
                        storage.save_settings({"preset_name": st.session_state.preset_name, "api_key": st.session_state.api_key})
                        st.toast("✅ تم تفعيل الربط بنجاح")
                    st.rerun()
        
        with t2:
            new_docs = file_processing.render_file_upload_widget()
            if new_docs:
                st.session_state.docs_text = new_docs
                st.success(f"✅ تم دمج {len(new_docs)} مستند في عقل البرنامج")
            if st.session_state.docs_text:
                if st.button("🗑️ إفراغ ذاكرة المستندات"):
                    st.session_state.docs_text = []
                    st.rerun()
        
        with t3:
            if st.button("⚠️ مسح شامل لجميع البيانات المؤقتة", use_container_width=True):
                storage.clear_all_sessions()
                st.session_state.current_sid = None
                st.session_state.current_msgs = []
                st.rerun()
    st.markdown("---")

# الهيكل الرئيسي للتطبيق
st.markdown("<div class='app-title'>FÜHRER</div>", unsafe_allow_html=True)

if st.session_state.persona is None:
    ui.render_persona_selection()
else:
    ui.render_nav_bar()
    ui.render_persona_badge()
    
    nav = st.session_state.active_nav
    if nav == "chat":
        ui.render_chat()
    elif nav == "tool_exec":
        ui.render_tool_execution()
    elif nav == "sessions":
        ui.render_sessions()
    elif nav == "analysis":
        ui.render_analysis()
    elif nav == "cases":
        ui.render_cases()
    elif nav == "switch":
        st.session_state.persona = None
        st.session_state.active_nav = "chat"
        st.rerun()
