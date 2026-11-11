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
from whatsapp_invoice_parser import parse_invoice, split_invoices  # noqa: E402

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

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


def scan_text(text: str) -> dict:
    chunks = split_invoices(text) or [text]
    started = time.perf_counter()
    rows = [invoice_dict(parse_invoice(chunk)) for chunk in chunks if chunk.strip()]
    elapsed = round((time.perf_counter() - started) * 1000, 1)
    return {
        "ok": True,
        "engine": "whatsapp_invoice_parser.py",
        "elapsed_ms": elapsed,
        "totals": {
            "count": len(rows),
            "total": round(sum(float(r["total"] or 0) for r in rows), 2),
            "tax": round(sum(float(r["tax"] or 0) for r in rows), 2),
            "needs_review": sum(1 for r in rows if float(r["confidence"] or 0) < 0.8),
        },
        "invoices": rows,
    }


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


@app.get("/api/rates")
def rates():
    return jsonify(fetch_rates())


@app.post("/api/scan")
def scan():
    text = ""
    if request.files:
        upload = next(iter(request.files.values()))
        raw = upload.read()
        for encoding in ("utf-8", "utf-8-sig", "cp1256"):
            try:
                text = raw.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        if not text:
            return jsonify({"ok": False, "error": "تعذّر قراءة الملف — استخدم ترميز UTF-8"}), 400
    else:
        payload = request.get_json(silent=True) or {}
        text = str(payload.get("text") or "")
    if not text.strip():
        return jsonify({"ok": False, "error": "لا يوجد نص فواتير"}), 400
    return jsonify(scan_text(text[:400_000]))


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
