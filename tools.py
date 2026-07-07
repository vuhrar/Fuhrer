# tools.py
import streamlit as st
from datetime import datetime
import analysis_engine
import legal_tools
from legal_tools_advanced import (
    legal_classifier, legal_search, rebuttal_generator,
    document_generator, entitlements_calculator,
    deadlines_tracker, slip_detector, case_analyzer, info_extractor
)
import api

def run_calculator():
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

def run_law_search():
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
                    results = analysis_engine.search_with_ai(search_query, api.ai_call, max_results=5)
            if results:
                st.markdown(f"### 📚 نتائج البحث ({len(results)} نتيجة)")
                for result in results:
                    with st.expander(f"{result.get('title', 'مادة غير معروفة')} — {result.get('category', 'عام')}"):
                        st.markdown(f"**المصدر:** {result.get('source', 'مجهول')}")
                        st.markdown(f"**المادة:** {result.get('id', 'مجهول')}")
                        st.markdown("**النص:**")
                        st.markdown(f"<div class='card'>{result.get('text', '')[:1000]}</div>", unsafe_allow_html=True)

def run_email_scan():
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

def run_case_strength():
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

def run_settlement():
    st.markdown("<div class='section-title'>🤝 تقييم خيارات التسوية</div>", unsafe_allow_html=True)
    case_details = st.text_area("تفاصيل القضية:", height=200, placeholder="صف القضيه، المطالبات، والمبلغ المتوقع...", key="settlement_input")
    if st.button("🤝 تقييم التسوية", use_container_width=True):
        if not case_details.strip():
            st.warning("الرجاء إدخال تفاصيل القضية.")
        else:
            with st.spinner("جاري التقييم..."):
                prompt = legal_tools.TOOL_PROMPTS["settlement"][2]
                prompt = f"{prompt}\n\nتفاصيل القضية:\n{case_details}"
                settlement = api.ai_call(prompt, [], legal_tools.PERSONA_PROMPTS["advisor"])
            st.markdown("### 🤝 خيارات التسوية")
            st.markdown(f"<div class='card'>{settlement}</div>", unsafe_allow_html=True)