"""نقطة الدخول الموحدة لتطبيق Führer.

التشغيل المدعوم: Streamlit فقط، لمستخدم واحد على شبكة خاصة.
لا يُعد هذا التطبيق خدمة متعددة المستخدمين ولا يوفّر مشاركة عامة.
"""
from __future__ import annotations

import hmac
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

import legal_tools
import tools

APP_TITLE = "Führer | المساعد القانوني الشخصي"
ACCESS_TOKEN = os.getenv("APP_ACCESS_TOKEN", "").strip()
REQUIRE_ACCESS_TOKEN = os.getenv("REQUIRE_ACCESS_TOKEN", "true").lower() in {"1", "true", "yes", "on"}

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

MOBILE_CSS = """
<style>
:root { --primary: #1f6feb; --surface: #121821; --border: #273244; }
.block-container { max-width: 860px; padding: 1rem .85rem 3rem; }
section[data-testid="stSidebar"] { display: none; }
[data-testid="stHeader"] { background: transparent; }
.stButton > button, .stDownloadButton > button { min-height: 2.85rem; border-radius: .75rem; font-weight: 700; }
textarea, input, [data-baseweb="select"] { font-size: 16px !important; }
[data-testid="stFileUploader"] { border: 1px dashed var(--border); border-radius: .85rem; padding: .35rem; }
.mobile-card { border: 1px solid var(--border); border-radius: 1rem; padding: 1rem; margin: .65rem 0; background: rgba(18,24,33,.72); }
.disclaimer { border-right: 4px solid #e3a008; padding: .8rem; background: rgba(227,160,8,.1); border-radius: .6rem; font-size: .9rem; }
@media (max-width: 600px) { .block-container { padding: .7rem .65rem 2rem; } h1 { font-size: 1.55rem !important; } h2 { font-size: 1.25rem !important; } .stTabs [data-baseweb="tab-list"] { gap: .2rem; overflow-x: auto; } .stTabs [data-baseweb="tab"] { white-space: nowrap; padding: .55rem .6rem; } }
</style>
"""
st.markdown(MOBILE_CSS, unsafe_allow_html=True)


def _check_access() -> bool:
    if not REQUIRE_ACCESS_TOKEN:
        return True
    if not ACCESS_TOKEN:
        st.error("لم يتم ضبط APP_ACCESS_TOKEN. أوقف التطبيق، أضف الرمز إلى ملف .env، ثم أعد التشغيل.")
        st.code("APP_ACCESS_TOKEN=ضع_رمزًا_طويلًا_خاصًا_بك")
        return False
    if st.session_state.get("authenticated") is True:
        return True
    st.markdown("## دخول خاص")
    st.caption("هذا التطبيق مخصص لمستخدم واحد فقط ولا يتيح إنشاء حسابات أو مشاركة القضايا.")
    token = st.text_input("رمز الوصول", type="password", autocomplete="current-password")
    if st.button("دخول", type="primary", use_container_width=True):
        if hmac.compare_digest(token, ACCESS_TOKEN):
            st.session_state.authenticated = True
            st.rerun()
        st.error("رمز الوصول غير صحيح.")
    return False


def _init_state() -> None:
    st.session_state.setdefault("persona", "lawyer")
    st.session_state.setdefault("tool_id", "law_search")


def _render_home() -> None:
    st.title(APP_TITLE)
    st.markdown("مساعد قانوني شخصي للاستخدام المحلي، يركز على التحليل الأولي والبحث والحسابات المساعدة في نطاق الأنظمة السعودية.")
    st.markdown("<div class='disclaimer'><strong>تنبيه:</strong> المخرجات مساعدة أولية وليست بديلاً عن نصيحة محامٍ مؤهل أو تحقق مستقل من النظام والوقائع.</div>", unsafe_allow_html=True)
    st.markdown("### اختر الدور المهني")
    personas = {"lawyer": "المحامي", "advisor": "المستشار القانوني", "labor_consultant": "المستشار العمالي"}
    selected = st.selectbox("الدور", list(personas), format_func=lambda x: personas[x], key="persona")
    tools_for_role = legal_tools.get_tools_for_persona(selected)
    if not tools_for_role:
        tools_for_role = [
            ("🔍", "البحث في الأنظمة واللوائح", "law_search"),
            ("💰", "حساب المستحقات المالية", "calculator"),
            ("📊", "تقييم المخاطر والقضية", "case_strength"),
            ("📄", "استخراج البيانات من المستندات", "extractor"),
        ]
    labels = {tool_id: f"{icon} {name}" for icon, name, tool_id in tools_for_role}
    ids = list(labels)
    if st.session_state.get("tool_id") not in ids:
        st.session_state.tool_id = ids[0]
    choice = st.radio("الأداة", ids, format_func=lambda x: labels[x], key="tool_id")
    st.divider()
    renderer = {
        "calculator": tools.run_calculator,
        "law_search": tools.run_law_search,
        "email_scan": tools.run_email_scan,
        "case_strength": tools.run_case_strength,
        "settlement": tools.run_settlement,
        "extractor": tools.run_info_extractor,
        "litigation": tools.run_litigation_center,
        "document_gen": tools.run_litigation_center,
        "contract_review": tools.run_case_strength,
        "risk_report": tools.run_case_strength,
        "deadlines": tools.run_calculator,
    }
    renderer.get(choice, tools.run_law_search)()


def main() -> None:
    _init_state()
    if not _check_access():
        return
    with st.container():
        _render_home()
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.caption("وضع التشغيل: مستخدم واحد / جلسة محلية")
    with col2:
        if st.button("تسجيل الخروج", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()


if __name__ == "__main__":
    main()
else:
    main()
