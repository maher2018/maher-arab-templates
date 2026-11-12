/* Gulf Tax & Accounting Suite — واجهة ثنائية اللغة (AR/EN) وتوطين العملات بلا مكتبات خارجية */
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

/* ================== الترجمة ================== */
const I18N = {
  ar: {
    "page.title": "نظام المحاسبة والامتثال الضريبي الخليجي — Arab Templates",
    "brand.name": "الامتثال الضريبي الخليجي", "brand.sub": "Gulf Tax & Accounting Suite",
    "ticker.loading": "جارٍ تحميل العملات…",
    "status.connecting": "جارٍ الاتصال…", "status.online": "الخادم متصل", "status.offline": "الخادم غير متاح",
    "nav.invoice": "الفواتير الإلكترونية", "nav.return": "الإقرار الضريبي", "nav.scan": "الماسح الذكي",
    "nav.assistant": "المساعد والمحاسب", "nav.plans": "الباقات",
    "controls.country": "الدولة", "controls.currency": "العملة", "controls.settings": "الإعدادات",
    "hero.title": "نظام واحد للمحاسبة والامتثال الضريبي في الخليج",
    "hero.sub": "أصدر فواتير إلكترونية برمز QR معتمد، احسب صافي الإقرار تلقائيًا، واسحب فواتير المشتريات من صورة أو نص واتساب — بواجهة عربية وإنجليزية.",
    "hero.stat.scanned": "فاتورة ممسوحة في هذه الجلسة", "hero.stat.tax": "إجمالي الضريبة المستخرجة",
    "hero.stat.net": "صافي الإقرار الحالي", "hero.stat.news": "تحديثات سوق متاحة",

    "invoice.title": "مولّد الفواتير الإلكترونية المعتمدة", "invoice.country": "دولة الإصدار",
    "invoice.rate": "نسبة الضريبة %", "invoice.date": "تاريخ الفاتورة",
    "invoice.seller": "بيانات المورد (البائع)", "invoice.buyer": "بيانات العميل (المشتري)",
    "invoice.seller.name": "الاسم التجاري", "invoice.seller.vat": "الرقم الضريبي",
    "invoice.seller.address": "العنوان", "invoice.seller.email": "البريد", "invoice.seller.phone": "الهاتف",
    "invoice.buyer.name": "اسم العميل", "invoice.buyer.vat": "الرقم الضريبي للعميل (اختياري)",
    "invoice.buyer.address": "العنوان", "invoice.buyer.email": "البريد", "invoice.number": "رقم الفاتورة",
    "invoice.items": "بنود الفاتورة", "invoice.include_vat": "الأسعار تشمل الضريبة",
    "invoice.add_item": "+ إضافة بند",
    "invoice.footnote": "الفاتورة تُحسب وتُشفّر على الخادم بلا أي مكتبة خارجية في المتصفح، ولا تُحفظ إلا عند الضغط على «حفظ».",

    "col.no": "#", "col.desc": "الوصف", "col.qty": "الكمية", "col.price": "سعر الوحدة",
    "col.discount": "خصم %", "col.net": "الصافي", "col.vat": "الضريبة", "col.total": "الإجمالي", "col.actions": "",

    "sum.subtotal": "الإجمالي قبل الضريبة", "sum.discount": "الخصم", "sum.vat": "ضريبة القيمة المضافة",
    "sum.grand": "الإجمالي المستحق",
    "btn.issue": "إصدار الفاتورة ورمز QR", "btn.print": "طباعة / PDF", "btn.save": "حفظ ثم إضافة للمبيعات",
    "btn.new_invoice": "فاتورة جديدة", "btn.scan": "امسح الفواتير", "btn.sample": "نموذج واتساب",
    "btn.export": "تصدير CSV", "btn.bulk": "اختبار ٥٠٠ فاتورة", "btn.ocr_save": "أضف إلى سجل المشتريات",
    "btn.add_all": "أضف كل النتائج إلى سجل المشتريات", "btn.send": "إرسال", "btn.ticket": "إرسال إلى المحاسب",

    "qr.spec_label": "رمز QR المعتمد:",
    "qr.note": "حمولة TLV مشفّرة Base64 — تُقرأ تطبيقات التحقق الضريبي اسم المورد والرقم الضريبي والطابع الزمني والإجمالي والضريبة.",
    "qr.hash_label": "تجزئة الفاتورة:", "qr.copy": "نسخ الحمولة",

    "return.title": "حاسبة صافي الإقرار الضريبي", "return.tag": "ضريبة المبيعات − ضريبة المشتريات",
    "return.country": "الدولة", "return.period": "الفترة الضريبية", "return.refresh": "تحديث الحساب",
    "return.output": "ضريبة المبيعات المحصّلة", "return.input": "ضريبة المشتريات المدفوعة",
    "return.net": "صافي الضريبة المستحقة", "return.due": "آخر موعد للتقديم",
    "return.tab.sales": "سجل المبيعات", "return.tab.purchases": "سجل المشتريات",
    "return.fine": "تُخصم ضريبة المشتريات من ضريبة المبيعات لنفس الفترة. إن كانت المشتريات أكبر يظهر رصيد دائن يُرحَّل للفترة التالية.",
    "lcol.number": "رقم الفاتورة", "lcol.date": "التاريخ", "lcol.customer": "العميل", "lcol.supplier": "المورد",
    "lcol.net": "قبل الضريبة", "lcol.vat": "الضريبة", "lcol.total": "الإجمالي", "lcol.source": "المصدر",
    "ledger.empty.sales": "لا صفوف بعد — أصدر فاتورة واحفظها.",
    "ledger.empty.purchases": "لا صفوف بعد — امسح فاتورة مشتريات.",
    "ledger.delete": "حذف", "row.footer": "—",

    "scan.title": "ماسح الفواتير الذكي (صورة أو نص واتساب)", "scan.tag.simulation": "وضع المحاكاة",
    "scan.tag.ocr": "OCR فعلي",
    "scan.drop.title": "أفلت صورة فاتورة هنا", "scan.drop.or": "أو", "scan.drop.pick": "اختر صورة",
    "scan.drop.note": "PNG أو JPG أو WEBP أو PDF — حتى ٦ ميغابايت. استخراج الحقول ثم تراجعها قبل الحفظ.",
    "scan.demo": "تجربة صورة نموذجية", "scan.paste": "أو الصق نص الفواتير (واتساب / CSV)",
    "scan.ocr_title": "نتيجة قراءة الصورة", "scan.ocr_supplier": "المورد", "scan.ocr_date": "التاريخ",
    "scan.ocr_subtotal": "قبل الضريبة", "scan.ocr_tax": "الضريبة",
    "scan.totals.count": "عدد الفواتير", "scan.totals.total": "إجمالي المبالغ",
    "scan.totals.tax": "إجمالي الضريبة", "scan.totals.review": "تحتاج مراجعة",
    "scan.footnote": "المسح النصي يعمل على الخادم ولا يُخزَّن أي نص فاتورة على القرص.",
    "scol.supplier": "المورد", "scol.confidence": "الثقة",

    "assistant.title": "المساعد الضريبي الذكي", "assistant.tag": "قواعد معرفة خليجية · محلي",
    "assistant.greeting": "هلا بك! اسألني عن ضريبة القيمة المضافة، الفوترة الإلكترونية، أو مواعيد الإقرار في دول الخليج.",
    "assistant.placeholder": "اكتب سؤالك الضريبي…", "assistant.disclaimer": "المساعد يعتمد قواعد معرفة ثابتة يعرضها بوضوح، وليس استشارة ضريبية معتمدة.",
    "accountant.title": "التواصل مع المحاسب", "accountant.tag": "تذكرة لكل رسالة",
    "accountant.topic": "الموضوع", "accountant.message": "الرسالة", "accountant.empty": "لا رسائل بعد.",
    "news.title": "أخبار السوق والامتثال", "news.refresh": "تحديث", "news.none": "لا توجد أخبار محفوظة.",
    "checklist.title": "ملخص سريع", "checklist.tag": "آخر حالة",
    "check1": "راجع حقول الفاتورة قبل الإصدار: الاسم والرقم الضريبي والتاريخ.",
    "check2": "احفظ فواتير المبيعات لتظهر تلقائيًا في حساب الإقرار.",
    "check3": "أضف فواتير المشتريات من الماسح ليُخصم ضريبتها.",
    "check4": "أرشف الفواتير خمس سنوات على الأقل — شرط تدقيق في كل دول الخليج.",

    "chip.rates": "نسب الضريبة", "chip.deadlines": "مواعيد الإقرار", "chip.fields": "حقول الفاتورة",
    "chip.bulk": "المسح بالجملة", "chip.net": "صافي الإقرار",
    "chip.q.rates": "ما نسبة ضريبة القيمة المضافة في السعودية والإمارات؟",
    "chip.q.deadlines": "متى آخر موعد لتقديم الإقرار الضريبي؟",
    "chip.q.fields": "ما الحقول المطلوبة في الفاتورة الإلكترونية؟",
    "chip.q.bulk": "كيف أمسح دفعة فواتير كبيرة دفعة واحدة؟",
    "chip.q.net": "كيف أحسب صافي الإقرار؟",

    "plans.title": "الباقات وسعة مسح الفواتير", "plans.tag": "سعة شهرية فقط · بلا قيود لكل دقيقة",
    "plans.quota_note": "تُحسب السعة شهريًا فقط، مع سماحية تجاوز ١٠٪ تُستهلك تلقائيًا.",
    "plans.per_year": "سنة", "plans.scans": "فاتورة شهريًا", "plans.current": "الباقة الحالية", "plans.choose": "اختيار الباقة",

    "footer.product": "Gulf Tax & Accounting Suite — منتج Arab Templates",
    "footer.disclaimer": "معلومات إرشادية وليست استشارة قانونية أو ضريبية معتمدة.",

    "modal.title": "إعداداتك الضريبية", "modal.sub": "اختر الدولة والعملة واللغة — تُحفظ في متصفحك وتُستخدم في كل الحسابات والفواتير.",
    "modal.country": "الدولة", "modal.currency": "العملة المفضلة", "modal.lang": "اللغة الافتراضية",
    "modal.save": "حفظ وإغلاق", "modal.later": "لاحقًا",
    "modal.detected": "اكتشفنا أنك في {country} ({currency}) من منطقة {tz} — يمكنك تغيير ذلك.",
    "modal.detected.lang": "اكتشفنا الدولة من لغة متصفحك: {country} ({currency}) — يمكنك تغييرها.",
    "modal.saved": "حُفظت الإعدادات في هذا المتصفح.",
    "modal.facts": "نسبة الضريبة {rate}% · العملة {currency} · {authority}",

    "print.title": "فاتورة ضريبية", "print.bill_to": "فاتورة إلى", "print.invoice_no": "رقم الفاتورة",
    "print.date": "التاريخ", "print.currency": "العملة", "print.vat_no": "الرقم الضريبي",
    "print.footer": "فاتورة إلكترونية صادرة عن نظام الامتثال الضريبي الخليجي.",

    "note.legal": "الفاتورة الصادرة بعملة {currency} قانونيًا.",
    "note.converted": "المبالغ معروضة بـ{display} — محوّلة من {base} بسعر اليوم.",
    "note.rates_missing": "سعر الصرف لـ{currency} غير متاح — تُعرض المبالغ بعملة {base}.",
    "note.return_converted": "البطاقات معروضة بـ{display} ومحوّلة من {base}.",

    "msg.processing": "يتحقق الخادم من البيانات ويحسب الضريبة ويولّد رمز QR…",
    "msg.issued": "أُصدرت الفاتورة {number} — الإجمالي {total}.",
    "msg.saved": "حُفظت في سجل المبيعات.",
    "msg.qr_copied": "نُسخت حمولة QR إلى الحافظة.",
    "msg.qr_failed": "لم يسمح المتصفح بالنسخ.",
    "msg.qr_missing": "مكتبة segno غير مثبتة — يُعرض نص QR فقط.",
    "msg.invoice_required": "أصدر الفاتورة أولًا.",
    "msg.error": "تعذّر الإتمام: {error}",
    "msg.no_text": "الصق نص الفواتير أو أفلت ملفًا أولًا.",
    "msg.scan_working": "يُعالج النص على الخادم…",
    "msg.scanned": "تم مسح {count} فاتورة في {ms} ms",
    "msg.quota_used": " · استهلاك السعة {used}/{capacity}",
    "msg.quota_deferred": " · {deferred} فاتورة مؤجلة (سماحية الباقة)",
    "msg.sample_loaded": "حُمّل نموذج واتساب (٣ فواتير) — اضغط «امسح الفواتير».",
    "msg.sample_failed": "تعذّر تحميل النموذج.",
    "msg.added_purchases": "أُضيفت {count} فاتورة إلى سجل المشتريات — حدّث الإقرار لرؤية الخصم.",
    "msg.add_failed": "تعذّرت الإضافة: {error}",
    "msg.ocr_working": "جارٍ تحليل الصورة…",
    "msg.ocr_ready": "استُخرجت بيانات الفاتورة — راجعها ثم أضفها للسجل.",
    "msg.ocr_failed": "تعذّر تحليل الصورة: {error}",
    "msg.ocr_saved": "أُضيفت فاتورة {supplier} إلى سجل المشتريات.",
    "msg.confidence": "درجة الثقة {percent}% — راجع الحقول قبل الحفظ",
    "msg.ticket_required": "اكتب نص الرسالة أولًا.",
    "msg.ticket_sent": "رقم التذكرة {ticket} — {reply}",
    "msg.ticket_failed": "تعذّر الإرسال: {error}",
    "msg.return_failed": "تعذّر حساب الإقرار: {error}",
    "msg.delete_failed": "تعذّر الحذف: {error}",
    "msg.plan_selected": "الباقة النشطة: {name}",
    "msg.offline_ticker": "تعذّر تحميل أسعار العملات — تُستخدم آخر أسعار محفوظة.",
    "msg.news_failed": "تعذّر تحميل الأخبار.",
    "msg.assistant_failed": "تعذّر الوصول إلى المساعد: {error}",
    "msg.plans_failed": "تعذّر تحميل الباقات.",
    "msg.require_desc": "اكتب وصفًا للبند أولًا.",
    "msg.return_note_payable": "صافي الضريبة المستحقة للهيئة لهذه الفترة: {amount}. النسبة الفعلية {rate}%.",
    "msg.return_note_credit": "المشتريات أعلى من المبيعات — رصيد دائن {amount} يُرحَّل للفترة التالية.",
    "msg.return_note_zero": "لا مستحقات ولا رصيد لهذه الفترة.",
    "msg.quota_label": "استهلاك شهر {period} — باقة {plan}",
    "msg.quota_value": "{used} / {capacity} فاتورة",
    "msg.quota_remaining": "المتبقي: {remaining} فاتورة + سماحية {grace} — لا قيود لكل دقيقة.",
    "msg.quota_over": "تجاوزت السعة: {deferred} فاتورة مؤجلة، وسماحية {grace} استُهلكت.",

    "ph.seller_name": "شركة الأفق للتقنية", "ph.address": "الرياض — طريق الملك فهد",
    "ph.buyer_name": "مؤسسة النخيل التجارية", "ph.buyer_address": "جدة — حي الروضة",
    "ph.auto_number": "يُولّد تلقائيًا",
    "ph.scan": "المورد: شركة النخيل للتجارة\nالتاريخ: 2026-11-01\nالإجمالي قبل الضريبة: 1,000.00\nالضريبة (15%): 150.00\nالإجمالي: 1,150.00",
    "ph.topic": "إقرار الربع الثالث", "ph.message": "اشرح حالتك بإيجاز…",

    "currency.unit": "العملة"
  },
  en: {
    "page.title": "Gulf Tax & Accounting Suite — Arab Templates",
    "brand.name": "Gulf Tax Compliance", "brand.sub": "Gulf Tax & Accounting Suite",
    "ticker.loading": "Loading exchange rates…",
    "status.connecting": "Connecting…", "status.online": "Server connected", "status.offline": "Server unavailable",
    "nav.invoice": "E-invoices", "nav.return": "VAT return", "nav.scan": "Smart scanner",
    "nav.assistant": "Assistant & accountant", "nav.plans": "Plans",
    "controls.country": "Country", "controls.currency": "Currency", "controls.settings": "Settings",
    "hero.title": "One system for Gulf accounting and tax compliance",
    "hero.sub": "Issue e-invoices with a compliant QR code, calculate the VAT return automatically, and pull purchase invoices from an image or WhatsApp text — in Arabic and English.",
    "hero.stat.scanned": "invoices scanned in this session", "hero.stat.tax": "total VAT extracted",
    "hero.stat.net": "current net VAT", "hero.stat.news": "market updates available",

    "invoice.title": "Compliant e-invoice generator", "invoice.country": "Country of issue",
    "invoice.rate": "VAT rate %", "invoice.date": "Invoice date",
    "invoice.seller": "Seller details", "invoice.buyer": "Customer details",
    "invoice.seller.name": "Trade name", "invoice.seller.vat": "Tax number",
    "invoice.seller.address": "Address", "invoice.seller.email": "Email", "invoice.seller.phone": "Phone",
    "invoice.buyer.name": "Customer name", "invoice.buyer.vat": "Customer tax number (optional)",
    "invoice.buyer.address": "Address", "invoice.buyer.email": "Email", "invoice.number": "Invoice number",
    "invoice.items": "Invoice lines", "invoice.include_vat": "Prices include VAT",
    "invoice.add_item": "+ Add line",
    "invoice.footnote": "Totals and the QR payload are computed and encoded on the server with no external browser library, and nothing is stored until you press Save.",

    "col.no": "#", "col.desc": "Description", "col.qty": "Qty", "col.price": "Unit price",
    "col.discount": "Discount %", "col.net": "Net", "col.vat": "VAT", "col.total": "Total", "col.actions": "",

    "sum.subtotal": "Subtotal", "sum.discount": "Discount", "sum.vat": "VAT",
    "sum.grand": "Total due",
    "btn.issue": "Issue invoice with QR", "btn.print": "Print / PDF", "btn.save": "Save to sales ledger",
    "btn.new_invoice": "New invoice", "btn.scan": "Scan invoices", "btn.sample": "WhatsApp sample",
    "btn.export": "Export CSV", "btn.bulk": "Test 500 invoices", "btn.ocr_save": "Add to purchase ledger",
    "btn.add_all": "Add all results to the purchase ledger", "btn.send": "Send", "btn.ticket": "Send to accountant",

    "qr.spec_label": "Compliant QR:",
    "qr.note": "Base64-encoded TLV payload — tax validation apps read the seller name, tax number, timestamp, total and VAT from it.",
    "qr.hash_label": "Invoice hash:", "qr.copy": "Copy payload",

    "return.title": "Net VAT return calculator", "return.tag": "Output VAT − input VAT",
    "return.country": "Country", "return.period": "Tax period", "return.refresh": "Recalculate",
    "return.output": "Output VAT collected", "return.input": "Input VAT paid",
    "return.net": "Net VAT payable", "return.due": "Filing deadline",
    "return.tab.sales": "Sales ledger", "return.tab.purchases": "Purchase ledger",
    "return.fine": "Input VAT is deducted from output VAT for the same period. When purchases exceed sales a credit balance is carried forward.",
    "lcol.number": "Invoice no.", "lcol.date": "Date", "lcol.customer": "Customer", "lcol.supplier": "Supplier",
    "lcol.net": "Net", "lcol.vat": "VAT", "lcol.total": "Total", "lcol.source": "Source",
    "ledger.empty.sales": "No rows yet — issue and save an invoice.",
    "ledger.empty.purchases": "No rows yet — scan a purchase invoice.",
    "ledger.delete": "Delete", "row.footer": "—",

    "scan.title": "Smart invoice scanner (image or WhatsApp text)", "scan.tag.simulation": "Simulation mode",
    "scan.tag.ocr": "Real OCR",
    "scan.drop.title": "Drop an invoice image here", "scan.drop.or": "or", "scan.drop.pick": "choose a file",
    "scan.drop.note": "PNG, JPG, WEBP or PDF — up to 6 MB. Fields are extracted for you to review before saving.",
    "scan.demo": "Try a sample image", "scan.paste": "Or paste invoice text (WhatsApp / CSV)",
    "scan.ocr_title": "Image extraction result", "scan.ocr_supplier": "Supplier", "scan.ocr_date": "Date",
    "scan.ocr_subtotal": "Net", "scan.ocr_tax": "VAT",
    "scan.totals.count": "Invoices", "scan.totals.total": "Total amount",
    "scan.totals.tax": "Total VAT", "scan.totals.review": "Need review",
    "scan.footnote": "Text scanning runs on the server and no raw invoice text is written to disk.",
    "scol.supplier": "Supplier", "scol.confidence": "Confidence",

    "assistant.title": "Smart tax assistant", "assistant.tag": "Gulf knowledge base · local",
    "assistant.greeting": "Welcome! Ask me about VAT rates, e-invoicing, filing deadlines or penalties in the Gulf.",
    "assistant.placeholder": "Type your tax question…", "assistant.disclaimer": "The assistant uses a fixed, transparent knowledge base — it is not certified tax advice.",
    "accountant.title": "Talk to an accountant", "accountant.tag": "A ticket per message",
    "accountant.topic": "Subject", "accountant.message": "Message", "accountant.empty": "No messages yet.",
    "news.title": "Market & compliance news", "news.refresh": "Refresh", "news.none": "No saved news yet.",
    "checklist.title": "Quick checklist", "checklist.tag": "Latest state",
    "check1": "Check invoice fields before issuing: name, tax number and date.",
    "check2": "Save sales invoices so they show up in the return automatically.",
    "check3": "Add purchase invoices from the scanner so their VAT is deducted.",
    "check4": "Archive invoices for at least five years — an audit requirement across the Gulf.",

    "chip.rates": "VAT rates", "chip.deadlines": "Filing deadlines", "chip.fields": "Invoice fields",
    "chip.bulk": "Bulk scanning", "chip.net": "Net VAT",
    "chip.q.rates": "What are the VAT rates in Saudi Arabia and the UAE?",
    "chip.q.deadlines": "When is the VAT return due?",
    "chip.q.fields": "Which fields are required on an e-invoice?",
    "chip.q.bulk": "How do I scan a large batch of invoices?",
    "chip.q.net": "How is net VAT calculated?",

    "plans.title": "Plans and scanning capacity", "plans.tag": "Monthly capacity only · no per-minute limits",
    "plans.quota_note": "Capacity is monthly with a 10% overflow grace used automatically.",
    "plans.per_year": "year", "plans.scans": "invoices per month", "plans.current": "Current plan", "plans.choose": "Choose plan",

    "footer.product": "Gulf Tax & Accounting Suite — an Arab Templates product",
    "footer.disclaimer": "Guidance only — not certified legal or tax advice.",

    "modal.title": "Your tax setup", "modal.sub": "Choose your country, currency and language — saved in this browser and used by every calculation and invoice.",
    "modal.country": "Country", "modal.currency": "Preferred currency", "modal.lang": "Default language",
    "modal.save": "Save and close", "modal.later": "Later",
    "modal.detected": "We detected {country} ({currency}) from timezone {tz} — you can change it.",
    "modal.detected.lang": "We detected {country} ({currency}) from your browser language — you can change it.",
    "modal.saved": "Settings saved in this browser.",
    "modal.facts": "VAT {rate}% · Currency {currency} · {authority}",

    "print.title": "Tax Invoice", "print.bill_to": "Bill to", "print.invoice_no": "Invoice no.",
    "print.date": "Date", "print.currency": "Currency", "print.vat_no": "Tax number",
    "print.footer": "E-invoice issued by the Gulf Tax Compliance system.",

    "note.legal": "Invoice issued legally in {currency}.",
    "note.converted": "Amounts shown in {display} — converted from {base} at today's rate.",
    "note.rates_missing": "No exchange rate for {currency} — amounts are shown in {base}.",
    "note.return_converted": "Cards are shown in {display}, converted from {base}.",

    "msg.processing": "The server is validating, computing VAT and generating the QR code…",
    "msg.issued": "Invoice {number} issued — total {total}.",
    "msg.saved": "Saved to the sales ledger.",
    "msg.qr_copied": "QR payload copied to the clipboard.",
    "msg.qr_failed": "The browser blocked clipboard access.",
    "msg.qr_missing": "segno is not installed — showing the QR payload only.",
    "msg.invoice_required": "Issue the invoice first.",
    "msg.error": "Could not complete: {error}",
    "msg.no_text": "Paste invoice text or drop a file first.",
    "msg.scan_working": "Processing the text on the server…",
    "msg.scanned": "Scanned {count} invoices in {ms} ms",
    "msg.quota_used": " · capacity used {used}/{capacity}",
    "msg.quota_deferred": " · {deferred} invoices deferred (plan grace)",
    "msg.sample_loaded": "WhatsApp sample loaded (3 invoices) — press Scan invoices.",
    "msg.sample_failed": "Could not load the sample.",
    "msg.added_purchases": "{count} invoices added to the purchase ledger — refresh the return to see the deduction.",
    "msg.add_failed": "Could not add: {error}",
    "msg.ocr_working": "Analyzing the image…",
    "msg.ocr_ready": "Invoice fields extracted — review them, then add to the ledger.",
    "msg.ocr_failed": "Could not analyze the image: {error}",
    "msg.ocr_saved": "Invoice from {supplier} added to the purchase ledger.",
    "msg.confidence": "Confidence {percent}% — review the fields before saving",
    "msg.ticket_required": "Enter your message first.",
    "msg.ticket_sent": "Ticket {ticket} — {reply}",
    "msg.ticket_failed": "Could not send: {error}",
    "msg.return_failed": "Could not calculate the return: {error}",
    "msg.delete_failed": "Could not delete: {error}",
    "msg.plan_selected": "Active plan: {name}",
    "msg.offline_ticker": "Rates unavailable — using the last saved snapshot.",
    "msg.news_failed": "Could not load the news.",
    "msg.assistant_failed": "Could not reach the assistant: {error}",
    "msg.plans_failed": "Could not load the plans.",
    "msg.require_desc": "Enter a line description first.",
    "msg.return_note_payable": "Net VAT payable to the authority for this period: {amount}. Effective rate {rate}%.",
    "msg.return_note_credit": "Purchases exceed sales — a credit balance of {amount} is carried forward.",
    "msg.return_note_zero": "Nothing payable and no credit for this period.",
    "msg.quota_label": "{period} usage — {plan} plan",
    "msg.quota_value": "{used} / {capacity} invoices",
    "msg.quota_remaining": "Remaining: {remaining} invoices + {grace} grace — no per-minute limits.",
    "msg.quota_over": "Capacity exceeded: {deferred} invoices deferred and the {grace} grace used.",

    "ph.seller_name": "Gulf Tech Solutions", "ph.address": "Riyadh — King Fahd Road",
    "ph.buyer_name": "Al Nakheel Trading", "ph.buyer_address": "Jeddah — Al Rawdah",
    "ph.auto_number": "generated automatically",
    "ph.scan": "Supplier: Al Nakheel Trading\nDate: 2026-11-01\nNet: 1,000.00\nVAT (15%): 150.00\nTotal: 1,150.00",
    "ph.topic": "Q3 VAT return", "ph.message": "Describe your case briefly…",

    "currency.unit": "Currency"
  }
};

const PROFILE_KEY = "at_gulf_profile";
const ACCOUNT_KEY = "at_gulf_account";

const state = {
  lang: "ar",
  country: "SA",
  currency: "SAR",
  countries: [],
  currencies: [],
  rates: { SAR: 1 },
  ratesStale: false,
  ratesAt: "",
  plans: [],
  quota: null,
  items: [],
  invoice: null,
  scan: null,
  ocr: null,
  ledger: { sales: [], purchases: [] },
  ledgerTab: "sales",
  totals: { scanned: 0, tax: 0, taxCurrency: "SAR" },
  detected: null,
  profileSaved: false,
  ret: null,
};

const ACCOUNT = (localStorage.getItem(ACCOUNT_KEY) || (function () {
  const id = "acc-" + Math.random().toString(36).slice(2, 9);
  localStorage.setItem(ACCOUNT_KEY, id);
  return id;
})());

function t(key, vars) {
  const dict = I18N[state.lang] || I18N.ar;
  let text = dict[key] ?? I18N.ar[key] ?? key;
  if (vars) text = text.replace(/\{(\w+)\}/g, (m, k) => (vars[k] === undefined || vars[k] === null ? m : vars[k]));
  return text;
}

const fmtNum = (value, digits = 0) => new Intl.NumberFormat(state.lang === "en" ? "en-US" : "ar-SA", {
  minimumFractionDigits: digits, maximumFractionDigits: digits,
}).format(Number(value || 0));

async function api(path, options) {
  const res = await fetch(path, { cache: "no-store", ...(options || {}) });
  let data = null;
  try { data = await res.json(); } catch (err) { data = null; }
  if (!res.ok) throw new Error((data && data.error) || ("HTTP " + res.status));
  return data || {};
}

/* ================== العملات ================== */
function currencyInfo(code) {
  return state.currencies.find((c) => c.code === code) ||
    { code: code, symbol: code, decimals: 2, name: code, name_en: code };
}

function rateOf(code) {
  if (!code) return null;
  if (code === "SAR") return 1;
  const value = Number(state.rates[code]);
  return Number.isFinite(value) && value > 0 ? value : null;
}

function canConvert(from, to) {
  return rateOf(from) != null && rateOf(to) != null;
}

function convert(amount, from, to) {
  const value = Number(amount) || 0;
  if (!from || !to || from === to) return value;
  if (!canConvert(from, to)) return value;
  return value / rateOf(from) * rateOf(to);
}

function symbolFor(code) {
  const info = currencyInfo(code);
  return state.lang === "en" ? code : (info.symbol || code);
}

/** مبلغ بعملة العرض المفضلة (مع تحويل إن لزم). */
function money(amount, from) {
  const base = from || state.currency;
  const display = state.currency;
  const value = convert(amount, base, display);
  return `${fmtNum(value, 2)} ${symbolFor(display)}`;
}

/** مبلغ بعملة الفاتورة القانونية دون تحويل. */
function legalMoney(amount, currency) {
  return `${fmtNum(amount, 2)} ${symbolFor(currency || state.countryCurrency() || "SAR")}`;
}

function countryBy(code) {
  return state.countries.find((c) => c.code === code) || state.countries[0] || null;
}

state.countryCurrency = function () {
  const meta = countryBy(state.country);
  return meta ? meta.currency : "SAR";
};

/* ================== الملف الشخصي ================== */
function readProfile() {
  try {
    const raw = JSON.parse(localStorage.getItem(PROFILE_KEY) || "null");
    return raw && typeof raw === "object" ? raw : null;
  } catch (err) { return null; }
}

function writeProfile() {
  localStorage.setItem(PROFILE_KEY, JSON.stringify({
    country: state.country, currency: state.currency, lang: state.lang,
    savedAt: new Date().toISOString(),
  }));
  state.profileSaved = true;
}

/* ================== الترجمة والتطبيق ================== */
function applyStaticTexts() {
  document.documentElement.lang = state.lang;
  document.documentElement.dir = state.lang === "ar" ? "rtl" : "ltr";
  document.body.classList.toggle("ltr", state.lang === "en");
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (key) el.textContent = t(key);
  });
  document.querySelectorAll("[data-i18n-ph]").forEach((el) => {
    el.setAttribute("placeholder", t(el.getAttribute("data-i18n-ph")));
  });
  document.querySelectorAll("[data-i18n-aria]").forEach((el) => {
    el.setAttribute("aria-label", t(el.getAttribute("data-i18n-aria")));
  });
  $("langToggle").textContent = state.lang === "ar" ? "English" : "العربية";
  $("langToggle").setAttribute("title", state.lang === "ar" ? "Switch to English" : "التبديل إلى العربية");
  document.querySelectorAll(".lang-option").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.lang === state.lang);
  });
  renderItemsHead();
  renderScanHead();
  renderSuggestions();
  renderPlans();
  renderLedger();
  renderOcrMode();
  renderCurrencyNotes();
  renderChatGreeting();
  if (state.invoice) { fillQrBox(state.invoice); fillPrintDoc(state.invoice); }
}

async function setLanguage(lang, { persist = true, reload = true } = {}) {
  state.lang = lang === "en" ? "en" : "ar";
  applyStaticTexts();
  if (persist) writeProfile();
  if (!reload) return;
  await refreshCountries();
  applyCountry(state.country, { keepCurrency: true, reload: false });
  if (state.invoice) { fillQrBox(state.invoice); fillPrintDoc(state.invoice); }
  await Promise.all([loadPlans(), loadNews(), loadReturn(), loadQuota(), loadTickets()]);
  renderRatesTicker();
}

async function refreshCountries() {
  const data = await api("/api/countries?lang=" + state.lang);
  state.countries = data.countries || [];
  state.currencies = data.currencies || [];
  if (!state.countries.some((c) => c.code === state.country)) state.country = state.countries[0]?.code || "SA";
  if (!state.currencies.some((c) => c.code === state.currency)) {
    state.currency = (countryBy(state.country) || {}).currency || "SAR";
  }
  fillCountrySelects();
  fillCurrencySelects();
}

function fillCountrySelects() {
  const options = state.countries.map((c) => `<option value="${esc(c.code)}">${esc(c.name)} — ${fmtNum(c.vat_rate)}%</option>`).join("");
  ["countrySelect", "invCountry", "retCountry", "obCountry"].forEach((id) => {
    const el = $(id);
    if (!el) return;
    el.innerHTML = options;
    el.value = state.country;
  });
}

function fillCurrencySelects() {
  const options = state.currencies.map((c) => {
    const label = state.lang === "en" ? `${c.code} — ${c.name}` : `${c.code} — ${c.name} (${c.symbol})`;
    return `<option value="${esc(c.code)}">${esc(label)}</option>`;
  }).join("");
  ["currencySelect", "obCurrency"].forEach((id) => {
    const el = $(id);
    if (!el) return;
    el.innerHTML = options;
    el.value = state.currency;
  });
}

/* ================== الدولة والعملة ================== */
function applyCountry(code, { keepCurrency = false, reload = true, persist = true } = {}) {
  const meta = countryBy(code) || countryBy("SA");
  if (!meta) return;
  state.country = meta.code;
  if (!keepCurrency || !state.currency) state.currency = meta.currency;
  ["countrySelect", "invCountry", "retCountry", "obCountry"].forEach((id) => { const el = $(id); if (el) el.value = meta.code; });
  $("invRate").value = meta.vat_rate;
  $("sellerVatLabel").textContent = `${t("invoice.seller.vat")} — ${meta.tax_no_hint}`;
  $("invSpec").textContent = String(meta.qr_spec || "").split("—")[0].trim();
  $("authorityNote").textContent = `${meta.name} · ${meta.authority} · ${meta.filing}`;
  fillCurrencySelects();
  $("currencySelect").value = state.currency;
  $("obCurrency").value = state.currency;
  fillPeriods();
  recompute();
  renderCurrencyNotes();
  renderPlans();
  if (persist) writeProfile();
  if (reload) loadReturn();
}

function applyCurrency(code, { persist = true, reload = true } = {}) {
  if (!state.currencies.some((c) => c.code === code)) return;
  state.currency = code;
  ["currencySelect", "obCurrency"].forEach((id) => { const el = $(id); if (el) el.value = code; });
  renderCurrencyNotes();
  renderPlans();
  renderQuota();
  loadQuota();
  recompute();
  if (persist) writeProfile();
  if (reload) loadReturn();
}

function renderCurrencyNotes() {
  const meta = countryBy(state.country) || {};
  const legal = meta.currency || "SAR";
  const converted = state.currency !== legal;
  const missing = converted && !canConvert(legal, state.currency);
  const note = missing
    ? t("note.rates_missing", { currency: symbolFor(state.currency), base: symbolFor(legal) })
    : converted
      ? t("note.converted", { display: symbolFor(state.currency), base: symbolFor(legal) })
      : t("note.legal", { currency: symbolFor(legal) });
  const el = $("currencyNote");
  if (el) el.textContent = note;
  const ret = $("returnConvertNote");
  if (ret) ret.textContent = converted ? t("note.return_converted", { display: symbolFor(state.currency), base: symbolFor(legal) }) : "";
}

/* ================== التبويبات ================== */
function showView(name) {
  document.querySelectorAll(".view").forEach((v) => v.classList.toggle("active", v.id === "view-" + name));
  document.querySelectorAll("#tabsNav .tab").forEach((tab) => tab.classList.toggle("active", tab.dataset.view === name));
  if (name === "return") loadReturn();
  if (name === "assistant") { loadNews(); loadTickets(); }
  if (name === "plans") loadPlans();
  window.scrollTo({ top: 0, behavior: "smooth" });
}
document.querySelectorAll("#tabsNav .tab").forEach((tab) => {
  tab.addEventListener("click", () => showView(tab.dataset.view));
});

/* ================== الحالة والأسعار ================== */
async function loadHealth() {
  try {
    const data = await api("/api/health");
    $("statusText").textContent = data.engine ? t("status.online") : t("status.online");
    document.querySelector("#statusPill .dot").className = "dot ok";
  } catch (err) {
    $("statusText").textContent = t("status.offline");
    document.querySelector("#statusPill .dot").className = "dot bad";
  }
}

async function loadRates() {
  try {
    const data = await api("/api/rates");
    const rates = { SAR: 1 };
    Object.keys(data.rates || {}).forEach((code) => {
      const value = Number(data.rates[code]);
      if (Number.isFinite(value) && value > 0) rates[code] = value;
    });
    state.rates = rates;
    state.ratesStale = !!data.stale;
    state.ratesAt = data.updated_at || "";
    renderRatesTicker();
    recompute();
    renderPlans();
    if (state.ret) renderReturn(state.ret);
  } catch (err) {
    $("tickerTrack").innerHTML = `<span class="ticker-item">${esc(t("msg.offline_ticker"))}</span>`;
  }
}

function renderRatesTicker() {
  const codes = Object.keys(state.rates).filter((code) => code !== "SAR");
  if (!codes.length) {
    $("tickerTrack").innerHTML = `<span class="ticker-item">${esc(t("msg.offline_ticker"))}</span>`;
    return;
  }
  const items = codes.map((code) => {
    const perSar = Number(state.rates[code]);
    const perUnit = perSar > 0 ? 1 / perSar : 0;
    return `<span class="ticker-item"><b>${esc(code)}</b> ${fmtNum(perUnit, 3)} ${esc(symbolFor(code))}</span>`;
  }).join("");
  $("tickerTrack").innerHTML = items + `<span class="ticker-item">SAR · ${esc(state.ratesAt || "")}</span>`;
}

async function loadNews() {
  try {
    const data = await api("/api/news?lang=" + state.lang);
    const items = data.items || [];
    $("statNews").textContent = fmtNum(items.length);
    $("newsList").innerHTML = items.length ? items.map((n) => `
      <article class="news">
        <div class="meta"><span class="tag-sm">${esc(n.tag || "")}</span><span>${esc(n.date || "")}</span></div>
        <h3>${esc(n.title)}</h3>
        <p>${esc(n.summary)}</p>
        ${n.action ? `<div class="action">✔ ${esc(n.action)}</div>` : ""}
      </article>`).join("") : `<p class="fine">${esc(t("news.none"))}</p>`;
    $("newsMeta").textContent = data.updated_at || "—";
  } catch (err) {
    $("newsList").innerHTML = `<p class="fine">${esc(t("msg.news_failed"))}</p>`;
  }
}

/* ================== الفواتير ================== */
function blankItem() { return { description: "", quantity: 1, unit_price: 0, discount: 0 }; }

function renderItemsHead() {
  $("itemsHead").innerHTML = `<tr>
    <th>${esc(t("col.no"))}</th><th>${esc(t("col.desc"))}</th><th>${esc(t("col.qty"))}</th>
    <th>${esc(t("col.price"))}</th><th>${esc(t("col.discount"))}</th><th>${esc(t("col.net"))}</th>
    <th>${esc(t("col.vat"))}</th><th>${esc(t("col.total"))}</th><th></th></tr>`;
  $("pItemsHead").innerHTML = `<tr>
    <th>${esc(t("col.desc"))}</th><th>${esc(t("col.qty"))}</th><th>${esc(t("col.price"))}</th>
    <th>${esc(t("col.discount"))}</th><th>${esc(t("col.net"))}</th><th>${esc(t("col.vat"))}</th>
    <th>${esc(t("col.total"))}</th></tr>`;
}

function renderItems() {
  renderItemsHead();
  $("itemsBody").innerHTML = state.items.map((item, index) => `
    <tr data-row="${index}">
      <td>${fmtNum(index + 1)}</td>
      <td><input class="cell" data-f="description" type="text" value="${esc(item.description)}" placeholder="${esc(t("col.desc"))}"></td>
      <td><input class="cell narrow" data-f="quantity" type="number" min="0" step="1" value="${esc(item.quantity)}"></td>
      <td><input class="cell narrow" data-f="unit_price" type="number" min="0" step="0.01" value="${esc(item.unit_price)}"></td>
      <td><input class="cell narrow" data-f="discount" type="number" min="0" max="100" step="1" value="${esc(item.discount)}"></td>
      <td class="cell-out" data-out="net">—</td>
      <td class="cell-out" data-out="tax">—</td>
      <td class="cell-out strong" data-out="total">—</td>
      <td><button class="link danger" data-remove="${index}" type="button" aria-label="${esc(t("ledger.delete"))}">✕</button></td>
    </tr>`).join("");
  $("itemsBody").querySelectorAll("input[data-f]").forEach((input) => {
    input.addEventListener("input", (e) => {
      const row = e.target.closest("tr");
      const item = state.items[Number(row.dataset.row)];
      item[e.target.dataset.f] = e.target.value;
      recompute();
    });
  });
  $("itemsBody").querySelectorAll("[data-remove]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.items.splice(Number(btn.dataset.remove), 1);
      if (!state.items.length) state.items.push(blankItem());
      renderItems();
      recompute();
    });
  });
  recompute();
}

function computeClient() {
  const rate = Number($("invRate").value || 0) / 100;
  const includeVat = $("incVat").checked;
  let subtotal = 0, discount = 0, tax = 0;
  const rows = state.items.map((item) => {
    const qty = Math.max(0, Number(item.quantity) || 0);
    const price = Math.max(0, Number(item.unit_price) || 0);
    const discPct = Math.min(100, Math.max(0, Number(item.discount) || 0));
    const gross = qty * price;
    const discAmt = gross * discPct / 100;
    const netBase = gross - discAmt;
    let net, lineTax;
    if (includeVat && rate > 0) { net = netBase / (1 + rate); lineTax = netBase - net; }
    else { net = netBase; lineTax = net * rate; }
    net = Math.round(net * 100) / 100;
    lineTax = Math.round(lineTax * 100) / 100;
    subtotal += net; discount += discAmt; tax += lineTax;
    return { net, lineTax, total: Math.round((net + lineTax) * 100) / 100 };
  });
  return {
    rows, subtotal: Math.round(subtotal * 100) / 100, discount: Math.round(discount * 100) / 100,
    tax: Math.round(tax * 100) / 100, total: Math.round((subtotal + tax) * 100) / 100,
  };
}

function recompute() {
  const result = computeClient();
  const legal = (countryBy(state.country) || {}).currency || "SAR";
  state.items.forEach((item, index) => {
    const row = $("itemsBody").querySelector(`tr[data-row="${index}"]`);
    if (!row || !result.rows[index]) return;
    Object.keys({ net: 1, tax: 1, total: 1 }).forEach((key) => {
      const cell = row.querySelector(`[data-out="${key}"]`);
      if (cell) cell.textContent = fmtNum(result.rows[index][key === "tax" ? "lineTax" : key], 2);
    });
  });
  $("sumSubtotal").textContent = legalMoney(result.subtotal, legal);
  $("sumDiscount").textContent = legalMoney(result.discount, legal);
  $("sumTax").textContent = legalMoney(result.tax, legal);
  $("sumTotal").textContent = legalMoney(result.total, legal);
}
$("addItem").addEventListener("click", () => { state.items.push(blankItem()); renderItems(); });
$("incVat").addEventListener("change", recompute);
$("invRate").addEventListener("input", recompute);

function invoicePayload(save) {
  return {
    account: ACCOUNT, lang: state.lang, country: state.country,
    vat_rate: $("invRate").value, date: $("invDate").value || new Date().toISOString().slice(0, 10),
    number: $("invNumber").value.trim(), prices_include_vat: $("incVat").checked, save: !!save,
    seller: {
      name: $("sellerName").value, vat_number: $("sellerVat").value, address: $("sellerAddress").value,
      email: $("sellerEmail").value, phone: $("sellerPhone").value,
    },
    buyer: {
      name: $("buyerName").value, vat_number: $("buyerVat").value,
      address: $("buyerAddress").value, email: $("buyerEmail").value,
    },
    items: state.items.filter((item) => String(item.description).trim()),
  };
}

function setInvMsg(text, kind) {
  const el = $("invMsg");
  el.className = "msg " + (kind || "");
  el.textContent = text || "";
}

async function issueInvoice(save) {
  const button = save ? $("saveInvBtn") : $("issueBtn");
  const label = button.textContent;
  button.disabled = true;
  button.textContent = "…";
  setInvMsg(t("msg.processing"));
  try {
    const inv = await api("/api/einvoice", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(invoicePayload(save)),
    });
    state.invoice = inv;
    fillQrBox(inv);
    fillPrintDoc(inv);
    $("printBtn").disabled = false;
    $("saveInvBtn").disabled = false;
    let message = t("msg.issued", { number: inv.number, total: legalMoney(inv.total, inv.currency) });
    if (save && inv.saved) message += " " + t("msg.saved");
    if ((inv.notes || []).length) message += " " + inv.notes.join(" ");
    setInvMsg(message, "ok");
    if (save && inv.saved) {
      state.totals.scanned += 1;
      $("statInvoices").textContent = fmtNum(state.totals.scanned);
      loadReturn();
    }
  } catch (err) {
    setInvMsg(t("msg.error", { error: err.message }), "bad");
  } finally {
    button.disabled = false;
    button.textContent = label;
  }
}

$("issueBtn").addEventListener("click", () => issueInvoice(false));
$("saveInvBtn").addEventListener("click", () => issueInvoice(true));
$("printBtn").addEventListener("click", () => { if (state.invoice) window.print(); });

$("resetInvBtn").addEventListener("click", () => {
  ["sellerAddress", "sellerEmail", "sellerPhone", "buyerName", "buyerVat", "buyerAddress", "buyerEmail", "invNumber"].forEach((id) => { $(id).value = ""; });
  state.items = [blankItem()];
  state.invoice = null;
  $("qrBox").hidden = true;
  $("printBtn").disabled = true;
  $("saveInvBtn").disabled = true;
  $("invDate").value = new Date().toISOString().slice(0, 10);
  renderItems();
  setInvMsg("");
});

function fillQrBox(inv) {
  $("qrBox").hidden = false;
  $("qrImg").innerHTML = inv.qr && inv.qr.svg ? inv.qr.svg : `<p class="fine">${esc(t("msg.qr_missing"))}</p>`;
  const countryMeta = countryBy((inv.country || {}).code) || {};
  $("qrSpec").textContent = countryMeta.qr_spec || (inv.qr && inv.qr.spec) || "—";
  $("qrPayload").textContent = (inv.qr && inv.qr.payload) || "—";
  $("invHash").textContent = inv.hash || "—";
}

$("copyQrBtn").addEventListener("click", async () => {
  if (!state.invoice) { setInvMsg(t("msg.invoice_required"), "bad"); return; }
  try {
    await navigator.clipboard.writeText(state.invoice.qr.payload);
    setInvMsg(t("msg.qr_copied"), "ok");
  } catch (err) { setInvMsg(t("msg.qr_failed"), "bad"); }
});

function fillPrintDoc(inv) {
  $("pSeller").textContent = inv.seller.name;
  $("pSellerAddress").textContent = inv.seller.address || "";
  $("pSellerVat").textContent = inv.seller.vat_number;
  $("pSellerContact").textContent = [inv.seller.email, inv.seller.phone].filter(Boolean).join(" · ");
  $("pCountry").textContent = inv.country.name + " — " + inv.country.authority;
  $("pNumber").textContent = inv.number;
  $("pDate").textContent = inv.issued_at;
  $("pCurrency").textContent = `${inv.currency} (${symbolFor(inv.currency)})`;
  $("pBuyer").textContent = inv.buyer.name + (inv.buyer.address ? " — " + inv.buyer.address : "");
  $("pBuyerVat").textContent = inv.buyer.vat_number || "";
  $("pItems").innerHTML = inv.items.map((item) => `<tr>
      <td>${esc(item.description)}</td><td>${fmtNum(item.quantity, 2)}</td><td>${fmtNum(item.unit_price, 2)}</td>
      <td>${fmtNum(item.discount_amount, 2)}</td><td>${fmtNum(item.net, 2)}</td>
      <td>${fmtNum(item.tax, 2)}</td><td>${fmtNum(item.total, 2)}</td></tr>`).join("");
  $("pSubtotal").textContent = legalMoney(inv.subtotal, inv.currency);
  $("pRate").textContent = fmtNum(inv.vat_rate);
  $("pTax").textContent = legalMoney(inv.tax, inv.currency);
  $("pTotal").textContent = legalMoney(inv.total, inv.currency);
  $("pQr").innerHTML = inv.qr && inv.qr.svg ? inv.qr.svg : "";
  $("pHref").textContent = (inv.qr && inv.qr.payload) || "";
  $("pHash").textContent = inv.hash;
  $("pSpec").textContent = countryBy((inv.country || {}).code)?.qr_spec || (inv.qr && inv.qr.spec) || "";
}

/* ================== الإقرار الضريبي ================== */
function fillPeriods() {
  const meta = countryBy(state.country) || {};
  const quarterly = meta.period === "quarterly";
  const out = [];
  const cursor = new Date();
  cursor.setDate(1);
  for (let i = 0; i < 24 && out.length < 8; i++) {
    const key = cursor.toISOString().slice(0, 7);
    if (!quarterly || Number(key.slice(5, 7)) % 3 === 0) out.push(key);
    cursor.setMonth(cursor.getMonth() - 1);
  }
  const current = new Date().toISOString().slice(0, 7);
  $("retPeriod").innerHTML = out.map((p) => `<option value="${p}">${p}</option>`).join("");
  if (out.includes(current)) $("retPeriod").value = current;
}

async function loadReturn() {
  const period = $("retPeriod").value;
  if (!period) return;
  try {
    const tr = await api(`/api/taxreturn?account=${encodeURIComponent(ACCOUNT)}&country=${encodeURIComponent(state.country)}&period=${encodeURIComponent(period)}&lang=${state.lang}`);
    state.ret = tr;
    renderReturn(tr);
  } catch (err) {
    $("returnNote").textContent = t("msg.return_failed", { error: err.message });
  }
}

function renderReturn(tr) {
  const base = tr.currency || "SAR";
  $("kpiOutput").textContent = money(tr.output_tax, base);
  $("kpiOutputSub").textContent = `${fmtNum(tr.sales_count)} · ${money(tr.taxable_sales, base)}`;
  $("kpiInput").textContent = money(tr.input_tax, base);
  $("kpiInputSub").textContent = `${fmtNum(tr.purchases_count)} · ${money(tr.taxable_purchases, base)}`;
  $("kpiNet").textContent = money(tr.net, base);
  $("kpiNet").className = tr.net > 0 ? "due" : "credit";
  $("kpiStatus").textContent = tr.status + (tr.credit ? ` (+${money(tr.credit, base)})` : "");
  $("kpiDue").textContent = tr.due.due;
  $("kpiDueNote").textContent = tr.due.note;
  $("returnNote").textContent = tr.net > 0
    ? t("msg.return_note_payable", { amount: money(tr.net, base), rate: fmtNum(tr.effective_rate, 2) })
    : tr.net < 0
      ? t("msg.return_note_credit", { amount: money(tr.credit, base) })
      : t("msg.return_note_zero");
  $("statNet").textContent = money(tr.net, base);
  state.ledger = { sales: tr.sales || [], purchases: tr.purchases || [] };
  $("countSales").textContent = fmtNum(tr.sales_count);
  $("countPurchases").textContent = fmtNum(tr.purchases_count);
  renderLedger();
  renderCurrencyNotes();
}

$("refreshReturn").addEventListener("click", loadReturn);
$("retPeriod").addEventListener("change", loadReturn);

document.querySelectorAll("[data-ledger]").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("[data-ledger]").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    state.ledgerTab = btn.dataset.ledger;
    renderLedger();
  });
});

function renderLedger() {
  const kind = state.ledgerTab;
  const rows = state.ledger[kind] || [];
  $("ledgerHead").innerHTML = kind === "sales"
    ? `<tr><th>${esc(t("lcol.number"))}</th><th>${esc(t("lcol.date"))}</th><th>${esc(t("lcol.customer"))}</th><th>${esc(t("lcol.net"))}</th><th>${esc(t("lcol.vat"))}</th><th>${esc(t("lcol.total"))}</th><th></th></tr>`
    : `<tr><th>${esc(t("lcol.supplier"))}</th><th>${esc(t("lcol.date"))}</th><th>${esc(t("lcol.net"))}</th><th>${esc(t("lcol.vat"))}</th><th>${esc(t("lcol.total"))}</th><th>${esc(t("lcol.source"))}</th><th></th></tr>`;
  if (!rows.length) {
    $("ledgerBody").innerHTML = `<tr><td colspan="7" class="fine">${esc(t(kind === "sales" ? "ledger.empty.sales" : "ledger.empty.purchases"))}</td></tr>`;
    return;
  }
  const baseCountry = state.country;
  $("ledgerBody").innerHTML = rows.map((row) => {
    const rowCurrency = row.currency || (row.country ? (countryBy(row.country) || {}).currency : "") || countryBy(baseCountry)?.currency || "SAR";
    const del = `<button class="link danger" data-del="${esc(row.id)}" type="button">${esc(t("ledger.delete"))}</button>`;
    return kind === "sales"
      ? `<tr><td class="mono">${esc(row.number || "—")}</td><td>${esc(row.date || "—")}</td><td>${esc(row.buyer || "—")}</td>
         <td>${money(row.subtotal, rowCurrency)}</td><td>${money(row.tax, rowCurrency)}</td><td class="strong">${money(row.total, rowCurrency)}</td><td>${del}</td></tr>`
      : `<tr><td>${esc(row.supplier || "—")}</td><td>${esc(row.date || "—")}</td>
         <td>${money(row.subtotal, rowCurrency)}</td><td>${money(row.tax, rowCurrency)}</td><td class="strong">${money(row.total, rowCurrency)}</td>
         <td class="fine">${esc(row.source || "")}</td><td>${del}</td></tr>`;
  }).join("");
  $("ledgerBody").querySelectorAll("[data-del]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        await api(`/api/ledger/${kind}/${encodeURIComponent(btn.dataset.del)}?account=${encodeURIComponent(ACCOUNT)}`, { method: "DELETE" });
        loadReturn();
      } catch (err) { $("returnNote").textContent = t("msg.delete_failed", { error: err.message }); }
    });
  });
}

/* ================== الماسح ================== */
function setScanMsg(text, kind) {
  const el = $("scanMsg");
  el.className = "msg " + (kind || "");
  el.textContent = text || "";
}

function renderScanHead() {
  $("scanHead").innerHTML = `<tr><th>${esc(t("col.no"))}</th><th>${esc(t("scol.supplier"))}</th><th>${esc(t("lcol.date"))}</th>
    <th>${esc(t("lcol.net"))}</th><th>${esc(t("lcol.vat"))}</th><th>${esc(t("lcol.total"))}</th><th>%</th><th>${esc(t("scol.confidence"))}</th></tr>`;
}

function renderOcrMode() {
  const tag = $("ocrModeTag");
  if (!tag) return;
  const isOcr = state.ocr && state.ocr.mode === "tesseract";
  tag.textContent = isOcr ? t("scan.tag.ocr") : t("scan.tag.simulation");
  const mode = $("ocrMode");
  if (mode) mode.textContent = isOcr ? t("scan.tag.ocr") : t("scan.tag.simulation");
}

async function scanText() {
  const text = $("scanText").value.trim();
  if (!text) { setScanMsg(t("msg.no_text"), "bad"); return; }
  const btn = $("scanBtn");
  btn.disabled = true;
  setScanMsg(t("msg.scan_working"));
  try {
    const data = await api("/api/scan", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, account: ACCOUNT, plan: state.plan || "growth", lang: state.lang }),
    });
    if (!data.ok) throw new Error(data.error || "scan failed");
    renderScanResult(data);
  } catch (err) {
    setScanMsg(t("msg.error", { error: err.message }), "bad");
  } finally {
    btn.disabled = false;
  }
}

function renderScanResult(data) {
  state.scan = data;
  const rows = data.invoices || [];
  const totals = data.totals || {};
  $("totals").hidden = false;
  $("tableWrap").hidden = false;
  $("tCount").textContent = fmtNum(totals.count || rows.length);
  const scanCurrency = (rows[0] && rows[0].currency) || "SAR";
  state.totals.taxCurrency = scanCurrency;
  $("tTotal").textContent = money(totals.total, scanCurrency);
  $("tTax").textContent = money(totals.tax, scanCurrency);
  $("tReview").textContent = fmtNum(totals.needs_review || 0);
  $("scanBody").innerHTML = rows.map((inv, i) => {
    const low = Number(inv.confidence || 0) < 0.8;
    return `<tr><td>${fmtNum(i + 1)}</td><td>${esc(inv.supplier || "—")}</td><td>${esc(inv.date || "—")}</td>
      <td>${fmtNum(inv.subtotal, 2)}</td><td>${fmtNum(inv.tax, 2)}</td><td>${fmtNum(inv.total, 2)}</td>
      <td>${inv.rate == null ? "—" : fmtNum(inv.rate) + "%"}</td>
      <td class="${low ? "low" : ""}">${fmtNum((inv.confidence || 0) * 100)}%</td></tr>`;
  }).join("");
  $("exportBtn").disabled = !rows.length;
  state.totals.scanned += rows.length;
  state.totals.tax += Number(totals.tax || 0);
  $("statInvoices").textContent = fmtNum(state.totals.scanned);
  $("statTax").textContent = money(state.totals.tax, state.totals.taxCurrency || "SAR");
  const q = data.quota || null;
  let msg = t("msg.scanned", { count: fmtNum(rows.length), ms: fmtNum(data.elapsed_ms || 0) });
  if (q && q.capacity) msg += t("msg.quota_used", { used: fmtNum(q.used), capacity: fmtNum(q.capacity) });
  if (q && q.deferred) msg += t("msg.quota_deferred", { deferred: fmtNum(q.deferred) });
  setScanMsg(msg, "ok");
}

$("scanBtn").addEventListener("click", scanText);
$("newsRefresh").addEventListener("click", loadNews);

$("addPurchasesBtn").addEventListener("click", async () => {
  if (!state.scan || !(state.scan.invoices || []).length) return;
  try {
    const data = await api("/api/ledger", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ account: ACCOUNT, source: "scan", rows: state.scan.invoices.map((row) => ({ ...row, currency: row.currency || state.totals.taxCurrency || "SAR" })) }),
    });
    setScanMsg(t("msg.added_purchases", { count: fmtNum(data.count) }), "ok");
  } catch (err) { setScanMsg(t("msg.add_failed", { error: err.message }), "bad"); }
});

$("sampleBtn").addEventListener("click", async () => {
  try {
    const data = await api("/api/sample");
    $("scanText").value = data.text || "";
    setScanMsg(t("msg.sample_loaded"));
  } catch (err) { setScanMsg(t("msg.sample_failed"), "bad"); }
});

$("exportBtn").addEventListener("click", () => {
  if (!state.scan) return;
  const head = [t("scol.supplier"), t("lcol.date"), t("lcol.net"), t("lcol.vat"), t("lcol.total"), "%", t("scol.confidence")];
  const lines = state.scan.invoices.map((i) => [i.supplier || "", i.date || "", i.subtotal ?? "", i.tax ?? "", i.total ?? "", i.rate ?? "", i.confidence ?? ""]
    .map((v) => '"' + String(v).replace(/"/g, '""') + '"').join(","));
  const blob = new Blob(["\ufeff" + [head.join(",")].concat(lines).join("\r\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = "invoices-scan.csv"; a.click();
  URL.revokeObjectURL(url);
});

async function bulkTest() {
  const lines = [];
  for (let i = 1; i <= 500; i++) {
    const subtotal = 100 + (i % 900);
    const tax = Math.round(subtotal * 0.15 * 100) / 100;
    lines.push("المورد: شركة الاختبار " + i + "\nالتاريخ: 2026-11-" + String((i % 28) + 1).padStart(2, "0") +
      "\nالإجمالي قبل الضريبة: " + subtotal.toFixed(2) + "\nالضريبة (15%): " + tax.toFixed(2) +
      "\nالإجمالي: " + (subtotal + tax).toFixed(2));
  }
  $("scanText").value = lines.join("\n\n");
  await scanText();
}
$("bulkBtn").addEventListener("click", bulkTest);

/* ================== OCR ================== */
function showOcr(data) {
  state.ocr = data;
  const inv = data.invoice || {};
  $("ocrResult").hidden = false;
  renderOcrMode();
  $("ocrNote").textContent = data.note || "";
  $("ocrSupplier").value = inv.supplier || "";
  $("ocrDate").value = inv.date || new Date().toISOString().slice(0, 10);
  $("ocrSubtotal").value = inv.subtotal ?? "";
  $("ocrTax").value = inv.tax ?? "";
  $("ocrConfidence").textContent = inv.confidence != null
    ? t("msg.confidence", { percent: fmtNum(inv.confidence * 100) }) : "";
}

async function sendImage(file) {
  if (!file) return;
  const form = new FormData();
  form.append("image", file);
  form.append("account", ACCOUNT);
  form.append("lang", state.lang);
  setScanMsg(t("msg.ocr_working"));
  try {
    const res = await fetch("/api/ocr", { method: "POST", body: form });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || "OCR failed");
    showOcr(data);
    setScanMsg(t("msg.ocr_ready"), "ok");
  } catch (err) {
    setScanMsg(t("msg.ocr_failed", { error: err.message }), "bad");
  }
}

$("pick").addEventListener("click", () => $("file").click());
$("file").addEventListener("change", (e) => sendImage(e.target.files[0]));
$("drop").addEventListener("dragover", (e) => { e.preventDefault(); $("drop").classList.add("hover"); });
$("drop").addEventListener("dragleave", () => $("drop").classList.remove("hover"));
$("drop").addEventListener("drop", (e) => {
  e.preventDefault(); $("drop").classList.remove("hover");
  sendImage(e.dataTransfer.files && e.dataTransfer.files[0]);
});

$("demoOcrBtn").addEventListener("click", () => {
  const canvas = document.createElement("canvas");
  canvas.width = 480; canvas.height = 240;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, 480, 240);
  ctx.fillStyle = "#123"; ctx.font = "bold 20px Tahoma";
  ctx.fillText("TAX INVOICE", 24, 46);
  ctx.font = "16px Tahoma";
  ctx.fillText("Supplier: Gulf Tech Solutions", 24, 86);
  ctx.fillText("Total: 1,150.00  VAT: 150.00", 24, 120);
  ctx.fillText("2026-11-10", 24, 154);
  canvas.toBlob((blob) => { if (blob) sendImage(new File([blob], "demo-invoice.png", { type: "image/png" })); }, "image/png");
});

$("ocrSaveBtn").addEventListener("click", async () => {
  const subtotal = Number($("ocrSubtotal").value || 0);
  const tax = Number($("ocrTax").value || 0);
  const row = {
    supplier: $("ocrSupplier").value.trim() || "—", date: $("ocrDate").value || new Date().toISOString().slice(0, 10),
    subtotal, tax, total: Math.round((subtotal + tax) * 100) / 100,
    rate: subtotal > 0 ? Math.round((tax / subtotal) * 100) : 0,
    currency: countryBy(state.country)?.currency || "SAR",
    confidence: (state.ocr && state.ocr.invoice && state.ocr.invoice.confidence) || null,
  };
  try {
    const data = await api("/api/ledger", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ account: ACCOUNT, source: "ocr", rows: [row] }),
    });
    $("ocrResult").hidden = true;
    setScanMsg(t("msg.ocr_saved", { supplier: row.supplier }), "ok");
  } catch (err) { setScanMsg(t("msg.add_failed", { error: err.message }), "bad"); }
});

/* ================== المساعد والمحاسب ================== */
function renderChatGreeting() {
  const bubble = document.querySelector("#chatLog .msg.bot .bubble");
  if (bubble) bubble.textContent = t("assistant.greeting");
}

function renderSuggestions() {
  const chips = [
    ["chip.rates", "chip.q.rates"], ["chip.deadlines", "chip.q.deadlines"],
    ["chip.fields", "chip.q.fields"], ["chip.bulk", "chip.q.bulk"], ["chip.net", "chip.q.net"],
  ];
  $("suggestions").innerHTML = chips.map(([label, q]) =>
    `<button class="chip" type="button" data-q="${esc(t(q))}">${esc(t(label))}</button>`).join("");
  bindChips();
}

function appendMsg(role, text) {
  const wrap = document.createElement("div");
  wrap.className = "msg " + (role === "user" ? "user" : "bot");
  wrap.innerHTML = '<div class="bubble">' + esc(text) + "</div>";
  $("chatLog").appendChild(wrap);
  $("chatLog").scrollTop = $("chatLog").scrollHeight;
  return wrap;
}

async function ask(question) {
  const q = String(question || "").trim();
  if (!q) return;
  appendMsg("user", q);
  $("chatInput").value = "";
  const typing = appendMsg("bot", "…");
  typing.classList.add("typing");
  try {
    const data = await api("/api/assistant", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: q, lang: state.lang, invoice: state.scan && state.scan.invoices ? state.scan.invoices[0] : null }),
    });
    typing.remove();
    appendMsg("bot", data.answer || "—");
    if (Array.isArray(data.suggestions) && data.suggestions.length) {
      $("suggestions").innerHTML = data.suggestions
        .map((s) => `<button class="chip" type="button" data-q="${esc(s)}">${esc(s)}</button>`).join("");
      bindChips();
    }
  } catch (err) {
    typing.remove();
    appendMsg("bot", t("msg.assistant_failed", { error: err.message }));
  }
}

function bindChips() {
  document.querySelectorAll("#suggestions .chip").forEach((chip) => {
    chip.addEventListener("click", () => ask(chip.getAttribute("data-q")));
  });
}

$("chatForm").addEventListener("submit", (e) => { e.preventDefault(); ask($("chatInput").value); });

async function loadTickets() {
  try {
    const data = await api(`/api/support?account=${encodeURIComponent(ACCOUNT)}`);
    const list = data.messages || [];
    $("msgList").innerHTML = list.length ? list.map((m) => `
      <article class="msg-card">
        <div class="meta"><span class="tag-sm">${esc(m.ticket)}</span><span>${esc(String(m.created_at).replace("T", " "))}</span></div>
        <strong>${esc(m.topic)}</strong><p>${esc(m.message)}</p>
      </article>`).join("") : `<p class="fine">${esc(t("accountant.empty"))}</p>`;
  } catch (err) { /* يبقى العرض السابق */ }
}

$("sendTicketBtn").addEventListener("click", async () => {
  const message = $("ticketMessage").value.trim();
  const el = $("ticketMsg");
  if (!message) { el.className = "msg bad"; el.textContent = t("msg.ticket_required"); return; }
  try {
    const data = await api("/api/support", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ account: ACCOUNT, topic: $("ticketTopic").value, message, lang: state.lang }),
    });
    el.className = "msg ok";
    el.textContent = t("msg.ticket_sent", { ticket: data.ticket, reply: data.reply });
    $("ticketMessage").value = "";
    loadTickets();
  } catch (err) {
    el.className = "msg bad";
    el.textContent = t("msg.ticket_failed", { error: err.message });
  }
});

/* ================== الباقات ================== */
async function loadPlans() {
  try {
    const data = await api("/api/plans?lang=" + state.lang);
    state.plans = data.plans || [];
    renderPlans();
    await loadQuota();
  } catch (err) {
    $("planCards").innerHTML = `<p class="fine">${esc(t("msg.plans_failed"))}</p>`;
  }
}

function renderPlans() {
  if (!state.plans.length) return;
  const plan = state.plan || "growth";
  $("planCards").innerHTML = state.plans.map((p) => {
    const active = p.key === plan;
    const price = convert(p.price, "SAR", state.currency);
    return `<article class="plan${active ? " active" : ""}">
      <h3>${esc(p.name)}</h3>
      <div class="plan-price">${fmtNum(price)} <small>${esc(symbolFor(state.currency))} / ${esc(t("plans.per_year"))}</small></div>
      <div class="plan-scan">${fmtNum(p.scans)} ${esc(t("plans.scans"))}</div>
      <ul>${(p.features || []).map((f) => `<li>${esc(f)}</li>`).join("")}</ul>
      <p class="fine">${esc(p.for || "")}</p>
      <button class="${active ? "" : "ghost"}" data-plan="${esc(p.key)}" type="button">${esc(t(active ? "plans.current" : "plans.choose"))}</button>
    </article>`;
  }).join("");
  document.querySelectorAll("#planCards [data-plan]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      state.plan = btn.dataset.plan;
      localStorage.setItem("at_gulf_plan", state.plan);
      renderPlans();
      await loadQuota();
      setScanMsg(t("msg.plan_selected", { name: state.plan }), "ok");
    });
  });
}

async function loadQuota() {
  try {
    const q = await api(`/api/quota?account=${encodeURIComponent(ACCOUNT)}&plan=${encodeURIComponent(state.plan || "growth")}&lang=${state.lang}`);
    state.quota = q;
    renderQuota();
  } catch (err) { /* يبقى العرض السابق */ }
}

function renderQuota() {
  const q = state.quota;
  if (!q) return;
  const pct = Math.min(100, Math.round((q.used / (q.capacity + q.grace || 1)) * 100));
  $("quotaBar").style.width = pct + "%";
  $("quotaBar").className = "bar-fill" + (pct >= 90 ? " danger" : pct >= 70 ? " warn" : "");
  $("quotaLabel").textContent = t("msg.quota_label", { period: q.period, plan: q.plan_name || "" });
  $("quotaValue").textContent = t("msg.quota_value", { used: fmtNum(q.used), capacity: fmtNum(q.capacity) });
  $("quotaNote").textContent = q.deferred
    ? t("msg.quota_over", { deferred: fmtNum(q.deferred), grace: fmtNum(q.grace) })
    : t("msg.quota_remaining", { remaining: fmtNum(q.remaining), grace: fmtNum(q.grace) });
}

/* ================== الإعدادات / التسجيل ================== */
function openOnboarding({ firstRun = false } = {}) {
  const meta = countryBy(state.country) || {};
  $("obCountry").value = state.country;
  $("obCurrency").value = state.currency;
  document.querySelectorAll(".lang-option").forEach((btn) => btn.classList.toggle("active", btn.dataset.lang === state.lang));
  updateOnboardFacts();
  const note = $("detectNote");
  if (state.detected) {
    const d = state.detected;
    note.textContent = d.source === "language"
      ? t("modal.detected.lang", { country: (countryBy(d.country) || {}).name || d.country, currency: d.currency })
      : t("modal.detected", { country: (countryBy(d.country) || {}).name || d.country, currency: d.currency, tz: d.timezone || "—" });
    note.hidden = false;
  } else if (state.profileSaved) {
    note.textContent = t("modal.saved");
    note.hidden = false;
  } else {
    note.hidden = true;
  }
  $("onboarding").hidden = false;
  $("obSave").focus();
  state.onboardFirstRun = firstRun;
}

function updateOnboardFacts() {
  const code = $("obCountry").value;
  const meta = countryBy(code) || {};
  $("obFacts").textContent = t("modal.facts", {
    rate: fmtNum(meta.vat_rate), currency: $("obCurrency").value,
    authority: meta.authority || "",
  });
}

$("obCountry").addEventListener("change", () => {
  const meta = countryBy($("obCountry").value);
  if (meta) $("obCurrency").value = meta.currency;
  updateOnboardFacts();
});
$("obCurrency").addEventListener("change", updateOnboardFacts);
document.querySelectorAll(".lang-option").forEach((btn) => {
  btn.addEventListener("click", async () => {
    await setLanguage(btn.dataset.lang, { persist: false, reload: true });
    document.querySelectorAll(".lang-option").forEach((b) => b.classList.toggle("active", b.dataset.lang === state.lang));
    updateOnboardFacts();
  });
});

$("obSave").addEventListener("click", async () => {
  const country = $("obCountry").value;
  const currency = $("obCurrency").value;
  writeProfile();
  applyCountry(country, { keepCurrency: false, reload: false, persist: true });
  applyCurrency(currency, { persist: true, reload: false });
  $("onboarding").hidden = true;
  state.detected = null;
  await Promise.all([loadPlans(), loadNews(), loadQuota(), loadReturn()]);
  setScanMsg("");
});

$("obLater").addEventListener("click", () => {
  writeProfile();
  state.detected = null;
  $("onboarding").hidden = true;
});
$("onboardClose").addEventListener("click", () => {
  writeProfile();
  state.detected = null;
  $("onboarding").hidden = true;
});
$("settingsBtn").addEventListener("click", () => openOnboarding({ firstRun: false }));

/* ================== الربط العام ================== */
$("countrySelect").addEventListener("change", (e) => applyCountry(e.target.value));
$("invCountry").addEventListener("change", (e) => applyCountry(e.target.value));
$("retCountry").addEventListener("change", (e) => applyCountry(e.target.value, { keepCurrency: false, reload: true }));
$("currencySelect").addEventListener("change", (e) => applyCurrency(e.target.value));
$("langToggle").addEventListener("click", () => setLanguage(state.lang === "ar" ? "en" : "ar"));

/* ================== الإقلاع ================== */
async function boot() {
  const profile = readProfile();
  const browserLang = (navigator.language || "ar").toLowerCase();
  state.lang = profile?.lang === "en" || profile?.lang === "ar" ? profile.lang
    : (browserLang.startsWith("ar") ? "ar" : "en");
  if (profile?.country) state.country = profile.country;
  if (profile?.currency) state.currency = profile.currency;

  state.plan = localStorage.getItem("at_gulf_plan") || "growth";
  state.items = [blankItem()];
  $("invDate").value = new Date().toISOString().slice(0, 10);

  applyStaticTexts();
  renderItems();
  renderSuggestions();
  loadHealth();
  loadRates();

  try {
    await refreshCountries();
    if (!profile) {
      // الاكتشاف التلقائي عند أول زيارة: المنطقة الزمنية ثم لغة المتصفح.
      try {
        const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || "";
        const detected = await api(`/api/detect?tz=${encodeURIComponent(tz)}&lang=${state.lang}`);
        state.detected = detected;
        state.country = detected.country;
        state.currency = detected.currency;
      } catch (err) { /* يبقى الافتراضي */ }
    }
    applyCountry(state.country, { keepCurrency: true, reload: false, persist: false });
    applyCurrency(state.currency, { persist: false, reload: false });
  } catch (err) {
    $("authorityNote").textContent = err.message;
  }

  await Promise.all([loadPlans(), loadNews(), loadReturn(), loadQuota(), loadTickets()]);
  renderSuggestions();
  if (!profile) openOnboarding({ firstRun: true });
}

boot();
