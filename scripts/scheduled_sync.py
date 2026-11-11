#!/usr/bin/env python3
"""مزامنة Arab Templates الدورية: تشغيل تلقائي + سجل يومي.

يغلّف bubble_data_sync ليعمل بلا تدخّل:
  * يمنع التشغيل المتداخل بقفل ملف.
  * يكتب سجلًا يوميًا في logs/sync-YYYY-MM-DD.log وسطرًا في logs/history.csv.
  * يحذف السجلات الأقدم من عدد الأيام المحدد.
  * يسجّل مهمة Windows Task Scheduler يومية (أو cron على غير Windows).

أوامر:
    python scheduled_sync.py --once                 # تشغيلة واحدة (وهو ما ينفذه المجدول)
    python scheduled_sync.py --install              # مهمة يومية 08:00
    python scheduled_sync.py --install --time 07:30
    python scheduled_sync.py --status               # حالة المهمة وآخر التشغيلات
    python scheduled_sync.py --uninstall
"""

from __future__ import annotations

import argparse
import csv
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

try:
    from bubble_data_sync import (
        TEMPLATE_FIELDS,
        TEMPLATE_TYPE,
        BubbleClient,
        BubbleError,
        load_records,
        sync_records,
    )
except ImportError as exc:  # pragma: no cover
    sys.exit(f"ضع bubble_data_sync.py بجانب هذا الملف — {exc}")

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass

TASK_NAME = r"ArabTemplates\BubbleSync"
ROOT = HERE.parent
LOGS = ROOT / "logs"
LOCK = LOGS / ".sync.lock"
HISTORY = LOGS / "history.csv"
LOCK_TTL = timedelta(hours=6)


def log_path(day: datetime | None = None) -> Path:
    day = day or datetime.now()
    return LOGS / f"sync-{day:%Y-%m-%d}.log"


class RunLog:
    """يكتب في الطرفية وفي سجل اليوم معًا."""

    def __init__(self, quiet: bool = False):
        LOGS.mkdir(exist_ok=True)
        self.path = log_path()
        self.quiet = quiet

    def __call__(self, tag: str, message: str) -> None:
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{stamp} [{tag}] {message}"
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        if not self.quiet:
            print(line, flush=True)


def acquire_lock() -> bool:
    LOGS.mkdir(exist_ok=True)
    if LOCK.exists():
        age = datetime.now() - datetime.fromtimestamp(LOCK.stat().st_mtime)
        if age < LOCK_TTL:
            return False
        LOCK.unlink(missing_ok=True)
    LOCK.write_text(f"{os.getpid()} {datetime.now().isoformat(timespec='seconds')}", encoding="utf-8")
    return True


def release_lock() -> None:
    LOCK.unlink(missing_ok=True)


def prune_logs(keep_days: int) -> None:
    cutoff = datetime.now() - timedelta(days=keep_days)
    for path in LOGS.glob("sync-*.log"):
        try:
            day = datetime.strptime(path.stem.replace("sync-", ""), "%Y-%m-%d")
        except ValueError:
            continue
        if day < cutoff:
            path.unlink(missing_ok=True)


def append_history(counts: dict[str, int], status: str, seconds: float) -> None:
    new = not HISTORY.exists()
    with HISTORY.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if new:
            writer.writerow(["date", "time", "created", "updated", "unchanged", "failed", "status", "duration_s"])
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d"),
            datetime.now().strftime("%H:%M:%S"),
            counts.get("create", 0),
            counts.get("update", 0),
            counts.get("unchanged", 0),
            counts.get("failed", 0),
            status,
            f"{seconds:.1f}",
        ])


def run_once(json_file: str | None, dry_run: bool, quiet: bool, keep_days: int) -> int:
    if not acquire_lock():
        print("[i] تشغيلة أخرى قيد التنفيذ (قفل قائم) — تم التجاهل.", flush=True)
        return 3
    started = time.time()
    log = RunLog(quiet)
    log("START", "تشغيلة مزامنة" + (" (تجريبية)" if dry_run else ""))
    counts = {"create": 0, "update": 0, "unchanged": 0, "failed": 0}
    status = "failed"
    try:
        records = load_records(json_file, TEMPLATE_TYPE)
        log("SOURCE", f"{len(records)} سجلًا من {json_file or 'العيّنة المدمجة'}")
        client = BubbleClient(verbose=False)
        log("BUBBLE", f"الرابط: {client.base}")
        counts = sync_records(client, TEMPLATE_TYPE, records, TEMPLATE_FIELDS, key="Title", dry_run=dry_run)
        status = "ok" if not counts["failed"] else "partial"
        log("RESULT", f"جديد {counts['create']} | محدَّث {counts['update']} | بلا تغيير {counts['unchanged']} | فشل {counts['failed']}")
        code = 0 if counts["failed"] == 0 else 1
    except BubbleError as exc:
        log("ERROR", str(exc).splitlines()[0])
        code = 2
    except Exception as exc:  # pragma: no cover - أي خطأ غير متوقع يُسجّل ولا يُسقط المجدول
        log("ERROR", f"{type(exc).__name__}: {exc}")
        code = 2
    finally:
        seconds = time.time() - started
        append_history(counts, status, seconds)
        prune_logs(keep_days)
        log("DONE", f"{status} في {seconds:.1f} ثانية — السجل: {log.path.name}")
        release_lock()
    return code


# --------------------------------------------------------------------------- #
# Windows Task Scheduler
# --------------------------------------------------------------------------- #


def task_command() -> str:
    return f'"{sys.executable}" "{HERE / "scheduled_sync.py"}" --once --json "{ROOT / "data" / "templates_ar.json"}"'


def install(time_str: str) -> int:
    if os.name != "nt":
        print("[i] على غير Windows استخدم cron:")
        print(f'    0 8 * * * cd "{HERE}" && {sys.executable} scheduled_sync.py --once')
        return 0
    if not shutil.which("schtasks"):
        print("[✗] schtasks غير متاح على هذا النظام.")
        return 2
    result = subprocess.run(
        ["schtasks", "/Create", "/TN", TASK_NAME, "/TR", task_command(), "/SC", "DAILY", "/ST", time_str, "/F"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        print("[✗] فشل إنشاء المهمة:", (result.stdout or result.stderr).strip()[:400])
        return 2
    print(f"[✓] سُجّلت مهمة يومية باسم {TASK_NAME} الساعة {time_str}")
    print(f"    الأمر: {task_command()}")
    return 0


def uninstall() -> int:
    if os.name != "nt":
        print("[i] احذف سطر cron يدويًا.")
        return 0
    result = subprocess.run(
        ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        print("[✗] لم أجد المهمة أو تعذّر حذفها:", (result.stdout or result.stderr).strip()[:300])
        return 2
    print(f"[✓] حُذفت المهمة {TASK_NAME}")
    return 0


def status() -> int:
    if os.name == "nt":
        result = subprocess.run(
            ["schtasks", "/Query", "/TN", TASK_NAME, "/FO", "LIST"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        if result.returncode == 0:
            wanted = (
                "TaskName", "Next Run Time", "Status", "Last Run Time", "Last Result",
                "اسم المهمة", "وقت التشغيل التالي", "الحالة", "وقت آخر تشغيل", "آخر نتيجة",
            )
            print("[✓] المهمة المجدولة:")
            for line in (result.stdout or "").splitlines():
                if any(key in line for key in wanted):
                    print("   ", line.strip())
        else:
            print("[i] لا مهمة مجدولة بهذا الاسم بعد (شغّل --install).")
    if HISTORY.exists():
        rows = HISTORY.read_text(encoding="utf-8").strip().splitlines()[-6:]
        print("\n[i] آخر التشغيلات (logs/history.csv):")
        for row in rows:
            print("   ", row)
    today = log_path()
    print(f"\n[i] سجل اليوم: {today if today.exists() else 'لم يُكتب بعد'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="مزامنة دورية لبيانات القوالب مع سجل يومي.")
    parser.add_argument("--once", action="store_true", help="تشغيلة واحدة (تنفّذها المهمة المجدولة)")
    parser.add_argument("--install", action="store_true", help="سجّل مهمة يومية في Task Scheduler")
    parser.add_argument("--uninstall", action="store_true", help="احذف المهمة المجدولة")
    parser.add_argument("--status", action="store_true", help="حالة المهمة وآخر التشغيلات")
    parser.add_argument("--time", default="08:00", help="وقت التشغيل اليومي HH:MM (افتراضي 08:00)")
    default_json = ROOT / "data" / "templates_ar.json"
    parser.add_argument(
        "--json",
        dest="json_file",
        default=str(default_json) if default_json.exists() else None,
        help="ملف بيانات القوالب (افتراضيًا data/templates_ar.json ثم العيّنة المدمجة)",
    )
    parser.add_argument("--dry-run", action="store_true", help="تشغيلة تجريبية بلا كتابة")
    parser.add_argument("--quiet", action="store_true", help="لا تطبع إلا الأخطاء")
    parser.add_argument("--keep-days", type=int, default=30, help="أيام الاحتفاظ بسجلات التشغيل")
    args = parser.parse_args(argv)

    if args.install:
        return install(args.time)
    if args.uninstall:
        return uninstall()
    if args.status:
        return status()
    return run_once(args.json_file, args.dry_run, args.quiet, args.keep_days)


if __name__ == "__main__":
    sys.exit(main())
