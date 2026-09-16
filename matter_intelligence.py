"""تحليل مترابط لملف النزاع؛ نتائج فحص وليست رأيًا قانونيًا."""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List


def _doc_meta(document: Dict[str, Any]) -> Dict[str, Any]:
    raw = document.get("metadata_json", "{}")
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw or "{}")
    except Exception:
        return {}


def _contains(text: str, terms: tuple[str, ...]) -> bool:
    value = (text or "").lower()
    return any(term.lower() in value for term in terms)


def _contradictions(matter: Dict[str, Any]) -> List[Dict[str, Any]]:
    items = []
    facts = matter.get("facts", [])
    for idx, left in enumerate(facts):
        for right in facts[idx + 1:]:
            same_topic = any(token in (left.get("title", "") + " " + right.get("title", "")).lower() for token in ("أجر", "راتب", "إنهاء", "فصل", "انقطاع", "حضور", "إشعار"))
            certainty_conflict = left.get("certainty") in {"مثبت بمستند", "منفي"} and right.get("certainty") in {"مثبت بمستند", "منفي"} and left.get("certainty") != right.get("certainty")
            if same_topic and certainty_conflict:
                items.append({"type": "تعارض محتمل", "items": [left.get("id"), right.get("id")], "finding": f"تعارض محتمل بين الواقعتين: {left.get('title')} و{right.get('title')}", "action": "افتح النصين الأصليين واربط كل واقعة بدليل أو وسمها صراحة كمتنازع عليها."})
    return items


def analyze_matter(matter: Dict[str, Any]) -> Dict[str, Any]:
    facts = matter.get("facts", [])
    claims = matter.get("claims", [])
    documents = matter.get("documents", [])
    deadlines = matter.get("deadlines", [])
    evidence_links = matter.get("claim_evidence", [])
    combined = " ".join([matter.get("title", ""), matter.get("description", "")] + [f"{x.get('title','')} {x.get('description','')}" for x in facts] + [f"{x.get('title','')} {x.get('notes','')} {x.get('legal_basis','')}" for x in claims] + [str(_doc_meta(x)) for x in documents])
    labor = _contains(combined, ("عمال", "عامل", "راتب", "أجر", "صاحب العمل", "التسوية الودية", "إنهاء الخدمة", "الفصل"))
    linked_claims = {x.get("claim_id") for x in evidence_links}
    gaps: List[Dict[str, Any]] = []
    for fact in facts:
        if fact.get("certainty") not in {"مثبت بمستند", "مؤيد بقرائن"}:
            gaps.append({"type": "واقعة غير مثبتة", "severity": "مرتفع", "target_id": fact.get("id"), "finding": fact.get("title", "واقعة") + " غير مثبتة بدرجة كافية", "action": "أضف أصل المستند أو الشاهد أو وسمها كواقعة متنازع عليها."})
    for claim in claims:
        if claim.get("id") not in linked_claims:
            gaps.append({"type": "طلب بلا دليل", "severity": "مرتفع", "target_id": claim.get("id"), "finding": claim.get("title", "طلب") + " لا يرتبط بدليل", "action": "اربط الطلب بمستند أو سجل سبب عدم وجود الدليل."})
    if not documents:
        gaps.append({"type": "لا توجد مستندات", "severity": "حرج", "finding": "لم تُرفع مستندات أصلية إلى الملف", "action": "ارفع النسخ الأصلية واحفظ مصدر الحصول عليها."})
    contradictions = _contradictions(matter)
    sources_scanned = len(facts) + len(claims) + len(documents) + len(evidence_links)
    score = 100
    score -= min(35, len(gaps) * 12)
    score -= min(20, len(contradictions) * 10)
    if documents and all(x.get("integrity_status") == "سليم" for x in documents):
        score += 5
    score = max(0, min(100, score))
    labor_impacts = []
    if labor:
        labor_impacts = [
            {"area": "الأجر والاستحقاقات", "status": "يحتاج مطابقة" if _contains(combined, ("أجر", "راتب")) else "غير ظاهر", "action": "طابق العقد وكشوف التحويل والحضور والخصومات."},
            {"area": "الإنهاء والإشعار", "status": "يحتاج فحص" if _contains(combined, ("إنهاء", "فصل", "إشعار")) else "غير ظاهر", "action": "راجع السبب والتاريخ والإشعار والمستند المؤيد."},
            {"area": "التسوية الودية", "status": "مذكورة" if _contains(combined, ("التسوية الودية",)) else "غير موثقة", "action": "وثق رقم الطلب والجلسات والاتفاق أو محضر التعذر."},
            {"area": "الاختصاص والمواعيد", "status": "يحتاج تحقق", "action": "تحقق من المرحلة والمواعيد والجهة المختصة من المصدر الرسمي."},
        ]
    return {
        "matter_id": matter.get("id"),
        "context": "نزاع عمالي" if labor else "غير مصنف بالكامل",
        "readiness": {"score": score, "label": "جاهز للمراجعة النهائية" if score >= 85 else "يحتاج مراجعة", "not_a_legal_opinion": True},
        "coverage": {"facts": len(facts), "claims": len(claims), "documents": len(documents), "deadlines": len(deadlines), "evidence_links": len(evidence_links), "sources_scanned": sources_scanned, "characters_scanned": len(combined)},
        "gaps": gaps,
        "contradictions": contradictions,
        "labor_impacts": labor_impacts,
        "evidence_integrity": [{"document_id": x.get("id"), "status": x.get("integrity_status", "غير متحقق"), "source_hash": x.get("source_hash", "")} for x in documents],
        "next_actions": [g["action"] for g in gaps[:8]] + [c["action"] for c in contradictions[:4]],
        "disclaimer": "هذه نتائج استخراج وتدقيق آلي؛ لا تمثل رأيًا قانونيًا نهائيًا ولا تثبت صحة أي واقعة.",
    }
