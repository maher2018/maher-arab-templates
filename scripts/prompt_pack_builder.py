#!/usr/bin/env python3
"""مولّد حزم أوامر الذكاء الاصطناعي — Arab Templates.

يولّد حزمًا احترافية باللهجات الخليجية (سعودي، إماراتي، كويتي) في مجالين
(التجارة الإلكترونية، التسويق العقاري)، ويحفظها كمنتجات رقمية منظمة:

    prompt_packs/<dialect>-<domain>/
        README.md      صفحة المنتج: الوصف، المحتوى، لمن، طريقة الاستخدام، الترخيص
        prompts.md     كل الأوامر منظمة بأقسام جاهزة للنسخ
        prompts.txt    الأوامر فقط، مرقّمة، بلا تنسيق
        pack.json      بيانات الحزمة كاملة (للتسعير والرفع الآلي)
        <slug>.zip     (مع --zip) حزمة التنزيل التي تُباع

وفي جذر المخرجات:
    catalog.csv / catalog.json   الكتالوج بحقول متجرك: Title, Category,
                                 description, price, preview_url
    index.md                     فهرس المنتجات مع الأسعار

أمثلة:
    python prompt_pack_builder.py                       # كل الحزم
    python prompt_pack_builder.py --dialects saudi --domains realestate
    python prompt_pack_builder.py --zip --publish --dry-run
    python prompt_pack_builder.py --publish             # رفع الكتالوج إلى جدول template

الأوامر تُولَّد حتميًا مع --seed، فإعادة التشغيل تعطي نفس الملفات.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
import time
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass

VERSION = "1.0"
PRICE_CURRENCY = "SAR"
PREVIEW_BASE = "https://arab-templates.example.com/preview"

# --------------------------------------------------------------------------- #
# اللهجات: مفردات وأسلوب
# --------------------------------------------------------------------------- #

DIALECTS: dict[str, dict[str, str]] = {
    "saudi": {
        "label": "سعودي",
        "region": "السعودية",
        "want": "أبغى",
        "what": "وش",
        "now": "الحين",
        "much": "مرة",
        "do": "سوّي لي",
        "polite": "يا ليت",
        "tone": "سعودي بسيط وقريب من الناس، بلا فصحى متقعّرة ولا مبالغة",
        "greeting": "السلام عليكم",
        "thanks": "يعطيك العافية",
        "closing": "الله يوفقك",
        "audience": "العميل السعودي",
    },
    "emirati": {
        "label": "إماراتي",
        "region": "الإمارات",
        "want": "أبا",
        "what": "شو",
        "now": "الحين",
        "much": "وايد",
        "do": "سوّي لي",
        "polite": "لو سمحت",
        "tone": "إماراتي ودّي ولبق، هادئ وواثق",
        "greeting": "السلام عليكم ورحمة الله",
        "thanks": "مشكور",
        "closing": "الله يسعدك",
        "audience": "العميل الإماراتي",
    },
    "kuwaiti": {
        "label": "كويتي",
        "region": "الكويت",
        "want": "أبي",
        "what": "شنو",
        "now": "هالحين",
        "much": "وايد",
        "do": "سوّي لي",
        "polite": "لو تكرمت",
        "tone": "كويتي حار وودّي، بلا تكلّف",
        "greeting": "هلا والله",
        "thanks": "مشكور يا طويل العمر",
        "closing": "الله يوفقك",
        "audience": "العميل الكويتي",
    },
}

DOMAINS: dict[str, dict[str, object]] = {
    "ecommerce": {
        "label": "التجارة الإلكترونية",
        "store_category": "حزم أوامر AI — التجارة الإلكترونية",
        "price": 149,
        "promise": "محتوى يبيع: أوصاف منتجات، إعلانات، ردود واتساب، واسترجاع سلات متروكة.",
        "audience_note": "أصحاب المتاجر الإلكترونية والحسابات البيعية على إنستقرام وسناب وتيك توك.",
    },
    "realestate": {
        "label": "التسويق العقاري",
        "store_category": "حزم أوامر AI — التسويق العقاري",
        "price": 199,
        "promise": "إعلانات عقار مقنعة، ردود واتساب على الاستفسارات، نصوص معاينة، وعروض للمستثمر.",
        "audience_note": "المسوّقون العقاريون والمكاتب والوسطاء الذين يبيعون عبر واتساب وإنستقرام.",
    },
}

# --------------------------------------------------------------------------- #
# مواصفات الأوامر
# --------------------------------------------------------------------------- #
# كل مواصفة تُركّب مع مفردات اللهجة، فالمحتوى نفسه بلهجة سعودية أو إماراتية أو كويتية.

ECOMMERCE_SPECS: list[dict[str, object]] = [
    {
        "title": "وصف منتج يبيع",
        "use_case": "صفحة منتج في المتجر",
        "role": "كاتب محتوى تجارة إلكترونية",
        "task": "{do} وصف منتج يخلي {audience} يفهم الفايدة في أول سطرين ويقتنع يشتري.",
        "variables": ["اسم المنتج", "الفايدة الأساسية", "الجمهور", "السعر", "أهم ثلاث ميزات"],
        "constraints": [
            "اكتب بالنبرة {tone}.",
            "لا تذكر وعودًا طبية أو أرقامًا لا أعطيتك إياها.",
            "اذكر السعر مرة واحدة فقط وفي نهاية الوصف.",
        ],
        "output": "عنوان قصير + وصف من ٣ فقرات + ثلاث نقاط ميزات + جملة إغلاق فيها دعوة للشراء.",
        "tip": "{polite} جرّب نفس المنتج مرتين: مرة لجمهور يبحث عن التوفير، ومرة لجمهور يبحث عن الجودة.",
    },
    {
        "title": "عنوان منتج محسّن للبحث",
        "use_case": "عنوان SEO قصير لصفحة المنتج",
        "role": "خبير SEO عربي",
        "task": "{do} خمسة عناوين للمنتج، كل واحد أقل من ٦٠ حرفًا، وفيها الكلمة اللي يدوّرها {audience}.",
        "variables": ["اسم المنتج", "الكلمة المفتاحية الأساسية", "المدينة إن كان محليًا"],
        "constraints": [
            "بلا حشو كلمات مفتاحية، وبلا علامات تعجب أكثر من واحدة.",
            "كل عنوان يبدأ بفايدة لا باسم المنتج.",
            "اكتب بالأسلوب {tone}.",
        ],
        "output": "خمسة عناوين مرقّمة، وبعدها سطر يشرح لمن يصلح كل عنوان.",
        "tip": "{what} العنوان الأفضل؟ اللي يفهمه الزبون قبل ما يكمّل القراءة.",
    },
    {
        "title": "مجموعة كلمات مفتاحية",
        "use_case": "خطة إعلانات وكلمات بحث",
        "role": "محلّل كلمات مفتاحية",
        "task": "{do} مجموعة كلمات مفتاحية للمنتج مقسّمة إلى نوايا شراء: بحث، مقارنة، واستعداد للشراء.",
        "variables": ["اسم المنتج", "المدينة", "المنافسون إن وُجدوا"],
        "constraints": [
            "لا تخترع أحجام بحث رقمية؛ اكتفِ بترتيب الأولوية.",
            "اذكر صيغ اللهجة كما يكتبها الناس فعلًا، بلا تشكيل.",
            "خليها ٣٠ كلمة كحد أقصى.",
        ],
        "output": "جدول من ثلاثة أعمدة: الكلمة، النية، الصفحة المستهدفة.",
        "tip": "{polite} ابدأ بالكلمات الطويلة ثلاثية الكلمات، منافستها أقل وتكلفتها أرخص.",
    },
    {
        "title": "إعلان سناب أو إنستقرام قصير",
        "use_case": "منشور مدفوع أو ستوري",
        "role": "كاتب إعلانات سوشيال ميديا",
        "task": "{do} ثلاث نسخ إعلانية قصيرة للمنتج، كل نسخة أقل من ٤٠ كلمة وتوصل الفكرة في أول ٣ كلمات.",
        "variables": ["اسم المنتج", "العرض الحالي", "الجمهور", "مدة العرض"],
        "constraints": [
            "بلا مبالغات مثل «الأفضل في العالم».",
            "استخدم النبرة {tone}.",
            "ضع دعوة واحدة واضحة للتواصل أو الشراء.",
        ],
        "output": "ثلاث نسخ، مع اقتراح أول سطر على الشاشة لكل نسخة.",
        "tip": "الإعلان اللي ينجح غالبًا يبدأ بمشكلة يعرفها {audience} من تجربته.",
    },
    {
        "title": "رد واتساب على استفسار",
        "use_case": "أول رد على رسالة عميل",
        "role": "موظف خدمة عملاء محترف",
        "task": "{do} رد واتساب من ثلاث أسطر: ترحيب، إجابة مباشرة، وسؤال يفتح المحادثة.",
        "variables": ["سؤال العميل", "اسم المنتج", "التوفر", "السعر", "مدة التوصيل"],
        "constraints": [
            "ابدأ بـ{greeting}، وبلا رسميات زايدة.",
            "لا ترسل أكثر من سؤالين في الرسالة.",
            "لو ما عندك معلومة، اكتب {{تحتاج تأكيد}} بدل ما تخترع.",
        ],
        "output": "رسالة واحدة جاهزة للنسخ، بلا مقدمات ولا شرح.",
        "tip": "{polite} خلّ آخر سطر سؤالًا محددًا، مثل «تحب أوصف لك المقاسات؟».",
    },
    {
        "title": "الرد على «غالي»",
        "use_case": "اعتراض السعر",
        "role": "مسؤول مبيعات",
        "task": "{do} رد على عميل يقول «غالي» بأسلوب يحترم ميزانيته ويشرح القيمة بلا تقليل من المنتج.",
        "variables": ["اسم المنتج", "السعر", "أقرب بديل أرخص", "ضمان أو خدمة إضافية"],
        "constraints": [
            "لا تعتذر عن السعر ولا تخفّضه من نفسك.",
            "قدّم خيارين: قيمة أعلى، أو خيار أصغر بسعر أنسب.",
            "النبرة {tone}، بلا جدال.",
        ],
        "output": "رد من أربعة أسطر كحد أقصى + اقتراح بديل واحد.",
        "tip": "{thanks} لا تحوّل المحادثة لمفاوصة سعر مباشرة، حوّلها لمقارنة قيمة.",
    },
    {
        "title": "استرجاع سلة متروكة",
        "use_case": "رسالة متابعة بعد ترك السلة",
        "role": "مسوّق بالبريد والرسائل النصية",
        "task": "{do} رسالتين لمتابعة سلة متروكة: الأولى بعد ساعتين، والثانية بعد يوم.",
        "variables": ["اسم المنتج", "قيمة السلة", "سبب محتمل للتردد", "كود خصم إن وُجد"],
        "constraints": [
            "لا تلوم العميل ولا تصفه بالنسيان.",
            "الرسالة الأولى بلا خصم، والثانية فيها حافز واحد فقط.",
            "النبرة {tone}.",
        ],
        "output": "رسالتان، كل واحدة أقل من ٥٠ كلمة، مع عنوان مقترح لكل رسالة.",
        "tip": "{what} يوقف الناس؟ غالبًا سؤال عن المقاس أو التوصيل، جاوبه قبل العرض.",
    },
    {
        "title": "طلب تقييم بعد الشراء",
        "use_case": "رسالة ما بعد التوصيل",
        "role": "مسؤول تجربة العملاء",
        "task": "{do} رسالة تطلب تقييمًا بعد وصول الطلب، وتخلي التقييم سهلًا.",
        "variables": ["اسم المنتج", "يوم التوصيل", "رابط أو طريقة التقييم"],
        "constraints": [
            "بلا إلحاح، وبلا أكثر من طلب واحد.",
            "اقترح سؤالين محددين يساعدان على التقييم.",
            "النبرة {tone}.",
        ],
        "output": "رسالة قصيرة + سؤالان جاهزان يستخدمهما العميل لصياغة تقييمه.",
        "tip": "التقييم المكتوب بجملة واحدة عن الاستخدام أفضل للإعلانات من «ممتاز» فقط.",
    },
    {
        "title": "عرض حزمة أو خصم محدود",
        "use_case": "عرض موسمي",
        "role": "مخطط عروض تجارية",
        "task": "{do} عرض حزمة يجمع المنتج مع منتج مكمّل، ويوضّح التوفير بلا تعقيد.",
        "variables": ["المنتج الأساسي", "المنتج المكمّل", "السعر الأصلي", "سعر الحزمة", "آخر موعد"],
        "constraints": [
            "احسب التوفير بصراحة، ولا تبالغ في نسبته.",
            "حدّد موعدًا واضحًا للانتهاء.",
            "بلا كلمات ضغط مبالغ فيها.",
        ],
        "output": "نص عرض من ٤ أسطر + سطر شروط مختصر + سطر أخير للاستعجال بلطف.",
        "tip": "{polite} لا تقل «لفترة محدودة» بلا تاريخ؛ التاريخ يرفع التحويل.",
    },
    {
        "title": "سياسة إرجاع بلغة بشرية",
        "use_case": "صفحة السياسات والأسئلة",
        "role": "كاتب محتوى قانوني مبسّط",
        "task": "{do} صياغة سياسة إرجاع واضحة، مكتوبة بلغة يفهمها {audience} من أول قراءة.",
        "variables": ["مدة الإرجاع", "حالة المنتج المقبولة", "طريقة الاسترجاع", "من يتحمّل الشحن"],
        "constraints": [
            "بلا مصطلحات قانونية غامضة.",
            "قائمة نقاط بدل فقرة طويلة.",
            "لا تعد بشيء غير موجود في المعطيات.",
        ],
        "output": "ملخص في سطرين + خمس نقاط + سؤالين شائعين مع إجابتهما.",
        "tip": "{thanks} سياسة الإرجاع الواضحة ترفع الثقة وتقلل رسائل الدعم.",
    },
]

REALESTATE_SPECS: list[dict[str, object]] = [
    {
        "title": "وصف عقار للإعلان",
        "use_case": "إعلان في منصة عقارية",
        "role": "كاتب إعلانات عقارية",
        "task": "{do} وصف عقار يخلّي {audience} يتخيّل السكن قبل الزيارة، ويذكر الحي والمزايا بصدق.",
        "variables": ["نوع العقار", "المساحة", "عدد الغرف", "الحي والمدينة", "السعر", "أقرب خدمة مهمة"],
        "constraints": [
            "لا تذكر مزايا غير موجودة في المعطيات.",
            "النبرة {tone}، وركّز على الحياة اليومية لا على الأرقام فقط.",
            "اذكر السعر في نهاية الوصف.",
        ],
        "output": "عنوان + وصف من ٣ فقرات + خمس نقاط سريعة + دعوة لمعاينة.",
        "tip": "{what} يهم المشتري أول شيء؟ الضوء والمساحة والمواقف — ابدأ بالأقوى فيهم.",
    },
    {
        "title": "عنوان إعلان عقاري جذاب",
        "use_case": "عناوين المنصات والإعلانات",
        "role": "خبير كتابة عناوين",
        "task": "{do} ستة عناوين للعقار، كل عنوان أقل من ٥٥ حرفًا ويحمل ميزة واحدة واضحة.",
        "variables": ["نوع العقار", "أقوى ميزة", "الحي", "الفئة المستهدفة"],
        "constraints": [
            "بلا كلمات مثل «فرصة العمر».",
            "لا تستخدم أرقامًا غير موجودة في المعطيات.",
            "لغة {tone}.",
        ],
        "output": "ستة عناوين مرقّمة، وبجانب كل عنوان الفئة الأنسب له.",
        "tip": "العنوان الذي يذكر الحي بالاسم يجذب باحثًا جادًا أكثر من عنوان عام.",
    },
    {
        "title": "رد واتساب على استفسار عقار",
        "use_case": "أول رد على رسالة مهتم",
        "role": "وسيط عقاري محترف",
        "task": "{do} رد واتساب على استفسار عن العقار: إجابة مباشرة، معلومتان مفيدتان، وسؤال لتحديد الموعد.",
        "variables": ["سؤال العميل", "نوع العقار", "السعر", "التوفر", "أقرب موعد للمعاينة"],
        "constraints": [
            "ابدأ بـ{greeting}، وبلا رسائل طويلة.",
            "لا تضغط على العميل للمعاينة في أول رسالة.",
            "لو المعلومة غير متوفرة اكتب {{تحتاج تأكيد}}.",
        ],
        "output": "رسالة واحدة بحد أقصى خمسة أسطر.",
        "tip": "{polite} اسأل عن موعد مناسب بدل «متى تحب؟» — الاقتراح يسهّل الرد.",
    },
    {
        "title": "الرد على اعتراض السعر",
        "use_case": "مفاوضة سعر عقار",
        "role": "مستشار بيع عقاري",
        "task": "{do} رد على عميل يرى السعر مرتفعًا، بمقارنة موضوعية مع بدائل مشابهة في نفس الحي.",
        "variables": ["السعر", "متوسط سعر المتر في الحي", "ميزة لا توجد في البدائل", "إمكانية تفاوض"],
        "constraints": [
            "لا تُقلل من العقارات المنافسة.",
            "لا تعد بتخفيض غير مؤكد.",
            "اذكر حقيقة واحدة قابلة للتحقق.",
        ],
        "output": "رد من ثلاثة أسطر + سؤال يفحص ميزانيته بلا إحراج.",
        "tip": "{thanks} السعر يُقارن دائمًا بما يقدّمه العقار، لا برقم مجرد.",
    },
    {
        "title": "متابعة بعد المعاينة",
        "use_case": "رسالة بعد زيارة العقار",
        "role": "وسيط عقاري",
        "task": "{do} رسالة متابعة بعد المعاينة، تفتح باب الأسئلة بلا ضغط.",
        "variables": ["اسم العميل", "العقار", "ملاحظة من الزيارة", "بدائل متاحة"],
        "constraints": [
            "شخصية ومحددة، بلا رسائل عامة.",
            "اذكر ملاحظة واحدة من الزيارة فعلًا.",
            "النبرة {tone}.",
        ],
        "output": "رسالة من ثلاثة أسطر + سؤالين محتملين مع ردود قصيرة جاهزة.",
        "tip": "{polite} المتابعة الأفضل تُرسل بعد يوم، لا بعد ساعة.",
    },
    {
        "title": "سكربت ريلز لجولة في العقار",
        "use_case": "فيديو قصير ٣٠ ثانية",
        "role": "كاتب سكربتات فيديو قصير",
        "task": "{do} سكربت جولة للعقار في ٣٠ ثانية: خطاف، ثلاث لقطات، وسطر إغلاق.",
        "variables": ["نوع العقار", "أقوى ثلاث ميزات", "الحي", "السعر"],
        "constraints": [
            "كل جملة تُقرأ في أقل من ٥ ثوانٍ.",
            "لا تصف ما لا يظهر في الصورة.",
            "النبرة {tone}.",
        ],
        "output": "جدول: الثانية، اللقطة، النص المنطوق، نص على الشاشة.",
        "tip": "الخطاف الأفضل في العقار يبدأ بالمساحة أو الإطلالة، لا بالترحيب.",
    },
    {
        "title": "نص بروشور مشروع",
        "use_case": "بروشور أو صفحة مشروع",
        "role": "كاتب محتوى تسويقي عقاري",
        "task": "{do} نص بروشور لمشروع سكني: فكرة المشروع، تجربة السكن، والخدمات القريبة.",
        "variables": ["اسم المشروع", "الموقع", "أنواع الوحدات", "الخدمات", "موعد التسليم"],
        "constraints": [
            "بلا أرقام أو مواعيد غير موجودة في المعطيات.",
            "أسلوب هادئ وواثق.",
            "فقرات قصيرة تصلح للتخطيط في البروشور.",
        ],
        "output": "عنوان المشروع + ثلاث فقرات + قائمة خدمات + خاتمة فيها دعوة للتواصل.",
        "tip": "{what} يميّز المشروع؟ غالبًا الخدمات القريبة، فاذكرها بأسمائها.",
    },
    {
        "title": "شرح خطة السداد",
        "use_case": "رسالة أو صفحة تفاصيل الدفع",
        "role": "مستشار تمويل عقاري",
        "task": "{do} شرح خطة السداد بلغة واضحة: الدفعة الأولى، الأقساط، والمدة، بلا تعقيد.",
        "variables": ["سعر العقار", "الدفعة الأولى", "عدد الأقساط", "المدة", "الجهة الممولة"],
        "constraints": [
            "لا تحسب فائدة أو نسبة لم أعطها لك.",
            "اذكر أن الأرقام تقديرية وتحتاج تأكيدًا من الجهة الممولة.",
            "بلا وعد بالموافقة على التمويل.",
        ],
        "output": "جدول مختصر + فقرة شرح من ثلاثة أسطر + سؤال يحدد جاهزية العميل.",
        "tip": "{thanks} الوضوح في خطة السداد يقلل المكالمات غير الجاهزة.",
    },
    {
        "title": "دليل الحي للعميل",
        "use_case": "محتوى يبني الثقة",
        "role": "كاتب محتوى محلي",
        "task": "{do} دليلًا قصيرًا عن الحي: مدارس، خدمات، طرق، وطبيعة السكان.",
        "variables": ["الحي", "المدينة", "أقرب ثلاث خدمات", "الطرق الرئيسية"],
        "constraints": [
            "لا تذكر أسماء مدارس أو مراكز لست متأكدًا منها.",
            "اذكر أن المسافات تقديرية.",
            "النبرة {tone}.",
        ],
        "output": "مقدمة قصيرة + أربع نقاط + سؤال يربط الدليل باحتياج العميل.",
        "tip": "{polite} الدليل الجيد يجاوب سؤال «هل أقدر أعيش هنا؟» لا سؤال «كم السعر؟».",
    },
    {
        "title": "دعوة لمعاينة أو يوم مفتوح",
        "use_case": "دعوة لمناسبة معاينة",
        "role": "منسّق فعاليات عقارية",
        "task": "{do} دعوة ليوم معاينة مفتوح، فيها الموعد والمكان وما سيحدث بالضبط.",
        "variables": ["اسم المشروع", "التاريخ والوقت", "الموقع", "ما سيقدَّم للزائر"],
        "constraints": [
            "بلا عبارات ضغط مثل «الأماكن تنفد» إن لم تكن صحيحة.",
            "معلومات الموعد والمكان في أول سطرين.",
            "النبرة {tone}.",
        ],
        "output": "دعوة من أربعة أسطر + سطر تأكيد الحضور + تذكير قصير قبل الموعد بيوم.",
        "tip": "{what} يجعل الحضور أعلى؟ ذكر ما سيخرج به الزائر من المعاينة.",
    },
    {
        "title": "عرض عقاري للمستثمر",
        "use_case": "مخاطبة مستثمر",
        "role": "محلّل استثمار عقاري",
        "task": "{do} عرضًا للمستثمر يوضّح العائد المتوقع ومساراته بلا مبالغة.",
        "variables": ["سعر الشراء", "الإيجار السنوي المتوقع", "المصروفات", "مدة الاستثمار", "المخاطر"],
        "constraints": [
            "لا تحسب عائدًا من أرقام غير معطاة.",
            "اذكر المخاطر بصراحة.",
            "أرقام فقط إن كانت في المعطيات، وإلا ضع {{تحتاج تأكيد}}.",
        ],
        "output": "ملخص في ثلاثة أسطر + جدول عائد تقديري + ثلاث نقاط مخاطر.",
        "tip": "{thanks} المستثمر يثق أكثر حين ترى المخاطر مكتوبة، لا مخفية.",
    },
    {
        "title": "إعادة تسويق لعميل قديم",
        "use_case": "قاعدة عملاء سابقة",
        "role": "مسوّق علاقات عملاء",
        "task": "{do} رسالة لعميل سابق تعرض عليه عقارًا مشابهًا أو فرصة بيع وحدته الحالية.",
        "variables": ["اسم العميل", "العقار السابق", "العرض الجديد", "سبب الملاءمة"],
        "constraints": [
            "بلا افتراض أن وضعه المالي تغيّر.",
            "اذكر سببًا واحدًا محددًا لملاءمة العرض.",
            "النبرة {tone}.",
        ],
        "output": "رسالة من ثلاثة أسطر + سؤال مفتوح بدل عرض مباشر.",
        "tip": "{polite} العميل القديم يفضّل رسالة تذكره بشيء خاص، لا رسالة جماعية.",
    },
]


# --------------------------------------------------------------------------- #
# النماذج
# --------------------------------------------------------------------------- #


@dataclass
class Prompt:
    id: str
    title: str
    use_case: str
    body: str
    variables: list[str]
    tips: str


@dataclass
class Pack:
    slug: str
    title: str
    dialect: str
    dialect_label: str
    domain: str
    domain_label: str
    price: float
    description: str
    tags: list[str]
    prompts: list[Prompt] = field(default_factory=list)

    @property
    def store_row(self) -> dict[str, object]:
        return {
            "Title": self.title,
            "Category": DOMAINS[self.domain]["store_category"],
            "description": self.description,
            "price": self.price,
            "preview_url": f"{PREVIEW_BASE}/{self.slug}",
        }


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE).strip().lower()
    return re.sub(r"[\s_]+", "-", text)


def render_prompt(spec: dict[str, object], dialect: dict[str, str]) -> str:
    constraints = "\n".join(f"- {line.format(**dialect)}" for line in spec["constraints"])  # type: ignore[index]
    variables = "\n".join(f"- {name}: «…»" for name in spec["variables"])  # type: ignore[index]
    body = f"""## الدور
أنت {spec['role']}، وتشتغل مع {dialect['audience']} في {dialect['region']}.

## المهمة
{str(spec['task']).format(**dialect)}

## المعطيات
{variables}

## قيود
{constraints}
- اكتب باللهجة {dialect['label']}، وممنوع تخلط لهجة ثانية.
- لو معلومة ناقصة، اكتب {{تحتاج تأكيد}} بدل ما تخترع.

## صيغة الإخراج
{spec['output']}

## نصيحة
{str(spec['tip']).format(**dialect)}"""
    return body


def build_pack(dialect_key: str, domain_key: str, specs: list[dict[str, object]], rng: random.Random) -> Pack:
    dialect = DIALECTS[dialect_key]
    domain = DOMAINS[domain_key]
    chosen = list(specs)
    rng.shuffle(chosen)
    slug = f"{dialect_key}-{domain_key}"
    title = f"حزمة أوامر {domain['label']} — لهجة {dialect['label']}"
    description = (
        f"{len(chosen)} أمرًا جاهزًا باللهجة {dialect['label']} في {domain['label']}. "
        f"{domain['promise']} كل أمر مبني على دور ومعطيات وصيغة إخراج، فتنسخه وتعبّي الفراغات وتحصل على نتيجة قابلة للاستخدام."
    )
    prompts = [
        Prompt(
            id=f"{slug}-{index:02d}",
            title=str(spec["title"]),
            use_case=str(spec["use_case"]),
            body=render_prompt(spec, dialect),
            variables=list(spec["variables"]),  # type: ignore[arg-type]
            tips=str(spec["tip"]).format(**dialect),
        )
        for index, spec in enumerate(chosen, start=1)
    ]
    tags = [domain["label"], f"لهجة {dialect['label']}", "ذكاء اصطناعي", "محتوى جاهز", "أوامر جاهزة"]
    return Pack(
        slug=slug,
        title=title,
        dialect=dialect_key,
        dialect_label=dialect["label"],
        domain=domain_key,
        domain_label=str(domain["label"]),
        price=float(domain["price"]),  # type: ignore[arg-type]
        description=description,
        tags=tags,
        prompts=prompts,
    )


# --------------------------------------------------------------------------- #
# الكتابة إلى الملفات
# --------------------------------------------------------------------------- #


def pack_readme(pack: Pack) -> str:
    dialect = DIALECTS[pack.dialect]
    domain = DOMAINS[pack.domain]
    titles = "\n".join(f"{i}. {prompt.title} — {prompt.use_case}" for i, prompt in enumerate(pack.prompts, start=1))
    return f"""# {pack.title}

> {pack.description}

- **اللهجة:** {pack.dialect_label} ({dialect['region']})
- **المجال:** {pack.domain_label}
- **عدد الأوامر:** {len(pack.prompts)}
- **السعر:** {pack.price:,.0f} {PRICE_CURRENCY}
- **الإصدار:** {VERSION}

## لمن هذه الحزمة
{domain['audience_note']}

## ما تحصل عليه
{titles}

## طريقة الاستخدام
1. افتح `prompts.md` واختر الأمر المناسب لحالتك.
2. انسخ نص الأمر كاملًا إلى ChatGPT أو Claude أو Gemini.
3. عبّي الفراغات بين «…» بمعلوماتك الحقيقية: اسم المنتج، السعر، المدينة.
4. إذا ظهر `{{{{تحتاج تأكيد}}}}` في الناتج، فمعناه أن المعلومة ناقصة — أضفها وأعد التوليد.
5. عدّل الناتج ليصير بصوت علامتك؛ الأمر نقطة بداية لا نص نهائي.

## نصائح للنتيجة الأفضل
- اكتب معطيات أكثر من الحاجة؛ الجودة تأتي من المعطيات لا من طول الأمر.
- جرّب الأمر مرتين: مرة لجمهور يبحث عن التوفير، ومرة لجمهور يبحث عن الجودة.
- احفظ النسخ التي نجحت معك، فهي أصولك التسويقية الحقيقية.

## الترخيص
استخدام تجاري شخصي أو داخل شركتك بلا حد على عدد الاستخدامات. غير مسموح بإعادة بيع الحزمة كما هي أو توزيع ملفاتها.

## الدعم
لأي تحديث أو أمر إضافي، راسل فريق Arab Templates مع رقم الإصدار {VERSION}.
"""


def pack_markdown(pack: Pack) -> str:
    chunks = [f"# {pack.title}\n", f"> {pack.description}\n", f"عدد الأوامر: {len(pack.prompts)}\n", "---\n"]
    for index, prompt in enumerate(pack.prompts, start=1):
        chunks.append(f"## {index}. {prompt.title}\n\n**الاستخدام:** {prompt.use_case}\n")
        chunks.append("**المعطيات المطلوبة:** " + "، ".join(prompt.variables) + "\n")
        chunks.append("```text\n" + prompt.body.strip() + "\n```\n")
        chunks.append(f"**نصيحة:** {prompt.tips}\n")
    return "\n".join(chunks)


def pack_plain(pack: Pack) -> str:
    lines = [f"{pack.title}", f"عدد الأوامر: {len(pack.prompts)}", ""]
    for index, prompt in enumerate(pack.prompts, start=1):
        lines.append(f"--- {index}. {prompt.title} ---")
        lines.append(prompt.body.strip())
        lines.append("")
    return "\n".join(lines)


def write_pack(pack: Pack, out_root: Path, *, make_zip: bool, generated_at: str) -> Path:
    folder = out_root / pack.slug
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "README.md").write_text(pack_readme(pack), encoding="utf-8")
    (folder / "prompts.md").write_text(pack_markdown(pack), encoding="utf-8")
    (folder / "prompts.txt").write_text(pack_plain(pack), encoding="utf-8")
    payload = {
        "version": VERSION,
        "generated_at": generated_at,
        "currency": PRICE_CURRENCY,
        "slug": pack.slug,
        "title": pack.title,
        "dialect": {"key": pack.dialect, "label": pack.dialect_label, "region": DIALECTS[pack.dialect]["region"]},
        "domain": {"key": pack.domain, "label": pack.domain_label},
        "price": pack.price,
        "description": pack.description,
        "tags": pack.tags,
        "prompt_count": len(pack.prompts),
        "license": "استخدام تجاري شخصي أو داخل شركتك؛ يُمنع إعادة بيع الملفات كما هي.",
        "store": pack.store_row,
        "prompts": [
            {"id": prompt.id, "title": prompt.title, "use_case": prompt.use_case, "variables": prompt.variables, "prompt": prompt.body}
            for prompt in pack.prompts
        ],
    }
    (folder / "pack.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if make_zip:
        archive = out_root / f"{pack.slug}.zip"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
            for name in ("README.md", "prompts.md", "prompts.txt", "pack.json"):
                bundle.write(folder / name, arcname=f"{pack.slug}/{name}")
    return folder


def write_catalog(packs: list[Pack], out_root: Path) -> None:
    rows = [pack.store_row for pack in packs]
    with (out_root / "catalog.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Title", "Category", "description", "price", "preview_url"])
        writer.writeheader()
        writer.writerows(rows)
    (out_root / "catalog.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = ["# فهرس حزم الأوامر\n", "| الحزمة | اللهجة | المجال | الأوامر | السعر |", "| --- | --- | --- | --- | --- |"]
    for pack in packs:
        lines.append(f"| [{pack.title}]({pack.slug}/README.md) | {pack.dialect_label} | {pack.domain_label} | {len(pack.prompts)} | {pack.price:,.0f} {PRICE_CURRENCY} |")
    total = sum(pack.price for pack in packs)
    lines += ["", f"**عدد الحزم:** {len(packs)} — **قيمة الكتالوج:** {total:,.0f} {PRICE_CURRENCY}"]
    (out_root / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
# الرفع إلى متجر Arab Templates
# --------------------------------------------------------------------------- #


def publish(packs: list[Pack], dry_run: bool) -> int:
    try:
        from bubble_data_sync import TEMPLATE_FIELDS, TEMPLATE_TYPE, BubbleClient, BubbleError, sync_records
    except ImportError as exc:  # pragma: no cover
        print(f"[✗] الرفع يحتاج bubble_data_sync.py — {exc}")
        return 2
    try:
        client = BubbleClient(verbose=False)
    except BubbleError as exc:
        print(f"[✗] إعداد غير مكتمل: {exc}")
        return 2
    rows = [pack.store_row for pack in packs]
    counts = sync_records(client, TEMPLATE_TYPE, rows, TEMPLATE_FIELDS, key="Title", dry_run=dry_run)
    return 0 if not counts["failed"] else 1


# --------------------------------------------------------------------------- #
# واجهة الأوامر
# --------------------------------------------------------------------------- #


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="توليد حزم أوامر AI باللهجات الخليجية لمنتجات Arab Templates.")
    parser.add_argument("--dialects", default="saudi,emirati,kuwaiti", help="لهجات مفصولة بفواصل: saudi,emirati,kuwaiti")
    parser.add_argument("--domains", default="ecommerce,realestate", help="مجالات: ecommerce,realestate")
    parser.add_argument("--out", default="prompt_packs", help="مجلد الإخراج")
    parser.add_argument("--zip", action="store_true", help="أنشئ ملف zip لكل حزمة (ملف البيع)")
    parser.add_argument("--publish", action="store_true", help="ارفع الكتالوج إلى جدول template في Bubble")
    parser.add_argument("--dry-run", action="store_true", help="معاينة الرفع بلا كتابة")
    parser.add_argument("--seed", type=int, default=7, help="بذرة ترتيب الأوامر (لإعادة إنتاج نفس الملفات)")
    parser.add_argument("--clean", action="store_true", help="احذف مجلد الإخراج قبل التوليد")
    args = parser.parse_args(argv)

    dialects = [item.strip() for item in args.dialects.split(",") if item.strip()]
    domains = [item.strip() for item in args.domains.split(",") if item.strip()]
    unknown_dialects = [item for item in dialects if item not in DIALECTS]
    unknown_domains = [item for item in domains if item not in DOMAINS]
    if unknown_dialects or unknown_domains:
        parser.error(f"قيم غير معروفة: لهجات {unknown_dialects} / مجالات {unknown_domains}")

    specs = {"ecommerce": ECOMMERCE_SPECS, "realestate": REALESTATE_SPECS}
    out_root = (HERE.parent / "products" / args.out) if not Path(args.out).is_absolute() else Path(args.out)
    if args.clean and out_root.exists():
        for child in out_root.iterdir():
            if child.is_dir():
                for file in child.iterdir():
                    file.unlink()
                child.rmdir()
            else:
                child.unlink()
    out_root.mkdir(parents=True, exist_ok=True)

    rng = random.Random(args.seed)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    packs: list[Pack] = []

    for dialect_key in dialects:
        for domain_key in domains:
            pack = build_pack(dialect_key, domain_key, specs[domain_key], rng)
            folder = write_pack(pack, out_root, make_zip=args.zip, generated_at=generated_at)
            packs.append(pack)
            print(f"[✓] {pack.slug}: {len(pack.prompts)} أمرًا — {pack.price:,.0f} {PRICE_CURRENCY} → {folder.name}/")

    write_catalog(packs, out_root)
    total = sum(pack.price for pack in packs)
    print(f"\n[✓] {len(packs)} حزمة، {sum(len(pack.prompts) for pack in packs)} أمرًا، قيمة كتالوج {total:,.0f} {PRICE_CURRENCY}")
    print(f"[i] الكتالوج: {out_root / 'catalog.csv'} و{out_root / 'catalog.json'}")
    print(f"[i] الفهرس: {out_root / 'index.md'}")

    if args.publish:
        return publish(packs, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
