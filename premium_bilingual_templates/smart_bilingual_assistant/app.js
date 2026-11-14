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
    "catalog.store": "افتح في المتجر", "recommend.open": "افتح القالب المقترح في المتجر",
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
    "audit.currency": "عملة الفاتورة", "audit.period": "الفترة الضريبية",
    "audit.currency.valid": "العملة مطابقة لعملة الدولة ({currency})",
    "audit.currency.mismatch": "الفاتورة بعملة {actual} بينما العملة القانونية {expected} — وثّق سعر التحويل أو أعد الإصدار بالعملة المحلية",
    "audit.period.valid": "تاريخ الفاتورة داخل الفترة الضريبية ({period})",
    "audit.period.mismatch": "تاريخ الفاتورة {date} خارج الفترة المحددة {period}",
    "audit.period.missing": "لم تُحدد الفترة الضريبية — لا يمكن التحقق من ملاءمة التاريخ",
    "audit.period.future": "الفترة الضريبية في المستقبل ({period}) — راجع الشهر",
    "lines.title": "تدقيق بنود فاتورة نصية", "lines.tag": "بند بند",
    "lines.sub": "الصق البنود، كل بند في سطر بالصيغة: الوصف | الكمية | سعر الوحدة | الخصم% | الإجمالي المسجّل (اختياري).",
    "lines.ph": "استشارات ضريبية | 2 | 1000 | 0 | 2300\nاجتماعات | 1 | 500 | 10 | 517.50",
    "lines.run": "دقّق البنود", "lines.sample": "مثال", "lines.clear": "تفريغ",
    "lines.need": "الصق بندًا واحدًا على الأقل (الوصف | الكمية | السعر | الخصم%).",
    "lines.ok": "البند سليم", "lines.bad": "يحتاج تصحيحًا",
    "lines.descFallback": "بند {n}",
    "lines.verdict.ok": "كل البنود متسقة مع نسبة الدولة",
    "lines.verdict.bad": "{count} بندًا يحتاج تصحيحًا",
    "lines.totals": "مجموع البنود: الصافي {net} · الضريبة {vat} · الإجمالي {total}",
    "lines.totalsMatch": "مجموع البنود يطابق إجمالي الفاتورة أعلاه",
    "lines.totalsMismatch": "مجموع البنود لا يطابق إجمالي الفاتورة أعلاه (فرق {diff})",
    "lines.statedMismatch": "الإجمالي المسجّل {stated} يختلف عن المحسوب {computed}",
    "lines.qtyBad": "الكمية يجب أن تكون أكبر من صفر",
    "lines.priceBad": "السعر لا يكون سالبًا",
    "lines.discBad": "الخصم يجب أن يكون بين ٠ و١٠٠",
    "lines.sample.done": "حُمّل مثال بنود — اضغط «دقّق البنود».",
    "lines.cleared": "تم تفريغ البنود.",
    "lines.col.item": "البند", "lines.col.qty": "الكمية", "lines.col.price": "السعر",
    "lines.col.disc": "الخصم", "lines.col.net": "الصافي", "lines.col.vat": "الضريبة",
    "lines.col.total": "الإجمالي", "lines.col.state": "الحالة",
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
    "catalog.store": "Open in store", "recommend.open": "Open the suggested template in the store",
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
    "audit.currency": "Invoice currency", "audit.period": "Tax period",
    "audit.currency.valid": "Currency matches the country currency ({currency})",
    "audit.currency.mismatch": "Invoice is in {actual} but the legal currency is {expected} — document the conversion rate or reissue in local currency",
    "audit.period.valid": "Invoice date falls inside the tax period ({period})",
    "audit.period.mismatch": "Invoice date {date} is outside the selected period {period}",
    "audit.period.missing": "No tax period selected — the date cannot be checked against it",
    "audit.period.future": "The tax period is in the future ({period}) — review the month",
    "lines.title": "Audit pasted invoice lines", "lines.tag": "Line by line",
    "lines.sub": "Paste one line per row: description | quantity | unit price | discount% | recorded total (optional).",
    "lines.ph": "Tax consulting | 2 | 1000 | 0 | 2300\nMeetings | 1 | 500 | 10 | 517.50",
    "lines.run": "Audit lines", "lines.sample": "Sample", "lines.clear": "Clear",
    "lines.need": "Paste at least one line (description | quantity | price | discount%).",
    "lines.ok": "Line is valid", "lines.bad": "Needs correction",
    "lines.descFallback": "Line {n}",
    "lines.verdict.ok": "All lines agree with the country rate",
    "lines.verdict.bad": "{count} line(s) need correction",
    "lines.totals": "Line totals: net {net} · VAT {vat} · total {total}",
    "lines.totalsMatch": "The line totals match the invoice total above",
    "lines.totalsMismatch": "The line totals do not match the invoice total above (difference {diff})",
    "lines.statedMismatch": "Recorded total {stated} differs from the computed {computed}",
    "lines.qtyBad": "Quantity must be greater than zero",
    "lines.priceBad": "Price cannot be negative",
    "lines.discBad": "Discount must be between 0 and 100",
    "lines.sample.done": "Sample lines loaded — press “Audit lines”.",
    "lines.cleared": "Lines cleared.",
    "lines.col.item": "Item", "lines.col.qty": "Qty", "lines.col.price": "Price",
    "lines.col.disc": "Disc.", "lines.col.net": "Net", "lines.col.vat": "VAT",
    "lines.col.total": "Total", "lines.col.state": "Status",
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

const CURRENCY_NAMES = {
  SAR: { ar: "ريال سعودي", en: "Saudi riyal" },
  AED: { ar: "درهم إماراتي", en: "UAE dirham" },
  KWD: { ar: "دينار كويتي", en: "Kuwaiti dinar" },
  QAR: { ar: "ريال قطري", en: "Qatari riyal" },
  OMR: { ar: "ريال عماني", en: "Omani rial" },
  BHD: { ar: "دينار بحريني", en: "Bahraini dinar" },
  USD: { ar: "دولار أمريكي", en: "US dollar" },
  EUR: { ar: "يورو", en: "Euro" },
};

const round2 = (value) => Math.round((Number(value) || 0) * 100) / 100;
const currentPeriod = () => new Date().toISOString().slice(0, 7);
const esc = (value) => String(value == null ? "" : value).replace(/[&<>"']/g, (ch) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));

function renderCurrencyOptions() {
  const select = $("auditCurrency");
  if (!select) return;
  const previous = select.value;
  select.innerHTML = Object.keys(CURRENCY_NAMES).map((code) =>
    `<option value="${code}">${code} — ${CURRENCY_NAMES[code][state.lang === "en" ? "en" : "ar"]}</option>`).join("");
  select.value = previous && CURRENCY_NAMES[previous] ? previous : COUNTRIES[$("auditCountry").value].currency;
}

// رابط كتالوج المتجر — بدّله إلى نطاقك المنشور عند النشر (مثال: "https://store.example.com/")
const STORE_BASE = "http://127.0.0.1:8787/";

function storeLink(template) {
  const base = STORE_BASE || "../store/index.html";
  const query = new URLSearchParams({ from: "assistant" });
  if (template.store && template.store.q) query.set("q", template.store.q);
  if (template.store && template.store.cat) query.set("cat", template.store.cat);
  return base + "?" + query.toString();
}

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
    store: { q: "فواتير ضريبية", cat: "أنظمة الفواتير الضريبية" },
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
    store: { q: "متجر إلكتروني", cat: "متاجر إلكترونية" },
    link: "../store/index.html",
  },
  {
    id: "crm", name: { ar: "لوحة متابعة العملاء (CRM)", en: "Customer follow-up dashboard (CRM)" },
    kicker: { ar: "عملاء · مهام · تقارير", en: "Customers · tasks · reports" },
    best: { ar: "فرق المبيعات والخدمات التي تتابع عملاءها يدويًا في الجداول.", en: "Sales and service teams still tracking customers in spreadsheets." },
    tags: ["crm", "services", "accounting"],
    store: { q: "عملاء" },
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
    store: { q: "حجوزات", cat: "الحجوزات" },
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
    store: { q: "موقع شخصي", cat: "مواقع شخصية" },
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
    store: { q: "حملة بريدية", cat: "تسويق" },
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

/* قاعدة المعرفة والمطابقة في core.js */

/* ============================ المحادثة ============================ */
function appendMsg(role, text, link) {
  const wrap = document.createElement("div");
  wrap.className = "msg " + (role === "user" ? "user" : "bot");
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  if (link && link.href) {
    const anchor = document.createElement("a");
    anchor.className = "msg-link";
    anchor.href = link.href;
    anchor.target = "_blank";
    anchor.rel = "noopener";
    anchor.textContent = link.label || link.href;
    bubble.appendChild(anchor);
  }
  wrap.appendChild(bubble);
  $("chatLog").appendChild(wrap);
  $("chatLog").scrollTop = $("chatLog").scrollHeight;
  return wrap;
}

function answerFor(text) {
  const core = window.AssistantCore;
  const lang = state.lang === "en" ? "en" : "ar";
  const result = core ? core.matchIntent(text) : { intent: null };
  if (result.intent) {
    if (result.country) {
      const tailored = core.countryAnswer(result.intent.id, result.country, lang);
      if (tailored) {
        const hint = lang === "en"
          ? "Ask me about registration, filing deadlines or invoice fields for more detail."
          : "اسألني عن التسجيل أو مواعيد الإقرار أو حقول الفاتورة لمزيد من التفاصيل.";
        return [tailored, "", hint].join("\n");
      }
    }
    return result.intent.answer[lang];
  }
  return [t("msg.notfound")]
    .concat(TOPICS.slice(0, 5).map((topic) => "• " + t(topic.key)))
    .join("\n");
}

function isUnanswered(question) {
  const core = window.AssistantCore;
  if (!core || typeof core.matchIntent !== "function") return false;
  const result = core.matchIntent(question);
  return !result || !result.intent;
}

function logUnanswered(question) {
  if (!/^https?:$/.test(location.protocol)) return;
  fetch("/api/unanswered", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, lang: state.lang }),
    keepalive: true,
  }).catch(() => {});
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
    if (isUnanswered(q)) logUnanswered(q);
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
  appendMsg("bot", text, { href: storeLink(chosen), label: t("recommend.open") });
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
        <a class="btn" style="padding:7px 12px;font-size:.78rem;border-radius:9px" href="${storeLink(template)}" target="_blank" rel="noopener">${t("catalog.store")}</a>
        ${template.link && !template.store ? `<a class="btn ghost" style="padding:7px 12px;font-size:.78rem;border-radius:9px" href="${template.link}" target="_blank" rel="noopener">${state.lang === "en" ? "Open" : "فتح"}</a>` : ""}
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
  $("auditCurrency").value = "SAR";
  $("auditPeriod").value = currentPeriod();
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

  const currency = $("auditCurrency").value;
  if (currency === country.currency) {
    ok(l("عملة الفاتورة", "Invoice currency"), t("audit.currency.valid", { currency }));
  } else {
    bad(l("عملة الفاتورة", "Invoice currency"),
      t("audit.currency.mismatch", { actual: currency, expected: country.currency }));
  }

  const period = $("auditPeriod").value;
  if (!period) {
    warn(l("الفترة الضريبية", "Tax period"), t("audit.period.missing"));
  } else if (period > currentPeriod()) {
    warn(l("الفترة الضريبية", "Tax period"), t("audit.period.future", { period }));
  } else if (dateValue && dateValue.slice(0, 7) !== period) {
    bad(l("الفترة الضريبية", "Tax period"),
      t("audit.period.mismatch", { date: dateValue, period }));
  } else {
    ok(l("الفترة الضريبية", "Tax period"), t("audit.period.valid", { period }));
  }

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
  renderCurrencyOptions();
  if (state.audit) runAudit();
  if (state.lines) auditLines();
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
/* ---- تدقيق البنود النصية ---- */
function parseInvoiceLines(raw) {
  const rate = COUNTRIES[$("auditCountry").value].rate;
  const rows = [];
  String(raw || "").split(/\r?\n/).forEach((line) => {
    const text = line.trim();
    if (!text) return;
    const parts = text.split(/\s*[|\t;]\s*/).filter((part) => part !== "");
    let desc = "";
    const numbers = [];
    parts.forEach((part, index) => {
      const cleaned = part.replace(/,/g, "").trim();
      if (/^-?\d+(\.\d+)?$/.test(cleaned)) { numbers.push(Number(cleaned)); return; }
      if (index === 0 || !desc) desc = part.trim();
    });
    if (!numbers.length) return;
    let quantity = 1;
    let price = numbers[0];
    let discount = 0;
    let stated = null;
    if (numbers.length >= 2) {
      quantity = numbers[0];
      price = numbers[1];
      discount = numbers[2] || 0;
      if (numbers.length >= 4) stated = numbers[3];
    }
    const issues = [];
    if (!(quantity > 0)) issues.push(t("lines.qtyBad"));
    if (price < 0) issues.push(t("lines.priceBad"));
    if (discount < 0 || discount > 100) issues.push(t("lines.discBad"));
    const safeDiscount = Math.min(100, Math.max(0, discount));
    const gross = Math.max(0, quantity) * Math.max(0, price);
    const net = round2(gross - gross * safeDiscount / 100);
    const vat = round2(net * rate / 100);
    const total = round2(net + vat);
    if (stated !== null && Math.abs(stated - total) > 0.05) {
      issues.push(t("lines.statedMismatch", { stated: fmt(stated), computed: fmt(total) }));
    }
    rows.push({
      desc: desc || t("lines.descFallback", { n: rows.length + 1 }),
      quantity, price, discount, net, vat, total, issues,
    });
  });
  return rows;
}

function auditLines() {
  const rows = parseInvoiceLines($("auditLines").value);
  const message = $("linesMsg");
  if (!rows.length) {
    message.className = "msg bad";
    message.textContent = t("lines.need");
    $("linesResult").hidden = true;
    state.lines = null;
    return;
  }
  const okRows = rows.filter((row) => !row.issues.length).length;
  const totals = rows.reduce((acc, row) => ({
    net: round2(acc.net + row.net), vat: round2(acc.vat + row.vat), total: round2(acc.total + row.total),
  }), { net: 0, vat: 0, total: 0 });
  state.lines = { rows, okRows, totals };
  message.className = "msg";
  message.textContent = "";
  renderLines();
  $("linesResult").hidden = false;
}

function renderLines() {
  const data = state.lines;
  if (!data) return;
  const failed = data.rows.length - data.okRows;
  $("linesScore").textContent = fmt(data.okRows, 0) + " / " + fmt(data.rows.length, 0);
  $("linesVerdict").textContent = failed
    ? t("lines.verdict.bad", { count: fmt(failed, 0) })
    : t("lines.verdict.ok");
  $("linesHead").innerHTML = `<tr><th>#</th><th>${t("lines.col.item")}</th><th>${t("lines.col.qty")}</th>
    <th>${t("lines.col.price")}</th><th>${t("lines.col.disc")}</th><th>${t("lines.col.net")}</th>
    <th>${t("lines.col.vat")}</th><th>${t("lines.col.total")}</th><th>${t("lines.col.state")}</th></tr>`;
  $("linesBody").innerHTML = data.rows.map((row, index) => `
    <tr class="${row.issues.length ? "row-bad" : ""}">
      <td>${fmt(index + 1, 0)}</td>
      <td>${esc(row.desc)}</td>
      <td>${fmt(row.quantity, 2)}</td>
      <td>${fmt(row.price)}</td>
      <td>${fmt(row.discount, 0)}%</td>
      <td>${fmt(row.net)}</td>
      <td>${fmt(row.vat)}</td>
      <td>${fmt(row.total)}</td>
      <td class="${row.issues.length ? "bad-cell" : "ok-cell"}">${row.issues.length ? t("lines.bad") : t("lines.ok")}
        ${row.issues.length ? `<div class="tiny">${esc(row.issues.join(" · "))}</div>` : ""}</td>
    </tr>`).join("");
  const parts = [t("lines.totals", { net: fmt(data.totals.net), vat: fmt(data.totals.vat), total: fmt(data.totals.total) })];
  const invoiceNet = Number($("auditNet").value);
  if (invoiceNet > 0) {
    const diff = round2(data.totals.net - invoiceNet);
    parts.push(Math.abs(diff) <= 0.05
      ? t("lines.totalsMatch")
      : t("lines.totalsMismatch", { diff: fmt(Math.abs(diff)) }));
  }
  $("linesTotals").textContent = parts.join(" — ");
}

$("auditLinesBtn").addEventListener("click", auditLines);
$("linesSample").addEventListener("click", () => {
  $("auditLines").value = l(
    "استشارات ضريبية | 2 | 1000 | 0 | 2300\nاجتماعات | 1 | 500 | 10 | 517.50\nاشتراك سنوي | 1 | 1200 | 0",
    "Tax consulting | 2 | 1000 | 0 | 2300\nMeetings | 1 | 500 | 10 | 517.50\nAnnual subscription | 1 | 1200"
  );
  $("linesMsg").className = "msg";
  $("linesMsg").textContent = t("lines.sample.done");
});
$("linesClear").addEventListener("click", () => {
  $("auditLines").value = "";
  state.lines = null;
  $("linesResult").hidden = true;
  $("linesMsg").className = "msg";
  $("linesMsg").textContent = t("lines.cleared");
});
$("auditCountry").addEventListener("change", () => {
  $("auditCurrency").value = COUNTRIES[$("auditCountry").value].currency;
  if (state.lines) auditLines();
});

$("auditPeriod").value = currentPeriod();
renderCurrencyOptions();
$("auditDate").value = new Date().toISOString().slice(0, 10);

const saved = localStorage.getItem("at_assistant_lang");
applyLang(saved === "en" ? "en" : "ar", false);
