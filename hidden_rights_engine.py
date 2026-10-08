"""اكتشاف حقوق عمالية محتملة من كامل نص القضية والمرفقات.

المخرجات مؤشرات قابلة للمراجعة وليست تقريرًا بثبوت حق أو رأيًا قانونيًا.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List

RIGHT_CATALOG = [
    {"key": "unpaid_wages", "label": "أجور متأخرة أو غير مسددة", "terms": ("راتب متأخر", "أجر متأخر", "لم يدفع", "لم يتم تحويل", "متأخرات", "مسير راتب"), "elements": ("العلاقة العمالية", "الفترة", "الأجر المستحق", "عدم السداد"), "evidence": ("العقد", "مسير الراتب", "كشف الحساب", "التحويلات", "المراسلات")},
    {"key": "overtime", "label": "عمل إضافي محتمل", "terms": ("ساعات إضافية", "عمل إضافي", "بعد الدوام", "خارج ساعات", "دوام طويل", "12 ساعة", "10 ساعات"), "elements": ("الساعات الفعلية", "الجدول أو التكليف", "المقابل", "عدم السداد"), "evidence": ("سجل الحضور", "الجداول", "رسائل التكليف", "كشف الأجر")},
    {"key": "allowances", "label": "بدل أو استحقاق إضافي غير مفحوص", "terms": ("بدل سكن", "بدل نقل", "بدل اتصال", "بدل طبي", "بدل", "مكافأة", "عمولة"), "elements": ("مصدر الاستحقاق", "الفترة", "المبلغ", "السداد أو عدمه"), "evidence": ("العقد", "اللائحة", "مسير الراتب", "التحويلات")},
    {"key": "deductions", "label": "خصم من الأجر يحتاج تحققًا", "terms": ("خصم من الراتب", "خصم", "استقطاع", "حسم", "اقتطاع"), "elements": ("المبلغ", "سبب الخصم", "الإخطار", "السند", "التناسب"), "evidence": ("مسير الراتب", "الإشعار", "التحقيق", "اللائحة")},
    {"key": "leave_balance", "label": "رصيد إجازات أو مستحقات إجازة", "terms": ("رصيد إجاز", "إجازة سنوية", "إجازة لم تتمتع", "بدل إجازة", "أيام الإجازة"), "elements": ("الرصيد", "الفترة", "الأجر", "عدم التمتع أو السداد"), "evidence": ("نظام الموارد البشرية", "طلبات الإجازة", "كشف الرصيد", "مسير التسوية")},
    {"key": "end_of_service", "label": "مكافأة نهاية خدمة محتملة", "terms": ("مكافأة نهاية الخدمة", "نهاية الخدمة", "تسوية مستحقات", "المخالصة"), "elements": ("مدة الخدمة", "الأجر الأخير", "سبب الانتهاء", "مبلغ التسوية", "السداد"), "evidence": ("العقد", "خطاب الإنهاء", "المخالصة", "كشف التسوية")},
    {"key": "notice", "label": "بدل إشعار أو سلامة الإشعار", "terms": ("بدل إشعار", "مدة الإشعار", "إشعار الإنهاء", "إنهاء فوري", "بدون إشعار"), "elements": ("نوع العقد", "تاريخ الإشعار", "تاريخ النفاذ", "مدة الإشعار أو بدله"), "evidence": ("العقد", "خطاب الإنهاء", "المراسلات", "كشف المستحقات")},
    {"key": "termination_process", "label": "سلامة سبب وإجراء الإنهاء", "terms": ("فصل", "إنهاء الخدمة", "إنهاء عقد", "استقالة", "إنذار", "تحقيق", "مخالفة"), "elements": ("صاحب القرار", "السبب", "الإخطار", "التحقيق أو الإنذار", "تاريخ النفاذ"), "evidence": ("خطاب الإنهاء", "الإنذارات", "محضر التحقيق", "سجل الحضور", "المراسلات")},
    {"key": "service_certificate", "label": "شهادة خدمة أو مستندات نهاية العلاقة", "terms": ("شهادة خدمة", "إفادة خدمة", "خبرة", "إخلاء طرف"), "elements": ("طلب الشهادة", "بيانات الخدمة", "تاريخ الانتهاء", "تسليم المستند"), "evidence": ("الطلب", "المراسلات", "الشهادة أو رفضها")},
    {"key": "retaliation_discrimination", "label": "مؤشر انتقام أو تمييز يحتاج مراجعة", "terms": ("انتقام", "تمييز", "شكوى", "بعد أن اشتكيت", "بسبب الشكوى", "معاملة مختلفة"), "elements": ("الفعل المحمي أو الشكوى", "الفعل اللاحق", "التوقيت", "المقارنة أو الدافع"), "evidence": ("الشكوى", "الرسائل", "قرارات الجزاء", "حالات مماثلة")},
    {"key": "amicable_settlement", "label": "حقوق أو مطالبات ظهرت في مسار التسوية الودية", "terms": ("التسوية الودية", "مكتب العمل", "محضر تعذر", "جلسة التسوية", "طلب التسوية"), "elements": ("رقم الطلب", "المطالبات", "الجلسات", "النتيجة", "تطابق المطالبة الحالية"), "evidence": ("رقم الطلب", "المحاضر", "الإشعارات", "المراسلات")},
]


def _occurrences(text: str, terms: Iterable[str], limit: int = 6) -> List[Dict[str, Any]]:
    output = []
    for term in terms:
        for match in re.finditer(re.escape(term), text or "", re.IGNORECASE):
            left, right = max(0, match.start() - 130), min(len(text), match.end() + 130)
            output.append({"term": term, "start": match.start(), "end": match.end(), "excerpt": " ".join(text[left:right].split())})
            if len(output) >= limit:
                return output
    return output


def _has_claim(matter: Dict[str, Any], terms: Iterable[str]) -> bool:
    claim_text = " ".join(str(x.get("title", "")) + " " + str(x.get("legal_basis", "")) for x in matter.get("claims", []) or [])
    return any(term.lower() in claim_text.lower() for term in terms)


def discover(matter: Dict[str, Any]) -> Dict[str, Any]:
    documents = matter.get("documents", []) or []
    chunks = []
    for document in documents:
        text = document.get("extracted_text", "") or ""
        if text:
            chunks.append({"document_id": document.get("id"), "filename": document.get("filename"), "text": text, "inspection_status": document.get("integrity_status")})
    base_text = " ".join([str(matter.get("title", "")), str(matter.get("description", ""))] + [str(x.get("title", "")) + " " + str(x.get("description", "")) for x in matter.get("facts", []) or []] + [x["text"] for x in chunks])
    findings = []
    for right in RIGHT_CATALOG:
        triggers = []
        for chunk in chunks + [{"document_id": None, "filename": "بيانات القضية", "text": base_text, "inspection_status": "مدخلات القضية"}]:
            triggers.extend([{**hit, "document_id": chunk.get("document_id"), "filename": chunk.get("filename")} for hit in _occurrences(chunk["text"], right["terms"])])
        if not triggers:
            continue
        mentioned = _has_claim(matter, right["terms"])
        status = "مطالبة موجودة" if mentioned else "مؤشر حق غير مذكور"
        findings.append({
            "right_key": right["key"], "label": right["label"], "status": status,
            "trigger_count": len(triggers), "triggers": triggers[:12],
            "reason": f"ظهرت إشارات نصية مرتبطة بـ{right['label']} في مدخلات القضية أو المرفقات.",
            "elements_to_verify": list(right["elements"]), "evidence_needed": list(right["evidence"]),
            "missing_items": [f"تحقق من: {element}" for element in right["elements"]],
            "human_review_required": True,
            "source_refs": [{"source": "مدخلات القضية أو المستند المرفوع", "verification_required": True}],
        })
    return {
        "engine_version": "1.0", "documents_considered": len(documents),
        "findings": findings, "undisclosed_count": sum(x["status"] == "مؤشر حق غير مذكور" for x in findings),
        "disclaimer": "هذه مؤشرات حقوق محتملة مستخرجة من النصوص، وليست إثباتًا لحق أو رأيًا قانونيًا نهائيًا.",
    }
