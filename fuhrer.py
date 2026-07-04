# fuhrer.py
"""
Führer - تطبيق قانوني متخصص في القانون العمالي السعودي.
تطبيق Streamlit مع:
- واجهة عربية كاملة (RTL)
- 18 محور تحليل قانوني
- أدوات قانونية متقدمة
- قاعدة بيانات قانونية
- AI متكامل
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

# استيراد الوحدات
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

# تهيئة الصفحة
st.set_page_config(
    page_title="Führer",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS - ثيم داكن عربي
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;900&display=swap');
*, *::before, *::after { box-sizing: border-box !important; font-family: 'Tajawal', sans-serif !important; }
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"],
[data-testid="stBottom"], section[data-testid="stSidebar"] {
  background-color: #1c1c1e !important; color: #ffffff !important; direction: rtl !important;
}
[data-testid="stSidebar"], [data-testid="collapsedControl"], #MainMenu, footer, header { display: none !important; }
.main .block-container { max-width: 800px !important; padding: 0 16px 80px !important; margin: 0 auto !important; }
.app-title { text-align: center; padding: 32px 0 8px; font-size: 3.2rem; font-weight: 900; color: #ffffff; letter-spacing: 0.04em; }
.settings-corner { position: fixed; top: 12px; right: 12px; z-index: 9999; }
.persona-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin: 24px 0 8px; }
.persona-card {
  background: #2c2c2e; border: 2px solid #c9a84c; border-radius: 18px; padding: 28px 16px;
  text-align: center; cursor: pointer; transition: all 0.2s;
}
.persona-card.active { background: #3a3020; border-color: #f0c040; box-shadow: 0 0 0 3px rgba(201,168,76,0.3); }
.persona-card .pc-title { font-size: 1.25rem; font-weight: 800; color: #ffffff; margin: 10px 0 6px; }
.persona-card .pc-sub { font-size: 0.78rem; color: #aaaaaa; line-height: 1.5; }
.nav-bar { display: flex; gap: 8px; margin: 16px 0 4px; overflow-x: auto; padding-bottom: 4px; }
.nav-bar::-webkit-scrollbar { height: 0; }
.tools-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 10px; margin: 10px 0; }
.stButton > button {
  background: #2c2c2e !important; color: #ffffff !important; border: 1.5px solid #c9a84c !important;
  border-radius: 14px !important; font-weight: 700 !important; font-size: 0.95rem !important;
  font-family: 'Tajawal', sans-serif !important; padding: 12px 18px !important; width: 100% !important;
  transition: all 0.18s !important;
}
.stButton > button:hover { background: #3a3020 !important; border-color: #f0c040 !important; color: #f0c040 !important; }
.send-btn .stButton > button {
  background: linear-gradient(135deg, #c9a84c, #a8882e) !important; color: #1c1c1e !important;
  border-color: transparent !important; font-size: 1rem !important; padding: 14px !important;
}
.bubble-wrap { margin: 6px 0; }
.bubble-user {
  background: #2c3e50; border: 1px solid #3a5068; border-radius: 18px 18px 4px 18px;
  padding: 12px 16px; margin-right: 10%; color: #ffffff !important; font-size: 0.95rem;
  line-height: 1.75; word-wrap: break-word;
}
.bubble-ai {
  background: #2c2c2e; border: 1px solid #3a3a3c; border-right: 3px solid #c9a84c;
  border-radius: 18px 18px 18px 4px; padding: 12px 16px; margin-left: 10%;
  color: #ffffff !important; font-size: 0.95rem; line-height: 1.8; word-wrap: break-word;
}
.bubble-ai.adv { border-right-color: #4a9eff; }
.bubble-time { font-size: 0.68rem; color: #666 !important; margin-top: 4px; text-align: left; }
.stTextArea textarea, .stTextInput input {
  background: #2c2c2e !important; color: #ffffff !important; border: 1.5px solid #3a3a3c !important;
  border-radius: 14px !important; font-family: 'Tajawal', sans-serif !important;
  font-size: 0.95rem !important; direction: rtl !important; caret-color: #c9a84c;
}
.stTextArea textarea:focus, .stTextInput input:focus {
  border-color: #c9a84c !important; box-shadow: 0 0 0 2px rgba(201,168,76,0.2) !important;
}
.stSelectbox > div > div, .stNumberInput input {
  background: #2c2c2e !important; color: #ffffff !important; border: 1.5px solid #3a3a3c !important;
  border-radius: 12px !important;
}
.card {
  background: #2c2c2e; border: 1px solid #3a3a3c; border-right: 3px solid #c9a84c;
  border-radius: 14px; padding: 14px 18px; margin: 8px 0; color: #ffffff !important;
}
.card.blue { border-right-color: #4a9eff; }
.card.ok { border-right-color: #4ade80; }
.card.red { border-right-color: #ff5a5a; }
.alert {
  border-radius: 12px; padding: 10px 14px; margin: 6px 0; font-size: 0.88rem;
  line-height: 1.6; color: #ffffff !important;
}
.alert.warn { background: rgba(255,180,0,0.1); border-right: 3px solid #ffb400; }
.alert.danger { background: rgba(255,90,90,0.1); border-right: 3px solid #ff5a5a; }
.alert.ok { background: rgba(74,222,128,0.1); border-right: 3px solid #4ade80; }
.alert.info { background: rgba(74,158,255,0.1); border-right: 3px solid #4a9eff; }
.stat-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 12px 0; }
.stat-box {
  background: #2c2c2e; border: 1.5px solid #c9a84c; border-radius: 14px; padding: 14px;
  text-align: center;
}
.stat-box .v { font-size: 1.4rem; font-weight: 800; color: #c9a84c; }
.stat-box .l { font-size: 0.72rem; color: #aaaaaa; margin-top: 3px; }
.stProgress > div > div > div {
  background: linear-gradient(90deg, #c9a84c, #f0c040) !important; border-radius: 4px !important;
}
.sub-text { color: #aaaaaa !important; font-size: 0.85rem; }
.section-title {
  font-size: 1.05rem; font-weight: 800; color: #c9a84c; margin: 20px 0 10px;
  padding-bottom: 6px; border-bottom: 1px solid #3a3a3c;
}
.streamlit-expanderHeader {
  background: #2c2c2e !important; color: #ffffff !important; border-radius: 10px !important;
  border: 1px solid #3a3a3c !important;
}
.streamlit-expanderContent {
  background: #242426 !important; border: 1px solid #3a3a3c !important;
  border-radius: 0 0 10px 10px !important; color: #ffffff !important;
}
[data-testid="stFileUploader"] {
  background: #2c2c2e !important; border: 2px dashed #c9a84c !important;
  border-radius: 14px !important;
}
[data-testid="stFileUploader"] * { color: #ffffff !important; }
.stCaption, label, .stMarkdown p { color: #aaaaaa !important; }
@media (max-width: 500px) {
  .app-title { font-size: 2.4rem !important; }
  .persona-card .pc-title { font-size: 1.1rem; }
  .tools-grid { grid-template-columns: 1fr; }
  .stat-grid { grid-template-columns: 1fr; }
}
.classification-result {
  background: #2c2c2e; border: 2px solid #c9a84c; border-radius: 14px;
  padding: 16px; margin: 12px 0; text-align: center;
}
.classification-result .category {
  font-size: 1.4rem; font-weight: 800; color: #c9a84c; margin-bottom: 8px;
}
.classification-result .confidence { font-size: 0.9rem; color: #aaaaaa; }
.legal-search-result {
  background: #2c2c2e; border: 1px solid #3a3a3c; border-radius: 12px;
  padding: 12px 16px; margin: 8px 0;
}
.legal-search-result .title { font-weight: 700; color: #c9a84c; margin-bottom: 4px; }
.legal-search-result .snippet { color: #aaaaaa; font-size: 0.9rem; line-height: 1.6; }
.legal-search-result .meta { font-size: 0.8rem; color: #666; margin-top: 6px; }
</style>
""", unsafe_allow_html=True)

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
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

def ai_call(prompt, history, system):
    return ai_engine.call_ai(
        prompt, history, system,
        preset_name=st.session_state.preset_name,
        api_key=st.session_state.api_key,
        custom_url=st.session_state.custom_url,
        custom_model=st.session_state.custom_model,
        custom_fmt=st.session_state.custom_fmt,
    )

# زر الإعدادات
corner_col = st.columns([8, 1])[1]
with corner_col:
    if st.button("⚙️", key="corner_settings"):
        st.session_state.show_panel = (
            None if st.session_state.show_panel == "settings_full" else "settings_full"
        )
        st.rerun()

# اسم التطبيق
st.markdown("<div class='app-title'>Führer</div>", unsafe_allow_html=True)
st.markdown("<p class='sub-text' style='text-align:center;margin-top:-10px;'>النظام القانوني العمالي السعودي</p>",
            unsafe_allow_html=True)

# لوحة الإعدادات
if st.session_state.show_panel == "settings_full":
    st.markdown("<div class='section-title'>الإعدادات والاتصال</div>", unsafe_allow_html=True)
    tabs = st.tabs(["الاتصال بالخادم", "لوحة التحكم", "بيانات الجلسة"])
    with tabs[0]:
        # دالة اختبار اتصال
        def test_connection(api_type, value, url=None):
            if not value:
                return "⚠️ مفقود"
            clean_type = "".join([c for c in str(api_type).upper() if c.isalnum()])
            try:
                if "GROQ" in clean_type:
                    from ai_engine import GroqEngine
                    groq = GroqEngine(api_key=value)
                    groq.generate("اختبار", max_tokens=5)
                    return "🟢 متصل"
                elif "HUGGINGFACE" in clean_type or "HF" in clean_type:
                    from ai_engine import HuggingFaceEngine
                    hf = HuggingFaceEngine(api_token=value)
                    hf.generate("اختبار", max_tokens=5)
                    return "🟢 متصل"
                elif "SUPABASE" in clean_type:
                    from storage import SupabaseStorage
                    supabase = SupabaseStorage(url=url, key=value)
                    supabase.list_files()
                    return "🟢 متصل"
                else:
                    import requests
                    target_url = url if url else st.session_state.get("custom_url", "")
                    model_name = st.session_state.get("custom_model", "gpt-3.5-turbo")
                    fmt = st.session_state.get("custom_fmt", "openai").lower()
                    
                    if not target_url:
                        return "⚠️ رابط الـ API مفقود"
                        
                    headers = {"Authorization": f"Bearer {value}", "Content-Type": "application/json"}
                    
                    if fmt == "openai":
                        payload = {"model": model_name, "messages": [{"role": "user", "content": "test"}], "max_tokens": 5}
                        endpoint = target_url if "/chat/completions" in target_url else f"{target_url.rstrip('/')}/v1/chat/completions"
                    elif fmt == "huggingface":
                        payload = {"inputs": "test", "parameters": {"max_new_tokens": 5}}
                        endpoint = target_url
                    else:
                        payload = {"model": model_name, "prompt": "test", "max_tokens": 5}
                        endpoint = target_url

                    res = requests.post(endpoint, json=payload, headers=headers, timeout=8)
                    if res.status_code == 200:
                        return "🟢 متصل"
                    else:
                        return f"🔴 خطأ {res.status_code}: {res.text[:30]}"
            except Exception as e:
                return f"🔴 {str(e)}"


        # إعدادات النموذج
        def test_connection(api_type, value, url=None):
            if not value:
                return "⚠️ مفقود"
            try:
                # الفحص الفعلي لأي نموذج موجود في القائمة عبر ملف ai_engine الخاص بك
                if hasattr(ai_engine, 'get_preset_info'):
                    preset_info = ai_engine.get_preset_info(api_type)
                    if preset_info:
                        # جلب مسار الرابط أو المحرك الفعلي للنموذج المختار ديناميكياً
                        target_url = url if url else preset_info.get("url", st.session_state.get("custom_url", ""))
                        
                        import requests
                        headers = {"Authorization": f"Bearer {value}", "Content-Type": "application/json"}
                        # إضافة كود التعرف على مفاتيح Gemini إذا كان النموذج تابعاً لها
                        if "gemini" in str(api_type).lower() or "google" in str(api_type).lower():
                            headers = {"x-goog-api-key": value}
                            
                        res = requests.get(target_url if target_url else "https://openai.com", headers=headers, timeout=5)
                        if res.status_code in:
                            return "🟢 متصل"
                        else:
                            return f"🔴 خطأ {res.status_code}"
                
                return "🟢 تم إدخال المفتاح"
            except Exception as e:
                return f"🔴 {str(e)}"

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

# شاشة اختيار الشخصية
if st.session_state.persona is None:
    st.markdown("<p class='sub-text' style='text-align:center;margin-bottom:4px;'>اختر الشخصية التي تناسب حاجتك</p>",
                unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("👨⚖️ المحامي\n\nهجومي، يكتب الدعاوى", key="pick_lawyer", use_container_width=True):
            st.session_state.persona = "lawyer"
            st.session_state.active_nav = "chat"
            if not st.session_state.current_sid:
                sid = storage.new_session_id()
                st.session_state.current_sid = sid
                st.session_state.current_msgs = []
                storage.save_session(sid, {"name": "جلسة المحامي", "messages": [], "persona": "lawyer"})
            st.rerun()
    with c2:
        if st.button("👩💼 المستشار\n\nتحليلي، يحسب الاستحقاقات", key="pick_advisor", use_container_width=True):
            st.session_state.persona = "advisor"
            st.session_state.active_nav = "chat"
            if not st.session_state.current_sid:
                sid = storage.new_session_id()
                st.session_state.current_sid = sid
                st.session_state.current_msgs = []
                storage.save_session(sid, {"name": "جلسة المستشار", "messages": [], "persona": "advisor"})
            st.rerun()
    st.markdown("<div style='text-align:center;margin-top:40px;'>"
                "<p class='sub-text'>👨⚖️ المحامي — يكتب الدعاوى والحجج الدفاعية</p>"
                "<p class='sub-text'>👩💼 المستشار — يحسب المستحقات ويوجه</p>"
                "</div>", unsafe_allow_html=True)

# بعد اختيار الشخصية
else:
    persona = st.session_state.persona
    persona_label = "المحامي" if persona == "lawyer" else "المستشار"
    persona_icon = "👨⚖️" if persona == "lawyer" else "👩💼"

    # شريط التنقل
    nav_items = [
        ("💬 المحادثة", "chat"),
        ("🔧 الأدوات", "tools"),
        ("📋 الجلسات", "sessions"),
        ("📊 تحليل 18", "analysis"),
        ("📁 القضايا", "cases"),
        ("🔄 تغيير", "switch"),
    ]
    nav_cols = st.columns(len(nav_items))
    for col, (label, key) in zip(nav_cols, nav_items):
        with col:
            is_active = st.session_state.active_nav == key
            prefix = "✓ " if is_active else ""
            if st.button(f"{prefix}{label}", key=f"nav_{key}", use_container_width=True):
                if key == "switch":
                    st.session_state.persona = None
                    st.session_state.active_nav = "chat"
                    st.session_state.current_sid = None
                    st.session_state.current_msgs = []
                else:
                    st.session_state.active_nav = key
                st.rerun()

    # مؤشر الشخصية النشطة
    color = "#c9a84c" if persona == "lawyer" else "#4a9eff"
    st.markdown(f"""<div style='text-align:center;margin:6px 0 16px;'>
        <span style='font-size:0.82rem;color:{color};font-weight:700;
                       border:1px solid {color};border-radius:20px;
                       padding:4px 14px;'>
        {persona_icon} {persona_label}
        </span>
    </div>""", unsafe_allow_html=True)

    nav = st.session_state.active_nav

    # صفحة المحادثة
    if nav == "chat":
        if st.session_state.current_sid:
            sess_data = storage.load_session(st.session_state.current_sid)
            ai_cls = "bubble-ai adv" if persona == "advisor" else "bubble-ai"
            for msg in st.session_state.current_msgs:
                content = (msg["content"].replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>"))
                ts = msg.get("ts", "")
                if msg["role"] == "user":
                    st.markdown(f"<div class='bubble-user'>{content}<div class='bubble-time'>{ts}</div></div>",
                                unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='{ai_cls}'>{content}<div class='bubble-time'>{ts}</div></div>",
                                unsafe_allow_html=True)
            pending = st.session_state.get("pending_input", "")
            user_input = st.text_area("", value=pending, height=100,
                                       placeholder="اكتب سؤالك القانوني هنا...",
                                       label_visibility="collapsed", key="chat_input")
            if pending:
                st.session_state.pending_input = ""
            sc = st.columns([3, 1])
            with sc[0]:
                send = st.button("📤 إرسال", key="send_main", use_container_width=True)
            with sc[1]:
                if st.button("🗑️ مسح", key="clear_main", use_container_width=True):
                    st.session_state.current_msgs = []
                    sess_data["messages"] = []
                    storage.save_session(st.session_state.current_sid, sess_data)
                    st.rerun()
            if send and user_input.strip():
                ts = datetime.now().strftime("%H:%M")
                st.session_state.current_msgs.append(
                    {"role": "user", "content": user_input.strip(), "ts": ts})
                system_p = legal_tools.PERSONA_PROMPTS[persona]
                if st.session_state.docs_text:
                    context = "\n\n".join(st.session_state.docs_text[:3])
                    system_p += f"\n\nالوثائق المحملة:\n{context[:3000]}"
                with st.spinner("جارٍ التحليل..."):
                    resp = ai_call(user_input.strip(), st.session_state.current_msgs[:-1], system_p)
                st.session_state.current_msgs.append(
                    {"role": "assistant", "content": resp, "ts": ts})
                sess_data["messages"] = st.session_state.current_msgs
                sess_data["persona"] = persona
                storage.save_session(st.session_state.current_sid, sess_data)
                st.rerun()
        else:
            st.markdown("<p class='sub-text' style='text-align:center;margin-top:30px;'>"
                        "لا توجد جلسة نشطة — افتح جلسة جديدة من قسم الجلسات</p>",
                        unsafe_allow_html=True)

    # صفحة الأدوات
    elif nav == "tools":
        st.markdown("<div class='section-title'>🔧 الأدوات القانونية المتقدمة</div>", unsafe_allow_html=True)
        tools_list = legal_tools.get_tools_for_persona(persona)
        st.markdown("### اختر أداة:")
        cols = st.columns(2)
        for i, (icon, name, tool_id) in enumerate(tools_list):
            with cols[i % 2]:
                if st.button(f"{icon} {name}", key=f"tool_{tool_id}", use_container_width=True):
                    st.session_state.selected_tool = tool_id
                    st.rerun()
        if st.session_state.selected_tool:
            tool_id = st.session_state.selected_tool
            if tool_id == "calculator":
                st.markdown("<div class='section-title'>💰 حاسبة الاستحقاقات القانونية</div>", unsafe_allow_html=True)
                calc_tabs = st.tabs(["نهاية الخدمة", "رصيد الإجازة", "مواعيد قانونية"])
                with calc_tabs[0]:
                    st.markdown("#### 💰 مكافأة نهاية الخدمة (مادة 84)")
                    col1, col2 = st.columns(2)
                    with col1:
                        basic_salary = st.number_input("الراتب الأساسي (ريال):", min_value=0.0, value=10000.0, step=100.0, key="eosb_basic")
                        total_salary = st.number_input("الراتب الإجمالي (ريال):", min_value=0.0, value=15000.0, step=100.0, key="eosb_total")
                    with col2:
                        years_of_service = st.number_input("سنوات الخدمة:", min_value=0.0, value=5.0, step=0.1, key="eosb_years")
                        is_saudi = st.checkbox("عامل سعودي", value=True, key="eosb_saudi")
                    with st.expander("⚙️ خيارات متقدمة"):
                        arbitrary = st.checkbox("تعويض فصل تعسفي (مادة 77)", value=True, key="eosb_arbitrary")
                        delay_months = st.number_input("أشهر تأخير في دفع الراتب (مادة 90):", min_value=0, value=0, key="eosb_delay")
                    if st.button("🧮 احسب مكافأة نهاية الخدمة", use_container_width=True):
                        result = entitlements_calculator.calculate_eosb(
                            basic_salary=basic_salary, total_salary=total_salary,
                            years_of_service=years_of_service, is_arbitrary=arbitrary,
                            delay_months=delay_months, is_saudi=is_saudi)
                        st.markdown("### 💰 نتيجة الحساب")
                        st.markdown(f"""<div class='card'>
                            <h3>المجموع: {result['totals']['grand_total']:,.2f} ريال سعودي</h3>
                        </div>""", unsafe_allow_html=True)
                        st.markdown("### 📋 التفاصيل:")
                        for desc, detail in result['details'].items():
                            if detail['amount'] > 0:
                                st.markdown(f"- **{detail['description']}**: {detail['amount']:,.2f} ريال")
                with calc_tabs[1]:
                    st.markdown("#### 🗓️ رصيد الإجازة السنوية")
                    start_date = st.date_input("تاريخ بداية العمل:", value=datetime(2020, 1, 1), key="vacation_start")
                    end_date = st.date_input("تاريخ نهاية العمل (اختياري):", key="vacation_end")
                    annual_days = st.slider("أيام الإجازة السنوية:", min_value=21, max_value=30, value=21, key="vacation_days")
                    if st.button("🧮 احسب رصيد الإجازة", use_container_width=True):
                        result = entitlements_calculator.calculate_vacation_balance(
                            start_date=start_date.strftime("%Y-%m-%d"),
                            end_date=end_date.strftime("%Y-%m-%d") if end_date else "",
                            annual_vacation_days=annual_days)
                        st.markdown("### 🗓️ رصيد الإجازة")
                        st.markdown(f"""<div class='card'>
                            <h3>رصيد الإجازة: {result['earned_vacation']:.1f} يوم</h3>
                            <p>منها {result['full_years_vacation']} يوم كاملة + {result['remaining_vacation']:.1f} يوم جزئية</p>
                        </div>""", unsafe_allow_html=True)
                with calc_tabs[2]:
                    st.markdown("#### ⏳ متابعة المواعيد القانونية")
                    case_type = st.selectbox("نوع القضية:", list(deadlines_tracker.deadlines.keys()), key="deadline_case_type")
                    case_date = st.date_input("تاريخ بداية القضية:", value=datetime.now(), key="deadline_case_date")
                    if st.button("⏳ تحقق من الموعد", use_container_width=True):
                        result = deadlines_tracker.check_deadline(case_type, case_date.strftime("%Y-%m-%d"))
                        color = "#ff5a5a" if result['status'] == "manquée" else "#ffb400" if result['status'] in ["urgente", "proche"] else "#4ade80"
                        st.markdown(f"""<div class='card' style='border-right-color: {color};'>
                            <h3 style='color: {color};'>{result['message']}</h3>
                            <p><strong>المواعيد:</strong></p>
                            <p>- تاريخ بدء القضية: {result['case_date']}</p>
                            <p>- آخر موعد: {result['due_date']}</p>
                            <p>- الأيام المتبقية: {result['days_remaining']} يوم</p>
                            <p>- المادة القانونية: مادة {result['article']}</p>
                        </div>""", unsafe_allow_html=True)
                        st.markdown("### 📋 الإجراء المطلوب:")
                        st.markdown(result['action'])
            elif tool_id == "law_search":
                st.markdown("<div class='section-title'>📚 البحث في الأنظمة القانونية</div>", unsafe_allow_html=True)
                search_method = st.radio("طريقة البحث:", ["بحث سريع", "بحث متقدم (AI)"], horizontal=True, key="search_method")
                search_query = st.text_input("عبارة البحث:", placeholder="ادخل كلمات البحث...", key="law_search_query")
                category = st.selectbox("الفئة (اختياري):", ["جميع الفئات"] + analysis_engine.get_all_categories(), key="law_search_category")
                if st.button("🔍 بحث", use_container_width=True):
                    if not search_query.strip():
                        st.warning("الرجاء إدخال عبارة البحث.")
                    else:
                        with st.spinner("جاري البحث..."):
                            if search_method == "بحث سريع":
                                category_filter = None if category == "جميع الفئات" else category
                                results = analysis_engine.search_saudi_labor_laws(search_query, max_results=10)
                            else:
                                results = analysis_engine.search_with_ai(search_query, ai_call, max_results=5)
                        if results:
                            st.markdown(f"### 📚 نتائج البحث ({len(results)} نتيجة)")
                            for result in results:
                                with st.expander(f"{result.get('title', 'مادة غير معروفة')} — {result.get('category', 'عام')}"):
                                    st.markdown(f"**المصدر:** {result.get('source', 'مجهول')}")
                                    st.markdown(f"**المادة:** {result.get('id', 'مجهول')}")
                                    st.markdown("**النص:**")
                                    st.markdown(f"<div class='card'>{result.get('text', '')[:1000]}</div>", unsafe_allow_html=True)
            elif tool_id == "email_scan":
                st.markdown("<div class='section-title'>📧 فحص المراسلات القانونية</div>", unsafe_allow_html=True)
                email_text = st.text_area("نص المراسلة:", height=200, placeholder="ادخل نص البريد الإلكتروني أو الرسالة...", key="email_scan_input")
                if st.button("🔍 فحص المراسلة", use_container_width=True):
                    if not email_text.strip():
                        st.warning("الرجاء إدخال نص المراسلة.")
                    else:
                        with st.spinner("جاري الفحص..."):
                            slips = slip_detector.detect(email_text)
                        if slips:
                            st.markdown("### ⚠️ زلات قانونية مكتشفة")
                            for slip in slips:
                                st.markdown(f"""<div class='alert {slip['level']}'>
                                    <strong>{slip['msg']}</strong> (مادة {slip['article']})<br>
                                    <small>النص: {slip['snippet']}</small><br>
                                    <small>التوصية: {slip['suggestion']}</small>
                                </div>""", unsafe_allow_html=True)
                        else:
                            st.success("✅ لا توجد زلات قانونية واضحة في المراسلة.")
            elif tool_id == "case_strength":
                st.markdown("<div class='section-title'>📊 تقييم قوة القضية</div>", unsafe_allow_html=True)
                case_details = st.text_area("تفاصيل القضية:", height=200, placeholder="صف الوقائع، الأدلة، والمطالبات...", key="case_strength_input")
                if st.button("📊 تقييم القوة", use_container_width=True):
                    if not case_details.strip():
                        st.warning("الرجاء إدخال تفاصيل القضية.")
                    else:
                        with st.spinner("جاري التقييم..."):
                            category, confidence, _ = legal_classifier.classify(case_details)
                            analysis = case_analyzer.quick_analyze(case_details, category)
                        st.markdown("### 🎯 نتيجة التقييم")
                        score = analysis.get("score", 5)
                        if score >= 8:
                            strength, color, icon = "قوية جداً", "#4ade80", "💪"
                        elif score >= 6:
                            strength, color, icon = "قوية", "#4a9eff", "👍"
                        elif score >= 4:
                            strength, color, icon = "متوسطة", "#ffb400", "🤔"
                        else:
                            strength, color, icon = "ضعيفة", "#ff5a5a", "❌"
                        st.markdown(f"""<div class='card' style='border-right-color: {color};'>
                            <h2 style='color: {color};'>{icon} درجة القوة: {score}/10 - {strength}</h2>
                            <p><strong>احتمال النجاح:</strong> {analysis.get('success_probability', '50%')}</p>
                        </div>""", unsafe_allow_html=True)
                        st.markdown("### 📝 التحليل")
                        st.markdown(analysis.get("analysis", ""))
                        st.markdown("### 💡 التوصيات")
                        for rec in analysis.get("recommendations", []):
                            st.markdown(f"- {rec}")
            elif tool_id == "settlement":
                st.markdown("<div class='section-title'>🤝 تقييم خيارات التسوية</div>", unsafe_allow_html=True)
                case_details = st.text_area("تفاصيل القضية:", height=200, placeholder="صف القضيه، المطالبات، والمبلغ المتوقع...", key="settlement_input")
                if st.button("🤝 تقييم التسوية", use_container_width=True):
                    if not case_details.strip():
                        st.warning("الرجاء إدخال تفاصيل القضية.")
                    else:
                        with st.spinner("جاري التقييم..."):
                            prompt = legal_tools.TOOL_PROMPTS["settlement"][2]
                            prompt = f"{prompt}\n\nتفاصيل القضية:\n{case_details}"
                            settlement = ai_call(prompt, [], legal_tools.PERSONA_PROMPTS["advisor"])
                        st.markdown("### 🤝 خيارات التسوية")
                        st.markdown(f"<div class='card'>{settlement}</div>", unsafe_allow_html=True)
            if st.session_state.selected_tool:
                if st.button("⬅️ العودة إلى قائمة الأدوات", use_container_width=True):
                    st.session_state.selected_tool = None
                    st.rerun()

    # صفحة الجلسات
    elif nav == "sessions":
        st.markdown("<div class='section-title'>📋 إدارة الجلسات</div>", unsafe_allow_html=True)
        sessions = storage.list_sessions()
        if sessions:
            st.markdown("### الجلسات المحفوظة")
            for sess in sessions:
                with st.expander(f"📄 {sess['name']} — {sess['count']} رسائل — {sess['persona']}"):
                    st.markdown(f"**المعرف:** `{sess['id']}`")
                    st.markdown(f"**التاريخ:** {sess.get('created_at', 'مجهول')}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"فتح", key=f"open_sess_{sess['id']}"):
                            st.session_state.current_sid = sess['id']
                            st.session_state.current_msgs = storage.load_session(sess['id']).get("messages", [])
                            st.session_state.active_nav = "chat"
                            st.rerun()
                    with col2:
                        if st.button(f"حذف", key=f"del_sess_{sess['id']}"):
                            storage.delete_session(sess['id'])
                            st.rerun()
        else:
            st.info("لا توجد جلسات محفوظة.")
        st.markdown("---")
        st.markdown("### إنشاء جلسة جديدة")
        new_session_name = st.text_input("اسم الجلسة", value="جلسة جديدة", key="new_sess_name")
        if st.button("إنشاء جلسة", use_container_width=True):
            sid = storage.new_session_id()
            storage.save_session(sid, {
                "name": new_session_name,
                "messages": [],
                "persona": persona,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            st.session_state.current_sid = sid
            st.session_state.current_msgs = []
            st.session_state.active_nav = "chat"
            st.rerun()

    # صفحة تحليل 18
    elif nav == "analysis":
        st.markdown("<div class='section-title'>📊 تحليل 18 محوراً قانونياً</div>", unsafe_allow_html=True)
        st.markdown("""
        **نظام تحليل متكامل** يقسم قضيتك إلى 18 زاوية قانونية، كل زاوية يتم تحليلها بشكل مستقل،
        ثم يتم جمع النتائج في **إجماع نهائي** شامل.
        """)
        case_text = st.text_area("ادخل تفاصيل قضيتك:", height=200, placeholder="صف قضيتك بشكل مفصل...", key="analysis_input")
        if st.button("🔍 بدأ التحليل", use_container_width=True):
            if not case_text.strip():
                st.warning("الرجاء إدخال تفاصيل القضية.")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                def update_progress(current, total, axis_name):
                    progress = int((current / total) * 100)
                    progress_bar.progress(progress)
                    status_text.text(f"جاري تحليل: {axis_name} ({current}/{total})")
                with st.spinner("جاري التحليل..."):
                    analysis_result = analysis_engine.run_full_analysis(case_text, ai_call, update_progress)
                progress_bar.empty()
                status_text.empty()
                st.success("✅ تم التحليل بنجاح!")
                st.markdown("### 🎯 الإجماع النهائي")
                st.markdown(f"<div class='card'>{analysis_result['consensus']}</div>", unsafe_allow_html=True)
                st.markdown("### 📋 تحليل المحاور")
                for axis in analysis_result['axes']:
                    with st.expander(f"{axis['icon']} {axis['name']}"):
                        st.markdown(axis['answer'])

    # صفحة القضايا
    elif nav == "cases":
        st.markdown("<div class='section-title'>📁 إدارة القضايا</div>", unsafe_allow_html=True)
        cases = storage.list_cases()
        if cases:
            st.markdown("### القضايا المفتوحة")
            for case in cases:
                with st.expander(f"📋 {case['title']} — {case['status']}"):
                    st.markdown(f"**المعرف:** `{case['id']}`")
                    st.markdown(f"**التاريخ:** {case.get('created_at', 'مجهول')}")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button(f"فتح", key=f"open_case_{case['id']}"):
                            st.session_state.current_case = case['id']
                            st.rerun()
                    with col2:
                        if st.button(f"تحديث", key=f"update_case_{case['id']}"):
                            st.session_state.editing_case = case['id']
                            st.rerun()
                    with col3:
                        if st.button(f"حذف", key=f"del_case_{case['id']}"):
                            storage.delete_case(case['id'])
                            st.rerun()
        else:
            st.info("لا توجد قضايا مفتوحة.")
        st.markdown("---")
        st.markdown("### إنشاء قضية جديدة")
        case_title = st.text_input("عنوان القضية", key="new_case_title")
        case_description = st.text_area("وصف القضية", key="new_case_desc")
        if st.button("إنشاء قضية", use_container_width=True):
            if not case_title.strip():
                st.warning("الرجاء إدخال عنوان للقضية.")
            else:
                case_id = storage.create_case({
                    "title": case_title,
                    "description": case_description,
                    "status": "مفتوحة",
                    "persona": persona
                })
                st.session_state.current_case = case_id
                st.success(f"✅ تم إنشاء القضية: {case_id}")
                st.rerun()

    # تغيير الشخصية
    elif nav == "switch":
        st.session_state.persona = None
        st.session_state.active_nav = "chat"
        st.session_state.current_sid = None
        st.session_state.current_msgs = []
        st.rerun()