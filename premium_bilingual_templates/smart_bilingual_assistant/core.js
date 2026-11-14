/* core.js — قاعدة المعرفة والمطابقة الذكية للمساعد (بلا DOM، قابلة للاختبار) */
(function (root) {
  "use strict";

  const COUNTRIES = {
    SA: { rate: 15, currency: "SAR", nameAr: "السعودية", nameEn: "Saudi Arabia" },
    AE: { rate: 5, currency: "AED", nameAr: "الإمارات", nameEn: "the UAE" },
    OM: { rate: 5, currency: "OMR", nameAr: "عُمان", nameEn: "Oman" },
    BH: { rate: 10, currency: "BHD", nameAr: "البحرين", nameEn: "Bahrain" },
    QA: { rate: 0, currency: "QAR", nameAr: "قطر", nameEn: "Qatar" },
    KW: { rate: 0, currency: "KWD", nameAr: "الكويت", nameEn: "Kuwait" },
  };

  /* ---------- تطبيع النص العربي والإنجليزي ---------- */
  const DIACRITICS = /[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u0640]/g;

  function normalize(value) {
    return String(value == null ? "" : value)
      .toLowerCase()
      .replace(DIACRITICS, "")
      .replace(/[أإآٱ]/g, "ا")
      .replace(/ى/g, "ي")
      .replace(/ؤ/g, "و")
      .replace(/ئ/g, "ي")
      .replace(/ة/g, "ه")
      .replace(/[^\p{L}\p{N}\s%$]/gu, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  const PREFIXES = ["وال", "بال", "كال", "فال", "لل", "ال"];

  function stem(word) {
    let out = word;
    for (const prefix of PREFIXES) {
      if (out.length > prefix.length + 2 && out.startsWith(prefix)) { out = out.slice(prefix.length); break; }
    }
    return out;
  }

  function tokenize(text) {
    return normalize(text).split(" ").filter(Boolean).map(stem);
  }

  /* ---------- كشف الدولة ---------- */
  const COUNTRY_WORDS = {
    SA: ["السعوديه", "سعودي", "سعوديه", "الرياض", "رياض", "جده", "الدمام", "ksa", "saudi", "riyadh", "jeddah", "dammam"],
    AE: ["الامارات", "امارات", "اماراتي", "دبي", "ابوظبي", "الشارقه", "عجمان", "uae", "dubai", "abu dhabi", "sharjah"],
    OM: ["عمان", "عماني", "مسقط", "oman", "muscat", "omr"],
    BH: ["البحرين", "بحريني", "المنامه", "bahrain", "manama", "bhd"],
    QA: ["قطر", "قطري", "الدوحه", "qatar", "doha", "qar"],
    KW: ["الكويت", "كويتي", "kuwait", "kwd"],
  };

  const ATTACHED_PREFIXES = ["بال", "لل", "ال", "ب", "ل", "و", "ف", "ك"];

  function stripPrefixes(token) {
    for (const prefix of ATTACHED_PREFIXES) {
      if (token.length > prefix.length + 2 && token.startsWith(prefix)) return token.slice(prefix.length);
    }
    return token;
  }

  function detectCountry(text) {
    const norm = normalize(text);
    const tokens = norm.split(" ");
    const bare = tokens.map(stripPrefixes);
    for (const code of Object.keys(COUNTRY_WORDS)) {
      for (const word of COUNTRY_WORDS[code]) {
        const w = normalize(word);
        if (w.includes(" ")) { if (norm.includes(w)) return code; continue; }
        const hit = tokens.some((token, index) => token === w || bare[index] === w ||
          (w.length >= 4 && (token.endsWith(w) || token.startsWith(w))));
        if (hit) return code;
      }
    }
    return null;
  }

  /* ---------- قاعدة المعرفة ---------- */
  const INTENTS = [
    {
      id: "rates",
      keys: [
        "نسبة الضريبة", "نسب الضريبة", "نسبة ضريبة القيمة المضافة", "نسب ضريبة القيمة المضافة",
        "كم الضريبة", "كم نسبه الضريبه", "وش نسبة الضريبة", "ايش نسبة الضريبة", "وش النسبة",
        "ضريبة القيمة المضافة", "القيمة المضافة", "نسبة القيمة المضافة", "الضريبة المضافة",
        "كم ضريبة", "نسبة الvat", "vat rate", "vat percentage", "tax rate", "how much is vat",
        "what is vat", "what's the vat", "standard rate", "vat in", "نسبة", "نسب", "rate", "vat", "15%", "5%",
      ],
      boost: ["نسبه الضريبه", "نسب الضريبه", "vat rate", "كم الضريبه"],
      answer: {
        ar: "نسب ضريبة القيمة المضافة في الخليج:\n• السعودية 15%\n• الإمارات 5%\n• عُمان 5%\n• البحرين 10%\n• قطر والكويت: لا تُطبَّق حاليًا (0% في القالب).\n\nحدود التسجيل الإلزامي: 375,000 ر.س في السعودية و375,000 درهم في الإمارات، والاختياري 187,500 في البلدين.",
        en: "Gulf VAT rates:\n• Saudi Arabia 15%\n• UAE 5%\n• Oman 5%\n• Bahrain 10%\n• Qatar and Kuwait: not applied yet (0% in the template).\n\nMandatory registration thresholds: SAR 375,000 in Saudi Arabia and AED 375,000 in the UAE; voluntary at 187,500 in both.",
      },
    },
    {
      id: "registration",
      keys: [
        "حد التسجيل", "حدود التسجيل", "التسجيل الالزامي", "تسجيل ضريبة", "تسجيل في الضريبة",
        "هل احتاج اسجل", "هل لازم اسجل", "هل يجب ان اسجل", "لازم نسجل", "نسجل في الضريبة",
        "هل اسجل", "متى اسجل", "التسجيل في القيمة المضافة", "registration", "register for vat",
        "do i need to register", "when must i register", "when should i register", "registration threshold",
        "vat registration", "mandatory registration", "threshold", "375", "اسجل", "تسجيل",
      ],
      boost: ["اسجل", "التسجيل", "register"],
      answer: {
        ar: "حدود التسجيل في ضريبة القيمة المضافة:\n• السعودية: إلزامي عند 375,000 ر.س من الإيرادات السنوية، واختياري من 187,500.\n• الإمارات: إلزامي عند 375,000 درهم، واختياري من 187,500.\n• عُمان: إلزامي عند 38,500 ريال عماني.\n• البحرين: إلزامي عند 37,500 دينار بحريني (واختياري من 18,750).\n• قطر والكويت: لا ضريبة قيمة مضافة حاليًا.\n\nراقب الإيرادات على أساس 12 شهرًا متتالية، لا السنة الميلادية فقط.",
        en: "VAT registration thresholds:\n• Saudi Arabia: mandatory at SAR 375,000 annual revenue, voluntary from 187,500.\n• UAE: mandatory at AED 375,000, voluntary from 187,500.\n• Oman: mandatory at OMR 38,500.\n• Bahrain: mandatory at BHD 37,500 (voluntary from 18,750).\n• Qatar and Kuwait: no VAT yet.\n\nTrack revenue over any rolling 12-month period, not only the calendar year.",
      },
    },
    {
      id: "deadline",
      keys: [
        "موعد الاقرار", "مواعيد الاقرار", "اخر موعد", "متى الاقرار", "وقت الاقرار", "تقديم الاقرار",
        "الاقرار الضريبي", "الاقرار الربعي", "الاقرار الشهري", "deadline", "filing", "vat return",
        "when is the return", "due date", "when is vat due", "file the return", "quarterly return",
        "اقرار", "موعد", "مواعيد", "ربع", "return",
      ],
      boost: ["الاقرار", "deadline", "filing"],
      answer: {
        ar: "مواعيد الإقرار الضريبي:\n• السعودية: شهري أو ربع سنوي حسب حجم المنشأة، ويُقدَّم خلال الشهر التالي لنهاية الفترة.\n• الإمارات: ربع سنوي خلال 28 يومًا من نهاية الربع.\n• عُمان والبحرين: شهري أو ربع سنوي حسب التصنيف.\n• قطر والكويت: لا إقرار قيمة مضافة حاليًا.\n\nاحسب الموعد من تقويم الهيئة في بلدك، فقد يتغير باختلاف التصنيف.",
        en: "VAT filing deadlines:\n• Saudi Arabia: monthly or quarterly depending on size, filed in the month after the period ends.\n• UAE: quarterly, within 28 days of the quarter end.\n• Oman and Bahrain: monthly or quarterly depending on category.\n• Qatar and Kuwait: no VAT return yet.\n\nConfirm dates on your authority's portal, as the category can change the cadence.",
      },
    },
    {
      id: "fields",
      keys: [
        "حقول الفاتورة", "حقول فاتورة", "بيانات الفاتورة", "محتوى الفاتورة", "ماذا يجب ان تحتوي الفاتورة",
        "الفاتورة الضريبية", "الفاتورة الالكترونية", "فاتورة الكترونية", "رمز qr", "qr code",
        "invoice fields", "invoice requirements", "what must an invoice contain", "required invoice",
        "tax invoice", "e-invoice", "e-invoicing", "fields", "فاتورة", "حقول", "invoice",
      ],
      boost: ["حقول", "invoice fields", "فاتوره الكترونيه"],
      answer: {
        ar: "الحقول الأساسية للفاتورة الضريبية:\n• اسم المورد والرقم الضريبي\n• رقم الفاتورة وتاريخ الإصدار\n• اسم العميل ورقمه الضريبي إن كان مسجلًا\n• وصف البنود والكمية والسعر والخصم\n• الصافي ونسبة الضريبة ومبلغ الضريبة والإجمالي\n• العملة ورمز QR للفاتورة المبسطة (السعودية)\n\nالفاتورة الإلكترونية في السعودية: المرحلة الأولى تشمل QR، والمرحلة الثانية ربط تكاملي مع منصة فاتورة حسب شرائح الإيرادات.",
        en: "Required tax invoice fields:\n• Seller name and tax number\n• Invoice number and issue date\n• Customer name and tax number if registered\n• Line description, quantity, price and discount\n• Net, VAT rate, VAT amount and total\n• Currency and the QR code for simplified invoices (Saudi Arabia)\n\nSaudi e-invoicing: phase one covers the QR code; phase two is an integration with the Fatoora platform by revenue waves.",
      },
    },
    {
      id: "input",
      keys: [
        "خصم ضريبة المشتريات", "ضريبة المشتريات", "ضريبة المدخلات", "المدخلات", "استرداد الضريبة",
        "استرجاع الضريبة", "deduct input vat", "input vat", "purchase vat", "recover vat",
        "can i deduct", "deduction", "مشتريات", "خصم",
      ],
      boost: ["المدخلات", "input vat", "ضريبه المشتريات"],
      answer: {
        ar: "شروط خصم ضريبة المشتريات (المدخلات):\n• فاتورة ضريبية صحيحة تحمل رقم المورد الضريبي.\n• شراء لاستخدام العمل الخاضع للضريبة، لا للاستخدام الشخصي.\n• تسجيل الفاتورة في الفترة الصحيحة (فترة الاستلام عادةً).\n• عدم خصم ضريبة فواتير مفقودة أو غير مطابقة للبيانات.\n\nالفواتير منخفضة الثقة أو بلا رقم ضريبي لا تُعتمد عند التدقيق، ولهذا يوسم الماسح هذه الفواتير للمراجعة.",
        en: "Conditions for deducting input VAT:\n• A valid tax invoice carrying the supplier's tax number.\n• The purchase is used for taxable business activity, not private use.\n• The invoice is recorded in the correct period (usually when received).\n• No deduction on missing or mismatched invoices.\n\nLow-confidence invoices without a tax number are rejected at audit, which is why the scanner flags them for review.",
      },
    },
    {
      id: "zero",
      keys: [
        "معفاة", "معفاه", "اعفاء", "صفرية", "صفريه", "صفر بالمئة", "0%", "zero rated", "zero-rated",
        "exempt", "exemption", "difference between zero", "معفى",
      ],
      boost: ["معفاه", "صفريه", "exempt", "zero rated"],
      answer: {
        ar: "الفرق بين المعفاة والصفرية:\n• **صفرية (0%)**: خاضعة للضريبة بنسبة صفر — تُمكّنك من خصم ضريبة المدخلات، مثل التصدير والرعاية الصحية المؤهلة في بعض الدول.\n• **معفاة**: خارج نطاق الضريبة — لا تُحصّل ضريبة ولا تخصم ضريبة المدخلات المرتبطة بها.\n\nعمليًا: لا تُدخل ضريبة على الفاتورة في الحالتين، لكن المعالجة المحاسبية للمدخلات تختلف.",
        en: "Zero-rated vs exempt:\n• **Zero-rated (0%)**: taxable at zero — input VAT is usually recoverable, e.g. exports and qualifying healthcare in some countries.\n• **Exempt**: outside the scope — no output VAT and no recovery of related input VAT.\n\nIn practice both invoices show no VAT, but input VAT treatment differs.",
      },
    },
    {
      id: "penalty",
      keys: [
        "غرامة", "غرامات", "عقوبة", "عقوبات", "تاخير في الاقرار", "تأخير", "penalty", "penalties",
        "fine", "late filing", "late payment", "violation", "غرامة على التأخير", "هل هناك غرامة",
        "any penalty", "penalty for late", "في غرامة",
      ],
      boost: ["غرام", "penalt", "عقوب", "fine"],
      answer: {
        ar: "أكثر أسباب الغرامات الضريبية شيوعًا:\n• عدم إصدار فاتورة إلكترونية أو إصدارها ببيانات ناقصة.\n• التأخر في تقديم الإقرار أو السداد.\n• عدم مطابقة بيانات المورد بين الفاتورة والسجل.\n• عدم الاحتفاظ بالفواتير للمدة النظامية (٥ سنوات عادةً).\n\nالوقاية أرخص من التصحيح: تحقق من الحقول قبل الإصدار، وأرشف نسخة PDF لكل فاتورة.",
        en: "The most common tax penalties:\n• Missing or incomplete e-invoices.\n• Late filing or late payment.\n• Mismatched supplier details between invoice and records.\n• Not retaining invoices for the required period (often five years).\n\nPrevention is cheaper than correction: verify fields before issuing and archive a PDF of every invoice.",
      },
    },
    {
      id: "journal",
      keys: [
        "قيد", "قيود", "قيد اليومية", "قيود الفواتير", "قيد الفاتورة", "قيد فاتورة", "اسوي قيد",
        "تسجيل القيد", "تدقيق", "ترحيل", "مدين", "دائن",
        "journal entry", "journal", "audit", "double entry", "debit", "credit", "posting",
        "how do i audit", "entry",
      ],
      boost: ["قيود", "تدقيق", "ترحيل", "journal", "audit", "ادقق", "دقق", "راجع القيد"],
      answer: {
        ar: "القيد الصحيح لفاتورة مبيعات:\n• مدين: ذمم العملاء / النقدية = الإجمالي\n• دائن: الإيرادات = الصافي\n• دائن: ضريبة القيمة المضافة المستحقة = مبلغ الضريبة\n\nولفاتورة مشتريات:\n• مدين: المصروف أو الأصل = الصافي\n• مدين: ضريبة المدخلات = الضريبة\n• دائن: الموردون / النقدية = الإجمالي\n\nقبل الترحيل تحقق من: الصافي × النسبة = الضريبة، والصافي + الضريبة = الإجمالي، وصيغة الرقم الضريبي. أداة التدقيق بالأسفل تجري هذه الفحوص نيابةً عنك.",
        en: "Correct sales invoice entry:\n• Debit receivables / cash = total\n• Credit revenue = net\n• Credit VAT payable = VAT amount\n\nPurchase invoice entry:\n• Debit expense or asset = net\n• Debit input VAT = VAT\n• Credit payables / cash = total\n\nBefore posting, verify: net × rate = VAT, net + VAT = total, and the tax-number format. The audit tool below runs these checks for you.",
      },
    },
    {
      id: "templates",
      keys: [
        "قالب", "قوالب", "اي قالب", "افضل قالب", "قالب مناسب", "اختيار قالب", "باقة",
        "template", "templates", "which template", "best template", "recommend a template", "product",
      ],
      boost: ["قالب", "قوالب", "template"],
      answer: {
        ar: "قوالب Arab Templates المتاحة:\n• نظام المحاسبة والامتثال الضريبي الخليجي — فواتير QR وإقرار ومسح\n• متجر القوالب الرقمي — عرض وبيع القوالب\n• لوحة متابعة العملاء (CRM)\n• نظام حجز المواعيد\n• بطاقات تعليمية تفاعلية\n• موقع أعمال شخصي\n• مساعد ذكي مخصص\n• حملة بريدية عربية\n\nاضغط «اختر لي القالب المناسب» أو «هل يناسبني؟» على أي بطاقة في قسم القوالب، وسأشرح الخطوات بالتفصيل.",
        en: "Available Arab Templates:\n• Gulf tax & accounting suite — QR invoices, VAT return, scanning\n• Digital templates store — showcase and sell templates\n• Customer follow-up dashboard (CRM)\n• Appointment booking system\n• Interactive study flashcards\n• Personal portfolio site\n• Custom AI assistant\n• Arabic email campaign\n\nPress “Recommend a template” or “Is it right for me?” on any card in the catalogue and I will explain the setup steps.",
      },
    },
    {
      id: "setup",
      keys: [
        "تشغيل", "تثبيت", "كيف اشغل", "كيف اشغله", "طريقة التشغيل", "بدء الاستخدام", "بدايه الاستخدام",
        "install", "setup", "run the project", "how do i run", "how do i install it", "get started",
        "start the server", "python", "command", "طريقة الاستخدام", "استخدام", "اثبته", "اثبتها",
        "اثبت", "ثبت", "طريقة التنصيب",
      ],
      boost: ["تشغيل", "تثبيت", "setup", "install", "اثبت", "ثبت", "تنصيب"],
      answer: {
        ar: "خطوات تشغيل منتجات Arab Templates:\n1. تثبيت بايثون ثم الحزم: python -m pip install flask segno\n2. تشغيل الخادم: python gulf_tax_template_pro/server.py --port 5075\n3. فتح http://127.0.0.1:5075 في المتصفح\n4. من الإعدادات: الدولة والعملة واللغة\n5. إصدار أول فاتورة وحفظها لتظهر في الإقرار\n\nللمتجر: python scripts/store_server.py ثم http://127.0.0.1:8787.",
        en: "Running Arab Templates products:\n1. Install Python, then: python -m pip install flask segno\n2. Start the server: python gulf_tax_template_pro/server.py --port 5075\n3. Open http://127.0.0.1:5075\n4. In settings, pick country, currency and language\n5. Issue your first invoice and save it so it appears in the return\n\nFor the store: python scripts/store_server.py then http://127.0.0.1:8787.",
      },
    },
    {
      id: "support",
      keys: [
        "دعم", "دعم فني", "تواصل", "محاسب بشري", "شخص", "موظف", "تذكرة", "تذكره",
        "support", "contact", "human", "agent", "ticket", "talk to someone", "help me",
        "talk to a human", "speak to a human", "human support", "اتكلم مع", "اكلم احد",
      ],
      boost: ["دعم", "تواصل", "support", "بشري", "human", "اكلم", "اتكلم"],
      answer: {
        ar: "للحصول على دعم بشري:\n• اطرح سؤالك هنا أولًا — معظم أسئلة القوالب والضريبة لها جواب فوري.\n• إن احتجت متابعة بشرية، أرسل التفاصيل من صفحة المتجر أو من تبويب «التواصل مع المحاسب» داخل القالب الضريبي (يُنشئ تذكرة برقم).\n• أرفق دائمًا: الدولة، الفترة، ومبلغ الفاتورة، لتسريع الرد.",
        en: "For human support:\n• Ask here first — most template and VAT questions are answered instantly.\n• If you need a person, send details from the store page or the “Talk to an accountant” tab inside the tax template (it creates a ticket number).\n• Always include: country, period and invoice amount to speed up the reply.",
      },
    },
  ];

  /* ---------- إجابات مخصصة حسب الدولة ---------- */
  const COUNTRY_RATE_TEXT = {
    ar: {
      SA: "نسبة ضريبة القيمة المضافة في السعودية: 15%\n• حد التسجيل الإلزامي: 375,000 ر.س (اختياري من 187,500)\n• الإقرار: شهري أو ربع سنوي حسب حجم المنشأة\n• العملة: الريال السعودي (SAR)",
      AE: "نسبة ضريبة القيمة المضافة في الإمارات: 5%\n• حد التسجيل الإلزامي: 375,000 درهم (اختياري من 187,500)\n• الإقرار: ربع سنوي خلال 28 يومًا من نهاية الربع\n• العملة: الدرهم (AED)",
      OM: "نسبة ضريبة القيمة المضافة في عُمان: 5%\n• حد التسجيل الإلزامي: 38,500 ريال عماني\n• الإقرار: شهري أو ربع سنوي حسب تصنيف المنشأة\n• العملة: الريال العماني (OMR)",
      BH: "نسبة ضريبة القيمة المضافة في البحرين: 10%\n• حد التسجيل الإلزامي: 37,500 دينار بحريني (اختياري من 18,750)\n• الإقرار: شهري أو ربع سنوي حسب حجم التوريدات\n• العملة: الدينار البحريني (BHD)",
      QA: "قطر: لا تُطبَّق ضريبة القيمة المضافة حاليًا (0%)، والقالب جاهز عند التفعيل.\n• لا يوجد إقرار قيمة مضافة الآن\n• العملة: الريال القطري (QAR)",
      KW: "الكويت: لا تُطبَّق ضريبة القيمة المضافة حاليًا (0%)، والقالب جاهز عند التفعيل.\n• لا يوجد إقرار قيمة مضافة الآن\n• العملة: الدينار الكويتي (KWD)",
    },
    en: {
      SA: "VAT in Saudi Arabia: 15%\n• Mandatory registration: SAR 375,000 (voluntary from 187,500)\n• Return: monthly or quarterly depending on size\n• Currency: Saudi riyal (SAR)",
      AE: "VAT in the UAE: 5%\n• Mandatory registration: AED 375,000 (voluntary from 187,500)\n• Return: quarterly, within 28 days of the quarter end\n• Currency: UAE dirham (AED)",
      OM: "VAT in Oman: 5%\n• Mandatory registration: OMR 38,500\n• Return: monthly or quarterly depending on the business category\n• Currency: Omani rial (OMR)",
      BH: "VAT in Bahrain: 10%\n• Mandatory registration: BHD 37,500 (voluntary from 18,750)\n• Return: monthly or quarterly depending on supply volume\n• Currency: Bahraini dinar (BHD)",
      QA: "Qatar has no VAT yet (0%); the template is ready when it launches.\n• No VAT return today\n• Currency: Qatari riyal (QAR)",
      KW: "Kuwait has no VAT yet (0%); the template is ready when it launches.\n• No VAT return today\n• Currency: Kuwaiti dinar (KWD)",
    },
  };

  function countryAnswer(kind, code, lang) {
    const useEn = lang === "en";
    if (kind === "rates") {
      const text = (COUNTRY_RATE_TEXT[useEn ? "en" : "ar"] || {})[code];
      if (text) return text;
    }
    return null;
  }

  /* ---------- المطابقة ---------- */
  function scoreIntent(intent, normText, tokens) {
    let score = 0;
    (intent.keys || []).forEach((key) => {
      const k = normalize(key);
      if (!k) return;
      const kTokens = k.split(" ").filter(Boolean).map(stem);
      if (k.includes(" ")) {
        if (normText.includes(k)) score += 7 + kTokens.length * 2 + k.length / 8;
        else {
          const content = kTokens.filter((token) => token.length > 2);
          const hits = content.filter((token) => tokens.includes(token)).length;
          if (content.length && hits >= Math.min(2, content.length)) {
            score += (hits / content.length) * (4 + content.length);
          }
        }
      } else if (tokens.includes(kTokens[0])) {
        score += 3.2 + Math.min(k.length, 10) / 5;
      } else if (k.length >= 5 && normText.includes(k)) {
        score += 2.4;
      }
    });
    (intent.boost || []).forEach((key) => {
      const k = normalize(key);
      if (!k) return;
      const base = stem(k);
      if (k.includes(" ")) { if (normText.includes(k)) score += 8; return; }
      const hit = tokens.some((token) => token === base || (base.length >= 4 && token.startsWith(base)));
      if (hit) score += 8;
    });
    return score;
  }

  function matchIntent(text) {
    const normText = " " + normalize(text) + " ";
    const tokens = tokenize(text);
    let best = null;
    let bestScore = 0;
    INTENTS.forEach((intent) => {
      const score = scoreIntent(intent, normText, tokens);
      if (score > bestScore) { best = intent; bestScore = score; }
    });
    const country = detectCountry(text);
    return {
      intent: bestScore >= 4.5 ? best : null,
      id: best && bestScore >= 4.5 ? best.id : null,
      score: Math.round(bestScore * 100) / 100,
      country,
      answer: bestScore >= 4.5 && best ? best.answer : null,
    };
  }

  const api = { COUNTRIES, normalize, tokenize, stem, detectCountry, matchIntent, countryAnswer, INTENTS };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  root.AssistantCore = api;
})(typeof window !== "undefined" ? window : globalThis);
