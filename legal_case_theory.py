"""محرك بناء نظرية القضية للنزاعات العمالية.

يبني خريطة ادعاء/عنصر/واقعة/دليل/رد متوقع. لا يصدر حكمًا ولا رأيًا
قانونيًا نهائيًا؛ وظيفته تحويل الملف إلى أسئلة إثبات ومواجهة قابلة للمراجعة.
"""
from __future__ import annotations

from typing import Any, Dict, List

ISSUE_PLAYBOOKS = [
    {
        "key": "wages", "label": "الأجر والاستحقاقات",
        "signals": ("راتب", "أجر", "بدل", "مستحق", "تحويل", "خصم", "مكافأة"),
        "elements": ["وجود علاقة العمل", "الأجر المتفق عليه أو المستحق", "الفترة محل المطالبة", "عدم السداد أو النقص", "مقدار المطالبة ومصدره"],
        "proof": ["عقد العمل", "مسيرات وكشوف الأجور", "كشوف الحساب والتحويلات", "المراسلات", "سجل الحضور والدوام"],
        "counter": ["تم السداد", "الخصم مشروع", "العامل منقطع أو لم يؤد العمل", "المبلغ غير مستحق"],
        "questions": ["ما الأجر المتفق عليه ومصدره؟", "ما الفترة والمبلغ بدقة؟", "هل يوجد كشف يثبت النقص؟", "هل قدم الطرف الآخر كشفًا مضادًا؟"],
    },
    {
        "key": "termination", "label": "الإنهاء والفصل والإشعار",
        "signals": ("إنهاء", "فصل", "استقالة", "إشعار", "إنذار", "سبب الإنهاء"),
        "elements": ["قيام العلاقة وتاريخها", "فعل الإنهاء ومن صدر عنه", "تاريخ النفاذ", "السبب والإجراء المتبع", "الإشعار أو البديل النظامي", "الآثار والمستحقات"],
        "proof": ["العقد", "خطاب الإنهاء", "الإشعارات والإنذارات", "سجل الحضور", "تقييم الأداء", "المراسلات الداخلية"],
        "counter": ["استقالة أو اتفاق", "انقطاع عن العمل", "مخالفة جسيمة", "انتهاء مدة العقد", "تم الإشعار وفق النظام"],
        "questions": ["من اتخذ قرار الإنهاء ومتى؟", "ما السبب المكتوب وقت القرار؟", "هل سبق القرار إنذار أو تحقيق؟", "هل يتسق السبب مع السجلات والمراسلات؟"],
    },
    {
        "key": "attendance", "label": "الحضور والانقطاع والجزاءات",
        "signals": ("حضور", "غياب", "انقطاع", "بصمة", "دوام", "مخالفة", "تحقيق"),
        "elements": ["أيام أو ساعات الغياب المحددة", "علم الموظف بالجدول أو السياسة", "الإخطار أو الإنذار", "العذر أو الرد", "التناسب بين الواقعة والجزاء"],
        "proof": ["سجل البصمة", "الجداول", "الإنذارات", "محاضر التحقيق", "الأعذار الطبية", "رسائل التكليف"],
        "counter": ["السجل غير صحيح", "كان الغياب بعذر", "لم يصل الإنذار", "الجزاء متناسب ومثبت"],
        "questions": ["من أنشأ السجل وكيف حُفظ؟", "هل توجد أيام متعارضة مع رسائل أو تكليفات؟", "هل أُتيح الرد قبل الجزاء؟", "هل طبقت الإدارة نفس المعيار على حالات مماثلة؟"],
    },
    {
        "key": "settlement", "label": "التسوية الودية والإحالة",
        "signals": ("التسوية الودية", "محضر تعذر", "مكتب العمل", "جلسة التسوية", "اتفاق"),
        "elements": ["بيانات الأطراف", "رقم الطلب وتاريخه", "المطالبات المقدمة", "الجلسات والمراسلات", "الاتفاق أو التعذر", "الأثر الإجرائي للنتيجة"],
        "proof": ["رقم الطلب", "الإشعارات", "محاضر الجلسات", "محضر الاتفاق أو التعذر", "المراسلات"],
        "counter": ["لم يقدم الطلب بصورة صحيحة", "المطالبة غير محددة", "تم الاتفاق النهائي", "انقضت المهلة أو تغيرت المطالبة"],
        "questions": ["ما رقم الطلب وتاريخ فتحه؟", "ما الذي عرض في كل جلسة؟", "هل يوجد محضر رسمي؟", "هل تطابق المطالبة الحالية ما قدم في التسوية؟"],
    },
]


def _text(matter: Dict[str, Any]) -> str:
    parts = [matter.get("title", ""), matter.get("description", "")]
    for key in ("facts", "claims", "documents", "deadlines"):
        for item in matter.get(key, []) or []:
            parts.extend(str(v) for v in item.values() if v is not None)
    return " ".join(parts).lower()


def _match(text: str, terms: tuple[str, ...]) -> bool:
    return any(term.lower() in text for term in terms)


def _facts_for_issue(matter: Dict[str, Any], playbook: Dict[str, Any]) -> List[Dict[str, Any]]:
    terms = playbook["signals"]
    return [x for x in matter.get("facts", []) or [] if _match((x.get("title", "") + " " + x.get("description", "")), terms)]


def _documents_for_issue(matter: Dict[str, Any], playbook: Dict[str, Any]) -> List[Dict[str, Any]]:
    terms = playbook["signals"]
    return [x for x in matter.get("documents", []) or [] if _match((x.get("filename", "") + " " + x.get("kind", "") + " " + x.get("extracted_text", "") + " " + str(x.get("metadata_json", ""))), terms)]


def build_case_theory(matter: Dict[str, Any], role: str = "مستشار عمالي") -> Dict[str, Any]:
    text = _text(matter)
    claims = matter.get("claims", []) or []
    selected = [x for x in ISSUE_PLAYBOOKS if _match(text, x["signals"])]
    if not selected:
        selected = ISSUE_PLAYBOOKS[:1]
    issues = []
    for playbook in selected:
        facts = _facts_for_issue(matter, playbook)
        docs = _documents_for_issue(matter, playbook)
        related_claims = [x for x in claims if _match(x.get("title", ""), playbook["signals"])]
        missing = [p for p in playbook["proof"] if not _match(" ".join(d.get("filename", "") + " " + d.get("kind", "") for d in docs), (p,))]
        issues.append({
            "issue_key": playbook["key"], "issue": playbook["label"],
            "case_position": "مسألة ظاهرة في الملف",
            "related_claims": [{"id": c.get("id"), "title": c.get("title")} for c in related_claims],
            "elements": [{"element": e, "status": "يحتاج ربطًا" if not facts else "يحتاج تحققًا بالمصدر"} for e in playbook["elements"]],
            "supporting_facts": [{"id": f.get("id"), "title": f.get("title"), "certainty": f.get("certainty"), "date": f.get("event_date")} for f in facts],
            "supporting_documents": [{"id": d.get("id"), "filename": d.get("filename"), "integrity_status": d.get("integrity_status")} for d in docs],
            "missing_proof": missing,
            "expected_counterarguments": playbook["counter"],
            "cross_examination_questions": playbook["questions"],
            "position_gap": "قوي مبدئيًا" if facts and docs else "غير مكتمل الإثبات",
        })
    unsupported_claims = [c for c in claims if not any(c.get("id") in {r.get("id") for r in i["related_claims"]} for i in issues)]
    opponent_requests = ["اطلب السجل الأصلي لا صورة مختارة منه.", "اطلب تحديد مصدر كل رقم وتاريخ واسم مُنشئ السجل.", "قارن رواية الإدارة بالمراسلات المعاصرة للقرار.", "ثبّت أي تناقض في سجل زمني مستقل."]
    return {
        "engine_version": "1.0",
        "role": role,
        "theory": "تُبنى النظرية من عناصر كل مسألة، ثم تُربط كل واقعة بدليل، ويُختبر الرد المتوقع قبل صياغة أي مذكرة.",
        "issues": issues,
        "unsupported_claims": [{"id": c.get("id"), "title": c.get("title"), "action": "صنّف المطالبة واربطها بعنصر وواقعة ودليل."} for c in unsupported_claims],
        "administration_challenge_plan": opponent_requests,
        "interview_questions": [q for issue in issues for q in issue["cross_examination_questions"]][:24],
        "drafting_outline": ["الاختصاص والمسار الإجرائي", "الوقائع المؤرخة", "المسائل والعناصر", "تحليل كل عنصر بالدليل", "الرد على دفوع الإدارة", "الطلبات والمستندات المؤيدة"],
        "disclaimer": "هذه خريطة عمل للإثبات والمواجهة وليست رأيًا قانونيًا نهائيًا أو ضمانًا للنتيجة.",
    }
