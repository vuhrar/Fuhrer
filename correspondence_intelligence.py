# correspondence_intelligence.py
"""
محرك تحليل المراسلات الإلكترونية — المرحلة 4.

الغرض: فحص المراسلات بين الموظف وصاحب العمل (عبر منصة إلكترونية رسمية)،
ورفع ما قد يخدم موقف الموظف وما قد يُستخدم ضده، وربط المراسلات ببعضها زمنيًا.

القيد الصارم الذي صُمم حوله هذا الملف بالكامل: **لا استنتاج ولا تخمين بلا
دليل نصي مباشر**. لذلك:
- كل نتيجة تحمل `quoted_text` — المقتطف الحرفي من النص الأصلي، لا ملخصًا
  ولا إعادة صياغة. لو لم يوجد نص حرفي مطابق، لا توجد نتيجة.
- كل نتيجة تحمل `possible_interpretations` — قائمة بأكثر من احتمال حيثما
  أمكن، لا تفسيرًا واحدًا جازمًا. المحرك لا "يقرر" ماذا يعني النص؛ يعرضه
  مع الاحتمالات ويترك الحكم للمستخدم أو لمحاميه.
- أي عنصر مراسلة ينقصه تاريخ لا يُفترض له مكان في الترتيب الزمني؛ يُرفع
  صراحة في needs_more_info ويُستبعد من الجدول المرتّب بدل تخمين مكانه فيه.
- لا يوجد "درجة قوة" أو نسبة احتمال نجاح هنا — نفس المبدأ الذي استُبعدت
  لأجله CaseStrengthAnalyzer في المرحلة صفر.

ملاحظة تبسيط مقصودة: لا يُشترط هنا تحديد/فحص هوية "الطرف المرسل" لكل
مراسلة ولا يُطلَب كحقل ناقص. المراسلات تتم عبر نظام إلكتروني حكومي رسمي
توثّق هويته أصلًا من المنصة نفسها، فلا حاجة لازدواج ذلك هنا. الحقل الوحيد
المطلوب فعليًا لتفعيل الترتيب الزمني والربط الدقيق هو التاريخ.

هذا محرك قواعد نصية صريحة (regex) لا نموذج ذكاء اصطناعي — اختيار مقصود:
القواعد النصية تضمن ألا تُنتج النتيجة إلا من نص موجود فعليًا، بينما استدعاء
نموذج AI لتلخيص أو "فهم" المراسلات يفتح الباب لتوليد استنتاجات لا نص حرفيًا
وراءها، بالضبط ما يرفضه المستخدم صراحةً.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from legal_tools import info_extractor

# ============================================================
# مكتبة الأنماط — كل نمط: مفتاح، نص الاقتباس المطلوب، تفسيرات محتملة متعددة
# (لا تفسير واحد جازم)، ومادة نظامية ذات صلة إن وُجدت.
# ============================================================

FAVORABLE_PATTERNS = [
    {
        "key": "employer_admits_wage_delay",
        "label": "لغة تقر بتأخير أو عدم صرف مستحق من جهة صاحب العمل",
        "pattern": re.compile(r"(?:نعتذر عن|يؤسفنا)\s*(?:التأخير|عدم صرف|تأخر صرف)[^.؛\n]{0,120}|(?:لم نتمكن من صرف|تعذر صرف|سيتأخر صرف)[^.؛\n]{0,120}"),
        "possible_interpretations": [
            "قد يكون إقرارًا صريحًا من صاحب العمل بتأخر الأجر، وهو ما تتناوله المادة 90.",
            "قد يكون إشعارًا إداريًا روتينيًا (كتأخير تقني قصير) بلا دلالة إقرارية قوية بالإخلال.",
        ],
        "related_article": "90",
    },
    {
        "key": "employer_commitment_unconfirmed",
        "label": "التزام أو وعد من صاحب العمل لم يُؤكَّد تنفيذه في المراسلات المرفوعة",
        "pattern": re.compile(r"(?:سيتم|سنقوم ب|سنعمل على)\s*(?:صرف|تسوية|تعويض|معالجة)[^.؛\n]{0,120}|تم الاتفاق على\s*(?:صرف|تسوية)[^.؛\n]{0,120}"),
        "possible_interpretations": [
            "التزام لم يُنفَّذ بعد قدر ما تُظهره المراسلات المرفوعة — تحقق من وجود مراسلة لاحقة تؤكد التنفيذ.",
            "قد يكون نُفِّذ فعليًا خارج هذه المراسلات (كإيداع بنكي) ولم تُرفع المراسلة المؤكِّدة بعد.",
        ],
        "related_article": None,
    },
    {
        "key": "termination_language_no_stated_article_81_ground",
        "label": "لغة إنهاء خدمة دون ذكر أي من حالات المادة 81 الحصرية الثلاث ضمن النص نفسه",
        "pattern": re.compile(r"(?:تم إنهاء|سيتم إنهاء|قررنا إنهاء)\s*(?:خدمتك|خدماتك|عقدك|عملك)[^.؛\n]{0,150}"),
        "possible_interpretations": [
            "ملاحظة على ما ورد حرفيًا في هذا النص فقط: لا يحتوي إشارة إلى اعتداء أو غياب غير مبرر أو إفشاء أسرار (حالات المادة 81 الحصرية) — إن لم يُذكر سبب محدد في أي مستند آخر، هذا يقترب من نمط الفصل التعسفي (المادة 77).",
            "قد يكون السبب مذكورًا في مستند آخر لم يُرفع بعد (كخطاب إنذار سابق)، فلا يُفترض غياب السبب فعليًا من هذا النص وحده.",
        ],
        "related_article": "81",
    },
    {
        "key": "retaliation_adjacent_sequence",
        "label": "لغة تربط إجراءً ضد الموظف بشكوى أو مطالبة سابقة منه",
        "pattern": re.compile(r"(?:بعد|نتيجة|عقب)\s*(?:شكواك|تقديمك شكوى|مطالبتك|تواصلك مع)[^.؛\n]{0,120}"),
        "possible_interpretations": [
            "قد يشير إلى تسلسل زمني بين شكوى الموظف وإجراء لاحق ضده (مؤشر انتقام محتمل يحتاج تدقيقًا في التواريخ).",
            "قد يكون مجرد إشارة سياقية محايدة لا علاقة لها بأي إجراء تأديبي أو ضار.",
        ],
        "related_article": None,
    },
    {
        "key": "employer_instructs_unpaid_extra_work",
        "label": "تكليف بعمل إضافي أو مهام خارج النطاق المتفق عليه دون ذكر مقابل",
        "pattern": re.compile(r"(?:مطلوب منك|عليك|يجب أن تقوم ب)\s*(?:العمل|الحضور|إنجاز)[^.؛\n]{0,60}(?:عطلة|إجازة|خارج الدوام|نهاية الأسبوع)[^.؛\n]{0,100}"),
        "possible_interpretations": [
            "قد يشير إلى عمل إضافي يستحق أجرًا وفق المادة 106 إن لم يُدفع مقابله.",
            "قد يكون ضمن نطاق عمل متفق عليه مسبقًا بمقابل منفصل غير مذكور في هذا النص فقط.",
        ],
        "related_article": "106",
    },
]

CAUTIONARY_PATTERNS = [
    {
        "key": "employee_resignation_language",
        "label": "لغة من الموظف نفسه تفيد تقديم استقالة طوعية",
        "pattern": re.compile(r"(?:أقدم استقالتي|أرغب في الاستقالة|أود الاستقالة|سأترك العمل طواعية|استقالتي من العمل)[^.؛\n]{0,100}"),
        "possible_interpretations": [
            "إن ثبتت كاستقالة طوعية حقيقية، هذا يُغيّر نسبة مكافأة نهاية الخدمة المستحقة (راجع severance_pay) وينفي عادة أساس الفصل التعسفي.",
            "قد تكون استقالة تحت ضغط أو إكراه من صاحب العمل (استقالة لا تعكس إرادة حرة فعليًا) — هذا يحتاج توثيقًا منفصلًا لظروف كتابتها لا يظهر من نص الاستقالة نفسه.",
        ],
        "related_article": "84",
    },
    {
        "key": "employee_waiver_or_full_settlement_language",
        "label": "لغة من الموظف تفيد إقرارًا باستلام كامل المستحقات أو تنازلًا عن مطالبات",
        "pattern": re.compile(r"(?:أقر باستلام كامل|لا مطالبات لي|تنازلت عن|استلمت كامل مستحقاتي|لا يوجد لدي أي مطالبة)[^.؛\n]{0,100}"),
        "possible_interpretations": [
            "قد يُشكّل إقرارًا أو تسوية نهائية يصعب التراجع عنها لاحقًا في دعوى — يحتاج مراجعة محامٍ فورية قبل أي خطوة أخرى.",
            "قد يكون نصًا موقّعًا تحت ضغط ظرف الإنهاء دون فهم كامل لأثره القانوني؛ قابلية الطعن فيه مسألة قانونية تحتاج تقييم محامٍ، لا تُحسم آليًا هنا.",
        ],
        "related_article": None,
    },
    {
        "key": "employee_admits_misconduct",
        "label": "لغة من الموظف تقر بخطأ أو تقصير",
        "pattern": re.compile(r"(?:أعتذر عن|أقر بخطئي|كان تصرفي غير لائق|أتحمل المسؤولية الكاملة عن)[^.؛\n]{0,100}"),
        "possible_interpretations": [
            "قد يُستخدم لدعم سبب فصل من حالات المادة 81 إن كان الخطأ المقرّ به يطابق إحدى حالاتها الحصرية فعليًا.",
            "اعتذار عام عن خلاف بسيط لا يرقى بالضرورة لأي من حالات المادة 81 الحصرية الثلاث.",
        ],
        "related_article": "81",
    },
    {
        "key": "employee_acknowledges_notice_or_warning",
        "label": "إقرار من الموظف باستلام إنذار أو تنبيه رسمي",
        "pattern": re.compile(r"(?:أقر باستلام|استلمت|تسلمت)\s*(?:الإنذار|التنبيه|خطاب الإنذار|الإشعار)[^.؛\n]{0,100}"),
        "possible_interpretations": [
            "يثبت أن الإجراء التأديبي اتُّخذ باتباع إجراءات إشعار رسمية (ذو صلة بالمادة 155 — العقوبات التأديبية).",
            "الاستلام وحده لا يعني بالضرورة صحة أو تناسب العقوبة ذاتها مع المخالفة.",
        ],
        "related_article": "155",
    },
]


def scan_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """يفحص عنصر مراسلة واحد مقابل كل الأنماط؛ كل نتيجة تحمل الاقتباس الحرفي فقط."""
    text = item.get("text", "") or ""
    item_id = item.get("id", "")
    favorable, cautionary = [], []

    for pat in FAVORABLE_PATTERNS:
        for m in pat["pattern"].finditer(text):
            favorable.append({
                "item_id": item_id, "pattern_key": pat["key"], "label": pat["label"],
                "quoted_text": m.group(0).strip(),
                "possible_interpretations": pat["possible_interpretations"],
                "related_article": pat["related_article"],
            })
    for pat in CAUTIONARY_PATTERNS:
        for m in pat["pattern"].finditer(text):
            cautionary.append({
                "item_id": item_id, "pattern_key": pat["key"], "label": pat["label"],
                "quoted_text": m.group(0).strip(),
                "possible_interpretations": pat["possible_interpretations"],
                "related_article": pat["related_article"],
            })
    return {"favorable_to_user": favorable, "cautionary_for_user": cautionary}


def _cross_link(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    يربط عناصر المراسلة التي تشترك في تاريخ أو مبلغ أو مادة مذكورة صراحةً
    في نصوصها (لا تخمينًا لصلة موضوعية). يعتمد على LegalInfoExtractor
    المبني والمُختبر أصلًا في المرحلة صفر.
    """
    extracted = {item["id"]: info_extractor.extract_all(item.get("text", "")) for item in items}
    links = []
    ids = list(extracted.keys())
    for i, id_a in enumerate(ids):
        for id_b in ids[i + 1:]:
            shared_dates = set(extracted[id_a]["dates"]) & set(extracted[id_b]["dates"])
            shared_amounts = set(extracted[id_a]["amounts"]) & set(extracted[id_b]["amounts"])
            shared_articles = set(extracted[id_a]["articles"]) & set(extracted[id_b]["articles"])
            if shared_dates or shared_amounts or shared_articles:
                links.append({
                    "item_ids": [id_a, id_b],
                    "shared_dates": sorted(shared_dates),
                    "shared_amounts": sorted(shared_amounts),
                    "shared_articles": sorted(shared_articles),
                })
    return links


def analyze_correspondence(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    نقطة الدخول الرئيسية. كل عنصر في items: {id, text, date? (YYYY-MM-DD), channel?}.
    date اختياري لكنه الحقل الوحيد المؤثر فعليًا: أي عنصر ينقصه يُرفع صراحةً
    في needs_more_info ويُستبعد من الجدول الزمني المرتّب بدل افتراض مكانه فيه.
    """
    favorable_all, cautionary_all, needs_more_info = [], [], []
    dated_items, undated_items = [], []

    for item in items:
        item_id = item.get("id", "")
        if not item.get("date"):
            needs_more_info.append({"item_id": item_id, "missing": ["التاريخ"], "action": "أضف تاريخ هذه المراسلة لإدراجها في الترتيب الزمني والربط الدقيق."})

        scan = scan_item(item)
        favorable_all.extend(scan["favorable_to_user"])
        cautionary_all.extend(scan["cautionary_for_user"])

        entry = {"id": item_id, "date": item.get("date"), "channel": item.get("channel"), "favorable_findings": len(scan["favorable_to_user"]), "cautionary_findings": len(scan["cautionary_for_user"])}
        (dated_items if item.get("date") else undated_items).append(entry)

    timeline = sorted(dated_items, key=lambda x: x["date"])
    cross_references = _cross_link(items)

    return {
        "items_analyzed": len(items),
        "favorable_to_user": favorable_all,
        "cautionary_for_user": cautionary_all,
        "cross_references": cross_references,
        "timeline": timeline,
        "undated_items_excluded_from_timeline": undated_items,
        "needs_more_info": needs_more_info,
        "scope": "قواعد نصية صريحة فقط (لا نموذج ذكاء اصطناعي، لا تلخيص، لا استنتاج). كل نتيجة تحمل اقتباسًا حرفيًا من النص الأصلي وأكثر من تفسير محتمل حيثما أمكن.",
        "disclaimer": "هذا فرز أولي لمواضع قد تستحق المراجعة فقط، وليس رأيًا قانونيًا ولا تأكيدًا لصحة أو بطلان أي مستند أو تصرف. راجع كل نتيجة في سياقها الكامل، واستشر محاميًا مرخّصًا قبل اتخاذ أي قرار بناءً عليها.",
    }
