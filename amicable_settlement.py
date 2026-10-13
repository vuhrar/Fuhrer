# amicable_settlement.py
"""
صياغة طلب التسوية الودية (منصة تراضي) — المرحلة 5.

تراضي: الخدمة الإلكترونية لوزارة الموارد البشرية والتنمية الاجتماعية التي
تُنظّم المرحلة الأولى الإلزامية لأي نزاع عمالي قبل المحكمة العمالية — مجانية
للعامل، مدتها 21 يوم عمل، والدخول عبر النفاذ الوطني الموحد أو أبشر (مؤكَّد
ببحث مباشر مستقل عن legal_intelligence.OFFICIAL_SOURCES، لا من الذاكرة فقط).

لماذا هذه الوحدة مهمة بالذات: طلب التسوية الودية ليس إجراءً شكليًا منفصلاً
عن الدعوى — هو الأساس الذي يُبنى عليه كل ما يليه في الحالتين:
1. **إن تمت المصالحة**: نص الاتفاق هو ما يَحكم العلاقة بعدها؛ صياغة ضعيفة
   هنا (كإبراء عام غامض) قد تُسقط حقوقًا لم يقصد العامل التنازل عنها.
2. **إن فشلت المصالحة**: محضر التعذر يُحيل الملف للمحكمة العمالية، وما
   وثّقه الطلب الأصلي من وقائع ومطالبات يصبح الأساس الذي تُقاس عليه
   صحيفة الدعوى اللاحقة — تناقض أو نقص هنا قد يُضعف الموقف لاحقًا.

لذلك هذه الوحدة تخدم اتجاهين معًا بتصميم مقصود:
- `AmicableSettlementRequestDrafter` — يصوغ طلبًا شاملاً محتفظًا بالحقوق
  صراحةً، بصياغة وقائعية محايدة لا تُقدّم أي تنازل أو إقرار ضمني.
- `SettlementOfferReviewer` — يفحص أي عرض تسوية **مُقترَح** (نص فعلي يُرفع)
  بحثًا عن صياغات خطرة (كالإبراء العام المطلق) قبل التوقيع — بقواعد نصية
  صريحة فقط، لا استنتاج، تمامًا على نهج correspondence_intelligence.py.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

# الأنواع الخمسة التي تختص بها إدارة التسويات الودية فعليًا (مؤكَّدة ببحث مباشر)
DISPUTE_SUBJECT_CATEGORIES = [
    {"key": "wages_contract_injury", "label": "منازعات متعلقة بعقود العمل والأجور والحقوق وإصابات العمل والتعويض"},
    {"key": "dismissal", "label": "منازعات مترتبة على الفصل من العمل"},
    {"key": "disciplinary", "label": "منازعات متعلقة بإيقاع صاحب العمل جزاءات تأديبية على العامل"},
    {"key": "labor_law_subjects", "label": "منازعات متعلقة بالعمال الخاضعين لأحكام نظام العمل"},
    {"key": "labor_law_application", "label": "منازعات ناشئة عن تطبيق أحكام نظام العمل ولائحته التنفيذية"},
]

REQUIRED_FIELDS = ["بيانات المدعي", "مكتب التسوية والاختصاص المكاني", "بيانات المدعى عليه", "بيانات العمل", "موضوع الدعوى", "المستندات", "إقرار عدم كيدية الدعوى"]


def entitlements_worksheet_to_claims(worksheet: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    جسر تكامل مباشر: يحوّل مخرج legal_tools.full_entitlements_worksheet
    (المرحلة 3) إلى شكل claims المتوافق مباشرة مع AmicableSettlementRequestDrafter.draft
    (هذه المرحلة) — بلا أي إعادة تنسيق يدوي بين المحركين. كل بند بمبلغ
    None (كتعويض نقص الإشعار الذي لا صيغة نظامية صريحة له) يُمرَّر كما هو
    بلا اختلاق رقم له، تمامًا كأصل تصميمه في full_entitlements_worksheet.
    """
    claims = []
    for item in worksheet.get("items", []):
        basis = item.get("legal_basis")
        basis_str = f"المادة {basis['article']}" if isinstance(basis, dict) and basis.get("article") else ""
        claims.append({"title": item.get("item", "مطالبة"), "legal_basis": basis_str, "amount": item.get("amount")})
    return claims


# ============================================================
# 1. صياغة طلب التسوية الودية
# ============================================================
class AmicableSettlementRequestDrafter:
    """كل فقرة وقائية هنا مكتوبة عمدًا، لا مُضافة شكليًا — راجع protective_notes في المخرج لفهم وظيفة كل فقرة."""

    def draft(
        self,
        plaintiff_name: str = "",
        plaintiff_id: str = "",
        plaintiff_contact: str = "",
        defendant_name: str = "",
        defendant_cr_number: str = "",
        workplace_location: str = "",
        job_title: str = "",
        start_date: str = "",
        end_date: str = "",
        dispute_category_key: str = "dismissal",
        facts: Optional[List[Dict[str, str]]] = None,
        claims: Optional[List[Dict[str, Any]]] = None,
        evidence: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """facts: [{"date": "YYYY-MM-DD"|None, "text": "..."}]. claims: [{"title": "...", "legal_basis": "...", "amount": float|None}]."""
        facts = facts or []
        claims = claims or []
        evidence = evidence or []
        today = datetime.now().strftime("%Y-%m-%d")

        category = next((c for c in DISPUTE_SUBJECT_CATEGORIES if c["key"] == dispute_category_key), DISPUTE_SUBJECT_CATEGORIES[1])

        # الوقائع: مرتّبة زمنيًا (المؤرَّخة أولًا)، بصياغة وقائعية محايدة — لا إضافة تأويل هنا
        dated = sorted([f for f in facts if f.get("date")], key=lambda x: x["date"])
        undated = [f for f in facts if not f.get("date")]
        facts_lines = [f"{i}. [{f['date']}] {f['text']}" for i, f in enumerate(dated, 1)]
        facts_lines += [f"{i}. [تاريخ غير محدد — يلزم تحديده قبل التقديم] {f['text']}" for i, f in enumerate(undated, len(dated) + 1)]

        # المطالبات: مرقمة، كل واحدة مع أساسها النظامي ومبلغها إن وُجد
        claims_lines = []
        for i, c in enumerate(claims, 1):
            amount_txt = f" — المبلغ المُقدَّر: {c['amount']:,.2f} ريال" if c.get("amount") is not None else " — المبلغ: يُحدَّد لاحقًا أو يُترك لتقدير مكتب التسوية"
            basis_txt = f" (الأساس: {c['legal_basis']})" if c.get("legal_basis") else " (الأساس: يحتاج تحديدًا)"
            claims_lines.append(f"{i}. {c.get('title', 'مطالبة')}{basis_txt}{amount_txt}")

        evidence_lines = [f"{i}. {e}" for i, e in enumerate(evidence, 1)] or ["— يُرفق لاحقًا —"]

        document = f"""بسم الله الرحمن الرحيم

                    طلب تسوية ودية — منصة تراضي (مسودة للمراجعة قبل التقديم)

التاريخ: {today}

أولاً: بيانات المدعي (العامل)
- الاسم: {plaintiff_name or '____________ (يُستكمل من بيانات النفاذ الوطني عند التقديم الفعلي)'}
- رقم الهوية: {plaintiff_id or '____________'}
- وسيلة التواصل: {plaintiff_contact or '____________'}

ثانياً: بيانات المدعى عليه (صاحب العمل)
- الاسم/المنشأة: {defendant_name or '____________'}
- رقم السجل التجاري (إن وُجد): {defendant_cr_number or '____________'}

ثالثاً: بيانات العمل
- موقع/مقر العمل: {workplace_location or '____________ (يحدد مكتب التسوية المختص مكانيًا)'}
- المسمى الوظيفي: {job_title or '____________'}
- تاريخ المباشرة: {start_date or '____________'}
- تاريخ انتهاء العلاقة (إن وُجد): {end_date or '____________ / العلاقة قائمة'}

رابعاً: تصنيف موضوع الدعوى
{category['label']}

خامساً: الوقائع (مرتّبة زمنيًا)
{chr(10).join(facts_lines) or '— لم تُدخَل وقائع بعد —'}

سادساً: المطالبات
{chr(10).join(claims_lines) or '— لم تُدخَل مطالبات بعد —'}

سابعاً: الأدلة والمستندات المرفقة
{chr(10).join(evidence_lines)}

ثامناً: فقرة حفظ الحقوق (صياغة وقائعية — راجع protective_notes لشرح كل بند)
يتقدم المدعي بهذا الطلب محتفظًا بكامل حقوقه النظامية كافة، ولا يُعدّ تقديم
هذا الطلب أو المشاركة في جلسات التسوية الودية تنازلاً عن أي حق أو مطالبة
لم يرد ذكرها صراحةً أعلاه. وأي عرض أو مقترح يُطرح أثناء جلسات التسوية لا
يُعتبر إقرارًا من أي طرف بصحة أو عدم صحة أي مطالبة، ولا ينتج أي أثر ملزم
على أي من الطرفين إلا باتفاق تسوية نهائي مكتوب وموقّع من الطرفين صراحةً.

تاسعاً: إقرار عدم كيدية الدعوى
يقرّ مقدّم الطلب بأن هذا الطلب مقدَّم بحسن نية ولغرض مشروع هو تسوية نزاع
عمالي فعلي، لا بقصد الكيد أو الإضرار.

— مسودة للمراجعة الذاتية قبل التقديم الفعلي عبر منصة تراضي؛ راجع كل حقل
فارغ (____________) واستكمله، وراجع محاميًا قبل التقديم إن كانت المطالبة
كبيرة القيمة أو معقدة —
"""

        required_status = {
            "بيانات المدعي": bool(plaintiff_name and plaintiff_id),
            "مكتب التسوية والاختصاص المكاني": bool(workplace_location),
            "بيانات المدعى عليه": bool(defendant_name),
            "بيانات العمل": bool(job_title or start_date),
            "موضوع الدعوى": True,
            "المستندات": bool(evidence),
            "إقرار عدم كيدية الدعوى": True,
        }
        missing = [k for k, v in required_status.items() if not v]

        return {
            "document_text": document,
            "dispute_category": category,
            "required_fields_status": required_status,
            "missing_required_fields": missing,
            "undated_facts_count": len(undated),
            "protective_notes": [
                "فقرة حفظ الحقوق تمنع اعتبار المشاركة في التسوية تنازلاً ضمنيًا عن مطالبات لم تُذكر — بدونها، قد يُحتج لاحقًا بأن سكوتك عن مطالبة الآن يعني تنازلك عنها.",
                "عبارة 'لا ينتج أثر ملزم إلا باتفاق مكتوب وموقّع' تحمي من اعتبار نقاش أو عرض شفهي أثناء الجلسة التزامًا نهائيًا قبل التوقيع الفعلي.",
                "صياغة الوقائع وقائعية محايدة (تاريخ + فعل) عمدًا لا تأويلية — أي تناقض بين وصف الواقعة هنا ووصفها لاحقًا في صحيفة الدعوى (إن فشلت التسوية) قد يُستخدم ضدك.",
                f"{len(undated)} واقعة بلا تاريخ — حدّد التاريخ قبل التقديم؛ الوقائع غير المؤرَّخة تُضعف وضوح الجدول الزمني أمام مكتب التسوية.",
            ],
            "disclaimer": "مسودة أولية للمراجعة الذاتية، وليست نصًا نهائيًا جاهزًا للتقديم. راجع محاميًا مرخّصًا قبل التقديم الفعلي عبر منصة تراضي، خصوصًا عند مطالبات كبيرة القيمة أو وقائع متنازع عليها.",
        }


# ============================================================
# 2. فحص عرض تسوية مُقترَح — قواعد نصية صريحة، لا استنتاج
# ============================================================
SETTLEMENT_RED_FLAG_PATTERNS = [
    {
        "key": "broad_general_release",
        "label": "إبراء عام مطلق يتجاوز موضوع هذا النزاع تحديدًا",
        "pattern": re.compile(r"(?:إبراء عام|إبراء مطلق|براءة ذمة تامة|تنازل عن كافة الحقوق|لا مطالبات.{0,10}مهما كان نوعها|أي مطالبات حالية أو مستقبلية)[^.؛\n]{0,100}"),
        "severity": "مرتفع",
        "explanation": "صياغة كهذه قد تُسقط حقوقًا لا علاقة لها بموضوع هذا النزاع تحديدًا (كمستحقات مستقبلية أو مطالبات غير مكتشفة بعد) — طالب بحصر الإبراء في بنود النزاع المحدد المتفق عليه فقط.",
    },
    {
        "key": "no_specific_amount",
        "label": "غياب مبلغ رقمي محدد",
        "pattern": re.compile(r"مبلغ مناسب|مبلغ يُحدَّد لاحقًا|تعويض عادل بدون تحديد"),
        "severity": "مرتفع",
        "explanation": "اتفاق بلا رقم محدد صعب التنفيذ أو الإثبات لاحقًا — اطلب رقمًا صريحًا بالريال قبل التوقيع.",
    },
    {
        "key": "no_payment_deadline",
        "label": "غياب تاريخ سداد محدد",
        "pattern": re.compile(r"في أقرب وقت|حسب الإمكان|عند التيسّر|دون تحديد موعد"),
        "severity": "متوسط",
        "explanation": "موعد سداد غامض يصعب معه إثبات الإخلال لاحقًا — اطلب تاريخًا محددًا (يوم/شهر/سنة).",
    },
]

SETTLEMENT_GOOD_PRACTICE_PATTERNS = [
    {"key": "specific_amount_present", "label": "مبلغ رقمي محدد بالريال", "pattern": re.compile(r"\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*(?:ريال|SR|ر\.س)")},
    {"key": "specific_date_present", "label": "تاريخ محدد (سداد أو تنفيذ)", "pattern": re.compile(r"\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}")},
    {"key": "itemized_breakdown", "label": "تفصيل بنود منفصلة (لا مبلغ إجمالي غامض)", "pattern": re.compile(r"(?:أولاً|ثانياً|ثالثاً|بند|1\.|2\.)")},
]


class SettlementOfferReviewer:
    """يفحص نص عرض تسوية فعلي مُقترَح — كل نتيجة تحمل اقتباسًا حرفيًا، لا حكمًا بصحة أو بطلان العرض."""

    def review(self, offer_text: str) -> Dict[str, Any]:
        red_flags, good_practices = [], []
        for pat in SETTLEMENT_RED_FLAG_PATTERNS:
            for m in pat["pattern"].finditer(offer_text):
                red_flags.append({"key": pat["key"], "label": pat["label"], "severity": pat["severity"], "quoted_text": m.group(0).strip(), "explanation": pat["explanation"]})
        for pat in SETTLEMENT_GOOD_PRACTICE_PATTERNS:
            m = pat["pattern"].search(offer_text)
            good_practices.append({"key": pat["key"], "label": pat["label"], "present": bool(m), "quoted_text": m.group(0).strip() if m else None})

        return {
            "red_flags": red_flags,
            "good_practices": good_practices,
            "overall_note": (
                f"عُثر على {len(red_flags)} صياغة تحتاج انتباهًا خاصًا قبل التوقيع." if red_flags
                else "لم تُكتشف صياغات من الأنماط المعروفة الخطرة في هذا النص — هذا لا يعني أن العرض عادل أو كافٍ، فقط أنه لم يحوِ أحد الأنماط المحددة التي يفحصها هذا الماسح."
            ),
            "scope": "قواعد نصية صريحة فقط (لا نموذج ذكاء اصطناعي، لا استنتاج بلا دليل) — تفحص أنماطًا معروفة سلفًا؛ لا تُغني عن قراءة النص كاملًا.",
            "disclaimer": "هذا فحص أولي آلي لصياغات شائعة الخطورة، وليس رأيًا قانونيًا بعدالة العرض أو كفايته. لا توقّع أي إبراء نهائي قبل استلام كامل المبلغ المتفق عليه فعليًا ومراجعة محامٍ مرخّص، خصوصًا عند مبالغ كبيرة.",
        }


def pre_signature_checklist() -> List[str]:
    """قائمة مرجعية عامة — لا تحتاج نصًا مُدخلاً، للقراءة قبل أي جلسة تسوية."""
    return [
        "لا توقّع أي إبراء أو تنازل نهائي قبل استلام كامل المبلغ المتفق عليه فعليًا (لا وعدًا بالاستلام).",
        "تأكد أن المبلغ مذكور رقميًا بالريال، لا بعبارات عامة مثل 'مبلغ مناسب'.",
        "تأكد أن تاريخ السداد محدد بيوم/شهر/سنة، لا بعبارات مثل 'في أقرب وقت'.",
        "اطلب حصر الإبراء في بنود هذا النزاع المحدد فقط، لا 'كافة الحقوق الحالية والمستقبلية'.",
        "احتفظ بنسخة موقّعة من أي اتفاق نهائي، ولا تكتفِ بموافقة شفهية في الجلسة.",
        "إن كانت المطالبة كبيرة القيمة أو العرض يتضمن صياغة قانونية معقدة، استشر محاميًا قبل التوقيع — الإبراء الموقَّع يصعب جدًا التراجع عنه لاحقًا.",
    ]
