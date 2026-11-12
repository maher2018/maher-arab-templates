# Arab Templates — أدوات المحتوى والامتثال والأتمتة

مجموعة سكربتات بايثون عربية تشغّل منتجات متجر **Arab Templates**: مزامنة بيانات القوالب إلى Bubble، تحليل فواتير واتساب الواردة وإرسالها للسحابة، توليد حزم أوامر ذكاء اصطناعي باللهجات الخليجية، وتشغيل كل ذلك على جدولة يومية بسجلّات.

كل الاتصالات تمر عبر **Bubble Data API** للتطبيق `at-ai-lab`، والتوكن يُقرأ محليًا من `.env` ولا يُحفظ في الكود ولا يُطبع في أي مخرَج.

---

## 1) بنية المشروع

```text
arab-templates/
├── README.md                     هذا الدليل
├── .gitignore                    يستثني .env و*.bak والسجلات والمخرجات
├── data/
│   └── templates_ar.json         20 قالبًا عربيًا جاهزًا للمزامنة
├── scripts/
│   ├── bubble_data_sync.py       عميل Bubble Data API (الأساس لكل شيء)
│   ├── agents_swarm_core.py      سرب الوكلاء: جلب بيانات حيّة + كتابتها في Bubble
│   ├── scheduled_sync.py         تشغيل دوري + سجل يومي + Task Scheduler
│   ├── whatsapp_invoice_parser.py تحليل فواتير واردة + تقارير + إرسال
│   └── prompt_pack_builder.py    توليد حزم أوامر AI باللهجات الخليجية
├── products/
│   └── prompt_packs/             (مولّد) الحزم + الكتالوج + ملفات zip
├── logs/                          (محلي) سجلات التشغيل اليومية
└── reports/invoice_reports/       (محلي) تقارير الفواتير Markdown
```

> المجلدات المعلّمة بـ«محلي» مستثناة في `.gitignore`؛ تُنشأ تلقائيًا عند أول تشغيل.

---

## 2) المتطلبات والتثبيت

- **Python 3.10+** (الكود يستخدم `str | None`).
- حزمة واحدة: `requests`.

```bash
cd arab-templates
python -m pip install requests
```

### إعداد الاتصال (خطوة إلزامية قبل أي أمر)

أنشئ `scripts/.env` (مستثنى من Git) واكتب فيه:

```ini
BUBBLE_TOKEN=ضع_توكن_Data_API_هنا
BUBBLE_APP_URL=https://at-ai-lab.bubbleapps.io/version-test
```

- `BUBBLE_TOKEN`: من Bubble → **Settings → API** (لا تشاركه ولا تضعه في الكود).
- `BUBBLE_APP_URL`: نطاق تطبيقك. أضف `/version-test` للعمل على بيانات التطوير، واحذفه للنسخة الحيّة بعد نشر إعدادات API (Deploy).
- يمكن بدلًا من الملف تصدير متغيّري البيئة `BUBBLE_TOKEN` و`BUBBLE_APP_URL`.

### تهيئة Bubble (مرة واحدة)

1. **Settings → API**: فعّل Data API، وأنشئ توكنًا، واسمح بالعمليات المطلوبة (Read/Create/Modify) في Privacy Rules لكل نوع.
2. **Data Types المطلوبة:**

| النوع | الحقول (حساسة لحالة الأحرف) | الاستخدام |
| --- | --- | --- |
| `task` | `Task_Name` نص، `Priority` نص، `Progress_Percentage` رقم | لوحة الكانبان / الاختبار السريع |
| `template` | `Title` نص، `Category` نص، `description` نص، `price` رقم، `preview_url` نص | منتجات المتجر |
| `invoice` | `Supplier` نص، `Invoice_Date` نص، `Total_Amount` رقم، `Tax_Amount` رقم، `Raw_Text` نص | فواتير الامتثال الضريبي |

> ⚠️ الكتابة في Bubble حسّاسة لحالة الأحرف (`Title` بحرف كبير، `description` بحرف صغير…) بينما البحث غير حسّاس. السكربت يطابق أسماء الحقول تلقائيًا من أول سجل موجود، ويطبع أسماء الحقول الفعلية عند أي اختلاف.

---

## 3) وظيفة كل ملف وطريقة استخدامه

### `scripts/bubble_data_sync.py` — عميل Bubble Data API
الأساس الذي تستخدمه بقية السكربتات: قراءة، إنشاء، تحديث، إنشاء جماعي، و`upsert` (إنشاء أو تحديث حسب مفتاح)، مع إعادة محاولة عند تعذّر الاتصال ورسائل عربية تشرح كل رمز حالة.

```bash
cd arab-templates
python scripts/bubble_data_sync.py check                      # فحص الاتصال والتوكن
python scripts/bubble_data_sync.py schema --type template    # أسماء الحقول الفعلية
python scripts/bubble_data_sync.py list --type task --limit 5
python scripts/bubble_data_sync.py sync-templates --dry-run  # معاينة بلا كتابة
python scripts/bubble_data_sync.py sync-templates            # رفع/تحديث العيّنة المدمجة
python scripts/bubble_data_sync.py sync-templates --json data/templates_ar.json
python scripts/bubble_data_sync.py test-task                 # إنشاء ثم تحديث على task
```

الربط بببل: `POST /api/1.1/obj/<type>` للإنشاء، `PATCH /api/1.1/obj/<type>/<id>` للتحديث، و`GET /api/1.1/obj/<type>?constraints=[…]` للبحث بمفتاح التطابق قبل الإنشاء (منع التكرار).

### `scripts/whatsapp_invoice_parser.py` — تحليل فواتير واتساب
يستقبل نص فاتورة (أرقام عربية أو لاتينية، لهجة أو فصحى) ويستخرج: **اسم المورد، التاريخ، الإجمالي، الضريبة**، ثم يرسلها إلى جدول `invoice` ويُخرج تقرير Markdown.

```bash
python scripts/whatsapp_invoice_parser.py --demo                  # ثلاث فواتير نموذجية
python scripts/whatsapp_invoice_parser.py --text "المورد: … الإجمالي: 1150" --send
python scripts/whatsapp_invoice_parser.py --file invoices.txt --send --dedupe --save
type invoice.txt | python scripts/whatsapp_invoice_parser.py --stdin --send
```

- يشتق الضريبة من `الإجمالي − المجموع الفرعي` أو من نسبة الضريبة (15% افتراضيًا) ويتحقق من التناسق ويحذّر عند الاختلاف.
- `--dedupe` يحدّث فاتورة المورد نفسه في التاريخ نفسه بدل تكرارها.
- `--save` يحفظ التقرير في `reports/invoice_reports/`.

### `scripts/agents_swarm_core.py` — سرب الوكلاء
وكيل يجلب تحديثًا حيًّا من الإنترنت، ووكيل يكتبه في `task`، ودالة جاهزة لمزامنة القوالب.

```bash
python scripts/agents_swarm_core.py                                # مهمة واحدة إلى task
python scripts/agents_swarm_core.py --templates                    # + مزامنة القوالب
python scripts/agents_swarm_core.py --loop                         # حلقة مستمرة كل 60 دقيقة
python scripts/agents_swarm_core.py --loop --templates             # مع مزامنة القوالب كل دورة
python scripts/agents_swarm_core.py --loop --interval 15 --cycles 4 --log-file logs/swarm.log
```

- `--loop`: يبقى يعمل في الخلفية؛ كل دورة تجلب تحديثًا حيًّا وتكتبه في `task`، مع `--templates` تزامن القوالب أيضًا.
- `--interval` بالدقائق (افتراضي 60)، و`--cycles` لتحديد عدد الدورات ثم التوقف (0 = بلا حد).
- أي خطأ في دورة لا يُسقط الحلقة؛ يُسجَّل ويُنتظر للدورة التالية. `Ctrl+C` يوقفها بخروج نظيف.

### `scripts/prompt_pack_builder.py` — حزم أوامر AI خليجية
يولّد 6 حزم (3 لهجات × مجالين) وكل حزمة ملفها المستقل: `README.md` (صفحة المنتج)، `prompts.md`، `prompts.txt`، `pack.json`، و`zip` جاهز للبيع، مع كتالوج بحقول المتجر.

```bash
python scripts/prompt_pack_builder.py --zip                    # كل الحزم
python scripts/prompt_pack_builder.py --dialects saudi --domains realestate
python scripts/prompt_pack_builder.py --publish --dry-run      # معاينة الرفع لجدول template
python scripts/prompt_pack_builder.py --publish                # رفع الكتالوج فعليًا
```

المخرجات في `products/prompt_packs/`: `index.md` (فهرس بأسعار)، `catalog.csv` و`catalog.json` (بنفس حقول `template` فتصلح للرفع مباشرة).

### `scripts/scheduled_sync.py` — التشغيل الدوري
يشغّل مزامنة القوالب بلا تدخّل، ويكتب سجلًا يوميًا، ويسجّل مهمة Windows Task Scheduler.

```bash
python scripts/scheduled_sync.py --once                      # تشغيلة واحدة
python scripts/scheduled_sync.py --install --time 08:00      # مهمة يومية
python scripts/scheduled_sync.py --status                    # الحالة + آخر التشغيلات
python scripts/scheduled_sync.py --uninstall
```

- السجل اليومي: `logs/sync-YYYY-MM-DD.log`، والملخص التراكمي: `logs/history.csv`.
- قفل `logs/.sync.lock` يمنع التشغيل المتداخل، وأكواد الخروج: `0` نجاح، `1` فشل جزئي، `2` خطأ إعداد/اتصال، `3` تشغيل متداخل.
- على غير Windows يطبع الأمر المكافئ لـ `cron`.

---

## 4) دورة العمل المقترحة

```text
data/templates_ar.json  →  bubble_data_sync upsert  →  جدول template في Bubble  →  متجر القوالب
فواتير واتساب           →  whatsapp_invoice_parser  →  جدول invoice             →  تقرير Markdown
prompt_pack_builder    →  products/prompt_packs    →  جدول template             →  منتجات رقمية
scheduled_sync          →  كل ما سبق يوميًا 08:00   →  logs/history.csv
```

---

## 5) الأمان

- `.env` و`*.bak` و`logs/` و`reports/` مستثناة في `.gitignore` — **لا ترفع التوكن إلى GitHub**. تم فحص المستودع قبل أول كوميت للتأكد من عدم وجود أي توكن داخل الكود.
- السكربتات لا تطبع التوكن؛ تعرضه مقنّعًا مثل `4537…2c`.
- إن انكشف التوكن يومًا، أعد توليده من Bubble → Settings → API وحدّث `.env`.
- استخدم توكنًا بصلاحيات محدودة، وفعّل Privacy Rules بحيث لا يُسمح إلا بالعمليات التي تحتاجها.

---

## 6) الرفع إلى GitHub

```bash
cd arab-templates
git init
git add .
git status          # تأكد ألا يظهر scripts/.env ولا أي *.bak
git commit -m "Arab Templates: Bubble sync, invoice parser, prompt packs, scheduled runs"
git branch -M main
git remote add origin https://github.com/<اسم-حسابك>/<اسم-المستودع>.git
git push -u origin main
```

---

## 7) استكشاف الأخطاء

| الرسالة | السبب | الحل |
| --- | --- | --- |
| `HTTP 401 — Invalid or expired token` | التوكن غير صالح على هذا الفرع | جرّب `/version-test` أو أعد نشر إعدادات API ثم Deploy |
| `HTTP 404 — Type not found <type>` | اسم النوع غير مفعّل | فعّله في Settings → API وتأكد من الاسم |
| `HTTP 400 — Unrecognized field` | اسم حقل مختلف في Bubble | `python scripts/bubble_data_sync.py schema --type <type>` واستخدم الأسماء المطبوعة |
| `HTTP 400 — invalid appname` | نطاق التطبيق خاطئ في الرابط | صحّح `BUBBLE_APP_URL` |
| `تعذّر الوصول … بعد N محاولة` | شبكة أو جدار حماية | تحقق من الاتصال، وزِد `--retries` |
| `تشغيلة أخرى قيد التنفيذ` | قفل قديم | يُنظَّف تلقائيًا بعد 6 ساعات أو احذف `logs/.sync.lock` |

---

## 8) غير موجود في المستودع بعد

- **واجهة المتجر (HTML/CSS)**: صفحة عرض بطاقات القوالب وربطها بجدول `template` لم تُنشأ بعد؛ المكان المقترح `store/` مع خادم معاينة صغير يمرّر البيانات بدل كشف التوكن في المتصفح.
- **استقبال واتساب تلقائيًا**: التحليل يعمل على نص تُمرّره يدويًا أو من ملف؛ ربطه بـ WhatsApp Cloud API webhook خطوة تالية.

---

## المتجر والمعاينة (store/)

`store/index.html` واجهة متجر عربية (RTL) تعرض قوالب جدول `template` مع بحث وتصنيفات وبطاقات أسعار، و`scripts/store_server.py` خادم معاينة صغير (مكتبة بايثون القياسية فقط) يقدّم الصفحة ويُمرّر البيانات.

- **التوكن لا يصل إلى المتصفح إطلاقًا**: الصفحة تنادي `/api/templates` على نفس الأصل، والخادم هو من يتصل ببابل ويُرجع الحقول العامة فقط (العنوان، التصنيف، الوصف، السعر، رابط المعاينة). لا يخرج أي رأس مصادقة إلى العميل.
- استجابة بابل تُخزَّن 60 ثانية في الذاكرة، فلا يتكرر النداء لكل زائر.
- إن تعذّر الوصول إلى بابل يعرض الخادم نسخة من `data/templates_ar.json` ويعلن `source: "local"`.
- المسارات: `/` الصفحة · `/api/templates` البيانات · `/api/health` الحالة.

```bash
python scripts/store_server.py                 # http://127.0.0.1:8787
python scripts/store_server.py --port 9000 --open
python scripts/store_server.py --offline       # بلا اتصال ببابل
```

- لتفعيل زر «اطلب» ضع رابط واتساب أو الدفع في `ORDER_URL` أعلى سكربت `store/index.html`.
- الخادم للمعاينة المحلية على `127.0.0.1` فقط، وليس للنشر على الإنترنت: أي نشر حقيقي يحتاج استضافة تُشغّل Endpoint على الخادم يُبقي التوكن مخفيًا.


## نظام المحاسبة والامتثال الضريبي (gulf_tax_template_pro/)

المنتج الرئيسي لقالب الضرائب: صفحة عربية (RTL) واحدة تجمع أربع أدوات مترابطة:

1. **مولّد فواتير إلكترونية** برمز QR بصيغة ZATCA TLV — المرحلة الأولى (وهي نفس بنية FTA في الإمارات)، مع نسب تلقائية (السعودية ١٥٪، الإمارات وعُمان ٥٪، البحرين ١٠٪، قطر والكويت ٠٪)، بنود وخصومات، خيار «الأسعار تشمل الضريبة»، تجزئة SHA-256، ومعاينة طباعة A4.
2. **حاسبة صافي الإقرار**: ضريبة المبيعات المحصّلة − ضريبة المشتريات المدفوعة، مع رصيد دائن للترحيل، وموعد تقديم محسوب حسب الدولة.
3. **ماسح فواتير ذكي**: صورة (PNG/JPG/WEBP/PDF) أو نص واتساب/TXT/CSV، ثم مراجعة الحقول وإضافتها لسجل المشتريات.
4. **مساعد ضريبي وقناة محاسب**: دردشة بقواعد معرفة خليجية + تذاكر محفوظة برقم، مع الإبقاء على شريط العملات الحية وأخبار السوق.

```bash
python -m pip install flask segno     # segno اختيارية لصورة QR
python gulf_tax_template_pro/server.py               # http://127.0.0.1:5075
python gulf_tax_template_pro/server.py --port 5080 --open
```

- نقاط النهاية: `/api/countries`، `/api/einvoice`، `/api/ledger`، `/api/taxreturn`، `/api/ocr`، `/api/support`، إضافة إلى `/api/scan`، `/api/assistant`، `/api/news`، `/api/rates`، `/api/plans`، `/api/quota`، `/api/sample`، `/api/health`.
- التخزين: `reports/gulf/<account>.json` (مبيعات، مشتريات، رسائل) — بلا أسرار وبلا نص فاتورة خام.
- الحدود: OCR حقيقي يحتاج Tesseract (غير مثبت هنا، فالوضع محاكاة معلنة)؛ QR يحتاج `segno`؛ التوقيع الإلكتروني وختم المرحلة الثانية خارج النطاق؛ الرد من المحاسب آلي محلي.
- الدليل الكامل داخل المجلد: `gulf_tax_template_pro/README.md`.


## التشغيل السريع على ويندوز (START_ARAB_TEMPLATES.bat)

انقر نقرًا مزدوجًا على `START_ARAB_TEMPLATES.bat` في جذر المشروع، فيقوم بضغطة واحدة بـ:

1. حل مسار Python الحقيقي في الجهاز (اختصار متجر Windows ينتهي فورًا ويُفسد تتبّع المعرّفات).
2. تشغيل سرب الوكلاء في الخلفية: `agents_swarm_core.py --loop --templates` مع سجله في `logs/swarm_loop.log`.
3. تشغيل لوحة التحكم `admin_dashboard.py --port 5050` وفتحها في المتصفح مباشرة.
4. عدم تكرار الخدمات: يعتمد على `logs/swarm.pid` و`logs/dashboard.pid` وفحص منفذ 5050، ويطبع «يعمل بالفعل» عند إعادة النقر.
5. إبقاء الخدمتين بعد إغلاق النافذة (عمليات منفصلة DETACHED_PROCESS).

المنطق كاملًا في `scripts/start_services.py` والملف `.bat` غلاف رقيق. لتشغيلهما يدويًا:

```bash
python scripts/start_services.py --open
python scripts/start_services.py --no-swarm --port 5051
```

الإيقاف:

```bash
taskkill /PID $(cat logs/swarm.pid) /F
taskkill /PID $(cat logs/dashboard.pid) /F
```

## الترخيص

الاستخدام التجاري مسموح داخل مشروعك. حزم الأوامر المولّدة تُباع كمنتجات رقمية وفق شروط الحزمة نفسها (`prompt_packs/<slug>/README.md`).
