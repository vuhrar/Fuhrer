import requests

BASE = "http://127.0.0.1:8032"
HEADERS = {"X-App-Token": "e2e-token"}

def post(path, payload):
    r = requests.post(BASE + path, json=payload, headers=HEADERS)
    r.raise_for_status()
    return r.json()

def patch(path, payload):
    r = requests.patch(BASE + path, json=payload, headers=HEADERS)
    r.raise_for_status()
    return r.json()

matter = post("/api/matters", {
    "title": "نزاع أجر وإنهاء عقد مع مطالبة بالتسوية الودية",
    "matter_type": "نزاع عمالي",
    "client_name": "أحمد العامل",
    "opposing_party": "شركة المثال للتقنية",
    "jurisdiction": "التسوية الودية ثم المحكمة العمالية",
    "priority": "عالية",
    "description": "بدأت العلاقة في 2024-02-01 بعقد مكتوب. يقول العامل إن راتب شهر 2025-05 لم يدفع كاملًا، ثم تلقى إشعار إنهاء في 2025-06-15 دون بيان سبب واضح. تدعي الشركة وجود إخلال وانقطاع عن العمل، بينما يذكر العامل أنه أرسل اعتراضًا في 2025-06-20 وطلب التسوية الودية. توجد رسائل بريد وكشوف تحويل وحضور متعارضة تحتاج مقارنة."
})["matter"]
id = matter["id"]
post(f"/api/matters/{id}/parties", {"name":"أحمد العامل","role":"مدعٍ","contact":"سجل خاص"})
post(f"/api/matters/{id}/parties", {"name":"شركة المثال للتقنية","role":"مدعى عليها"})
post(f"/api/matters/{id}/facts", {"title":"بداية العلاقة","event_date":"2024-02-01","description":"وقع عقد مكتوب وبدأ العامل مباشرة العمل.","certainty":"مثبت بمستند"})
post(f"/api/matters/{id}/facts", {"title":"عدم اكتمال الأجر","event_date":"2025-05-31","description":"يقول العامل إن راتب مايو لم يدفع كاملًا، وتقول الشركة إن الخصم بسبب انقطاع.","certainty":"محل نزاع"})
post(f"/api/matters/{id}/facts", {"title":"إشعار الإنهاء","event_date":"2025-06-15","description":"أرسلت الشركة إشعار إنهاء، ويذكر العامل أن السبب غير واضح.","certainty":"مثبت بمستند"})
post(f"/api/matters/{id}/claims", {"title":"المطالبة بالأجر المتبقي","legal_basis":"يحتاج التحقق من عقد العمل وكشوف الأجر ونظام العمل الساري."})
post(f"/api/matters/{id}/claims", {"title":"مراجعة مشروعية الإنهاء","legal_basis":"يحتاج التحقق من سبب الإنهاء والإشعار والإجراءات والمادة النافذة."})
post(f"/api/matters/{id}/deadlines", {"title":"جلسة التسوية الودية","due_date":"2025-07-01","source":"إشعار منصة التسوية"})
patch(f"/api/matters/{id}/procedure/amicable_settlement", {"status":"جارية","notes":"تم فتح المسار، ويلزم حفظ رقم الطلب ومحضر كل جلسة."})
patch(f"/api/matters/{id}/procedure/referral", {"status":"غير مكتملة","notes":"لا يُعد محضر تعذر صادرًا بعد."})
analysis = requests.get(BASE + f"/api/matters/{id}/intelligence", headers=HEADERS)
analysis.raise_for_status()
package = requests.get(BASE + f"/api/matters/{id}/package", headers=HEADERS)
package.raise_for_status()
final = requests.get(BASE + f"/api/matters/{id}", headers=HEADERS).json()["matter"]
assert analysis.json()["analysis"]["coverage"]["sources_scanned"] >= 4
assert analysis.json()["analysis"]["readiness"]["score"] < 100
assert len(final["procedure_steps"]) == 10
assert next(x for x in final["procedure_steps"] if x["step_key"] == "amicable_settlement")["status"] == "جارية"
assert "نزاع" in package.json()["package"]["matter"]["title"]
print({
    "matter_id": id,
    "readiness": analysis.json()["analysis"]["readiness"],
    "coverage": analysis.json()["analysis"]["coverage"],
    "gaps": len(analysis.json()["analysis"]["input_gaps"]),
    "contradictions": len(analysis.json()["analysis"]["contradictions"]),
    "procedure_steps": len(final["procedure_steps"]),
})
