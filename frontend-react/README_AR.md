# واجهة Führer React للحقوق القانونية

واجهة RTL متجاوبة مصممة للاستخدام الخاص على iPhone 13، وتتصل بمسارات FastAPI التالية:

- `POST /api/matters/{matter_id}/rights/analyze`
- `GET /api/matters/{matter_id}/repository-rights`
- `GET /api/matters/{matter_id}/legal-statements`
- `POST /api/matters/{matter_id}/right-review`
- `POST /api/matters`

## التشغيل المحلي

من داخل هذا المجلد:

```bash
npm install
VITE_BACKEND_URL=http://localhost:8000 npm run dev
```

ثم افتح:

```text
http://localhost:5173
```

في التطوير يمرر Vite طلبات `/api` إلى FastAPI عبر `VITE_BACKEND_URL`. في الإنتاج يمكن بناء الملفات:

```bash
npm run build
```

ثم تقديم مجلد `dist` خلف نفس النطاق أو عبر Reverse Proxy يمرر `/api` إلى FastAPI.

## الاستخدام

1. أدخل `X-App-Token`.
2. أنشئ قضية أو أدخل معرف قضية موجودة.
3. اختر دورًا واحدًا من الأدوار الثلاثة:
   - المحامي.
   - المستشار القانوني.
   - المستشار العمالي.
4. الصق النص القانوني.
5. اضغط **حلّل واحفظ**.
6. راجع الحقوق المحتملة والجمل المحللة.
7. اختر تأكيدًا أو طلب مستند إضافي أو عدم انطباق.

الواجهة لا تعرض أدوار العامل أو القاضي، ولا تحتوي زر أدوات عامًا؛ الأدوات مرتبطة بسياق مراجعة الحقوق الحالي.
