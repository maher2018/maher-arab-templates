#!/usr/bin/env python3
"""مُحلِّل فواتير واتساب لمُنتج الامتثال الضريبي في Arab Templates.

يستقبل نص فاتورة واردة (كما يُنسخ من واتساب أو من صورة استُخرج نصها)، ويستخرج:
اسم المورد، التاريخ، المبلغ الإجمالي، وقيمة الضريبة — بأرقام عربية أو لاتينية،
وبفواصل عربية أو إنجليزية. يتحقق من تناسق (المجموع الفرعي + الضريبة = الإجمالي)
ويشتق الحقل الناقص من نسبة الضريبة عند الإمكان، ثم يرسل الفاتورة إلى جدول
``invoice`` في تطبيق at-ai-lab ويُخرج تقريرًا جاهزًا (Markdown + JSON).

أمثلة:
    python whatsapp_invoice_parser.py --demo
    python whatsapp_invoice_parser.py --demo --send
    python whatsapp_invoice_parser.py --file invoices.txt --send --save
    python whatsapp_invoice_parser.py --text "المورد: شركة النخيل … الإجمالي: 1150"
    type invoice.txt | python whatsapp_invoice_parser.py --stdin

لا يُطبع التوكن ولا يُرسل إلى أي مكان غير تطبيقك.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

try:
    from bubble_data_sync import BubbleClient, BubbleError
except ImportError as exc:  # pragma: no cover
    sys.exit(f"ضع bubble_data_sync.py بجانب هذا الملف — {exc}")

try:  # أسماء عربية في مخرجات الطرفية على Windows
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass

ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
ARABIC_MONTHS = {
    "يناير": 1, "فبراير": 2, "مارس": 3, "أبريل": 4, "ابريل": 4, "إبريل": 4,
    "مايو": 5, "يونيو": 6, "يونيه": 6, "يوليو": 7, "يوليه": 7,
    "أغسطس": 8, "اغسطس": 8, "سبتمبر": 9, "أكتوبر": 10, "اكتوبر": 10,
    "نوفمبر": 11, "ديسمبر": 12,
}

#: نسبة الضريبة الافتراضية في السعودية عندما لا تُذكر في الفاتورة.
DEFAULT_VAT_RATE = 15.0

LABELS: dict[str, list[str]] = {
    "supplier": ["اسم المورد", "المورد", "اسم البائع", "البائع", "اسم الشركة", "الشركة", "Vendor", "Supplier", "Seller", "Company"],
    "date": ["تاريخ الفاتورة", "تاريخ الإصدار", "التاريخ", "Invoice Date", "Date"],
    "subtotal": ["المجموع الفرعي", "الإجمالي قبل الضريبة", "المبلغ قبل الضريبة", "Subtotal", "Sub Total", "Net Amount"],
    "total": ["المبلغ الإجمالي", "إجمالي الفاتورة", "الإجمالي المستحق", "المجموع الكلي", "الإجمالي", "Grand Total", "Total Amount", "Amount Due", "Total"],
    "tax": ["ضريبة القيمة المضافة", "مبلغ الضريبة", "الضريبة", "VAT Amount", "VAT", "Tax Amount", "Tax"],
}

NUM_RE = re.compile(r"\d+(?:[.,٬]\d{3})*(?:[.,]\d{1,2})?")
RATE_RE = re.compile(r"(\d{1,2}(?:[.,]\d+)?)\s*%")


# --------------------------------------------------------------------------- #
# نموذج البيانات
# --------------------------------------------------------------------------- #


@dataclass
class Invoice:
    supplier: str | None = None
    invoice_date: str | None = None
    total: float | None = None
    tax: float | None = None
    subtotal: float | None = None
    vat_rate: float | None = None
    currency: str = "SAR"
    confidence: float = 0.0
    warnings: list[str] = field(default_factory=list)
    raw_text: str = ""

    @property
    def ready(self) -> bool:
        return all([self.supplier, self.invoice_date, self.total is not None])

    def as_row(self) -> dict[str, object]:
        return {
            "المورد": self.supplier,
            "التاريخ": self.invoice_date,
            "الإجمالي": self.total,
            "الضريبة": self.tax,
            "قبل الضريبة": self.subtotal,
            "النسبة": self.vat_rate,
            "الثقة": f"{self.confidence:.0%}",
        }


# --------------------------------------------------------------------------- #
# التطبيع والقراءة
# --------------------------------------------------------------------------- #


def normalize(text: str) -> str:
    """أرقام عربية → لاتينية، فواصل موحّدة، بلا تشكيل ولا تطويل."""
    text = text.translate(ARABIC_DIGITS)
    text = text.replace("٪", "%").replace("٬", ",").replace("٫", ".").replace("\u0640", "")
    text = re.sub(r"[\u064B-\u0652]", "", text)
    return text


def to_number(raw: str | None) -> float | None:
    if not raw:
        return None
    cleaned = re.sub(r"[^\d.,\-]", "", raw.replace(" ", ""))
    cleaned = cleaned.strip(".,-")
    if not cleaned:
        return None
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", "") if re.fullmatch(r"\d{1,3}(,\d{3})+", cleaned) else cleaned.replace(",", ".")
    try:
        return round(float(cleaned), 2)
    except ValueError:
        return None


def first_amount(text: str) -> float | None:
    """أول رقم ليس متبوعًا بعلامة ٪ (لتجاهل «15%» داخل سطر الإجمالي)."""
    for match in NUM_RE.finditer(text):
        rest = text[match.end():].lstrip()
        if rest.startswith("%"):
            continue
        value = to_number(match.group(0))
        if value is not None:
            return value
    return None


#: بادئات تجعل «الضريبة» جزءًا من اسم حقل آخر (صافي/شامل) لا قيمة ضريبة.
NET_PREFIXES = ("قبل ", "بعد ", "غير ", "بدون ", "بلا ", "شامل ")


QUALIFIERS = (
    "قبل الضريبة", "بعد الضريبة", "بدون الضريبة", "قبل الخصم", "بعد الخصم",
    "غير شامل", "شامل الضريبة", "قبل الرسوم", "Net ", "Before Tax", "Incl",
)


def value_after(line: str, label: str) -> str | None:
    """قيمة التسمية في السطر، مع تجاهل «قبل الضريبة» و«بعد الضريبة»."""
    for match in re.finditer(re.escape(label) + r"\s*[:：]?\s*(.+)$", line, re.IGNORECASE):
        before = line[: match.start()].rstrip()
        if any(before.endswith(prefix.strip()) for prefix in NET_PREFIXES):
            continue
        rest = match.group(1).strip()

        # «الإجمالي قبل الضريبة» ليس إجماليًا: التسمية جزء من عبارة أطول، فنتخطاها.
        if any(rest.startswith(q) for q in QUALIFIERS):
            continue
        return rest
    return None


def labelled_field(lines: list[str], labels: list[str], *, numeric: bool) -> tuple[float | str | None, str | None]:
    """يبحث عن التسمية (الأطول أولًا) ويعيد قيمتها ومصدرها."""
    for label in sorted(labels, key=len, reverse=True):
        for line in lines:
            if label.lower() not in line.lower():
                continue
            rest = value_after(line, label)
            if not rest:
                continue
            if numeric:
                value = first_amount(rest)
                if value is not None:
                    return value, line
            else:
                text = re.sub(r"\s{2,}", " ", rest).strip(" -–—:،").strip()
                text = re.split(r"\s+(?:الرقم الضريبي|الرقم الضريبى|VAT No|Tax No|CR|سجل)", text, flags=re.IGNORECASE)[0].strip()
                if text:
                    return text[:120], line
    return None, None


def parse_date(text: str) -> str | None:
    patterns = [
        (r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", "ymd"),
        (r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})", "dmy"),
        (r"(\d{1,2})\s+([^\W\d_]+)\s+(\d{4})", "dMy"),
    ]
    for pattern, order in patterns:
        for match in re.finditer(pattern, text):
            try:
                if order == "ymd":
                    year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                elif order == "dmy":
                    day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    if month > 12 and day <= 12:  # صيغة أمريكية شاذة: MM/DD/YYYY
                        day, month = month, day
                else:
                    month = ARABIC_MONTHS.get(match.group(2).strip())
                    if not month:
                        continue
                    day, year = int(match.group(1)), int(match.group(3))
                parsed = date(year, month, day)
            except (ValueError, TypeError):
                continue
            if 2000 <= parsed.year <= 2100:
                return parsed.isoformat()
    return None


def detect_currency(text: str) -> str:
    if re.search(r"دولار|USD|\$", text, re.IGNORECASE):
        return "USD"
    if re.search(r"درهم|AED", text, re.IGNORECASE):
        return "AED"
    if re.search(r"دينار|KWD|BHD|JOD", text, re.IGNORECASE):
        return "KWD"
    return "SAR"


def parse_invoice(text: str, default_rate: float = DEFAULT_VAT_RATE) -> Invoice:
    """يستخرج حقول الفاتورة من نص حر، ويشتق الناقص عند وجود نسبة ضريبة."""
    normalized = normalize(text)
    lines = [line.strip() for line in normalized.splitlines() if line.strip()]
    invoice = Invoice(raw_text=text.strip(), currency=detect_currency(normalized))
    found = 0

    supplier, _ = labelled_field(lines, LABELS["supplier"], numeric=False)
    if supplier:
        invoice.supplier = str(supplier)
        found += 1

    date_value, date_source = labelled_field(lines, LABELS["date"], numeric=False)
    parsed = parse_date(str(date_value)) if date_value else None
    if not parsed:
        parsed = parse_date(normalized)
    if parsed:
        invoice.invoice_date = parsed
        found += 1

    total, total_line = labelled_field(lines, LABELS["total"], numeric=True)
    subtotal, _ = labelled_field(lines, LABELS["subtotal"], numeric=True)
    tax, tax_line = labelled_field(lines, LABELS["tax"], numeric=True)

    if total is not None:
        invoice.total = float(total)
        found += 1
    if subtotal is not None:
        invoice.subtotal = float(subtotal)
    if tax is not None:
        invoice.tax = float(tax)
        found += 1

    # نسبة الضريبة: من سطر الضريبة أولًا، ثم من النص كله.
    for candidate in (tax_line, total_line, normalized):
        if not candidate:
            continue
        match = RATE_RE.search(candidate)
        if match:
            invoice.vat_rate = to_number(match.group(1))
            break

    if invoice.supplier is None:
        company = re.compile(r"شركة|مؤسسة|مكتب|متجر|مصنع|مقاولات|L\.?L\.?C|Est\.?|Company|Store", re.IGNORECASE)
        for line in lines:
            if not company.search(line) or re.search(r"ضريب", line):
                continue
            candidate = re.split(r"\s*[—–|•]\s*|\s+-\s+", line)[0].strip()
            candidate = re.sub(r"\s+(فاتورة|Invoice).*$", "", candidate, flags=re.IGNORECASE).strip(" -–—:،")
            if candidate:
                invoice.supplier = candidate[:120]
                invoice.warnings.append("اسم المورد مُستنتج من نص السطر، وليس من تسمية صريحة.")
                break

    # اشتقاق الناقص
    rate = invoice.vat_rate if invoice.vat_rate is not None else default_rate
    if invoice.tax is None and invoice.total is not None:
        if invoice.subtotal is not None:
            invoice.tax = round(invoice.total - invoice.subtotal, 2)
            invoice.warnings.append("الضريبة حُسبت من فرق الإجمالي عن المجموع الفرعي.")
        else:
            invoice.tax = round(invoice.total * rate / (100 + rate), 2)
            invoice.vat_rate = rate
            invoice.warnings.append(f"الضريبة حُسبت بافتراض أنها مشمولة في الإجمالي بنسبة {rate:g}%.")
    if invoice.subtotal is None and invoice.total is not None and invoice.tax is not None:
        invoice.subtotal = round(invoice.total - invoice.tax, 2)
    if invoice.total is None and invoice.tax is not None:
        invoice.total = round(invoice.tax * (100 + rate) / rate, 2)
        invoice.vat_rate = rate
        invoice.warnings.append(f"الإجمالي اشتُق من الضريبة بنسبة {rate:g}%.")
    if invoice.vat_rate is None and invoice.tax is not None and invoice.subtotal:
        invoice.vat_rate = round(invoice.tax / invoice.subtotal * 100, 2)

    # تحقق التناسق
    checked = False
    if None not in (invoice.total, invoice.tax, invoice.subtotal):
        if abs((invoice.subtotal + invoice.tax) - invoice.total) <= 0.06:
            checked = True
        else:
            invoice.warnings.append(
                f"عدم تناسق: {invoice.subtotal} + {invoice.tax} ≠ {invoice.total} (فرق {invoice.total - invoice.subtotal - invoice.tax:+.2f})."
            )

    if not invoice.supplier:
        invoice.warnings.append("لم يُعثر على اسم المورد.")
    if not invoice.invoice_date:
        invoice.warnings.append("لم يُعثر على تاريخ صالح.")
    if invoice.total is None:
        invoice.warnings.append("لم يُعثر على المبلغ الإجمالي.")

    score = min(found, 4) / 4 * 0.8 + (0.2 if checked else 0.0)
    if invoice.warnings:
        score -= min(0.2, 0.05 * len(invoice.warnings))
    invoice.confidence = max(0.0, min(1.0, score))
    return invoice


# --------------------------------------------------------------------------- #
# التقرير
# --------------------------------------------------------------------------- #


def report_markdown(invoice: Invoice, *, bubble_id: str | None = None, error: str | None = None) -> str:
    money = lambda value: "—" if value is None else f"{value:,.2f} {invoice.currency}"
    rows = [
        ("اسم المورد", invoice.supplier or "—"),
        ("التاريخ", invoice.invoice_date or "—"),
        ("المجموع الفرعي", money(invoice.subtotal)),
        ("الضريبة" + (f" ({invoice.vat_rate:g}%)" if invoice.vat_rate is not None else ""), money(invoice.tax)),
        ("الإجمالي", money(invoice.total)),
        ("ثقة الاستخراج", f"{invoice.confidence:.0%}"),
        ("الحالة في Bubble", bubble_id or (f"لم تُرسل — {error}" if error else "لم تُرسل")),
    ]
    lines = ["# تقرير فاتورة واردة", "", "| الحقل | القيمة |", "| --- | --- |"]
    lines += [f"| {key} | {value} |" for key, value in rows]
    if invoice.warnings:
        lines += ["", "## ملاحظات", *[f"- {warning}" for warning in invoice.warnings]]
    lines += ["", "## النص الأصلي", "```", invoice.raw_text[:1500], "```", ""]
    return "\n".join(lines)


def summary_table(invoices: list[Invoice]) -> str:
    header = ["#", "المورد", "التاريخ", "الإجمالي", "الضريبة", "الثقة"]
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join("---" for _ in header) + " |"]
    for index, invoice in enumerate(invoices, start=1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    (invoice.supplier or "—")[:32],
                    invoice.invoice_date or "—",
                    "—" if invoice.total is None else f"{invoice.total:,.2f}",
                    "—" if invoice.tax is None else f"{invoice.tax:,.2f}",
                    f"{invoice.confidence:.0%}",
                ]
            )
            + " |"
        )
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# الإرسال إلى Bubble
# --------------------------------------------------------------------------- #

#: حقول جدول invoice في Bubble كما ستُنشأ في التطبيق.
INVOICE_MAP = {
    "Supplier": "supplier",
    "Invoice_Date": "invoice_date",
    "Total_Amount": "total",
    "Tax_Amount": "tax",
    "Raw_Text": "raw_text",
}


def invoice_payload(invoice: Invoice) -> dict[str, object]:
    source = asdict(invoice)
    payload: dict[str, object] = {}
    for bubble_field, attribute in INVOICE_MAP.items():
        value = source.get(attribute)
        if value not in (None, ""):
            payload[bubble_field] = value
    return payload


def send_invoice(client: BubbleClient, invoice: Invoice, type_name: str, *, dedupe: bool = False, dry_run: bool = False) -> tuple[str, str]:
    payload = invoice_payload(invoice)
    if not payload.get("Supplier"):
        raise BubbleError("لا يمكن الإرسال بلا اسم مورد.")
    if dedupe and invoice.invoice_date:
        rows = client.list_things(
            type_name,
            constraints=[
                {"key": "Supplier", "constraint_type": "equals", "value": invoice.supplier},
                {"key": "Invoice_Date", "constraint_type": "equals", "value": invoice.invoice_date},
            ],
            limit=1,
        )
        if rows:
            uid = str(rows[0].get("_id") or "")
            if dry_run:
                return "update (تجريبي)", uid
            client.update(type_name, uid, payload)
            return "update", uid
    if dry_run:
        return "create (تجريبي)", ""
    return "create", client.create(type_name, payload)


# --------------------------------------------------------------------------- #
# واجهة الأوامر
# --------------------------------------------------------------------------- #

DEMO_INVOICES = [
    """فاتورة ضريبية رقم 1024
المورد: شركة النخيل للتجارة
التاريخ: 12/03/2026
المجموع الفرعي: 1,000.00
ضريبة القيمة المضافة 15%: 150.00
الإجمالي: 1,150.00 ريال
""",
    """مؤسسة البدر للمقاولات — فاتورة
تاريخ الفاتورة: ٢٨ فبراير ٢٠٢٦
المبلغ قبل الضريبة ٢٬٤٠٠٫٠٠
المجموع الكلي ٢٬٧٦٠٫٠٠
الضريبة ١٥ ٪
""",
    """Al Noor Trading LLC
Vendor: Al Noor Trading LLC
Date: 2026-02-28
Subtotal: 800.00 SAR
VAT: 120.00 SAR
Grand Total: 920.00 SAR
""",
]


def split_invoices(text: str) -> list[str]:
    blocks = re.split(r"(?m)^\s*[-=]{3,}\s*$", text)
    if len(blocks) == 1:
        blocks = [block for block in re.split(r"\n\s*\n", text) if re.search(r"فاتورة|invoice|VAT|ضريب", block, re.IGNORECASE)]
    return [block.strip() for block in blocks if block.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="تحليل فواتير واتساب الواردة وتصديرها إلى Bubble.")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--text", help="نص الفاتورة مباشرة")
    source.add_argument("--file", help="ملف نصي فيه فاتورة أو أكثر (افصل بــ ---)")
    source.add_argument("--json-in", help="ملف JSON: قائمة نصوص أو قائمة كائنات فيها text/raw")
    source.add_argument("--stdin", action="store_true", help="اقرأ من الإدخال القياسي")
    source.add_argument("--demo", action="store_true", help="شغّل على ثلاث فواتير تجريبية")
    parser.add_argument("--type", default="invoice", help="اسم Data Type في Bubble (افتراضي: invoice)")
    parser.add_argument("--send", action="store_true", help="أرسل إلى Bubble (بلا هذا الخيار: تحليل فقط)")
    parser.add_argument("--dedupe", action="store_true", help="حدّث الفاتورة إن وُجد للمورد نفس التاريخ")
    parser.add_argument("--dry-run", action="store_true", help="لا تكتب في Bubble، اعرض ما سيحدث")
    parser.add_argument("--save", action="store_true", help="احفظ التقارير في مجلد invoice_reports")
    parser.add_argument("--app-url", default=None, help="رابط تطبيق Bubble (افتراضيًا من agents_swarm_core.py)")
    parser.add_argument("--rate", type=float, default=DEFAULT_VAT_RATE, help="نسبة الضريبة الافتراضية عند غيابها")
    args = parser.parse_args(argv)

    if args.demo:
        texts = list(DEMO_INVOICES)
    elif args.text:
        texts = [args.text]
    elif args.file:
        texts = split_invoices(Path(args.file).read_text(encoding="utf-8"))
    elif args.json_in:
        data = json.loads(Path(args.json_in).read_text(encoding="utf-8"))
        texts = [item if isinstance(item, str) else (item.get("text") or item.get("raw") or "") for item in data]
    elif args.stdin:
        texts = split_invoices(sys.stdin.read())
    else:
        parser.error("اختر مصدرًا: --text أو --file أو --json-in أو --stdin أو --demo")

    invoices = [parse_invoice(text, args.rate) for text in texts]
    client: BubbleClient | None = None
    results: list[tuple[str, str]] = []

    for index, invoice in enumerate(invoices, start=1):
        bubble_id: str | None = None
        error: str | None = None
        if args.send or args.dry_run:
            try:
                client = client or BubbleClient(app_url=args.app_url, verbose=False)
                status, bubble_id = send_invoice(client, invoice, args.type, dedupe=args.dedupe, dry_run=args.dry_run)
                results.append((status, bubble_id))
            except BubbleError as exc:
                error = str(exc).splitlines()[0]
                if "type not found" in error.lower():
                    error += " — أنشئ Data Type باسم " + args.type + " بالحقول: " + ", ".join(INVOICE_MAP) + "."
                results.append(("failed", error))
        status_note = None if error else (bubble_id or (f"{args.type}: {results[-1][0]}" if results else None))
        report = report_markdown(invoice, bubble_id=status_note, error=error)
        print(report)
        if args.save:
            out_dir = HERE.parent / "reports" / "invoice_reports"
            out_dir.mkdir(exist_ok=True)
            stamp = time.strftime("%Y%m%d-%H%M%S")
            target = out_dir / f"invoice-{stamp}-{index}.md"
            target.write_text(report, encoding="utf-8")
            print(f"[i] حُفظ التقرير: {target}")

    if len(invoices) > 1:
        print("\n## ملخص الدفعة\n")
        print(summary_table(invoices))
        if results:
            print("\n**نتيجة الإرسال:** " + " | ".join(f"{status}: {count}" for status, count in _count(results).items()))

    failed = sum(1 for status, _ in results if status == "failed")
    incomplete = sum(1 for invoice in invoices if not invoice.ready)
    return 1 if failed or incomplete else 0


def _count(pairs: list[tuple[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for status, _ in pairs:
        key = status.split(" ")[0]
        counts[key] = counts.get(key, 0) + 1
    return counts


if __name__ == "__main__":
    sys.exit(main())
