#!/usr/bin/env python3
"""خادم معاينة متجر Arab Templates.

يقدّم الصفحات الثابتة من store/ ويُمرّر:
  GET  /api/templates        الكتالوج الموحّد (بابل + حزم الأوامر + بيانات وصفية)
  GET  /api/template?id=     منتج واحد بتفاصيله
  GET  /api/plans            باقات وسعات مسح الفواتير
  GET  /api/news             أخبار السوق المحفوظة
  GET  /api/quota            استهلاك سعة المسح لحساب
  GET  /api/health
  POST /api/scan             مسح دفعة فواتير من نص واتساب
  POST /api/assistant        مساعد ذكي محلي فوق سياق الفواتير

التوكن يبقى في الخادم ولا يصل إلى المتصفح.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import threading
import time
import webbrowser
from collections import Counter
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
STORE_DIR = ROOT / "store"
DATA_FILE = ROOT / "data" / "templates_ar.json"
META_FILE = ROOT / "data" / "store_meta.json"
PACKS_FILE = ROOT / "products" / "prompt_packs" / "catalog.json"
NEWS_FILE = ROOT / "data" / "market_news.json"
USAGE_FILE = ROOT / "reports" / "usage" / "usage.json"
CACHE_SECONDS = 60
MAX_BODY = 2 * 1024 * 1024

TOOL_KEYS = ("bubble", "make", "zapier", "notion", "prompts")
TOOL_LABELS = {
    "bubble": "Bubble",
    "make": "Make",
    "zapier": "Zapier",
    "notion": "Notion",
    "prompts": "برومبتات AI",
}
TOOL_BY_LABEL = {
    "bubble": "bubble",
    "make": "make",
    "zapier": "zapier",
    "notion": "notion",
    "برومبتات ai": "prompts",
    "برومبتات الذكاء الاصطناعي": "prompts",
    "prompts": "prompts",
}

DEFAULT_PLANS = [
    {"key": "starter", "name": "الأساسية", "price": 899, "scans": 300, "batch": 50,
     "for": "منشأة صغيرة أو مكتب محاسبة بفواتير محدودة"},
    {"key": "growth", "name": "النمو", "price": 1490, "scans": 3000, "batch": 250,
     "for": "شركة متوسطة تستلم مئات الفواتير شهريًا"},
    {"key": "scale", "name": "المؤسسات", "price": 2990, "scans": 20000, "batch": 1000,
     "for": "شركات وفروع كثيرة تحتاج مسحًا بالجملة"},
]
GRACE_RATIO = 0.1  # سماحية تجاوز لا توقف العمل

sys.path.insert(0, str(HERE))
from bubble_data_sync import (  # noqa: E402
    TEMPLATE_TYPE,
    BubbleClient,
    BubbleError,
    load_records,
)
from whatsapp_invoice_parser import invoice_payload, parse_invoice, split_invoices  # noqa: E402

_cache: dict[str, object] = {"at": 0.0, "payload": None}
_cache_lock = threading.Lock()
_usage_lock = threading.Lock()


def _text(value: object) -> str:
    return "" if value is None else str(value).strip()


def _norm(value: object) -> str:
    return re.sub(r"\s+", " ", _text(value)).strip()


def _pick(row: dict, *names: str):
    lowered = {str(key).lower(): value for key, value in row.items()}
    for name in names:
        if name in row:
            return row[name]
        found = lowered.get(name.lower())
        if found is not None:
            return found
    return None


def _price(value: object) -> float | None:
    try:
        number = float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def load_meta() -> dict[str, dict]:
    try:
        raw = json.loads(META_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {}
    block = raw.get("items", raw) if isinstance(raw, dict) else {}
    return {_norm(key): value for key, value in block.items() if isinstance(value, dict)}


def _tool_key(label: object, default: str) -> str:
    key = TOOL_BY_LABEL.get(_norm(label).lower())
    return key if key else default


def _item(row: dict, meta: dict[str, dict], default_tool: str, source: str, fallback_id: str = "") -> dict:
    title = _norm(_pick(row, "Title", "title")) or "بدون عنوان"
    description = _norm(_pick(row, "description", "Description", "desc"))
    category = _norm(_pick(row, "Category", "category")) or "غير مصنّف"
    detail = meta.get(title, {})
    tool = _tool_key(detail.get("tool"), default_tool)
    item_id = _norm(_pick(row, "_id", "id")) or fallback_id
    if not item_id:
        item_id = "t-" + hashlib.sha1(title.encode("utf-8")).hexdigest()[:12]
    return {
        "id": item_id,
        "title": title,
        "category": category,
        "sector": _norm(detail.get("sector")) or category,
        "tool": tool,
        "tool_label": TOOL_LABELS.get(tool, tool),
        "description": description,
        "problem": _norm(detail.get("problem")) or description,
        "roi": _norm(detail.get("roi")),
        "how": [str(step) for step in (detail.get("how") or [])],
        "requirements": [str(req) for req in (detail.get("requirements") or [])],
        "features": detail.get("features") or [],
        "plans": detail.get("plans") or [],
        "flagship": bool(detail.get("flagship")),
        "badge": _norm(detail.get("badge")),
        "demo_url": _norm(detail.get("demo_url")) or _norm(_pick(row, "preview_url", "Preview_URL")),
        "order_url": _norm(detail.get("order_url")),
        "price": _price(_pick(row, "price", "Price")),
        "preview_url": _norm(_pick(row, "preview_url", "Preview_URL")),
        "source": source,
    }


def _sort_key(item: dict) -> tuple[int, str, float]:
    return (0 if item["flagship"] else 1, item["sector"], -(item["price"] or 0.0))


def _payload(source: str, items: list[dict]) -> dict:
    ordered = sorted(items, key=_sort_key)
    tool_counts = Counter(item["tool"] for item in ordered)
    sector_counts = Counter(item["sector"] for item in ordered)
    return {
        "source": source,
        "count": len(ordered),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "tools": [
            {"key": key, "label": TOOL_LABELS[key], "count": tool_counts.get(key, 0)}
            for key in TOOL_KEYS
        ],
        "sectors": [
            {"label": label, "count": count} for label, count in sector_counts.most_common()
        ],
        "items": ordered,
    }


def fetch_live() -> list[dict]:
    client = BubbleClient(verbose=False)
    return client.list_things(TEMPLATE_TYPE, limit=100)


def fetch_packs() -> list[dict]:
    try:
        rows = json.loads(PACKS_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return []
    return rows if isinstance(rows, list) else []


def build_payload(offline: bool = False) -> dict:
    with _cache_lock:
        cached = _cache["payload"]
        if isinstance(cached, dict) and time.time() - float(_cache["at"]) < CACHE_SECONDS:
            return cached

    meta = load_meta()
    source = "bubble"
    template_rows: list[dict] = []
    if not offline:
        try:
            template_rows = fetch_live()
        except (BubbleError, OSError) as exc:
            print(f"[تحذير] تعذّر قراءة بابل: {str(exc).splitlines()[0]} — سيُستخدم الملف المحلي.")
        except Exception as exc:
            print(f"[تحذير] خطأ غير متوقع من بابل: {type(exc).__name__}: {exc}")
    if not template_rows:
        source = "local"
        template_rows = load_records(DATA_FILE, TEMPLATE_TYPE)

    items = [_item(row, meta, "bubble", source) for row in template_rows]
    packs = fetch_packs()
    items += [_item(row, meta, "prompts", "packs", f"pack-{i}") for i, row in enumerate(packs, 1)]

    payload = _payload(source, items)
    if source == "local":
        payload["note"] = "تعذّر الوصول إلى بابل؛ تُعرض نسخة من الملف المحلي."
    with _cache_lock:
        _cache["at"] = time.time()
        _cache["payload"] = payload
    return payload


def find_item(item_id: str) -> dict | None:
    wanted = _norm(item_id)
    for item in build_payload()["items"]:
        if item["id"] == wanted:
            return item
    return None


def plans_catalog() -> dict:
    """باقات المسح المعلنة في صفحة المنتج الرئيسي (أو الافتراضية)."""
    for item in build_payload()["items"]:
        if item["plans"]:
            return {"product": item["title"], "plans": item["plans"], "grace_ratio": GRACE_RATIO}
    return {"product": "", "plans": DEFAULT_PLANS, "grace_ratio": GRACE_RATIO}


def _plan(key: str) -> dict:
    for plan in plans_catalog()["plans"]:
        if _norm(plan.get("key")) == _norm(key):
            return plan
    return plans_catalog()["plans"][0]


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
    capacity = int(plan.get("scans") or 0)
    period = datetime.now().strftime("%Y-%m")
    with _usage_lock:
        data = _usage_all()
        record = data.get(account, {})
        used = int(record.get("used", 0)) if record.get("period") == period else 0
    grace = int(capacity * GRACE_RATIO)
    return {
        "account": account,
        "plan": plan.get("key"),
        "plan_name": plan.get("name"),
        "period": period,
        "capacity": capacity,
        "used": used,
        "remaining": max(capacity - used, 0),
        "grace": grace,
        "available": max(capacity + grace - used, 0),
    }


def consume_quota(account: str, plan_key: str, count: int) -> dict:
    plan = _plan(plan_key)
    capacity = int(plan.get("scans") or 0)
    period = datetime.now().strftime("%Y-%m")
    grace = int(capacity * GRACE_RATIO)
    with _usage_lock:
        data = _usage_all()
        record = data.get(account, {})
        used = int(record.get("used", 0)) if record.get("period") == period else 0
        available = max(capacity + grace - used, 0)
        accepted = min(count, available)
        deferred = count - accepted
        data[account] = {"period": period, "used": used + accepted, "plan": plan.get("key")}
        _usage_save(data)
    state = quota_state(account, plan_key)
    state["accepted"] = accepted
    state["deferred"] = deferred
    return state


def scan_invoices(text: str, account: str, plan_key: str) -> dict:
    chunks = split_invoices(text) or [text]
    results: list[dict] = []
    started = time.perf_counter()
    for chunk in chunks:
        if not chunk.strip():
            continue
        invoice = parse_invoice(chunk)
        results.append(invoice_payload(invoice))
    elapsed = (time.perf_counter() - started) * 1000
    quota = consume_quota(account, plan_key, len(results))
    totals = {
        "count": len(results),
        "total": round(sum(float(r.get("total") or 0) for r in results), 2),
        "tax": round(sum(float(r.get("tax") or 0) for r in results), 2),
        "needs_review": sum(1 for r in results if float(r.get("confidence") or 0) < 0.8),
    }
    return {
        "ok": True,
        "engine": "محلّل محلي (regex + قواعد خليجية)",
        "elapsed_ms": round(elapsed, 1),
        "quota": quota,
        "totals": totals,
        "invoices": results,
    }


FAQ: list[tuple[tuple[str, ...], str]] = [
    (("ضريبة", "vat", "قيمة مضافة"),
     "القوالب تحسب ضريبة القيمة المضافة تلقائيًا من البنود، وتجمع الإقرار ربع سنويًا بتفصيل المدخلات والمخرجات. المعتمد في السعودية ١٥٪، والإمارات ٥٪، والكويت بلا ضريبة قيمة مضافة حاليًا لكن القالب يدعم تعطيلها."),
    (("مسح", "واتساب", "فواتير", "scan"),
     "أرسل الفواتير كنص إلى رقم واتساب المتجر أو الصقها في مربع المسح: يقرأ المحلّل المورّد والتاريخ والإجمالي والضريبة والنسبة، ويوسم الفواتير التي تحتاج مراجعة بشرية. يمكن مسح دفعة واحدة بالجملة بلا حد لكل دقيقة."),
    (("باقة", "باقات", "سعر", "تكلفة", "capacity"),
     "الباقات تُحدد بسعة شهرية لا بقيود زمنية: ٣٠٠ فاتورة للأساسية، ٣٠٠٠ للنمو، و٢٠٠٠٠ للمؤسسات، مع سماحية تجاوز ١٠٪ تُستهلك تلقائيًا بدل رفض العمل."),
    (("أخبار", "سوق", "news"),
     "لوحة أخبار السوق داخل القالب تعرض تحديثات الامتثال والضريبة في الخليج، وتُحدَّث من ملف أخبار السوق المحلي أو تغذية RSS عند ضبطها في متغيّر البيئة NEWS_FEED_URL."),
    (("امتثال", "سعودي", "إماراتي", "كويتي", "compliance"),
     "القالب يوحّد الحقول المطلوبة في الدول الثلاث: الرقم الضريبي، تاريخ الفاتورة، الإجمالي، الضريبة، والعملة، ثم يولّد تقرير امتثال لكل دولة على حدة."),
    (("تركيب", "تشغيل", "متطلبات", "requirements"),
     "المتطلبات: حساب Bubble بخطة Starter أو أعلى، رقم واتساب أعمال (WhatsApp Cloud API أو مزود وسيط)، ومفتاح نموذج لغوي للمساعد الذكي. التركيب لا يحتاج كودًا على خادمك."),
]


def assistant_answer(question: str, invoice: dict | None) -> dict:
    text = _norm(question).lower()
    for keys, answer in FAQ:
        if any(key.lower() in text for key in keys):
            reply = answer
            break
    else:
        reply = (
            "أقدر أساعدك في مسح الفواتير، حساب الضريبة، توليد تقرير الامتثال، وشرح الباقات. "
            "اسأل مثلًا: «كيف أمسح ٥٠٠ فاتورة دفعة واحدة؟» أو «ما سعة الباقة للمؤسسات؟»"
        )
    context = None
    if isinstance(invoice, dict) and invoice:
        context = {
            "supplier": invoice.get("supplier"),
            "total": invoice.get("total"),
            "tax": invoice.get("tax"),
            "vat_rate": invoice.get("vat_rate"),
            "needs_review": float(invoice.get("confidence") or 0) < 0.8,
        }
        if context["needs_review"]:
            reply += " لاحظت أن هذه الفاتورة ثقتها منخفضة؛ راجع الإجمالي وسطر الضريبة قبل الترحيل."
    return {
        "mode": "local",
        "answer": reply,
        "context": context,
        "suggestions": [
            "كيف أمسح دفعة فواتير من واتساب؟",
            "ما الفرق بين الباقات في سعة المسح؟",
            "كيف يُحسب تقرير الامتثال لكل دولة؟",
        ],
    }


def market_news() -> dict:
    try:
        rows = json.loads(NEWS_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        rows = []
    items = rows.get("items", []) if isinstance(rows, dict) else rows
    items = sorted(items, key=lambda row: str(row.get("date") or ""), reverse=True)
    return {"count": len(items), "items": items, "updated_at": _text((rows or {}).get("updated_at"))}


class StoreHandler(SimpleHTTPRequestHandler):
    server_version = "ArabTemplatesStore/1.2"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STORE_DIR), **kwargs)

    def _send_json(self, data: dict, status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY:
            raise ValueError("حجم الطلب غير مقبول")
        raw = self.rfile.read(length).decode("utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("الصيغة يجب أن تكون كائن JSON")
        return data

    def _route_get(self) -> bool:
        parts = urlsplit(self.path)
        path, query = parts.path, parse_qs(parts.query)
        if path == "/api/health":
            self._send_json({"ok": True, "offline": self.server.offline})
            return True
        if path in ("/api/templates", "/api/templates/source"):
            payload = build_payload(offline=self.server.offline)
            if path == "/api/templates":
                self._send_json(payload)
            else:
                self._send_json({"source": payload["source"], "count": payload["count"]})
            return True
        if path == "/api/template":
            item = find_item((query.get("id") or [""])[0])
            if item is None:
                self._send_json({"error": "not_found"}, 404)
            else:
                self._send_json({"item": item})
            return True
        if path == "/api/plans":
            self._send_json(plans_catalog())
            return True
        if path == "/api/news":
            self._send_json(market_news())
            return True
        if path == "/api/quota":
            account = _norm((query.get("account") or ["demo"])[0])[:64] or "demo"
            plan = _norm((query.get("plan") or ["growth"])[0])
            self._send_json(quota_state(account, plan))
            return True
        return False

    def _route_post(self) -> bool:
        path = urlsplit(self.path).path
        if path not in ("/api/scan", "/api/assistant"):
            return False
        try:
            data = self._read_json()
        except (ValueError, UnicodeDecodeError) as exc:
            self._send_json({"error": f"طلب غير صالح: {exc}"}, 400)
            return True
        account = _norm(data.get("account"))[:64] or "demo"
        plan = _norm(data.get("plan"))[:32] or "growth"
        if path == "/api/scan":
            text = _text(data.get("text"))
            if not text.strip():
                self._send_json({"error": "لا يوجد نص فواتير"}, 400)
                return True
            self._send_json(scan_invoices(text, account, plan))
            return True
        self._send_json(assistant_answer(_text(data.get("question")), data.get("invoice")))
        return True

    def do_GET(self) -> None:
        if self._route_get():
            return
        if urlsplit(self.path).path in ("/", "/index.html"):
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:
        if not self._route_post():
            self._send_json({"error": "not_found"}, 404)

    def do_HEAD(self) -> None:
        if self._route_get():
            return
        super().do_HEAD()

    def end_headers(self) -> None:
        self.send_header("Referrer-Policy", "no-referrer")
        super().end_headers()

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write(f"[{datetime.now():%H:%M:%S}] {self.address_string()} {fmt % args}\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="خادم معاينة متجر Arab Templates (التوكن يبقى في الخادم).")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--offline", action="store_true", help="اعرض الملف المحلي بلا اتصال ببابل")
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args(argv)

    if not STORE_DIR.is_dir():
        print(f"[خطأ] مجلد الصفحة غير موجود: {STORE_DIR}", file=sys.stderr)
        return 2
    try:
        server = ThreadingHTTPServer((args.host, args.port), StoreHandler)
    except OSError as exc:
        print(f"[خطأ] تعذّر فتح المنفذ {args.port}: {exc}", file=sys.stderr)
        return 1
    server.offline = args.offline  # type: ignore[attr-defined]

    url = f"http://{args.host}:{args.port}/"
    print(f"متجر Arab Templates — {url}")
    print(f"   البيانات: {'الملف المحلي (offline)' if args.offline else 'بابل + حزم الأوامر (كاش 60 ثانية)'}")
    print("   التوكن يبقى في الخادم. الإيقاف: Ctrl+C")
    if args.open:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[⛔] أُوقف الخادم.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
