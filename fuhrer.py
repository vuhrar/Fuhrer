import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from datetime import datetime
import ai_engine, analysis_engine, legal_tools, file_processing, storage

st.set_page_config(page_title="Führer", page_icon="⚖️",
                   layout="centered", initial_sidebar_state="collapsed")

# ══════════════════════════════════════════════
# CSS — رصاصي غامق، نص أبيض، حواف ذهبية، بلا sidebar
# ══════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;900&display=swap');

*, *::before, *::after {
  box-sizing: border-box !important;
  font-family: 'Tajawal', sans-serif !important;
}

/* خلفية رصاصية غامقة كاملة */
html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
[data-testid="stBottom"],
section[data-testid="stSidebar"] {
  background-color: #1c1c1e !important;
  color: #ffffff !important;
  direction: rtl !important;
}

/* إخفاء sidebar وعناصر streamlit الزائدة */
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
#MainMenu, footer, header { display: none !important; }

.main .block-container {
  max-width: 700px !important;
  padding: 0 16px 80px !important;
  margin: 0 auto !important;
}

/* ── اسم التطبيق ── */
.app-title {
  text-align: center;
  padding: 32px 0 8px;
  font-size: 3.2rem;
  font-weight: 900;
  color: #ffffff;
  letter-spacing: 0.04em;
}

/* ── زر الإعدادات — زاوية يمين أعلى ── */
.settings-corner {
  position: fixed;
  top: 12px;
  right: 12px;
  z-index: 9999;
}

/* ── المربعان الرئيسيان (محامي / مستشار) ── */
.persona-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin: 24px 0 8px;
}
.persona-card {
  background: #2c2c2e;
  border: 2px solid #c9a84c;
  border-radius: 18px;
  padding: 28px 16px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}
.persona-card.active {
  background: #3a3020;
  border-color: #f0c040;
  box-shadow: 0 0 0 3px rgba(201,168,76,0.3);
}
.persona-card .pc-title {
  font-size: 1.25rem;
  font-weight: 800;
  color: #ffffff;
  margin: 10px 0 6px;
}
.persona-card .pc-sub {
  font-size: 0.78rem;
  color: #aaaaaa;
  line-height: 1.5;
}
.persona-card .pc-icon {
  font-size: 2rem;
}

/* ── شريط التنقل العلوي (يظهر بعد اختيار شخصية) ── */
.nav-bar {
  display: flex;
  gap: 8px;
  margin: 16px 0 4px;
  overflow-x: auto;
  padding-bottom: 4px;
}
.nav-bar::-webkit-scrollbar { height: 0; }

/* ── أدوات ── */
.tools-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin: 10px 0;
}

/* ── أزرار streamlit — إعادة تصميم كاملة ── */
.stButton > button {
  background: #2c2c2e !important;
  color: #ffffff !important;
  border: 1.5px solid #c9a84c !important;
  border-radius: 14px !important;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
  font-family: 'Tajawal', sans-serif !important;
  padding: 12px 18px !important;
  width: 100% !important;
  transition: all 0.18s !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}
.stButton > button:hover {
  background: #3a3020 !important;
  border-color: #f0c040 !important;
  color: #f0c040 !important;
}
.stButton > button:focus {
  box-shadow: 0 0 0 3px rgba(201,168,76,0.25) !important;
}

/* زر الإرسال — مميز */
.send-btn .stButton > button {
  background: linear-gradient(135deg, #c9a84c, #a8882e) !important;
  color: #1c1c1e !important;
  border-color: transparent !important;
  font-size: 1rem !important;
  padding: 14px !important;
}

/* ── فقاعات الدردشة ── */
.bubble-wrap { margin: 6px 0; }
.bubble-user {
  background: #2c3e50;
  border: 1px solid #3a5068;
  border-radius: 18px 18px 4px 18px;
  padding: 12px 16px;
  margin-right: 10%;
  color: #ffffff !important;
  font-size: 0.95rem;
  line-height: 1.75;
  word-wrap: break-word;
}
.bubble-ai {
  background: #2c2c2e;
  border: 1px solid #3a3a3c;
  border-right: 3px solid #c9a84c;
  border-radius: 18px 18px 18px 4px;
  padding: 12px 16px;
  margin-left: 10%;
  color: #ffffff !important;
  font-size: 0.95rem;
  line-height: 1.8;
  word-wrap: break-word;
}
.bubble-ai.adv { border-right-color: #4a9eff; }
.bubble-time {
  font-size: 0.68rem;
  color: #666 !important;
  margin-top: 4px;
  text-align: left;
}

/* ── حقول الإدخال ── */
.stTextArea textarea, .stTextInput input {
  background: #2c2c2e !important;
  color: #ffffff !important;
  border: 1.5px solid #3a3a3c !important;
  border-radius: 14px !important;
  font-family: 'Tajawal', sans-serif !important;
  font-size: 0.95rem !important;
  direction: rtl !important;
  caret-color: #c9a84c;
}
.stTextArea textarea:focus, .stTextInput input:focus {
  border-color: #c9a84c !important;
  box-shadow: 0 0 0 2px rgba(201,168,76,0.2) !important;
}
.stSelectbox > div > div, .stNumberInput input {
  background: #2c2c2e !important;
  color: #ffffff !important;
  border: 1.5px solid #3a3a3c !important;
  border-radius: 12px !important;
}

/* ── بطاقات ونتائج ── */
.card {
  background: #2c2c2e;
  border: 1px solid #3a3a3c;
  border-right: 3px solid #c9a84c;
  border-radius: 14px;
  padding: 14px 18px;
  margin: 8px 0;
  color: #ffffff !important;
}
.card.blue { border-right-color: #4a9eff; }
.card.ok   { border-right-color: #4ade80; }
.card.red  { border-right-color: #ff5a5a; }

.alert {
  border-radius: 12px;
  padding: 10px 14px;
  margin: 6px 0;
  font-size: 0.88rem;
  line-height: 1.6;
  color: #ffffff !important;
}
.alert.warn   { background: rgba(255,180,0,0.1);   border-right: 3px solid #ffb400; }
.alert.danger { background: rgba(255,90,90,0.1);   border-right: 3px solid #ff5a5a; }
.alert.ok     { background: rgba(74,222,128,0.1);  border-right: 3px solid #4ade80; }
.alert.info   { background: rgba(74,158,255,0.1);  border-right: 3px solid #4a9eff; }

.stat-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin: 12px 0;
}
.stat-box {
  background: #2c2c2e;
  border: 1.5px solid #c9a84c;
  border-radius: 14px;
  padding: 14px;
  text-align: center;
}
.stat-box .v { font-size: 1.4rem; font-weight: 800; color: #c9a84c; }
.stat-box .l { font-size: 0.72rem; color: #aaaaaa; margin-top: 3px; }

/* ── شريط تقدم ── */
.stProgress > div > div > div {
  background: linear-gradient(90deg, #c9a84c, #f0c040) !important;
  border-radius: 4px !important;
}

/* ── نص رصاصي فاتح للشروحات ── */
.sub-text { color: #aaaaaa !important; font-size: 0.85rem; }

/* ── قسم ── */
.section-title {
  font-size: 1.05rem;
  font-weight: 800;
  color: #c9a84c;
  margin: 20px 0 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid #3a3a3c;
}

/* ── expander ── */
.streamlit-expanderHeader {
  background: #2c2c2e !important;
  color: #ffffff !important;
  border-radius: 10px !important;
  border: 1px solid #3a3a3c !important;
}
.streamlit-expanderContent {
  background: #242426 !important;
  border: 1px solid #3a3a3c !important;
  border-radius: 0 0 10px 10px !important;
  color: #ffffff !important;
}

/* ── file uploader ── */
[data-testid="stFileUploader"] {
  background: #2c2c2e !important;
  border: 2px dashed #c9a84c !important;
  border-radius: 14px !important;
}
[data-testid="stFileUploader"] * { color: #ffffff !important; }

/* ── caption / label ── */
.stCaption, label, .stMarkdown p { color: #aaaaaa !important; }

/* موبايل */
@media (max-width: 500px) {
  .app-title { font-size: 2.4rem !important; }
  .persona-card .pc-title { font-size: 1.1rem; }
  .tools-grid { grid-template-columns: 1fr; }
  .stat-grid { grid-template-columns: 1fr; }
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# تهيئة الحالة
# ══════════════════════════════════════════════
_saved = storage.load_settings()
_defaults = {
    "persona":       None,          # None = لم يُختر بعد
    "active_tool":   None,
    "active_nav":    "chat",        # chat | tools | sessions | analysis
    "current_sid":   None,
    "current_msgs":  [],
    "docs_text":     [],
    "preset_name":   _saved.get("preset_name", list(ai_engine.PRESETS.keys())[0]),
    "api_key":       _saved.get("api_key", ""),
    "custom_url":    _saved.get("custom_url", ""),
    "custom_model":  _saved.get("custom_model", ""),
    "custom_fmt":    _saved.get("custom_fmt", "openai"),
    "pending_input": "",
    "show_panel":    None,          # settings | dashboard | connection | None
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


# ══════════════════════════════════════════════
# زر الإعدادات — زاوية يمين أعلى (ثابت)
# ══════════════════════════════════════════════
corner_col = st.columns([8, 1])[1]
with corner_col:
    if st.button("⚙️", key="corner_settings"):
        st.session_state.show_panel = (
            None if st.session_state.show_panel == "settings_full" else "settings_full"
        )
        st.rerun()


# ══════════════════════════════════════════════
# اسم التطبيق — وسط الشاشة، ضعف الحجم الحالي
# ══════════════════════════════════════════════
st.markdown("<div class='app-title'>Führer</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# لوحة الإعدادات الكاملة (تظهر عند ضغط ⚙️)
# ══════════════════════════════════════════════
if st.session_state.show_panel == "settings_full":
    st.markdown("<div class='section-title'>الإعدادات والاتصال</div>", unsafe_allow_html=True)

    tabs = st.tabs(["الاتصال بالخادم", "لوحة التحكم", "بيانات الجلسة"])

    with tabs[0]:
        new_preset = st.selectbox(
            "النموذج",
            list(ai_engine.PRESETS.keys()),
            index=list(ai_engine.PRESETS.keys()).index(st.session_state.preset_name)
                  if st.session_state.preset_name in ai_engine.PRESETS else 0
        )
        st.session_state.preset_name = new_preset

        if new_preset == "⚙️ مخصص":
            st.session_state.custom_url   = st.text_input("رابط API", value=st.session_state.custom_url)
            st.session_state.custom_model = st.text_input("النموذج", value=st.session_state.custom_model)
            st.session_state.custom_fmt   = st.selectbox("الصيغة", ["openai","gemini","anthropic"])

        st.session_state.api_key = st.text_input(
            "مفتاح API", value=st.session_state.api_key,
            type="password", placeholder="AIza... أو sk-..."
        )
        key_ok = bool(st.session_state.api_key.strip())
        col = "#4ade80" if key_ok else "#ff5a5a"
        txt = "متصل" if key_ok else "غير متصل — أدخل مفتاح API"
        st.markdown(f"<div class='alert {'ok' if key_ok else 'danger'}'>{txt}</div>",
                    unsafe_allow_html=True)
        if st.button("حفظ إعدادات الاتصال"):
            storage.save_settings({
                "preset_name": st.session_state.preset_name,
                "custom_url": st.session_state.custom_url,
                "custom_model": st.session_state.custom_model,
                "custom_fmt": st.session_state.custom_fmt,
            })
            st.success("تم الحفظ")

    with tabs[1]:
        sessions = storage.list_sessions()
        st.markdown(f"""
        <div class='stat-grid'>
          <div class='stat-box'><div class='v'>{len(sessions)}</div><div class='l'>الجلسات</div></div>
          <div class='stat-box'><div class='v'>{len(st.session_state.current_msgs)}</div><div class='l'>رسائل الجلسة</div></div>
          <div class='stat-box'><div class='v'>{len(st.session_state.docs_text)}</div><div class='l'>مستندات</div></div>
          <div class='stat-box'><div class='v'>{"نعم" if key_ok else "لا"}</div><div class='l'>API متصل</div></div>
        </div>
        """, unsafe_allow_html=True)

    with tabs[2]:
        if st.button("مسح كل الجلسات المحفوظة"):
            for s in storage.list_sessions():
                storage.delete_session(s["id"])
            st.session_state.current_sid  = None
            st.session_state.current_msgs = []
            st.success("تم المسح")
            st.rerun()

    st.markdown("---")


# ══════════════════════════════════════════════
# شاشة اختيار الشخصية — مربعان فقط بعد الاسم
# ══════════════════════════════════════════════
if st.session_state.persona is None:
    st.markdown("""
    <p class='sub-text' style='text-align:center;margin-bottom:4px;'>
      اختر الشخصية التي تناسب حاجتك
    </p>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("المحامي\n⚖️", key="pick_lawyer", use_container_width=True):
            st.session_state.persona    = "lawyer"
            st.session_state.active_nav = "chat"
            if not st.session_state.current_sid:
                sid = storage.new_session_id()
                st.session_state.current_sid  = sid
                st.session_state.current_msgs = []
                storage.save_session(sid, {"name":"جلسة المحامي","messages":[],"persona":"lawyer"})
            st.rerun()
    with c2:
        if st.button("المستشار\n🧑", key="pick_advisor", use_container_width=True):
            st.session_state.persona    = "advisor"
            st.session_state.active_nav = "chat"
            if not st.session_state.current_sid:
                sid = storage.new_session_id()
                st.session_state.current_sid  = sid
                st.session_state.current_msgs = []
                storage.save_session(sid, {"name":"جلسة المستشار","messages":[],"persona":"advisor"})
            st.rerun()

    st.markdown("""
    <div style='text-align:center;margin-top:40px;'>
      <p class='sub-text'>المحامي — هجومي، يكتب الدعاوى والحجج</p>
      <p class='sub-text'>المستشار — تحليلي، يحسب المستحقات ويوجّه</p>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════
# بعد اختيار الشخصية
# ══════════════════════════════════════════════
else:
    persona = st.session_state.persona
    persona_label = "المحامي" if persona == "lawyer" else "المستشار"

    # ── شريط التنقل الأفقي (زر واحد يفتح قائمة) ──
    nav_cols = st.columns([1,1,1,1,1])

    nav_items = [
        ("المحادثة", "chat"),
        ("الأدوات",  "tools"),
        ("الجلسات",  "sessions"),
        ("تحليل 18", "analysis"),
        ("تغيير",    "switch"),
    ]

    for col, (label, key) in zip(nav_cols, nav_items):
        with col:
            is_active = st.session_state.active_nav == key
            prefix = "← " if is_active else ""
            if st.button(f"{prefix}{label}", key=f"nav_{key}", use_container_width=True):
                if key == "switch":
                    st.session_state.persona    = None
                    st.session_state.active_nav = "chat"
                    st.session_state.current_sid  = None
                    st.session_state.current_msgs = []
                else:
                    st.session_state.active_nav = key
                st.rerun()

    # مؤشر الشخصية النشطة
    color = "#c9a84c" if persona == "lawyer" else "#4a9eff"
    st.markdown(f"""
    <div style='text-align:center;margin:6px 0 16px;'>
      <span style='font-size:0.82rem;color:{color};font-weight:700;
                   border:1px solid {color};border-radius:20px;
                   padding:4px 14px;'>
        {persona_label}
      </span>
    </div>
    """, unsafe_allow_html=True)

    nav = st.session_state.active_nav

    # ════════════════════════════════════
    # صفحة المحادثة
    # ════════════════════════════════════
    if nav == "chat":
        if st.session_state.current_sid:
            sess_data = storage.load_session(st.session_state.current_sid)

            # عرض الرسائل
            ai_cls = "bubble-ai adv" if persona == "advisor" else "bubble-ai"
            for msg in st.session_state.current_msgs:
                content = (msg["content"]
                           .replace("<","&lt;").replace(">","&gt;")
                           .replace("\n","<br>"))
                ts = msg.get("ts","")
                if msg["role"] == "user":
                    st.markdown(
                        f"<div class='bubble-user'>{content}"
                        f"<div class='bubble-time'>{ts}</div></div>",
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        f"<div class='{ai_cls}'>{content}"
                        f"<div class='bubble-time'>{ts}</div></div>",
                        unsafe_allow_html=True)

            # صندوق الإدخال
            pending = st.session_state.get("pending_input","")
            user_input = st.text_area("", value=pending, height=100,
                                       placeholder="اكتب سؤالك القانوني هنا...",
                                       label_visibility="collapsed")
            if pending:
                st.session_state.pending_input = ""

            sc = st.columns([3,1])
            with sc[0]:
                send = st.button("إرسال", key="send_main", use_container_width=True)
            with sc[1]:
                if st.button("مسح", key="clear_main", use_container_width=True):
                    st.session_state.current_msgs = []
                    sess_data["messages"] = []
                    storage.save_session(st.session_state.current_sid, sess_data)
                    st.rerun()

            if send and user_input.strip():
                ts = datetime.now().strftime("%H:%M")
                st.session_state.current_msgs.append(
                    {"role":"user","content":user_input.strip(),"ts":ts})

                system_p = legal_tools.PERSONA_PROMPTS[persona]
                if st.session_state.docs_text:
                    system_p += "\n\nالوثائق:\n" + "\n\n".join(
                        st.session_state.docs_text[:3])[:3000]

                with st.spinner("جارٍ التحليل..."):
                    resp = ai_call(user_input.strip(),
                                   st.session_state.current_msgs[:-1], system_p)

                st.session_state.current_msgs.append(
                    {"role":"assistant","content":resp,"ts":ts})
                sess_data["messages"] = st.session_state.current_msgs
                sess_data["persona"]  = persona
                storage.save_session(st.session_state.current_sid, sess_data)
                st.rerun()
        else:
            st.markdown("<p class='sub-text' style='text-align:center;margin-top:30px;'>لا توجد جلسة نشطة — افتح جلسة جديدة من قسم الجلسات</p>",
                        unsafe_allow_html=True)

    # ════════════════════════════════════
    # صفحة الأدوات
    # ════════════════════════════════════
    elif nav == "tools":
        st.markdown("<div class='section-title'>الأدوات المتخصصة</div>", unsafe_allow_html=True)

        tools_list = legal_tools.TOOLS[persona]
        # عرض الأدوات بشبكة 2×3
        rows = [tools_list[i:i+2] for i in range(0, len(tools_list), 2)]
        for row in rows:
            cols = st.columns(len(row))
            for col, (icon, label, key) in zip(cols, row):
                with col:
                    active = st.session_state.active_tool == key
                    if st.button(label, key=f"t_{key}", use_container_width=True):
                        st.session_state.active_tool = None if active else key
                        st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)

        # محتوى الأداة النشطة
        active_tool = st.session_state.active_tool

        if active_tool == "calculator":
            st.markdown("<div class='section-title'>حاسبة المستحقات</div>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                basic = st.number_input("الراتب الأساسي", min_value=0.0, step=500.0)
                years = st.number_input("سنوات الخدمة", min_value=0.0, step=0.5)
            with c2:
                total   = st.number_input("الراتب الإجمالي", min_value=0.0, step=500.0)
                delay_m = st.number_input("أشهر التأخير", min_value=0, step=1)
            arbitrary = st.checkbox("فصل تعسفي (م.77)")

            if st.button("احسب المستحقات"):
                if basic > 0 and years > 0:
                    res = legal_tools.calculate_eosb(
                        basic, total if total > 0 else basic, years, arbitrary, delay_m)
                    st.markdown(f"""
                    <div class='stat-grid'>
                      <div class='stat-box'><div class='v'>{res['eosb']:,.0f}</div><div class='l'>مكافأة نهاية الخدمة</div></div>
                      <div class='stat-box'><div class='v'>{res['arbitrary']:,.0f}</div><div class='l'>تعويض تعسفي</div></div>
                      <div class='stat-box'><div class='v'>{res['delay']:,.0f}</div><div class='l'>تعويض التأخير</div></div>
                      <div class='stat-box' style='border-color:#c9a84c;grid-column:span 2;'>
                        <div class='v' style='font-size:1.7rem;'>{res['grand']:,.0f}</div>
                        <div class='l'>الإجمالي (ريال)</div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                    for d in res["details"]:
                        if d:
                            st.markdown(f"<div class='alert info'>{d}</div>",
                                        unsafe_allow_html=True)
                else:
                    st.warning("أدخل الراتب الأساسي وسنوات الخدمة")

        elif active_tool == "email_scan":
            st.markdown("<div class='section-title'>فحص المراسلات</div>", unsafe_allow_html=True)
            up = st.file_uploader("ارفع ملفات المراسلات",
                                   type=["pdf","txt","docx"], accept_multiple_files=True)
            manual = st.text_area("أو الصق النص مباشرة", height=120)
            if st.button("فحص المراسلات"):
                combined = manual
                if up:
                    for f in up:
                        combined += "\n\n" + file_processing.extract_text_from_file(f)
                if combined.strip():
                    findings = legal_tools.scan_for_slips(combined)
                    if findings:
                        for fi in findings:
                            lvl = fi["level"]
                            msg = fi["msg"]
                            snp = fi["snippet"]
                            st.markdown(
                                f"<div class='alert {lvl}'>"
                                f"<strong>{msg}</strong><br>"
                                f"<small style='opacity:0.7;'>«{snp}»</small></div>",
                                unsafe_allow_html=True)
                    else:
                        st.markdown("<div class='alert ok'>لم تُكتشف زلات صريحة</div>",
                                    unsafe_allow_html=True)
                else:
                    st.warning("ارفع ملفاً أو الصق النص")

        elif active_tool == "doc_analysis":
            st.markdown("<div class='section-title'>تحليل المستندات</div>", unsafe_allow_html=True)
            up = st.file_uploader("ارفع الملفات",
                                   type=["pdf","docx","txt"], accept_multiple_files=True)
            if up:
                texts = []
                for f in up:
                    with st.expander(f.name):
                        txt = file_processing.extract_text_from_file(f)
                        texts.append(txt)
                        st.text_area("معاينة", txt[:500]+"...", height=100, key=f"p_{f.name}")
                        facts = legal_tools.extract_quick_facts(txt)
                        if facts["dates"]:    st.write("تواريخ:", " | ".join(facts["dates"]))
                        if facts["amounts"]:  st.write("مبالغ:",  " | ".join(facts["amounts"]))
                        if facts["articles"]: st.write("مواد:",   " | ".join(facts["articles"]))
                if st.button("إرسال للمحادثة"):
                    st.session_state.docs_text = texts
                    st.session_state.pending_input = (
                        "حلّل هذه الوثائق:\n1. الوقائع\n2. نقاط القوة\n"
                        "3. نقاط الخصم\n4. التوصيات\n\n" +
                        "\n---\n".join(texts)[:5000])
                    st.session_state.active_nav = "chat"
                    st.rerun()

        elif active_tool == "law_search":
            st.markdown("<div class='section-title'>البحث في نظام العمل</div>", unsafe_allow_html=True)
            q = st.text_input("موضوع البحث", placeholder="مثال: مكافأة نهاية الخدمة")
            if st.button("بحث") and q.strip():
                st.session_state.pending_input = (
                    f"ابحث في نظام العمل السعودي: {q}\n"
                    "اذكر رقم المادة ونصها الجوهري.")
                st.session_state.active_nav = "chat"
                st.rerun()

        elif active_tool in legal_tools.TOOL_PROMPTS:
            icon, title, auto_p = legal_tools.TOOL_PROMPTS[active_tool]
            st.markdown(f"<div class='section-title'>{title}</div>", unsafe_allow_html=True)
            ctx = st.text_area("معطيات القضية (اختياري)", height=120)
            if st.button("تشغيل"):
                full = auto_p + (f"\n\nمعطيات:\n{ctx}" if ctx.strip() else "")
                st.session_state.pending_input  = full
                st.session_state.active_nav = "chat"
                st.rerun()

    # ════════════════════════════════════
    # صفحة الجلسات
    # ════════════════════════════════════
    elif nav == "sessions":
        st.markdown("<div class='section-title'>الجلسات المحفوظة</div>", unsafe_allow_html=True)

        if st.button("جلسة جديدة", use_container_width=True):
            sid = storage.new_session_id()
            label = "المحامي" if persona == "lawyer" else "المستشار"
            st.session_state.current_sid  = sid
            st.session_state.current_msgs = []
            storage.save_session(sid, {"name":f"جلسة {label}","messages":[],"persona":persona})
            st.session_state.active_nav = "chat"
            st.rerun()

        sessions = storage.list_sessions()
        if not sessions:
            st.markdown("<p class='sub-text' style='text-align:center;margin-top:20px;'>لا توجد جلسات محفوظة</p>",
                        unsafe_allow_html=True)
        for s in sessions[:8]:
            cur = s["id"] == st.session_state.current_sid
            sc1, sc2 = st.columns([5,1])
            with sc1:
                label = f"{'← ' if cur else ''}{s['name'][:18]} ({s['count']} رسالة)"
                if st.button(label, key=f"sess_{s['id']}", use_container_width=True):
                    d = storage.load_session(s["id"])
                    st.session_state.current_sid  = s["id"]
                    st.session_state.current_msgs = d.get("messages",[])
                    st.session_state.persona      = d.get("persona","lawyer")
                    st.session_state.active_nav   = "chat"
                    st.rerun()
            with sc2:
                if st.button("حذف", key=f"del_{s['id']}", use_container_width=True):
                    storage.delete_session(s["id"])
                    if st.session_state.current_sid == s["id"]:
                        st.session_state.current_sid  = None
                        st.session_state.current_msgs = []
                    st.rerun()

    # ════════════════════════════════════
    # صفحة التحليل الشامل 18 محوراً
    # ════════════════════════════════════
    elif nav == "analysis":
        st.markdown("<div class='section-title'>التحليل الشامل — 18 محوراً قانونياً</div>",
                    unsafe_allow_html=True)
        st.markdown("""
        <p class='sub-text'>
          يحلل قضيتك من 18 زاوية متخصصة بنظام العمل السعودي بالتسلسل،
          وينتهي برأي إجماع موحّد يجمع كل الزوايا في توصية واحدة.
        </p>
        """, unsafe_allow_html=True)

        case_text = st.text_area(
            "صف القضية أو الصق وقائعها",
            height=160,
            placeholder="مثال: نُقلت تعسفياً بعد شكوى رسمية، وتلقيت تقييم أداء سلبياً من مشرف لم يعمل معي..."
        )

        if not st.session_state.api_key:
            st.markdown("<div class='alert warn'>أدخل مفتاح API أولاً من زر ⚙️ في الأعلى</div>",
                        unsafe_allow_html=True)

        if st.button("ابدأ التحليل الشامل", use_container_width=True):
            if not st.session_state.api_key:
                st.error("أدخل مفتاح API أولاً")
            elif not case_text.strip():
                st.warning("اكتب وقائع القضية أولاً")
            else:
                prog  = st.progress(0, text="جارٍ التحليل...")
                stat  = st.empty()

                def _upd(i, total, name):
                    prog.progress(i/total, text=f"محور {i}/{total}: {name}")
                    stat.caption(name)

                with st.spinner("جارٍ تحليل القضية..."):
                    result = analysis_engine.run_full_analysis(
                        case_text, ai_call, progress_callback=_upd)

                prog.empty(); stat.empty()

                st.markdown("<div class='section-title'>رأي الإجماع النهائي</div>",
                            unsafe_allow_html=True)
                st.markdown(
                    f"<div class='card'>{result['consensus'].replace(chr(10),'<br>')}</div>",
                    unsafe_allow_html=True)

                st.markdown("<div class='section-title'>تفاصيل المحاور الثمانية عشر</div>",
                            unsafe_allow_html=True)
                for r in result["axes"]:
                    with st.expander(f"{r['icon']} {r['name']}"):
                        st.markdown(r["answer"])
