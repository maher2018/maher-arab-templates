#!/usr/bin/env python3
"""عميل Bubble Data API لمشروع Arab Templates.

يقرأ التوكن ورابط التطبيق من ``agents_swarm_core.py`` (أو من متغيّري البيئة
``BUBBLE_TOKEN`` و``BUBBLE_APP_URL``)، ويوفّر:

* عمليات CRUD عامة على أي Data Type (list / find / create / update / bulk).
* رفع وتحديث **تلقائي** لبيانات القوالب العربية على جدول ``template``
  (Title, Category, Description, Price, Preview_URL) بمنطق upsert: يُحدَّث
  القالب الموجود ويُنشأ غير الموجود، فلا تتكرر السجلات عند إعادة التشغيل.
* مسار ``task`` الجاهز للاختبار الفوري (Task_Name, Priority, Progress_Percentage).
* معالجة أخطاء الاتصال: مهلة، إعادة محاولة بتراجع أُسّي، ورسائل عربية واضحة
  تشرح كل رمز حالة من Bubble (401/400/404/429) وسببها وكيفية إصلاحه.

أمثلة:
    python bubble_data_sync.py check
    python bubble_data_sync.py list --type task
    python bubble_data_sync.py test-task
    python bubble_data_sync.py sync-templates --dry-run
    python bubble_data_sync.py sync-templates --json my_templates.json
    python bubble_data_sync.py sync-tasks

التوكن لا يُطبع في أي مخرج (يُقنَّع دائمًا).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Iterable, Sequence
from urllib.parse import urlparse

try:
    import requests
except ImportError:  # pragma: no cover - بيئة بلا requests
    sys.exit("هذا السكربت يحتاج حزمة requests:  pip install requests")

try:  # أسماء عربية في مخرجات الطرفية على Windows
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass

HERE = Path(__file__).resolve().parent
DEFAULT_CONFIG_FILE = HERE / "agents_swarm_core.py"

TASK_TYPE = "task"
TEMPLATE_TYPE = "template"
TASK_FIELDS = ("Task_Name", "Priority", "Progress_Percentage")
# أسماء الحقول كما هي فعلًا في تطبيق Arab Templates: الكتابة في Bubble حسّاسة لحالة الأحرف.
TEMPLATE_FIELDS = ("Title", "Category", "description", "price", "preview_url")

#: مفاتيح مقبولة في ملفات JSON: إنجليزي، أو اسم الحقل نفسه، أو عربي.
ALIASES: dict[str, tuple[str, ...]] = {
    "Title": ("title", "name", "اسم القالب", "الاسم", "العنوان"),
    "Category": ("category", "الفئة", "التصنيف"),
    "description": ("Description", "description", "الوصف", "وصف"),
    "price": ("Price", "price", "السعر", "الثمن"),
    "preview_url": ("Preview_URL", "preview_url", "preview", "رابط_المعاينة", "رابط المعاينة"),
    "Task_Name": ("task_name", "name", "المهمة", "اسم المهمة"),
    "Priority": ("priority", "الأولوية"),
    "Progress_Percentage": ("progress_percentage", "progress", "نسبة الإنجاز"),
}

#: بيانات القوالب العربية الافتراضية (تُرفع عند تشغيل sync-templates بلا --json).
ARABIC_TEMPLATES: list[dict[str, Any]] = [
    {
        "Title": "قالب متجر إلكتروني عربي",
        "Category": "متاجر إلكترونية",
        "Description": "قالب متجر كامل بواجهة عربية من اليمين إلى اليسار، مع سلة شراء وصفحة دفع جاهزة.",
        "Price": 249,
        "Preview_URL": "https://arab-templates.example.com/previews/store-ar",
    },
    {
        "Title": "قالب لوحة تحكم تحليلية",
        "Category": "لوحات تحكم",
        "Description": "لوحة تحكم بالرسوم البيانية والتقارير، مناسبة للمشاريع التي تحتاج متابعة مؤشرات يومية.",
        "Price": 399,
        "Preview_URL": "https://arab-templates.example.com/previews/dashboard-ar",
    },
    {
        "Title": "قالب موقع شخصي للمستقلين",
        "Category": "مواقع شخصية",
        "Description": "صفحة تعريفية أنيقة لعرض الأعمال والمهارات مع نموذج تواصل.",
        "Price": 99,
        "Preview_URL": "https://arab-templates.example.com/previews/portfolio-ar",
    },
    {
        "Title": "قالب تطبيق حجوزات",
        "Category": "تطبيقات",
        "Description": "قالب حجوزات مواعيد بواجهة عربية وبطاقات خدمة وتقويم قابل للتخصيص.",
        "Price": 299,
        "Preview_URL": "https://arab-templates.example.com/previews/booking-ar",
    },
    {
        "Title": "قالب صفحة هبوط للحملات",
        "Category": "تسويق",
        "Description": "صفحة هبوط سريعة بمكوّنات قابلة للتعديل ونداءات للعمل ونموذج تسجيل.",
        "Price": 79,
        "Preview_URL": "https://arab-templates.example.com/previews/landing-ar",
    },
]


class BubbleError(RuntimeError):
    """خطأ في الإعداد أو في استجابة Bubble، برسالة عربية قابلة للعرض."""

    def __init__(self, message: str, status: int | None = None, body: str | None = None):
        super().__init__(message)
        self.status = status
        self.body = body


# --------------------------------------------------------------------------- #
# الإعدادات
# --------------------------------------------------------------------------- #


def mask(secret: str) -> str:
    """يجعل التوكن قابلًا للعرض في السجل دون كشفه."""
    if not secret:
        return "(غير موجود)"
    if len(secret) <= 8:
        return "*" * len(secret)
    return f"{secret[:4]}…{secret[-2:]} ({len(secret)} حرفًا)"


def _read_config(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _dotenv(key: str) -> str | None:
    """يقرأ مفتاحًا من scripts/.env أو .env في جذر المشروع (بلا طباعة قيمه)."""
    for candidate in (HERE / ".env", HERE.parent / ".env"):
        try:
            for line in candidate.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                name, value = line.split("=", 1)
                if name.strip() == key:
                    return value.strip().strip('"').strip("'")
        except OSError:
            continue
    return None


def load_token(config_file: Path = DEFAULT_CONFIG_FILE, override: str | None = None) -> str:
    """التوكن من الوسيط، ثم البيئة، ثم ملف الإعدادات."""
    token = (override or os.environ.get("BUBBLE_TOKEN") or _dotenv("BUBBLE_TOKEN") or "").strip()
    if token:
        return token
    text = _read_config(config_file)
    match = re.search(r"BUBBLE_TOKEN\s*=\s*[\"']([^\"']+)[\"']", text) or re.search(
        r"BUBBLE_API_TOKEN\s*=\s*[\"']([^\"']+)[\"']", text
    )
    if not match:
        raise BubbleError(
            f"لم أجد BUBBLE_TOKEN في {config_file}. أضف السطر: BUBBLE_TOKEN = \"...\" "
            "أو صدّر المتغيّر BUBBLE_TOKEN."
        )
    return match.group(1).strip()


def load_app_url(config_file: Path = DEFAULT_CONFIG_FILE, override: str | None = None) -> str:
    """رابط التطبيق من الوسيط، ثم البيئة، ثم ملف الإعدادات."""
    url = (override or os.environ.get("BUBBLE_APP_URL") or _dotenv("BUBBLE_APP_URL") or "").strip()
    if url:
        return url
    text = _read_config(config_file)
    match = re.search(r"BUBBLE_API_URL\s*=\s*[\"']([^\"']+)[\"']", text)
    if not match:
        raise BubbleError(
            f"لم أجد BUBBLE_API_URL في {config_file}. ضع رابط تطبيقك مثل "
            "https://my-app.bubbleapps.io، أو مرّر --app-url."
        )
    return match.group(1).strip()


def normalize_base(url: str) -> str:
    """يُكمل الرابط إلى صيغة ``https://<app>.bubbleapps.io/api/1.1/obj``."""
    base = url.strip().rstrip("/")
    if not base:
        raise BubbleError("رابط تطبيق Bubble فارغ.")
    if "://" not in base:
        base = "https://" + base
    parsed = urlparse(base)
    if not parsed.netloc:
        raise BubbleError(f"رابط غير صالح: {url}")
    if parsed.netloc in {"bubbleapps.io", "www.bubbleapps.io"}:
        raise BubbleError(
            "الرابط «https://bubbleapps.io» هو نطاق الخدمة وليس تطبيقك. المطلوب نطاق فرعي، مثل "
            "https://my-app.bubbleapps.io  (أو نطاقك المخصص)، ويمكن إضافة /version-test لبيانات التطوير."
        )
    if base.endswith("/api/1.1/obj"):
        return base
    if base.endswith("/api/1.1"):
        return base + "/obj"
    return base + "/api/1.1/obj"


def _error_detail(response: "requests.Response") -> str:
    """رسالة Bubble كما هي، مختصرة، بلا أي سر."""
    try:
        body = response.json()
    except ValueError:
        return (response.text or "").strip()[:300]
    if isinstance(body, dict):
        inner = body.get("body") if isinstance(body.get("body"), dict) else body
        for key in ("message", "error", "status"):
            value = inner.get(key) if isinstance(inner, dict) else None
            if isinstance(value, str) and value:
                return value[:300]
        return json.dumps(body, ensure_ascii=False)[:300]
    return str(body)[:300]


_STATUS_HINTS = {
    400: "حقل غير معروف أو نوع قيمة خاطئ. أسماء الحقول يجب أن تطابق Data Type حرفيًا (مثل Title و Price).",
    401: "التوكن مرفوض: تحقق من صحته، ومن أن Privacy Rules تسمح بـ Create/Modify via API، وأن الإعدادات منشورة على الفرع الصحيح.",
    403: "التوكن لا يملك صلاحية على هذا النوع (نوع تطبيق مختلف أو توكن مستخدم بدل توكن إدارة).",
    404: "النوع أو السجل غير موجود: تأكد أن Data Type مفعّل في Settings → API، وأن اسمه صحيح (task / template)، وأنك على الفرع الصحيح (مثل /version-test).",
    429: "تجاوزت سعة التطبيق أو حدّ المعدل. أعد المحاولة بعد قليل أو قلّل عدد الطلبات المتوازية.",
}


class BubbleClient:
    """عميل صغير وواضح لـ Bubble Data API."""

    def __init__(
        self,
        app_url: str | None = None,
        token: str | None = None,
        config_file: Path = DEFAULT_CONFIG_FILE,
        timeout: float = 20.0,
        retries: int = 3,
        backoff: float = 1.7,
        verbose: bool = True,
    ):
        self.config_file = config_file
        self.token = load_token(config_file, token)
        self.base = normalize_base(load_app_url(config_file, app_url))
        self.timeout = timeout
        self.retries = max(0, retries)
        self.backoff = backoff
        self.verbose = verbose
        self._key_cache: dict[str, list[str] | None] = {}
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/json",
                "User-Agent": "arab-templates-bubble-sync/1.0",
            }
        )

    # -- طبقة النقل --------------------------------------------------------- #

    def _log(self, message: str) -> None:
        if self.verbose:
            print(message, flush=True)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
        data: str | None = None,
        content_type: str | None = None,
    ) -> "requests.Response":
        url = f"{self.base}/{path.lstrip('/')}"
        headers = {"Content-Type": content_type} if content_type else None
        last_error: Exception | None = None

        for attempt in range(1, self.retries + 2):
            try:
                response = self.session.request(
                    method, url, params=params, json=json_body, data=data, headers=headers, timeout=self.timeout
                )
            except requests.exceptions.Timeout as exc:
                last_error = exc
                if attempt > self.retries:
                    raise BubbleError(f"انتهت مهلة الاتصال بـ Bubble ({self.timeout:.0f} ثانية) بعد {attempt - 1} محاولة. تحقق من الشبكة.") from exc
            except requests.exceptions.SSLError as exc:
                raise BubbleError(f"خطأ في شهادة TLS مع {urlparse(url).netloc}: {exc}") from exc
            except requests.exceptions.ConnectionError as exc:
                last_error = exc
                if attempt > self.retries:
                    raise BubbleError(
                        f"تعذّر الوصول إلى {urlparse(url).netloc} بعد {attempt - 1} محاولة. "
                        "تحقق من اسم التطبيق في الرابط، ومن اتصال الإنترنت، ومن أي جدار حماية."
                    ) from exc
            else:
                # 5xx و429: أخطاء عابرة تستحق إعادة المحاولة قبل أن نفشل.
                if response.status_code in (429, 500, 502, 503, 504) and attempt <= self.retries:
                    wait = self.backoff ** attempt
                    self._log(f"   [↻] استجابة {response.status_code} — إعادة المحاولة {attempt}/{self.retries} بعد {wait:.1f} ث")
                    time.sleep(wait)
                    continue
                return response

            wait = self.backoff ** attempt
            self._log(f"   [↻] خطأ اتصال ({type(last_error).__name__}) — إعادة {attempt}/{self.retries} بعد {wait:.1f} ث")
            time.sleep(wait)

        raise BubbleError("فشل الطلب دون استجابة من Bubble.")

    def _expect(self, response: "requests.Response", action: str, type_name: str) -> None:
        if response.ok:
            return
        detail = _error_detail(response)
        hint = _STATUS_HINTS.get(response.status_code, "")
        if response.status_code == 400 and "invalid appname" in detail.lower():
            hint = "اسم التطبيق في الرابط غير موجود. استخدم اسم التطبيق نفسه كما في Bubble، مثل https://at-ai-lab.bubbleapps.io"
        elif response.status_code == 401 and "expired token" in detail.lower():
            hint = (
                "التوكن غير صالح على هذا الفرع. جرّب فرع التطوير بإضافة /version-test، "
                "أو أعد نشر إعدادات API في Settings ثم Deploy إلى النسخة الحيّة."
            )
        message = f"{action} على «{type_name}» فشل: HTTP {response.status_code}"
        if detail:
            message += f" — {detail}"
        if hint:
            message += f"\n   ↳ {hint}"
        raise BubbleError(message, status=response.status_code, body=detail)

    # -- CRUD --------------------------------------------------------------- #

    def field_keys(self, type_name: str) -> list[str] | None:
        """أسماء الحقول الفعلية كما يعيدها Bubble، مستنتجة من أول سجل موجود."""
        if type_name in self._key_cache:
            return self._key_cache[type_name]
        keys: list[str] | None = None
        try:
            rows = self.list_things(type_name, limit=1)
        except BubbleError:
            rows = []
        if rows:
            keys = list(rows[0].keys())
        self._key_cache[type_name] = keys
        return keys

    def fit_payload(self, type_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        """يطابق حالة أحرف المفاتيح مع مفاتيح Bubble الحقيقية (الكتابة حسّاسة لها)."""
        keys = self.field_keys(type_name)
        if not keys:
            return payload
        lookup = {k.lower(): k for k in keys}
        fitted: dict[str, Any] = {}
        unknown: list[str] = []
        for key, value in payload.items():
            if key in keys:
                fitted[key] = value
            elif key.lower() in lookup:
                fitted[lookup[key.lower()]] = value
            else:
                unknown.append(key)
        if unknown:
            raise BubbleError(
                f"الحقول {unknown} غير موجودة في «{type_name}». الموجود فعلًا: {keys}",
                status=400,
            )
        return fitted

    def list_things(
        self,
        type_name: str,
        *,
        key: str | None = None,
        value: Any = None,
        limit: int = 100,
        cursor: int | None = None,
        sort_field: str | None = None,
        descending: bool | None = None,
        constraints: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": limit}
        if constraints:
            params["constraints"] = json.dumps(constraints, ensure_ascii=False)
        elif key is not None:
            params["constraints"] = json.dumps(
                [{"key": key, "constraint_type": "equals", "value": value}], ensure_ascii=False
            )
        if cursor is not None:
            params["cursor"] = cursor
        if sort_field:
            params["sort_field"] = sort_field
        if descending is not None:
            params["descending"] = str(descending).lower()
        response = self._request("GET", type_name, params=params)
        self._expect(response, "قراءة", type_name)
        payload = response.json() or {}
        return (payload.get("response") or {}).get("results") or []

    def find_one(self, type_name: str, key: str, value: Any) -> dict[str, Any] | None:
        found = self.list_things(type_name, key=key, value=value, limit=1)
        return found[0] if found else None

    def create(self, type_name: str, payload: dict[str, Any]) -> str:
        response = self._request("POST", type_name, json_body=payload)
        self._expect(response, "إنشاء", type_name)
        body = response.json() or {}
        new_id = body.get("id") or (body.get("response") or {}).get("_id")
        return str(new_id or "")

    def update(self, type_name: str, uid: str, payload: dict[str, Any]) -> None:
        response = self._request("PATCH", f"{type_name}/{uid}", json_body=payload)
        self._expect(response, "تحديث", type_name)

    def bulk_create(self, type_name: str, records: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
        """إنشاء سجلات كثيرة بطلب واحد (NDJSON، حد أقصى 1000 سجل)."""
        if not records:
            return []
        if len(records) > 1000:
            raise BubbleError("الحد الأقصى في طلب bulk هو 1000 سجل؛ قسّم الدفعة.")
        body = "\n".join(json.dumps(record, ensure_ascii=False) for record in records)
        response = self._request(
            "POST", f"{type_name}/bulk", data=body.encode("utf-8"), content_type="text/plain; charset=utf-8"
        )
        self._expect(response, "إنشاء جماعي", type_name)
        results = []
        for line in (response.text or "").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                results.append(json.loads(line))
            except ValueError:
                results.append({"status": "error", "raw": line[:200]})
        return results

    # -- upsert ------------------------------------------------------------- #

    def upsert(
        self,
        type_name: str,
        payload: dict[str, Any],
        *,
        key: str = "Title",
        dry_run: bool = False,
    ) -> tuple[str, str]:
        """يُنشئ السجل أو يحدّثه حسب حقل ``key``. يعيد (الحالة، المعرّف)."""
        payload = self.fit_payload(type_name, payload)
        actual_key = key if key in payload else next((k for k in payload if k.lower() == key.lower()), key)
        value = payload.get(actual_key)
        if value in (None, ""):
            raise BubbleError(f"الحقل «{key}» مطلوب لتحديد وجود السجل في «{type_name}».")
        existing = self.find_one(type_name, actual_key, value)
        if existing is None:
            if dry_run:
                return "create (تجريبي)", ""
            return "create", self.create(type_name, payload)

        uid = str(existing.get("_id") or "")
        changed = {
            field: val
            for field, val in payload.items()
            if _differs(existing.get(field), val)
        }
        if not changed:
            return "unchanged", uid
        if dry_run:
            return f"update (تجريبي: {', '.join(changed)})", uid
        self.update(type_name, uid, changed)
        return "update", uid


def _differs(current: Any, wanted: Any) -> bool:
    if isinstance(wanted, (int, float)) and not isinstance(wanted, bool):
        try:
            return round(float(current or 0), 4) != round(float(wanted), 4)
        except (TypeError, ValueError):
            return True
    return ("" if current is None else str(current)) != ("" if wanted is None else str(wanted))


# --------------------------------------------------------------------------- #
# تطبيع البيانات العربية
# --------------------------------------------------------------------------- #


def _pick(row: dict[str, Any], field: str) -> Any:
    if field in row:
        return row[field]
    lowered = {str(k).strip().lower(): v for k, v in row.items()}
    for alias in ALIASES.get(field, ()):
        if alias.lower() in lowered:
            return lowered[alias.lower()]
    return None


def normalize_record(row: dict[str, Any], fields: Sequence[str], type_name: str) -> dict[str, Any]:
    """يحوّل أي مفاتيح (عربية أو إنجليزية) إلى أسماء حقول Bubble، ويرفض السجل الناقص."""
    record: dict[str, Any] = {}
    for field in fields:
        value = _pick(row, field)
        if value is None:
            continue
        if isinstance(value, str):
            value = value.strip()
        if field.lower() == "price":
            try:
                value = round(float(value), 2)
            except (TypeError, ValueError):
                raise BubbleError(f"السعر في «{row}» ليس رقمًا صالحًا: {value!r}")
            if value < 0:
                raise BubbleError(f"السعر سالب في القالب «{_pick(row, 'Title')}».")
        record[field] = value

    required = "Title" if type_name == TEMPLATE_TYPE else "Task_Name"
    if not record.get(required):
        raise BubbleError(f"السجل في «{type_name}» يحتاج الحقل «{required}»: {row}")
    known = {str(f).lower() for f in fields}
    for f in fields:
        known.update(alias.lower() for alias in ALIASES.get(f, ()))
    unknown = [k for k in row if str(k).lower() not in known and str(k).lower() not in {"id", "_id"}]
    if unknown and type_name == TEMPLATE_TYPE:
        print(f"   [i] تم تجاهل حقول غير معروفة: {', '.join(map(str, unknown))}")
    return record


def load_records(path: str | Path | None, type_name: str) -> list[dict[str, Any]]:
    """يقرأ السجلات من JSON (قائمة أو كائن فيه records/items/templates) أو من العيّنة."""
    if path is None:
        if type_name == TEMPLATE_TYPE:
            return [dict(item) for item in ARABIC_TEMPLATES]
        raise BubbleError("مرّر --json لبيانات task، أو استخدم test-task لتجربة سريعة.")
    file = Path(path)
    try:
        raw = json.loads(file.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise BubbleError(f"الملف غير موجود: {file}")
    except ValueError as exc:
        raise BubbleError(f"ملف JSON غير صالح ({file}): {exc}")
    if isinstance(raw, dict):
        for key in ("records", "items", "templates", "data"):
            if isinstance(raw.get(key), list):
                raw = raw[key]
                break
        else:
            raw = [raw]
    if not isinstance(raw, list):
        raise BubbleError("صيغة الملف يجب أن تكون قائمة سجلات أو كائنًا يحتوي records.")
    return raw


def sync_records(
    client: BubbleClient,
    type_name: str,
    records: Iterable[dict[str, Any]],
    fields: Sequence[str],
    *,
    key: str,
    dry_run: bool = False,
) -> dict[str, int]:
    """upsert لكل سجل مع متابعة الأخطاء بدل التوقف عند أول فشل."""
    counts = {"create": 0, "update": 0, "unchanged": 0, "failed": 0}
    records = list(records)
    print(f"\n[⇪] مزامنة {len(records)} سجلًا على «{type_name}» (مفتاح التطابق: {key})"
          + (" — وضع تجريبي بلا كتابة" if dry_run else ""))

    for index, row in enumerate(records, start=1):
        try:
            payload = normalize_record(row, fields, type_name)
            status, uid = client.upsert(type_name, payload, key=key, dry_run=dry_run)
        except BubbleError as exc:
            if exc.status == 400 and "unrecognized field" in str(exc).lower():
                remaining = len(records) - index + 1
                counts["failed"] += remaining
                print(f"   [!] مخطط «{type_name}» لا يطابق الحقول المطلوبة — أوقفت المزامنة، ولم أحاول {remaining} سجلًا آخر.")
                print(f"       {exc}")
                break
            if exc.status == 400 and "غير موجودة في" in str(exc):
                remaining = len(records) - index + 1
                counts["failed"] += remaining
                print(f"   [!] حقول «{type_name}» لا تطابق المخطط الحالي — أوقفت المزامنة، ولم أحاول {remaining} سجلًا آخر.")
                print(f"       {exc}")
                break
            if exc.status == 404 and "type not found" in str(exc).lower():
                remaining = len(records) - index + 1
                counts["failed"] += remaining
                print(f"   [!] النوع «{type_name}» غير مفعّل في هذا التطبيق (HTTP 404) — أوقفت المزامنة، "
                      f"ولم أحاول {remaining} سجلًا آخر. فعّل النوع في Settings → API ثم أعد التشغيل.")
                break
            counts["failed"] += 1
            print(f"   [{index}/{len(records)}] ✗ {exc}")
            continue
        bucket = status.split(" ")[0]
        counts[bucket if bucket in ("create", "update") else "unchanged"] += 1
        label = {"create": "أُنشئ", "update": "حُدِّث", "unchanged": "بلا تغيير"}[bucket if bucket in ("create", "update") else "unchanged"]
        print(f"   [{index}/{len(records)}] ✓ {label}: {payload.get(key)} {uid}".rstrip())

    print(
        f"\n[✓] النتيجة — جديد: {counts['create']} | محدَّث: {counts['update']} | "
        f"بلا تغيير: {counts['unchanged']} | فشل: {counts['failed']}"
    )
    return counts


# --------------------------------------------------------------------------- #
# واجهة الأوامر
# --------------------------------------------------------------------------- #


def build_client(args: argparse.Namespace) -> BubbleClient:
    return BubbleClient(
        app_url=args.app_url,
        token=args.token,
        config_file=Path(args.config_file),
        timeout=args.timeout,
        retries=args.retries,
    )


def cmd_check(client: BubbleClient, type_name: str) -> int:
    print(f"[i] الرابط الفعلي : {client.base}")
    print(f"[i] التوكن       : {mask(client.token)}")
    print(f"[i] نوع الاختبار : {type_name}")
    try:
        rows = client.list_things(type_name, limit=1)
    except BubbleError as exc:
        print(f"[✗] فشل الاتصال: {exc}")
        return 2
    print(f"[✓] الاتصال ناجح — عدد السجلات المقروءة: {len(rows)}")
    if rows:
        print(f"    مثال: {json.dumps({k: rows[0][k] for k in list(rows[0])[:4]}, ensure_ascii=False)}")
    return 0


def cmd_schema(client: BubbleClient, type_name: str) -> int:
    keys = client.field_keys(type_name)
    if not keys:
        print(f"[i] لا سجل واحد في «{type_name}» بعد — أضف سجلًا في Bubble ليُستنتج المخطط، أو استخدم أسماء حقول task نفسها.")
        return 0
    print(f"[i] حقول «{type_name}» الفعلية: {', '.join(keys)}")
    return 0


def cmd_list(client: BubbleClient, type_name: str, limit: int) -> int:
    rows = client.list_things(type_name, limit=limit)
    if not rows:
        print(f"[i] «{type_name}» فارغ.")
        return 0
    for row in rows:
        print(json.dumps({k: v for k, v in row.items() if k not in {"Created Date", "Modified Date", "Created By"}}, ensure_ascii=False))
    return 0


def cmd_test_task(client: BubbleClient) -> int:
    stamp = time.strftime("%Y-%m-%d %H:%M")
    name = f"اختبار الربط — {stamp}"
    print(f"[1/2] إنشاء مهمة: {name}")
    status, uid = client.upsert(
        TASK_TYPE,
        {"Task_Name": name, "Priority": "High", "Progress_Percentage": 85},
        key="Task_Name",
    )
    print(f"      {status} (المعرّف: {uid or '—'})")
    print("[2/2] تحديث النسبة إلى 100")
    status2, uid2 = client.upsert(
        TASK_TYPE,
        {"Task_Name": name, "Progress_Percentage": 100},
        key="Task_Name",
    )
    print(f"      {status2} (المعرّف: {uid2 or uid or '—'})")
    print("[✓] مسار task يعمل: إنشاء ثم تحديث على نفس السجل بنجاح.")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="رفع وتحديث بيانات القوالب العربية في Bubble Data API.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("command", choices=["check", "schema", "list", "test-task", "sync-templates", "sync-tasks"], help="الأمر المطلوب")
    parser.add_argument("--type", default=None, help=f"نوع البيانات (افتراضي: {TASK_TYPE} لـ check/list)")
    parser.add_argument("--app-url", default=None, help="رابط تطبيقك، مثل https://my-app.bubbleapps.io")
    parser.add_argument("--token", default=None, help="توكن بديل (يُفضّل الملف أو BUBBLE_TOKEN)")
    parser.add_argument("--config-file", default=str(DEFAULT_CONFIG_FILE), help="ملف يُقرأ منه التوكن والرابط")
    parser.add_argument("--json", default=None, help="ملف JSON لبيانات القوالب أو المهام")
    parser.add_argument("--limit", type=int, default=20, help="عدد السجلات في list")
    parser.add_argument("--dry-run", action="store_true", help="معاينة ما سيحدث دون كتابة")
    parser.add_argument("--timeout", type=float, default=20.0, help="مهلة الطلب بالثواني")
    parser.add_argument("--retries", type=int, default=3, help="عدد إعادات المحاولة عند تعذّر الاتصال")
    args = parser.parse_args(argv)

    try:
        client = build_client(args)
    except BubbleError as exc:
        print(f"[✗] إعداد غير مكتمل: {exc}")
        return 2

    try:
        if args.command == "check":
            return cmd_check(client, args.type or TASK_TYPE)
        if args.command == "schema":
            return cmd_schema(client, args.type or TASK_TYPE)
        if args.command == "list":
            return cmd_list(client, args.type or TASK_TYPE, args.limit)
        if args.command == "test-task":
            return cmd_test_task(client)
        if args.command == "sync-templates":
            records = load_records(args.json, TEMPLATE_TYPE)
            counts = sync_records(client, TEMPLATE_TYPE, records, TEMPLATE_FIELDS, key="Title", dry_run=args.dry_run)
            return 1 if counts["failed"] else 0
        if args.command == "sync-tasks":
            records = load_records(args.json, TASK_TYPE)
            counts = sync_records(client, TASK_TYPE, records, TASK_FIELDS, key="Task_Name", dry_run=args.dry_run)
            return 1 if counts["failed"] else 0
    except BubbleError as exc:
        print(f"[✗] {exc}")
        return 2
    except KeyboardInterrupt:
        print("\n[!] أُوقف يدويًا.")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
