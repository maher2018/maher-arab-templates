#!/usr/bin/env python3
"""لوحة تحكم Arab Templates المحلية (Flask، عربية RTL).

تعرض حالة اتصال السرب بتطبيق Bubble، وعدد القوالب والمهام المرفوعة،
وتوفّر زرًا واحدًا لتشغيل المزامنة، وآخر لتوليد فاتورة ضريبية جديدة.

    python admin_dashboard.py            # http://127.0.0.1:5050
    python admin_dashboard.py --port 5060 --open
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE / "scripts"
REPORTS = HERE / "reports" / "invoice_reports"
HISTORY = HERE / "logs" / "history.csv"
sys.path.insert(0, str(SCRIPTS))

from bubble_data_sync import (  # noqa: E402
    TEMPLATE_TYPE,
    BubbleClient,
    BubbleError,
    load_app_url,
)
from whatsapp_invoice_parser import (  # noqa: E402
    parse_invoice,
    report_markdown,
    send_invoice,
)

app = Flask(__name__)
_lock = threading.Lock()
_last_sync: dict[str, object] = {"at": None, "ok": None, "output": "", "counts": None}


def _tail(text: str, lines: int = 40) -> str:
    return "\n".join(text.strip().splitlines()[-lines:])


def bubble_status() -> dict:
    """يقرأ حالة الاتصال والعدادات من بابل مباشرة."""
    started = time.perf_counter()
    info: dict[str, object] = {
        "app": "at-ai-lab",
        "app_url": "",
        "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "connected": False,
        "error": None,
        "latency_ms": None,
        "counts": {"templates": None, "tasks": None, "invoices": None},
    }
    try:
        info["app_url"] = load_app_url()
        client = BubbleClient(verbose=False)
        templates = client.list_things(TEMPLATE_TYPE, limit=100)
        tasks = client.list_things("task", limit=100)
        info["counts"]["templates"] = len(templates)  # type: ignore[index]
        info["counts"]["tasks"] = len(tasks)  # type: ignore[index]
        try:
            invoices = client.list_things("invoice", limit=100)
            info["counts"]["invoices"] = len(invoices)  # type: ignore[index]
        except BubbleError:
            info["counts"]["invoices"] = "missing"  # type: ignore[index]
        info["connected"] = True
    except BubbleError as exc:
        info["error"] = str(exc).splitlines()[0][:200]
    except Exception as exc:  # شبكة أو إعداد ناقص
        info["error"] = f"{type(exc).__name__}: {exc}"[:200]
    info["latency_ms"] = round((time.perf_counter() - started) * 1000)
    return info


def last_sync_row() -> dict | None:
    try:
        with HISTORY.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except (FileNotFoundError, OSError):
        return None
    return rows[-1] if rows else None


COUNT_RE = re.compile(r"جديد (\d+) \| محدَّث (\d+) \| بلا تغيير (\d+) \| فشل (\d+)")


def run_sync() -> dict:
    """تشغيل scheduled_sync.py --once وإرجاع ملخص النتيجة."""
    if not _lock.acquire(blocking=False):
        return {"ok": False, "error": "مزامنة قيد التشغيل بالفعل", "output": ""}
    try:
        started = time.perf_counter()
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "scheduled_sync.py"), "--once"],
            cwd=str(HERE),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=240,
        )
        output = (proc.stdout or "") + (proc.stderr or "")
        match = COUNT_RE.search(output)
        counts = None
        if match:
            create, update, unchanged, failed = (int(value) for value in match.groups())
            counts = {
                "create": create,
                "update": update,
                "unchanged": unchanged,
                "failed": failed,
            }
        result = {
            "ok": proc.returncode == 0,
            "counts": counts,
            "seconds": round(time.perf_counter() - started, 1),
            "output": _tail(output),
            "at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        _last_sync.update(result)
        return result
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "انتهت مهلة المزامنة (240 ثانية)", "output": ""}
    finally:
        _lock.release()


def generate_invoice(supplier: str, amount: float, rate: float) -> dict:
    """ينشئ فاتورة ضريبية: يحللها، يحفظ تقريرها، ويحاول رفعها إلى بابل."""
    supplier = supplier.strip()[:120]
    if not supplier:
        raise ValueError("اسم المورد مطلوب")
    if amount <= 0:
        raise ValueError("المبلغ يجب أن يكون أكبر من صفر")
    if not 0 <= rate <= 100:
        raise ValueError("نسبة الضريبة يجب أن تكون بين 0 و100")

    subtotal = round(amount, 2)
    tax = round(subtotal * rate / 100, 2)
    total = round(subtotal + tax, 2)
    text = (
        f"المورد: {supplier}\n"
        f"التاريخ: {datetime.now():%Y-%m-%d}\n"
        f"الإجمالي قبل الضريبة: {subtotal:,.2f}\n"
        f"الضريبة ({rate:g}%): {tax:,.2f}\n"
        f"الإجمالي: {total:,.2f}\n"
    )
    invoice = parse_invoice(text)
    invoice.supplier = supplier
    invoice.subtotal = subtotal
    invoice.tax = tax
    invoice.total = total
    invoice.vat_rate = rate

    bubble_id: str | None = None
    error: str | None = None
    try:
        client = BubbleClient(verbose=False)
        bubble_id, _ = send_invoice(client, invoice, "invoice")
    except BubbleError as exc:
        error = str(exc).splitlines()[0][:200]
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"[:200]

    REPORTS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report = REPORTS / f"admin-invoice-{stamp}.md"
    report.write_text(report_markdown(invoice, bubble_id=bubble_id, error=error), encoding="utf-8")

    return {
        "ok": True,
        "bubble_id": bubble_id,
        "uploaded": bool(bubble_id),
        "warning": error,
        "report": str(report.relative_to(HERE)),
        "invoice": invoice.as_row(),
        "at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


@app.get("/")
def index() -> str:
    return PAGE


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "time": datetime.now().isoformat(timespec="seconds")})


@app.get("/api/status")
def api_status():
    return jsonify({"status": bubble_status(), "last_sync": last_sync_row(), "session": _last_sync})


@app.post("/api/sync")
def api_sync():
    return jsonify(run_sync())


@app.post("/api/invoice")
def api_invoice():
    data = request.get_json(silent=True) or {}
    try:
        supplier = str(data.get("supplier") or "")
        amount = float(data.get("amount") or 0)
        rate = float(data.get("rate") if data.get("rate") not in (None, "") else 15)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "قيم غير رقمية"}), 400
    try:
        return jsonify(generate_invoice(supplier, amount, rate))
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


PAGE = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>لوحة تحكم Arab Templates</title>
<style>
:root{--bg:#0d1a26;--panel:#132635;--panel2:#17303f;--ink:#eef4f8;--muted:#93a8b8;--line:#23404f;--ok:#3fbf8b;--warn:#e0b044;--bad:#e2685f;--accent:#4ea8de}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"Segoe UI",Tahoma,system-ui,sans-serif;line-height:1.7}
.wrap{max-width:1080px;margin:0 auto;padding:26px 20px 60px}
header{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;padding-bottom:18px;border-bottom:1px solid var(--line)}
h1{font-size:1.35rem;margin:0}
.sub{color:var(--muted);font-size:.85rem}
.pill{display:inline-flex;align-items:center;gap:8px;padding:7px 14px;border-radius:999px;background:var(--panel);border:1px solid var(--line);font-size:.85rem}
.dot{width:9px;height:9px;border-radius:50%;background:var(--muted)}
.dot.ok{background:var(--ok);box-shadow:0 0 0 4px rgba(63,191,139,.15)}
.dot.bad{background:var(--bad);box-shadow:0 0 0 4px rgba(226,104,95,.15)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin:22px 0}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px}
.stat .label{color:var(--muted);font-size:.82rem}
.stat .value{font-size:1.9rem;font-weight:800;margin-top:4px}
.stat .hint{color:var(--muted);font-size:.76rem;margin-top:2px}
.actions{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px;margin-bottom:22px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px}
.card h2{font-size:1rem;margin:0 0 10px}
.row{display:flex;gap:10px;flex-wrap:wrap}
.field{display:flex;flex-direction:column;gap:5px;flex:1 1 130px}
label{color:var(--muted);font-size:.8rem}
input{background:var(--panel2);border:1px solid var(--line);border-radius:9px;padding:9px 11px;color:var(--ink);font:inherit;font-size:.9rem;outline:none}
input:focus{border-color:var(--accent)}
button{background:var(--accent);color:#04121c;border:0;border-radius:9px;padding:10px 16px;font:inherit;font-weight:700;font-size:.88rem;cursor:pointer;transition:.15s}
button:hover{filter:brightness(1.08)}
button:disabled{opacity:.55;cursor:progress}
button.ghost{background:transparent;color:var(--ink);border:1px solid var(--line)}
pre{background:#0a1620;border:1px solid var(--line);border-radius:10px;padding:12px;font-size:.78rem;line-height:1.5;max-height:210px;overflow:auto;white-space:pre-wrap;margin:12px 0 0;color:#c8dbe6}
.note{font-size:.78rem;color:var(--muted);margin-top:8px}
.msg{margin-top:10px;font-size:.85rem}
.msg.ok{color:var(--ok)} .msg.bad{color:var(--bad)} .msg.warn{color:var(--warn)}
table{width:100%;border-collapse:collapse;margin-top:10px;font-size:.85rem}
th,td{text-align:right;padding:7px 8px;border-bottom:1px solid var(--line)}
th{color:var(--muted);font-weight:600}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div>
      <h1>لوحة تحكم Arab Templates</h1>
      <div class="sub">إدارة الاتصال بالسرب ومزامنة القوالب وتوليد الفواتير</div>
    </div>
    <div class="pill"><span class="dot" id="dot"></span><span id="conn">جارٍ الفحص…</span></div>
  </header>

  <div class="stats">
    <div class="stat"><div class="label">القوالب المرفوعة</div><div class="value" id="templates">—</div><div class="hint" id="app-url">—</div></div>
    <div class="stat"><div class="label">المهام المرفوعة</div><div class="value" id="tasks">—</div><div class="hint">جدول task</div></div>
    <div class="stat"><div class="label">جدول الفواتير</div><div class="value" id="invoices">—</div><div class="hint">جدول invoice</div></div>
    <div class="stat"><div class="label">زمن استجابة بابل</div><div class="value" id="latency">—</div><div class="hint" id="checked">—</div></div>
  </div>

  <div class="actions">
    <div class="card">
      <h2>المزامنة والسرب</h2>
      <p class="note">يشغّل <code>scheduled_sync.py --once</code> على مجموعة العشرين قالبًا ويكتب السجل.</p>
      <div class="row" style="margin-top:10px">
        <button id="syncBtn">تشغيل المزامنة الآن</button>
        <button class="ghost" id="refreshBtn">تحديث الحالة</button>
      </div>
      <div class="msg" id="syncMsg"></div>
      <pre id="syncLog">لا توجد مزامنة في هذه الجلسة بعد.</pre>
    </div>

    <div class="card">
      <h2>توليد فاتورة ضريبية</h2>
      <div class="row">
        <div class="field"><label>اسم المورد</label><input id="supplier" placeholder="شركة النخيل للتجارة"></div>
        <div class="field"><label>المبلغ قبل الضريبة</label><input id="amount" type="number" min="0" step="0.01" value="1000"></div>
        <div class="field"><label>نسبة الضريبة %</label><input id="rate" type="number" min="0" max="100" step="0.5" value="15"></div>
      </div>
      <div class="row" style="margin-top:12px"><button id="invBtn">توليد الفاتورة</button></div>
      <div class="msg" id="invMsg"></div>
      <div id="invResult"></div>
    </div>
  </div>

  <div class="card">
    <h2>آخر عملية مزامنة مسجّلة</h2>
    <div id="lastSync" class="note">—</div>
  </div>
</div>

<script>
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));

async function loadStatus() {
  try {
    const res = await fetch("/api/status", {cache: "no-store"});
    const data = await res.json();
    const s = data.status;
    $("dot").className = "dot " + (s.connected ? "ok" : "bad");
    $("conn").textContent = s.connected ? "متصل بـ " + (s.app || "بابل") : "غير متصل";
    $("templates").textContent = s.counts.templates ?? "—";
    $("tasks").textContent = s.counts.tasks ?? "—";
    const invoices = s.counts.invoices;
    $("invoices").textContent = invoices === "missing" ? "غير موجود" : (invoices ?? "—");
    $("latency").textContent = s.latency_ms != null ? s.latency_ms + " ms" : "—";
    $("checked").textContent = "آخر فحص " + (s.checked_at || "—");
    $("app-url").textContent = s.app_url || "—";
    if (s.error) { $("conn").textContent = "غير متصل"; $("conn").title = s.error; }
    const row = data.last_sync;
    $("lastSync").textContent = row
      ? `آخر سجل: ${row.date || row.timestamp || ""} — جديد ${row.created ?? row.new ?? "?"} · محدَّث ${row.updated ?? "?"} · فشل ${row.failed ?? "?"}`
      : "لا يوجد سجل سابق في logs/history.csv";
  } catch (err) {
    $("dot").className = "dot bad";
    $("conn").textContent = "تعذّر الوصول للخادم";
  }
}

async function runSync() {
  const btn = $("syncBtn");
  btn.disabled = true; btn.textContent = "جارٍ التشغيل…";
  $("syncMsg").className = "msg"; $("syncMsg").textContent = "";
  try {
    const res = await fetch("/api/sync", {method: "POST"});
    const data = await res.json();
    $("syncLog").textContent = data.output || data.error || "(بلا مخرجات)";
    if (data.ok) {
      const c = data.counts || {};
      $("syncMsg").className = "msg ok";
      $("syncMsg").textContent = `تمّت في ${data.seconds}s — جديد ${c.create ?? "?"} · محدَّث ${c.update ?? "?"} · بلا تغيير ${c.unchanged ?? "?"} · فشل ${c.failed ?? "?"}`;
    } else {
      $("syncMsg").className = "msg bad";
      $("syncMsg").textContent = data.error || "فشلت المزامنة — راجع السجل أدناه";
    }
    await loadStatus();
  } catch (err) {
    $("syncMsg").className = "msg bad"; $("syncMsg").textContent = "خطأ: " + err.message;
  } finally {
    btn.disabled = false; btn.textContent = "تشغيل المزامنة الآن";
  }
}

async function makeInvoice() {
  const btn = $("invBtn");
  btn.disabled = true; btn.textContent = "جارٍ التوليد…";
  $("invMsg").className = "msg"; $("invMsg").textContent = ""; $("invResult").innerHTML = "";
  try {
    const res = await fetch("/api/invoice", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({supplier: $("supplier").value, amount: $("amount").value, rate: $("rate").value})
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "فشل التوليد");
    const inv = data.invoice;
    const rows = Object.entries(inv).map(([k, v]) => `<tr><th>${esc(k)}</th><td>${esc(v ?? "—")}</td></tr>`).join("");
    $("invResult").innerHTML = `<table>${rows}</table>`;
    $("invMsg").className = "msg " + (data.uploaded ? "ok" : "warn");
    $("invMsg").textContent = data.uploaded
      ? "رُفعت إلى بابل (id: " + data.bubble_id + ") — التقرير: " + data.report
      : "حُفظت محليًا فقط: " + (data.warning || "") + " — التقرير: " + data.report;
  } catch (err) {
    $("invMsg").className = "msg bad"; $("invMsg").textContent = err.message;
  } finally {
    btn.disabled = false; btn.textContent = "توليد الفاتورة";
  }
}

$("syncBtn").addEventListener("click", runSync);
$("invBtn").addEventListener("click", makeInvoice);
$("refreshBtn").addEventListener("click", loadStatus);
loadStatus();
setInterval(loadStatus, 15000);
</script>
</body>
</html>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="لوحة تحكم Arab Templates المحلية (Flask، عربية RTL).")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5050)
    parser.add_argument("--open", action="store_true")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args(argv)

    url = f"http://{args.host}:{args.port}/"
    print(f"لوحة تحكم Arab Templates — {url}")
    print("   التوكن يُقرأ من scripts/.env ولا يظهر في الصفحة.")
    if args.open:
        threading.Timer(0.9, lambda: webbrowser.open(url)).start()
    app.run(host=args.host, port=args.port, debug=args.debug, use_reloader=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
