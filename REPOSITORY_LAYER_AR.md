# طبقة Repository المرنة

الملف `repository.py` يقدم واجهة موحدة لتخزين الكيانات والجمل القانونية ومحفزات الحقوق وقرارات المراجعة، دون أن تعتمد محركات التحليل على نوع قاعدة البيانات.

## SQLite المحلي

إذا لم تضبط `DATABASE_URL` يستخدم النظام:

```text
$FUHRER_DATA_DIR/workspace.sqlite3
```

أو يمكن تحديده صراحة:

```env
DATABASE_URL=sqlite:////absolute/path/workspace.sqlite3
```

## PostgreSQL الإنتاجي

```env
DATABASE_URL=postgresql://user:password@host:5432/fuhrer
```

يجب تثبيت `psycopg2-binary`، وهو موجود ضمن `requirements.txt`.

## الاستخدام

```python
from repository import repository_from_env

repo = repository_from_env()
entity = repo.save_entity(
    matter_id="matter_1",
    document_id="doc_1",
    entity_type="pay_record",
    value={"agreed": 10000, "paid": 8500},
    page_number=2,
    excerpt="10000 | 8500",
    confidence=0.94,
)

statement = repo.save_statement(
    matter_id="matter_1",
    document_id="doc_1",
    text="تدعي الإدارة أن العامل لم يعمل ساعات إضافية",
    speaker="الإدارة",
    polarity="منفي",
    status="negated_by_employer",
    negation_cue="لم",
    page_number=3,
    confidence=0.82,
)

repo.save_right_trigger(
    discovered_right_id="right_1",
    entity_id=entity["id"],
    statement_id=statement["id"],
    trigger_type="contradiction",
    excerpt="10000 | 8500",
    page_number=2,
    source_quality=0.95,
)
```

## ملاحظات الإنتاج

- لا تضع كلمة مرور PostgreSQL في الواجهة أو في المستودع.
- استخدم متغيرات بيئية أو مدير أسرار.
- شغّل `init_schema()` أثناء مرحلة نشر منفصلة، وليس مع كل طلب HTTP في الإنتاج.
- أنشئ migrations رسمية قبل تغيير المخطط الإنتاجي.
- طبقة Repository الحالية لا تحذف الجداول القائمة؛ تنشئ فقط جداول البيانات المنظمة الجديدة.
- SQLite مناسب للاستخدام الفردي المحلي، وPostgreSQL هو الخيار المناسب للنسخة المستضافة أو المهام المتوازية.
