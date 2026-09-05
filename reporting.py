from __future__ import annotations

from typing import Any, Dict


def build_matter_report(matter: Dict[str, Any]) -> str:
    lines = [
        f"# مذكرة تشغيلية — {matter.get('title', 'ملف قانوني')}",
        "",
        "> هذه المذكرة مخرج عمل أولي للمراجعة الداخلية، وليست رأيًا قانونيًا نهائيًا.",
        "",
        "## بيانات الملف",
        "",
        f"- الحالة: {matter.get('status', '')}",
        f"- النوع: {matter.get('matter_type', '')}",
        f"- الأولوية: {matter.get('priority', '')}",
        f"- العميل: {matter.get('client_name', '') or 'غير محدد'}",
        f"- الطرف المقابل: {matter.get('opposing_party', '') or 'غير محدد'}",
        f"- الاختصاص: {matter.get('jurisdiction', '') or 'غير محدد'}",
        "",
        "## الوصف والوقائع المدخلة",
        "",
        matter.get("description", "") or "لم تُسجل وقائع وصفية بعد.",
        "",
        "## المهام التشغيلية",
        "",
    ]
    tasks = matter.get("tasks", [])
    if tasks:
        for task in tasks:
            lines.append(f"- [{task.get('status', 'مفتوحة')}] {task.get('title', '')} — الموعد: {task.get('due_date') or 'غير محدد'} — الأولوية: {task.get('priority', 'متوسطة')}")
    else:
        lines.append("- لا توجد مهام مسجلة.")
    lines.extend(["", "## الأطراف", ""])
    parties = matter.get("parties", [])
    if parties:
        for party in parties:
            lines.append(f"- {party.get('name', '')} — الصفة: {party.get('role', '')} — التواصل: {party.get('contact') or 'غير مسجل'}")
    else:
        lines.append("- لا توجد أطراف مسجلة.")
    lines.extend(["", "## الخط الزمني والوقائع", ""])
    facts = matter.get("facts", [])
    if facts:
        for fact in facts:
            lines.append(f"- {fact.get('event_date') or 'تاريخ غير محدد'} — {fact.get('title', '')} — درجة التحقق: {fact.get('certainty', 'غير متحقق')}")
            if fact.get("description"):
                lines.append(f"  - الوصف: {fact['description']}")
    else:
        lines.append("- لا توجد وقائع مسجلة.")
    lines.extend(["", "## الطلبات والمواقف القانونية", ""])
    claims = matter.get("claims", [])
    if claims:
        for claim in claims:
            lines.append(f"- {claim.get('title', '')} — الحالة: {claim.get('status', 'قيد التحقق')} — الموقف: {claim.get('position', 'مقترح')}")
            if claim.get("legal_basis"):
                lines.append(f"  - الأساس المدخل: {claim['legal_basis']}")
    else:
        lines.append("- لا توجد طلبات مسجلة.")
    lines.extend(["", "## المواعيد والإجراءات", ""])
    deadlines = matter.get("deadlines", [])
    if deadlines:
        for deadline in deadlines:
            lines.append(f"- {deadline.get('due_date') or 'تاريخ غير محدد'} — {deadline.get('title', '')} — الحالة: {deadline.get('status', 'مفتوح')} — المصدر: {deadline.get('source') or 'غير مسجل'}")
    else:
        lines.append("- لا توجد مواعيد مسجلة.")
    lines.extend(["", "## المستندات المرتبطة", ""])
    documents = matter.get("documents", [])
    if documents:
        for doc in documents:
            lines.append(f"- {doc.get('filename', '')} — النوع: {doc.get('kind', '')} — البصمة: `{doc.get('source_hash', '')}`")
    else:
        lines.append("- لا توجد مستندات مرتبطة.")
    lines.extend(["", "## ضوابط الجودة", "", "- يجب التحقق من النسخة النافذة للنظام والمصدر الرسمي.", "- يجب فصل الوقائع المثبتة عن الاستنتاجات والافتراضات.", "- يجب مراجعة أي موعد أو التزام إجرائي مع المستند الأصلي.", "- يجب اعتماد المذكرة من محامٍ مؤهل قبل إرسالها أو اتخاذ إجراء بناءً عليها.", ""])
    return "\n".join(lines)
