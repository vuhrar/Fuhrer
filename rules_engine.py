# rules_engine.py
"""
محرك القواعد - قواعد عمالية فقط (تمت تنقيتها وحذف القواعد الجنائية/التجارية).
"""
import re, operator
from typing import List, Dict

# القواعد العمالية فقط (تمت تصفيتها من القواعد الجنائية والتجارية)
RULES = [
    # العمل والانقطاع
    {"c": "days_abandoned>30", "o": "⚠️ انقطاع >30 يوم (ترك العمل) - يُمكن اعتباره استقالة ضمنية ما لم يثبت عذر.", "cat": "عمل"},
    {"c": "days_abandoned>15 and days_abandoned<=30", "o": "⚠️ انقطاع 15-30 يوم (يستوجب إنذاراً قبل الفصل)", "cat": "عمل"},
    {"c": "absence_days>30", "o": "⚠️ غياب >30 يوم (يُمكن الفصل بعد التحقيق)", "cat": "غياب"},
    {"c": "absence_days>20 and absence_days<=30", "o": "⚠️ غياب 20-30 يوم (إنذار ثانٍ)", "cat": "غياب"},
    {"c": "absence_days>15 and absence_days<=20", "o": "⚠️ غياب 15-20 يوم (إنذار أول)", "cat": "غياب"},

    # التقادم
    {"c": "days_since_firing>365", "o": "⛔ مضى >سنة على الفصل (سقط حق التقاضي - المادة 84 من نظام المرافعات)", "cat": "تقادم"},
    {"c": "days_since_firing>180 and days_since_firing<=365", "o": "⏳ مضى >6 أشهر (تقادم جزئي - يُنصح بالإسراع)", "cat": "تقادم"},

    # الإجراءات والفصل
    {"c": "no_investigation", "o": "⚖️ فصل بلا تحقيق (بطلان القرار - المادة 80)", "cat": "إجراءات"},
    {"c": "arbitrary_dismissal", "o": "⚖️ فصل تعسفي (يستوجب تعويضاً - المادة 77 و 81)", "cat": "عمل"},
    {"c": "salary_delay", "o": "⚖️ تأخير الراتب (يستوجب تعويضاً - المادة 90)", "cat": "عمل"},
    {"c": "eosb_not_paid", "o": "⚖️ مكافأة نهاية الخدمة لم تُصرف (المادة 84)", "cat": "عمل"},
    {"c": "notification_late", "o": "⚖️ تبليغ بعد 7 أيام (إخلال إجرائي)", "cat": "إجراءات"},
    {"c": "judgment_without_hearing", "o": "⚖️ حكم دون سماعك (بطلان - المادة 17 من نظام المرافعات)", "cat": "إجراءات"},
    {"c": "no_response_90_days", "o": "⚖️ 90 يوم بلا رد (موافقة ضمنية)", "cat": "إجراءات"},

    # مدة الخدمة والمكافأة
    {"c": "service_length<2", "o": "📌 خدمة <2 سنة (نصف شهر عن كل سنة - المادة 84)", "cat": "مكافأة"},
    {"c": "service_length>=2 and service_length<5", "o": "📌 خدمة 2-5 سنوات (شهر عن كل سنة - المادة 84)", "cat": "مكافأة"},
    {"c": "service_length>=5", "o": "📌 خدمة ≥5 سنوات (شهر ونصف عن كل سنة - المادة 84)", "cat": "مكافأة"},

    # الصلح والتفاوض
    {"c": "settlement_offer is True and risk_score>60", "o": "🤝 الصلح أفضل من التقاضي (لتجنب المخاطر)", "cat": "صلح"},
    {"c": "settlement_offer is True and risk_score<=40", "o": "⚖️ الصلح ممكن والقضية قوية (يمكنك المطالبة بأكثر)", "cat": "صلح"},
    {"c": "offer_rejected_by_opponent", "o": "📌 رفض الخصم الصلح (يُعتبر تعنتاً - يُحسب لصالحك)", "cat": "صلح"},

    # تعارضات وتناقضات
    {"c": "ambiguous_count>3", "o": "🔍 عبارات غامضة (طعن محتمل في الدعوى)", "cat": "لغوي"},
    {"c": "contradictions>1", "o": "⚡ تناقض في مراسلات الخصم (يُضعف موقفه)", "cat": "تناقضات"},

    # أعذار
    {"c": "force_majeure is True and days_abandoned>60", "o": "📌 عذر قاهر يبرر الانقطاع (مثل الحجز أو المرض)", "cat": "أعذار"},
    {"c": "proven_illness", "o": "📌 مرض مثبت (عذر مقبول - يُلغي الفصل)", "cat": "أعذار"},
    {"c": "natural_disaster", "o": "📌 كارثة طبيعية (قوة قاهرة - عذر مشروع)", "cat": "أعذار"},
    {"c": "travel_ban", "o": "📌 منع السفر (قوة قاهرة - عذر مشروع)", "cat": "أعذار"},
    {"c": "death_of_relative", "o": "📌 وفاة قريب (إجازة رسمية - عذر مقبول)", "cat": "أعذار"},

    # الغرامات والمخالفات
    {"c": "disproportionate_fine", "o": "⚖️ غرامة غير متناسبة (تُخفَّض أو تُلغى)", "cat": "غرامات"},
    {"c": "fine_illegal", "o": "⚖️ غرامة مخالفة للنظام (تُلغى)", "cat": "غرامات"},

    # إجراءات المحكمة
    {"c": "expert_request_denied", "o": "⚖️ رفض الخبرة (إخلال بحق الدفاع)", "cat": "إجراءات"},
    {"c": "non_judicial_acknowledgment", "o": "📌 إقرار غير قضائي (حجة على المُقِر - المادة 17 من نظام الإثبات)", "cat": "مستندات"},
    {"c": "opponent_threatens", "o": "⚖️ تهديد متكرر (يُعتبر تعسفاً - يُحسب لصالحك)", "cat": "سلوك"},
    {"c": "witnesses_conflict", "o": "⚖️ تناقض الشهود (تُرجح الأعدل)", "cat": "شهادات"},
    {"c": "two_vs_one_witness", "o": "📌 شاهدان ضد واحد (مقبول - المادة 79 من نظام الإثبات)", "cat": "شهادات"},
    {"c": "no_registered_letter", "o": "⚖️ تبليغ بغير بريد مسجل (إخلال إجرائي)", "cat": "إجراءات"},
    {"c": "doc_unsigned", "o": "⚖️ مستند غير موقع (لا حجية له - المادة 40 من نظام الإثبات)", "cat": "مستندات"},
    {"c": "forgery_proven", "o": "🚨 تزوير مثبت (جريمة جنائية - إحالة للنيابة العامة)", "cat": "مستندات"},
    {"c": "opponent_hides_doc", "o": "⚖️ الخصم يخفي مستنداً (يُحكم ضده - المادة 34 من نظام الإثبات)", "cat": "مستندات"},
]

OPS = {">": operator.gt, ">=": operator.ge, "<": operator.lt, "<=": operator.le, "==": operator.eq, "!=": operator.ne}

def eval_simple_condition(cond: str, ctx: dict) -> bool:
    cond = cond.strip()
    # flag
    if re.fullmatch(r"[A-Za-z_]\w*$", cond):
        return bool(ctx.get(cond, False))
    # is True/False
    m = re.match(r"^([A-Za-z_]\w*)\s+is\s+(True|False)$", cond)
    if m:
        return bool(ctx.get(m.group(1), False)) == (m.group(2) == "True")
    # numeric comparison
    m = re.match(r"^([A-Za-z_]\w*)\s*(>=|<=|>|<|==|!=)\s*([0-9]+(?:\.[0-9]+)?)$", cond)
    if m:
        lhs = float(ctx.get(m.group(1), 0))
        rhs = float(m.group(3))
        return OPS[m.group(2)](lhs, rhs)
    # string equality
    m = re.match(r"^([A-Za-z_]\w*)\s*==\s*'([^']*)'$", cond)
    if m:
        return str(ctx.get(m.group(1), "")) == m.group(2)
    return False

def eval_rule_v2(expression: str, ctx: dict) -> bool:
    parts = [p.strip() for p in expression.split(" and ") if p.strip()]
    return all(eval_simple_condition(p, ctx) for p in parts)

def apply_rules(ctx: dict, rules=RULES) -> List[Dict]:
    return [{"text": r["o"], "cat": r["cat"]} for r in rules if eval_rule_v2(r["c"], ctx)]
