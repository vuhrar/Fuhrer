"""تحليل سياقي محافظ للنصوص القانونية العربية.

لا يقرر صحة الواقعة؛ يحدد من قالها، واتجاهها، ونطاق النفي، وهل هي
اقتباس أو ادعاء أو عبارة غير كافية، مع حفظ موضعها في النص الأصلي.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Tuple

SPEAKER_PATTERNS = {
    "الإدارة": (r"تدعي\s+(?:الإدارة|الشركة|المنشأة)", r"ذكرت\s+(?:الشركة|الإدارة)", r"بحسب\s+(?:صاحب\s+العمل|الشركة)", r"توضح\s+الموارد\s+البشرية", r"تدفع\s+(?:الإدارة|الشركة)"),
    "العامل": (r"أفاد\s+(?:العامل|الموظف)", r"ذكر\s+(?:العامل|الموظف)", r"بحسب\s+(?:العامل|الموظف)", r"أطالب", r"أعمل", r"عملت"),
    "جهة رسمية": (r"ورد\s+في\s+(?:المحضر|الحكم|القرار)", r"أفادت\s+(?:الوزارة|المحكمة)", r"بحسب\s+(?:الوزارة|المحكمة)", r"نص\s+النظام"),
}

NEGATION_CUES = (
    "لم", "لا", "ليس", "ليست", "لن", "غير", "دون", "لا يوجد", "لا توجد", "لم يتم", "لم يثبت", "ليس صحيحًا", "ليس صحيحا", "تنفي", "ينفي", "نفى",
)
UNPROVEN_CUES = ("لم يثبت", "لم يثبت أن", "لا دليل على", "دون دليل", "غير ثابت", "غير مثبت", "لم يتبين")
POSITIVE_CUES = ("ثبت", "يثبت", "أثبت", "تم دفع", "تم السداد", "سددت", "دفع", "يستحق", "عمل", "باشر", "استمر")
PAYMENT_CUES = ("تم دفع", "تم السداد", "سدد", "حولت", "تم تحويل", "استلم")


def normalize_arabic(text: str) -> str:
    text = text or ""
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ى", "ي")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _sentences_with_offsets(text: str) -> List[Tuple[str, int, int]]:
    return [(m.group(0).strip(), m.start(), m.end()) for m in re.finditer(r"[^.!؟؛\n]+(?:[.!؟؛]|$)", text or "") if m.group(0).strip()]


def _quoted_spans(text: str) -> List[Tuple[int, int]]:
    spans = []
    for pattern in (r"\"([^\"]+)\"", r"«([^»]+)»", r"\(([^()]{4,})\)"):
        spans.extend((m.start(1), m.end(1)) for m in re.finditer(pattern, text or ""))
    return spans


def _is_in_quote(start: int, end: int, spans: List[Tuple[int, int]]) -> bool:
    return any(start >= left and end <= right for left, right in spans)


def detect_speaker(sentence: str) -> str:
    for speaker, patterns in SPEAKER_PATTERNS.items():
        if any(re.search(pattern, sentence or "", flags=re.IGNORECASE) for pattern in patterns):
            return speaker
    return "غير محدد"


def _near_concept(text: str, concept_terms: Iterable[str]) -> Tuple[str | None, int | None]:
    normalized = normalize_arabic(text)
    for term in concept_terms:
        target = normalize_arabic(term)
        variants = {target}
        words = target.split()
        if words:
            variants.add(" ".join((word[2:] if word.startswith("ال") and len(word) > 3 else word) for word in words))
            variants.add(" ".join((word if word.startswith("ال") else "ال" + word) for word in words))
        for variant in variants:
            position = normalized.find(variant)
            if position >= 0:
                return variant, position
    return None, None


def classify_polarity(sentence: str, concept_terms: Iterable[str]) -> Dict[str, Any]:
    """صنّف الاتجاه مع التمييز بين النفي وعدم الإثبات والسداد."""
    clean = normalize_arabic(sentence)
    concept, position = _near_concept(clean, concept_terms)
    if concept is None:
        return {"polarity": "غير محدد", "status": "insufficient_context", "cue": None, "confidence": 0.2}
    window = clean[max(0, position - 65): min(len(clean), position + len(concept) + 65)]
    if any(cue in window for cue in UNPROVEN_CUES):
        cue = next(cue for cue in UNPROVEN_CUES if cue in window)
        return {"polarity": "غير مثبت", "status": "unproven", "cue": cue, "confidence": 0.82}
    if any(cue in window for cue in PAYMENT_CUES):
        cue = next(cue for cue in PAYMENT_CUES if cue in window)
        return {"polarity": "مثبت بالسداد", "status": "paid_claimed", "cue": cue, "confidence": 0.78}
    negation = next((cue for cue in NEGATION_CUES if cue in window), None)
    if negation:
        return {"polarity": "منفي", "status": "negated", "cue": negation, "confidence": 0.82}
    positive = next((cue for cue in POSITIVE_CUES if cue in window), None)
    return {"polarity": "مثبت مبدئيًا", "status": "positive_signal", "cue": positive, "confidence": 0.58}


def analyze_legal_text(text: str, right_concepts: Dict[str, Iterable[str]], *, document_id: str | None = None, filename: str | None = None, page: int | None = None) -> List[Dict[str, Any]]:
    """استخرج عبارات الحقوق مع المتحدث والنفي والاقتباس ومصدر النص.

    ``right_concepts`` مثال: ``{"overtime": ["ساعات إضافية", "بعد الدوام"]}``.
    تعاد العبارات التي ظهر فيها مفهوم فقط، ولا تعاد الجمل التي لا تحمل
    إشارة كافية. تحفظ offsets للنص الأصلي لعرضه أو مراجعته.
    """
    output = []
    quote_spans = _quoted_spans(text or "")
    for sentence, start, end in _sentences_with_offsets(text or ""):
        for right_key, terms in right_concepts.items():
            normalized_sentence = normalize_arabic(sentence)
            if not any(normalize_arabic(term) in normalized_sentence for term in terms):
                continue
            classification = classify_polarity(sentence, terms)
            speaker = detect_speaker(sentence)
            quoted = _is_in_quote(start, end, quote_spans)
            status = classification["status"]
            if quoted and status == "positive_signal":
                status = "quoted_claim"
            elif speaker == "الإدارة" and status == "negated":
                status = "negated_by_employer"
            elif speaker == "العامل" and status == "negated":
                status = "negated_by_worker"
            elif speaker == "الإدارة" and status == "paid_claimed":
                status = "payment_claimed_by_employer"
            output.append({
                "right_key": right_key,
                "text": sentence,
                "excerpt": sentence,
                "start": start,
                "end": end,
                "speaker": speaker,
                "polarity": classification["polarity"],
                "status": status,
                "negation_cue": classification["cue"],
                "quoted": quoted,
                "confidence": classification["confidence"],
                "document_id": document_id,
                "filename": filename,
                "page": page,
                "human_review_required": True,
            })
    return output
