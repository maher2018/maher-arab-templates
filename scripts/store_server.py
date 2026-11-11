#!/usr/bin/env python3
"""خادم معاينة متجر Arab Templates.

يقدّم صفحة store/index.html ويُمرّر بيانات جدول template عبر /api/templates،
فيتصل بـ Bubble من الخادم فقط ويبقى التوكن خارج المتصفح تمامًا.
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import time
import webbrowser
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
STORE_DIR = ROOT / "store"
DATA_FILE = ROOT / "data" / "templates_ar.json"
CACHE_SECONDS = 60

sys.path.insert(0, str(HERE))
from bubble_data_sync import (  # noqa: E402
    TEMPLATE_TYPE,
    BubbleClient,
    BubbleError,
    load_records,
)

_cache: dict[str, object] = {"at": 0.0, "payload": None}
_cache_lock = threading.Lock()


def _text(value: object) -> str:
    return "" if value is None else str(value).strip()


def public_item(row: dict) -> dict:
    """الحقول المسموح ظهورها في المتصفح — لا شيء غيرها يخرج من الخادم."""
    raw_price = row.get("price")
    try:
        price = float(str(raw_price).replace(",", "").strip())
    except (TypeError, ValueError):
        price = None
    return {
        "id": _text(row.get("_id")),
        "title": _text(row.get("Title")) or "بدون عنوان",
        "category": _text(row.get("Category")) or "غير مصنّف",
        "description": _text(row.get("description")),
        "price": price,
        "preview_url": _text(row.get("preview_url")),
    }


def _sort_key(item: dict) -> tuple[str, float]:
    return (item["category"], -(item["price"] or 0.0))


def _payload(source: str, items: list[dict]) -> dict:
    return {
        "source": source,
        "count": len(items),
        "categories": sorted({item["category"] for item in items}),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "items": items,
    }


def fetch_live() -> dict:
    client = BubbleClient(verbose=False)
    rows = client.list_things(TEMPLATE_TYPE, limit=100)
    items = sorted((public_item(row) for row in rows), key=_sort_key)
    return _payload("bubble", items)


def fetch_local() -> dict:
    rows = load_records(DATA_FILE, TEMPLATE_TYPE)
    items = sorted((public_item(row) for row in rows), key=_sort_key)
    payload = _payload("local", items)
    payload["note"] = "تعذّر الوصول إلى بابل؛ تُعرض نسخة من الملف المحلي."
    return payload


def build_payload(offline: bool = False) -> dict:
    with _cache_lock:
        cached = _cache["payload"]
        if isinstance(cached, dict) and time.time() - float(_cache["at"]) < CACHE_SECONDS:
            return cached
    payload: dict | None = None
    if not offline:
        try:
            payload = fetch_live()
        except (BubbleError, OSError) as exc:
            print(f"[تحذير] تعذّر قراءة بابل: {str(exc).splitlines()[0]} — سيُستخدم الملف المحلي.")
        except Exception as exc:  # لا نُسقط الخادم بسبب خطأ شبكة غير متوقع
            print(f"[تحذير] خطأ غير متوقع من بابل: {type(exc).__name__}: {exc}")
    if payload is None:
        payload = fetch_local()
    with _cache_lock:
        _cache["at"] = time.time()
        _cache["payload"] = payload
    return payload


class StoreHandler(SimpleHTTPRequestHandler):
    server_version = "ArabTemplatesStore/1.0"

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

    def _route(self) -> bool:
        path = urlsplit(self.path).path
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
        return False

    def do_GET(self) -> None:
        if self._route():
            return
        if urlsplit(self.path).path in ("/", "/index.html"):
            self.path = "/index.html"
        super().do_GET()

    def do_HEAD(self) -> None:
        if self._route():
            return
        super().do_HEAD()

    def end_headers(self) -> None:
        self.send_header("Referrer-Policy", "no-referrer")
        super().end_headers()

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write(f"[{datetime.now():%H:%M:%S}] {self.address_string()} {fmt % args}\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="خادم معاينة متجر Arab Templates (يُبقي توكن بابل في الخادم)."
    )
    parser.add_argument("--host", default="127.0.0.1", help="افتراضيًا 127.0.0.1 (محلي فقط)")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--offline", action="store_true", help="اعرض الملف المحلي بلا اتصال ببابل")
    parser.add_argument("--open", action="store_true", help="افتح المتصفح بعد التشغيل")
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
    print(f"   البيانات: {'الملف المحلي (offline)' if args.offline else 'بابل (نسخة مخزّنة 60 ثانية)'}")
    print("   التوكن يبقى في الخادم؛ المتصفح يرى /api/templates فقط.")
    print("   الإيقاف: Ctrl+C")
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
