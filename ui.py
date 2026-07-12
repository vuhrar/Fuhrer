# ui.py
import streamlit as st
from datetime import datetime
import api
import tools
import storage
import legal_tools
from legal_tools_advanced import entitlements_calculator, deadlines_tracker, slip_detector, case_analyzer, legal_classifier

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;900&display=swap');
*, *::before, *::after { box-sizing: border-box !important; font-family: 'Tajawal', sans-serif !important; }
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"],
[data-testid="stBottom"], section[data-testid="stSidebar"] {
  background-color: #1c1c1e !important; color: #ffffff !important; direction: rtl !important;
}
[data-testid="stSidebar"], [data-testid="collapsedControl"], #MainMenu, footer, header { display: none !important; }
.main .block-container { max-width: 800px !important; padding: 0 16px 80px !important; margin: 0 auto !important; }
.app-title {
  text-align: center; padding: 40px 0 10px; font-size: 6.4rem; font-weight: 900;
  background: linear-gradient(135deg, #ffffff, #4a9eff);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text; text-shadow: 0 10px 30px rgba(0,0,0,0.4);
  letter-spacing: -0.02em;
}
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
  background: #d1d5db !important; color: #ffffff !important; border: 1.5px solid #9ca3af !important;
  border-radius: 14px !important; font-family: 'Tajawal', sans-serif !important;
  font-size: 0.95rem !important; direction: rtl !important; caret-color: #4a9eff;
  font-weight: 500 !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
  border-color: #c9a84c !important; box-shadow: 0 0 0 2px rgba(201,168,76,0.2) !important;
}
.stSelectbox > div > div, .stNumberInput input {
  background: #d1d5db !important; color: #ffffff !important; border: 1.5px solid #9ca3af !important;
  border-radius: 12px !important;
}
.stTabs [data-baseweb="tab-list"] {
  background: #ffffff !important; border-radius: 12px !important; gap: 4px; padding: 4px;
  border: 1px solid #e5e7eb !important;
}
.stTabs [data-baseweb="tab"]  { background: transparent !important; color: #4b5563 !important; border-radius: 8px !important; }
.stTabs [aria-selected="true"] { background: #4a9eff !important; color: #ffffff !important; }
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
"""

def render_persona_selection():
    st.markdown("<p class='sub-text' style='text-align:center;margin-bottom:16px;'>اختر الشخصية التي تناسب حاجتك</p>", unsafe_allow_html=True)

    personas = [
        ("lawyer",  "👨‍⚖️", "المحامي",    "هجومي — يكتب الدعاوى والحجج الدفاعية"),
        ("advisor", "👩‍💼", "المستشار",  "تحليلي — يحسب المستحقات ويوجه"),
        ("worker",  "👷", "العامل",    "حماية الحقوق — يدافع عن حقوق العامل"),
        ("judge",   "⚖️",   "القاضي",    "حيادي — يحلّل ويطبّق مواد النظام"),
    ]

    c1, c2 = st.columns(2)
    for idx, (pid, icon, name, desc) in enumerate(personas):
        col = c1 if idx % 2 == 0 else c2
        with col:
            if st.button(f"{icon} {name}\n\n{desc}", key=f"pick_{pid}", use_container_width=True):
                st.session_state.persona = pid
                st.session_state.active_nav = "chat"
                if not st.session_state.current_sid:
                    sid = storage.new_session_id()
                    st.session_state.current_sid = sid
                    st.session_state.current_msgs = []
                    storage.save_session(sid, {"name": f"جلسة {name}", "messages": [], "persona": pid})
                st.rerun()

def render_nav_bar():
    nav_items = [
        ("💬 المحادثة", "chat"),
        ("🔧 الأدوات", "tools"),
        ("📋 الجلسات", "sessions"),
        ("📊 تحليل 18", "analysis"),
        ("📁 القضايا", "cases"),
        ("🔄 تغيير", "switch"),
    ]
    cols = st.columns(len(nav_items))
    for col, (label, key) in zip(cols, nav_items):
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

def render_persona_badge():
    persona = st.session_state.persona
    _map = {
        "lawyer":  ("👨‍⚖️", "المحامي",   "#c9a84c"),
        "advisor": ("👩‍💼", "المستشار", "#4a9eff"),
        "worker":  ("👷",   "العامل",   "#4ade80"),
        "judge":   ("⚖️",   "القاضي",   "#a78bfa"),
    }
    persona_icon, persona_label, color = _map.get(persona, ("👤", persona, "#888"))
    st.markdown(f"""<div style='text-align:center;margin:6px 0 16px;'>
        <span style='font-size:0.82rem;color:{color};font-weight:700;
                       border:1px solid {color};border-radius:20px;
                       padding:4px 14px;'>
        {persona_icon} {persona_label}
        </span>
    </div>""", unsafe_allow_html=True)

def render_chat():
    if st.session_state.current_sid:
        sess_data = storage.load_session(st.session_state.current_sid)
        ai_cls = "bubble-ai adv" if st.session_state.persona == "advisor" else "bubble-ai"
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
            system_p = legal_tools.PERSONA_PROMPTS[st.session_state.persona]
            if st.session_state.docs_text:
                context = "\n\n".join(st.session_state.docs_text[:3])
                system_p += f"\n\nالوثائق المحملة:\n{context[:3000]}"
            with st.spinner("جارٍ التحليل..."):
                resp = api.ai_call(user_input.strip(), st.session_state.current_msgs[:-1], system_p)
            st.session_state.current_msgs.append(
                {"role": "assistant", "content": resp, "ts": ts})
            sess_data["messages"] = st.session_state.current_msgs
            sess_data["persona"] = st.session_state.persona
            storage.save_session(st.session_state.current_sid, sess_data)
            st.rerun()
    else:
        st.markdown("<p class='sub-text' style='text-align:center;margin-top:30px;'>"
                    "لا توجد جلسة نشطة — افتح جلسة جديدة من قسم الجلسات</p>",
                    unsafe_allow_html=True)

def render_tools():
    st.markdown("<div class='section-title'>🔧 الأدوات القانونية المتقدمة</div>", unsafe_allow_html=True)
    tools_list = legal_tools.get_tools_for_persona(st.session_state.persona)
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
            tools.run_calculator()
        elif tool_id == "law_search":
            tools.run_law_search()
        elif tool_id == "email_scan":
            tools.run_email_scan()
        elif tool_id == "case_strength":
            tools.run_case_strength()
        elif tool_id == "settlement":
            tools.run_settlement()
        elif tool_id == "extractor":
            tools.run_info_extractor()
        if st.button("⬅️ العودة إلى قائمة الأدوات", use_container_width=True):
            st.session_state.selected_tool = None
            st.rerun()

def render_sessions():
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
            "persona": st.session_state.persona,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        st.session_state.current_sid = sid
        st.session_state.current_msgs = []
        st.session_state.active_nav = "chat"
        st.rerun()

def render_analysis():
    import analysis_engine
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
                analysis_result = analysis_engine.run_full_analysis(case_text, api.ai_call, update_progress)
            progress_bar.empty()
            status_text.empty()
            st.success("✅ تم التحليل بنجاح!")
            st.markdown("### 🎯 الإجماع النهائي")
            st.markdown(f"<div class='card'>{analysis_result['consensus']}</div>", unsafe_allow_html=True)
            st.markdown("### 📋 تحليل المحاور")
            for axis in analysis_result['axes']:
                with st.expander(f"{axis['icon']} {axis['name']}"):
                    st.markdown(axis['answer'])

def render_cases():
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
                "persona": st.session_state.persona
            })
            st.session_state.current_case = case_id
            st.success(f"✅ تم إنشاء القضية: {case_id}")
            st.rerun()
