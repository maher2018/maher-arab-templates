#!/usr/bin/env python3
"""خادم منتج Gulf Tax Compliance Pro.

يقدّم واجهة gulf_tax_template_pro ويعمل كمحرك خلفي لها:
  GET  /               الصفحة (CSS و JavaScript مدمجان داخلها)
  GET  /api/health     الحالة
  GET  /api/sample     نص فواتير نموذجي (واتساب)
  GET  /api/news       أخبار السوق من data/market_news.json
  GET  /api/rates      أسعار العملات مقابل الريال (حيّ مع لقطة احتياطية)
  POST /api/scan       مسح فواتير من نص أو ملف — عبر whatsapp_invoice_parser.py
  POST /api/assistant  مساعد ضريبي محلي بقواعد معرفة خليجية

محرك الفواتير الإلكترونية والإقرار الضريبي:
  GET  /api/countries  الدول ونسب الضريبة والدوريات
  POST /api/einvoice   إصدار فاتورة (حساب + QR بصيغة ZATCA/FTA + تجزئة)
  GET  /api/ledger     سجل المبيعات والمشتريات
  POST /api/ledger     إضافة صفوف مشتريات (من المسح)
  DELETE /api/ledger   حذف صف من السجل
  GET  /api/taxreturn  صافي الإقرار: ضريبة المبيعات − ضريبة المشتريات
  POST /api/ocr        استخراج بيانات فاتورة من صورة (OCR فعلي أو محاكاة)
  POST /api/support    رسالة إلى المحاسب + رقم تذكرة
  GET  /api/support    محادثات المحاسب السابقة

    python gulf_tax_template_pro/server.py --port 5075 --open
"""
from __future__ import annotations

import argparse
import html as html_lib
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from datetime import date, datetime
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
SCRIPTS = ROOT / "scripts"
DATA = ROOT / "data"
SNAPSHOT = BASE / "exchange_rates.json"

sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(BASE))
from whatsapp_invoice_parser import parse_invoice, split_invoices  # noqa: E402

import einvoice  # noqa: E402
import ledger  # noqa: E402
import ocr  # noqa: E402

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

SAMPLE_TEXT = """المورد: شركة النخيل للتجارة
التاريخ: 2026-11-01
الإجمالي قبل الضريبة: 1,000.00
الضريبة (15%): 150.00
الإجمالي: 1,150.00

المورد: مؤسسة الخليج للمقاولات
التاريخ: 2026-10-28
الإجمالي قبل الضريبة: 2,400.00
الضريبة (15%): 360.00
الإجمالي: 2,760.00

المورد: متجر الواحة
التاريخ: 2026-10-25
الإجمالي قبل الضريبة: 800.00
الضريبة (5%): 40.00
الإجمالي: 840.00
"""

PLANS = [
    {"key": "starter", "name": "الأساسية", "name_en": "Starter", "price": 899, "scans": 300, "batch": 100,
     "for": "مكتب محاسبة أو منشأة صغيرة بفواتير محدودة",
     "for_en": "A small accounting office or business with limited invoices",
     "features": ["مسح نص واتساب", "تصدير CSV", "مساعد ضريبي"],
     "features_en": ["WhatsApp text scanning", "CSV export", "Tax assistant"]},
    {"key": "growth", "name": "النمو", "name_en": "Growth", "price": 1490, "scans": 3000, "batch": 500,
     "for": "شركة متوسطة تستلم مئات الفواتير شهريًا",
     "for_en": "A mid-size company receiving hundreds of invoices every month",
     "features": ["مسح بالجملة ٥٠٠ فاتورة", "تصدير CSV وJSON", "أخبار وعملات", "أولوية دعم"],
     "features_en": ["500-invoice batch scan", "CSV and JSON export", "Market news and rates", "Priority support"]},
    {"key": "scale", "name": "المؤسسات", "name_en": "Enterprise", "price": 2990, "scans": 20000, "batch": 2000,
     "for": "مجموعة شركات وفروع متعددة",
     "for_en": "A group of companies with multiple branches",
     "features": ["مسح بالجملة ٢٠٠٠ فاتورة", "سعة شهرية ٢٠٠٠٠", "سماحية تجاوز ١٠٪", "تقارير متعددة الدول"],
     "features_en": ["2,000-invoice batch scan", "20,000 monthly capacity", "10% overflow grace", "Multi-country reports"]},
]
GRACE_RATIO = 0.10
MAX_INVOICES = 5000
USAGE_FILE = ROOT / "reports" / "usage" / "gulf_usage.json"

_usage_lock = threading.Lock()


def request_lang(payload: dict | None = None) -> str:
    """لغة الطلب: ?lang=en أو حقل JSON، وإلا العربية."""
    value = str(request.args.get("lang") or (payload or {}).get("lang") or "").strip().lower()
    return "en" if value.startswith("en") else "ar"


def plan_public(plan: dict, lang: str) -> dict:
    use_en = lang == "en"
    return {
        "key": plan["key"],
        "name": plan["name_en"] if use_en else plan["name"],
        "price": plan["price"], "scans": plan["scans"], "batch": plan["batch"],
        "for": plan["for_en"] if use_en else plan["for"],
        "features": plan["features_en"] if use_en else plan["features"],
    }


def _plan(key: str) -> dict:
    for plan in PLANS:
        if plan["key"] == (key or "").strip():
            return plan
    return PLANS[1]


def _usage_all() -> dict:
    try:
        return json.loads(USAGE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {}


def _usage_save(data: dict) -> None:
    USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    USAGE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def quota_state(account: str, plan_key: str) -> dict:
    plan = _plan(plan_key)
    capacity = int(plan["scans"])
    period = datetime.now().strftime("%Y-%m")
    with _usage_lock:
        record = _usage_all().get(account, {})
        used = int(record.get("used", 0)) if record.get("period") == period else 0
    grace = int(capacity * GRACE_RATIO)
    return {
        "account": account,
        "plan": plan["key"],
        "plan_name": plan["name"],
        "period": period,
        "capacity": capacity,
        "used": used,
        "remaining": max(capacity - used, 0),
        "grace": grace,
        "available": max(capacity + grace - used, 0),
        "monthly_only": True,
    }


def consume_quota(account: str, plan_key: str, count: int) -> dict:
    """السعة شهرية فقط: لا حدود لكل دقيقة أو لكل طلب، مع سماحية ١٠٪."""
    plan = _plan(plan_key)
    capacity = int(plan["scans"])
    period = datetime.now().strftime("%Y-%m")
    grace = int(capacity * GRACE_RATIO)
    with _usage_lock:
        data = _usage_all()
        record = data.get(account, {})
        used = int(record.get("used", 0)) if record.get("period") == period else 0
        available = max(capacity + grace - used, 0)
        accepted = min(count, available)
        data[account] = {"period": period, "used": used + accepted, "plan": plan["key"]}
        _usage_save(data)
    state = quota_state(account, plan_key)
    state["accepted"] = accepted
    state["deferred"] = count - accepted
    return state


_rates_cache: dict[str, object] = {"at": 0.0, "data": None}
_rates_lock = threading.Lock()


def invoice_dict(invoice) -> dict:
    return {
        "supplier": invoice.supplier,
        "date": invoice.invoice_date,
        "subtotal": invoice.subtotal,
        "tax": invoice.tax,
        "total": invoice.total,
        "rate": invoice.vat_rate,
        "currency": invoice.currency,
        "confidence": round(float(invoice.confidence or 0), 2),
        "warnings": invoice.warnings,
    }


def scan_text(text: str, account: str = "demo", plan_key: str = "growth") -> dict:
    chunks = [chunk for chunk in (split_invoices(text) or [text]) if chunk.strip()]
    truncated = 0
    if len(chunks) > MAX_INVOICES:
        truncated = len(chunks) - MAX_INVOICES
        chunks = chunks[:MAX_INVOICES]
    started = time.perf_counter()
    rows = [invoice_dict(parse_invoice(chunk)) for chunk in chunks]
    elapsed = round((time.perf_counter() - started) * 1000, 1)
    result = {
        "ok": True,
        "engine": "whatsapp_invoice_parser.py",
        "elapsed_ms": elapsed,
        "quota": consume_quota(account, plan_key, len(rows)),
        "totals": {
            "count": len(rows),
            "total": round(sum(float(r["total"] or 0) for r in rows), 2),
            "tax": round(sum(float(r["tax"] or 0) for r in rows), 2),
            "needs_review": sum(1 for r in rows if float(r["confidence"] or 0) < 0.8),
        },
        "invoices": rows,
    }
    if truncated:
        result["truncated"] = truncated
    return result


KNOWLEDGE = [
    (("نسبة", "نسب", "كم", "rate", "15", "5"), "نسب ضريبة القيمة المضافة:\n• السعودية ١٥٪\n• الإمارات ٥٪\n• الكويت: لا تُطبَّق ضريبة قيمة مضافة حاليًا (يُفعَّل القالب مع نسبتها صفرًا).\nحد التسجيل الإلزامي في السعودية ٣٧٥ ألف ريال، والاختياري ١٨٧٫٥ ألف ريال. في الإمارات ٣٧٥ ألف درهم إلزامي و١٨٧٫٥ ألف اختياري."),
    (("إقرار", "موعد", "مواعيد", "deadline", "ربع"), "مواعيد الإقرار:\n• السعودية: إقرار شهري أو ربع سنوي حسب حجم المنشأة، ويُقدَّم خلال الشهر التالي لنهاية الفترة.\n• الإمارات: إقرار ربع سنوي خلال ٢٨ يومًا من نهاية الربع.\n• الكويت: لا يوجد إقرار قيمة مضافة حاليًا.\nتأكد دائمًا من بوابة الهيئة في بلدك، فالتصنيف قد يغيّر الدورية."),
    (("فاتورة", "حقول", "fields", "إلكترونية"), "الحقول الأساسية للفاتورة الضريبية:\n• اسم المورد والرقم الضريبي\n• تاريخ الإصدار ورقم الفاتورة\n• وصف البنود والكمية والسعر\n• المبلغ قبل الضريبة، نسبة الضريبة، مبلغ الضريبة، الإجمالي\n• العملة وبيانات المشتري\n• رمز QR للفاتورة المبسطة في السعودية"),
    (("غرامة", "عقوبة", "penalty"), "الغرامات تختلف بالدولة، وأكثر أسبابها شيوعًا: عدم الإصدار، التأخر في تقديم الإقرار، أو عدم مطابقة بيانات المورد. استخدم المسح للتحقق من الحقول قبل الترحيل، وأرشف الفواتير ٥ سنوات على الأقل."),
    (("مسح", "واتساب", "دفعة", "bulk", "scan"), "المسح بالجملة:\n١. الصق نص محادثة واتساب أو أفلت ملف TXT/CSV.\n٢. امسح مرة واحدة — كل فاتورة تُفصل تلقائيًا وتُقرأ حقولها.\n٣. راجع الفواتير منخفضة الثقة فقط، ثم صدّر CSV.\nلا يوجد حد لعدد الفواتير في الطلب الواحد."),
    (("صادر", "مشتريات", "خصم", "input"), "الخصم الضريبي على المشتريات يحتاج فاتورة مطابقة ببيانات مورد صحيحة. الفواتير الناقصة أو بلا رقم ضريبي لا تُعتمد عند التدقيق، ولذلك يوسم المسح الفواتير منخفضة الثقة للمراجعة."),
    (("عملة", "عملات", "currency", "ريال", "درهم"), "الأسعار المعروضة إرشادية مقابل الريال السعودي وتُحدَّث من مصدر عام عند توفر الاتصال، مع لقطة احتياطية عند انقطاعه. للفاتورة استخدم عملة الإصدار الأصلية دائمًا."),
]


def assistant_answer(question: str, invoice: dict | None) -> dict:
    text = (question or "").strip().lower()
    answer = None
    for keys, reply in KNOWLEDGE:
        if any(key in text for key in keys):
            answer = reply
            break
    if answer is None:
        answer = ("أقدر أساعدك في نسب الضريبة، مواعيد الإقرار، حقول الفاتورة، الغرامات، "
                  "والمسح بالجملة. اسأل مثلًا: «ما موعد إقرار الربع في الإمارات؟»")
    if invoice:
        low = float(invoice.get("confidence") or 0) < 0.8
        answer += f"\n\nبخصوص فاتورة «{invoice.get('supplier') or 'بدون مورد'}»: الإجمالي {invoice.get('total')} والضريبة {invoice.get('tax')}."
        if low:
            answer += " ثقة القراءة منخفضة — راجع الإجمالي وسطر الضريبة قبل الترحيل."
    return {
        "mode": "local-knowledge",
        "answer": answer,
        "suggestions": [
            "ما موعد إقرار الربع في الإمارات؟",
            "ما الحقول المطلوبة في الفاتورة الإلكترونية؟",
            "كيف أمسح ٥٠٠ فاتورة من واتساب؟",
        ],
        "disclaimer": "معلومات إرشادية وليست استشارة ضريبية معتمدة.",
        "lang": "ar",
    }


KNOWLEDGE_EN = [
    (("rate", "vat", "percent", "percentage", "15", "5"),
     "Gulf VAT rates:\n• Saudi Arabia 15%\n• UAE 5%\n• Oman 5%\n• Bahrain 10%\n• Qatar and Kuwait: no VAT yet (the template runs at 0%).\nMandatory registration thresholds: SAR 375k in Saudi Arabia and AED 375k in the UAE."),
    (("deadline", "due", "filing", "return", "quarter"),
     "Filing deadlines:\n• Saudi Arabia: monthly or quarterly depending on business size, filed in the month after the period ends.\n• UAE: quarterly, within 28 days of the quarter end.\n• Qatar and Kuwait: no VAT return yet.\nAlways confirm on your authority's portal, as the category can change the cadence."),
    (("invoice", "field", "qr", "e-invoice"),
     "Required tax invoice fields:\n• Seller name and tax number\n• Issue date and invoice number\n• Line description, quantity and price\n• Net amount, VAT rate, VAT amount, total\n• Currency and buyer details\n• QR code for simplified invoices in Saudi Arabia"),
    (("penalty", "fine"),
     "Penalties differ per country; the common causes are missing invoices, late returns and mismatched seller details. Verify fields before posting and archive invoices for at least five years."),
    (("bulk", "scan", "whatsapp", "batch"),
     "Bulk scanning:\n1. Paste a WhatsApp transcript or drop a TXT/CSV file.\n2. Scan once — every invoice is split and parsed automatically.\n3. Review only the low-confidence rows, then export CSV.\nThere is no per-request limit."),
    (("input", "purchase", "deduct", "credit"),
     "Input VAT can only be deducted with a valid supplier invoice. Invoices missing a tax number are rejected at audit, which is why the scanner flags low-confidence rows for review."),
    (("currency", "exchange", "rate", "riyal", "dirham"),
     "Rates shown are indicative against the Saudi riyal and refresh from a public source when online, with an offline snapshot. Always issue the invoice in its legal country currency."),
    (("return", "net", "payable", "settle"),
     "Net VAT due = output VAT collected on sales − input VAT paid on purchases. If purchases exceed sales you carry a credit forward. Change country or period in the return tab to recalculate instantly."),
]

SUGGESTIONS = {
    "ar": ["ما موعد إقرار الربع في الإمارات؟", "ما الحقول المطلوبة في الفاتورة الإلكترونية؟",
           "كيف أمسح ٥٠٠ فاتورة من واتساب؟", "كيف أحسب صافي الإقرار؟"],
    "en": ["What is the quarterly filing deadline in the UAE?",
           "Which fields are required on an e-invoice?",
           "How do I scan 500 invoices from WhatsApp?",
           "How is net VAT calculated?"],
}


def assistant_answer(question: str, invoice: dict | None, lang: str = "ar") -> dict:
    use_en = lang == "en"
    text = (question or "").strip().lower()
    knowledge = KNOWLEDGE_EN if use_en else KNOWLEDGE
    answer = None
    for keys, reply in knowledge:
        if any(key in text for key in keys):
            answer = reply
            break
    if answer is None:
        answer = ("I can help with VAT rates, filing deadlines, invoice fields, penalties, bulk scanning "
                  "and net VAT. Ask for example: \"What is the VAT rate in Oman?\"") if use_en else (
                  "أقدر أساعدك في نسب الضريبة، مواعيد الإقرار، حقول الفاتورة، الغرامات، "
                  "والمسح بالجملة. اسأل مثلًا: «ما موعد إقرار الربع في الإمارات؟»")
    if invoice:
        low = float(invoice.get("confidence") or 0) < 0.8
        supplier = invoice.get("supplier") or ("unknown supplier" if use_en else "بدون مورد")
        if use_en:
            answer += f"\n\nAbout the invoice from «{supplier}»: total {invoice.get('total')} and VAT {invoice.get('tax')}."
            if low:
                answer += " Confidence is low — review the total and VAT line before posting."
        else:
            answer += f"\n\nبخصوص فاتورة «{supplier}»: الإجمالي {invoice.get('total')} والضريبة {invoice.get('tax')}."
            if low:
                answer += " ثقة القراءة منخفضة — راجع الإجمالي وسطر الضريبة قبل الترحيل."
    return {
        "mode": "local-knowledge",
        "lang": lang,
        "answer": answer,
        "suggestions": SUGGESTIONS["en" if use_en else "ar"],
        "disclaimer": ("Guidance only — not certified tax advice." if use_en
                       else "معلومات إرشادية وليست استشارة ضريبية معتمدة."),
    }


def fetch_rates() -> dict:
    with _rates_lock:
        cached = _rates_cache["data"]
        if cached and time.time() - float(_rates_cache["at"]) < 900:
            return cached
    data = None
    try:
        req = urllib.request.Request(
            "https://open.er-api.com/v6/latest/SAR",
            headers={"User-Agent": "ArabTemplates/1.0"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        src = payload.get("rates") or {}
        wanted = ["USD", "AED", "KWD", "QAR", "OMR", "BHD", "EGP", "EUR"]
        data = {
            "base": "SAR",
            "source": "open.er-api.com",
            "stale": False,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "rates": {code: round(float(src[code]), 4) for code in wanted if code in src},
            "changes": {code: 0 for code in wanted if code in src},
        }
    except Exception:
        data = None
    if not data or not data.get("rates"):
        try:
            data = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
            data["stale"] = True
        except (FileNotFoundError, ValueError):
            data = {"base": "SAR", "source": "لا يوجد", "stale": True, "updated_at": "—",
                    "rates": {}, "changes": {}}
    with _rates_lock:
        _rates_cache["at"] = time.time()
        _rates_cache["data"] = data
    return data


def market_news(lang: str = "ar") -> dict:
    try:
        raw = json.loads((DATA / "market_news.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {"items": [], "updated_at": "—"}
    items = raw.get("items", []) if isinstance(raw, dict) else raw
    items = sorted(items, key=lambda row: str(row.get("date") or ""), reverse=True)
    if lang == "en":
        items = [{
            "date": row.get("date"), "tag": row.get("tag_en") or row.get("tag"),
            "title": row.get("title_en") or row.get("title"),
            "summary": row.get("summary_en") or row.get("summary"),
            "action": row.get("action_en") or row.get("action"),
            "source": row.get("source_en") or row.get("source"),
        } for row in items]
    return {"items": items, "updated_at": (raw or {}).get("updated_at", "—"), "lang": lang}


@app.get("/")
def index():
    return send_from_directory(BASE, "index.html")


@app.get("/favicon.ico")
def favicon():
    return ("", 204)


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "engine": "whatsapp_invoice_parser.py",
                    "time": datetime.now().isoformat(timespec="seconds")})


@app.get("/api/sample")
def sample():
    return jsonify({"text": SAMPLE_TEXT})


@app.get("/api/news")
def news():
    return jsonify(market_news(request_lang()))


@app.get("/api/plans")
def plans():
    lang = request_lang()
    return jsonify({"plans": [plan_public(plan, lang) for plan in PLANS], "lang": lang,
                    "grace_ratio": GRACE_RATIO, "max_invoices": MAX_INVOICES})


@app.get("/api/quota")
def quota():
    account = (request.args.get("account") or "demo").strip()[:64] or "demo"
    plan_key = (request.args.get("plan") or "growth").strip()
    lang = request_lang()
    state = quota_state(account, plan_key)
    state["plan_name"] = plan_public(_plan(plan_key), lang)["name"]
    state["lang"] = lang
    return jsonify(state)


@app.get("/api/rates")
def rates():
    return jsonify(fetch_rates())


@app.post("/api/scan")
def scan():
    account = "demo"
    plan_key = "growth"
    if request.files:
        upload = next(iter(request.files.values()))
        raw = upload.read()
        text = ""
        for encoding in ("utf-8", "utf-8-sig", "cp1256"):
            try:
                text = raw.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        if not text:
            return jsonify({"ok": False, "error": "تعذّر قراءة الملف — استخدم ترميز UTF-8"}), 400
        account = (request.form.get("account") or "demo").strip()[:64] or "demo"
        plan_key = (request.form.get("plan") or "growth").strip()
    else:
        payload = request.get_json(silent=True) or {}
        text = str(payload.get("text") or "")
        account = str(payload.get("account") or "demo").strip()[:64] or "demo"
        plan_key = str(payload.get("plan") or "growth").strip()
    if not text.strip():
        return jsonify({"ok": False, "error": "لا يوجد نص فواتير"}), 400
    return jsonify(scan_text(text[:800_000], account, plan_key))


@app.get("/api/countries")
def countries():
    lang = request_lang()
    meta = einvoice.country_meta(einvoice.DEFAULT_COUNTRY, lang)
    return jsonify({
        "countries": einvoice.countries_public(lang),
        "currencies": einvoice.currencies_public(lang),
        "default": meta,
        "periods": einvoice.periods(meta["code"]),
        "max_items": einvoice.MAX_ITEMS,
        "lang": lang,
    })


@app.get("/api/detect")
def detect():
    """اكتشاف تلقائي للدولة والعملة من المنطقة الزمنية ولغة المتصفح."""
    lang = request_lang()
    result = einvoice.detect_country(
        request.args.get("tz") or request.args.get("timezone"),
        request.headers.get("Accept-Language"),
        lang,
    )
    result["ok"] = True
    result["lang"] = lang
    return jsonify(result)


@app.post("/api/einvoice")
def einvoice_build():
    payload = request.get_json(silent=True) or {}
    account = str(payload.get("account") or "demo").strip()[:64] or "demo"
    try:
        invoice = einvoice.build_invoice(payload)
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    if payload.get("save"):
        invoice["saved"] = ledger.add_sale(account, invoice)
    return jsonify(invoice)


@app.get("/api/ledger")
def ledger_get():
    account = (request.args.get("account") or "demo").strip()[:64] or "demo"
    data = ledger.load(account)
    return jsonify({"ok": True, "account": account, "sales": data["sales"][:200],
                    "purchases": data["purchases"][:200],
                    "counts": {"sales": len(data["sales"]), "purchases": len(data["purchases"])}})


@app.post("/api/ledger")
def ledger_post():
    payload = request.get_json(silent=True) or {}
    account = str(payload.get("account") or "demo").strip()[:64] or "demo"
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        return jsonify({"ok": False, "error": "لا توجد صفوف لإضافتها"}), 400
    added = ledger.add_purchases(account, rows[:500], str(payload.get("source") or "manual")[:24])
    return jsonify({"ok": True, "added": added, "count": len(added)})


@app.delete("/api/ledger/<kind>/<entry_id>")
def ledger_delete(kind: str, entry_id: str):
    account = (request.args.get("account") or "demo").strip()[:64] or "demo"
    if not ledger.delete_entry(account, kind, entry_id):
        return jsonify({"ok": False, "error": "الصف غير موجود"}), 404
    return jsonify({"ok": True, "deleted": entry_id})


AUDIT_PENALTY = {"critical": 25, "warning": 8}


def _num(value: object) -> float | None:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _audit_invoice(entry: dict, duplicated: set[str], today: str) -> list[dict]:
    """يفحص فاتورة محفوظة ويعيد قائمة ملاحظات بأكواد تُعرَض مترجمة في الواجهة."""
    findings: list[dict] = []
    number = str(entry.get("number") or "—")

    def add(code: str, severity: str, **extra: object) -> None:
        row = {"code": code, "severity": severity, "number": number, "date": entry.get("date")}
        row.update({key: value for key, value in extra.items() if value is not None})
        findings.append(row)

    legacy = "qr_payload" not in entry
    seller_vat = str(entry.get("seller_vat") or "").strip()
    buyer_vat = str(entry.get("buyer_vat") or "").strip()
    country = str(entry.get("country") or "").upper()

    if legacy:
        add("legacy_record", "warning")
    else:
        if not seller_vat:
            add("vat_missing", "critical")
        else:
            try:
                einvoice.validate_tax_no(country, seller_vat, "VAT", "en")
            except (ValueError, KeyError):
                add("vat_invalid", "critical")
        if not str(entry.get("qr_payload") or "").strip():
            add("qr_missing", "critical")
        if not str(entry.get("hash") or "").strip():
            add("hash_missing", "warning")
        if entry.get("items_count") == 0:
            add("items_missing", "warning")

    if not str(entry.get("buyer") or "").strip():
        add("buyer_missing", "warning")
    if not buyer_vat:
        add("buyer_vat_missing", "warning")

    subtotal = _num(entry.get("subtotal"))
    tax = _num(entry.get("tax"))
    total = _num(entry.get("total"))
    rate = _num(entry.get("vat_rate"))
    if subtotal is not None and tax is not None and rate is not None:
        expected = round(subtotal * rate / 100, 2)
        diff = round(tax - expected, 2)
        if abs(diff) > max(0.05, abs(subtotal) * 0.001):
            add("tax_mismatch", "critical", diff=diff, expected=expected)
    if subtotal is not None and tax is not None and total is not None:
        diff = round(subtotal + tax - total, 2)
        if abs(diff) > 0.05:
            add("total_mismatch", "critical", diff=diff)
    if subtotal is None or tax is None or total is None:
        add("amounts_missing", "critical")

    issued = str(entry.get("date") or "").strip()
    if not issued:
        add("bad_date", "warning")
    elif issued[:10] > today:
        add("future_date", "warning")

    if number != "—" and number in duplicated:
        add("duplicate_number", "warning")
    if not entry.get("currency") or not country:
        add("meta_missing", "warning")
    return findings


def audit_sales(rows: list[dict]) -> dict:
    today = date.today().isoformat()
    numbers = [str(row.get("number")) for row in rows if row.get("number")]
    duplicated = {number for number in numbers if numbers.count(number) > 1}
    findings: list[dict] = []
    scores: list[int] = []
    critical_count = warning_count = clean = 0
    for row in rows:
        row_findings = _audit_invoice(row if isinstance(row, dict) else {}, duplicated, today)
        findings.extend(row_findings)
        penalty = sum(AUDIT_PENALTY.get(item["severity"], 0) for item in row_findings)
        scores.append(max(0, 100 - penalty))
        if any(item["severity"] == "critical" for item in row_findings):
            critical_count += 1
        elif row_findings:
            warning_count += 1
        if not row_findings:
            clean += 1
    score = round(sum(scores) / len(scores)) if scores else 100
    grade = "safe" if score >= 90 else "review" if score >= 70 else "high" if score >= 40 else "critical"
    order = {"critical": 0, "warning": 1}
    recommendations: list[str] = []
    for item in sorted(findings, key=lambda f: order.get(f["severity"], 2)):
        if item["code"] not in recommendations:
            recommendations.append(item["code"])
    return {
        "ok": True,
        "scanned": len(rows),
        "score": score,
        "grade": grade,
        "counts": {
            "critical": critical_count,
            "warning": warning_count,
            "clean": clean,
            "critical_findings": sum(1 for f in findings if f["severity"] == "critical"),
            "warning_findings": sum(1 for f in findings if f["severity"] == "warning"),
        },
        "findings": findings[:200],
        "recommendations": recommendations,
        "checked_at": datetime.now().isoformat(timespec="seconds"),
    }


@app.get("/api/audit")
def audit():
    account = (request.args.get("account") or "demo").strip()[:64] or "demo"
    data = ledger.load(account)
    result = audit_sales([row for row in data["sales"] if isinstance(row, dict)])
    result["account"] = account
    return jsonify(result)


def _month_key(value: object) -> str:
    text = str(value or "")[:7]
    return text if re.match(r"^\d{4}-\d{2}$", text) else ""


def _month_shift(key: str, delta: int) -> str:
    year, month = int(key[:4]), int(key[5:7])
    total = year * 12 + (month - 1) + delta
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


def _forecast(values: list[float], steps: int) -> list[float]:
    """توقع بسيط: مزيج من اتجاه الانحدار الخطي ومتوسط آخر ثلاث قيم."""
    if not values:
        return [0.0] * steps
    if len(values) == 1:
        return [max(0.0, values[0])] * steps
    n = len(values)
    mean_x = (n - 1) / 2
    mean_y = sum(values) / n
    denom = sum((index - mean_x) ** 2 for index in range(n)) or 1
    slope = sum((index - mean_x) * (value - mean_y) for index, value in enumerate(values)) / denom
    recent = values[-3:]
    recent_avg = sum(recent) / len(recent)
    out: list[float] = []
    for step in range(1, steps + 1):
        trend = mean_y + slope * ((n - 1 + step) - mean_x)
        blended = 0.6 * trend + 0.4 * recent_avg
        out.append(round(max(0.0, blended), 2))
    return out


def cashflow_analysis(sales: list[dict], purchases: list[dict], months: int = 3) -> dict:
    months = max(1, min(6, int(months or 3)))
    current = datetime.now().strftime("%Y-%m")
    history = [_month_shift(current, -offset) for offset in range(5, -1, -1)]
    inflow = {key: 0.0 for key in history}
    outflow = {key: 0.0 for key in history}
    for row in sales:
        key = _month_key(row.get("date"))
        if key in inflow:
            inflow[key] += _num(row.get("total")) or 0.0
    for row in purchases:
        key = _month_key(row.get("date"))
        if key in outflow:
            outflow[key] += _num(row.get("total")) or 0.0
    series = [{"month": key, "inflow": round(inflow[key], 2), "outflow": round(outflow[key], 2),
               "net": round(inflow[key] - outflow[key], 2)} for key in history]
    forecast_in = _forecast([item["inflow"] for item in series], months)
    forecast_out = _forecast([item["outflow"] for item in series], months)
    cumulative = round(sum(item["net"] for item in series), 2)
    forecast: list[dict] = []
    for index in range(months):
        net = round(forecast_in[index] - forecast_out[index], 2)
        cumulative = round(cumulative + net, 2)
        forecast.append({"month": _month_shift(current, index + 1), "inflow": forecast_in[index],
                         "outflow": forecast_out[index], "net": net, "cumulative": cumulative})

    # كشف الهدر: فاتورة مورد أعلى بكثير من خط أساسه، أو قفزة شهرية في إجمالي المورد
    by_supplier: dict[str, list[dict]] = {}
    for row in purchases:
        name = str(row.get("supplier") or "").strip() or "—"
        by_supplier.setdefault(name, []).append(row)
    all_amounts = sorted((_num(row.get("total")) or 0.0) for row in purchases)
    median = all_amounts[len(all_amounts) // 2] if all_amounts else 0.0
    anomalies: list[dict] = []
    for supplier, rows in by_supplier.items():
        amounts = [(_num(row.get("total")) or 0.0) for row in rows]
        count = len(amounts)
        mean = sum(amounts) / count if count else 0.0
        variance = sum((value - mean) ** 2 for value in amounts) / count if count else 0.0
        std = variance ** 0.5
        for row, amount in zip(rows, amounts):
            if amount <= 0:
                continue
            ratio = round(amount / mean, 2) if mean else 0.0
            if count >= 2 and std > 0 and amount > mean + 2 * std and amount > mean * 1.4:
                anomalies.append({"supplier": supplier, "amount": round(amount, 2), "date": row.get("date"),
                                  "baseline": round(mean, 2), "ratio": ratio, "severity": "high", "code": "outlier"})
            elif count == 1 and median > 0 and amount > median * 2:
                anomalies.append({"supplier": supplier, "amount": round(amount, 2), "date": row.get("date"),
                                  "baseline": round(median, 2), "ratio": round(amount / median, 2),
                                  "severity": "medium", "code": "single_large"})
        monthly: dict[str, float] = {}
        for row in rows:
            key = _month_key(row.get("date"))
            if key:
                monthly[key] = monthly.get(key, 0.0) + (_num(row.get("total")) or 0.0)
        keys = sorted(monthly)
        for previous, following in zip(keys, keys[1:]):
            if monthly[previous] > 0 and monthly[following] > monthly[previous] * 1.8:
                anomalies.append({"supplier": supplier, "amount": round(monthly[following], 2),
                                  "date": following, "baseline": round(monthly[previous], 2),
                                  "ratio": round(monthly[following] / monthly[previous], 2),
                                  "severity": "medium", "code": "monthly_spike"})
    anomalies.sort(key=lambda item: item["amount"], reverse=True)

    total_in = round(sum(item["inflow"] for item in series), 2)
    total_out = round(sum(item["outflow"] for item in series), 2)
    active = [item for item in series if item["inflow"] or item["outflow"]]
    avg_net = round(sum(item["net"] for item in active) / len(active), 2) if active else 0.0
    runway = round(cumulative / abs(avg_net), 1) if avg_net < 0 and cumulative > 0 else None
    return {
        "ok": True,
        "months": months,
        "history": series,
        "forecast": forecast,
        "totals": {"inflow": total_in, "outflow": total_out, "net": round(total_in - total_out, 2)},
        "avg_net": avg_net,
        "runway_months": runway,
        "anomalies": anomalies[:20],
        "method": "trend_blend",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }


@app.get("/api/cashflow")
def cashflow():
    account = (request.args.get("account") or "demo").strip()[:64] or "demo"
    try:
        months = int(request.args.get("months") or 3)
    except ValueError:
        months = 3
    data = ledger.load(account)
    result = cashflow_analysis(
        [row for row in data["sales"] if isinstance(row, dict)],
        [row for row in data["purchases"] if isinstance(row, dict)],
        months,
    )
    result["account"] = account
    result["currency"] = (einvoice.country_meta(request.args.get("country") or einvoice.DEFAULT_COUNTRY).get("currency") or "SAR")
    return jsonify(result)


@app.get("/api/taxreturn")
def taxreturn():
    account = (request.args.get("account") or "demo").strip()[:64] or "demo"
    country = request.args.get("country") or einvoice.DEFAULT_COUNTRY
    period = request.args.get("period") or datetime.now().strftime("%Y-%m")
    try:
        return jsonify(ledger.summary(account, country, period, request_lang()))
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.post("/api/ocr")
def ocr_scan():
    lang = request_lang()
    if str(request.form.get("lang") or "").lower().startswith("en"):
        lang = "en"
    upload = request.files.get("image") or (next(iter(request.files.values())) if request.files else None)
    if not upload:
        return jsonify({"ok": False, "error": "أرفق صورة فاتورة" if lang == "ar" else "Attach an invoice image"}), 400
    raw = upload.read()
    account = (request.form.get("account") or "demo").strip()[:64] or "demo"
    try:
        result = ocr.extract(raw, upload.filename or "image.png", lang)
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    except Exception as exc:  # pragma: no cover - حماية من فشل OCR غير المتوقع
        return jsonify({"ok": False, "error": f"تعذّر تحليل الصورة: {type(exc).__name__}"}), 500
    if str(request.form.get("save") or "").lower() in ("1", "true", "yes"):
        result["saved"] = ledger.add_purchases(account, [result["invoice"]], "ocr")
    return jsonify(result)


ACCOUNTANT_REPLY = {
    "ar": ("وصلت رسالتك إلى المحاسب وسيُرد عليك خلال يوم عمل. "
           "في هذه النسخة المحلية يُحفظ الطلب في سجل الحساب ويظهر رقم التذكرة أدناه، "
           "ويمكنك متابعة الأسئلة الفورية مع المساعد الضريبي في الأعلى."),
    "en": ("Your message reached the accountant and you will get a reply within one business day. "
           "In this local build the request is stored in your account ledger and a ticket number is shown below; "
           "use the tax assistant above for instant answers meanwhile."),
}


@app.post("/api/support")
def support_post():
    payload = request.get_json(silent=True) or {}
    lang = request_lang(payload)
    account = str(payload.get("account") or "demo").strip()[:64] or "demo"
    message = str(payload.get("message") or "").strip()
    if not message:
        return jsonify({"ok": False, "error": "اكتب نص الرسالة" if lang == "ar" else "Enter your message"}), 400
    if len(message) > 2000:
        return jsonify({"ok": False,
                        "error": "الرسالة أطول من ٢٠٠٠ حرف" if lang == "ar" else "Message is longer than 2000 characters"}), 400
    topic = str(payload.get("topic") or ("استشارة ضريبية" if lang == "ar" else "Tax consultation"))
    entry = ledger.add_message(account, topic, message)
    return jsonify({"ok": True, "ticket": entry["ticket"], "entry": entry,
                    "reply": ACCOUNTANT_REPLY[lang], "lang": lang})


@app.get("/api/support")
def support_get():
    account = (request.args.get("account") or "demo").strip()[:64] or "demo"
    return jsonify({"ok": True, "messages": ledger.list_messages(account)[:50]})


@app.post("/api/assistant")
def assistant():
    payload = request.get_json(silent=True) or {}
    lang = request_lang(payload)
    question = str(payload.get("question") or "")
    if len(question) > 1000:
        return jsonify({"ok": False,
                        "error": "السؤال طويل جدًا" if lang == "ar" else "Question is too long"}), 400
    return jsonify(assistant_answer(question, payload.get("invoice"), lang))


# ===================== SMTP2GO — إرسال الفواتير بالبريد =====================
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
DEFAULT_AFFILIATE_LINK = "https://www.smtp2go.com/?via=arab-templates"
SMTP2GO_ENDPOINT = "https://api.smtp2go.com/v3/email/send"
ENV_FILES = (ROOT / ".env", ROOT / "scripts" / ".env", BASE / ".env")

EMAIL_STRINGS = {
    "missing_key": ("حساب SMTP2GO غير مربوط بعد: أضف SMTP2GO_API_KEY في ملف .env، "
                    "أو ابدأ من زر التسجيل السريع لإنشاء الحساب ثم انسخ المفتاح.",
                    "SMTP2GO is not linked yet: add SMTP2GO_API_KEY to your .env file, "
                    "or use the quick signup button to create the account, then paste the key."),
    "bad_to": ("بريد المستلم غير صالح", "Invalid recipient email address"),
    "bad_sender": ("بريد المُرسل غير صالح — استخدم بريدًا موثقًا في SMTP2GO",
                   "Invalid sender email — use an address verified in SMTP2GO"),
    "no_invoice": ("أصدر الفاتورة أولًا قبل إرسالها بالبريد", "Issue the invoice before emailing it"),
    "sent": ("أُرسلت الفاتورة {number} إلى {to}", "Invoice {number} was sent to {to}"),
    "test_sent": ("أُرسلت رسالة اختبار إلى {to} — تحقق من صندوق الوارد",
                  "A test message was sent to {to} — check the inbox"),
    "provider_error": ("رفض SMTP2GO الطلب: {detail}", "SMTP2GO rejected the request: {detail}"),
    "network": ("تعذّر الوصول إلى SMTP2GO: {detail}", "Could not reach SMTP2GO: {detail}"),
}

EMAIL_LABELS = {
    "ar": {"title": "فاتورة ضريبية", "number": "رقم الفاتورة", "date": "التاريخ", "from": "من",
           "to": "إلى", "item": "البند", "qty": "الكمية", "price": "السعر", "net": "الصافي",
           "vat": "الضريبة", "total": "الإجمالي", "subtotal": "قبل الضريبة", "grand": "الإجمالي المستحق",
           "vat_no": "الرقم الضريبي", "qr": "حمولة QR", "hash": "تجزئة الفاتورة",
           "footer": "فاتورة إلكترونية صادرة عن نظام الامتثال الضريبي الخليجي.",
           "test_subject": "اختبار إعداد البريد — SMTP2GO",
           "test_body": "نجح ربط SMTP2GO بالقالب الضريبي. سيصل بريد الفواتير من هذا العنوان.",
           "invoice_subject": "فاتورة {number} من {seller}"},
    "en": {"title": "Tax Invoice", "number": "Invoice no.", "date": "Date", "from": "From",
           "to": "To", "item": "Item", "qty": "Qty", "price": "Price", "net": "Net",
           "vat": "VAT", "total": "Total", "subtotal": "Subtotal", "grand": "Total due",
           "vat_no": "Tax number", "qr": "QR payload", "hash": "Invoice hash",
           "footer": "E-invoice issued by the Gulf Tax Compliance system.",
           "test_subject": "Email setup test — SMTP2GO",
           "test_body": "SMTP2GO is now linked to the tax template. Invoice email will arrive from this address.",
           "invoice_subject": "Invoice {number} from {seller}"},
}


def es(lang: str, key: str, **vars: object) -> str:
    ar, en = EMAIL_STRINGS[key]
    text = en if lang == "en" else ar
    return text.format(**vars) if vars else text


def _load_env_files() -> None:
    """يقرأ .env المحلي (غير المتتبَّع) دون تجاوز متغيرات البيئة الحقيقية."""
    for path in ENV_FILES:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (FileNotFoundError, OSError, UnicodeDecodeError):
            continue
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env_files()


def smtp2go_config() -> dict:
    """إعدادات SMTP2GO العامة — المفتاح لا يُعاد أبدًا إلى المتصفح."""
    return {
        "provider": "smtp2go",
        "configured": bool((os.environ.get("SMTP2GO_API_KEY") or "").strip()),
        "api_url": SMTP2GO_ENDPOINT,
        "affiliate_link": (os.environ.get("SMTP2GO_AFFILIATE_LINK") or DEFAULT_AFFILIATE_LINK).strip(),
        "sender_default": (os.environ.get("SMTP2GO_SENDER") or "").strip(),
        "sender_name_default": (os.environ.get("SMTP2GO_SENDER_NAME") or "Arab Templates").strip(),
        "env_var": "SMTP2GO_API_KEY",
        "docs": "https://support.smtp2go.com/hc/en-gb/articles/4409244343561-SMTP2GO-API",
    }


def _money(value: object) -> str:
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value or "0.00")


def invoice_email_html(invoice: dict, lang: str) -> tuple[str, str]:
    """يبني جسم HTML ونصًا بديلًا لبريد الفاتورة بعملة الفاتورة القانونية."""
    labels = EMAIL_LABELS["en" if lang == "en" else "ar"]
    currency = invoice.get("currency") or "SAR"
    seller = invoice.get("seller") or {}
    buyer = invoice.get("buyer") or {}
    rows = []
    plain = []
    for item in invoice.get("items") or []:
        rows.append(
            "<tr>"
            f"<td style='padding:6px 8px;border-bottom:1px solid #e3e8ee'>{html_lib.escape(str(item.get('description') or ''))}</td>"
            f"<td style='padding:6px 8px;border-bottom:1px solid #e3e8ee;text-align:center'>{_money(item.get('quantity'))}</td>"
            f"<td style='padding:6px 8px;border-bottom:1px solid #e3e8ee;text-align:center'>{_money(item.get('unit_price'))}</td>"
            f"<td style='padding:6px 8px;border-bottom:1px solid #e3e8ee;text-align:center'>{_money(item.get('net'))}</td>"
            f"<td style='padding:6px 8px;border-bottom:1px solid #e3e8ee;text-align:center'>{_money(item.get('tax'))}</td>"
            f"<td style='padding:6px 8px;border-bottom:1px solid #e3e8ee;text-align:center'>{_money(item.get('total'))}</td>"
            "</tr>"
        )
        plain.append(f"- {item.get('description')} × {item.get('quantity')} = {_money(item.get('total'))} {currency}")
    qr = (invoice.get("qr") or {}).get("payload") or ""
    head = (
        "<html><body style='margin:0;background:#f4f7fa;padding:24px;font-family:Tahoma,Segoe UI,Arial,sans-serif;color:#12263a'>"
        "<div style='max-width:640px;margin:0 auto;background:#fff;border:1px solid #e3e8ee;border-radius:14px;padding:22px'>"
        f"<h1 style='margin:0 0 4px;font-size:20px'>{labels['title']}</h1>"
        f"<p style='margin:0 0 2px;color:#5b6b7c;font-size:13px'>"
        f"{labels['number']}: <b>{html_lib.escape(str(invoice.get('number') or ''))}</b> · "
        f"{labels['date']}: {html_lib.escape(str(invoice.get('issued_at') or ''))}</p>"
        f"<p style='margin:0 0 12px;color:#5b6b7c;font-size:13px'>{labels['from']}: "
        f"{html_lib.escape(str(seller.get('name') or ''))} · {labels['vat_no']}: "
        f"{html_lib.escape(str(seller.get('vat_number') or ''))}</p>"
        f"<p style='margin:0 0 12px;font-size:13px'>{labels['to']}: "
        f"{html_lib.escape(str(buyer.get('name') or ''))}</p>"
        "<table style='width:100%;border-collapse:collapse;font-size:13px'>"
        f"<thead><tr style='background:#eef4f7;text-align:center'>"
        f"<th style='padding:7px 8px;text-align:start'>{labels['item']}</th><th style='padding:7px 8px'>{labels['qty']}</th>"
        f"<th style='padding:7px 8px'>{labels['price']}</th><th style='padding:7px 8px'>{labels['net']}</th>"
        f"<th style='padding:7px 8px'>{labels['vat']}</th><th style='padding:7px 8px'>{labels['total']}</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
        "<div style='margin-top:14px;font-size:13px;text-align:end'>"
        f"<p style='margin:2px 0'>{labels['subtotal']}: <b>{_money(invoice.get('subtotal'))} {currency}</b></p>"
        f"<p style='margin:2px 0'>{labels['vat']}: <b>{_money(invoice.get('tax'))} {currency}</b></p>"
        f"<p style='margin:6px 0;font-size:16px'>{labels['grand']}: <b>{_money(invoice.get('total'))} {currency}</b></p>"
        "</div>"
    )
    if qr:
        head += (f"<p style='margin:12px 0 2px;font-size:11px;color:#5b6b7c'>{labels['qr']}</p>"
                 f"<p style='margin:0;font-family:Consolas,monospace;font-size:10px;word-break:break-all;color:#5b6b7c'>{qr}</p>")
    if invoice.get("hash"):
        head += (f"<p style='margin:8px 0 0;font-size:10px;color:#8a9aa8'>{labels['hash']}: "
                 f"{html_lib.escape(str(invoice.get('hash')))}</p>")
    head += (f"<p style='margin:16px 0 0;font-size:11px;color:#8a9aa8;border-top:1px dashed #d8e0e8;padding-top:10px'>"
             f"{labels['footer']}</p></div></body></html>")
    text = "\n".join([
        labels["title"],
        f"{labels['number']}: {invoice.get('number')}  {labels['date']}: {invoice.get('issued_at')}",
        f"{labels['from']}: {seller.get('name')} ({seller.get('vat_number')})",
        f"{labels['to']}: {buyer.get('name')}",
        "",
        *plain,
        "",
        f"{labels['subtotal']}: {_money(invoice.get('subtotal'))} {currency}",
        f"{labels['vat']}: {_money(invoice.get('tax'))} {currency}",
        f"{labels['grand']}: {_money(invoice.get('total'))} {currency}",
        "",
        labels["footer"],
    ])
    return head, text


def _smtp2go_post(body: dict) -> tuple[int, dict]:
    req = urllib.request.Request(
        SMTP2GO_ENDPOINT,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json",
                 "User-Agent": "ArabTemplates-GulfTax/1.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read().decode("utf-8") or "{}")
        except (ValueError, OSError):
            return exc.code, {}


@app.get("/api/email/config")
def email_config():
    cfg = smtp2go_config()
    cfg["ok"] = True
    cfg["lang"] = request_lang()
    return jsonify(cfg)


@app.post("/api/email/send")
def email_send():
    payload = request.get_json(silent=True) or {}
    lang = request_lang(payload)
    cfg = smtp2go_config()
    invoice = payload.get("invoice") or {}
    to = str(payload.get("to") or "").strip()
    if payload.get("test"):
        if not EMAIL_RE.match(to):
            return jsonify({"ok": False, "error": es(lang, "bad_to")}), 400
    elif not invoice:
        return jsonify({"ok": False, "error": es(lang, "no_invoice")}), 400
    elif not EMAIL_RE.match(to):
        return jsonify({"ok": False, "error": es(lang, "bad_to")}), 400
    if not cfg["configured"]:
        return jsonify({"ok": False, "needs_key": True, "env_var": cfg["env_var"],
                        "affiliate_link": cfg["affiliate_link"],
                        "error": es(lang, "missing_key")}), 400
    sender = str(payload.get("sender") or cfg["sender_default"] or "").strip()
    if not EMAIL_RE.match(sender):
        return jsonify({"ok": False, "error": es(lang, "bad_sender")}), 400
    sender_name = str(payload.get("sender_name") or cfg["sender_name_default"]).strip()[:80]
    labels = EMAIL_LABELS["en" if lang == "en" else "ar"]
    if payload.get("test"):
        subject = labels["test_subject"]
        html_body = ("<html><body style='font-family:Tahoma,Arial,sans-serif;color:#12263a;padding:20px'>"
                     f"<h2 style='margin:0 0 8px'>{labels['test_subject']}</h2>"
                     f"<p style='margin:0;color:#5b6b7c'>{labels['test_body']}</p></body></html>")
        text_body = f"{labels['test_subject']}\n\n{labels['test_body']}"
        number = "TEST"
    else:
        number = str(invoice.get("number") or "")
        seller_name = (invoice.get("seller") or {}).get("name") or sender_name
        subject = labels["invoice_subject"].format(number=number, seller=seller_name)[:180]
        html_body, text_body = invoice_email_html(invoice, lang)
    body = {
        "api_key": (os.environ.get("SMTP2GO_API_KEY") or "").strip(),
        "to": [to],
        "sender": f"{sender_name} <{sender}>" if sender_name else sender,
        "subject": subject,
        "html_body": html_body,
        "text_body": text_body,
    }
    reply_to = str(payload.get("reply_to") or "").strip()
    if EMAIL_RE.match(reply_to):
        body["custom_headers"] = [{"header": "Reply-To", "value": reply_to}]
    try:
        status, data = _smtp2go_post(body)
    except Exception as exc:  # pragma: no cover - شبكة
        return jsonify({"ok": False, "error": es(lang, "network", detail=type(exc).__name__)}), 502
    info = data.get("data") if isinstance(data, dict) else None
    succeeded = int((info or {}).get("succeeded") or 0)
    if status >= 400 or succeeded < 1:
        detail = ""
        if isinstance(info, dict):
            failures = info.get("failures") or info.get("error") or info.get("error_code") or ""
            detail = json.dumps(failures, ensure_ascii=False)[:240] if not isinstance(failures, str) else failures[:240]
        if not detail:
            detail = f"HTTP {status}"
        return jsonify({"ok": False, "error": es(lang, "provider_error", detail=detail)}), 502
    key = "test_sent" if payload.get("test") else "sent"
    return jsonify({"ok": True, "provider": "smtp2go", "to": to, "sent": succeeded,
                    "number": number, "lang": lang, "message": es(lang, key, number=number, to=to)})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gulf Tax Compliance Pro — خادم الواجهة.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5075)
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args(argv)

    url = f"http://{args.host}:{args.port}/"
    print(f"Gulf Tax Compliance Pro — {url}")
    print("   المسح يعمل عبر scripts/whatsapp_invoice_parser.py | الإيقاف: Ctrl+C")
    if args.open:
        threading.Timer(0.9, lambda: webbrowser.open(url)).start()
    app.run(host=args.host, port=args.port, debug=False, use_reloader=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
