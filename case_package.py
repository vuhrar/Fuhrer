from __future__ import annotations

import json
from html import escape
from datetime import datetime, timezone
from typing import Any, Dict


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_package(matter: Dict[str, Any]) -> Dict[str, Any]:
    facts = matter.get("facts", [])
    claims = matter.get("claims", [])
    documents = matter.get("documents", [])
    tasks = matter.get("tasks", [])
    deadlines = matter.get("deadlines", [])
    return {
        "package_version": "1.0",
        "generated_at": _now(),
        "disclaimer": "مخرج عمل أولي للمراجعة الشخصية؛ لا يمثل رأيًا قانونيًا نهائيًا ولا يغني عن التحقق المهني.",
        "matter": {k: matter.get(k, "") for k in ("id", "title", "matter_type", "status", "priority", "client_name", "opposing_party", "jurisdiction", "description", "created_at", "updated_at")},
        "parties": matter.get("parties", []),
        "chronology": sorted(facts, key=lambda x: (x.get("event_date") or "9999", x.get("created_at") or "")),
        "claims_matrix": [{
            "claim": claim,
            "related_facts": [fact for fact in facts if claim.get("title", "").split()[0:2] and any(word in (fact.get("title", "") + " " + fact.get("description", "")) for word in claim.get("title", "").split()[:2])],
            "verification_status": claim.get("status", "قيد التحقق"),
        } for claim in claims],
        "evidence_index": [{"id": d.get("id"), "filename": d.get("filename"), "kind": d.get("kind"), "hash": d.get("source_hash"), "created_at": d.get("created_at")} for d in documents],
        "deadlines": deadlines,
        "tasks": tasks,
        "audit": matter.get("audit", []),
        "quality_flags": {
            "facts_without_date": sum(1 for x in facts if not x.get("event_date")),
            "unverified_facts": sum(1 for x in facts if x.get("certainty") not in ("مثبت بمستند", "مؤيد بقرائن")),
            "claims_without_basis": sum(1 for x in claims if not x.get("legal_basis")),
            "documents_count": len(documents),
            "open_deadlines": sum(1 for x in deadlines if x.get("status") not in ("مكتمل", "ملغى")),
        },
    }


def to_markdown(package: Dict[str, Any]) -> str:
    matter = package["matter"]
    lines = [f"# ملف النزاع الكامل: {matter.get('title', '')}", "", f"> {package['disclaimer']}", "", "## 1. ملخص الملف", "", f"- النوع: {matter.get('matter_type', '')}", f"- الحالة: {matter.get('status', '')}", f"- الأولوية: {matter.get('priority', '')}", f"- العميل: {matter.get('client_name') or 'غير محدد'}", f"- الطرف المقابل: {matter.get('opposing_party') or 'غير محدد'}", f"- الاختصاص: {matter.get('jurisdiction') or 'غير محدد'}", "", matter.get("description", "") or "لا يوجد وصف مدخل.", "", "## 2. الأطراف", ""]
    for p in package["parties"] or [{}]:
        lines.append(f"- {p.get('name', 'لا توجد أطراف')} — {p.get('role', '')} — {p.get('contact', '')}")
    lines.extend(["", "## 3. الخط الزمني", ""])
    for f in package["chronology"] or [{}]:
        lines.append(f"- {f.get('event_date') or 'تاريخ غير محدد'} | {f.get('title', 'لا توجد وقائع')} | التحقق: {f.get('certainty', 'غير متحقق')} | {f.get('description', '')}")
    lines.extend(["", "## 4. مصفوفة الطلبات والادعاءات", ""])
    for item in package["claims_matrix"] or [{}]:
        claim = item.get("claim", {})
        lines.append(f"### {claim.get('title', 'لا توجد طلبات')}")
        lines.append(f"- الحالة: {claim.get('status', 'قيد التحقق')} — الموقف: {claim.get('position', 'مقترح')}")
        lines.append(f"- الأساس المدخل: {claim.get('legal_basis') or 'غير مدخل ويحتاج تحققًا'}")
        related = item.get("related_facts", [])
        lines.append(f"- الوقائع المرشحة للارتباط: {', '.join(x.get('title', '') for x in related) or 'لا توجد مطابقة آلية؛ يجب الربط يدويًا'}")
    lines.extend(["", "## 5. فهرس الأدلة والمستندات", ""])
    for e in package["evidence_index"] or [{}]:
        lines.append(f"- {e.get('filename', 'لا توجد مستندات')} — {e.get('kind', '')} — SHA-256: `{e.get('hash', '')}`")
    lines.extend(["", "## 6. المواعيد والإجراءات", ""])
    for d in package["deadlines"] or [{}]:
        lines.append(f"- {d.get('due_date') or 'غير محدد'} — {d.get('title', 'لا توجد مواعيد')} — الحالة: {d.get('status', 'مفتوح')} — المصدر: {d.get('source', '')}")
    lines.extend(["", "## 7. المهام", ""])
    for t in package["tasks"] or [{}]:
        lines.append(f"- {t.get('title', 'لا توجد مهام')} — {t.get('status', 'مفتوحة')} — الموعد: {t.get('due_date') or 'غير محدد'}")
    q = package["quality_flags"]
    lines.extend(["", "## 8. فحص جودة الملف", "", f"- وقائع بلا تاريخ: {q['facts_without_date']}", f"- وقائع غير متحققة أو محل نزاع: {q['unverified_facts']}", f"- طلبات بلا أساس مدخل: {q['claims_without_basis']}", f"- عدد المستندات: {q['documents_count']}", f"- المواعيد المفتوحة: {q['open_deadlines']}", "", "## 9. ضوابط قبل الاعتماد", "", "- مطابقة كل واقعة بالمستند الأصلي أو تسجيلها صراحة كواقعة غير متحققة.", "- مراجعة النص النظامي النافذ وتاريخ آخر تحديث من المصدر الرسمي.", "- مراجعة المواعيد والإجراءات من الإشعارات أو المنصات الرسمية.", "- مراجعة المذكرة من محامٍ مرخص قبل تقديمها أو اتخاذ إجراء قانوني."])
    return "\n".join(lines)


def to_json(package: Dict[str, Any]) -> str:
    return json.dumps(package, ensure_ascii=False, indent=2)


def to_html(package: Dict[str, Any]) -> str:
    matter = package["matter"]
    q = package["quality_flags"]
    def e(value: Any) -> str:
        return escape(str(value or ""))
    party_rows = "".join(f"<tr><td>{e(p.get('name'))}</td><td>{e(p.get('role'))}</td><td>{e(p.get('contact'))}</td></tr>" for p in package["parties"])
    fact_rows = "".join(f"<tr><td>{e(f.get('event_date') or 'غير محدد')}</td><td>{e(f.get('title'))}</td><td>{e(f.get('certainty'))}</td><td>{e(f.get('description'))}</td></tr>" for f in package["chronology"])
    claim_rows = "".join(f"<tr><td>{e(x.get('claim', {}).get('title'))}</td><td>{e(x.get('claim', {}).get('status'))}</td><td>{e(x.get('claim', {}).get('legal_basis') or 'غير مدخل')}</td><td>{e(', '.join(f.get('title','') for f in x.get('related_facts', [])) or 'لا يوجد ربط آلي')}</td></tr>" for x in package["claims_matrix"])
    evidence_rows = "".join(f"<tr><td>{e(x.get('filename'))}</td><td>{e(x.get('kind'))}</td><td><code>{e(x.get('hash'))}</code></td></tr>" for x in package["evidence_index"])
    deadline_rows = "".join(f"<tr><td>{e(d.get('due_date') or 'غير محدد')}</td><td>{e(d.get('title'))}</td><td>{e(d.get('status'))}</td><td>{e(d.get('source'))}</td></tr>" for d in package["deadlines"])
    task_rows = "".join(f"<tr><td>{e(t.get('title'))}</td><td>{e(t.get('status'))}</td><td>{e(t.get('due_date') or 'غير محدد')}</td></tr>" for t in package["tasks"])
    return f'''<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ملف النزاع - {e(matter.get('title'))}</title><style>body{{font-family:Arial,Tahoma,sans-serif;max-width:1100px;margin:0 auto;padding:32px;color:#17202a;line-height:1.7}}h1,h2{{color:#123b4a;border-bottom:2px solid #d9e6ea;padding-bottom:6px}}.notice{{background:#fff7e6;border:1px solid #e8c46a;padding:12px;border-radius:8px}}table{{border-collapse:collapse;width:100%;margin:12px 0 28px}}th,td{{border:1px solid #cbd8dc;padding:8px;text-align:right;vertical-align:top}}th{{background:#eaf2f4}}.meta{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}}.meta div{{background:#f4f7f8;padding:8px;border-radius:6px}}.quality{{display:grid;grid-template-columns:repeat(5,1fr);gap:8px}}.quality div{{border:1px solid #cbd8dc;padding:10px;text-align:center}}@media print{{body{{padding:0}}.no-print{{display:none}}}}</style></head><body><p class="no-print">تم توليد هذا الملف للمراجعة والطباعة. راجع الوقائع والمصادر قبل الاعتماد.</p><h1>ملف النزاع الكامل: {e(matter.get('title'))}</h1><div class="notice">{e(package['disclaimer'])}</div><h2>1. ملخص الملف</h2><div class="meta"><div><b>النوع</b><br>{e(matter.get('matter_type'))}</div><div><b>الحالة</b><br>{e(matter.get('status'))}</div><div><b>الأولوية</b><br>{e(matter.get('priority'))}</div><div><b>العميل</b><br>{e(matter.get('client_name') or 'غير محدد')}</div><div><b>الطرف المقابل</b><br>{e(matter.get('opposing_party') or 'غير محدد')}</div><div><b>الاختصاص</b><br>{e(matter.get('jurisdiction') or 'غير محدد')}</div></div><p>{e(matter.get('description') or 'لا يوجد وصف مدخل.')}</p><h2>2. الأطراف</h2><table><tr><th>الاسم</th><th>الصفة</th><th>التواصل</th></tr>{party_rows or '<tr><td colspan="3">لا توجد أطراف</td></tr>'}</table><h2>3. الخط الزمني والوقائع</h2><table><tr><th>التاريخ</th><th>العنوان</th><th>التحقق</th><th>الوصف</th></tr>{fact_rows or '<tr><td colspan="4">لا توجد وقائع</td></tr>'}</table><h2>4. مصفوفة الطلبات والادعاءات</h2><table><tr><th>الطلب</th><th>الحالة</th><th>الأساس المدخل</th><th>الوقائع المرتبطة</th></tr>{claim_rows or '<tr><td colspan="4">لا توجد طلبات</td></tr>'}</table><h2>5. فهرس الأدلة</h2><table><tr><th>الملف</th><th>النوع</th><th>SHA-256</th></tr>{evidence_rows or '<tr><td colspan="3">لا توجد مستندات</td></tr>'}</table><h2>6. المواعيد والإجراءات</h2><table><tr><th>التاريخ</th><th>الإجراء</th><th>الحالة</th><th>المصدر</th></tr>{deadline_rows or '<tr><td colspan="4">لا توجد مواعيد</td></tr>'}</table><h2>7. المهام</h2><table><tr><th>المهمة</th><th>الحالة</th><th>الموعد</th></tr>{task_rows or '<tr><td colspan="3">لا توجد مهام</td></tr>'}</table><h2>8. فحص جودة الملف</h2><div class="quality"><div>بلا تاريخ<br><b>{q['facts_without_date']}</b></div><div>غير متحققة<br><b>{q['unverified_facts']}</b></div><div>طلبات بلا أساس<br><b>{q['claims_without_basis']}</b></div><div>المستندات<br><b>{q['documents_count']}</b></div><div>مواعيد مفتوحة<br><b>{q['open_deadlines']}</b></div></div><h2>9. ضوابط الاعتماد</h2><ol><li>مطابقة كل واقعة بالمستند الأصلي أو وسمها كغير متحققة.</li><li>مراجعة النص النظامي النافذ وتاريخ تحديثه من المصدر الرسمي.</li><li>مراجعة المواعيد من الإشعارات أو المنصات الرسمية.</li><li>مراجعة الملف من محامٍ مرخص قبل اتخاذ إجراء قانوني.</li></ol></body></html>'''
