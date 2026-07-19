# ui.py - الواجهة الاحترافية لمنصة FÜHRER
import streamlit as st
from datetime import datetime
import api
import tools
import storage
import legal_tools
from legal_tools_advanced import entitlements_calculator, deadlines_tracker, slip_detector, case_analyzer, legal_classifier

def render_persona_selection():
    st.markdown("<h2 style='text-align:center;color:#c9a84c;margin-bottom:10px;'>مرحباً بك في المنصة القانونية</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#aaaaaa;margin-bottom:40px;'>يرجى اختيار التخصص المطلوب لبدء الجلسة الاستشارية</p>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class='persona-card'>
            <div class='pc-icon'>⚖️</div>
            <div class='pc-title'>المحامي والمستشار القانوني</div>
            <div class='pc-sub'>متخصص في الترافع، صياغة المذكرات، والتحليل الاستراتيجي للقضايا العمالية.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("بدء بصفتي محامي", key="btn_lawyer", use_container_width=True):
            select_persona("lawyer")

    with col2:
        st.markdown("""
        <div class='persona-card'>
            <div class='pc-icon'>💼</div>
            <div class='pc-title'>المستشار العمالي</div>
            <div class='pc-sub'>خبير في الامتثال، التسويات الودية، وحساب المستحقات المالية العمالية.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("بدء بصفتي مستشار", key="btn_advisor", use_container_width=True):
            select_persona("advisor")

def select_persona(pid):
    st.session_state.persona = pid
    st.session_state.active_nav = "chat"
    name = legal_tools.get_persona_display_name(pid)
    sid = storage.new_session_id()
    st.session_state.current_sid = sid
    st.session_state.current_msgs = []
    storage.save_session(sid, {"name": f"استشارة {name}", "messages": [], "persona": pid})
    st.rerun()

def render_nav_bar():
    nav_items = [
        ("💬 المحادثة الاستشارية", "chat"),
        ("📋 سجل الجلسات", "sessions"),
        ("📊 التحليل القانوني المعمق", "analysis"),
        ("📁 أرشيف القضايا", "cases"),
        ("🔄 تغيير التخصص", "switch"),
    ]
    
    cols = st.columns(len(nav_items))
    for col, (label, key) in zip(cols, nav_items):
        with col:
            is_active = st.session_state.active_nav == key
            btn_label = f"**{label}**" if is_active else label
            if st.button(btn_label, key=f"nav_{key}", use_container_width=True, type="secondary" if not is_active else "primary"):
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
    name = legal_tools.get_persona_display_name(persona)
    icon = "⚖️" if persona == "lawyer" else "💼"
    st.markdown(f"""
    <div style='text-align:center; margin-bottom:20px;'>
        <span style='background:#2c2c2e; border:1px solid #c9a84c; color:#c9a84c; padding:5px 20px; border-radius:20px; font-weight:700;'>
            {icon} {name}
        </span>
    </div>
    """, unsafe_allow_html=True)

def render_chat():
    chat_col, tool_col = st.columns([3, 1])
    
    with tool_col:
        st.markdown("<div class='section-title'>🛠️ أدوات التخصص</div>", unsafe_allow_html=True)
        tools_list = legal_tools.get_tools_for_persona(st.session_state.persona)
        for icon, name, tool_id in tools_list:
            if st.button(f"{icon} {name}", key=f"tool_{tool_id}", use_container_width=True):
                st.session_state.selected_tool = tool_id
                st.session_state.active_nav = "tool_exec"
                st.rerun()
        
        st.markdown("<div class='section-title'>📄 المستندات</div>", unsafe_allow_html=True)
        if st.session_state.docs_text:
            st.success(f"تم تحميل {len(st.session_state.docs_text)} مستند")
        else:
            st.info("لا توجد مستندات نشطة")

    with chat_col:
        if st.session_state.current_sid:
            sess_data = storage.load_session(st.session_state.current_sid)
            
            for msg in st.session_state.current_msgs:
                if msg["role"] == "user":
                    st.markdown(f"<div class='bubble-user'>{msg['content']}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='bubble-ai'>{msg['content']}</div>", unsafe_allow_html=True)
            
            user_input = st.text_area("", placeholder="اطلب استشارة أو حلل واقعة قانونية...", label_visibility="collapsed", key="chat_input")
            
            c1, c2 = st.columns([4, 1])
            with c1:
                if st.button("🚀 إرسال الاستشارة", use_container_width=True, type="primary"):
                    if user_input.strip():
                        process_chat(user_input, sess_data)
            with c2:
                if st.button("🗑️", use_container_width=True):
                    st.session_state.current_msgs = []
                    sess_data["messages"] = []
                    storage.save_session(st.session_state.current_sid, sess_data)
                    st.rerun()

def process_chat(user_input, sess_data):
    ts = datetime.now().strftime("%H:%M")
    st.session_state.current_msgs.append({"role": "user", "content": user_input.strip(), "ts": ts})
    
    system_p = legal_tools.get_persona_prompt(st.session_state.persona)
    from analysis_engine import LAW_BRAIN_SYSTEM
    system_p = LAW_BRAIN_SYSTEM + "\n\n" + system_p
    
    if st.session_state.docs_text:
        context = "\n\n".join(st.session_state.docs_text[:3])
        system_p += f"\n\nالوثائق القانونية المرفقة:\n{context[:3000]}"
    
    with st.spinner("جاري التحليل القانوني..."):
        resp = api.ai_call(user_input.strip(), st.session_state.current_msgs[:-1], system_p)
    
    st.session_state.current_msgs.append({"role": "assistant", "content": resp, "ts": ts})
    sess_data["messages"] = st.session_state.current_msgs
    storage.save_session(st.session_state.current_sid, sess_data)
    st.rerun()

def render_tool_execution():
    st.markdown(f"<div class='section-title'>🛠️ تشغيل الأداة: {st.session_state.selected_tool}</div>", unsafe_allow_html=True)
    
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
    elif tool_id == "litigation":
        tools.run_litigation_center()
    
    if st.button("⬅️ العودة للمحادثة", use_container_width=True):
        st.session_state.selected_tool = None
        st.session_state.active_nav = "chat"
        st.rerun()

def render_sessions():
    st.markdown("<div class='section-title'>📋 سجل الجلسات الاستشارية</div>", unsafe_allow_html=True)
    sessions = storage.list_sessions()
    if not sessions:
        st.info("لا توجد جلسات سابقة.")
        return
    
    for sid in sessions:
        data = storage.load_session(sid)
        name = data.get("name", sid)
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(f"📄 {name}", key=f"sess_{sid}", use_container_width=True):
                st.session_state.current_sid = sid
                st.session_state.current_msgs = data.get("messages", [])
                st.session_state.persona = data.get("persona", "lawyer")
                st.session_state.active_nav = "chat"
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{sid}", use_container_width=True):
                storage.delete_session(sid)
                st.rerun()

def render_analysis():
    st.markdown("<div class='section-title'>📊 التحليل القانوني المعمق (18 محوراً)</div>", unsafe_allow_html=True)
    case_text = st.text_area("أدخل وقائع القضية للتحليل الشامل:", height=200)
    if st.button("بدء التحليل الاستراتيجي", type="primary"):
        if case_text:
            import analysis_engine
            with st.spinner("جاري تشغيل محاور التحليل الـ 18..."):
                res = analysis_engine.run_full_analysis(case_text, api.ai_call)
                st.markdown("### 🏆 الإجماع القانوني النهائي")
                st.write(res["consensus"])
                for axis in res["axes"]:
                    with st.expander(f"{axis['icon']} {axis['name']}"):
                        st.write(axis["answer"])

def render_cases():
    st.markdown("<div class='section-title'>📁 أرشيف القضايا الموثقة</div>", unsafe_allow_html=True)
    cases = storage.list_cases()
    if not cases:
        st.info("لا توجد قضايا مؤرشفة.")
        return
    for cid in cases:
        data = storage.load_case(cid)
        with st.expander(f"💼 قضية: {data.get('title', cid)}"):
            st.write(data.get("content", ""))
            if st.button("حذف القضية", key=f"del_case_{cid}"):
                storage.delete_case(cid)
                st.rerun()
