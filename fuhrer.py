# fuhrer.py - المنصة القانونية الاحترافية الموحدة
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

import ai_engine, analysis_engine, legal_tools, file_processing, storage, api, tools, styles

st.set_page_config(page_title="FÜHRER — المنصة القانونية الاحترافية", page_icon="⚖️", layout="wide", initial_sidebar_state="collapsed")
st.markdown(styles.MAIN_CSS, unsafe_allow_html=True)

_saved = storage.load_settings()
_defaults = {
    "persona": None, "active_nav": "chat", "current_sid": None, "current_msgs": [],
    "docs_text": [], "preset_name": _saved.get("preset_name", "Groq LLaMA 3.3 70B 🚀 (مجاني)"),
    "api_key": _saved.get("api_key", ""), "custom_url": _saved.get("custom_url", ""),
    "custom_model": _saved.get("custom_model", ""), "custom_fmt": _saved.get("custom_fmt", "openai"),
    "show_panel": None, "selected_tool": None, "connection_status": "unknown", "connection_msg": "",
}
for k, v in _defaults.items():
    if k not in st.session_state: st.session_state[k] = v

# ── شريط الحالة ──
status_col, corner_col = st.columns([10, 1])
with status_col:
    if st.session_state.get("connection_status") == "connected": st.markdown("🟢 النظام متصل")
    elif st.session_state.get("connection_status") == "failed": st.markdown("🔴 خطأ في الربط")
with corner_col:
    if st.button("⚙️", key="settings_icon"):
        st.session_state.show_panel = None if st.session_state.show_panel == "full" else "full"
        st.rerun()

# ── لوحة الإعدادات ──
if st.session_state.show_panel == "full":
    with st.container():
        st.markdown("<div class='section-title'>⚙️ إعدادات المنصة والربط التقني</div>", unsafe_allow_html=True)
        t1, t2, t3 = st.tabs(["الربط مع الخادم", "المستندات القانونية", "إدارة النظام"])
        with t1:
            preset_keys = list(ai_engine.PRESETS.keys())
            current_idx = preset_keys.index(st.session_state.preset_name) if st.session_state.preset_name in preset_keys else 0
            st.session_state.preset_name = st.selectbox("🤖 مزود الذكاء الاصطناعي", preset_keys, index=current_idx)
            selected = ai_engine.PRESETS[st.session_state.preset_name]
            is_local = "Führer" in st.session_state.preset_name and "محلي" in st.session_state.preset_name
            badge = "🟢 مجاني" if selected.free else "🔵 مدفوع"
            st.markdown(f"<div style='background:#2c2c2e;padding:12px;border-radius:8px;margin:6px 0;'><b>{selected.name}</b> {badge}<br><span style='color:#94a3b8;'>{selected.description}</span><br><code>{selected.url or 'localhost'}</code></div>", unsafe_allow_html=True)
            if is_local: st.info("🧠 Führer Law Brain — حمّل LM Studio وشغّل النموذج على المنفذ 1234")
            col_a, col_b = st.columns(2)
            with col_a:
                if not is_local: st.session_state.api_key = st.text_input("مفتاح API", value=st.session_state.api_key, type="password")
            with col_b:
                if "مخصص" in st.session_state.preset_name:
                    st.session_state.custom_url = st.text_input("رابط API", value=st.session_state.custom_url)
                    st.session_state.custom_model = st.text_input("اسم النموذج", value=st.session_state.custom_model)
            if st.button("🔌 اختبار وتفعيل الربط", use_container_width=True):
                with st.spinner("جاري التحقق..."):
                    ok, msg = ai_engine.test_connection(st.session_state.preset_name, st.session_state.api_key, st.session_state.custom_url, st.session_state.custom_model, st.session_state.custom_fmt)
                    st.session_state.connection_status = "connected" if ok else "failed"
                    if ok: storage.save_settings({"preset_name": st.session_state.preset_name, "api_key": st.session_state.api_key})
                    st.rerun()
        with t2:
            new_docs = file_processing.render_file_upload_widget()
            if new_docs: st.session_state.docs_text = new_docs; st.success(f"✅ تم دمج {len(new_docs)} مستند")
            if st.session_state.docs_text:
                if st.button("🗑️ إفراغ ذاكرة المستندات"): st.session_state.docs_text = []; st.rerun()
        with t3:
            if st.button("⚠️ مسح شامل لجميع البيانات المؤقتة", use_container_width=True):
                storage.clear_all_sessions(); st.session_state.current_sid = None; st.session_state.current_msgs = []; st.rerun()
    st.markdown("---")

# ── العنوان الرئيسي ──
st.markdown("<div class='app-title'>FÜHRER</div>", unsafe_allow_html=True)

# ── اختيار الشخصية ──
def select_persona(pid):
    st.session_state.persona = pid; st.session_state.active_nav = "chat"
    name = legal_tools.get_persona_display_name(pid)
    sid = storage.new_session_id(); st.session_state.current_sid = sid; st.session_state.current_msgs = []
    storage.save_session(sid, {"name": f"استشارة {name}", "messages": [], "persona": pid})
    st.rerun()

if st.session_state.persona is None:
    st.markdown("<h2 style='text-align:center;color:#c9a84c;'>مرحباً بك في المنصة القانونية</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#aaaaaa;margin-bottom:40px;'>يرجى اختيار التخصص المطلوب</p>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='persona-card'><div class='pc-icon'>⚖️</div><div class='pc-title'>المحامي والمستشار القانوني</div><div class='pc-sub'>متخصص في الترافع، صياغة المذكرات، والتحليل الاستراتيجي للقضايا العمالية.</div></div>", unsafe_allow_html=True)
        if st.button("بدء بصفتي محامي", key="btn_lawyer", use_container_width=True): select_persona("lawyer")
    with col2:
        st.markdown("<div class='persona-card'><div class='pc-icon'>💼</div><div class='pc-title'>المستشار العمالي</div><div class='pc-sub'>خبير في الامتثال، التسويات الودية، وحساب المستحقات المالية العمالية.</div></div>", unsafe_allow_html=True)
        if st.button("بدء بصفتي مستشار", key="btn_advisor", use_container_width=True): select_persona("advisor")

else:
    # ── شريط التنقل ──
    nav_items = [("💬 المحادثة", "chat"), ("📋 الجلسات", "sessions"), ("📊 التحليل", "analysis"), ("📁 القضايا", "cases"), ("🔄 تغيير", "switch")]
    cols = st.columns(len(nav_items))
    for col, (label, key) in zip(cols, nav_items):
        with col:
            is_active = st.session_state.active_nav == key
            if st.button(f"**{label}**" if is_active else label, key=f"nav_{key}", use_container_width=True, type="secondary" if not is_active else "primary"):
                if key == "switch": st.session_state.persona = None; st.session_state.active_nav = "chat"; st.session_state.current_sid = None; st.session_state.current_msgs = []
                else: st.session_state.active_nav = key
                st.rerun()

    # ── شارة الشخصية ──
    persona = st.session_state.persona
    name = legal_tools.get_persona_display_name(persona)
    icon = "⚖️" if persona == "lawyer" else "💼"
    st.markdown(f"<div style='text-align:center;margin-bottom:20px;'><span style='background:#2c2c2e;border:1px solid #c9a84c;color:#c9a84c;padding:5px 20px;border-radius:20px;font-weight:700;'>{icon} {name}</span></div>", unsafe_allow_html=True)

    nav = st.session_state.active_nav

    if nav == "chat":
        chat_col, tool_col = st.columns([3, 1])
        with tool_col:
            st.markdown("<div class='section-title'>🛠️ أدوات التخصص</div>", unsafe_allow_html=True)
            for icon_t, tname, tid in legal_tools.get_tools_for_persona(st.session_state.persona):
                if st.button(f"{icon_t} {tname}", key=f"tool_{tid}", use_container_width=True):
                    st.session_state.selected_tool = tid; st.session_state.active_nav = "tool_exec"; st.rerun()
            st.markdown("<div class='section-title'>📄 المستندات</div>", unsafe_allow_html=True)
            if st.session_state.docs_text: st.success(f"✅ {len(st.session_state.docs_text)} مستند")
            else: st.info("لا توجد مستندات")
        with chat_col:
            if st.session_state.current_sid:
                for msg in st.session_state.current_msgs:
                    if msg["role"] == "user": st.markdown(f"<div class='bubble-user'>{msg['content']}</div>", unsafe_allow_html=True)
                    else: st.markdown(f"<div class='bubble-ai'>{msg['content']}</div>", unsafe_allow_html=True)
                user_input = st.text_area("", placeholder="اطلب استشارة أو حلل واقعة قانونية...", label_visibility="collapsed", key="chat_input")
                c1, c2 = st.columns([4, 1])
                with c1:
                    if st.button("🚀 إرسال", use_container_width=True, type="primary"):
                        if user_input.strip():
                            sess_data = storage.load_session(st.session_state.current_sid)
                            ts = datetime.now().strftime("%H:%M")
                            st.session_state.current_msgs.append({"role": "user", "content": user_input.strip(), "ts": ts})
                            system_p = legal_tools.get_persona_prompt(st.session_state.persona)
                            from analysis_engine import LAW_BRAIN_SYSTEM
                            system_p = LAW_BRAIN_SYSTEM + "\n\n" + system_p
                            if st.session_state.docs_text:
                                system_p += f"\n\nالوثائق المرفقة:\n" + "\n\n".join(st.session_state.docs_text[:3])[:3000]
                            with st.spinner("جاري التحليل..."):
                                resp = api.ai_call(user_input.strip(), st.session_state.current_msgs[:-1], system_p)
                            st.session_state.current_msgs.append({"role": "assistant", "content": resp, "ts": ts})
                            sess_data["messages"] = st.session_state.current_msgs
                            storage.save_session(st.session_state.current_sid, sess_data)
                            st.rerun()
                with c2:
                    if st.button("🗑️", use_container_width=True):
                        st.session_state.current_msgs = []
                        sd = storage.load_session(st.session_state.current_sid)
                        sd["messages"] = []
                        storage.save_session(st.session_state.current_sid, sd)
                        st.rerun()

    elif nav == "tool_exec":
        tool_id = st.session_state.selected_tool
        if tool_id == "calculator": tools.run_calculator()
        elif tool_id == "law_search": tools.run_law_search()
        elif tool_id == "email_scan": tools.run_email_scan()
        elif tool_id == "case_strength": tools.run_case_strength()
        elif tool_id == "settlement": tools.run_settlement()
        elif tool_id == "extractor": tools.run_info_extractor()
        elif tool_id == "litigation": tools.run_litigation_center()
        if st.button("⬅️ العودة للمحادثة", use_container_width=True):
            st.session_state.selected_tool = None; st.session_state.active_nav = "chat"; st.rerun()

    elif nav == "sessions":
        st.markdown("<div class='section-title'>📋 سجل الجلسات</div>", unsafe_allow_html=True)
        sessions = storage.list_sessions()
        if not sessions: st.info("لا توجد جلسات سابقة.")
        for sid in sessions:
            data = storage.load_session(sid)
            c1, c2 = st.columns([4, 1])
            with c1:
                if st.button(f"📄 {data.get('name', sid)}", key=f"sess_{sid}", use_container_width=True):
                    st.session_state.current_sid = sid; st.session_state.current_msgs = data.get("messages", [])
                    st.session_state.persona = data.get("persona", "lawyer"); st.session_state.active_nav = "chat"; st.rerun()
            with c2:
                if st.button("🗑️", key=f"del_{sid}", use_container_width=True): storage.delete_session(sid); st.rerun()

    elif nav == "analysis":
        st.markdown("<div class='section-title'>📊 التحليل القانوني المعمق (18 محوراً)</div>", unsafe_allow_html=True)
        case_text = st.text_area("أدخل وقائع القضية للتحليل الشامل:", height=200)
        if st.button("بدء التحليل الاستراتيجي", type="primary"):
            if case_text:
                with st.spinner("جاري تشغيل محاور التحليل الـ 18..."):
                    res = analysis_engine.run_full_analysis(case_text, api.ai_call)
                    st.markdown("### 🏆 الإجماع القانوني النهائي")
                    st.write(res["consensus"])
                    for axis in res["axes"]:
                        with st.expander(f"{axis['icon']} {axis['name']}"): st.write(axis["answer"])

    elif nav == "cases":
        st.markdown("<div class='section-title'>📁 أرشيف القضايا</div>", unsafe_allow_html=True)
        cases = storage.list_cases()
        if not cases: st.info("لا توجد قضايا مؤرشفة.")
        for cid in cases:
            data = storage.load_case(cid)
            with st.expander(f"💼 {data.get('title', cid)}"):
                st.write(data.get("content", ""))
                if st.button("حذف", key=f"del_case_{cid}"): storage.delete_case(cid); st.rerun()
