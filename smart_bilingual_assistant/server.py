"""خادم أداة المساعد الذكي: يقدّم الملفات ويسجّل الأسئلة غير المجابة.

GET  /                الملفات الثابتة من مجلد الأداة
GET  /api/health      فحص سريع
GET  /api/unanswered  ملخّص الفجوات: العدد، الأكثر تكرارًا، وآخر الأسئلة (?limit=50)
POST /api/unanswered  {"question": "...", "lang": "ar"} يسجّل سؤالًا بلا جواب
      /api/unanswered/clear  يفرّغ السجل بعد تحديث قاعدة المعرفة

التشغيل:
    python smart_bilingual_assistant/server.py --port 5083
السجل: smart_bilingual_assistant/logs/unanswered.jsonl (مستثنى من git).
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import webbrowser
from collections import Counter
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "unanswered.jsonl"
MAX_QUESTION = 500
MAX_BODY = 4096
WRITE_LOCK = threading.Lock()


def _clean_question(value: object) -> str:
    text = " ".join(str(value or "").split())
    return text[:MAX_QUESTION]


def read_entries() -> list[dict]:
    if not LOG_FILE.exists():
        return []
    rows: list[dict] = []
    for line in LOG_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def append_entry(question: str, lang: str) -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "at": datetime.now().isoformat(timespec="seconds"),
        "question": question,
        "lang": lang,
    }
    with WRITE_LOCK:
        with LOG_FILE.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return sum(1 for _ in LOG_FILE.open(encoding="utf-8"))


def clear_entries() -> int:
    with WRITE_LOCK:
        removed = 0
        if LOG_FILE.exists():
            removed = sum(1 for _ in LOG_FILE.open(encoding="utf-8"))
            LOG_FILE.write_text("", encoding="utf-8")
        return removed


def summary(limit: int = 50) -> dict:
    rows = read_entries()
    counts = Counter(_clean_question(row.get("question")) for row in rows)
    counts.pop("", None)
    return {
        "ok": True,
        "total": len(rows),
        "unique": len(counts),
        "top": [{"question": q, "count": c} for q, c in counts.most_common(20)],
        "recent": list(reversed(rows))[:limit],
        "log_file": str(LOG_FILE),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }


class AssistantHandler(SimpleHTTPRequestHandler):
    server_version = "AssistantServer/1.0"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    # ---- أدوات الاستجابة ----
    def _json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY:
            raise ValueError("حجم الطلب غير مقبول")
        data = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("الصيغة يجب أن تكون كائن JSON")
        return data

    # ---- المسارات ----
    def _route_get(self) -> bool:
        parts = urlsplit(self.path)
        query = parse_qs(parts.query)
        if parts.path == "/api/health":
            self._json({"ok": True, "service": "smart_bilingual_assistant"})
            return True
        if parts.path == "/api/unanswered":
            try:
                limit = int((query.get("limit") or ["50"])[0])
            except ValueError:
                limit = 50
            self._json(summary(max(1, min(limit, 500))))
            return True
        return False

    def _route_post(self) -> bool:
        path = urlsplit(self.path).path
        if path == "/api/unanswered/clear":
            removed = clear_entries()
            self._json({"ok": True, "removed": removed})
            return True
        if path != "/api/unanswered":
            return False
        try:
            data = self._read_json()
        except (ValueError, UnicodeDecodeError) as exc:
            self._json({"ok": False, "error": f"طلب غير صالح: {exc}"}, 400)
            return True
        question = _clean_question(data.get("question"))
        if not question:
            self._json({"ok": False, "error": "لا يوجد نص سؤال"}, 400)
            return True
        lang = "en" if str(data.get("lang") or "").lower() == "en" else "ar"
        total = append_entry(question, lang)
        self._json({"ok": True, "total": total})
        return True

    def do_GET(self) -> None:  # noqa: N802 - اسم إلزامي في http.server
        if self._route_get():
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        if not self._route_post():
            self._json({"ok": False, "error": "not_found"}, 404)

    def end_headers(self) -> None:
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write(f"[{datetime.now():%H:%M:%S}] {self.address_string()} {fmt % args}\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="خادم أداة المساعد الذكي مع تسجيل الأسئلة غير المجابة.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5083)
    parser.add_argument("--open", action="store_true", help="افتح المتصفح بعد التشغيل")
    args = parser.parse_args(argv)

    try:
        server = ThreadingHTTPServer((args.host, args.port), AssistantHandler)
    except OSError as exc:
        print(f"[خطأ] تعذّر فتح المنفذ {args.port}: {exc}", file=sys.stderr)
        return 1

    url = f"http://{args.host}:{args.port}/"
    print(f"خادم المساعد يعمل على {url}")
    print(f"سجل الأسئلة غير المجابة: {LOG_FILE}")
    print(f"ملخّص الفجوات: {url}api/unanswered")
    if args.open:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nإيقاف الخادم.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
