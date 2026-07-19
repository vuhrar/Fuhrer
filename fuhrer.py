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
st.markdown(styles.MAIN_CSS, unsafe_allow_html=True)


# تهيئة حالة الجلسة
_saved = storage.load_settings()
_defaults = {
    "persona": None,
    "active_nav": "chat",
    "current_sid": None,
    "current_msgs": [],
    "docs_text": [],
    "preset_name": _saved.get("preset_name", "Groq LLaMA 3.3 70B 🚀 (مجاني)"),
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
            # اختيار المزود
            preset_keys = list(ai_engine.PRESETS.keys())
            current_idx = preset_keys.index(st.session_state.preset_name) if st.session_state.preset_name in preset_keys else 0
            st.session_state.preset_name = st.selectbox("🤖 مزود الذكاء الاصطناعي", preset_keys, index=current_idx)

            selected = ai_engine.PRESETS[st.session_state.preset_name]

            # بطاقة معلومات المزود
            is_local = "Führer" in st.session_state.preset_name and "محلي" in st.session_state.preset_name
            badge = "🟢 مجاني" if selected.free else "🔵 مدفوع"
            st.markdown(
                f"<div style='background:#f1f5f9;border-right:4px solid #6366f1;padding:10px 14px;"
                f"border-radius:8px;margin:6px 0 12px;font-size:0.85rem;'>"
                f"<b>{selected.name}</b> &nbsp; {badge}<br>"
                f"<span style='color:#64748b;'>{selected.description}</span><br>"
                f"<code style='font-size:0.75rem;color:#475569;'>{selected.url or 'localhost'}</code>"
                f"</div>",
                unsafe_allow_html=True
            )

            # تعليمات Führer Brain المحلي
            if is_local:
                st.info(
                    "🧠 **Führer Law Brain — نموذج محلي**\n\n"
                    "لتشغيل هذا النموذج:\n"
                    "1. حمّل [LM Studio](https://lmstudio.ai) على حاسبك\n"
                    "2. افتح النموذج: `distil-qwen3-0.6b-shellper-q4_k_m`\n"
                    "3. شغّل الخادم المحلي على المنفذ **1234**\n"
                    "4. اضغط 'اختبار الاتصال' — لا يلزم مفتاح API"
                )

            # روابط الحصول على مفاتيح API
            _key_links = {
                "Groq":     ("مجاني من", "https://console.groq.com/keys"),
                "Gemini":   ("مجاني من", "https://aistudio.google.com/app/apikey"),
                "Claude":   ("من", "https://console.anthropic.com/settings/keys"),
                "GPT":      ("من", "https://platform.openai.com/api-keys"),
                "HF ":      ("مجاني من", "https://huggingface.co/settings/tokens"),
                "DeepSeek": ("من", "https://platform.deepseek.com/api_keys"),
                "Together": ("من", "https://api.together.xyz/settings/api-keys"),
            }
            for keyword, (label, link) in _key_links.items():
                if keyword in st.session_state.preset_name:
                    st.caption(f"🔑 احصل على مفتاح API {label}: [{link}]({link})")
                    break

            col_a, col_b = st.columns(2)
            with col_a:
                if not is_local:
                    st.session_state.api_key = st.text_input(
                        "مفتاح API", value=st.session_state.api_key, type="password",
                        placeholder="أدخل المفتاح هنا..."
                    )
            with col_b:
                if "مخصص" in st.session_state.preset_name:
                    st.session_state.custom_url   = st.text_input("رابط API المخصص",    value=st.session_state.custom_url)
                    st.session_state.custom_model = st.text_input("اسم النموذج المخصص", value=st.session_state.custom_model)

            if st.button("🔌 اختبار وتفعيل الربط", use_container_width=True):
                with st.spinner("جاري التحقق من استجابة الخادم..."):
                    ok, msg = ai_engine.test_connection(
                        st.session_state.preset_name, st.session_state.api_key,
                        st.session_state.custom_url, st.session_state.custom_model,
                        st.session_state.custom_fmt
                    )
                    st.session_state.connection_status = "connected" if ok else "failed"
                    st.session_state.connection_msg = msg
                    if ok:
                        storage.save_settings({
                            "preset_name": st.session_state.preset_name,
                            "api_key":     st.session_state.api_key
                        })
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
