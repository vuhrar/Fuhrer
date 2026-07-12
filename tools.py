# tools.py
"""
طبقة الأدوات — الجسر بين الواجهة ومنطق الأعمال
النسخة الاحترافية v2.0 — إصلاح كامل لجميع تناقضات العقود
"""

import streamlit as st
from datetime import datetime
from typing import Optional, Callable

import analysis_engine
import legal_tools
from legal_tools_advanced import (
    legal_classifier,
    legal_search,
    rebuttal_generator,
    document_generator,
    entitlements_calculator,
    deadlines_tracker,
    slip_detector,
    case_analyzer,
    info_extractor,
)
import api


# ============================================================
# 1. حاسبة الاستحقاقات — مُصلَحة بالكامل
# ============================================================
def run_calculator():
    st.markdown("<div class='section-title'>💰 حاسبة الاستحقاقات القانونية</div>", unsafe_allow_html=True)

    calc_tabs = st.tabs(["🏦 نهاية الخدمة", "🗓️ رصيد الإجازة", "⏰ عمل إضافي", "⏳ مواعيد قانونية"])

    # ── تبويب 1: مكافأة نهاية الخدمة ──────────────────────
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
            resignation = st.checkbox("إنهاء بالاستقالة (يؤثر على نسبة المكافأة)", value=False, key="eosb_resignation")
            delay_months = st.number_input("أشهر تأخير في دفع الراتب (مادة 90):", min_value=0, value=0, key="eosb_delay")

        if st.button("🧮 احسب مكافأة نهاية الخدمة", use_container_width=True, key="btn_calc_eosb"):
            # ← إصلاح: استدعاء الدالة بالمعاملات الصحيحة
            result = entitlements_calculator.calculate_eosb(
                basic_salary=basic_salary,
                total_salary=total_salary,
                years_of_service=years_of_service,
                is_arbitrary=arbitrary,
                delay_months=delay_months,
                is_saudi=is_saudi,
                resignation=resignation,
            )
            st.markdown("### 💰 نتيجة الحساب")
            grand_total = result["totals"]["grand_total"]
            st.markdown(f"""
            <div class='card' style='border-right: 4px solid #4a9eff;'>
                <h2 style='color: #4a9eff;'>الإجمالي: {grand_total:,.2f} ريال سعودي</h2>
                <p>سنوات الخدمة: {result['years_of_service']:.1f} سنة</p>
            </div>""", unsafe_allow_html=True)

            st.markdown("### 📋 التفاصيل:")
            # ← إصلاح: الوصول إلى details الذي يعيده calculate_eosb الآن
            for key, detail in result["details"].items():
                if detail["amount"] > 0:
                    st.markdown(
                        f"- **{detail['description']}**: `{detail['amount']:,.2f} ريال`  \n"
                        f"  _{detail.get('formula', '')}_"
                    )

            st.markdown("---")
            st.markdown("### 📊 الملخص:")
            for line in result.get("summary", []):
                if line:
                    st.markdown(line)

    # ── تبويب 2: رصيد الإجازة ──────────────────────────────
    with calc_tabs[1]:
        st.markdown("#### 🗓️ رصيد الإجازة السنوية (مادة 109)")
        start_date = st.date_input("تاريخ بداية العمل:", value=datetime(2020, 1, 1), key="vacation_start")
        end_date = st.date_input("تاريخ نهاية العمل (اتركه فارغاً للتاريخ الحالي):", key="vacation_end", value=None)
        annual_days = st.slider("أيام الإجازة السنوية:", min_value=21, max_value=30, value=21, key="vacation_days")

        if st.button("🧮 احسب رصيد الإجازة", use_container_width=True, key="btn_calc_vacation"):
            result = entitlements_calculator.calculate_vacation_balance(
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d") if end_date else "",
                annual_vacation_days=annual_days,
            )
            if "error" in result:
                st.error(f"خطأ: {result['error']}")
            else:
                st.markdown(f"""
                <div class='card' style='border-right: 4px solid #4ade80;'>
                    <h2 style='color: #4ade80;'>رصيد الإجازة: {result['earned_vacation']:.1f} يوم</h2>
                    <p>سنوات الخدمة: {result['total_years']:.1f} سنة</p>
                    <p>أيام الإجازة السنوية: {result['annual_vacation_days']} يوم</p>
                </div>""", unsafe_allow_html=True)
                st.info(f"💡 {result.get('cash_value_note', '')}")

    # ── تبويب 3: العمل الإضافي ─────────────────────────────
    with calc_tabs[2]:
        st.markdown("#### ⏰ أجر العمل الإضافي (مادة 106)")
        monthly_salary = st.number_input("الراتب الشهري (ريال):", min_value=0.0, value=10000.0, step=100.0, key="ot_salary")
        overtime_hours = st.number_input("عدد ساعات العمل الإضافي:", min_value=0.0, value=10.0, step=0.5, key="ot_hours")

        if st.button("🧮 احسب أجر العمل الإضافي", use_container_width=True, key="btn_calc_ot"):
            # حساب أجر الساعة: الراتب / 30 يوم / 8 ساعات
            hourly_rate = monthly_salary / 30 / 8
            result = entitlements_calculator.calculate_overtime(hourly_rate, overtime_hours)
            st.markdown(f"""
            <div class='card' style='border-right: 4px solid #ffb400;'>
                <h2 style='color: #ffb400;'>أجر العمل الإضافي: {result['overtime_pay']:,.2f} ريال</h2>
                <p>أجر الساعة العادية: {result['hourly_rate']:.2f} ريال</p>
                <p>أجر الساعة الإضافية (150%): {result['hourly_rate'] * 1.5:.2f} ريال</p>
                <p>عدد الساعات: {result['overtime_hours']:.1f} ساعة</p>
            </div>""", unsafe_allow_html=True)
            st.info(f"📋 الأساس القانوني: {result['legal_basis']}")

    # ── تبويب 4: المواعيد القانونية ────────────────────────
    with calc_tabs[3]:
        st.markdown("#### ⏳ متابعة المواعيد القانونية")
        case_type = st.selectbox(
            "نوع القضية:",
            list(deadlines_tracker.deadlines.keys()),
            key="deadline_case_type",
        )
        case_date = st.date_input("تاريخ بداية القضية:", value=datetime.now(), key="deadline_case_date")

        if st.button("⏳ تحقق من الموعد", use_container_width=True, key="btn_check_deadline"):
            # ← إصلاح: الدالة الآن تعيد 'message' و 'action' و 'color' بشكل صحيح
            result = deadlines_tracker.check_deadline(case_type, case_date.strftime("%Y-%m-%d"))

            if "error" in result and result.get("status") == "unknown":
                st.error(result["error"])
            else:
                color = result.get("color", "#4ade80")
                st.markdown(f"""
                <div class='card' style='border-right: 4px solid {color};'>
                    <h3 style='color: {color};'>{result['message']}</h3>
                    <p>- تاريخ بدء القضية: <strong>{result['case_date']}</strong></p>
                    <p>- آخر موعد قانوني: <strong>{result['due_date']}</strong></p>
                    <p>- الأيام المتبقية: <strong>{result['days_remaining']} يوم</strong></p>
                    <p>- المادة القانونية: <strong>مادة {result['article']}</strong></p>
                </div>""", unsafe_allow_html=True)
                st.markdown("### 📋 الإجراء المطلوب:")
                st.markdown(f"> {result['action']}")


# ============================================================
# 2. البحث القانوني
# ============================================================
def run_law_search():
    st.markdown("<div class='section-title'>📚 البحث في الأنظمة القانونية</div>", unsafe_allow_html=True)

    search_method = st.radio(
        "طريقة البحث:",
        ["🔍 بحث سريع في قاعدة البيانات", "🤖 بحث متقدم بالذكاء الاصطناعي"],
        horizontal=True,
        key="search_method",
    )
    search_query = st.text_input(
        "عبارة البحث:",
        placeholder="مثال: مكافأة نهاية الخدمة، فصل تعسفي، ساعات العمل...",
        key="law_search_query",
    )
    # ← إصلاح: get_all_categories موجودة الآن في analysis_engine
    categories = ["جميع الفئات"] + analysis_engine.get_all_categories()
    category = st.selectbox("الفئة (اختياري):", categories, key="law_search_category")

    if st.button("🔍 بحث", use_container_width=True, key="btn_law_search"):
        if not search_query.strip():
            st.warning("الرجاء إدخال عبارة البحث.")
        else:
            with st.spinner("جاري البحث..."):
                if "سريع" in search_method:
                    # ← إصلاح: search_saudi_labor_laws موجودة الآن في analysis_engine
                    results = analysis_engine.search_saudi_labor_laws(search_query, max_results=10)
                else:
                    # ← إصلاح: search_with_ai موجودة الآن في analysis_engine
                    results = analysis_engine.search_with_ai(search_query, api.ai_call, max_results=5)

            if results:
                st.markdown(f"### 📚 نتائج البحث ({len(results)} نتيجة)")
                for result in results:
                    title = result.get("title", "مادة قانونية")
                    cat = result.get("category", "عام")
                    article_num = result.get("article", "")
                    with st.expander(f"📄 {title} — {cat} {'(م' + article_num + ')' if article_num else ''}"):
                        st.markdown(f"**الفئة:** {cat}")
                        if article_num:
                            st.markdown(f"**رقم المادة:** {article_num}")
                        st.markdown("**النص:**")
                        st.markdown(f"<div class='card'>{result.get('text', '')[:1500]}</div>", unsafe_allow_html=True)
                        keywords = result.get("keywords", [])
                        if keywords:
                            st.markdown(f"**الكلمات المفتاحية:** {', '.join(keywords[:8])}")
            else:
                st.info("لم يتم العثور على نتائج. جرّب كلمات بحث مختلفة أو استخدم البحث بالذكاء الاصطناعي.")


# ============================================================
# 3. فحص المراسلات — مُصلَح
# ============================================================
def run_email_scan():
    st.markdown("<div class='section-title'>📧 فحص المراسلات القانونية</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class='info-box'>
    🔍 يقوم هذا النظام بتحليل المراسلات والرسائل للكشف عن الزلات القانونية التي قد تُستخدم كأدلة في القضايا العمالية.
    </div>""", unsafe_allow_html=True)

    email_text = st.text_area(
        "نص المراسلة:",
        height=250,
        placeholder="ادخل نص البريد الإلكتروني، الرسالة، أو أي مراسلة رسمية...",
        key="email_scan_input",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 فحص تلقائي", use_container_width=True, key="btn_scan_auto"):
            if not email_text.strip():
                st.warning("الرجاء إدخال نص المراسلة.")
            else:
                with st.spinner("جاري الفحص..."):
                    # ← إصلاح: slip_detector.detect يعيد 'msg' و 'suggestion' الآن
                    slips = slip_detector.detect(email_text)

                if slips:
                    st.markdown(f"### ⚠️ تم اكتشاف {len(slips)} زلة قانونية")
                    for slip in slips:
                        level_color = "#ff5a5a" if slip["level"] == "danger" else "#ffb400"
                        level_icon = "🔴" if slip["level"] == "danger" else "🟡"
                        st.markdown(f"""
                        <div class='card' style='border-right: 4px solid {level_color}; margin-bottom: 12px;'>
                            <h4 style='color: {level_color};'>{level_icon} {slip['msg']}</h4>
                            <p><strong>المادة القانونية:</strong> مادة {slip['article']}</p>
                            <p><strong>النص المكتشف:</strong> <em>"{slip['snippet']}"</em></p>
                            <p><strong>التوصية:</strong> {slip['suggestion']}</p>
                        </div>""", unsafe_allow_html=True)
                else:
                    st.success("✅ لا توجد زلات قانونية واضحة في المراسلة.")

    with col2:
        if st.button("🤖 تحليل AI متعمق", use_container_width=True, key="btn_scan_ai"):
            if not email_text.strip():
                st.warning("الرجاء إدخال نص المراسلة.")
            else:
                with st.spinner("جاري التحليل المتعمق بالذكاء الاصطناعي..."):
                    prompt = (
                        f"حلّل هذه المراسلة القانونية وابحث عن:\n"
                        f"1. أي زلات قانونية أو إقرارات ضارة\n"
                        f"2. أي انتهاكات لنظام العمل السعودي\n"
                        f"3. أي دليل يمكن استخدامه في محكمة العمل\n\n"
                        f"المراسلة:\n{email_text}"
                    )
                    result = api.ai_call(prompt, [], legal_tools.PERSONA_PROMPTS.get("analyzer", "أنت خبير قانوني."))
                st.markdown("### 🤖 تحليل الذكاء الاصطناعي:")
                st.markdown(f"<div class='card'>{result}</div>", unsafe_allow_html=True)


# ============================================================
# 4. تقييم قوة القضية — مُصلَح
# ============================================================
def run_case_strength():
    st.markdown("<div class='section-title'>📊 تقييم قوة القضية</div>", unsafe_allow_html=True)

    case_details = st.text_area(
        "تفاصيل القضية:",
        height=250,
        placeholder="صف الوقائع، الأدلة المتوفرة، والمطالبات المطلوبة...",
        key="case_strength_input",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⚡ تقييم سريع", use_container_width=True, key="btn_quick_strength"):
            if not case_details.strip():
                st.warning("الرجاء إدخال تفاصيل القضية.")
            else:
                with st.spinner("جاري التقييم..."):
                    # ← إصلاح: classify يعيد tuple (category, confidence, keywords)
                    category, confidence, _ = legal_classifier.classify(case_details)
                    # ← إصلاح: quick_analyze يأخذ (case_text, category) الآن
                    analysis = case_analyzer.quick_analyze(case_details, category)
                _display_strength_result(analysis, category)

    with col2:
        if st.button("🤖 تقييم AI متعمق", use_container_width=True, key="btn_ai_strength"):
            if not case_details.strip():
                st.warning("الرجاء إدخال تفاصيل القضية.")
            else:
                with st.spinner("جاري التحليل المتعمق..."):
                    # ← إصلاح: analyze_with_ai يأخذ (case_text, call_ai_fn)
                    analysis = case_analyzer.analyze_with_ai(case_details, api.ai_call)
                    category, _, _ = legal_classifier.classify(case_details)
                _display_strength_result(analysis, category)


def _display_strength_result(analysis: dict, category: str):
    """عرض نتيجة تقييم القضية."""
    score = analysis.get("score", 5)
    if score >= 8:
        strength, color, icon = "قوية جداً", "#4ade80", "💪"
    elif score >= 6:
        strength, color, icon = "قوية", "#4a9eff", "👍"
    elif score >= 4:
        strength, color, icon = "متوسطة", "#ffb400", "🤔"
    else:
        strength, color, icon = "ضعيفة", "#ff5a5a", "❌"

    st.markdown(f"""
    <div class='card' style='border-right: 4px solid {color};'>
        <h2 style='color: {color};'>{icon} درجة القوة: {score}/10 — {strength}</h2>
        <p><strong>احتمال النجاح:</strong> {analysis.get('success_probability', '50%')}</p>
        <p><strong>تصنيف القضية:</strong> {category}</p>
    </div>""", unsafe_allow_html=True)

    analysis_text = analysis.get("analysis", "")
    if analysis_text:
        st.markdown("### 📝 التحليل التفصيلي:")
        st.markdown(f"<div class='card'>{analysis_text}</div>", unsafe_allow_html=True)

    recs = analysis.get("recommendations", [])
    if recs:
        st.markdown("### 💡 التوصيات العملية:")
        for rec in recs:
            if rec:
                st.markdown(f"✅ {rec}")


# ============================================================
# 5. تقييم التسوية
# ============================================================
def run_settlement():
    st.markdown("<div class='section-title'>🤝 تقييم خيارات التسوية</div>", unsafe_allow_html=True)

    case_details = st.text_area(
        "تفاصيل القضية:",
        height=250,
        placeholder="صف القضية، المطالبات، والمبلغ المتوقع...",
        key="settlement_input",
    )

    if st.button("🤝 تقييم خيارات التسوية", use_container_width=True, key="btn_settlement"):
        if not case_details.strip():
            st.warning("الرجاء إدخال تفاصيل القضية.")
        else:
            with st.spinner("جاري تقييم خيارات التسوية..."):
                prompt = (
                    f"أنت مستشار قانوني خبير في التسوية الودية للمنازعات العمالية السعودية.\n\n"
                    f"قيّم خيارات التسوية لهذه القضية:\n{case_details}\n\n"
                    f"قدّم:\n"
                    f"1. هل التسوية الودية مناسبة لهذه القضية؟\n"
                    f"2. نطاق التسوية المقبول (الحد الأدنى والأقصى)\n"
                    f"3. استراتيجية التفاوض المثلى\n"
                    f"4. مقارنة بين التسوية ورفع الدعوى\n"
                    f"5. التوصية النهائية"
                )
                settlement = api.ai_call(
                    prompt, [],
                    legal_tools.PERSONA_PROMPTS.get("advisor", "أنت مستشار قانوني خبير.")
                )
            st.markdown("### 🤝 تقييم خيارات التسوية:")
            st.markdown(f"<div class='card'>{settlement}</div>", unsafe_allow_html=True)


# ============================================================
# 6. استخراج المعلومات من المستندات
# ============================================================
def run_info_extractor():
    st.markdown("<div class='section-title'>🔎 استخراج المعلومات القانونية</div>", unsafe_allow_html=True)

    text = st.text_area(
        "النص المراد تحليله:",
        height=200,
        placeholder="ادخل نص العقد، المراسلة، أو أي مستند قانوني...",
        key="extractor_input",
    )

    if st.button("🔎 استخراج المعلومات", use_container_width=True, key="btn_extract"):
        if not text.strip():
            st.warning("الرجاء إدخال النص.")
        else:
            extracted = info_extractor.extract_all(text)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("### 📅 التواريخ المكتشفة")
                dates = extracted.get("dates", [])
                if dates:
                    for d in dates:
                        st.markdown(f"- `{d}`")
                else:
                    st.info("لا توجد تواريخ")
            with col2:
                st.markdown("### 💰 المبالغ المالية")
                amounts = extracted.get("amounts", [])
                if amounts:
                    for a in amounts:
                        st.markdown(f"- `{a}`")
                else:
                    st.info("لا توجد مبالغ")
            with col3:
                st.markdown("### 📋 المواد القانونية")
                articles = extracted.get("articles", [])
                if articles:
                    for art in articles:
                        st.markdown(f"- `{art}`")
                else:
                    st.info("لا توجد مواد")
