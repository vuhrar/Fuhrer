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


def _all_manual_text(facts: List[Dict], claims: List[Dict]) -> Dict[str, set]:
    from legal_tools import info_extractor
    dates, amounts, articles = set(), set(), set()
    for f in facts:
        blob = f"{f.get('title','')} {f.get('description','')}"
        if f.get("event_date"):
            dates.add(str(f["event_date"])[:10])
        dates.update(info_extractor.extract_dates(blob))
        amounts.update(info_extractor.extract_amounts(blob))
    for c in claims:
        blob = f"{c.get('title','')} {c.get('notes','')} {c.get('legal_basis','')}"
        amounts.update(info_extractor.extract_amounts(blob))
        articles.update(info_extractor.extract_articles(blob))
    return {"dates": dates, "amounts": amounts, "articles": articles}


def cross_reference_documents(matter: Dict[str, Any], document_texts: Dict[str, str]) -> Dict[str, Any]:
    """
    محرك الربط بين المستندات والوقائع/الطلبات المُدخلة يدويًا (المرحلة 2).

    ما يفعله فعليًا: يستخرج التواريخ والمبالغ والمواد من نص كل مستند مرفوع
    (عبر legal_tools.info_extractor، مبني ومُختبر أصلًا في المرحلة صفر)،
    ويقارنها بما أُدخل يدويًا في الوقائع والطلبات. أي قيمة تظهر في مستند
    ولا تظهر في أي واقعة أو طلب مُدخل تُرفَع كـ"معلومة غير مُلتقَطة بعد" —
    ليست اتهامًا بخطأ، بل تذكيرًا صريحًا بمراجعة المستند.

    حد صادق يجب معرفته: هذه مطابقة نصية حرفية (سلسلة نص إلى سلسلة نص)، لا
    فهم دلالي. "12,000 ريال" في مستند و"12000" في واقعة مُدخلة يدويًا قد
    لا تتطابقان رغم أنهما نفس المبلغ فعليًا. كذلك لا يحاول هذا الإصدار كشف
    "تعارض" (رقمان مختلفان لنفس البند) تلقائيًا لأن ذلك يتطلب مطابقة أي
    مبلغ في المستند يقابل أي بند في الواقعة دلاليًا — خطوة أعقد ستُبنى لاحقًا
    بثقة بعد التحقق من نمط بيانات فعلي حقيقي، لا افتراضًا نظريًا الآن. هذا
    الإصدار متعمَّد أضيق نطاقًا لكن **موثوق فيما يدّعيه فعلًا**: تغطية لا
    اكتشاف تعارض.
    """
    from legal_tools import info_extractor

    facts, claims, documents = matter.get("facts", []), matter.get("claims", []), matter.get("documents", [])
    manual = _all_manual_text(facts, claims)

    findings: List[Dict[str, Any]] = []
    documents_analyzed = 0
    for doc in documents:
        text = document_texts.get(doc.get("id"), "")
        if not text.strip():
            continue
        documents_analyzed += 1
        extracted = info_extractor.extract_all(text)
        filename = doc.get("filename", "مستند")

        new_dates = sorted(set(extracted["dates"]) - manual["dates"])
        if new_dates:
            findings.append({"type": "تاريخ في المستند غير مسجَّل كواقعة", "document_id": doc.get("id"), "document": filename, "values": new_dates, "action": f"راجع هذا التاريخ في «{filename}» وأضف واقعة مطابقة إن كان ذا صلة."})

        new_amounts = sorted(set(extracted["amounts"]) - manual["amounts"])
        if new_amounts:
            findings.append({"type": "مبلغ في المستند غير مرتبط بأي طلب أو واقعة", "document_id": doc.get("id"), "document": filename, "values": new_amounts, "action": f"تحقق إن كان هذا المبلغ في «{filename}» يخص طلبًا قائمًا أو يستدعي طلبًا جديدًا."})

        new_articles = sorted(set(extracted["articles"]) - manual["articles"])
        if new_articles:
            findings.append({"type": "مادة مذكورة في المستند وغير مستخدمة كأساس لأي طلب", "document_id": doc.get("id"), "document": filename, "values": new_articles, "action": f"راجع إن كانت هذه المادة في «{filename}» تدعم طلبًا إضافيًا لم يُدرَج بعد."})

    return {
        "documents_analyzed": documents_analyzed,
        "documents_with_no_text": len(documents) - documents_analyzed,
        "findings": findings,
        "scope": "تغطية (معلومات في المستندات غير ملتقطة يدويًا) — لا يكشف تعارضًا بين رقمين بعد؛ راجع الوصف الكامل في التوثيق.",
        "disclaimer": "استخراج آلي بمطابقة نصية حرفية للمقارنة فقط؛ لا يثبت صحة أي واقعة ولا يغني عن قراءة المستند كاملًا.",
    }


def analyze_correspondence_for_matter(matter: Dict[str, Any], document_texts: Dict[str, str]) -> Dict[str, Any]:
    """يجمع مستندات القضية الموسومة kind='مراسلة' ويمرر نصوصها لمحرك correspondence_intelligence (المرحلة 4)."""
    from correspondence_intelligence import analyze_correspondence

    items = []
    for doc in matter.get("documents", []):
        if doc.get("kind") != "مراسلة":
            continue
        text = document_texts.get(doc.get("id"), "")
        if not text.strip():
            continue
        meta = _doc_meta(doc)
        items.append({"id": doc.get("id"), "text": text, "date": meta.get("date"), "channel": meta.get("channel")})

    if not items:
        return {"items_analyzed": 0, "note": "لا توجد مستندات بنوع 'مراسلة' مرفوعة لهذه القضية بعد."}
    return analyze_correspondence(items)


def draft_amicable_settlement_for_matter(matter: Dict[str, Any], dispute_category_key: str = "dismissal", plaintiff_contact: str = "") -> Dict[str, Any]:
    """يبني طلب تراضي مباشرة من بيانات قضية حقيقية مُخزَّنة: الوقائع والطلبات وفهرس المستندات."""
    from amicable_settlement import AmicableSettlementRequestDrafter

    facts = [{"date": f.get("event_date"), "text": (f.get("title") or "") + ((": " + f["description"]) if f.get("description") else "")} for f in matter.get("facts", [])]
    claims = [{"title": c.get("title", ""), "legal_basis": c.get("legal_basis", "")} for c in matter.get("claims", [])]
    evidence = [d.get("filename", "") for d in matter.get("documents", []) if d.get("filename")]

    return AmicableSettlementRequestDrafter().draft(
        plaintiff_name=matter.get("client_name", "") or "", plaintiff_contact=plaintiff_contact,
        defendant_name=matter.get("opposing_party", "") or "", workplace_location=matter.get("jurisdiction", "") or "",
        dispute_category_key=dispute_category_key, facts=facts, claims=claims, evidence=evidence,
    )


def analyze_matter_deep(matter: Dict[str, Any], document_texts: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """analyze_matter() الأصلية دون أي تغيير + طبقة الربط الجديدة إن توفرت نصوص المستندات. تراجعية التوافق بالكامل."""
    result = analyze_matter(matter)
    if document_texts:
        result["document_cross_reference"] = cross_reference_documents(matter, document_texts)
    return result


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
