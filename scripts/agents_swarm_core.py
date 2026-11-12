#!/usr/bin/env python3
"""نظام الطيار الآلي الكامل — Arab Templates Autopilot (AR/EN).

Full autopilot for the Arab Templates platform: it hunts trending template ideas
from the open web, localizes each idea into Arabic **and** English, publishes the
bilingual record into the Bubble ``template`` table of ``at-ai-lab``, watches the
Bubble connection with retries/self-healing, and writes a performance summary to
``autopilot_report.json``.

الوكلاء الثلاثة:

1. ``ScraperLocalizer`` — وكيل الصيد والتعريب:
   يجلب أفكار القوالب الرائجة (GitHub / Hacker News / بذور محلية)، يصوغ لكل فكرة
   عنوانًا ووصفًا بالعربية والإنجليزية، ثم يرفعها إلى جدول Template. عند غياب
   الشبكة تُحفظ الأفكار في طابور محلي وتُرفع تلقائيًا في الدورة التالية.
2. ``HealthMonitor`` — وكيل المراقبة والتعافي الذاتي:
   فحص دوري لاتصال Bubble بمهلة وإعادة محاولة بتراجع أسّي، مع إحصاء الزمن
   والاستجابات والتعافيات، وتلخيص كل ذلك في ``autopilot_report.json``.
3. ``Scheduler`` — وضع التشغيل المستمر:
   حلقة بفاصل زمني، أو مهمة مجدولة في Windows Task Scheduler (``--install``)،
   مع قفل يمنع التداخل وتقرير يُحدَّث في كل دورة.

    python agents_swarm_core.py --once                  # دورة طيار كاملة
    python agents_swarm_core.py --loop --interval 60    # تشغيل مستمر
    python agents_swarm_core.py --check                 # فحص اتصال فقط
    python agents_swarm_core.py --install --interval 60 # جدولة كل ساعة
    python agents_swarm_core.py --status                # حالة المهمة والتقرير

التوكن يُقرأ من ``scripts/.env`` أو البيئة ولا يُطبع أبدًا.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Sequence

import requests

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = ROOT / "data"
LOGS = ROOT / "logs"
TEMPLATES_FILE = DATA / "templates_ar.json"
IDEA_CATALOG = DATA / "templates_bilingual.json"
IDEA_QUEUE = DATA / "autopilot_queue.json"
REPORT_FILE = ROOT / "autopilot_report.json"
LOCK_FILE = LOGS / ".autopilot.lock"
TASK_NAME = r"ArabTemplates\Autopilot"
LOCK_TTL = timedelta(hours=6)

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
    raise SystemExit(f"ضع bubble_data_sync.py بجانب هذا الملف — {exc}") from exc

BUBBLE_API_URL = os.environ.get("BUBBLE_APP_URL", "https://at-ai-lab.bubbleapps.io/version-test")
BUBBLE_TOKEN = os.environ.get("BUBBLE_TOKEN", "")

GITHUB_SEARCH = "https://api.github.com/search/repositories"
HN_SEARCH = "https://hn.algolia.com/api/v1/search"
USER_AGENT = "arab-templates-autopilot/2.0"
DEFAULT_SOURCES = "github,hn,local"
MAX_IDEAS_PER_CYCLE = 25

# --------------------------------------------------------------------------- #
# ثنائية اللغة: الرسائل
# --------------------------------------------------------------------------- #


class Speaker:
    """طابعة ثنائية اللغة: عربي، إنجليزي، أو الاثنان معًا."""

    def __init__(self, lang: str = "both", log_file: str | None = None, quiet: bool = False):
        self.lang = lang if lang in ("ar", "en", "both") else "both"
        self.quiet = quiet
        self.handle = open(log_file, "a", encoding="utf-8") if log_file else None

    def _emit(self, text: str) -> None:
        if self.quiet:
            return
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{stamp} {text}"
        print(line, flush=True)
        if self.handle:
            self.handle.write(line + "\n")
            self.handle.flush()

    def say(self, ar: str, en: str = "", *, tag: str = "") -> None:
        prefix = f"[{tag}] " if tag else ""
        if self.lang == "ar":
            self._emit(prefix + ar)
        elif self.lang == "en":
            self._emit(prefix + (en or ar))
        else:
            self._emit(prefix + ar)
            self._emit("            " + (en or ar))

    def raw(self, text: str) -> None:
        self._emit(text)

    def close(self) -> None:
        if self.handle:
            self.handle.close()


def bilingual(text_ar: str, text_en: str) -> tuple[str, str]:
    return text_ar, text_en


# --------------------------------------------------------------------------- #
# المعرفة اللغوية: التصنيفات والمصطلحات
# --------------------------------------------------------------------------- #

# (مفتاح، اسم عربي، اسم إنجليزي، سعر، ميزات عربية، ميزات إنجليزية، سلَغ الرابط)
CATEGORIES: tuple[tuple[str, str, str, int, tuple[str, ...], tuple[str, ...], str], ...] = (
    ("dashboard", "لوحة تحكم", "Admin Dashboard", 449,
     ("مؤشرات فورية", "إدارة الأدوار والصلاحيات", "تقارير قابلة للتصدير"), ("live KPIs", "role permissions", "exportable reports"), "admin-dashboard"),
    ("crm", "إدارة العملاء", "CRM", 549,
     ("خط أنابيب المبيعات", "سجل المكالمات والملاحظات", "متابعة الصفقات"), ("sales pipeline", "call notes", "deal tracking"), "crm"),
    ("invoice", "الفوترة والمحاسبة", "Invoicing", 399,
     ("فواتير ضريبية", "مدفوعات ومتابعة تحصيل", "تقارير مالية"), ("tax invoices", "payments tracking", "financial reports"), "invoicing"),
    ("ecommerce", "متجر إلكتروني", "E-commerce", 649,
     ("سلة وشراء سريع", "إدارة المخزون", "بوابات دفع خليجية"), ("cart and checkout", "inventory", "Gulf payment gateways"), "ecommerce"),
    ("booking", "الحجوزات والمواعيد", "Booking", 499,
     ("تقويم المواعيد", "تأكيد تلقائي", "دفع عربون"), ("appointment calendar", "auto confirmation", "deposit payment"), "booking"),
    ("portfolio", "ملف الأعمال", "Portfolio", 249,
     ("معرض أعمال", "صفحة خدمات", "نموذج تواصل"), ("work gallery", "services page", "contact form"), "portfolio"),
    ("hr", "الموارد البشرية", "HR", 599,
     ("ملفات الموظفين", "الإجازات والرواتب", "تقييم الأداء"), ("employee records", "leave and payroll", "performance reviews"), "hr"),
    ("inventory", "المخزون", "Inventory", 549,
     ("حركة المخزون", "تنبيهات النفاد", "باركود"), ("stock movements", "low-stock alerts", "barcode"), "inventory"),
    ("analytics", "التحليلات", "Analytics", 699,
     ("لوحات بيانات", "مقارنة فترات", "تصدير Excel"), ("data dashboards", "period comparison", "Excel export"), "analytics"),
    ("learning", "التعليم الإلكتروني", "E-learning", 599,
     ("دورات ودروس", "اختبارات", "شهادات"), ("courses and lessons", "quizzes", "certificates"), "elearning"),
    ("clinic", "العيادات", "Clinic", 599,
     ("ملفات المرضى", "جدولة الزيارات", "وصفات طبية"), ("patient records", "visit scheduling", "prescriptions"), "clinic"),
    ("restaurant", "المطاعم", "Restaurant", 499,
     ("قائمة رقمية", "طلبات واتساب", "إدارة الطاولات"), ("digital menu", "WhatsApp orders", "table management"), "restaurant"),
    ("realestate", "العقارات", "Real Estate", 649,
     ("عرض العقارات", "طلبات معاينة", "مقارنة أسعار"), ("property listings", "viewing requests", "price comparison"), "real-estate"),
    ("logistics", "الخدمات اللوجستية", "Logistics", 599,
     ("تتبع الشحنات", "إدارة السائقين", "تقارير التسليم"), ("shipment tracking", "driver management", "delivery reports"), "logistics"),
    ("tax", "الضرائب والامتثال", "Tax Compliance", 749,
     ("فواتير إلكترونية", "إقرار ضريبي", "سجل مشتريات"), ("e-invoices", "tax return", "purchase ledger"), "tax"),
    ("chat", "الدردشة والدعم", "Support Chat", 449,
     ("صندوق وارد موحّد", "ردود جاهزة", "تقييم الخدمة"), ("unified inbox", "canned replies", "CSAT"), "support-chat"),
    ("project", "إدارة المشاريع", "Project Management", 499,
     ("مهام ومسؤوليات", "جدول زمني", "تقارير تقدم"), ("tasks and owners", "timeline", "progress reports"), "project-management"),
    ("marketing", "التسويق", "Marketing", 399,
     ("حملات بريدية", "صفحات هبوط", "تحليل التحويل"), ("email campaigns", "landing pages", "conversion analytics"), "marketing"),
    ("school", "المدارس", "School", 599,
     ("سجلات الطلاب", "الجدول الدراسي", "تواصل الأهل"), ("student records", "timetables", "parent messaging"), "school"),
    ("gym", "الأندية الرياضية", "Gym", 399,
     ("عضويات", "حصص وحضور", "اشتراكات"), ("memberships", "classes and attendance", "subscriptions"), "gym"),
)

# مصطلحات إنجليزية → عربية تُستخدم في التعريب والعنونة.
GLOSSARY: dict[str, str] = {
    "dashboard": "لوحة تحكم", "admin": "إدارة", "crm": "إدارة العملاء",
    "invoice": "فواتير", "invoicing": "فوترة", "billing": "فواتير",
    "ecommerce": "متجر إلكتروني", "shop": "متجر", "store": "متجر", "cart": "سلة",
    "booking": "حجوزات", "appointment": "مواعيد", "scheduling": "جدولة",
    "portfolio": "ملف أعمال", "landing": "صفحة هبوط", "page": "صفحة",
    "hr": "موارد بشرية", "payroll": "رواتب", "employee": "موظفين",
    "inventory": "مخزون", "stock": "مخزون", "warehouse": "مستودعات",
    "analytics": "تحليلات", "chart": "رسوم بيانية", "report": "تقارير",
    "learning": "تعليم", "course": "دورات", "lms": "تعليم إلكتروني", "school": "مدارس",
    "clinic": "عيادات", "patient": "مرضى", "medical": "طبي", "health": "صحي",
    "restaurant": "مطاعم", "menu": "قائمة", "food": "طعام", "cafe": "مقاهي",
    "real": "عقارات", "estate": "عقارات", "property": "عقارات",
    "logistics": "لوجستيات", "delivery": "توصيل", "shipping": "شحن", "fleet": "أسطول",
    "tax": "ضرائب", "vat": "ضريبة القيمة المضافة", "compliance": "امتثال",
    "chat": "دردشة", "support": "دعم", "ticket": "تذاكر", "helpdesk": "مكتب مساعدة",
    "project": "مشاريع", "task": "مهام", "kanban": "كانبان", "team": "فريق",
    "marketing": "تسويق", "email": "بريد", "campaign": "حملات", "seo": "سيو",
    "gym": "نادٍ رياضي", "fitness": "لياقة", "membership": "عضويات",
    "ai": "ذكاء اصطناعي", "template": "قالب", "saas": "اشتراك", "app": "تطبيق",
    "arabic": "عربي", "rtl": "من اليمين لليسار", "bootstrap": "واجهة جاهزة",
    "nextjs": "Next.js", "react": "React", "python": "بايثون",
}

# كلمات تدل على فكرة قالب تجاري قابلة للبيع — وأخرى تُستبعد كضجيج بحث.
IDEA_KEYWORDS: tuple[str, ...] = (
    "dashboard", "crm", "erp", "invoice", "invoic", "ecommerce", "e-commerce", "shop", "store",
    "booking", "appointment", "portfolio", "landing", "admin", "analytics", "inventory", "payroll",
    "hr", "clinic", "patient", "restaurant", "menu", "school", "lms", "course", "real estate",
    "property", "logistic", "shipping", "delivery", "tax", "vat", "chat", "support", "helpdesk",
    "project", "kanban", "task", "marketing", "email", "gym", "fitness", "hotel", "pos", "cms", "saas",
)
NOISE_WORDS: tuple[str, ...] = (
    "gitignore", "awesome", "dotfiles", "ppt", "powerpoint", "latex", "resume", "curriculum",
    "leetcode", "interview", "algorithm", "wallpaper", "icon pack", "font", "logo", "cheat sheet",
    "design resources", "boilerplate list", "machine learning paper", "dataset", "kernel", "ebook",
)
# كلمات عامة لا تصلح للتمييز في العنوان العربي.
GENERIC_AR: frozenset[str] = frozenset({"قالب", "تطبيق", "صفحة", "واجهة جاهزة", "من اليمين لليسار"})

SEED_IDEAS: tuple[dict[str, Any], ...] = (
    {"source": "local", "external_id": "seed-crm-gulf", "raw_title": "Gulf CRM for real estate agents",
     "raw_summary": "CRM with pipeline, WhatsApp follow-ups and Arabic RTL interface", "url": "", "category": "crm"},
    {"source": "local", "external_id": "seed-clinic-booking", "raw_title": "Clinic appointment booking system",
     "raw_summary": "Booking, patient records and reminder messages for small clinics", "url": "", "category": "clinic"},
    {"source": "local", "external_id": "seed-tax-invoicing", "raw_title": "VAT e-invoicing with QR codes",
     "raw_summary": "Tax invoices, purchase ledger and quarterly VAT return", "url": "", "category": "tax"},
    {"source": "local", "external_id": "seed-school-portal", "raw_title": "School management portal",
     "raw_summary": "Student records, timetables and parent messaging", "url": "", "category": "school"},
    {"source": "local", "external_id": "seed-restaurant-menu", "raw_title": "Restaurant digital menu and orders",
     "raw_summary": "Digital menu, WhatsApp orders and table management", "url": "", "category": "restaurant"},
    {"source": "local", "external_id": "seed-logistics-fleet", "raw_title": "Logistics fleet tracking dashboard",
     "raw_summary": "Shipment tracking, driver management and delivery reports", "url": "", "category": "logistics"},
)


def category_by_key(key: str) -> tuple[str, str, str, int, tuple[str, ...], tuple[str, ...], str]:
    for row in CATEGORIES:
        if row[0] == key:
            return row
    return CATEGORIES[0]


def detect_category(text: str) -> str:
    """يستنتج التصنيف من نص الفكرة بمطابقة المصطلحات (إنجليزي أو عربي)."""
    low = (text or "").lower()
    best, score = "dashboard", 0
    for row in CATEGORIES:
        key, ar_name = row[0], row[1]
        hits = low.count(key) * 2 + low.count(ar_name)
        if hits > score:
            best, score = key, hits
    if score == 0:
        for en, ar in GLOSSARY.items():
            if en in low:
                for row in CATEGORIES:
                    if row[0] in en or en in row[0]:
                        return row[0]
    return best


# --------------------------------------------------------------------------- #
# مساعدات الملفات
# --------------------------------------------------------------------------- #


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return default


def write_json(path: Path, payload: Any) -> None:
    """كتابة ذرّية: ملف مؤقت ثم استبدال — لا يبقى تقرير ناقص أبدًا."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, path)


def slugify(text: str) -> str:
    clean = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return clean[:48] or "template"


def normalize_title(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\u0600-\u06FF ]+", " ", (text or "").lower())).strip()


# --------------------------------------------------------------------------- #
# الوكيل الأول: الصيد والتعريب
# --------------------------------------------------------------------------- #


class ScraperLocalizer:
    """يجلب الأفكار العالمية، يعرّبها ويترجمها، ثم ينشرها في جدول template."""

    def __init__(self, log: Speaker, *, offline: bool = False, timeout: float = 12.0):
        self.log = log
        self.offline = offline
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})

    # -- الصيد ------------------------------------------------------------- #

    def fetch(self, sources: Sequence[str], limit: int) -> list[dict[str, Any]]:
        ideas: list[dict[str, Any]] = []
        for source in sources:
            handler = {"github": self._from_github, "hn": self._from_hn, "local": self._from_local}.get(source)
            if handler is None:
                self.log.say(f"مصدر غير معروف تُجوهل: {source}", f"unknown source skipped: {source}", tag="🌐 Scraper")
                continue
            try:
                found = handler(limit)
            except (requests.RequestException, ValueError, KeyError) as exc:
                self.log.say(f"تعذّر الجلب من {source}: {type(exc).__name__}",
                             f"fetch failed from {source}: {type(exc).__name__}", tag="⚠️ Scraper")
                continue
            self.log.say(f"{source}: {len(found)} فكرة", f"{source}: {len(found)} ideas", tag="🌐 Scraper")
            ideas.extend(found)
        return self._dedupe(ideas)[: max(1, limit)]

    def _get(self, url: str, params: dict[str, Any] | None = None) -> Any:
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def is_relevant(title: str, summary: str) -> bool:
        """هل الفكرة قالب تجاري فعلًا؟ يمنع الضجيج (قوائم، سير ذاتية، أدوات شخصية)."""
        text = f"{title} {summary}".lower()
        if any(noise in text for noise in NOISE_WORDS):
            return False
        return any(keyword in text for keyword in IDEA_KEYWORDS)

    def _from_github(self, limit: int) -> list[dict[str, Any]]:
        if self.offline:
            raise requests.RequestException("offline mode")
        queries = (
            "dashboard template in:name,description stars:>100",
            "crm in:name,description stars:>150",
            "ecommerce booking template in:name,description stars:>80",
        )
        rows: list[dict[str, Any]] = []
        for query in queries:
            if len(rows) >= limit * 3:
                break
            payload = self._get(GITHUB_SEARCH, {
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": min(20, max(5, limit * 2)),
            })
            for item in payload.get("items") or []:
                title = str(item.get("name") or "").replace("-", " ").replace("_", " ").strip()
                summary = str(item.get("description") or "").strip()
                if len(summary) < 20 or not self.is_relevant(title, summary):
                    continue
                rows.append({
                    "source": "github",
                    "external_id": f"gh-{item.get('id')}",
                    "raw_title": title,
                    "raw_summary": summary,
                    "url": item.get("html_url") or "",
                    "stars": int(item.get("stargazers_count") or 0),
                    "category": detect_category(f"{title} {summary}"),
                })
        return rows

    def _from_hn(self, limit: int) -> list[dict[str, Any]]:
        if self.offline:
            raise requests.RequestException("offline mode")
        payload = self._get(HN_SEARCH, {
            "query": "saas template dashboard",
            "tags": "story",
            "hitsPerPage": min(30, max(3, limit * 2)),
        })
        rows = []
        for hit in (payload.get("hits") or [])[: limit * 3]:
            title = str(hit.get("title") or "").strip()
            if not title:
                continue
            summary = str(hit.get("story_text") or hit.get("url") or "").strip()[:220] or title
            if int(hit.get("points") or 0) < 10 or not self.is_relevant(title, summary):
                continue
            rows.append({
                "source": "hn",
                "external_id": f"hn-{hit.get('objectID')}",
                "raw_title": title,
                "raw_summary": summary,
                "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                "stars": int(hit.get("points") or 0),
                "category": detect_category(f"{title} {summary}"),
            })
        return rows

    def _from_local(self, limit: int) -> list[dict[str, Any]]:
        seeds = [dict(seed) for seed in SEED_IDEAS]
        return seeds[: max(1, limit)]

    @staticmethod
    def _dedupe(ideas: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        out: list[dict[str, Any]] = []
        for idea in ideas:
            key = idea.get("external_id") or normalize_title(idea.get("raw_title", ""))
            if key in seen:
                continue
            seen.add(key)
            out.append(idea)
        return out

    # -- التعريب والترجمة -------------------------------------------------- #

    def localize(self, idea: dict[str, Any]) -> dict[str, Any]:
        key = idea.get("category") or detect_category(f"{idea.get('raw_title','')} {idea.get('raw_summary','')}")
        _, cat_ar, cat_en, price, features_ar, features_en, slug = category_by_key(key)
        raw = f"{idea.get('raw_title','')} {idea.get('raw_summary','')}".lower()
        matched = [ar for en, ar in GLOSSARY.items() if en in raw]
        # لا نكرر اسم التصنيف نفسه في العنوان، ونفضّل ميزة مميزة للتنويع.
        keyword_ar = next((k for k in matched if k != cat_ar and k not in GENERIC_AR and len(k) > 2), None)
        if keyword_ar is None:
            keyword_ar = next((k for k in features_ar if k != cat_ar), "واجهة جاهزة")
        source_label = {"github": "GitHub", "hn": "Hacker News", "local": "كتالوج محلي"}.get(idea.get("source", ""), "الإنترنت")

        title_ar = f"قالب {cat_ar} — {keyword_ar}".strip()
        title_en = self._english_title(idea.get("raw_title") or "", cat_en)
        desc_ar = (f"قالب {cat_ar} بواجهة عربية RTL يشمل {'، '.join(features_ar)}. "
                   f"مستوحى من فكرة رائجة على {source_label} وجاهز للتخصيص والنشر.")
        desc_en = (f"{cat_en} template with an Arabic RTL interface including {', '.join(features_en)}. "
                   f"Inspired by a trending idea on {source_label}, ready to customize and launch.")
        idea_id = idea.get("external_id") or f"idea-{uuid.uuid4().hex[:8]}"
        return {
            "idea_id": idea_id,
            "source": idea.get("source"),
            "source_url": idea.get("url") or "",
            "raw_title": idea.get("raw_title") or "",
            "stars": int(idea.get("stars") or 0),
            "category": cat_ar,
            "Category": cat_ar,
            "category_en": cat_en,
            "Category_EN": cat_en,
            "category_key": key,
            "Title": title_ar,
            "Title_EN": title_en,
            "description": desc_ar,
            "Description_EN": desc_en,
            "price": price,
            "preview_url": (f"https://arab-templates.example.com/previews/"
                            f"{slugify(str(idea.get('raw_title') or '')) or slug}"),
            "localized_at": now_iso(),
        }

    @staticmethod
    def _brand(record: dict[str, Any]) -> str:
        """اسم مختصر من الفكرة الأصلية لتمييز العنوان العربي عند التشابه."""
        raw = str(record.get("raw_title") or "").strip()
        ascii_words = [w for w in re.split(r"\s+", raw) if re.fullmatch(r"[A-Za-z0-9.+\-]+", w or "")]
        brand = " ".join(ascii_words[:3])[:28].strip()
        return brand if len(brand) > 2 else ""

    @staticmethod
    def _english_title(raw_title: str, cat_en: str) -> str:
        """يحافظ على حالة الأحرف الأصلية (CRM، VAT، QR) ويضيف وصفًا إنجليزيًا."""
        clean = re.sub(r"\s+", " ", raw_title).strip()
        clean = re.sub(r"[^\w\s\-+.&/]", "", clean)[:70].strip()
        if not clean:
            return f"Arabic {cat_en} Template"
        if "template" in clean.lower():
            return clean
        return f"{clean} — Arabic {cat_en} Template"

    # -- النشر ------------------------------------------------------------- #

    def bubble_payload(self, record: dict[str, Any], allowed: Sequence[str] | None) -> dict[str, Any]:
        """يُبقي فقط الحقول الموجودة فعلًا في جدول template."""
        core = {"Title", "Category", "description", "price", "preview_url"}
        keys = set(allowed or ()) or core
        payload: dict[str, Any] = {}
        for field in ("Title", "Category", "description", "price", "preview_url",
                      "Title_EN", "Description_EN", "Category_EN", "source_url", "idea_id"):
            if field in keys and record.get(field) not in (None, ""):
                payload[field] = record[field]
        for field in core:  # الحقول الأساسية دائمًا موجودة
            if field not in payload and record.get(field) not in (None, ""):
                if field in (keys or core):
                    payload[field] = record[field]
            elif field == "description" and record.get("description") is not None and field in keys:
                payload[field] = record["description"]
        if "Category" not in payload and "Category" in keys:
            payload["Category"] = record.get("category")
        return payload


# --------------------------------------------------------------------------- #
# الوكيل الثاني: المراقبة والتعافي الذاتي
# --------------------------------------------------------------------------- #


class HealthMonitor:
    """يفحص اتصال Bubble، يعيد المحاولة، ويحصي الأداء والتعافيات."""

    def __init__(self, probe: Callable[[], Any], log: Speaker, *, retries: int = 2,
                 backoff: float = 1.8, max_backoff: float = 30.0):
        self.probe = probe
        self.log = log
        self.retries = max(0, retries)
        self.backoff = max(1.0, backoff)
        self.max_backoff = max_backoff
        self.checks = 0
        self.failures = 0
        self.recoveries = 0
        self.consecutive_failures = 0
        self.latencies: list[float] = []
        self.last_ok_at: str | None = None
        self.last_error: str | None = None
        self.last_backoff = 0.0

    def check(self, *, label: str = "Bubble") -> bool:
        self.checks += 1
        attempts = self.retries + 1
        for attempt in range(1, attempts + 1):
            started = time.perf_counter()
            try:
                self.probe()
            except Exception as exc:  # أي عطل يُعاد فحصه قبل إعلان الفشل
                waited = min(self.max_backoff, self.backoff ** attempt)
                self.last_backoff = round(waited, 2)
                self.last_error = f"{type(exc).__name__}: {str(exc).splitlines()[0][:180]}"
                fast_fail = "offline mode" in str(exc).lower()
                self.log.say(
                    f"فحص {label} فشل ({attempt}/{attempts}) — إعادة بعد {waited:.1f} ث: {self.last_error}",
                    f"{label} probe failed ({attempt}/{attempts}) — retrying in {waited:.1f}s: {self.last_error}",
                    tag="🩺 Monitor",
                )
                if attempt < attempts and not fast_fail:
                    time.sleep(min(waited, 5.0))
                if fast_fail:
                    break
                continue
            latency = round((time.perf_counter() - started) * 1000, 1)
            self.latencies.append(latency)
            self.latencies = self.latencies[-50:]
            if self.consecutive_failures > 0:
                self.recoveries += 1
            self.consecutive_failures = 0
            self.last_ok_at = now_iso()
            self.last_error = None
            self.last_backoff = 0.0
            self.log.say(f"{label} متصل — {latency:.0f} ms", f"{label} reachable — {latency:.0f} ms", tag="🩺 Monitor")
            return True
        self.failures += 1
        self.consecutive_failures += 1
        self.log.say(f"{label} غير متاح — سيُعاد تلقائيًا في الدورة القادمة",
                     f"{label} unreachable — will self-heal next cycle", tag="🚨 Monitor")
        return False

    def snapshot(self) -> dict[str, Any]:
        avg = round(sum(self.latencies) / len(self.latencies), 1) if self.latencies else None
        return {
            "checks": self.checks,
            "failures": self.failures,
            "recoveries": self.recoveries,
            "consecutive_failures": self.consecutive_failures,
            "avg_latency_ms": avg,
            "last_latency_ms": self.latencies[-1] if self.latencies else None,
            "last_ok_at": self.last_ok_at,
            "last_error": self.last_error,
            "next_backoff_seconds": self.last_backoff,
            "status": "online" if self.consecutive_failures == 0 else "offline",
        }


# --------------------------------------------------------------------------- #
# سرب الوكلاء (متوافق مع الاستدعاءات القديمة)
# --------------------------------------------------------------------------- #


class AIAgentSwarm:
    """نواة السرب: عميل واحد، ووكلاء الصيد والنشر والمراقبة."""

    def __init__(self, app_url: str = BUBBLE_API_URL, token: str = BUBBLE_TOKEN,
                 verbose: bool = True, *, lang: str = "both", offline: bool = False,
                 dry_run: bool = False, log: Speaker | None = None):
        self.app_url = app_url
        self.token = token
        self.verbose = verbose
        self.offline = offline
        self.dry_run = dry_run
        self.log = log or Speaker(lang)
        self._client: BubbleClient | None = None
        self._allowed: list[str] | None = None
        self.localizer = ScraperLocalizer(self.log, offline=offline)
        self.monitor = HealthMonitor(self._probe, self.log)

    # -- البنية ------------------------------------------------------------ #

    @property
    def client(self) -> BubbleClient:
        if self._client is None:
            self._client = BubbleClient(app_url=self.app_url, token=self.token, verbose=False)
            self.log.say(f"رابط Bubble: {self._client.base}", f"Bubble endpoint: {self._client.base}", tag="🔗 Bubble")
        return self._client

    def _probe(self) -> None:
        if self.offline:
            raise ConnectionError("offline mode")
        self.client.list_things(TEMPLATE_TYPE, limit=1)

    def allowed_fields(self) -> list[str] | None:
        """حقول جدول template الفعلية — تُحدد مرة واحدة وتُستخدم لتصفية الحمولة."""
        if self._allowed is not None:
            return self._allowed
        if self.offline or self.dry_run:
            return None
        try:
            self._allowed = self.client.field_keys(TEMPLATE_TYPE)
        except BubbleError:
            self._allowed = None
        return self._allowed

    # -- الوكلاء القدامى (توافق خلفي) --------------------------------------- #

    def data_fetcher_agent(self) -> str:
        """فكرة حيّة واحدة (يحافظ على السلوك القديم عند --with-task)."""
        ideas = self.localizer.fetch(("github", "local"), 1)
        return ideas[0].get("raw_title", "") if ideas else "تحديث دوري للقوالب"

    def cloud_connector_agent(self, task_name: str, priority: str = "High", progress: int = 0) -> bool:
        if self.dry_run:
            self.log.say(f"(تجريبي) كانت ستُكتب مهمة: {task_name[:50]}",
                         f"(dry-run) would write task: {task_name[:50]}", tag="🚀 API")
            return True
        try:
            status, uid = self.client.upsert(
                "task",
                {"Task_Name": task_name, "Priority": priority, "Progress_Percentage": progress},
                key="Task_Name",
            )
        except BubbleError as exc:
            self.log.say(f"فشل الكتابة في task: {exc}", f"task write failed: {exc}", tag="❌ API")
            return False
        self.log.say(f"task: {status} — {task_name[:50]}", f"task: {status} — {task_name[:50]}", tag="🎉 API")
        return True

    def cloud_connector_templates(self, records=None, dry_run: bool = False, json_file: str | None = None) -> dict[str, int]:
        data = records
        if data is None:
            data = load_records(json_file or str(TEMPLATES_FILE), TEMPLATE_TYPE)
        try:
            return sync_records(self.client, TEMPLATE_TYPE, data, TEMPLATE_FIELDS, key="Title", dry_run=dry_run)
        except BubbleError as exc:
            self.log.say(f"مزامنة القوالب فشلت: {exc}", f"template sync failed: {exc}", tag="❌ API")
            return {"create": 0, "update": 0, "unchanged": 0, "failed": len(data)}

    # -- وكيل الصيد والتعريب: دورة كاملة ------------------------------------ #

    def publish_ideas(self, ideas: list[dict[str, Any]], limit: int) -> dict[str, Any]:
        catalog = read_json(IDEA_CATALOG, [])
        queue = read_json(IDEA_QUEUE, [])
        known = {normalize_title(row.get("Title", "")) for row in catalog if isinstance(row, dict)}
        known |= {normalize_title(row.get("raw_title", "")) for row in catalog if isinstance(row, dict)}
        # الطابور أيضًا يمنع تكرار الأفكار بين الدورات التجريبية.
        known |= {normalize_title(row.get("Title", "")) for row in queue if isinstance(row, dict)}
        known |= {normalize_title(row.get("raw_title", "")) for row in queue if isinstance(row, dict)}
        result = {"discovered": len(ideas), "published": 0, "queued": 0, "skipped": 0, "failed": 0, "titles": []}

        for idea in ideas[:limit]:
            record = self.localizer.localize(idea)
            fingerprint = normalize_title(record["Title"])
            raw_fp = normalize_title(record.get("raw_title", ""))
            if fingerprint in known and raw_fp not in known:
                # عنوان عربي متشابه لفكرة مختلفة: نُميّزها باسم المصدر بدل إسقاطها.
                brand = self.localizer._brand(record)
                if brand:
                    record["Title"] = f"قالب {record['category']} — {brand}"
                    fingerprint = normalize_title(record["Title"])
            if fingerprint in known or raw_fp in known:
                result["skipped"] += 1
                self.log.say(f"مكرر — تخطّي: {record['Title']}", f"duplicate — skipped: {record['Title']}", tag="↷ Ideas")
                continue

            if self.dry_run or self.offline:
                if not any(normalize_title(row.get("Title", "")) == fingerprint for row in queue if isinstance(row, dict)):
                    queue.append(record)
                result["queued"] += 1
                self.log.say(f"(لم يُرفع) {record['Title']} / {record['Title_EN']}",
                             f"(not uploaded) {record['Title']} / {record['Title_EN']}", tag="🧪 Ideas")
                known.add(fingerprint)
                continue

            payload = self.localizer.bubble_payload(record, self.allowed_fields())
            try:
                status, uid = self.client.upsert(TEMPLATE_TYPE, payload, key="Title")
            except BubbleError as exc:
                queue.append(record)
                result["queued"] += 1
                self.log.say(f"تعذّر النشر — أُضيفت للطابور: {record['Title']} ({str(exc)[:90]})",
                             f"publish failed — queued: {record['Title']} ({str(exc)[:90]})", tag="⚠️ Ideas")
                continue
            catalog.append(record)
            known.add(fingerprint)
            known.add(raw_fp)
            result["published"] += 1
            result["titles"].append(record["Title"])
            self.log.say(f"نُشر ({status}): {record['Title']} / {record['Title_EN']}",
                         f"published ({status}): {record['Title']} / {record['Title_EN']}", tag="📤 Ideas")

        write_json(IDEA_CATALOG, catalog[-500:])
        write_json(IDEA_QUEUE, queue[-200:])
        return result

    def flush_queue(self) -> dict[str, Any]:
        """يرفع الأفكار التي تعذّر نشرها سابقًا (تعافٍ بعد انقطاع الشبكة)."""
        queue = read_json(IDEA_QUEUE, [])
        if not queue or self.offline or self.dry_run:
            return {"flushed": 0, "remaining": len(queue)}
        remaining: list[dict[str, Any]] = []
        flushed = 0
        for record in queue:
            try:
                self.client.upsert(TEMPLATE_TYPE, self.localizer.bubble_payload(record, self.allowed_fields()), key="Title")
                flushed += 1
            except BubbleError:
                remaining.append(record)
        write_json(IDEA_QUEUE, remaining)
        if flushed:
            self.log.say(f"تعافٍ: رُفع {flushed} فكرة من الطابور", f"self-heal: flushed {flushed} queued ideas", tag="♻️ Recovery")
        return {"flushed": flushed, "remaining": len(remaining)}


# --------------------------------------------------------------------------- #
# التقرير
# --------------------------------------------------------------------------- #


class AutopilotReport:
    """تجميع الأداء وحفظه في autopilot_report.json."""

    def __init__(self, path: Path, *, mode: str, lang: str, dry_run: bool, offline: bool, interval: float):
        self.path = path
        previous = read_json(path, {})
        self.data: dict[str, Any] = {
            "version": "2.0",
            "product": "Arab Templates — Full Autopilot",
            "generated_at": now_iso(),
            "run": {
                "started_at": now_iso(),
                "mode": mode,
                "language": lang,
                "dry_run": dry_run,
                "offline": offline,
                "interval_minutes": interval,
                "cycles": 0,
                "pid": os.getpid(),
            },
            "totals": {
                "ideas_discovered": 0, "ideas_published": 0, "ideas_queued": 0,
                "ideas_skipped": 0, "ideas_flushed": 0,
                "template_create": 0, "template_update": 0,
                "template_unchanged": 0, "template_failed": 0,
                "tasks_written": 0,
            },
            "last_cycle": {},
            "health": {},
            "performance": {"cycles_completed": 0, "avg_cycle_seconds": None, "uptime_seconds": 0},
            "history": (previous.get("history") or [])[-20:] if isinstance(previous, dict) else [],
            "errors": [],
        }
        self._cycle_seconds: list[float] = []
        self._started = time.time()

    def add(self, key: str, value: int) -> None:
        self.data["totals"][key] += int(value)

    def cycle(self, number: int, summary: dict[str, Any]) -> None:
        self.data["run"]["cycles"] = number
        self.data["performance"]["cycles_completed"] = number
        seconds = float(summary.get("seconds") or 0)
        self._cycle_seconds.append(seconds)
        self.data["performance"]["avg_cycle_seconds"] = round(
            sum(self._cycle_seconds) / len(self._cycle_seconds), 2)
        self.data["performance"]["uptime_seconds"] = round(time.time() - self._started, 1)
        self.data["last_cycle"] = {"number": number, **summary}
        self.data["history"] = (self.data["history"] + [{
            "cycle": number, "at": summary.get("finished_at"),
            "seconds": seconds, "published": summary.get("ideas", {}).get("published", 0),
            "queued": summary.get("ideas", {}).get("queued", 0),
            "online": summary.get("online"),
        }])[-20:]

    def error(self, message: str) -> None:
        self.data["errors"] = (self.data["errors"] + [{"at": now_iso(), "message": message[:300]}])[-20:]

    def save(self, health: dict[str, Any] | None = None) -> None:
        self.data["generated_at"] = now_iso()
        if health is not None:
            self.data["health"] = health
        self.data["performance"]["uptime_seconds"] = round(time.time() - self._started, 1)
        write_json(self.path, self.data)


# --------------------------------------------------------------------------- #
# جدولة Windows Task Scheduler
# --------------------------------------------------------------------------- #


def task_command(interval_minutes: float) -> str:
    """أمر المهمة المجدولة: ملف .bat قصير لأن schtasks يرفض /TR أطول من ٢٦١ حرفًا."""
    return str(write_task_launcher(interval_minutes))


def write_task_launcher(interval_minutes: float) -> Path:
    """يكتب مشغّل الدورة المجدولة بمسارات مطلقة ويسجل مخرجاته في ملف سجل."""
    bat = HERE / "autopilot_task.bat"
    script = HERE / "agents_swarm_core.py"
    log = LOGS / "autopilot_task.log"
    lines = [
        "@echo off",
        "chcp 65001 >nul",
        f'cd /d "{ROOT}"',
        (f'"{sys.executable}" "{script}" --once --lang both --ideas 3 --templates '
         f'--interval {interval_minutes:g} --report "{REPORT_FILE}" >> "{log}" 2>&1'),
    ]
    LOGS.mkdir(parents=True, exist_ok=True)
    bat.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8", newline="")
    return bat


def install_schedule(interval_minutes: float, daily_time: str | None = None) -> int:
    if os.name != "nt":
        print("[i] على غير Windows استخدم cron:")
        print(f'    0 * * * * cd "{ROOT}" && "{sys.executable}" scripts/agents_swarm_core.py --once')
        return 0
    if not shutil.which("schtasks"):
        print("[✗] schtasks غير متاح على هذا النظام. / schtasks is not available.")
        return 2
    bat = write_task_launcher(interval_minutes)
    command = f'"{bat}"'
    if daily_time:
        schedule = ["/SC", "DAILY", "/ST", daily_time]
        human = f"يوميًا الساعة {daily_time} / daily at {daily_time}"
    else:
        minutes = max(1, min(1439, int(interval_minutes)))
        schedule = ["/SC", "MINUTE", "/MO", str(minutes)]
        human = f"كل {minutes} دقيقة / every {minutes} minutes"
    result = subprocess.run(["schtasks", "/Create", "/TN", TASK_NAME, "/TR", command, *schedule, "/F"],
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        print("[✗] فشل إنشاء المهمة / task creation failed:", (result.stdout or result.stderr).strip()[:400])
        return 2
    print(f"[✓] سُجّلت مهمة {TASK_NAME} — {human}")
    print(f"    الأمر / command: {command}")
    return 0


def uninstall_schedule() -> int:
    if os.name != "nt":
        print("[i] احذف سطر cron يدويًا. / remove the cron line manually.")
        return 0
    result = subprocess.run(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"],
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        print("[✗] لم أجد المهمة أو تعذّر حذفها / task not found:", (result.stdout or result.stderr).strip()[:300])
        return 2
    print(f"[✓] حُذفت المهمة {TASK_NAME}")
    return 0


def schedule_status(report_path: Path) -> int:
    if os.name == "nt":
        result = subprocess.run(["schtasks", "/Query", "/TN", TASK_NAME, "/FO", "LIST"],
                                capture_output=True, text=True, encoding="utf-8", errors="replace")
        if result.returncode == 0:
            wanted = ("TaskName", "Next Run Time", "Status", "Last Run Time", "Last Result",
                      "اسم المهمة", "وقت التشغيل التالي", "الحالة", "وقت آخر تشغيل", "آخر نتيجة")
            print("[✓] المهمة المجدولة / scheduled task:")
            for line in (result.stdout or "").splitlines():
                if any(key in line for key in wanted):
                    print("   ", line.strip())
        else:
            print("[i] لا مهمة مجدولة بهذا الاسم بعد (شغّل --install). / no scheduled task yet.")
    report = read_json(report_path, {})
    if report:
        totals = report.get("totals", {})
        health = report.get("health", {})
        print("\n[i] آخر تقرير / latest report:", report_path)
        print(f"    آخر تحديث / generated: {report.get('generated_at')}")
        print(f"    دورات / cycles: {report.get('run', {}).get('cycles')} | "
              f"منشور / published: {totals.get('ideas_published')} | "
              f"في الطابور / queued: {totals.get('ideas_queued')}")
        print(f"    صحة / health: {health.get('status')} | "
              f"متوسط الزمن / avg latency: {health.get('avg_latency_ms')} ms")
    else:
        print("[i] لا تقرير بعد / no report yet:", report_path)
    return 0


# --------------------------------------------------------------------------- #
# القفل
# --------------------------------------------------------------------------- #


def acquire_lock() -> bool:
    LOGS.mkdir(parents=True, exist_ok=True)
    if LOCK_FILE.exists():
        try:
            stamp = datetime.fromisoformat(LOCK_FILE.read_text(encoding="utf-8").strip())
        except ValueError:
            stamp = datetime.now() - LOCK_TTL - timedelta(seconds=1)
        if datetime.now() - stamp < LOCK_TTL:
            return False
        LOCK_FILE.unlink(missing_ok=True)
    try:
        LOCK_FILE.write_text(datetime.now().isoformat(timespec="seconds"), encoding="utf-8")
    except OSError:
        return False
    return True


def release_lock() -> None:
    LOCK_FILE.unlink(missing_ok=True)


# --------------------------------------------------------------------------- #
# الدورة والحلقة
# --------------------------------------------------------------------------- #


def run_cycle(swarm: AIAgentSwarm, *, with_templates: bool, log: Speaker,
              templates_file: str | None = None, ideas: int = 5,
              sources: Sequence[str] = ("github", "hn", "local"),
              report: AutopilotReport | None = None, number: int = 1,
              with_task: bool = False) -> dict[str, Any]:
    """دورة واحدة كاملة: مراقبة → صيد وتعريب → نشر → (مزامنة قوالب) → تقرير."""
    started = time.time()
    summary: dict[str, Any] = {"number": number, "started_at": now_iso(), "online": False}
    log.say(f"بدء الدورة {number}", f"cycle {number} starting", tag="🔄 Cycle")

    online = swarm.monitor.check()
    summary["online"] = online
    if online and not (swarm.dry_run or swarm.offline):
        summary["queue"] = swarm.flush_queue()

    idea_result = swarm.publish_ideas(swarm.localizer.fetch(sources, ideas), ideas) if ideas > 0 else {
        "discovered": 0, "published": 0, "queued": 0, "skipped": 0, "failed": 0, "titles": []}
    summary["ideas"] = idea_result
    if report:
        for key, value in (("ideas_discovered", idea_result["discovered"]),
                           ("ideas_published", idea_result["published"]),
                           ("ideas_queued", idea_result["queued"]),
                           ("ideas_skipped", idea_result["skipped"])):
            report.add(key, value)
        report.add("ideas_flushed", (summary.get("queue") or {}).get("flushed", 0))

    if with_templates:
        counts = swarm.cloud_connector_templates(json_file=templates_file, dry_run=swarm.dry_run)
        summary["templates"] = counts
        if report:
            report.add("template_create", counts.get("create", 0))
            report.add("template_update", counts.get("update", 0))
            report.add("template_unchanged", counts.get("unchanged", 0))
            report.add("template_failed", counts.get("failed", 0))
        log.say(f"القوالب: جديد {counts['create']} | محدَّث {counts['update']} | بلا تغيير {counts['unchanged']} | فشل {counts['failed']}",
                f"templates: new {counts['create']} | updated {counts['update']} | unchanged {counts['unchanged']} | failed {counts['failed']}",
                tag="📦 Library")

    if with_task and online:
        headline = idea_result["titles"][0] if idea_result["titles"] else "تحديث دوري للقوالب"
        if swarm.cloud_connector_agent(f"تحديث تلقائي: {headline[:50]}", "Medium", 100) and report:
            report.add("tasks_written", 1)

    summary["seconds"] = round(time.time() - started, 2)
    summary["finished_at"] = now_iso()
    summary["health"] = swarm.monitor.snapshot()
    log.say(f"انتهت الدورة {number} في {summary['seconds']} ث — منشور {idea_result['published']}، طابور {idea_result['queued']}",
            f"cycle {number} done in {summary['seconds']}s — published {idea_result['published']}, queued {idea_result['queued']}",
            tag="✅ Cycle")
    if report:
        report.cycle(number, summary)
        report.save(summary["health"])
    return summary


def run_loop(swarm: AIAgentSwarm, *, interval_minutes: float, cycles: int,
             with_templates: bool, log: Speaker, templates_file: str | None = None,
             ideas: int = 5, sources: Sequence[str] = ("github", "hn", "local"),
             report: AutopilotReport | None = None, with_task: bool = False) -> int:
    interval_seconds = max(5.0, interval_minutes * 60)
    plan = "بلا حد / unlimited" if cycles <= 0 else f"{cycles} دورة / cycles"
    log.say(f"بدأ التشغيل المستمر كل {interval_minutes:g} دقيقة ({plan})",
            f"continuous mode every {interval_minutes:g} minutes ({plan})", tag="🔁 Loop")
    completed = 0
    try:
        while True:
            completed += 1
            try:
                run_cycle(swarm, with_templates=with_templates, log=log, templates_file=templates_file,
                          ideas=ideas, sources=sources, report=report, number=completed, with_task=with_task)
            except BubbleError as exc:
                log.say(f"خطأ Bubble في الدورة {completed}: {str(exc).splitlines()[0]}",
                        f"Bubble error in cycle {completed}: {str(exc).splitlines()[0]}", tag="❌ Loop")
                if report:
                    report.error(f"Bubble: {exc}")
                    report.save(swarm.monitor.snapshot())
            except Exception as exc:  # الحلقة لا تسقط بسبب دورة واحدة
                log.say(f"خطأ غير متوقع في الدورة {completed}: {type(exc).__name__}: {exc}",
                        f"unexpected error in cycle {completed}: {type(exc).__name__}: {exc}", tag="❌ Loop")
                if report:
                    report.error(f"{type(exc).__name__}: {exc}")
                    report.save(swarm.monitor.snapshot())
            if cycles > 0 and completed >= cycles:
                log.say(f"اكتملت الدورات المطلوبة ({completed})", f"requested cycles completed ({completed})", tag="✅ Loop")
                return 0
            log.say(f"انتظار {interval_minutes:g} دقيقة…", f"sleeping {interval_minutes:g} minutes…", tag="⏳")
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        log.say(f"أُوقف التشغيل يدويًا بعد {completed} دورة — خروج نظيف",
                f"stopped manually after {completed} cycles — clean exit", tag="⛔")
        return 0


# --------------------------------------------------------------------------- #
# واجهة الأوامر
# --------------------------------------------------------------------------- #


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="الطيار الآلي لـ Arab Templates: صيد أفكار + تعريب ثنائي + نشر في Bubble + مراقبة وتعافٍ + جدولة.",
    )
    parser.add_argument("--once", action="store_true", help="دورة واحدة كاملة (افتراضي)")
    parser.add_argument("--loop", action="store_true", help="تشغيل مستمر / continuous mode")
    parser.add_argument("--interval", type=float, default=60.0, help="الدقائق بين الدورات (افتراضي 60)")
    parser.add_argument("--cycles", type=int, default=0, help="عدد الدورات ثم التوقف (0 = بلا حد)")
    parser.add_argument("--ideas", type=int, default=5, help="عدد الأفكار في كل دورة (0 = تعطيل الصيد)")
    parser.add_argument("--sources", default=DEFAULT_SOURCES, help="مصادر الأفكار: github,hn,local")
    parser.add_argument("--templates", action="store_true", help="مزامنة القوالب العربية من data/templates_ar.json")
    parser.add_argument("--templates-file", default=None, help="ملف القوالب البديل")
    parser.add_argument("--with-task", action="store_true", help="كتابة مهمة ملخّص في جدول task (السلوك القديم)")
    parser.add_argument("--lang", choices=("ar", "en", "both"), default="both", help="لغة السجلات (افتراضي both)")
    parser.add_argument("--app-url", default=None, help="رابط Bubble (افتراضيًا من .env)")
    parser.add_argument("--dry-run", action="store_true", help="بلا كتابة في Bubble، والأفكار تُحفظ في الطابور")
    parser.add_argument("--offline", action="store_true", help="بلا أي اتصال شبكي (اختبار)")
    parser.add_argument("--report", default=str(REPORT_FILE), help="مسار تقرير الأداء")
    parser.add_argument("--log-file", default=None, help="ملف سجل إضافي للطرفية")
    parser.add_argument("--retries", type=int, default=2, help="محاولات الفحص الإضافية قبل إعلان الانقطاع")
    parser.add_argument("--timeout", type=float, default=12.0, help="مهلة جلب الأفكار بالثواني")
    parser.add_argument("--check", action="store_true", help="فحص اتصال Bubble فقط ثم الخروج")
    parser.add_argument("--install", action="store_true", help="تسجيل مهمة مجدولة في Windows Task Scheduler")
    parser.add_argument("--uninstall", action="store_true", help="حذف المهمة المجدولة")
    parser.add_argument("--status", action="store_true", help="حالة المهمة المجدولة وآخر تقرير")
    parser.add_argument("--daily", metavar="HH:MM", default=None, help="جدولة يومية بوقت محدد بدل كل ساعة")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    report_path = Path(args.report)
    log = Speaker(args.lang, args.log_file)

    if args.install:
        return install_schedule(args.interval, args.daily)
    if args.uninstall:
        return uninstall_schedule()
    if args.status:
        return schedule_status(report_path)

    sources = tuple(s.strip().lower() for s in str(args.sources).split(",") if s.strip())
    swarm = AIAgentSwarm(app_url=args.app_url or BUBBLE_API_URL, lang=args.lang,
                         offline=args.offline, dry_run=args.dry_run, log=log)
    swarm.monitor.retries = max(0, args.retries)
    swarm.localizer.timeout = max(3.0, args.timeout)

    if args.check:
        ok = swarm.monitor.check()
        snapshot = swarm.monitor.snapshot()
        write_json(report_path, {
            "version": "2.0", "product": "Arab Templates — Full Autopilot",
            "generated_at": now_iso(), "mode": "health-check", "health": snapshot,
        })
        log.say(f"نتيجة الفحص: {snapshot['status']} — متوسط {snapshot['avg_latency_ms']} ms",
                f"health result: {snapshot['status']} — avg {snapshot['avg_latency_ms']} ms", tag="🩺 Summary")
        log.close()
        return 0 if ok else 1

    report = AutopilotReport(report_path, mode="loop" if args.loop else "once", lang=args.lang,
                             dry_run=args.dry_run, offline=args.offline, interval=args.interval)
    if not acquire_lock():
        log.say("تشغيل آخر قيد التنفيذ (قفل قائم) — تم التجاهل",
                "another autopilot run is active (lock held) — skipped", tag="🔒 Lock")
        log.close()
        return 3

    log.say("بدأ الطيار الآلي — صيد وتعريب، مراقبة وتعافٍ، نشر تلقائي",
            "autopilot started — scraping, localizing, monitoring, publishing", tag="🤖 Autopilot")
    log.say(f"الإعدادات: أفكار {args.ideas} | مصادر {','.join(sources)} | تجريبي {args.dry_run} | غير متصل {args.offline}",
            f"settings: ideas {args.ideas} | sources {','.join(sources)} | dry-run {args.dry_run} | offline {args.offline}",
            tag="⚙️ Setup")
    code = 0
    try:
        if args.loop:
            code = run_loop(swarm, interval_minutes=args.interval, cycles=args.cycles,
                            with_templates=args.templates, log=log, templates_file=args.templates_file,
                            ideas=max(0, args.ideas), sources=sources, report=report, with_task=args.with_task)
        else:
            summary = run_cycle(swarm, with_templates=args.templates, log=log,
                                templates_file=args.templates_file, ideas=max(0, args.ideas),
                                sources=sources, report=report, number=1, with_task=args.with_task)
            code = 0 if summary.get("online") or args.offline or args.dry_run else 1
    except BubbleError as exc:
        log.say(f"فشل الاتصال: {exc}", f"connection failure: {exc}", tag="❌ Fatal")
        report.error(str(exc))
        report.save(swarm.monitor.snapshot())
        code = 2
    except KeyboardInterrupt:
        log.say("أُوقف يدويًا — خروج نظيف", "interrupted manually — clean exit", tag="⛔")
    finally:
        report.save(swarm.monitor.snapshot())
        release_lock()
        log.say(f"التقرير: {report_path}", f"report: {report_path}", tag="📄 Report")
        log.close()
    return code


if __name__ == "__main__":
    sys.exit(main())
