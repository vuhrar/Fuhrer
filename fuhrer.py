# fuhrer.py - المنصة القانونية الاحترافية الموحدة
2	import sys
3	import os
4	sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
5	
6	import streamlit as st
7	from datetime import datetime
8	from dotenv import load_dotenv
9	load_dotenv()
10	
11	import ai_engine
12	import analysis_engine
13	import legal_tools
14	import file_processing
15	import storage
16	import ui
17	import api
18	import tools
19	
20	st.set_page_config(
21	    page_title="FÜHRER — المنصة القانونية الاحترافية",
22	    page_icon="⚖️",
23	    layout="wide",
24	    initial_sidebar_state="collapsed"
25	)
26	
27	# تطبيق التنسيق الاحترافي
28	st.markdown(ui.CSS, unsafe_allow_html=True)
29	
30	# تهيئة حالة الجلسة
31	_saved = storage.load_settings()
32	_defaults = {
33	    "persona": None,
34	    "active_nav": "chat",
35	    "current_sid": None,
36	    "current_msgs": [],
37	    "docs_text": [],
38	    "preset_name": _saved.get("preset_name", "Führer Law Brain (Qwen 0.6B) 🧠"),
39	    "api_key": _saved.get("api_key", ""),
40	    "custom_url": _saved.get("custom_url", ""),
41	    "custom_model": _saved.get("custom_model", ""),
42	    "custom_fmt": _saved.get("custom_fmt", "openai"),
43	    "show_panel": None,
44	    "selected_tool": None,
45	    "connection_status": "unknown",
46	    "connection_msg": "",
47	}
48	for k, v in _defaults.items():
49	    if k not in st.session_state:
50	        st.session_state[k] = v
51	
52	# شريط الحالة العلوي
53	status_col, corner_col = st.columns([10, 1])
54	with status_col:
55	    conn_status = st.session_state.get("connection_status", "unknown")
56	    if conn_status == "connected":
57	        st.markdown("<span style='color:#4ade80;font-size:0.8rem;float:left;margin-top:10px;'>🟢 النظام متصل</span>", unsafe_allow_html=True)
58	    elif conn_status == "failed":
59	        st.markdown("<span style='color:#f87171;font-size:0.8rem;float:left;margin-top:10px;'>🔴 خطأ في الربط</span>", unsafe_allow_html=True)
60	with corner_col:
61	    if st.button("⚙️", key="settings_icon"):
62	        st.session_state.show_panel = None if st.session_state.show_panel == "full" else "full"
63	        st.rerun()
64	
65	# واجهة الإعدادات الاحترافية
66	if st.session_state.show_panel == "full":
67	    with st.container():
68	        st.markdown("<div class='section-title'>⚙️ إعدادات المنصة والربط التقني</div>", unsafe_allow_html=True)
69	        t1, t2, t3 = st.tabs(["الربط مع الخادم", "المستندات القانونية", "إدارة النظام"])
70	        
71	        with t1:
72	            col_a, col_b = st.columns(2)
73	            with col_a:
74	                st.session_state.preset_name = st.selectbox("مزود الذكاء الاصطناعي", list(ai_engine.PRESETS.keys()), 
75	                    index=list(ai_engine.PRESETS.keys()).index(st.session_state.preset_name) if st.session_state.preset_name in ai_engine.PRESETS else 0)
76	                st.session_state.api_key = st.text_input("مفتاح API", value=st.session_state.api_key, type="password")
77	            with col_b:
78	                if st.session_state.preset_name == "⚙️ مخصص":
79	                    st.session_state.custom_url = st.text_input("رابط API المخصص", value=st.session_state.custom_url)
80	                    st.session_state.custom_model = st.text_input("اسم النموذج المخصص", value=st.session_state.custom_model)
81	            
82	            if st.button("🔌 اختبار وتفعيل الربط", use_container_width=True):
83	                with st.spinner("جاري التحقق من استجابة الخادم..."):
84	                    ok, msg = ai_engine.test_connection(st.session_state.preset_name, st.session_state.api_key, 
85	                        st.session_state.custom_url, st.session_state.custom_model, st.session_state.custom_fmt)
86	                    st.session_state.connection_status = "connected" if ok else "failed"
87	                    st.session_state.connection_msg = msg
88	                    if ok:
89	                        storage.save_settings({"preset_name": st.session_state.preset_name, "api_key": st.session_state.api_key})
90	                        st.toast("✅ تم تفعيل الربط بنجاح")
91	                    st.rerun()
92	        
93	        with t2:
100	            new_docs = file_processing.render_file_upload_widget()
101	            if new_docs:
102	                st.session_state.docs_text = new_docs
103	                st.success(f"✅ تم دمج {len(new_docs)} مستند في عقل البرنامج")
104	            if st.session_state.docs_text:
105	                if st.button("🗑️ إفراغ ذاكرة المستندات"):
106	                    st.session_state.docs_text = []
107	                    st.rerun()
108	        
109	        with t3:
110	            if st.button("⚠️ مسح شامل لجميع البيانات المؤقتة", use_container_width=True):
111	                storage.clear_all_sessions()
112	                st.session_state.current_sid = None
113	                st.session_state.current_msgs = []
114	                st.rerun()
115	    st.markdown("---")
116	
117	# الهيكل الرئيسي للتطبيق
118	st.markdown("<div class='app-title'>FÜHRER</div>", unsafe_allow_html=True)
119	
120	if st.session_state.persona is None:
121	    ui.render_persona_selection()
122	else:
123	    ui.render_nav_bar()
124	    ui.render_persona_badge()
125	    
126	    nav = st.session_state.active_nav
127	    if nav == "chat":
128	        ui.render_chat()
129	    elif nav == "tool_exec":
130	        ui.render_tool_execution()
131	    elif nav == "sessions":
132	        ui.render_sessions()
133	    elif nav == "analysis":
134	        ui.render_analysis()
135	    elif nav == "cases":
136	        ui.render_cases()
137	    elif nav == "switch":
138	        st.session_state.persona = None
139	        st.session_state.active_nav = "chat"
140	        st.rerun()
141	
