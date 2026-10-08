"""دمج إشارات المطابقة الدلالية والكيانات الجدولية والسياق المتعارض.

الدالة لا تصدر حكمًا قانونيًا؛ تنتج درجة ثقة تفسيرية لمؤشر حق محتمل
مع بيان ما دعمه وما نفاه ومصادره.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List


POSITIVE_STATUSES = {"positive_signal", "مؤشر إيجابي", "مثبت مبدئيًا", "مؤيد"}
NEGATIVE_STATUSES = {"negated_by_employer", "negated_by_worker", "منفي", "دفع من الإدارة", "منفي من الإدارة"}


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 3)


def _confidence_label(score: float) -> str:
    if score < 0.45:
        return "إشارة ضعيفة"
    if score < 0.70:
        return "مؤشر يحتاج تحققًا"
    if score < 0.85:
        return "مؤشر قوي مبدئيًا"
    return "نتيجة قوية من ناحية الاستخراج — ليست إثباتًا قانونيًا"


def _source_quality(item: Dict[str, Any]) -> float:
    explicit = item.get("source_quality")
    if explicit is not None:
        return _clamp(float(explicit))
    if item.get("document_id") and item.get("page"):
        return 0.95
    if item.get("document_id"):
        return 0.85
    if item.get("source") in {"structured_table", "table"}:
        return 0.80
    return 0.55


def _trace(item: Dict[str, Any], trigger_type: str) -> Dict[str, Any]:
    return {
        "trigger_type": trigger_type,
        "document_id": item.get("document_id") or item.get("source_document_id"),
        "filename": item.get("filename"),
        "page": item.get("page") or item.get("page_number"),
        "excerpt": item.get("excerpt") or item.get("source_excerpt") or item.get("text"),
        "source_quality": _source_quality(item),
    }


def fuse_semantic_table_evidence(
    semantic_matches: Iterable[Dict[str, Any]],
    table_entities: Iterable[Dict[str, Any]] = (),
    contextual_statements: Iterable[Dict[str, Any]] = (),
    *,
    right_catalog: Dict[str, Dict[str, Any]] | None = None,
    claim_keys: Iterable[str] = (),
    min_score: float = 0.20,
) -> List[Dict[str, Any]]:
    """ادمج المطابقة الدلالية والجداول والسياق في نتائج حقوق قابلة للتدقيق.

    Parameters
    ----------
    semantic_matches:
        عناصر مثل ``{"right_key": "overtime", "semantic_score": .78,
        "text": "عمل بعد الدوام", "document_id": "doc_1", "page": 2}``.
    table_entities:
        كيانات منظمة من الجداول. يجب أن تحتوي على ``right_key`` ويفضل
        ``entity_type`` و``confidence`` ومصدر/صفحة. يدعم ``polarity`` أو
        ``status`` لاختبار النفي.
    contextual_statements:
        جمل مصنفة مسبقًا بــ ``right_key``, ``status``, ``speaker`` و``text``.
    right_catalog:
        تعريف اختياري للعناوين والعناصر والأدلة المطلوبة.
    claim_keys:
        الحقوق التي ذكرها المستخدم كمطالبات؛ غيرها يوسم كمؤشر غير مذكور.
    min_score:
        أقل درجة لإخراج نتيجة.

    Returns
    -------
    list[dict]
        نتيجة لكل حق، مع ``final_confidence`` و``source_trace`` و``why_detected``.
    """
    catalog = right_catalog or {}
    mentioned = set(claim_keys)
    buckets: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "semantic": [], "tables": [], "positive": [], "negative": [], "traces": [], "why": [], "speakers": set()
    })

    for match in semantic_matches or ():
        key = match.get("right_key")
        if not key:
            continue
        score = _clamp(float(match.get("semantic_score", match.get("score", 0.0))))
        bucket = buckets[key]
        bucket["semantic"].append(score)
        bucket["traces"].append(_trace(match, "semantic_match"))
        if match.get("text") or match.get("excerpt"):
            bucket["why"].append(match.get("text") or match.get("excerpt"))

    for entity in table_entities or ():
        key = entity.get("right_key")
        if not key:
            continue
        bucket = buckets[key]
        entity_score = _clamp(float(entity.get("confidence", entity.get("score", 0.80))))
        polarity = entity.get("polarity") or entity.get("status")
        if polarity in NEGATIVE_STATUSES or entity.get("is_negative") is True:
            bucket["negative"].append(entity)
        else:
            bucket["positive"].append(entity)
        bucket["tables"].append(entity_score)
        bucket["traces"].append(_trace(entity, "structured_table"))
        if entity.get("reason"):
            bucket["why"].append(entity["reason"])
        elif entity.get("source_excerpt"):
            bucket["why"].append(entity["source_excerpt"])

    for statement in contextual_statements or ():
        key = statement.get("right_key")
        if not key:
            continue
        bucket = buckets[key]
        status = statement.get("status") or statement.get("polarity")
        if status in NEGATIVE_STATUSES or statement.get("is_negative") is True:
            bucket["negative"].append(statement)
            if statement.get("speaker"):
                bucket["speakers"].add(statement["speaker"])
        else:
            bucket["positive"].append(statement)
        bucket["traces"].append(_trace(statement, "contextual_statement"))
        if statement.get("text") or statement.get("excerpt"):
            bucket["why"].append(statement.get("text") or statement.get("excerpt"))

    results = []
    for key, bucket in buckets.items():
        semantic_score = max(bucket["semantic"], default=0.0)
        table_score = max(bucket["tables"], default=0.0)
        structured_signal = bool(bucket["tables"])
        positive_count = len(bucket["positive"])
        negative_count = len(bucket["negative"])
        contradiction = positive_count > 0 and negative_count > 0
        source_scores = [x["source_quality"] for x in bucket["traces"]]
        source_quality = sum(source_scores) / len(source_scores) if source_scores else 0.0
        # دمج تفسيري: الدلالة، الجدول، وجود سياق مؤيد، جودة المصدر، ثم خصم التعارض.
        score = (
            semantic_score * 0.30
            + table_score * 0.25
            + (1.0 if positive_count else 0.0) * 0.15
            + source_quality * 0.15
            + (0.10 if len(bucket["traces"]) >= 2 else 0.0)
            - (0.15 if contradiction else 0.0)
            - (0.10 if negative_count and not positive_count else 0.0)
        )
        final_score = _clamp(score)
        if final_score < min_score:
            continue
        if contradiction:
            status = "محل نزاع ويحتاج تحققًا"
        elif negative_count and not positive_count:
            status = "دفع أو نفي يحتاج اختبارًا"
        elif key in mentioned:
            status = "مطالبة موجودة"
        else:
            status = "مؤشر حق غير مذكور"
        definition = catalog.get(key, {})
        results.append({
            "right_key": key,
            "label": definition.get("label", key),
            "status": status,
            "final_confidence": final_score,
            "confidence_label": _confidence_label(final_score),
            "semantic_score": semantic_score,
            "table_score": table_score,
            "positive_evidence_count": positive_count,
            "negative_evidence_count": negative_count,
            "contradiction": contradiction,
            "speakers": sorted(bucket["speakers"]),
            "why_detected": list(dict.fromkeys(bucket["why"]))[:12],
            "source_trace": bucket["traces"][:20],
            "elements_to_verify": definition.get("elements", definition.get("required_elements", [])),
            "evidence_needed": definition.get("evidence", definition.get("required_evidence", [])),
            "missing_proof": [f"تحقق من: {x}" for x in definition.get("elements", definition.get("required_elements", []))],
            "human_review_required": True,
        })
    return sorted(results, key=lambda item: item["final_confidence"], reverse=True)
