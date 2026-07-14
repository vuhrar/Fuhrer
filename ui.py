# ui.py - الواجهة الاحترافية لمنصة FÜHRER
2	import streamlit as st
3	from datetime import datetime
4	import api
5	import tools
6	import storage
7	import legal_tools
8	from legal_tools_advanced import entitlements_calculator, deadlines_tracker, slip_detector, case_analyzer, legal_classifier
9	
10	CSS = """
11	<style>
12	@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;900&display=swap');
13	*, *::before, *::after { box-sizing: border-box !important; font-family: 'Tajawal', sans-serif !important; }
14	html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"],
15	[data-testid="stBottom"], section[data-testid="stSidebar"] {
16	  background-color: #1c1c1e !important; color: #ffffff !important; direction: rtl !important;
17	}
18	[data-testid="stSidebar"], [data-testid="collapsedControl"], #MainMenu, footer, header { display: none !important; }
19	.main .block-container { max-width: 900px !important; padding: 0 16px 80px !important; margin: 0 auto !important; }
20	.app-title {
21	  text-align: center; padding: 40px 0 10px; font-size: 6.4rem; font-weight: 900;
22	  background: linear-gradient(135deg, #ffffff, #4a9eff);
23	  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
24	  background-clip: text; text-shadow: 0 10px 30px rgba(0,0,0,0.4);
25	  letter-spacing: -0.02em; margin-bottom: 10px;
26	}
27	.persona-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 40px 0; }
28	.persona-card {
29	  background: #2c2c2e; border: 2px solid #c9a84c; border-radius: 20px; padding: 40px 20px;
30	  text-align: center; cursor: pointer; transition: all 0.3s ease;
31	}
32	.persona-card:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(201,168,76,0.2); border-color: #f0c040; }
33	.persona-card .pc-icon { font-size: 3rem; margin-bottom: 15px; }
34	.persona-card .pc-title { font-size: 1.5rem; font-weight: 800; color: #ffffff; margin-bottom: 10px; }
35	.persona-card .pc-sub { font-size: 0.9rem; color: #aaaaaa; line-height: 1.6; }
36	
37	.nav-bar { display: flex; justify-content: center; gap: 15px; margin-bottom: 30px; border-bottom: 1px solid #3a3a3c; padding-bottom: 15px; }
38	.nav-item { cursor: pointer; padding: 8px 20px; border-radius: 20px; font-weight: 600; font-size: 0.95rem; transition: 0.2s; }
39	.nav-item.active { background: #c9a84c; color: #1c1c1e; }
40	
41	.tool-sidebar {
42	  background: #252527; border-left: 1px solid #3a3a3c; padding: 20px; border-radius: 15px;
43	  margin-bottom: 20px;
44	}
45	.tool-btn {
46	  background: #2c2c2e !important; color: #ffffff !important; border: 1px solid #3a3a3c !important;
47	  border-radius: 10px !important; padding: 10px 15px !important; margin-bottom: 8px !important;
48	  text-align: right !important; font-size: 0.9rem !important; width: 100% !important;
49	}
50	.tool-btn:hover { border-color: #c9a84c !important; color: #c9a84c !important; }
51	
52	.bubble-user {
53	  background: #2c3e50; border-radius: 20px 20px 5px 20px; padding: 15px 20px;
54	  margin: 10px 0 10px 15%; color: #ffffff; font-size: 1rem; line-height: 1.7;
55	}
56	.bubble-ai {
57	  background: #2c2c2e; border-right: 4px solid #c9a84c; border-radius: 20px 20px 20px 5px;
58	  padding: 15px 20px; margin: 10px 15% 10px 0; color: #ffffff; font-size: 1rem; line-height: 1.8;
59	}
60	
61	/* تحسين خانات الإدخال */
62	.stTextArea textarea {
63	  background-color: #2c2c2e !important; color: #ffffff !important;
64	  border: 1px solid #3a3a3c !important; border-radius: 15px !important;
65	  padding: 15px !important; font-size: 1rem !important;
66	}
67	
68	.stButton > button {
69	  border-radius: 12px !important; font-weight: 700 !important;
70	}
71	
72	.section-title {
73	  font-size: 1.2rem; font-weight: 800; color: #c9a84c; margin: 25px 0 15px;
74	  display: flex; align-items: center; gap: 10px;
75	}
76	.section-title::after { content: ""; flex: 1; height: 1px; background: #3a3a3c; }
77	</style>
78	"""
79	
80	def render_persona_selection():
81	    st.markdown("<h2 style='text-align:center;color:#c9a84c;margin-bottom:10px;'>مرحباً بك في المنصة القانونية</h2>", unsafe_allow_html=True)
82	    st.markdown("<p style='text-align:center;color:#aaaaaa;margin-bottom:40px;'>يرجى اختيار التخصص المطلوب لبدء الجلسة الاستشارية</p>", unsafe_allow_html=True)
83	
84	    col1, col2 = st.columns(2)
85	    
86	    with col1:
87	        st.markdown(f"""
88	        <div class='persona-card' onclick='document.getElementById("pick_lawyer").click()'>
89	            <div class='pc-icon'>⚖️</div>
90	            <div class='pc-title'>المحامي والمستشار القانوني</div>
91	            <div class='pc-sub'>متخصص في الترافع، صياغة المذكرات، والتحليل الاستراتيجي للقضايا العمالية.</div>
92	        </div>
93	        """, unsafe_allow_html=True)
94	        if st.button("بدء بصفتي محامي", key="pick_lawyer", use_container_width=True):
95	            select_persona("lawyer")
96	
97	    with col2:
98	        st.markdown(f"""
99	        <div class='persona-card' onclick='document.getElementById("pick_advisor").click()'>
100	            <div class='pc-icon'>💼</div>
101	            <div class='pc-title'>المستشار العمالي</div>
102	            <div class='pc-sub'>خبير في الامتثال، التسويات الودية، وحساب المستحقات المالية العمالية.</div>
103	        </div>
104	        """, unsafe_allow_html=True)
105	        if st.button("بدء بصفتي مستشار", key="pick_advisor", use_container_width=True):
106	            select_persona("advisor")
107	
108	def select_persona(pid):
109	    st.session_state.persona = pid
110	    st.session_state.active_nav = "chat"
111	    name = legal_tools.get_persona_display_name(pid)
112	    sid = storage.new_session_id()
113	    st.session_state.current_sid = sid
114	    st.session_state.current_msgs = []
115	    storage.save_session(sid, {"name": f"استشارة {name}", "messages": [], "persona": pid})
116	    st.rerun()
117	
118	def render_nav_bar():
119	    nav_items = [
120	        ("💬 المحادثة الاستشارية", "chat"),
121	        ("📋 سجل الجلسات", "sessions"),
122	        ("📊 التحليل القانوني المعمق", "analysis"),
123	        ("📁 أرشيف القضايا", "cases"),
124	        ("🔄 تغيير التخصص", "switch"),
125	    ]
126	    
127	    cols = st.columns(len(nav_items))
128	    for col, (label, key) in zip(cols, nav_items):
129	        with col:
130	            is_active = st.session_state.active_nav == key
131	            btn_label = f"**{label}**" if is_active else label
132	            if st.button(btn_label, key=f"nav_{key}", use_container_width=True, type="secondary" if not is_active else "primary"):
133	                if key == "switch":
134	                    st.session_state.persona = None
135	                    st.session_state.active_nav = "chat"
136	                    st.session_state.current_sid = None
137	                    st.session_state.current_msgs = []
138	                else:
139	                    st.session_state.active_nav = key
140	                st.rerun()
141	
142	def render_persona_badge():
143	    persona = st.session_state.persona
144	    name = legal_tools.get_persona_display_name(persona)
145	    icon = "⚖️" if persona == "lawyer" else "💼"
146	    st.markdown(f"""
147	    <div style='text-align:center; margin-bottom:20px;'>
148	        <span style='background:#2c2c2e; border:1px solid #c9a84c; color:#c9a84c; padding:5px 20px; border-radius:20px; font-weight:700;'>
149	            {icon} {name}
150	        </span>
151	    </div>
152	    """, unsafe_allow_html=True)
153	
154	def render_chat():
155	    # تقسيم الشاشة لدمج الأدوات في الجانب
156	    chat_col, tool_col = st.columns([3, 1])
157	    
158	    with tool_col:
159	        st.markdown("<div class='section-title'>🛠️ أدوات التخصص</div>", unsafe_allow_html=True)
160	        tools_list = legal_tools.get_tools_for_persona(st.session_state.persona)
161	        for icon, name, tool_id in tools_list:
162	            if st.button(f"{icon} {name}", key=f"tool_{tool_id}", use_container_width=True):
163	                st.session_state.selected_tool = tool_id
164	                st.session_state.active_nav = "tool_exec"
165	                st.rerun()
166	        
167	        st.markdown("<div class='section-title'>📄 المستندات</div>", unsafe_allow_html=True)
168	        if st.session_state.docs_text:
169	            st.success(f"تم تحميل {len(st.session_state.docs_text)} مستند")
170	        else:
171	            st.info("لا توجد مستندات نشطة")
172	
173	    with chat_col:
174	        if st.session_state.current_sid:
175	            sess_data = storage.load_session(st.session_state.current_sid)
176	            
177	            # عرض الرسائل
178	            for msg in st.session_state.current_msgs:
179	                if msg["role"] == "user":
180	                    st.markdown(f"<div class='bubble-user'>{msg['content']}</div>", unsafe_allow_html=True)
181	                else:
182	                    st.markdown(f"<div class='bubble-ai'>{msg['content']}</div>", unsafe_allow_html=True)
183	            
184	            # منطقة الإدخال
185	            user_input = st.text_area("", placeholder="اطلب استشارة أو حلل واقعة قانونية...", label_visibility="collapsed", key="chat_input")
186	            
187	            c1, c2 = st.columns([4, 1])
188	            with c1:
189	                if st.button("🚀 إرسال الاستشارة", use_container_width=True, type="primary"):
190	                    if user_input.strip():
191	                        process_chat(user_input, sess_data)
192	            with c2:
193	                if st.button("🗑️", use_container_width=True):
194	                    st.session_state.current_msgs = []
195	                    sess_data["messages"] = []
196	                    storage.save_session(st.session_state.current_sid, sess_data)
197	                    st.rerun()
198	
199	def process_chat(user_input, sess_data):
200	    ts = datetime.now().strftime("%H:%M")
201	    st.session_state.current_msgs.append({"role": "user", "content": user_input.strip(), "ts": ts})
202	    
203	    system_p = legal_tools.get_persona_prompt(st.session_state.persona)
204	    # إضافة سياق عقل البرنامج
205	    from analysis_engine import LAW_BRAIN_SYSTEM
206	    system_p = LAW_BRAIN_SYSTEM + "\n\n" + system_p
207	    
208	    if st.session_state.docs_text:
209	        context = "\n\n".join(st.session_state.docs_text[:3])
210	        system_p += f"\n\nالوثائق القانونية المرفقة:\n{context[:3000]}"
211	    
212	    with st.spinner("جاري التحليل القانوني..."):
213	        resp = api.ai_call(user_input.strip(), st.session_state.current_msgs[:-1], system_p)
214	    
215	    st.session_state.current_msgs.append({"role": "assistant", "content": resp, "ts": ts})
216	    sess_data["messages"] = st.session_state.current_msgs
217	    storage.save_session(st.session_state.current_sid, sess_data)
218	    st.rerun()
219	
220	def render_tool_execution():
221	    st.markdown(f"<div class='section-title'>🛠️ تشغيل الأداة: {st.session_state.selected_tool}</div>", unsafe_allow_html=True)
222	    
223	    tool_id = st.session_state.selected_tool
224	    if tool_id == "calculator":
225	        tools.run_calculator()
226	    elif tool_id == "law_search":
227	        tools.run_law_search()
228	    elif tool_id == "email_scan":
229	        tools.run_email_scan()
230	    elif tool_id == "case_strength":
231	        tools.run_case_strength()
232	    elif tool_id == "settlement":
233	        tools.run_settlement()
234	    elif tool_id == "extractor":
235	        tools.run_info_extractor()
236	    
237	    if st.button("⬅️ العودة للمحادثة", use_container_width=True):
238	        st.session_state.selected_tool = None
239	        st.session_state.active_nav = "chat"
240	        st.rerun()
241	
242	def render_sessions():
243	    st.markdown("<div class='section-title'>📋 سجل الجلسات الاستشارية</div>", unsafe_allow_html=True)
244	    sessions = storage.list_sessions()
245	    if not sessions:
246	        st.info("لا توجد جلسات سابقة.")
247	        return
248	    
249	    for sid in sessions:
250	        data = storage.load_session(sid)
251	        name = data.get("name", sid)
252	        col1, col2 = st.columns([4, 1])
253	        with col1:
254	            if st.button(f"📄 {name}", key=f"sess_{sid}", use_container_width=True):
255	                st.session_state.current_sid = sid
256	                st.session_state.current_msgs = data.get("messages", [])
257	                st.session_state.persona = data.get("persona", "lawyer")
258	                st.session_state.active_nav = "chat"
259	                st.rerun()
260	        with col2:
261	            if st.button("🗑️", key=f"del_{sid}", use_container_width=True):
262	                storage.delete_session(sid)
263	                st.rerun()
264	
265	def render_analysis():
266	    st.markdown("<div class='section-title'>📊 التحليل القانوني المعمق (18 محوراً)</div>", unsafe_allow_html=True)
267	    case_text = st.text_area("أدخل وقائع القضية للتحليل الشامل:", height=200)
268	    if st.button("بدء التحليل الاستراتيجي", type="primary"):
269	        if case_text:
270	            import analysis_engine
271	            with st.spinner("جاري تشغيل محاور التحليل الـ 18..."):
272	                res = analysis_engine.run_full_analysis(case_text, api.ai_call)
273	                st.markdown("### 🏆 الإجماع القانوني النهائي")
274	                st.write(res["consensus"])
275	                for axis in res["axes"]:
276	                    with st.expander(f"{axis['icon']} {axis['name']}"):
277	                        st.write(axis["answer"])
278	
279	def render_cases():
280	    st.markdown("<div class='section-title'>📁 أرشيف القضايا الموثقة</div>", unsafe_allow_html=True)
281	    cases = storage.list_cases()
282	    if not cases:
283	        st.info("لا توجد قضايا مؤرشفة.")
284	        return
285	    for cid in cases:
286	        data = storage.load_case(cid)
287	        with st.expander(f"💼 قضية: {data.get('title', cid)}"):
288	            st.write(data.get("content", ""))
289	            if st.button("حذف القضية", key=f"del_case_{cid}"):
290	                storage.delete_case(cid)
291	                st.rerun()
292	
