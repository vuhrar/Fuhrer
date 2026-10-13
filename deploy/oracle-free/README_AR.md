# نشر FüLaw على VM مجاني خاص

هذا المسار لا يرفع ملفات القضايا إلى GitHub أو إلى خدمة استضافة عامة. يجهز VM Ubuntu ليشغل التطبيق داخل Docker، ويحفظ البيانات في volume خاص، ويعرضه عبر Tailscale فقط.

## الاختيار المجاني الواقعي

يوفر Oracle Cloud موارد Always Free في بعض المناطق، لكن إنشاء الحساب وتوفر السعة قد يتطلبان تسجيلًا يدويًا وقد لا يكون VM متاحًا في كل منطقة. لا يستطيع التطبيق إنشاء الحساب أو تجاوز متطلبات التحقق بدلًا عن المستخدم. راجع: https://www.oracle.com/cloud/free/ و https://docs.oracle.com/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm

Tailscale لا يقدم VM، لكنه يربط جهاز المستخدم والـVM بشبكة خاصة. خطته الشخصية المجانية مناسبة لعدد محدود من المستخدمين والأجهزة: https://tailscale.com/pricing

## التنفيذ

أنشئ Ubuntu 24.04 VM، ثم استخدم `cloud-init.sh` أثناء الإنشاء أو نفذه بحذر عبر SSH. بعد ذلك انسخ المشروع إلى `/opt/fulaw` باستخدام SSH خاص بك، ولا تستخدم رمز GitHub داخل ملف cloud-init.

انسخ `.env.example` إلى `.env` وأنشئ القيم السرية على الخادم:

```bash
cd /opt/fulaw
cp .env.example .env
python3 - <<'PY'
from cryptography.fernet import Fernet
from pathlib import Path
p=Path('.env')
s=p.read_text()
s=s.replace('APP_ACCESS_TOKEN=غيّر_هذا_إلى_رمز_طويل_وفريد', 'APP_ACCESS_TOKEN=' + Fernet.generate_key().decode())
s=s.replace('FULAW_STORAGE_KEY=', 'FULAW_STORAGE_KEY=' + Fernet.generate_key().decode())
p.write_text(s)
PY
chmod 600 .env
docker compose up -d --build
```

سجّل الخادم في Tailscale، ثم اجعل الخدمة متاحة داخل الشبكة الخاصة فقط:

```bash
sudo tailscale up
sudo tailscale serve --bg http://127.0.0.1:8000
```

لا تفتح المنفذ 8000 في Security List أو الجدار الناري العام. استخدم عنوان HTTPS الذي يعرضه Tailscale، واحتفظ بالـVM وvolume والنسخ الاحتياطية تحت حسابك أنت.

## الخصوصية المطبقة

ملفات القضية والنصوص المستخرجة تُشفّر محليًا باستخدام Fernet. لا تضع `.env` أو `.storage.key` أو مجلد البيانات في Git. النسخة الاحتياطية تحتوي على ملفات مشفرة، لكن لا تحفظ مفتاح التشفير بجانب النسخة الاحتياطية.

مكتبة الأنظمة المضافة من واجهة التطبيق تُفهرس وتُخزن مشفرة أيضًا. نتائجها تظهر كـ`مكتبة المستخدم` وتحتاج مراجعة، ولا تُرفع تلقائيًا إلى قائمة المصادر الرسمية ولا تُعامل كأنها نظام نافذ.
