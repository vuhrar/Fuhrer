"""محرك تقييم مهني حتمي لملفات النزاعات العمالية.

لا يصدر رأيًا قانونيًا؛ يبني سجل مخاطر قابلًا للتدقيق، وبوابات انتقال،
ومصفوفة نقص مرتبطة بالوقائع والأدلة والإجراءات.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any, Dict, Iterable, List

ROLES = {
    "محامي": {
        "label": "المحامي",
        "focus": "بناء نظرية القضية، اختبار قابلية الإثبات، ومراجعة الإجراء قبل التقديم.",
        "tools": ["مصفوفة الادعاء والدليل", "سجل المخاطر", "بوابات الإجراء", "حزمة المراجعة"],
    },
    "مستشار قانوني": {
        "label": "المستشار القانوني",
        "focus": "تدقيق الوقائع والمصادر والالتزامات وصياغة خيارات عملية قابلة للمراجعة.",
        "tools": ["تدقيق المصدر", "تحليل النواقص", "خط زمني موثق", "مذكرة قرار"],
    },
    "مستشار عمالي": {
        "label": "المستشار العمالي",
        "focus": "فحص الأجر والحضور والإنهاء والتسوية الودية وسلامة ملف الموظف.",
        "tools": ["فحص الأجر", "فحص الحضور", "بوابة التسوية الودية", "سجل المستندات"],
    },
}

RISK_DOMAINS = [
    ("العلاقة العمالية", ("عقد", "علاقة", "مباشرة", "مسمى"), "ثبّت بداية العلاقة ونوعها وشروطها وأي تعديل لاحق."),
    ("الأجر والاستحقاقات", ("راتب", "أجر", "بدل", "استحقاق", "تحويل", "خصم"), "طابق الأجر التعاقدي مع التحويلات والكشوف والبدلات والخصومات."),
    ("الدوام والحضور", ("حضور", "غياب", "انقطاع", "بصمة", "دوام", "ساعات"), "اجمع سجل الحضور والإنذارات والأعذار ورد الطرف الآخر."),
    ("الإنهاء والإشعار", ("إنهاء", "فصل", "استقالة", "إشعار", "سبب"), "افحص السبب والتاريخ والإشعار والمستند المؤيد وأقوال الطرفين."),
    ("التسوية الودية", ("تسوية ودية", "محضر تعذر", "جلسة التسوية", "مكتب العمل"), "وثّق رقم الطلب والجلسات والاتفاق أو محضر التعذر."),
    ("الاختصاص والمواعيد", ("اختصاص", "محكمة", "دعوى", "موعد", "إحالة"), "تحقق من الجهة والمرحلة والمواعيد من المصدر الرسمي."),
    ("سلامة الإثبات", ("مستند", "رسالة", "بريد", "كشف", "شهادة", "سجل"), "اربط كل ادعاء بمستند أصلي أو قرينة وسجل مصدره وسلامته."),
]

PROCEDURE_GATES = {
    "evidence": {"label": "جمع الأدلة", "requires": ("documents",), "action": "ارفع المستندات الأصلية واربطها بالوقائع والطلبات."},
    "legal_review": {"label": "المراجعة القانونية", "requires": ("claims_basis", "jurisdiction"), "action": "أدخل أساس كل طلب والاختصاص مع مصدر قابل للتحقق."},
    "amicable_settlement": {"label": "التسوية الودية", "requires": ("parties", "documents"), "action": "أكمل بيانات الأطراف وارفع ما يثبت طلب التسوية ومراسلاتها."},
    "referral": {"label": "الإحالة", "requires": ("settlement_outcome",), "action": "سجّل الاتفاق أو محضر التعذر ورقم الطلب قبل الإحالة."},
    "lawsuit": {"label": "تجهيز الدعوى", "requires": ("claims_basis", "documents", "chronology"), "action": "أكمل صحيفة الوقائع والطلبات والمرفقات والمواعيد."},
    "enforcement": {"label": "التنفيذ", "requires": ("judgment_or_settlement",), "action": "احفظ الحكم أو الاتفاق وما يثبت التنفيذ أو المتبقي."},
}


def _text(matter: Dict[str, Any]) -> str:
    chunks = [matter.get("title", ""), matter.get("description", "")]
    for key in ("facts", "claims", "documents", "deadlines"):
        for item in matter.get(key, []) or []:
            chunks.extend(str(v) for v in item.values() if v is not None)
    return " ".join(chunks).lower()


def _has_any(text: str, terms: Iterable[str]) -> bool:
    return any(term.lower() in text for term in terms)


def _domain_status(text: str, domain: tuple[str, tuple[str, ...], str]) -> Dict[str, Any]:
    name, terms, action = domain
    present = _has_any(text, terms)
    return {"domain": name, "status": "مؤشر موجود" if present else "غير ظاهر", "severity": "مراجعة" if present else "مرتفع", "finding": "وجدت مؤشرات مرتبطة بالمجال." if present else f"لم تظهر بيانات كافية عن {name}.", "action": action}


def _chronology(matter: Dict[str, Any]) -> Dict[str, Any]:
    facts = matter.get("facts", []) or []
    dated = [x for x in facts if x.get("event_date")]
    invalid = [x.get("title", "واقعة") for x in facts if not x.get("event_date")]
    ordered = sorted(dated, key=lambda x: x.get("event_date", "9999"))
    anomalies: List[Dict[str, Any]] = []
    for left, right in zip(ordered, ordered[1:]):
        if left.get("event_date", "") > right.get("event_date", ""):
            anomalies.append({"type": "ترتيب زمني غير متسق", "items": [left.get("title"), right.get("title")], "action": "افتح المستندين الأصليين وتحقق من التاريخ."})
    return {"dated_facts": len(dated), "undated_facts": len(invalid), "undated_titles": invalid, "ordered": [{"date": x.get("event_date"), "title": x.get("title")} for x in ordered], "anomalies": anomalies}


def _claim_matrix(matter: Dict[str, Any]) -> List[Dict[str, Any]]:
    links = defaultdict(list)
    for link in matter.get("claim_evidence", []) or []:
        links[link.get("claim_id")].append(link)
    result = []
    for claim in matter.get("claims", []) or []:
        evidence = links.get(claim.get("id"), [])
        result.append({"claim_id": claim.get("id"), "claim": claim.get("title", ""), "basis_status": "مدخل" if claim.get("legal_basis") else "ناقص", "evidence_status": "مرتبط" if evidence else "غير مرتبط", "evidence_count": len(evidence), "next_action": "راجع كفاية الدليل ومصدره." if evidence else "اربط المطالبة بمستند أو سجل سبب عدم وجوده."})
    return result


def _gate_status(matter: Dict[str, Any], key: str) -> Dict[str, Any]:
    gate = PROCEDURE_GATES[key]
    docs = matter.get("documents", []) or []
    facts = matter.get("facts", []) or []
    claims = matter.get("claims", []) or []
    parties = matter.get("parties", []) or []
    steps = {x.get("step_key"): x for x in matter.get("procedure_steps", []) or []}
    checks = {
        "documents": bool(docs), "claims_basis": bool(claims) and all(x.get("legal_basis") for x in claims),
        "jurisdiction": bool(matter.get("jurisdiction")), "parties": len(parties) >= 2,
        "settlement_outcome": _has_any(_text(matter), ("محضر تعذر", "اتفاق تسوية", "تمت التسوية")),
        "chronology": bool(facts) and all(x.get("event_date") for x in facts),
        "judgment_or_settlement": _has_any(_text(matter), ("حكم", "اتفاق تسوية", "محضر تعذر")),
    }
    missing = [name for name in gate["requires"] if not checks.get(name)]
    current = steps.get(key, {}).get("status", "غير مكتملة")
    return {"step_key": key, "label": gate["label"], "current_status": current, "status": "مستوفاة" if not missing else "بوابة متوقفة", "missing": missing, "action": gate["action"] if missing else "يمكن مراجعة الانتقال مع التحقق البشري."}


def assess_matter(matter: Dict[str, Any], role: str = "مستشار عمالي") -> Dict[str, Any]:
    role = role if role in ROLES else "مستشار عمالي"
    text = _text(matter)
    domains = [_domain_status(text, item) for item in RISK_DOMAINS]
    matrix = _claim_matrix(matter)
    chronology = _chronology(matter)
    gaps = []
    for row in matrix:
        if row["basis_status"] == "ناقص" or row["evidence_status"] == "غير مرتبط":
            gaps.append({"type": "مصفوفة الادعاء", "severity": "مرتفع", "finding": row["claim"] or "طلب غير مسمى", "action": row["next_action"]})
    gaps.extend({"type": "خط زمني", "severity": "متوسط", "finding": title + " بلا تاريخ", "action": "أدخل التاريخ من المستند الأصلي أو وسم الواقعة كغير مؤرخة."} for title in chronology["undated_titles"])
    gates = [_gate_status(matter, key) for key in PROCEDURE_GATES]
    blocked = sum(1 for x in gates if x["status"] == "بوابة متوقفة")
    high = sum(1 for x in domains if x["severity"] == "مرتفع")
    score = max(0, min(100, 100 - len(gaps) * 9 - blocked * 5 - high * 3 - len(chronology["anomalies"]) * 7))
    return {
        "engine_version": "2.0",
        "role": ROLES[role],
        "readiness": {"score": score, "label": "جاهز للمراجعة النهائية" if score >= 85 else "يحتاج معالجة قبل الاعتماد", "confidence": "متوسطة — فحص حتمي يحتاج تحققًا بشريًا"},
        "risk_register": domains,
        "claim_evidence_matrix": matrix,
        "chronology": chronology,
        "procedure_gates": gates,
        "gaps": gaps,
        "next_actions": [x["action"] for x in gaps[:8]] + [x["action"] for x in gates if x["status"] == "بوابة متوقفة"][:6],
        "disclaimer": "هذه مخرجات تدقيق وتنظيم آلي وليست رأيًا قانونيًا نهائيًا أو ضمانًا لنتيجة النزاع.",
    }


def role_catalog() -> List[Dict[str, Any]]:
    return [{"key": key, **value} for key, value in ROLES.items()]
