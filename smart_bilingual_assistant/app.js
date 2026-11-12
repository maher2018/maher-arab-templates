/* المساعد الذكي الرسمي لمنصة Arab Templates — عربي/إنجليزي، بلا مكتبات خارجية */
const $ = (id) => document.getElementById(id);
const state = { lang: "ar", flow: null, audit: null };

/* ============================ الترجمة ============================ */
const I18N = {
  ar: {
    "page.title": "المساعد الذكي — Arab Templates",
    "brand.name": "المساعد الذكي", "brand.sub": "Arab Templates · Smart Assistant",
    "nav.chat": "المحادثة", "nav.catalog": "القوالب", "nav.audit": "تدقيق القيود", "nav.topics": "مواضيع ضريبية",
    "status.local": "يعمل محليًا بلا إنترنت",
    "hero.badge": "مساعد رسمي · عربي / English",
    "hero.title": "اسأل عن القوالب أو الضريبة — واحصل على جواب واضح فورًا",
    "hero.sub": "يدعم الزوار والموظفين في اختيار القالب المناسب وشرح خطوات الاستخدام، ويجيب عن استفسارات ضريبة القيمة المضافة في السعودية والإمارات ودول الخليج، ويساعد المحاسبين في تدقيق قيود الفواتير.",
    "hero.cta.recommend": "اختر لي القالب المناسب", "hero.cta.audit": "افتح أداة تدقيق الفواتير",
    "chat.title": "المحادثة", "chat.tag": "قواعد معرفة خليجية · بلا إرسال بيانات",
    "chat.greeting": "أهلًا بك! أنا المساعد الذكي لمنصة Arab Templates. أستطيع اختيار قالب يناسب نشاطك، شرح خطوات استخدامه، والإجابة عن أسئلتك الضريبية والمحاسبية.",
    "chat.placeholder": "اكتب سؤالك… مثال: ما نسبة الضريبة في عُمان؟", "chat.send": "إرسال",
    "chat.fine": "المساعد يعمل بقواعد معرفة مكتوبة وواضحة داخل الصفحة، وليس استشارة ضريبية معتمدة.",
    "side.quick": "أسئلة سريعة", "side.guide": "دليل سريع", "side.guide.tag": "٣ خطوات",
    "side.step1": "اختر نشاطك من زر «اختر لي القالب المناسب».",
    "side.step2": "اسأل عن النسبة أو الموعد أو حقول الفاتورة في أي وقت.",
    "side.step3": "راجع قيودك في أداة التدقيق قبل الترحيل.",
    "topics.title": "مواضيع ضريبية ومحاسبية", "topics.tag": "السعودية · الإمارات · الخليج",
    "topics.sub": "اضغط أي موضوع ليُطرح على المساعد ويظهر الجواب كاملًا داخل المحادثة.",
    "catalog.title": "قوالب Arab Templates", "catalog.tag": "جاهزة للتخصيص",
    "catalog.sub": "يقترح المساعد أحد هذه القوالب حسب نشاطك، ويعرض خطوات استخدامه باللغتين.",
    "audit.title": "تدقيق قيود الفواتير", "audit.tag": "تحقق فوري من الحساب والرقم الضريبي",
    "audit.sub": "أدخل بيانات الفاتورة كما سُجّلت في القيد، وستحصل على قائمة تحقق واضحة والقيد المحاسبي المقترح.",
    "audit.country": "الدولة", "audit.taxno": "الرقم الضريبي للمورد", "audit.date": "تاريخ الفاتورة",
    "audit.net": "المبلغ قبل الضريبة", "audit.vat": "مبلغ الضريبة المسجّل", "audit.total": "إجمالي الفاتورة المسجّل",
    "audit.run": "دقّق الفاتورة", "audit.sample": "مثال تعبئة", "audit.clear": "تفريغ",
    "audit.verdict": "—", "audit.journal.title": "القيد المحاسبي المقترح",
    "country.SA": "السعودية — 15%", "country.AE": "الإمارات — 5%", "country.OM": "عُمان — 5%",
    "country.BH": "البحرين — 10%", "country.QA": "قطر — 0%", "country.KW": "الكويت — 0%",
    "footer.product": "Arab Templates — المساعد الذكي الرسمي",
    "footer.disclaimer": "معلومات إرشادية وليست استشارة ضريبية أو قانونية معتمدة.",
    "chip.rates": "نسب الضريبة", "chip.deadline": "مواعيد الإقرار", "chip.fields": "حقول الفاتورة",
    "chip.recommend": "اختر لي قالبًا", "chip.audit": "كيف أدقق القيد؟",
    "chip.q.rates": "ما نسبة ضريبة القيمة المضافة في السعودية والإمارات ودول الخليج؟",
    "chip.q.deadline": "ما آخر موعد لتقديم الإقرار الضريبي؟",
    "chip.q.fields": "ما الحقول المطلوبة في الفاتورة الضريبية؟",
    "chip.q.audit": "كيف أدقق قيود فواتير المبيعات والمشتريات؟",
    "quick.vat": "نسب الضريبة الخليجية", "quick.threshold": "حدود التسجيل الإلزامي",
    "quick.deadline": "مواعيد الإقرار", "quick.audit": "تدقيق القيد المحاسبي",
    "quick.template": "أي قالب يناسب مكتب محاسبة؟",
    "topic.rates": "نسب ضريبة القيمة المضافة", "topic.rates.sub": "١٥٪ السعودية · ٥٪ الإمارات وعُمان · ١٠٪ البحرين · ٠٪ قطر والكويت",
    "topic.threshold": "حدود التسجيل", "topic.threshold.sub": "متى تصبح المنشأة ملزمة بالتسجيل؟",
    "topic.deadline": "مواعيد الإقرار", "topic.deadline.sub": "شهري أم ربع سنوي، ومتى آخر يوم؟",
    "topic.einvoice": "الفوترة الإلكترونية", "topic.einvoice.sub": "المرحلة الأولى والثانية ورمز QR",
    "topic.fields": "حقول الفاتورة", "topic.fields.sub": "ما الذي يجب أن تحتويه الفاتورة الضريبية؟",
    "topic.input": "خصم ضريبة المشتريات", "topic.input.sub": "شروط اعتماد ضريبة المدخلات",
    "topic.zero": "المعفاة والصفرية", "topic.zero.sub": "الفرق بين 0% والمعفاة",
    "topic.penalty": "الغرامات", "topic.penalty.sub": "أشهر أسباب الغرامات وكيف تتجنبها",
    "topic.journal": "قيود الفواتير", "topic.journal.sub": "القيد الصحيح للمبيعات والمشتريات",
    "catalog.ask": "خطوات الاستخدام", "catalog.recommend": "هل يناسبني؟",
    "flow.activity": "ما نوع نشاطك؟", "flow.priority": "وما أهم ما تحتاجه الآن؟",
    "flow.choose": "اختر أحد الخيارات من الأزرار بالأسفل.",
    "act.ecommerce": "تجارة إلكترونية أو متجر", "act.services": "خدمات واستشارات", "act.accounting": "مكتب محاسبة",
    "act.education": "تعليم وتدريب", "act.personal": "موقع شخصي أو أعمال", "act.other": "نشاط آخر",
    "prio.invoicing": "فواتير وضريبة", "prio.crm": "متابعة عملاء", "prio.booking": "حجز مواعيد",
    "prio.learning": "محتوى تعليمي", "prio.showcase": "عرض أعمال",
    "recommend.done": "التوصية المناسبة لك: {name}",
    "recommend.why": "السبب: {reason}",
    "recommend.steps": "خطوات الاستخدام:",
    "recommend.reset": "اختر من جديد",
    "audit.sample.done": "تم تعبئة مثال سعودي — اضغط «دقّق الفاتورة».",
    "audit.cleared": "تم تفريغ الحقول.",
    "audit.score": "{passed} من {total} فحوصًا ناجحة",
    "audit.pass": "سليم", "audit.fail": "تحتاج تصحيحًا", "audit.warn": "ملاحظة",
    "audit.v.ok": "القيود متوازنة وسليمة",
    "audit.v.warn": "سليمة مع ملاحظات بسيطة",
    "audit.v.bad": "تحتاج تصحيحًا قبل الترحيل",
    "audit.net.valid": "المبلغ قبل الضريبة صالح",
    "audit.net.invalid": "أدخل مبلغًا قبل الضريبة أكبر من صفر",
    "audit.vat.valid": "مبلغ الضريبة صالح",
    "audit.vat.negative": "مبلغ الضريبة لا يكون سالبًا",
    "audit.vat.mismatch": "الضريبة المسجّلة {actual} تختلف عن المتوقّعة {expected}",
    "audit.vat.zero": "هذه الدولة بلا ضريبة قيمة مضافة حاليًا — يجب أن تكون الضريبة صفرًا",
    "audit.total.mismatch": "الإجمالي المسجّل {actual} لا يساوي (الصافي + الضريبة) = {expected}",
    "audit.total.valid": "إجمالي الفاتورة مطابق للمجاميع",
    "audit.taxno.valid": "الرقم الضريبي بالصيغة الصحيحة ({hint})",
    "audit.taxno.invalid": "الرقم الضريبي غير مطابق لصيغة الدولة ({hint})",
    "audit.date.future": "تاريخ الفاتورة في المستقبل — راجع التاريخ",
    "audit.date.valid": "تاريخ الفاتورة سليم",
    "audit.rate.valid": "نسبة الضريبة المطبقة مطابقة لنسبة الدولة ({rate}%)",
    "audit.suggest": "التصحيح المقترح: الضريبة {vat} والإجمالي {total}.",
    "audit.journal.net": "مبيعات / إيرادات", "audit.journal.vat": "ضريبة القيمة المضافة المستحقة",
    "audit.journal.total": "ذمم العملاء / النقدية",
    "audit.journal.debit": "مدين", "audit.journal.credit": "دائن", "audit.journal.account": "الحساب",
    "audit.journal.note": "قيود المبيعات: يُحمَّل حساب العملاء بالإجمالي، ويُقيد الإيراد بالصافي، وتُقيد الضريبة المستحقة بالفرق. للفواتير المعفاة أو الصفرية لا يوجد سطر ضريبة.",
    "audit.journal.note.adjust": "للتصحيح: الضريبة {vat} والإجمالي {total}.",
    "msg.steps": "خطوات استخدام {name}:",
    "msg.notfound": "لم أجد جوابًا دقيقًا لهذا السؤال. جرّب أحد هذه المواضيع:",
  },
  en: {
    "page.title": "Smart Assistant — Arab Templates",
    "brand.name": "Smart Assistant", "brand.sub": "Arab Templates · Smart Assistant",
    "nav.chat": "Chat", "nav.catalog": "Templates", "nav.audit": "Entry check", "nav.topics": "Tax topics",
    "status.local": "Runs locally, no internet",
    "hero.badge": "Official assistant · عربي / English",
    "hero.title": "Ask about templates or tax — get a clear answer instantly",
    "hero.sub": "Helps visitors and staff pick the right template and understand its setup steps, answers Gulf VAT questions for Saudi Arabia, the UAE and the wider region, and helps accountants audit invoice entries.",
    "hero.cta.recommend": "Recommend a template", "hero.cta.audit": "Open the invoice audit tool",
    "chat.title": "Chat", "chat.tag": "Gulf knowledge base · nothing leaves the page",
    "chat.greeting": "Welcome! I am the official Arab Templates assistant. I can pick a template for your business, explain its setup steps, and answer your tax and accounting questions.",
    "chat.placeholder": "Type your question… e.g. What is the VAT rate in Oman?", "chat.send": "Send",
    "chat.fine": "The assistant answers from a written knowledge base in this page — it is not certified tax advice.",
    "side.quick": "Quick questions", "side.guide": "Quick guide", "side.guide.tag": "3 steps",
    "side.step1": "Choose your activity with the “Recommend a template” button.",
    "side.step2": "Ask about rates, deadlines or invoice fields at any time.",
    "side.step3": "Check your entries in the audit tool before posting.",
    "topics.title": "Tax and accounting topics", "topics.tag": "Saudi Arabia · UAE · Gulf",
    "topics.sub": "Click any topic to ask the assistant; the full answer appears in the chat.",
    "catalog.title": "Arab Templates catalogue", "catalog.tag": "Ready to customise",
    "catalog.sub": "The assistant suggests one of these based on your activity and shows its setup steps in both languages.",
    "audit.title": "Invoice entry audit", "audit.tag": "Instant arithmetic and tax number checks",
    "audit.sub": "Enter the invoice as it was posted, and get a clear checklist plus the suggested journal entry.",
    "audit.country": "Country", "audit.taxno": "Supplier tax number", "audit.date": "Invoice date",
    "audit.net": "Amount before VAT", "audit.vat": "Recorded VAT amount", "audit.total": "Recorded invoice total",
    "audit.run": "Audit invoice", "audit.sample": "Fill sample", "audit.clear": "Clear",
    "audit.verdict": "—", "audit.journal.title": "Suggested journal entry",
    "country.SA": "Saudi Arabia — 15%", "country.AE": "United Arab Emirates — 5%", "country.OM": "Oman — 5%",
    "country.BH": "Bahrain — 10%", "country.QA": "Qatar — 0%", "country.KW": "Kuwait — 0%",
    "footer.product": "Arab Templates — official smart assistant",
    "footer.disclaimer": "Guidance only — not certified tax or legal advice.",
    "chip.rates": "VAT rates", "chip.deadline": "Filing deadlines", "chip.fields": "Invoice fields",
    "chip.recommend": "Recommend a template", "chip.audit": "How do I audit an entry?",
    "chip.q.rates": "What are the VAT rates in Saudi Arabia, the UAE and the Gulf?",
    "chip.q.deadline": "When is the VAT return due?",
    "chip.q.fields": "Which fields are required on a tax invoice?",
    "chip.q.audit": "How do I audit sales and purchase invoice entries?",
    "quick.vat": "Gulf VAT rates", "quick.threshold": "Mandatory registration thresholds",
    "quick.deadline": "Filing deadlines", "quick.audit": "Audit the journal entry",
    "quick.template": "Which template suits an accounting office?",
    "topic.rates": "VAT rates", "topic.rates.sub": "15% Saudi Arabia · 5% UAE and Oman · 10% Bahrain · 0% Qatar and Kuwait",
    "topic.threshold": "Registration thresholds", "topic.threshold.sub": "When must a business register?",
    "topic.deadline": "Filing deadlines", "topic.deadline.sub": "Monthly or quarterly — and which day?",
    "topic.einvoice": "E-invoicing", "topic.einvoice.sub": "Phase one, phase two and the QR code",
    "topic.fields": "Invoice fields", "topic.fields.sub": "What must a tax invoice contain?",
    "topic.input": "Input VAT deduction", "topic.input.sub": "Conditions for deducting purchase VAT",
    "topic.zero": "Zero-rated vs exempt", "topic.zero.sub": "What the difference means",
    "topic.penalty": "Penalties", "topic.penalty.sub": "Common causes and how to avoid them",
    "topic.journal": "Invoice entries", "topic.journal.sub": "Correct entries for sales and purchases",
    "catalog.ask": "Setup steps", "catalog.recommend": "Is it right for me?",
    "flow.activity": "What kind of business do you run?", "flow.priority": "And what do you need most right now?",
    "flow.choose": "Pick one of the options below.",
    "act.ecommerce": "E-commerce or a store", "act.services": "Services and consulting", "act.accounting": "Accounting office",
    "act.education": "Education and training", "act.personal": "Personal site or portfolio", "act.other": "Something else",
    "prio.invoicing": "Invoices and VAT", "prio.crm": "Customer follow-up", "prio.booking": "Appointments",
    "prio.learning": "Learning content", "prio.showcase": "Showcase work",
    "recommend.done": "Best match for you: {name}",
    "recommend.why": "Why: {reason}",
    "recommend.steps": "Setup steps:",
    "recommend.reset": "Start over",
    "audit.sample.done": "A Saudi sample is filled in — press “Audit invoice”.",
    "audit.cleared": "Fields cleared.",
    "audit.score": "{passed} of {total} checks passed",
    "audit.pass": "Pass", "audit.fail": "Needs correction", "audit.warn": "Note",
    "audit.v.ok": "Entries are balanced and correct",
    "audit.v.warn": "Correct with minor notes",
    "audit.v.bad": "Needs correction before posting",
    "audit.net.valid": "The pre-VAT amount is valid",
    "audit.net.invalid": "Enter a pre-VAT amount greater than zero",
    "audit.vat.valid": "The recorded VAT amount is valid",
    "audit.vat.negative": "VAT cannot be negative",
    "audit.vat.mismatch": "Recorded VAT {actual} differs from the expected {expected}",
    "audit.vat.zero": "This country has no VAT yet — VAT must be zero",
    "audit.total.mismatch": "Recorded total {actual} does not equal (net + VAT) = {expected}",
    "audit.total.valid": "Invoice total matches the components",
    "audit.taxno.valid": "Tax number matches the country format ({hint})",
    "audit.taxno.invalid": "Tax number does not match the country format ({hint})",
    "audit.date.future": "Invoice date is in the future — review it",
    "audit.date.valid": "Invoice date is valid",
    "audit.rate.valid": "Applied VAT rate matches the country rate ({rate}%)",
    "audit.suggest": "Suggested fix: VAT {vat} and total {total}.",
    "audit.journal.net": "Sales / revenue", "audit.journal.vat": "VAT payable",
    "audit.journal.total": "Accounts receivable / cash",
    "audit.journal.debit": "Debit", "audit.journal.credit": "Credit", "audit.journal.account": "Account",
    "audit.journal.note": "Sales entry: debit receivables with the total, credit revenue with the net, and credit VAT payable with the difference. Zero-rated or exempt invoices have no VAT line.",
    "audit.journal.note.adjust": "Suggested correction: VAT {vat} and total {total}.",
    "msg.steps": "How to use {name}:",
    "msg.notfound": "I could not find an exact answer. Try one of these topics:",
  },
};

function t(key, vars) {
  const dict = I18N[state.lang] || I18N.ar;
  let text = dict[key] ?? I18N.ar[key] ?? key;
  if (vars) text = text.replace(/\{(\w+)\}/g, (m, k) => (vars[k] === undefined || vars[k] === null ? m : vars[k]));
  return text;
}

const l = (ar, en) => (state.lang === "en" ? en : ar);
const fmt = (n, d = 2) => new Intl.NumberFormat(state.lang === "en" ? "en-US" : "ar-SA",
  { minimumFractionDigits: d, maximumFractionDigits: d }).format(Number(n) || 0);

/* ============================ البيانات ============================ */
const COUNTRIES = {
  SA: { rate: 15, currency: "SAR", regex: /^\d{15}$/, hintAr: "١٥ رقمًا", hintEn: "15 digits" },
  AE: { rate: 5, currency: "AED", regex: /^\d{15}$/, hintAr: "١٥ رقمًا (TRN)", hintEn: "15 digits (TRN)" },
  OM: { rate: 5, currency: "OMR", regex: /^[A-Za-z0-9]{5,20}$/, hintAr: "٥ إلى ٢٠ حرفًا أو رقمًا", hintEn: "5–20 letters or digits" },
  BH: { rate: 10, currency: "BHD", regex: /^\d{10,15}$/, hintAr: "١٠ إلى ١٥ رقمًا", hintEn: "10–15 digits" },
  QA: { rate: 0, currency: "QAR", regex: /^[A-Za-z0-9]{5,20}$/, hintAr: "رقم تسجيل ضريبي", hintEn: "tax registration number" },
  KW: { rate: 0, currency: "KWD", regex: /^[A-Za-z0-9]{5,20}$/, hintAr: "رقم تسجيل ضريبي", hintEn: "tax registration number" },
};

const TEMPLATES = [
  {
    id: "gulf", name: { ar: "نظام المحاسبة والامتثال الضريبي الخليجي", en: "Gulf tax & accounting suite" },
    kicker: { ar: "فواتير · إقرار · مسح", en: "Invoices · VAT return · scanning" },
    best: { ar: "مكاتب المحاسبة والشركات التي تصدر فواتير ضريبية في الخليج.", en: "Accounting offices and Gulf businesses issuing tax invoices." },
    tags: ["accounting", "invoicing", "services", "ecommerce"],
    steps: {
      ar: ["شغّل الخادم: python gulf_tax_template_pro/server.py --port 5075", "اختر الدولة والعملة واللغة من نافذة الإعدادات الأولى", "أصدر فاتورة برمز QR ثم احفظها، وتابع الإقرار في تبويب الإقرار"],
      en: ["Start the server: python gulf_tax_template_pro/server.py --port 5075", "Pick country, currency and language in the first-run setup", "Issue an invoice with its QR code, save it, then track the return in the return tab"],
    },
    link: "../gulf_tax_template_pro/index.html",
  },
  {
    id: "store", name: { ar: "متجر القوالب الرقمي", en: "Digital templates store" },
    kicker: { ar: "متجر · بحث وتصنيفات", en: "Storefront · search and categories" },
    best: { ar: "من يبيع قوالب أو منتجات رقمية ويحتاج واجهة عرض عربية سريعة.", en: "Anyone selling templates or digital products who needs a fast Arabic storefront." },
    tags: ["ecommerce", "showcase", "personal"],
    steps: {
      ar: ["شغّل خادم المتجر: python scripts/store_server.py", "اضبط ORDER_URL في أعلى store/index.html لرابط الطلب", "أضف القوالب من لوحة بابل أو من الملف المحلي وستظهر تلقائيًا"],
      en: ["Run the store server: python scripts/store_server.py", "Set ORDER_URL at the top of store/index.html", "Add templates from Bubble or the local file — they appear automatically"],
    },
    link: "../store/index.html",
  },
  {
    id: "crm", name: { ar: "لوحة متابعة العملاء (CRM)", en: "Customer follow-up dashboard (CRM)" },
    kicker: { ar: "عملاء · مهام · تقارير", en: "Customers · tasks · reports" },
    best: { ar: "فرق المبيعات والخدمات التي تتابع عملاءها يدويًا في الجداول.", en: "Sales and service teams still tracking customers in spreadsheets." },
    tags: ["crm", "services", "accounting"],
    steps: {
      ar: ["استورد قائمة العملاء الحالية (CSV)", "حدّد مراحل البيع ومسؤول كل عميل", "راقب المهام المتأخرة من اللوحة أسبوعيًا"],
      en: ["Import your current customer list (CSV)", "Define pipeline stages and an owner per customer", "Review overdue tasks weekly from the dashboard"],
    },
  },
  {
    id: "booking", name: { ar: "نظام حجز المواعيد", en: "Appointment booking system" },
    kicker: { ar: "مواعيد · تذكيرات", en: "Slots · reminders" },
    best: { ar: "العيادات والمكاتب التي تحجز مواعيدها عبر واتساب يدويًا.", en: "Clinics and offices booking appointments manually over WhatsApp." },
    tags: ["booking", "services"],
    steps: {
      ar: ["حدّد ساعات العمل ومدة الموعد", "أضف الخدمات وأسماء الفريق", "شارك رابط الحجز مع العملاء وفعّل التذكيرات"],
      en: ["Set working hours and slot length", "Add services and team members", "Share the booking link and enable reminders"],
    },
  },
  {
    id: "edu", name: { ar: "بطاقات تعليمية تفاعلية", en: "Interactive study flashcards" },
    kicker: { ar: "تعليم · مراجعة", en: "Learning · revision" },
    best: { ar: "المدربين والطلاب الذين يحتاجون مراجعة سريعة باللغتين.", en: "Trainers and students who need quick bilingual revision." },
    tags: ["education", "learning"],
    steps: {
      ar: ["أضف البطاقات (سؤال/جواب) أو استوردها", "نظّمها في مجموعات حسب الموضوع", "استخدم وضع المراجعة السريع قبل الاختبار"],
      en: ["Add question/answer cards or import them", "Group them by topic", "Use quick review mode before the exam"],
    },
  },
  {
    id: "portfolio", name: { ar: "موقع أعمال شخصي", en: "Personal portfolio site" },
    kicker: { ar: "أعمال · سيرة · تواصل", en: "Work · bio · contact" },
    best: { ar: "المستقلين والمصممين الذين يعرضون أعمالهم لجمهور عربي.", en: "Freelancers and designers showcasing work to an Arabic audience." },
    tags: ["personal", "showcase"],
    steps: {
      ar: ["بدّل العنوان والاسم والنبذة", "أضف ٣ إلى ٦ أعمال بصور حقيقية", "اربط نموذج التواصل ببريدك أو واتساب"],
      en: ["Replace the headline, name and bio", "Add 3–6 projects with real images", "Connect the contact form to your email or WhatsApp"],
    },
  },
  {
    id: "ai", name: { ar: "مساعد ذكي مخصص", en: "Custom AI assistant" },
    kicker: { ar: "دردشة · قاعدة معرفة", en: "Chat · knowledge base" },
    best: { ar: "المنصات التي تريد مساعدًا يجيب من محتواها الخاص فقط.", en: "Platforms that want an assistant answering only from their own content." },
    tags: ["services", "learning", "accounting"],
    steps: {
      ar: ["اجمع الأسئلة والأجوبة الشائعة في ملف معرفة", "اربط المساعد بالصفحة أو الويدجت", "راجع الأسئلة غير المجابة أسبوعيًا وأضفها"],
      en: ["Collect FAQs into a knowledge file", "Embed the assistant on the page or widget", "Review unanswered questions weekly and add them"],
    },
  },
  {
    id: "email", name: { ar: "حملة بريدية عربية", en: "Arabic email campaign" },
    kicker: { ar: "بريد · تتبع", en: "Email · tracking" },
    best: { ar: "من يبني قائمة عملاء ويحتاج سلسلة رسائل جاهزة.", en: "Anyone building a list who needs a ready email sequence." },
    tags: ["ecommerce", "crm", "services"],
    steps: {
      ar: ["اختر أحد قوالب السلسلة (ترحيب أو متابعة)", "بدّل النصوص والعروض", "أرسل عبر مزود بريد موثق وتابع الفتح والنقر"],
      en: ["Pick a sequence (welcome or follow-up)", "Replace the copy and offers", "Send through a verified email provider and track opens and clicks"],
    },
  },
];

const CHIPS = [
  { label: "chip.rates", ask: "chip.q.rates" },
  { label: "chip.deadline", ask: "chip.q.deadline" },
  { label: "chip.fields", ask: "chip.q.fields" },
  { label: "chip.audit", ask: "chip.q.audit" },
  { label: "chip.recommend", flow: "recommend" },
];

const QUICK = [
  { label: "quick.vat", ask: "chip.q.rates" },
  { label: "quick.threshold", ask: "topic.threshold" },
  { label: "quick.deadline", ask: "chip.q.deadline" },
  { label: "quick.audit", ask: "chip.q.audit" },
  { label: "quick.template", ask: "accounting template" },
];

const TOPICS = [
  { key: "topic.rates", ask: "chip.q.rates" },
  { key: "topic.threshold", ask: "threshold registration" },
  { key: "topic.deadline", ask: "chip.q.deadline" },
  { key: "topic.einvoice", ask: "e-invoicing phase" },
  { key: "topic.fields", ask: "chip.q.fields" },
  { key: "topic.input", ask: "input vat purchase deduction" },
  { key: "topic.zero", ask: "zero rated exempt" },
  { key: "topic.penalty", ask: "penalty fine" },
  { key: "topic.journal", ask: "chip.q.audit" },
];

const FLOW_ACTIVITY = [
  { value: "accounting", label: "act.accounting" },
  { value: "services", label: "act.services" },
  { value: "ecommerce", label: "act.ecommerce" },
  { value: "education", label: "act.education" },
  { value: "personal", label: "act.personal" },
  { value: "other", label: "act.other" },
];

const FLOW_PRIORITY = [
  { value: "invoicing", label: "prio.invoicing", tags: ["invoicing", "accounting"] },
  { value: "crm", label: "prio.crm", tags: ["crm"] },
  { value: "booking", label: "prio.booking", tags: ["booking"] },
  { value: "learning", label: "prio.learning", tags: ["learning", "education"] },
  { value: "showcase", label: "prio.showcase", tags: ["showcase", "personal"] },
];

/* ============================ المعرفة ============================ */
const INTENTS = [
  {
    keys: ["نسبة", "نسب", "كم الضريبة", "rate", "vat rate", "percent", "15", "5%"],
    answer: {
      ar: "نسب ضريبة القيمة المضافة في الخليج:\n• السعودية 15%\n• الإمارات 5%\n• عُمان 5%\n• البحرين 10%\n• قطر والكويت: لا تُطبَّق حاليًا (0% في القالب).\n\nحدود التسجيل الإلزامي: 375,000 ر.س في السعودية و375,000 درهم في الإمارات، والاختياري 187,500 في البلدين.",
      en: "Gulf VAT rates:\n• Saudi Arabia 15%\n• UAE 5%\n• Oman 5%\n• Bahrain 10%\n• Qatar and Kuwait: not applied yet (0% in the template).\n\nMandatory registration thresholds: SAR 375,000 in Saudi Arabia and AED 375,000 in the UAE; voluntary at 187,500 in both.",
    },
  },
  {
    keys: ["تسجيل", "حد التسجيل", "registration", "threshold", "375"],
    answer: {
      ar: "حدود التسجيل في ضريبة القيمة المضافة:\n• السعودية: إلزامي عند 375,000 ر.س من الإيرادات السنوية، واختياري من 187,500.\n• الإمارات: إلزامي عند 375,000 درهم، واختياري من 187,500.\n• عُمان: إلزامي عند 38,500 ريال عماني.\n• البحرين: إلزامي عند 37,500 دينار بحريني (واختياري من 18,750).\n• قطر والكويت: لا ضريبة قيمة مضافة حاليًا.\n\nراقب الإيرادات على أساس 12 شهرًا متتالية، لا السنة الميلادية فقط.",
      en: "VAT registration thresholds:\n• Saudi Arabia: mandatory at SAR 375,000 annual revenue, voluntary from 187,500.\n• UAE: mandatory at AED 375,000, voluntary from 187,500.\n• Oman: mandatory at OMR 38,500.\n• Bahrain: mandatory at BHD 37,500 (voluntary from 18,750).\n• Qatar and Kuwait: no VAT yet.\n\nTrack revenue over any rolling 12-month period, not only the calendar year.",
    },
  },
  {
    keys: ["موعد", "مواعيد", "إقرار", "deadline", "filing", "return", "ربع"],
    answer: {
      ar: "مواعيد الإقرار الضريبي:\n• السعودية: شهري أو ربع سنوي حسب حجم المنشأة، ويُقدَّم خلال الشهر التالي لنهاية الفترة.\n• الإمارات: ربع سنوي خلال 28 يومًا من نهاية الربع.\n• عُمان والبحرين: شهري أو ربع سنوي حسب التصنيف.\n• قطر والكويت: لا إقرار قيمة مضافة حاليًا.\n\nاحسب الموعد من تقويم الهيئة في بلدك، فقد يتغير باختلاف التصنيف.",
      en: "VAT filing deadlines:\n• Saudi Arabia: monthly or quarterly depending on size, filed in the month after the period ends.\n• UAE: quarterly, within 28 days of the quarter end.\n• Oman and Bahrain: monthly or quarterly depending on category.\n• Qatar and Kuwait: no VAT return yet.\n\nConfirm dates on your authority's portal, as the category can change the cadence.",
    },
  },
  {
    keys: ["حقول", "fields", "required fields", "qr", "فاتورة إلكترونية", "e-invoicing", "حقول الفاتورة"],
    answer: {
      ar: "الحقول الأساسية للفاتورة الضريبية:\n• اسم المورد والرقم الضريبي\n• رقم الفاتورة وتاريخ الإصدار\n• اسم العميل ورقمه الضريبي إن كان مسجلًا\n• وصف البنود والكمية والسعر والخصم\n• الصافي ونسبة الضريبة ومبلغ الضريبة والإجمالي\n• العملة ورمز QR للفاتورة المبسطة (السعودية)\n\nالفاتورة الإلكترونية في السعودية: المرحلة الأولى تشمل QR، والمرحلة الثانية ربط تكاملي مع منصة فاتورة حسب شرائح الإيرادات.",
      en: "Required tax invoice fields:\n• Seller name and tax number\n• Invoice number and issue date\n• Customer name and tax number if registered\n• Line description, quantity, price and discount\n• Net, VAT rate, VAT amount and total\n• Currency and the QR code for simplified invoices (Saudi Arabia)\n\nSaudi e-invoicing: phase one covers the QR code; phase two is an integration with the Fatoora platform by revenue waves.",
    },
  },
  {
    keys: ["مشتريات", "خصم", "مدخلات", "input", "purchase", "deduct"],
    answer: {
      ar: "شروط خصم ضريبة المشتريات (المدخلات):\n• فاتورة ضريبية صحيحة تحمل رقم المورد الضريبي.\n• شراء لاستخدام العمل الخاضع للضريبة، لا للاستخدام الشخصي.\n• تسجيل الفاتورة في الفترة الصحيحة (فترة الاستلام عادةً).\n• عدم خصم ضريبة فواتير مفقودة أو غير مطابقة للبيانات.\n\nالفواتير منخفضة الثقة أو بلا رقم ضريبي لا تُعتمد عند التدقيق، ولهذا يوسم الماسح هذه الفواتير للمراجعة.",
      en: "Conditions for deducting input VAT:\n• A valid tax invoice carrying the supplier's tax number.\n• The purchase is used for taxable business activity, not private use.\n• The invoice is recorded in the correct period (usually when received).\n• No deduction on missing or mismatched invoices.\n\nLow-confidence invoices without a tax number are rejected at audit, which is why the scanner flags them for review.",
    },
  },
  {
    keys: ["معفاة", "صفرية", "zero", "exempt", "0%"],
    answer: {
      ar: "الفرق بين المعفاة والصفرية:\n• **صفرية (0%)**: خاضعة للضريبة بنسبة صفر — تُمكّنك من خصم ضريبة المدخلات، مثل التصدير والرعاية الصحية المؤهلة في بعض الدول.\n• **معفاة**: خارج نطاق الضريبة — لا تُحصّل ضريبة ولا تخصم ضريبة المدخلات المرتبطة بها.\n\nعمليًا: لا تُدخل ضريبة على الفاتورة في الحالتين، لكن المعالجة المحاسبية للمدخلات تختلف.",
      en: "Zero-rated vs exempt:\n• **Zero-rated (0%)**: taxable at zero — input VAT is usually recoverable, e.g. exports and qualifying healthcare in some countries.\n• **Exempt**: outside the scope — no output VAT and no recovery of related input VAT.\n\nIn practice both invoices show no VAT, but input VAT treatment differs.",
    },
  },
  {
    keys: ["غرامة", "عقوبة", "penalty", "fine", "تأخير"],
    answer: {
      ar: "أكثر أسباب الغرامات الضريبية شيوعًا:\n• عدم إصدار فاتورة إلكترونية أو إصدارها ببيانات ناقصة.\n• التأخر في تقديم الإقرار أو السداد.\n• عدم مطابقة بيانات المورد بين الفاتورة والسجل.\n• عدم الاحتفاظ بالفواتير للمدة النظامية (٥ سنوات عادةً).\n\nالوقاية أرخص من التصحيح: تحقق من الحقول قبل الإصدار، وأرشف نسخة PDF لكل فاتورة.",
      en: "The most common tax penalties:\n• Missing or incomplete e-invoices.\n• Late filing or late payment.\n• Mismatched supplier details between invoice and records.\n• Not retaining invoices for the required period (often five years).\n\nPrevention is cheaper than correction: verify fields before issuing and archive a PDF of every invoice.",
    },
  },
  {
    keys: ["قيد", "قيود", "journal", "entry", "تدقيق", "audit", "ترحيل"],
    boost: ["قيود", "تدقيق", "ترحيل", "journal", "audit"],
    answer: {
      ar: "القيد الصحيح لفاتورة مبيعات:\n• مدين: ذمم العملاء / النقدية = الإجمالي\n• دائن: الإيرادات = الصافي\n• دائن: ضريبة القيمة المضافة المستحقة = مبلغ الضريبة\n\nولفاتورة مشتريات:\n• مدين: المصروف أو الأصل = الصافي\n• مدين: ضريبة المدخلات = الضريبة\n• دائن: الموردون / النقدية = الإجمالي\n\nقبل الترحيل تحقق من: الصافي × النسبة = الضريبة، والصافي + الضريبة = الإجمالي، وصيغة الرقم الضريبي. أداة التدقيق بالأسفل تجري هذه الفحوص نيابةً عنك.",
      en: "Correct sales invoice entry:\n• Debit receivables / cash = total\n• Credit revenue = net\n• Credit VAT payable = VAT amount\n\nPurchase invoice entry:\n• Debit expense or asset = net\n• Debit input VAT = VAT\n• Credit payables / cash = total\n\nBefore posting, verify: net × rate = VAT, net + VAT = total, and the tax-number format. The audit tool below runs these checks for you.",
    },
  },
  {
    keys: ["قالب", "قوالب", "template", "templates", "أي قالب"],
    answer: {
      ar: "قوالب Arab Templates المتاحة:\n• نظام المحاسبة والامتثال الضريبي الخليجي — فواتير QR وإقرار ومسح\n• متجر القوالب الرقمي — عرض وبيع القوالب\n• لوحة متابعة العملاء (CRM)\n• نظام حجز المواعيد\n• بطاقات تعليمية تفاعلية\n• موقع أعمال شخصي\n• مساعد ذكي مخصص\n• حملة بريدية عربية\n\nاضغط «اختر لي القالب المناسب» أو «هل يناسبني؟» على أي بطاقة في قسم القوالب، وسأشرح الخطوات بالتفصيل.",
      en: "Available Arab Templates:\n• Gulf tax & accounting suite — QR invoices, VAT return, scanning\n• Digital templates store — showcase and sell templates\n• Customer follow-up dashboard (CRM)\n• Appointment booking system\n• Interactive study flashcards\n• Personal portfolio site\n• Custom AI assistant\n• Arabic email campaign\n\nPress “Recommend a template” or “Is it right for me?” on any card in the catalogue and I will explain the setup steps.",
    },
  },
  {
    keys: ["تشغيل", "استخدام", "setup", "install", "run", "start", "كيف أستخدم"],
    answer: {
      ar: "خطوات تشغيل منتجات Arab Templates:\n1. تثبيت بايثون ثم الحزم: python -m pip install flask segno\n2. تشغيل الخادم: python gulf_tax_template_pro/server.py --port 5075\n3. فتح http://127.0.0.1:5075 في المتصفح\n4. من الإعدادات: الدولة والعملة واللغة\n5. إصدار أول فاتورة وحفظها لتظهر في الإقرار\n\nللمتجر: python scripts/store_server.py ثم http://127.0.0.1:8787.",
      en: "Running Arab Templates products:\n1. Install Python, then: python -m pip install flask segno\n2. Start the server: python gulf_tax_template_pro/server.py --port 5075\n3. Open http://127.0.0.1:5075\n4. In settings, pick country, currency and language\n5. Issue your first invoice and save it so it appears in the return\n\nFor the store: python scripts/store_server.py then http://127.0.0.1:8787.",
    },
  },
  {
    keys: ["دعم", "تواصل", "support", "contact", "بشري", "human"],
    answer: {
      ar: "للحصول على دعم بشري:\n• اطرح سؤالك هنا أولًا — معظم أسئلة القوالب والضريبة لها جواب فوري.\n• إن احتجت متابعة بشرية، أرسل التفاصيل من صفحة المتجر أو من تبويب «التواصل مع المحاسب» داخل القالب الضريبي (يُنشئ تذكرة برقم).\n• أرفق دائمًا: الدولة، الفترة، ومبلغ الفاتورة، لتسريع الرد.",
      en: "For human support:\n• Ask here first — most template and VAT questions are answered instantly.\n• If you need a person, send details from the store page or the “Talk to an accountant” tab inside the tax template (it creates a ticket number).\n• Always include: country, period and invoice amount to speed up the reply.",
    },
  },
];

/* ============================ المحادثة ============================ */
function appendMsg(role, text) {
  const wrap = document.createElement("div");
  wrap.className = "msg " + (role === "user" ? "user" : "bot");
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  wrap.appendChild(bubble);
  $("chatLog").appendChild(wrap);
  $("chatLog").scrollTop = $("chatLog").scrollHeight;
  return wrap;
}

function answerFor(text) {
  const norm = String(text || "").toLowerCase();
  let best = null, bestScore = 0;
  INTENTS.forEach((intent) => {
    let score = 0;
    intent.keys.forEach((key) => {
      if (norm.includes(String(key).toLowerCase())) score += Math.max(2, String(key).length);
    });
    (intent.boost || []).forEach((key) => {
      if (norm.includes(String(key).toLowerCase())) score += 12;
    });
    if (score > bestScore) { best = intent; bestScore = score; }
  });
  if (best && bestScore >= 2) return best.answer[state.lang === "en" ? "en" : "ar"];
  return t("msg.notfound") + "\n" + TOPICS.slice(0, 5).map((topic) => "• " + t(topic.key)).join("\n");
}

function ask(question) {
  const q = String(question || "").trim();
  if (!q) return;
  appendMsg("user", q);
  const typing = appendMsg("bot", "…");
  typing.classList.add("typing");
  setTimeout(() => {
    typing.remove();
    appendMsg("bot", answerFor(q));
  }, 420);
}

/* ---- التوصية ---- */
function startRecommend() {
  state.flow = { step: "activity", activity: null };
  appendMsg("bot", t("flow.activity") + "\n" + t("flow.choose"));
  renderChips();
}

function renderChips() {
  const box = $("chips");
  if (state.flow) {
    const options = state.flow.step === "activity" ? FLOW_ACTIVITY : FLOW_PRIORITY;
    box.innerHTML = options.map((option) =>
      `<button class="chip" type="button" data-flow="${option.value}">${t(option.label)}</button>`).join("");
  } else {
    box.innerHTML = CHIPS.map((chip) =>
      `<button class="chip" type="button" data-ask="${chip.ask ? t(chip.ask) : ""}" data-flow="${chip.flow || ""}">${t(chip.label)}</button>`).join("");
  }
  box.querySelectorAll("button").forEach((btn) => {
    btn.addEventListener("click", () => {
      const flowValue = btn.getAttribute("data-flow");
      if (flowValue) { handleFlow(flowValue); return; }
      ask(btn.getAttribute("data-ask"));
    });
  });
}

function handleFlow(value) {
  if (!state.flow) return;
  if (state.flow.step === "activity") {
    const option = FLOW_ACTIVITY.find((item) => item.value === value);
    state.flow.activity = value;
    state.flow.step = "priority";
    appendMsg("user", option ? t(option.label) : value);
    appendMsg("bot", t("flow.priority") + "\n" + t("flow.choose"));
    renderChips();
    return;
  }
  const priority = FLOW_PRIORITY.find((item) => item.value === value);
  appendMsg("user", priority ? t(priority.label) : value);
  const wanted = new Set([...(priority ? priority.tags : [])]);
  if (state.flow.activity && state.flow.activity !== "other") wanted.add(state.flow.activity);
  let chosen = TEMPLATES[0];
  let score = -1;
  TEMPLATES.forEach((template) => {
    const hit = template.tags.filter((tag) => wanted.has(tag)).length;
    if (hit > score) { score = hit; chosen = template; }
  });
  const steps = chosen.steps[state.lang === "en" ? "en" : "ar"];
  const text = [
    t("recommend.done", { name: chosen.name[state.lang === "en" ? "en" : "ar"] }),
    t("recommend.why", { reason: chosen.best[state.lang === "en" ? "en" : "ar"] }),
    "",
    t("recommend.steps"),
    ...steps.map((step, index) => `${index + 1}. ${step}`),
  ].join("\n");
  appendMsg("bot", text);
  state.flow = null;
  renderChips();
}

/* ---- الأزرار الجانبية والمواضيع والكتالوج ---- */
function renderQuick() {
  $("quickList").innerHTML = QUICK.map((item) =>
    `<button type="button" data-ask="${t(item.ask)}">${t(item.label)}</button>`).join("");
  $("quickList").querySelectorAll("button").forEach((btn) =>
    btn.addEventListener("click", () => ask(btn.getAttribute("data-ask"))));
}

function renderTopics() {
  $("topicGrid").innerHTML = TOPICS.map((topic) =>
    `<button class="topic" type="button" data-ask="${t(topic.ask)}">
      <strong>${t(topic.key)}</strong><span>${t(topic.key + ".sub")}</span></button>`).join("");
  $("topicGrid").querySelectorAll("button").forEach((btn) =>
    btn.addEventListener("click", () => {
      ask(btn.getAttribute("data-ask"));
      document.getElementById("assistant").scrollIntoView({ behavior: "smooth", block: "start" });
    }));
}

function renderCatalog() {
  $("catalogGrid").innerHTML = TEMPLATES.map((template) => {
    const name = template.name[state.lang === "en" ? "en" : "ar"];
    const steps = template.steps[state.lang === "en" ? "en" : "ar"];
    return `<article class="tcard">
      <span class="kicker">${template.kicker[state.lang === "en" ? "en" : "ar"]}</span>
      <h3>${name}</h3>
      <p>${template.best[state.lang === "en" ? "en" : "ar"]}</p>
      <ol>${steps.map((step) => `<li>${step}</li>`).join("")}</ol>
      <div class="actions">
        <button type="button" data-steps="${template.id}">${t("catalog.ask")}</button>
        ${template.link ? `<a class="btn ghost" style="padding:7px 12px;font-size:.78rem;border-radius:9px" href="${template.link}" target="_blank" rel="noopener">${state.lang === "en" ? "Open" : "فتح"}</a>` : ""}
      </div>
    </article>`;
  }).join("");
  $("catalogGrid").querySelectorAll("[data-steps]").forEach((btn) =>
    btn.addEventListener("click", () => {
      const template = TEMPLATES.find((item) => item.id === btn.getAttribute("data-steps"));
      if (!template) return;
      const lang = state.lang === "en" ? "en" : "ar";
      appendMsg("user", template.name[lang]);
      appendMsg("bot", t("msg.steps", { name: template.name[lang] }) + "\n" +
        template.steps[lang].map((step, index) => `${index + 1}. ${step}`).join("\n"));
      document.getElementById("assistant").scrollIntoView({ behavior: "smooth", block: "start" });
    }));
}

/* ============================ أداة التدقيق ============================ */
function auditSample() {
  $("auditCountry").value = "SA";
  $("auditTaxNo").value = "310123456700003";
  $("auditDate").value = new Date().toISOString().slice(0, 10);
  $("auditNet").value = "1000";
  $("auditVat").value = "150";
  $("auditTotal").value = "1150";
  $("auditResult").hidden = true;
  appendMsg("bot", t("audit.sample.done"));
}

function runAudit() {
  const code = $("auditCountry").value;
  const country = COUNTRIES[code];
  const net = Number($("auditNet").value);
  const vat = Number($("auditVat").value);
  const total = Number($("auditTotal").value);
  const taxNo = $("auditTaxNo").value.trim();
  const dateValue = $("auditDate").value;
  const checks = [];
  const ok = (label, detail) => checks.push({ status: "ok", label, detail });
  const bad = (label, detail) => checks.push({ status: "bad", label, detail });
  const warn = (label, detail) => checks.push({ status: "warn", label, detail });

  if (!(net > 0)) bad(l("المبلغ قبل الضريبة", "Pre-VAT amount"), t("audit.net.invalid"));
  else ok(l("المبلغ قبل الضريبة", "Pre-VAT amount"), t("audit.net.valid"));

  const expectedVat = Math.round(net * country.rate) / 100;
  if (vat < 0) bad(l("مبلغ الضريبة", "VAT amount"), t("audit.vat.negative"));
  else if (country.rate === 0 && vat > 0.009) bad(l("مبلغ الضريبة", "VAT amount"), t("audit.vat.zero"));
  else if (Math.abs(vat - expectedVat) > 0.05) {
    bad(l("مبلغ الضريبة", "VAT amount"),
      t("audit.vat.mismatch", { actual: fmt(vat), expected: fmt(expectedVat) }));
  } else ok(l("مبلغ الضريبة", "VAT amount"), t("audit.rate.valid", { rate: fmt(country.rate, 0) }));

  const expectedTotal = Math.round((net + expectedVat) * 100) / 100;
  if (!(total > 0) || Math.abs(total - expectedTotal) > 0.05) {
    bad(l("إجمالي الفاتورة", "Invoice total"),
      t("audit.total.mismatch", { actual: fmt(total), expected: fmt(expectedTotal) }));
  } else ok(l("إجمالي الفاتورة", "Invoice total"), t("audit.total.valid"));

  const hint = state.lang === "en" ? country.hintEn : country.hintAr;
  if (!taxNo) warn(l("الرقم الضريبي", "Tax number"), t("audit.taxno.invalid", { hint }));
  else if (!country.regex.test(taxNo)) bad(l("الرقم الضريبي", "Tax number"), t("audit.taxno.invalid", { hint }));
  else ok(l("الرقم الضريبي", "Tax number"), t("audit.taxno.valid", { hint }));

  if (!dateValue) warn(l("تاريخ الفاتورة", "Invoice date"), t("audit.date.future"));
  else if (dateValue > new Date().toISOString().slice(0, 10)) bad(l("تاريخ الفاتورة", "Invoice date"), t("audit.date.future"));
  else ok(l("تاريخ الفاتورة", "Invoice date"), t("audit.date.valid"));

  const passed = checks.filter((check) => check.status === "ok").length;
  const score = Math.round((passed / checks.length) * 100);
  state.audit = { checks, passed, total: checks.length, score, net, vat, total, expectedVat, expectedTotal, country, code };
  renderAudit();
  $("auditResult").hidden = false;
}

function renderAudit() {
  const audit = state.audit;
  if (!audit) return;
  $("auditScore").textContent = audit.score + "%";
  $("auditVerdict").textContent = audit.score === 100 ? t("audit.v.ok")
    : audit.score >= 70 ? t("audit.v.warn") : t("audit.v.bad");
  $("auditChecks").innerHTML = audit.checks.map((check) => {
    const icon = check.status === "ok" ? "✓" : check.status === "warn" ? "!" : "✕";
    return `<li class="${check.status}"><span class="ic">${icon}</span>
      <span><strong>${check.label}</strong> — ${check.detail}</span></li>`;
  }).join("");

  $("journalHead").innerHTML = `<tr><th>${t("audit.journal.account")}</th><th>${t("audit.journal.debit")}</th><th>${t("audit.journal.credit")}</th></tr>`;
  const net = Number.isFinite(audit.net) ? audit.net : 0;
  const vat = Number.isFinite(audit.vat) ? audit.vat : 0;
  const total = Number.isFinite(audit.total) ? audit.total : net + vat;
  const rows = [
    [t("audit.journal.total"), fmt(total), ""],
    [t("audit.journal.net"), "", fmt(net)],
  ];
  if (vat > 0) rows.push([t("audit.journal.vat"), "", fmt(vat)]);
  $("journalBody").innerHTML = rows.map((row) =>
    `<tr><td>${row[0]}</td><td>${row[1]}</td><td>${row[2]}</td></tr>`).join("");
  const needsFix = Math.abs(vat - audit.expectedVat) > 0.05 || Math.abs(total - audit.expectedTotal) > 0.05;
  $("journalNote").textContent = needsFix
    ? t("audit.journal.note.adjust", { vat: fmt(audit.expectedVat), total: fmt(audit.expectedTotal) }) +
      " " + t("audit.journal.note")
    : t("audit.journal.note");
}

/* ============================ اللغة والتشغيل ============================ */
function applyLang(lang, persist = true) {
  state.lang = lang === "en" ? "en" : "ar";
  const ar = state.lang === "ar";
  document.documentElement.lang = ar ? "ar" : "en";
  document.documentElement.dir = ar ? "rtl" : "ltr";
  document.body.classList.toggle("ltr", !ar);
  document.title = t("page.title");
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (key && I18N[state.lang][key] !== undefined) el.textContent = t(key);
  });
  document.querySelectorAll("[data-i18n-ph]").forEach((el) => {
    el.setAttribute("placeholder", t(el.getAttribute("data-i18n-ph")));
  });
  $("langBtn").textContent = ar ? "English" : "العربية";
  renderChips();
  renderQuick();
  renderTopics();
  renderCatalog();
  if (state.audit) runAudit();
  if (persist) localStorage.setItem("at_assistant_lang", state.lang);
}

$("langBtn").addEventListener("click", () => applyLang(state.lang === "ar" ? "en" : "ar"));
$("chatForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const input = $("chatInput");
  const value = input.value.trim();
  input.value = "";
  ask(value);
});
document.querySelectorAll("[data-action='recommend']").forEach((btn) =>
  btn.addEventListener("click", () => {
    document.getElementById("assistant").scrollIntoView({ behavior: "smooth", block: "start" });
    startRecommend();
  }));
$("auditBtn").addEventListener("click", runAudit);
$("auditSample").addEventListener("click", auditSample);
$("auditClear").addEventListener("click", () => {
  ["auditTaxNo", "auditDate", "auditNet", "auditVat", "auditTotal"].forEach((id) => { $(id).value = ""; });
  state.audit = null;
  $("auditResult").hidden = true;
  appendMsg("bot", t("audit.cleared"));
});
$("auditDate").value = new Date().toISOString().slice(0, 10);

const saved = localStorage.getItem("at_assistant_lang");
applyLang(saved === "en" ? "en" : "ar", false);
