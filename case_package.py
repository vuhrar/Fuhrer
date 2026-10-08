from __future__ import annotations

import json
from html import escape
from datetime import datetime, timezone
from typing import Any, Dict

from matter_intelligence import analyze_matter
import advanced_dispute_engine
import legal_case_theory
import hidden_rights_engine


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_package(matter: Dict[str, Any]) -> Dict[str, Any]:
    facts = matter.get("facts", [])
    claims = matter.get("claims", [])
    documents = matter.get("documents", [])
    tasks = matter.get("tasks", [])
    deadlines = matter.get("deadlines", [])
    claim_evidence = matter.get("claim_evidence", [])
    evidence_by_claim = {}
    for link in claim_evidence:
        evidence_by_claim.setdefault(link.get("claim_id"), []).append(link)
    quality_flags = {
        "facts_without_date": sum(1 for x in facts if not x.get("event_date")),
        "unverified_facts": sum(1 for x in facts if x.get("certainty") not in ("مثبت بمستند", "مؤيد بقرائن")),
        "claims_without_basis": sum(1 for x in claims if not x.get("legal_basis")),
        "claims_without_evidence_link": sum(1 for x in claims if not evidence_by_claim.get(x.get("id"))),
        "facts_without_source_link": sum(1 for x in facts if not x.get("source_document_id")),
        "documents_count": len(documents),
        "evidence_links_count": len(claim_evidence),
        "open_deadlines": sum(1 for x in deadlines if x.get("status") not in ("مكتمل", "ملغى")),
    }
    intelligence = analyze_matter(matter)
    advanced_review = advanced_dispute_engine.assess_matter(matter)
    case_theory = legal_case_theory.build_case_theory(matter)
    hidden_rights = hidden_rights_engine.discover(matter)
    inspections = matter.get("document_inspections", [])
    inspection_coverage = {
        "documents_total": len(inspections),
        "documents_read": sum(bool(x.get("readable")) for x in inspections),
        "documents_unreadable": sum(not bool(x.get("readable")) for x in inspections),
        "manual_review_required": any(not bool(x.get("readable")) for x in inspections),
    }
    issue_count = quality_flags["facts_without_date"] + quality_flags["unverified_facts"] + quality_flags["claims_without_basis"] + quality_flags["claims_without_evidence_link"] + quality_flags["facts_without_source_link"]
    denominator = max(1, len(facts) * 2 + len(claims) * 2 + 2)
    completeness = max(0, min(100, round(100 * (1 - issue_count / denominator))))
    return {
        "package_version": "1.2",
        "generated_at": _now(),
        "disclaimer": "مخرج عمل أولي للمراجعة الشخصية؛ لا يمثل رأيًا قانونيًا نهائيًا ولا يغني عن التحقق المهني.",
        "matter": {k: matter.get(k, "") for k in ("id", "title", "matter_type", "status", "priority", "client_name", "opposing_party", "jurisdiction", "description", "created_at", "updated_at")},
        "parties": matter.get("parties", []),
        "chronology": sorted(facts, key=lambda x: (x.get("event_date") or "9999", x.get("created_at") or "")),
        "claims_matrix": [{
            "claim": claim,
            "related_facts": [fact for fact in facts if claim.get("title", "").split()[0:2] and any(word in (fact.get("title", "") + " " + fact.get("description", "")) for word in claim.get("title", "").split()[:2])],
            "verification_status": claim.get("status", "قيد التحقق"),
            "evidence_links": evidence_by_claim.get(claim.get("id"), []),
        } for claim in claims],
        "evidence_index": [{"id": d.get("id"), "filename": d.get("filename"), "kind": d.get("kind"), "hash": d.get("source_hash"), "created_at": d.get("created_at")} for d in documents],
        "deadlines": deadlines,
        "tasks": tasks,
        "audit": matter.get("audit", []),
        "quality_flags": quality_flags,
        "completeness_score": completeness,
        "intelligence": intelligence,
        "advanced_review": advanced_review,
        "case_theory": case_theory,
        "inspection_coverage": inspection_coverage,
        "hidden_rights": hidden_rights,
        "procedure_steps": matter.get("procedure_steps", []),
        "next_actions": [
            "أضف تاريخًا لكل واقعة غير مؤرخة." if quality_flags["facts_without_date"] else "لا توجد وقائع بلا تاريخ.",
            "اربط كل واقعة بمستند أو قرينة." if quality_flags["facts_without_source_link"] else "الوقائع لها روابط مصدر مدخلة.",
            "أضف أساسًا نظاميًا لكل طلب." if quality_flags["claims_without_basis"] else "لكل طلب أساس مدخل.",
            "أضف ملاحظة مصدر أو دليل لكل طلب." if quality_flags["claims_without_evidence_link"] else "الطلبات تحتوي على ملاحظات مصدر.",
        ],
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
        evidence = item.get("evidence_links", [])
        lines.append(f"- الأدلة المرتبطة: {', '.join(x.get('filename', '') for x in evidence) or 'لا يوجد دليل مرتبط صراحة'}")
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
    intel = package.get("intelligence", {})
    readiness = intel.get("readiness", {})
    gap_lines = [f"- {x.get('finding')} — {x.get('action')}" for x in intel.get('input_gaps', [])] or ["- لا توجد نواقص آلية مسجلة."]
    contradiction_lines = [f"- {x.get('finding')} — {x.get('action')}" for x in intel.get('contradictions', [])] or ["- لم يظهر تعارض آلي؛ لا يعني ذلك عدم وجود تعارض واقعي."]
    procedure_lines = [f"- {x.get('title')}: {x.get('status')}" for x in package.get('procedure_steps', [])] or ["- لم يُنشأ مسار إجرائي."]
    advanced = package.get("advanced_review", {})
    advanced_lines = [f"- {x.get('domain')}: {x.get('severity')} — {x.get('action')}" for x in advanced.get("risk_register", [])] or ["- لا توجد مؤشرات مخاطر متقدمة مسجلة."]
    theory = package.get("case_theory", {})
    theory_lines = [f"- {x.get('issue')}: {x.get('position_gap')} — نقص الإثبات: {', '.join(x.get('missing_proof', [])) or 'لا يوجد محدد آليًا'}" for x in theory.get("issues", [])] or ["- لم تُصنّف مسألة قضية بعد."]
    coverage = package.get("inspection_coverage", {})
    hidden_lines = [f"- {x.get('label')}: {x.get('status')} — {x.get('reason')} — المصدر: {', '.join(t.get('filename') or 'مدخلات القضية' for t in x.get('triggers', [])[:2])}" for x in package.get("hidden_rights", {}).get("findings", [])] or ["- لم تظهر مؤشرات حقوق من النص المفحوص."]
    lines.extend(["", "## 8. فحص جودة الملف", "", f"- درجة اكتمال الملف: {package.get('completeness_score', 0)}%", f"- درجة الجاهزية التحليلية: {readiness.get('score', 0)}% — {readiness.get('label', 'غير متاح')}", f"- تغطية المرفقات: {coverage.get('documents_read', 0)} مقروءة من {coverage.get('documents_total', 0)}", f"- ملفات تحتاج مراجعة يدوية: {coverage.get('documents_unreadable', 0)}", f"- نطاق الفحص: {intel.get('coverage', {}).get('sources_scanned', 0)} مصدر/سجل و{intel.get('coverage', {}).get('characters_scanned', 0)} حرفًا", *[f"- الإجراء التالي: {x}" for x in package.get('next_actions', [])], f"- وقائع بلا تاريخ: {q['facts_without_date']}", f"- وقائع غير متحققة أو محل نزاع: {q['unverified_facts']}", f"- طلبات بلا أساس مدخل: {q['claims_without_basis']}", f"- عدد المستندات: {q['documents_count']}", f"- روابط الأدلة: {q['evidence_links_count']}", f"- المواعيد المفتوحة: {q['open_deadlines']}", "", "### الحقوق المحتملة المكتشفة", *hidden_lines, "", "### النواقص الحرجة", *gap_lines, "", "### التناقضات المحتملة", *contradiction_lines, "", "## 9. المسار الإجرائي", *procedure_lines, "", "## 10. سجل المخاطر المتقدم", *advanced_lines, "", "## 11. نظرية القضية وخطة المواجهة", *theory_lines, "", "## 12. ضوابط قبل الاعتماد", "", "- مطابقة كل واقعة بالمستند الأصلي أو تسجيلها صراحة كواقعة غير متحققة.", "- مراجعة النص النظامي النافذ وتاريخ آخر تحديث من المصدر الرسمي.", "- مراجعة المواعيد والإجراءات من الإشعارات أو المنصات الرسمية.", "- مراجعة المذكرة من محامٍ مرخص قبل تقديمها أو اتخاذ إجراء قانوني."])
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
    claim_rows = "".join(f"<tr><td>{e(x.get('claim', {}).get('title'))}</td><td>{e(x.get('claim', {}).get('status'))}</td><td>{e(x.get('claim', {}).get('legal_basis') or 'غير مدخل')}</td><td>{e(', '.join(f.get('title','') for f in x.get('related_facts', [])) or 'لا يوجد ربط آلي')}</td><td>{e(', '.join(v.get('filename','') for v in x.get('evidence_links', [])) or 'لا يوجد دليل مرتبط')}</td></tr>" for x in package["claims_matrix"])
    evidence_rows = "".join(f"<tr><td>{e(x.get('filename'))}</td><td>{e(x.get('kind'))}</td><td><code>{e(x.get('hash'))}</code></td></tr>" for x in package["evidence_index"])
    deadline_rows = "".join(f"<tr><td>{e(d.get('due_date') or 'غير محدد')}</td><td>{e(d.get('title'))}</td><td>{e(d.get('status'))}</td><td>{e(d.get('source'))}</td></tr>" for d in package["deadlines"])
    task_rows = "".join(f"<tr><td>{e(t.get('title'))}</td><td>{e(t.get('status'))}</td><td>{e(t.get('due_date') or 'غير محدد')}</td></tr>" for t in package["tasks"])
    procedure_rows = "".join(f"<tr><td>{e(x.get('title'))}</td><td>{e(x.get('status'))}</td><td>{e(x.get('completed_at') or 'غير مكتملة')}</td></tr>" for x in package.get("procedure_steps", []))
    intel = package.get("intelligence", {})
    readiness = intel.get("readiness", {})
    gap_rows = "".join(f"<li>{e(x.get('finding'))} — {e(x.get('action'))}</li>" for x in intel.get("input_gaps", [])) or "<li>لا توجد نواقص آلية مسجلة.</li>"
    contradiction_rows = "".join(f"<li>{e(x.get('finding'))} — {e(x.get('action'))}</li>" for x in intel.get("contradictions", [])) or "<li>لم يظهر تعارض آلي؛ لا يعني ذلك عدم وجود تعارض واقعي.</li>"
    return f'''<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ملف النزاع - {e(matter.get('title'))}</title><style>body{{font-family:Arial,Tahoma,sans-serif;max-width:1100px;margin:0 auto;padding:32px;color:#17202a;line-height:1.7}}h1,h2{{color:#123b4a;border-bottom:2px solid #d9e6ea;padding-bottom:6px}}.notice{{background:#fff7e6;border:1px solid #e8c46a;padding:12px;border-radius:8px}}table{{border-collapse:collapse;width:100%;margin:12px 0 28px}}th,td{{border:1px solid #cbd8dc;padding:8px;text-align:right;vertical-align:top}}th{{background:#eaf2f4}}.meta{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}}.meta div{{background:#f4f7f8;padding:8px;border-radius:6px}}.quality{{display:grid;grid-template-columns:repeat(5,1fr);gap:8px}}.quality div{{border:1px solid #cbd8dc;padding:10px;text-align:center}}@media print{{body{{padding:0}}.no-print{{display:none}}}}</style></head><body><p class="no-print">تم توليد هذا الملف للمراجعة والطباعة. راجع الوقائع والمصادر قبل الاعتماد.</p><h1>ملف النزاع الكامل: {e(matter.get('title'))}</h1><div class="notice">{e(package['disclaimer'])}</div><h2>1. ملخص الملف</h2><div class="meta"><div><b>النوع</b><br>{e(matter.get('matter_type'))}</div><div><b>الحالة</b><br>{e(matter.get('status'))}</div><div><b>الأولوية</b><br>{e(matter.get('priority'))}</div><div><b>العميل</b><br>{e(matter.get('client_name') or 'غير محدد')}</div><div><b>الطرف المقابل</b><br>{e(matter.get('opposing_party') or 'غير محدد')}</div><div><b>الاختصاص</b><br>{e(matter.get('jurisdiction') or 'غير محدد')}</div></div><p>{e(matter.get('description') or 'لا يوجد وصف مدخل.')}</p><h2>2. الأطراف</h2><table><tr><th>الاسم</th><th>الصفة</th><th>التواصل</th></tr>{party_rows or '<tr><td colspan="3">لا توجد أطراف</td></tr>'}</table><h2>3. الخط الزمني والوقائع</h2><table><tr><th>التاريخ</th><th>العنوان</th><th>التحقق</th><th>الوصف</th></tr>{fact_rows or '<tr><td colspan="4">لا توجد وقائع</td></tr>'}</table><h2>4. مصفوفة الطلبات والادعاءات</h2><table><tr><th>الطلب</th><th>الحالة</th><th>الأساس المدخل</th><th>الوقائع المرتبطة</th><th>الأدلة المرتبطة</th></tr>{claim_rows or '<tr><td colspan="4">لا توجد طلبات</td></tr>'}</table><h2>5. فهرس الأدلة</h2><table><tr><th>الملف</th><th>النوع</th><th>SHA-256</th></tr>{evidence_rows or '<tr><td colspan="3">لا توجد مستندات</td></tr>'}</table><h2>6. المواعيد والإجراءات</h2><table><tr><th>التاريخ</th><th>الإجراء</th><th>الحالة</th><th>المصدر</th></tr>{deadline_rows or '<tr><td colspan="4">لا توجد مواعيد</td></tr>'}</table><h2>7. المهام</h2><table><tr><th>المهمة</th><th>الحالة</th><th>الموعد</th></tr>{task_rows or '<tr><td colspan="3">لا توجد مهام</td></tr>'}</table><h2>8. فحص جودة الملف والجاهزية</h2><div class="notice"><b>درجة اكتمال الملف: {package.get('completeness_score', 0)}%</b><br><b>درجة الجاهزية التحليلية: {e(readiness.get('score', 0))}% — {e(readiness.get('label', 'غير متاح'))}</b><br>نطاق الفحص: {e(intel.get('coverage', {}).get('sources_scanned', 0))} مصدر/سجل و{e(intel.get('coverage', {}).get('characters_scanned', 0))} حرفًا<br>{e(' | '.join(package.get('next_actions', [])))}</div><div class="quality"><div>بلا تاريخ<br><b>{q['facts_without_date']}</b></div><div>غير متحققة<br><b>{q['unverified_facts']}</b></div><div>طلبات بلا أساس<br><b>{q['claims_without_basis']}</b></div><div>المستندات<br><b>{q['documents_count']}</b></div><div>مواعيد مفتوحة<br><b>{q['open_deadlines']}</b></div></div><h3>النواقص</h3><ul>{gap_rows}</ul><h3>التناقضات المحتملة</h3><ul>{contradiction_rows}</ul><h2>9. المسار الإجرائي</h2><table><tr><th>المرحلة</th><th>الحالة</th><th>تاريخ الإنجاز</th></tr>{procedure_rows or '<tr><td colspan="3">لا يوجد مسار إجرائي</td></tr>'}</table><h2>10. سجل المخاطر المتقدم</h2><ul>{"".join(f"<li>{e(x.get('domain'))}: {e(x.get('severity'))} — {e(x.get('action'))}</li>" for x in package.get("advanced_review", {}).get("risk_register", [])) or "<li>لا توجد مؤشرات مسجلة.</li>"}</ul><h2>11. نظرية القضية وخطة المواجهة</h2><ul>{"".join(f"<li>{e(x.get('issue'))}: {e(x.get('position_gap'))} — نقص الإثبات: {e(', '.join(x.get('missing_proof', [])) or 'لا يوجد محدد آليًا')}</li>" for x in package.get("case_theory", {}).get("issues", [])) or "<li>لم تُصنّف مسألة قضية بعد.</li>"}</ul><h2>12. ضوابط الاعتماد</h2><ol><li>مطابقة كل واقعة بالمستند الأصلي أو وسمها كغير متحققة.</li><li>مراجعة النص النظامي النافذ وتاريخ تحديثه من المصدر الرسمي.</li><li>مراجعة المواعيد من الإشعارات أو المنصات الرسمية.</li><li>مراجعة الملف من محامٍ مرخص قبل اتخاذ إجراء قانوني.</li></ol></body></html>'''
