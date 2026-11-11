#!/usr/bin/env python3
"""نواة سرب الوكلاء — Arab Templates × Bubble.

الوكيل الأول (data_fetcher_agent) يجلب تحديثًا حيًّا من الإنترنت، والثاني
(cloud_connector_agent) يضخّه إلى جدول ``task`` في Bubble، مع دوال جاهزة
لبثّ بيانات القوالب العربية إلى جدول ``template``.

كل الكتابة تمر عبر ``bubble_data_sync.BubbleClient``: رابط صحيح
(``/api/1.1/obj/<type>``)، مهلة، إعادة محاولة عند تعذّر الاتصال، ورسائل
عربية تشرح كل رمز حالة. التوكن يبقى في هذا الملف ولا يُطبع أبدًا.

    python agents_swarm_core.py               # مهمة واحدة إلى task
    python agents_swarm_core.py --templates   # + مزامنة القوالب العربية
"""

from __future__ import annotations

import os
import sys
import time
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
        sync_records,
    )
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"ضع bubble_data_sync.py بجانب هذا الملف — {exc}") from exc

NEWS_API = "https://api.spaceflightnewsapi.net/v4/articles?limit=1"
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

    def cloud_connector_templates(self, records=None, dry_run: bool = False) -> dict[str, int]:
        """يرفع/يحدّث القوالب العربية على جدول template (Title مفتاح التطابق)."""
        data = records if records is not None else None
        if data is None:
            from bubble_data_sync import ARABIC_TEMPLATES

            data = ARABIC_TEMPLATES
        try:
            return sync_records(self.client, TEMPLATE_TYPE, data, TEMPLATE_FIELDS, key="Title", dry_run=dry_run)
        except BubbleError as exc:
            print(f"[❌ API Agent] مزامنة القوالب فشلت: {exc}")
            return {"create": 0, "update": 0, "unchanged": 0, "failed": len(data)}


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    with_templates = "--templates" in argv
    app_url = BUBBLE_API_URL
    for index, arg in enumerate(argv):
        if arg == "--app-url" and index + 1 < len(argv):
            app_url = argv[index + 1]

    swarm = AIAgentSwarm(app_url=app_url)
    live_data = swarm.data_fetcher_agent()

    ok = swarm.cloud_connector_agent(
        f"معالجة تحديث: {live_data[:50]}", "High", 85
    )
    if with_templates:
        counts = swarm.cloud_connector_templates()
        ok = ok and not counts.get("failed")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
