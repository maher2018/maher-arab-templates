#!/usr/bin/env python3
"""خادم منتج Gulf Tax Compliance Pro.

يقدّم واجهة gulf_tax_template_pro ويعمل كمحرك خلفي لها:
  GET  /               الصفحة
  GET  /styles.css     التنسيق
  GET  /app.js         منطق الواجهة
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
import json
import sys
import threading
import time
import urllib.request
import webbrowser
from datetime import datetime
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
    {"key": "starter", "name": "الأساسية", "price": 899, "scans": 300, "batch": 100,
     "for": "مكتب محاسبة أو منشأة صغيرة بفواتير محدودة",
     "features": ["مسح نص واتساب", "تصدير CSV", "مساعد ضريبي"]},
    {"key": "growth", "name": "النمو", "price": 1490, "scans": 3000, "batch": 500,
     "for": "شركة متوسطة تستلم مئات الفواتير شهريًا",
     "features": ["مسح بالجملة ٥٠٠ فاتورة", "تصدير CSV وJSON", "أخبار وعملات", "أولوية دعم"]},
    {"key": "scale", "name": "المؤسسات", "price": 2990, "scans": 20000, "batch": 2000,
     "for": "مجموعة شركات وفروع متعددة",
     "features": ["مسح بالجملة ٢٠٠٠ فاتورة", "سعة شهرية ٢٠٠٠٠", "سماحية تجاوز ١٠٪", "تقارير متعددة الدول"]},
]
GRACE_RATIO = 0.10
MAX_INVOICES = 5000
USAGE_FILE = ROOT / "reports" / "usage" / "gulf_usage.json"

_usage_lock = threading.Lock()


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


def market_news() -> dict:
    try:
        raw = json.loads((DATA / "market_news.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {"items": [], "updated_at": "—"}
    items = raw.get("items", []) if isinstance(raw, dict) else raw
    items = sorted(items, key=lambda row: str(row.get("date") or ""), reverse=True)
    return {"items": items, "updated_at": (raw or {}).get("updated_at", "—")}


@app.get("/")
def index():
    return send_from_directory(BASE, "index.html")


@app.get("/styles.css")
def styles():
    return send_from_directory(BASE, "styles.css")


@app.get("/app.js")
def app_js():
    return send_from_directory(BASE, "app.js")


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
    return jsonify(market_news())


@app.get("/api/plans")
def plans():
    return jsonify({"plans": PLANS, "grace_ratio": GRACE_RATIO, "max_invoices": MAX_INVOICES})


@app.get("/api/quota")
def quota():
    account = (request.args.get("account") or "demo").strip()[:64] or "demo"
    plan_key = (request.args.get("plan") or "growth").strip()
    return jsonify(quota_state(account, plan_key))


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
    meta = einvoice.country_meta(einvoice.DEFAULT_COUNTRY)
    return jsonify({
        "countries": einvoice.countries_public(),
        "default": meta,
        "periods": einvoice.periods(meta["code"]),
        "max_items": einvoice.MAX_ITEMS,
    })


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


@app.get("/api/taxreturn")
def taxreturn():
    account = (request.args.get("account") or "demo").strip()[:64] or "demo"
    country = request.args.get("country") or einvoice.DEFAULT_COUNTRY
    period = request.args.get("period") or datetime.now().strftime("%Y-%m")
    try:
        return jsonify(ledger.summary(account, country, period))
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.post("/api/ocr")
def ocr_scan():
    upload = request.files.get("image") or (next(iter(request.files.values())) if request.files else None)
    if not upload:
        return jsonify({"ok": False, "error": "أرفق صورة فاتورة"}), 400
    raw = upload.read()
    account = (request.form.get("account") or "demo").strip()[:64] or "demo"
    try:
        result = ocr.extract(raw, upload.filename or "image.png")
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    except Exception as exc:  # pragma: no cover - حماية من فشل OCR غير المتوقع
        return jsonify({"ok": False, "error": f"تعذّر تحليل الصورة: {type(exc).__name__}"}), 500
    if str(request.form.get("save") or "").lower() in ("1", "true", "yes"):
        result["saved"] = ledger.add_purchases(account, [result["invoice"]], "ocr")
    return jsonify(result)


ACCOUNTANT_REPLY = (
    "وصلت رسالتك إلى المحاسب وسيُرد عليك خلال يوم عمل. "
    "في هذه النسخة المحلية يُحفظ الطلب في سجل الحساب ويظهر رقم التذكرة أدناه، "
    "ويمكنك متابعة الأسئلة الفورية مع المساعد الضريبي في الأعلى."
)


@app.post("/api/support")
def support_post():
    payload = request.get_json(silent=True) or {}
    account = str(payload.get("account") or "demo").strip()[:64] or "demo"
    message = str(payload.get("message") or "").strip()
    if not message:
        return jsonify({"ok": False, "error": "اكتب نص الرسالة"}), 400
    if len(message) > 2000:
        return jsonify({"ok": False, "error": "الرسالة أطول من ٢٠٠٠ حرف"}), 400
    entry = ledger.add_message(account, str(payload.get("topic") or "استشارة ضريبية"), message)
    return jsonify({"ok": True, "ticket": entry["ticket"], "entry": entry,
                    "reply": ACCOUNTANT_REPLY})


@app.get("/api/support")
def support_get():
    account = (request.args.get("account") or "demo").strip()[:64] or "demo"
    return jsonify({"ok": True, "messages": ledger.list_messages(account)[:50]})


@app.post("/api/assistant")
def assistant():
    payload = request.get_json(silent=True) or {}
    question = str(payload.get("question") or "")
    if len(question) > 1000:
        return jsonify({"ok": False, "error": "السؤال طويل جدًا"}), 400
    return jsonify(assistant_answer(question, payload.get("invoice")))


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
