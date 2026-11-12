# Arab Templates — أدوات المحتوى والامتثال والأتمتة

مجموعة سكربتات بايثون عربية تشغّل منتجات متجر **Arab Templates**: مزامنة بيانات القوالب إلى Bubble، تحليل فواتير واتساب الواردة وإرسالها للسحابة، توليد حزم أوامر ذكاء اصطناعي باللهجات الخليجية، وتشغيل كل ذلك على جدولة يومية بسجلّات.

وبجانب السكربتات يحتوي المشروع على خمس واجهات جاهزة للتسليم: **متجر القوالب** (`store/`)، **نظام المحاسبة والامتثال الضريبي الخليجي** (`gulf_tax_template_pro/`)، **المساعد الذكي ثنائي اللغة** (`smart_bilingual_assistant/`)، و**قالبَين Premium** لحاسبة تسعير المناقصات ولوحة الأتمتة الدائرية للمصانع (`premium_bilingual_templates/`)، مع أدلة العملاء وبرنامج الموزعين.

كل الاتصالات تمر عبر **Bubble Data API** للتطبيق `at-ai-lab`، والتوكن يُقرأ محليًا من `.env` ولا يُحفظ في الكود ولا يُطبع في أي مخرَج.

---

## 1) بنية المشروع

```text
arab-templates/
├── README.md                     هذا الدليل
├── .gitignore                    يستثني .env و*.bak والسجلات والمخرجات
├── data/
│   ├── templates_ar.json         20 قالبًا عربيًا جاهزًا للمزامنة
│   ├── templates_bilingual.json  كتالوج الأفكار ثنائي اللغة (مولّد)
│   ├── store_meta.json           بيانات وصفية لكل منتج (أداة، قطاع، مشكلة، عائد)
│   └── market_news.json          أخبار الامتثال والضريبة المعروضة داخل القالب
├── scripts/
│   ├── bubble_data_sync.py       عميل Bubble Data API (الأساس لكل شيء)
│   ├── agents_swarm_core.py      الطيار الآلي: صيد أفكار + تعريب AR/EN + نشر + مراقبة
│   ├── scheduled_sync.py         تشغيل دوري + سجل يومي + Task Scheduler
│   ├── whatsapp_invoice_parser.py تحليل فواتير واردة + تقارير + إرسال
│   ├── prompt_pack_builder.py    توليد حزم أوامر AI باللهجات الخليجية
│   ├── store_server.py           خادم معاينة المتجر (يمرّر بيانات بابل بلا كشف التوكن)
│   └── start_services.py         تشغيل السرب ولوحة التحكم معًا (يستخدمه ملف .bat)
├── products/
│   └── prompt_packs/             (مولّد) الحزم + الكتالوج + ملفات zip
├── store/
│   ├── index.html                واجهة المتجر (بحث، تصنيفات، روابط معاينة)
│   └── reseller_and_affiliates.html  برنامج الموزعين والعمولة
├── gulf_tax_template_pro/        نظام المحاسبة والامتثال الضريبي (خادم + واجهة + OCR)
├── smart_bilingual_assistant/    المساعد الذكي ثنائي اللغة + خادم تسجيل الأسئلة
├── premium_bilingual_templates/  فهرس + قالبان Premium، كل صفحة ملف مستقل
├── customer_guides/              أدلة SMTP2GO والبدء السريع والموزعين
├── deploy/                        worker.js + (محلي) bubble_token.txt
├── admin_dashboard.py             لوحة تحكم محلية للمشروع والخدمات
├── START_ARAB_TEMPLATES.bat      تشغيل بنقرة: السرب + لوحة التحكم
├── logs/                          (محلي) سجلات التشغيل اليومية
└── reports/invoice_reports/       (محلي) تقارير الفواتير وبيانات المنتجات
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

### `scripts/agents_swarm_core.py` — الطيار الآلي الكامل (Full Autopilot)
ثلاثة وكلاء في نظام واحد يعمل بالعربية والإنجليزية: **وكيل الصيد والتعريب** (يجلب أفكار
القوالب الرائجة من GitHub وHacker News وبذور محلية، ويصوغ لكل فكرة عنوانًا ووصفًا
بالعربية والإنجليزية، ثم يرفعها إلى جدول `template` في `at-ai-lab`)، **وكيل المراقبة
والتعافي الذاتي** (فحص دوري لاتصال Bubble، إعادة محاولة بتراجع أسّي، وطابور محلي يُفرَّغ
تلقائيًا عند عودة الشبكة)، و**المجدول** (حلقة مستمرة أو مهمة في Windows Task Scheduler)،
مع تقرير أداء يُحدَّث كل دورة في `autopilot_report.json`.

```bash
python scripts/agents_swarm_core.py --once                         # دورة كاملة: صيد + تعريب + نشر
python scripts/agents_swarm_core.py --once --dry-run               # بلا كتابة في Bubble (الأفكار تُطابَر)
python scripts/agents_swarm_core.py --loop --interval 60           # تشغيل مستمر كل ساعة
python scripts/agents_swarm_core.py --check                        # فحص اتصال Bubble فقط
python scripts/agents_swarm_core.py --install --interval 60        # تفعيل مهمة مجدولة كل ساعة
python scripts/agents_swarm_core.py --install --daily 08:00        # أو مهمة يومية
python scripts/agents_swarm_core.py --status                       # حالة المهمة وآخر تقرير
python scripts/agents_swarm_core.py --uninstall                    # إزالة المهمة
python scripts/agents_swarm_core.py --once --lang en --ideas 3 --sources github,hn,local
```

- `--ideas` عدد الأفكار لكل دورة (0 = تعطيل الصيد)، و`--sources` من `github,hn,local`.
- `--lang ar|en|both` لغة السجلات (افتراضي `both`)، و`--log-file` يضيف ملف سجل.
- `--dry-run` لا يكتب في Bubble ويحفظ الأفكار في `data/autopilot_queue.json`، و`--offline` يمنع أي اتصال شبكي للاختبار.
- `--templates` يزامن القوالب العربية من `data/templates_ar.json` في الدورة نفسها.
- الحالة تُحفظ في `autopilot_report.json` (إجماليات، صحة الاتصال، متوسط زمن الاستجابة، آخر 20 دورة)، والكتالوج ثنائي اللغة للأفكار في `data/templates_bilingual.json`.
- المهمة المجدولة تعمل عبر `scripts/autopilot_task.bat` (يُولَّد تلقائيًا بمسارات مطلقة) وسجلها `logs/autopilot_task.log`؛ قفل `logs/.autopilot.lock` يمنع تشغيلين متداخلين.
- جدول `template` في Bubble يحتوي الحقول الخمسة الأساسية فقط، لذا تُرفع النسخة العربية إليه وتُحفظ النسخة الإنجليزية كاملة في الكتالوج المحلي (وأي حقول `Title_EN`/`Description_EN` تُضاف لاحقًا تُرفع تلقائيًا إن وُجدت).

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
git remote add origin https://github.com/maher2018/maher-arab-templates.git
# أو إن كان الريموت موجودًا مسبقًا:
git remote set-url origin https://github.com/maher2018/maher-arab-templates.git
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

- **استقبال واتساب تلقائيًا**: التحليل يعمل على نص تُمرّره يدويًا أو من ملف؛ ربطه بـ WhatsApp Cloud API webhook خطوة تالية.
- **توقيع الفاتورة — المرحلة الثانية (ZATCA/FTA)**: التوقيع الإلكتروني والختم خارج النطاق الحالي.

> واجهة المتجر صارت موجودة في `store/` مع خادم المعاينة `scripts/store_server.py` — راجع القسم التالي.

---

## المتجر والمعاينة (store/)

`store/index.html` واجهة متجر عربية (RTL) تعرض قوالب جدول `template` مع بحث وتصنيفات وبطاقات أسعار، و`scripts/store_server.py` خادم معاينة صغير (مكتبة بايثون القياسية فقط) يقدّم الصفحة ويُمرّر البيانات.

- **التوكن لا يصل إلى المتصفح إطلاقًا**: الصفحة تنادي `/api/templates` على نفس الأصل، والخادم هو من يتصل ببابل ويُرجع الحقول العامة فقط (العنوان، التصنيف، الوصف، السعر، رابط المعاينة). لا يخرج أي رأس مصادقة إلى العميل.
- استجابة بابل تُخزَّن 60 ثانية في الذاكرة، فلا يتكرر النداء لكل زائر.
- إن تعذّر الوصول إلى بابل يعرض الخادم نسخة من `data/templates_ar.json` ويعلن `source: "local"`.
- المسارات: `/` الصفحة · `/api/templates` البيانات · `/api/health` الحالة · `/api/template?id=` منتج واحد.
- **روابط اقتراح المساعد**: `store/index.html?q=<كلمة>&cat=<فئة>&from=assistant` يملأ البحث والفئة تلقائيًا، ويعرض شريط «اقتراح المساعد الذكي» مع زر معاينة، ويبرز البطاقة المطابقة ويتمرّر إليها، مع زر «عرض كل القوالب» لتنظيف الفلترة.

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
- **البريد عبر SMTP2GO**: قسم إعدادات ثنائي اللغة في الواجهة (حالة الربط، المُرسل، Reply-To، زر تسجيل سريع برابط `SMTP2GO_AFFILIATE_LINK`)، وإرسال الفاتورة بالبريد عبر `POST /api/email/send` بمفتاح `SMTP2GO_API_KEY` من الخادم فقط.
- الدليل الكامل داخل المجلد: `gulf_tax_template_pro/README.md`، ودليل خطوات ربط البريد: `customer_guides/smtp2go_email_setup.md`.

## المساعد الذكي ثنائي اللغة (smart_bilingual_assistant/)

مساعد محادثة عربي/إنجليزي يعمل بلا مكتبات خارجية، ويجيب من قاعدة معرفة محلية فقط:

- **قاعدة معرفة ومطابقة**: `core.js` يوحّد الألف والتاء المربوطة والهمزات، ويستخدم أوزان عبارات وعتبة 4.5 درجة، ويكشف الدولة من السؤال ثم يقدّم إجابة مخصّصة لها (نسب الضريبة، حد التسجيل، مواعيد الإقرار، حقول الفاتورة) — وما دون العتبة يعيد «لم أجد جوابًا» بدل تخمين.
- **أداة تدقيق القيود**: تتحقق من `الصافي × النسبة = الضريبة` و`الصافي + الضريبة = الإجمالي` وصيغة الرقم الضريبي لكل دولة، وتضيف فحص **العملة** مقابل العملة القانونية للدولة، وفحص **الفترة الضريبية** (شهر `YYYY-MM`) مقابل تاريخ الفاتورة، ثم تعرض نسبة نجاح وقائمة فحوص والقيد المحاسبي المقترح.
- **تدقيق بنود نصية**: لصق بند لكل سطر `الوصف | الكمية | السعر | الخصم% | الإجمالي المسجّل (اختياري)`، ويُحسب لكل بند الصافي والضريبة والإجمالي ويُوسم المخالف (كمية صفر، سعر سالب، خصم خارج 0–100، إجمالي لا يطابق المحسوب)، ثم يجمع ويقارن بمجاميع الفاتورة.
- **توصية قالب + ربط بالمتجر**: أسئلة النشاط والأولوية تنتهي بتوصية من كتالوج القوالب، مع زر **«افتح القالب المقترح في المتجر»** يفتح `store/index.html?from=assistant&q=…&cat=…`، فيطبّق المتجر البحث والفئة ويعرض شريط اقتراح ويبرز البطاقة المطابقة. يُضبط عنوان المتجر من `STORE_BASE` أعلى `app.js`.
- **خادم تسجيل الأسئلة غير المجابة**: `server.py` يقدّم الملفات ويسجّل كل سؤال بلا مطابقة في `logs/unanswered.jsonl` (مستثنى من git)، مع `GET /api/unanswered` لملخّص الثغرات و`POST /api/unanswered/clear` بعد تحديث القاعدة.
- **اختبارات المطابقة**: `tests.html` يشغّل 40 حالة عربية فصحى وخليجية وإنجليزية (كلها ناجحة) للتأكد من الفهم ومن أن الأسئلة خارج النطاق تُعيد «لا أعرف».

```bash
python smart_bilingual_assistant/server.py --port 5083   # الصفحة + تسجيل الأسئلة
# ثم افتح http://127.0.0.1:5083/  وللملخّص: /api/unanswered
```

الدليل الكامل: `smart_bilingual_assistant/README.md`.

## قوالب Premium ثنائية اللغة (premium_bilingual_templates/)

قالبان تفاعليان، كل واحد **ملف HTML واحد مستقل** (CSS و JavaScript مدمجان، بلا أي مكتبة خارجية أو خادم) يعمل بفتحه مباشرة، مع تبديل فوري عربي/إنجليزي واتجاه RTL/LTR، وسبع عملات (SAR, AED, KWD, QAR, OMR, BHD, USD) بكسور عشرية صحيحة، وحفظ تلقائي في `localStorage`.

| الملف | الاستخدام | أبرز الحسابات |
| --- | --- | --- |
| `tender_cost_estimator.html` | حاسبة تسعير المشاريع والمناقصات للمقاولين | مواد خام + عمالة، مصاريف إدارية، احتياطي طوارئ، هامش ربح صافٍ على سعر البيع مع ما يعادله Markup، ضريبة تلقائية حسب العملة، عرض سعر جاهز للطباعة |
| `factory_circular_ops.html` | لوحة إدارة خطوط الإنتاج والمخلفات للمصانع | مخلفات كل خط (كجم)، نسبة القابل للتدوير، كفاءة التحويل، المسترجَع والمفقود، القيمة المضافة وتوفير التخلص، رسم الدورة الدائرية، تقرير كفاءة يومي للمديرين والمشرفين قابل للنسخ والطباعة مقابل هدف استرجاع |
| `index.html` | فهرس المجموعة: يربط القالبين ويصف كل واحد بالعربية والإنجليزية | بطاقتان بملخص الميزات والوسوم وزرّي فتح + روابط مباشرة إلى عرض السعر وتقرير الكفاءة، مع تبديل لغة فوري |

```bash
# لا يحتاج تشغيلًا: افتح الملف مباشرة، أو عبر
python -m http.server 5084 --directory premium_bilingual_templates
# ثم: http://127.0.0.1:5084/index.html
```

## برنامج الموزعين والشركاء (store/reseller_and_affiliates.html)

صفحة مستقلة ثنائية اللغة (عربي/إنجليزي مع تبديل فوري واتجاه RTL/LTR) تعرض مسارَي البيع:

- **باقة الموزعين للمكاتب المحاسبية**: ترخيص سنوي 9,900 ر.س، هوية بيضاء، 10 مقاعد، 250 ملف عميل، 50,000 فاتورة مسح سنويًا، تدريب ودعم أولوية، وهامش جملة يصل إلى 40%.
- **التسويق بالعمولة المتكررة 25%**: عمولة على كل دفعة اشتراك لمدة 12 شهرًا لكل عميل، تتبّع 60 يومًا، كود خصم 10% للعميل، ودفعات شهرية بعد 300 ر.س.
- تشمل: جدول أرباح تقديري، خطوات الانضمام، أسئلة شائعة، ونموذج تقديم يجهّز رسالة بريد جاهزة (لا يرسل بيانات إلى أي خادم).

افتح الملف مباشرة في المتصفح أو عبر `python -m http.server` داخل `store/`.

## أدلة العملاء (customer_guides/)

مركز الأدلة القصيرة التي تُسلَّم مع المنتج: `smtp2go_email_setup.md` (ربط البريد خطوة بخطوة، مفتاح الـAPI، الاختبار، واستكشاف الأخطاء)، `gulf_tax_quickstart.md` (البدء السريع والفاتورة الأولى)، و`reseller_program.md` (المسارَان والعمولة والدفعات). الفهرس في `customer_guides/README.md`.


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
