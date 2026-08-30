"""أدوات قانونية عملية قائمة على مصادر، لا حاسبات مالية."""
from __future__ import annotations

import re
from typing import Any, Dict, List

from legal_tools_advanced import legal_search

OFFICIAL_SOURCES = [
    {
        "id": "hrsd_labor_law_2025",
        "title": "نظام العمل في المملكة العربية السعودية",
        "publisher": "وزارة الموارد البشرية والتنمية الاجتماعية",
        "url": "https://www.hrsd.gov.sa/sites/default/files/2025-11/labor-law.pdf",
        "page": "نسخة PDF الرسمية المرتبطة بصفحة الوزارة",
        "version_note": "تتضمن الصفحة الرسمية تعديلات من بينها المرسوم الملكي م/44 بتاريخ 8/2/1446هـ",
    },
    {
        "id": "hrsd_labor_law_page",
        "title": "نظام العمل في المملكة | صفحة المصدر",
        "publisher": "وزارة الموارد البشرية والتنمية الاجتماعية",
        "url": "https://www.hrsd.gov.sa/knowledge-centre/decisions-and-regulations/regulation-and-procedures/%D9%86%D8%B8%D8%A7%D9%85-%D8%A7%D9%84%D8%B9%D9%85%D9%84",
        "page": "صفحة القرارات والأنظمة",
        "version_note": "صفحة المصدر الرسمية والتحديثات والروابط المرتبطة",
    },
    {
        "id": "hrsd_executive_regulation",
        "title": "اللائحة التنفيذية لنظام العمل وملحقاتها",
        "publisher": "وزارة الموارد البشرية والتنمية الاجتماعية",
        "url": "https://www.hrsd.gov.sa/knowledge-centre/decisions-and-regulations/regulation-and-procedures/%D8%A7%D9%84%D9%84%D8%A7%D8%A6%D8%AD%D8%A9-%D8%A7%D9%84%D8%AA%D9%86%D9%81%D9%8A%D8%B0%D9%8A%D8%A9-%D9%84%D9%86%D8%B8%D8%A7%D9%85-%D8%A7%D9%84%D8%B9%D9%85%D9%84-%D9%88%D9%85%D9%84%D8%AD%D9%82%D8%A7%D8%AA%D9%87%D8%A7",
        "page": "صفحة اللائحة التنفيذية",
        "version_note": "يجب التحقق من النسخة النافذة قبل الاعتماد",
    },
]

OBLIGATION_PATTERNS = [
    ("التزام صريح", re.compile(r"(?:يلتزم|يجب على|يتعين على|يتوجب على|على الطرف|لا يجوز|يحظر)\s+[^.؛\n]{5,220}")),
    ("حق أو استحقاق", re.compile(r"(?:يحق لـ|يستحق|للطرف|للعامل|لصاحب العمل)\s+[^.؛\n]{5,220}")),
]

RISK_RULES = [
    ("نطاق العمل", ["نطاق العمل", "الخدمات", "المخرجات", "deliverables"], "غياب وصف دقيق للمخرجات قد يسبب نزاعًا حول ما يجب تسليمه."),
    ("المقابل والدفع", ["الأجر", "المقابل", "الدفع", "الفاتورة", "السداد", "الرسوم"], "يجب تحديد المبلغ أو آلية التسعير وتاريخ الاستحقاق وآثار التأخير."),
    ("المدة والإنهاء", ["المدة", "ينتهي", "الإنهاء", "فسخ", "إشعار"], "غياب آلية إنهاء واضحة يرفع خطر النزاع عند الخروج من العلاقة."),
    ("السرية", ["سرية", "معلومات سرية", "عدم الإفصاح"], "غياب السرية قد يعرّض المعلومات التجارية أو بيانات العملاء للكشف."),
    ("الملكية الفكرية", ["الملكية الفكرية", "حقوق المؤلف", "الشفرة المصدرية", "الترخيص"], "يجب تحديد ملكية المخرجات وحقوق الاستخدام بعد التسليم."),
    ("حماية البيانات", ["البيانات الشخصية", "الخصوصية", "حماية البيانات", "ساما"], "غياب ضوابط البيانات يترك أغراض المعالجة والوصول والاحتفاظ غير واضحة."),
    ("المسؤولية", ["المسؤولية", "التعويض", "الضمان", "حدود المسؤولية"], "ينبغي تحديد نطاق المسؤولية والاستثناءات والحدود بصورة صريحة."),
    ("القانون والاختصاص", ["القانون واجب التطبيق", "الاختصاص", "المحكمة", "التحكيم", "تسوية المنازعات"], "غياب آلية النزاع والقانون الواجب التطبيق يزيد كلفة التصعيد."),
    ("التجديد", ["يتجدد تلقائيًا", "التجديد التلقائي", "التجديد"], "التجديد التلقائي يحتاج مدة إشعار وإجراء إلغاء واضحين."),
]

EVIDENCE_MAP = [
    ("الأجر أو المقابل", ["راتب", "أجر", "مقابل", "دفع", "فاتورة"], ["العقد", "كشوف الحساب أو التحويلات", "الفواتير", "المراسلات المالية"]),
    ("الإنهاء", ["فصل", "إنهاء", "استقالة", "فسخ", "إشعار"], ["خطاب الإنهاء", "إثبات الإشعار", "العقد", "سجل الحضور أو الأداء"]),
    ("الالتزامات", ["يلتزم", "يجب", "تسليم", "خدمة", "مخرج"], ["نسخة العقد", "الملاحق", "محاضر التسليم", "المراسلات والتعليمات"]),
    ("السرية والبيانات", ["سرية", "بيانات", "خصوصية", "إفشاء"], ["سياسة الخصوصية", "سجل الوصول", "اتفاق السرية", "إثبات الواقعة"]),
]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def source_record(article: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(article)
    result["source"] = OFFICIAL_SOURCES[0]
    result["citation"] = f"نظام العمل، المادة {article.get('article', 'غير محددة')} — وزارة الموارد البشرية"
    result["verification_required"] = True
    return result


def search_with_sources(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    return [source_record(item) for item in legal_search.search(query, max_results=max_results)]


def extract_obligations(text: str) -> List[Dict[str, Any]]:
    clean = _normalize(text)
    found: List[Dict[str, Any]] = []
    seen = set()
    # التحليل على مستوى الجملة يمنع دمج التزامات طرفين مختلفين في سجل واحد.
    sentences = [s.strip(" ،") for s in re.split(r"[.؛!?؟\\n]+", clean) if s.strip()]
    for sentence in sentences:
        for kind, pattern in OBLIGATION_PATTERNS:
            match = pattern.search(sentence)
            if not match:
                continue
            statement = match.group(0).strip(" ،")
            key = statement[:220]
            if key in seen:
                continue
            seen.add(key)
            party = "غير محدد"
            if "صاحب العمل" in statement:
                party = "صاحب العمل"
            elif "العامل" in statement:
                party = "العامل"
            elif "المورد" in statement or "المقاول" in statement:
                party = "المورد/المقاول"
            elif "العميل" in statement:
                party = "العميل"
            found.append({"type": kind, "party": party, "text": statement, "confidence": "متوسطة", "needs_review": True})
    return found[:80]


def scan_risks(text: str) -> List[Dict[str, Any]]:
    clean = _normalize(text).lower()
    risks = []
    for name, terms, explanation in RISK_RULES:
        present = any(term.lower() in clean for term in terms)
        if not present:
            risks.append({"area": name, "severity": "مرتفع" if name in {"المدة والإنهاء", "المسؤولية", "القانون والاختصاص"} else "متوسط", "finding": explanation, "status": "غير ظاهر في النص", "action": f"أضف بندًا واضحًا يغطي {name} أو أكد سبب عدم انطباقه."})
    if re.search(r"(?:غير محدود|دون حد|لا يتحمل أي مسؤولية|إعفاء كامل)", clean):
        risks.append({"area": "إعفاء أو مسؤولية غير متوازنة", "severity": "مرتفع", "finding": "يظهر نص قد يستبعد المسؤولية بصورة واسعة.", "status": "مؤشر يحتاج مراجعة", "action": "حدد الاستثناءات والحد المالي والضرر المباشر وغير المباشر."})
    return risks


def evidence_checklist(text: str) -> List[Dict[str, Any]]:
    clean = _normalize(text).lower()
    result = []
    for issue, terms, evidence in EVIDENCE_MAP:
        if any(term.lower() in clean for term in terms):
            result.append({"issue": issue, "documents": evidence, "priority": "عالية"})
    return result


def legal_review_package(text: str) -> Dict[str, Any]:
    obligations = extract_obligations(text)
    risks = scan_risks(text)
    evidence = evidence_checklist(text)
    article_numbers = sorted(set(re.findall(r"(?:المادة|مادة)\s*([0-9]{1,3})", text)))
    sources = [source_record(item) for number in article_numbers for item in legal_search.search(number, max_results=1)]
    if not sources:
        sources = [{"source": source, "citation": "مصدر رسمي عام — يلزم ربط النتيجة بمادة محددة"} for source in OFFICIAL_SOURCES[:2]]
    return {
        "obligations": obligations,
        "risks": risks,
        "evidence_checklist": evidence,
        "mentioned_articles": article_numbers,
        "sources": sources,
        "quality": {"grounding": "جزئي", "requires_lawyer_review": True, "reason": "الاستخراج حتمي جزئيًا والمادة النافذة يجب التحقق منها"},
    }
