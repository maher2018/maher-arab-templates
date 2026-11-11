#!/usr/bin/env python3
"""نواة سرب الوكلاء — Arab Templates × Bubble.

الوكيل الأول (data_fetcher_agent) يجلب تحديثًا حيًّا من الإنترنت، والثاني
(cloud_connector_agent) يضخّه إلى جدول ``task`` في Bubble، مع دوال جاهزة
لبثّ بيانات القوالب العربية إلى جدول ``template``.

كل الكتابة تمر عبر ``bubble_data_sync.BubbleClient``: رابط صحيح
(``/api/1.1/obj/<type>``)، مهلة، إعادة محاولة عند تعذّر الاتصال، ورسائل
عربية تشرح كل رمز حالة. التوكن يبقى في هذا الملف ولا يُطبع أبدًا.

    python agents_swarm_core.py                      # مهمة واحدة إلى task
    python agents_swarm_core.py --templates          # + مزامنة القوالب العربية
    python agents_swarm_core.py --loop              # حلقة مستمرة كل 60 دقيقة
    python agents_swarm_core.py --loop --interval 15 --templates
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

# إعدادات الاتصال السحابي بتطبيق Bubble (Arab Templates).
# BUBBLE_API_URL يجب أن يكون نطاق تطبيقك نفسه، مثل https://my-app.bubbleapps.io
# (أضف /version-test لمزامنة بيانات التطوير بدل النسخة الحيّة).
# الفرع الذي يستجيب فعلًا الآن هو فرع التطوير. بعد نشر إعدادات API في النسخة الحيّة
# (Settings → API ثم Deploy) احذف «/version-test» من الرابط.
BUBBLE_API_URL = os.environ.get("BUBBLE_APP_URL", "https://at-ai-lab.bubbleapps.io/version-test")
BUBBLE_TOKEN = os.environ.get("BUBBLE_TOKEN", "")

sys.path.insert(0, str(Path(__file__).resolve().parent))

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
    raise SystemExit(f"ضع bubble_data_sync.py بجانب هذا الملف — {exc}") from exc

NEWS_API = "https://api.spaceflightnewsapi.net/v4/articles?limit=1"
TEMPLATES_FILE = Path(__file__).resolve().parent.parent / "data" / "templates_ar.json"
FALLBACK_HEADLINE = "مراجعة وتحديث أسعار صرف العملات الخليجية مقابل الدولار"


class AIAgentSwarm:
    def __init__(self, app_url: str = BUBBLE_API_URL, token: str = BUBBLE_TOKEN, verbose: bool = True):
        self.app_url = app_url
        self.token = token
        self.verbose = verbose
        print("[🤖 System] تم تنشيط سرب الوكلاء الموسع: ربط البيانات الحية من الإنترنت لعام 2026...")
        self._client: BubbleClient | None = None

    @property
    def client(self) -> BubbleClient:
        """اتصال واحد يُعاد استخدامه، ويُبنى عند أول حاجة فقط."""
        if self._client is None:
            self._client = BubbleClient(app_url=self.app_url, token=self.token, verbose=self.verbose)
            print(f"[🔗 Bubble] الرابط الفعلي: {self._client.base}")
        return self._client

    # -- الوكيل الأول: سحب البيانات ---------------------------------------- #

    def data_fetcher_agent(self) -> str:
        """يجلب عنوانًا حيًّا من الإنترنت، ويعود بمهمة بديلة عند أي عائق."""
        print("[🌐 Fetcher Agent] جاري فحص الإنترنت لجلب تحديثات السوق والفرص الخليجية...")
        try:
            response = requests.get(NEWS_API, timeout=10)
            response.raise_for_status()
            results = (response.json() or {}).get("results") or []
            title = (results[0] or {}).get("title") if results else None
            if title:
                print(f"[✅ Fetcher Agent] تحديث حقيقي من الإنترنت: {title[:60]}...")
                return title
        except (requests.RequestException, ValueError, KeyError) as exc:
            print(f"[⚠️ Fetcher Agent] تعذّر الجلب ({type(exc).__name__}) — استخدام المهمة الاحتياطية.")
        return FALLBACK_HEADLINE

    # -- الوكيل الثاني: الكتابة إلى Bubble ---------------------------------- #

    def cloud_connector_agent(self, task_name: str, priority: str = "High", progress: int = 0) -> bool:
        """upsert لمهمة في جدول task (لا تتكرر عند إعادة التشغيل)."""
        print("[🚀 API Agent] جاري ضخ البيانات سحابيًا إلى لوحة الكانبان...")
        try:
            status, uid = self.client.upsert(
                "task",
                {"Task_Name": task_name, "Priority": priority, "Progress_Percentage": progress},
                key="Task_Name",
            )
        except BubbleError as exc:
            print(f"[❌ API Agent] فشل الكتابة في task: {exc}")
            return False
        label = {"create": "سجل جديد", "update": "تم تحديث مهمة موجودة", "unchanged": "موجودة بلا تغيير"}.get(status, status)
        print(f"[🎉 API Agent] {label} — {task_name[:60]}")
        if uid:
            print(f"     المعرّف: {uid}")
        return True

    def cloud_connector_templates(self, records=None, dry_run: bool = False, json_file: str | None = None) -> dict[str, int]:
        """يرفع/يحدّث القوالب العربية على جدول template (Title مفتاح التطابق).

        المصدر الافتراضي هو data/templates_ar.json، لا العيّنة المدمجة، حتى لا
        تُنشأ سجلات تجريبية عند كل دورة من دورات الحلقة.
        """
        data = records
        if data is None:
            data = load_records(json_file or str(TEMPLATES_FILE), TEMPLATE_TYPE)
        try:
            return sync_records(self.client, TEMPLATE_TYPE, data, TEMPLATE_FIELDS, key="Title", dry_run=dry_run)
        except BubbleError as exc:
            print(f"[❌ API Agent] مزامنة القوالب فشلت: {exc}")
            return {"create": 0, "update": 0, "unchanged": 0, "failed": len(data)}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="سرب الوكلاء: جلب تحديث حيّ وكتابته في Bubble، مرة واحدة أو في حلقة مستمرة.",
    )
    parser.add_argument("--loop", action="store_true", help="تشغيل مستمر في الخلفية بدل دورة واحدة")
    parser.add_argument("--interval", type=float, default=60.0, help="الدقائق بين الدورات (افتراضي 60)")
    parser.add_argument("--cycles", type=int, default=0, help="عدد الدورات ثم التوقف (0 = بلا حد)")
    parser.add_argument("--templates", action="store_true", help="مزامنة القوالب العربية في كل دورة")
    parser.add_argument("--app-url", default=None, help="رابط تطبيق Bubble (افتراضيًا من .env أو الثابت)")
    parser.add_argument("--templates-file", default=None, help="ملف بيانات القوالب (افتراضيًا data/templates_ar.json)")
    parser.add_argument("--log-file", default=None, help="حفظ سجل الدورات في ملف نصي بالإضافة إلى الطرفية")
    return parser.parse_args(argv)


def make_logger(log_file: str | None):
    """سجل موحّد: الطرفية دائمًا، والملف عند تمريره (مفيد عند التشغيل في الخلفية)."""
    handle = open(log_file, "a", encoding="utf-8") if log_file else None

    def log(message: str, *, quiet: bool = False) -> None:
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{stamp} {message}"
        if not quiet:
            print(line, flush=True)
        if handle:
            handle.write(line + chr(10))
            handle.flush()

    log.close = lambda: handle.close() if handle else None  # type: ignore[attr-defined]
    return log


def run_cycle(swarm: AIAgentSwarm, *, with_templates: bool, log, templates_file: str | None = None) -> bool:
    """دورة واحدة: جلب تحديث حيّ، كتابته في task، ثم (اختياريًا) مزامنة القوالب."""
    live_data = swarm.data_fetcher_agent()
    ok = swarm.cloud_connector_agent(f"معالجة تحديث: {live_data[:50]}", "High", 85)
    if with_templates:
        counts = swarm.cloud_connector_templates(json_file=templates_file)
        ok = ok and not counts.get("failed")
        log(
            "[📦 القوالب] "
            f"جديد {counts['create']} | محدَّث {counts['update']} | "
            f"بلا تغيير {counts['unchanged']} | فشل {counts['failed']}"
        )
    return ok


def run_loop(
    swarm: AIAgentSwarm,
    *,
    interval_minutes: float,
    cycles: int,
    with_templates: bool,
    log,
    templates_file: str | None = None,
) -> int:
    """حلقة مستمرة: كل دورة تُسجّل نتيجتها، وأي خطأ لا يُسقط الحلقة."""
    interval_seconds = max(0.0, interval_minutes) * 60
    plan = "بلا حد" if cycles <= 0 else f"{cycles} دورة"
    log(f"[🔁 Loop] بدأت الحلقة — كل {interval_minutes:g} دقيقة ({plan})")
    completed = 0
    try:
        while True:
            completed += 1
            started = time.time()
            log(f"[🔄 دورة {completed}] بدأت")
            try:
                ok = run_cycle(swarm, with_templates=with_templates, log=log, templates_file=templates_file)
            except BubbleError as exc:
                ok = False
                log(f"[❌ دورة {completed}] خطأ Bubble: {str(exc).splitlines()[0]}")
            except Exception as exc:  # الحلقة تستمر حتى لو فشلت دورة
                ok = False
                log(f"[❌ دورة {completed}] خطأ غير متوقع: {type(exc).__name__}: {exc}")
            log(f"[🔄 دورة {completed}] {('نجحت' if ok else 'بها فشل')} في {time.time() - started:.1f} ثانية")
            if cycles > 0 and completed >= cycles:
                log(f"[✅ Loop] انتهت الدورات المطلوبة ({completed})")
                return 0
            log(f"[⏳] انتظار {interval_minutes:g} دقيقة حتى الدورة {completed + 1}…")
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        log(f"[⛔] أُوقفت الحلقة يدويًا بعد {completed} دورة — خروج نظيف.")
        return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    log = make_logger(args.log_file)
    swarm = AIAgentSwarm(app_url=args.app_url or BUBBLE_API_URL)

    if args.loop:
        try:
            return run_loop(
                swarm,
                interval_minutes=args.interval,
                cycles=args.cycles,
                with_templates=args.templates,
                log=log,
                templates_file=args.templates_file,
            )
        finally:
            log.close()  # type: ignore[attr-defined]

    ok = run_cycle(swarm, with_templates=args.templates, log=log, templates_file=args.templates_file)
    log.close()  # type: ignore[attr-defined]
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
