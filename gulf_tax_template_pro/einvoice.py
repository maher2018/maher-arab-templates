#!/usr/bin/env python3
"""محرك الفواتير الإلكترونية الخليجية — ثنائي اللغة.

Bilingual Gulf e-invoicing engine: VAT by country (SA 15%, AE/OM 5%, BH 10%,
QA/KW 0%), currency metadata, ZATCA/FTA TLV+Base64 QR payload, printable hash,
and automatic country detection from timezone / Accept-Language.

    from einvoice import build_invoice, detect_country
    inv = build_invoice({...}, lang="en")
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import re
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

CENT = Decimal("0.01")
LANGS = ("ar", "en")
DEFAULT_COUNTRY = "SA"
MAX_ITEMS = 200

COUNTRIES: dict[str, dict[str, Any]] = {
    "SA": {
        "name": "السعودية", "name_en": "Saudi Arabia",
        "authority": "هيئة الزكاة والضريبة والجمارك (ZATCA)",
        "authority_en": "Zakat, Tax and Customs Authority (ZATCA)",
        "vat_rate": 15.0, "currency": "SAR",
        "tax_no_label": "الرقم الضريبي (VAT)", "tax_no_label_en": "VAT number",
        "tax_no_regex": r"^\d{15}$",
        "tax_no_hint": "١٥ رقمًا", "tax_no_hint_en": "15 digits",
        "filing": "إقرار شهري أو ربع سنوي — يُقدَّم خلال الشهر التالي لنهاية الفترة",
        "filing_en": "Monthly or quarterly return — filed in the month after the period ends",
        "qr_spec": "ZATCA TLV — المرحلة الأولى (Phase 1)",
        "qr_spec_en": "ZATCA TLV — Phase 1",
        "period": "monthly",
    },
    "AE": {
        "name": "الإمارات", "name_en": "United Arab Emirates",
        "authority": "الهيئة الاتحادية للضرائب (FTA)",
        "authority_en": "Federal Tax Authority (FTA)",
        "vat_rate": 5.0, "currency": "AED",
        "tax_no_label": "رقم التسجيل الضريبي (TRN)", "tax_no_label_en": "Tax Registration Number (TRN)",
        "tax_no_regex": r"^\d{15}$",
        "tax_no_hint": "١٥ رقمًا", "tax_no_hint_en": "15 digits",
        "filing": "إقرار ربع سنوي — خلال ٢٨ يومًا من نهاية الربع",
        "filing_en": "Quarterly return — within 28 days of the quarter end",
        "qr_spec": "FTA QR — اسم المورد، TRN، التاريخ، الإجمالي، الضريبة",
        "qr_spec_en": "FTA QR — seller, TRN, timestamp, total, VAT",
        "period": "quarterly",
    },
    "OM": {
        "name": "عُمان", "name_en": "Oman",
        "authority": "جهاز الضرائب", "authority_en": "Tax Authority of Oman",
        "vat_rate": 5.0, "currency": "OMR",
        "tax_no_label": "الرقم الضريبي", "tax_no_label_en": "Tax number",
        "tax_no_regex": r"^[A-Za-z0-9]{5,20}$",
        "tax_no_hint": "رقم التسجيل الضريبي", "tax_no_hint_en": "Tax registration number",
        "filing": "إقرار شهري أو ربع سنوي حسب تصنيف المنشأة",
        "filing_en": "Monthly or quarterly return depending on the business category",
        "qr_spec": "QR ضريبي — بيانات المورد والإجمالي والضريبة",
        "qr_spec_en": "Tax QR — seller, total and VAT",
        "period": "monthly",
    },
    "BH": {
        "name": "البحرين", "name_en": "Bahrain",
        "authority": "الجهاز الوطني للإيرادات (NBR)",
        "authority_en": "National Bureau for Revenue (NBR)",
        "vat_rate": 10.0, "currency": "BHD",
        "tax_no_label": "الرقم الضريبي", "tax_no_label_en": "Tax number",
        "tax_no_regex": r"^\d{10,15}$",
        "tax_no_hint": "١٠ إلى ١٥ رقمًا", "tax_no_hint_en": "10 to 15 digits",
        "filing": "إقرار شهري أو ربع سنوي حسب حجم التوريدات",
        "filing_en": "Monthly or quarterly return depending on supply volume",
        "qr_spec": "QR ضريبي — بيانات المورد والإجمالي والضريبة",
        "qr_spec_en": "Tax QR — seller, total and VAT",
        "period": "monthly",
    },
    "QA": {
        "name": "قطر", "name_en": "Qatar",
        "authority": "الهيئة العامة للضرائب", "authority_en": "General Tax Authority",
        "vat_rate": 0.0, "currency": "QAR",
        "tax_no_label": "الرقم الضريبي", "tax_no_label_en": "Tax number",
        "tax_no_regex": r"^[A-Za-z0-9]{5,20}$",
        "tax_no_hint": "رقم التسجيل الضريبي", "tax_no_hint_en": "Tax registration number",
        "filing": "لا ضريبة قيمة مضافة مطبقة حاليًا — القالب جاهز عند تفعيلها",
        "filing_en": "VAT is not applied yet — the template is ready when it launches",
        "qr_spec": "QR ضريبي", "qr_spec_en": "Tax QR",
        "period": "monthly",
    },
    "KW": {
        "name": "الكويت", "name_en": "Kuwait",
        "authority": "وزارة المالية — الإدارة الضريبية",
        "authority_en": "Ministry of Finance — Tax Department",
        "vat_rate": 0.0, "currency": "KWD",
        "tax_no_label": "الرقم الضريبي", "tax_no_label_en": "Tax number",
        "tax_no_regex": r"^[A-Za-z0-9]{5,20}$",
        "tax_no_hint": "رقم التسجيل الضريبي", "tax_no_hint_en": "Tax registration number",
        "filing": "لا ضريبة قيمة مضافة مطبقة حاليًا — القالب جاهز عند تفعيلها",
        "filing_en": "VAT is not applied yet — the template is ready when it launches",
        "qr_spec": "QR ضريبي", "qr_spec_en": "Tax QR",
        "period": "monthly",
    },
}

CURRENCIES: dict[str, dict[str, Any]] = {
    "SAR": {"name": "ريال سعودي", "name_en": "Saudi Riyal", "symbol": "ر.س", "decimals": 2},
    "AED": {"name": "درهم إماراتي", "name_en": "UAE Dirham", "symbol": "د.إ", "decimals": 2},
    "KWD": {"name": "دينار كويتي", "name_en": "Kuwaiti Dinar", "symbol": "د.ك", "decimals": 3},
    "QAR": {"name": "ريال قطري", "name_en": "Qatari Riyal", "symbol": "ر.ق", "decimals": 2},
    "OMR": {"name": "ريال عُماني", "name_en": "Omani Rial", "symbol": "ر.ع", "decimals": 3},
    "BHD": {"name": "دينار بحريني", "name_en": "Bahraini Dinar", "symbol": "د.ب", "decimals": 3},
    "USD": {"name": "دولار أمريكي", "name_en": "US Dollar", "symbol": "$", "decimals": 2},
    "EUR": {"name": "يورو", "name_en": "Euro", "symbol": "€", "decimals": 2},
}

# خرائط الاكتشاف التلقائي: المنطقة الزمنية أولًا ثم لغة المتصفح ثم المنطقة.
TIMEZONE_COUNTRY: dict[str, str] = {
    "asia/riyadh": "SA", "asia/dubai": "AE", "asia/kuwait": "KW", "asia/qatar": "QA",
    "asia/muscat": "OM", "asia/bahrain": "BH",
}
LANGUAGE_COUNTRY: dict[str, str] = {
    "ar-sa": "SA", "ar-ae": "AE", "ar-kw": "KW", "ar-qa": "QA", "ar-om": "OM", "ar-bh": "BH",
    "en-ae": "AE", "en-bh": "BH", "en-qa": "QA", "en-om": "OM", "en-kw": "KW", "en-sa": "SA",
}


def normalize_lang(value: Any) -> str:
    return "en" if str(value or "").strip().lower().startswith("en") else "ar"


def m(lang: str, ar: str, en: str) -> str:
    """رسالة ثنائية حسب اللغة المطلوبة."""
    return en if normalize_lang(lang) == "en" else ar


def decimal(value: Any, default: str = "0") -> Decimal:
    """تحويل آمن إلى Decimal — يقبل «١٢٣٤٫٥» والفاصلة العربية."""
    if value is None or value == "":
        return Decimal(default)
    if isinstance(value, bool):
        raise ValueError(m("ar", "قيمة رقمية غير صالحة", "invalid numeric value"))
    text = str(value).strip()
    text = (text.replace("٬", "").replace(",", "").replace("٫", ".")
            .replace("−", "-").replace("—", "-"))
    arabic = "٠١٢٣٤٥٦٧٨٩"
    text = "".join(str(arabic.index(ch)) if ch in arabic else ch for ch in text)
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(m("ar", f"قيمة رقمية غير صالحة: {value}", f"invalid numeric value: {value}")) from exc


def money(value: Any) -> Decimal:
    return decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def fnum(value: Any) -> float:
    return float(money(value))


def country_meta(code: str | None, lang: str = "ar") -> dict[str, Any]:
    """بيانات الدولة مع نصوص معروضة باللغة المطلوبة (مع إبقاء الأصلين)."""
    key = (code or DEFAULT_COUNTRY).strip().upper()
    if key not in COUNTRIES:
        raise ValueError(m(lang, f"دولة غير مدعومة: {code}", f"unsupported country: {code}"))
    base = COUNTRIES[key]
    use_en = normalize_lang(lang) == "en"
    meta = {"code": key, **base, "lang": "en" if use_en else "ar"}
    for field in ("name", "authority", "tax_no_label", "tax_no_hint", "filing", "qr_spec"):
        meta[field] = base[f"{field}_en"] if use_en else base[field]
    meta["currency"] = base["currency"]
    meta["currency_info"] = {"code": base["currency"], **CURRENCIES.get(base["currency"], {})}
    return meta


def countries_public(lang: str = "ar") -> list[dict[str, Any]]:
    return [country_meta(code, lang) for code in COUNTRIES]


def currencies_public(lang: str = "ar") -> list[dict[str, Any]]:
    rows = []
    for code, info in CURRENCIES.items():
        rows.append({
            "code": code,
            "name": info["name_en"] if normalize_lang(lang) == "en" else info["name"],
            "name_ar": info["name"], "name_en": info["name_en"],
            "symbol": info["symbol"], "decimals": info["decimals"],
        })
    return rows


def detect_country(tz: str | None = None, accept_language: str | None = None,
                   lang: str = "ar") -> dict[str, Any]:
    """يخمّن دولة العميل من المنطقة الزمنية ثم لغة المتصفح، ويضبط العملة والنسبة."""
    zone = (tz or "").strip().lower()
    if zone in TIMEZONE_COUNTRY:
        code, source = TIMEZONE_COUNTRY[zone], "timezone"
    else:
        code, source = "", ""
        for part in (accept_language or "").replace(";", ",").split(","):
            tag = part.strip().lower()[:5]
            if tag in LANGUAGE_COUNTRY:
                code, source = LANGUAGE_COUNTRY[tag], "language"
                break
            short = tag[:2]
            if short in ("ar", "en"):
                code, source = DEFAULT_COUNTRY, "language"
    if not code:
        code, source = DEFAULT_COUNTRY, "default"
    meta = country_meta(code, lang)
    return {
        "country": meta["code"],
        "country_name": meta["name"],
        "currency": meta["currency"],
        "vat_rate": meta["vat_rate"],
        "timezone": tz or "",
        "source": source,
        "confidence": {"timezone": 0.95, "language": 0.6, "default": 0.3}[source],
    }


def compute_lines(items: list[dict[str, Any]], rate: float, prices_include_vat: bool = False,
                  lang: str = "ar") -> dict[str, Any]:
    """يحسب كل بند ثم الإجماليات. الأسعار قد تُدخل شاملة الضريبة أو قبلها."""
    if not isinstance(items, list) or not items:
        raise ValueError(m(lang, "أضف بندًا واحدًا على الأقل للفاتورة", "add at least one invoice line"))
    if len(items) > MAX_ITEMS:
        raise ValueError(m(lang, f"الحد الأقصى {MAX_ITEMS} بندًا في الفاتورة", f"maximum {MAX_ITEMS} lines per invoice"))
    factor = Decimal("1") + Decimal(str(rate)) / Decimal("100")
    rows: list[dict[str, Any]] = []
    subtotal = discount_total = tax_total = Decimal("0")
    for index, item in enumerate(items, start=1):
        desc = str(item.get("description") or "").strip()
        if not desc:
            raise ValueError(m(lang, f"البند {index}: الوصف مطلوب", f"line {index}: description is required"))
        qty = decimal(item.get("quantity", 1))
        if qty <= 0:
            raise ValueError(m(lang, f"البند {index}: الكمية يجب أن تكون أكبر من صفر",
                               f"line {index}: quantity must be greater than zero"))
        price = decimal(item.get("unit_price", 0))
        if price < 0:
            raise ValueError(m(lang, f"البند {index}: السعر لا يكون سالبًا", f"line {index}: price cannot be negative"))
        discount_pct = decimal(item.get("discount", 0))
        if discount_pct < 0 or discount_pct > 100:
            raise ValueError(m(lang, f"البند {index}: نسبة الخصم بين ٠ و١٠٠", f"line {index}: discount must be 0-100"))
        gross = qty * price
        discount_amount = (gross * discount_pct / Decimal("100")).quantize(CENT, rounding=ROUND_HALF_UP)
        net_input = gross - discount_amount
        if prices_include_vat and factor > 0:
            net = (net_input / factor).quantize(CENT, rounding=ROUND_HALF_UP)
            tax = (net_input - net).quantize(CENT, rounding=ROUND_HALF_UP)
        else:
            net = net_input.quantize(CENT, rounding=ROUND_HALF_UP)
            tax = (net * Decimal(str(rate)) / Decimal("100")).quantize(CENT, rounding=ROUND_HALF_UP)
        line_total = (net + tax).quantize(CENT, rounding=ROUND_HALF_UP)
        subtotal += net
        discount_total += discount_amount
        tax_total += tax
        rows.append({
            "description": desc,
            "quantity": float(qty),
            "unit_price": fnum(price),
            "discount_pct": fnum(discount_pct),
            "discount_amount": fnum(discount_amount),
            "net": fnum(net),
            "tax": fnum(tax),
            "total": fnum(line_total),
        })
    subtotal = subtotal.quantize(CENT, rounding=ROUND_HALF_UP)
    tax_total = tax_total.quantize(CENT, rounding=ROUND_HALF_UP)
    return {
        "rows": rows,
        "subtotal": fnum(subtotal),
        "discount": fnum(discount_total),
        "tax": fnum(tax_total),
        "total": fnum(subtotal + tax_total),
        "vat_rate": float(rate),
        "prices_include_vat": bool(prices_include_vat),
    }


def _tlv(tag: int, value: str) -> bytes:
    raw = value.encode("utf-8")
    if len(raw) > 255:
        raw = raw[:255]
    return bytes([tag, len(raw)]) + raw


def zatca_tlv(seller_name: str, vat_number: str, timestamp: str, total: Any, tax: Any) -> str:
    """حمولة QR: خمس وسوم (اسم المورد، الرقم الضريبي، الطابع الزمني، الإجمالي، الضريبة)."""
    payload = b"".join([
        _tlv(1, seller_name),
        _tlv(2, vat_number),
        _tlv(3, timestamp),
        _tlv(4, f"{money(total):.2f}"),
        _tlv(5, f"{money(tax):.2f}"),
    ])
    return base64.b64encode(payload).decode("ascii")


def qr_svg(payload: str, scale: int = 5) -> str | None:
    """صورة QR كـSVG مضمّن. تعيد None إن لم تكن segno مثبتة."""
    try:
        import segno  # type: ignore
    except Exception:
        return None
    buffer = io.BytesIO()
    segno.make(payload, error="m").save(
        buffer, kind="svg", scale=scale, border=2, dark="#0b2431", light="#ffffff"
    )
    return buffer.getvalue().decode("utf-8")


def invoice_number(country: str, issued: date, sequence: int | None = None) -> str:
    if sequence and sequence > 0:
        return f"INV-{country}-{issued.strftime('%Y%m')}-{sequence:04d}"
    return f"INV-{country}-{issued.strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"


def validate_tax_no(code: str, value: str, label: str, lang: str = "ar") -> str:
    clean = (value or "").strip()
    if not clean:
        raise ValueError(m(lang, f"{label} مطلوب", f"{label} is required"))
    pattern = COUNTRIES[code]["tax_no_regex"]
    if pattern and not re.match(pattern, clean):
        hint = COUNTRIES[code]["tax_no_hint_en" if normalize_lang(lang) == "en" else "tax_no_hint"]
        raise ValueError(m(lang, f"{label} غير صالح — {hint}", f"invalid {label} — {hint}"))
    return clean


def build_invoice(payload: dict[str, Any]) -> dict[str, Any]:
    """يبني فاتورة كاملة (تحقق + حسابات + QR + تجزئة) دون أي تخزين."""
    if not isinstance(payload, dict):
        raise ValueError(m("ar", "حمولة غير صالحة", "invalid payload"))
    lang = normalize_lang(payload.get("lang"))
    meta = country_meta(payload.get("country"), lang)
    code = meta["code"]
    rate = meta["vat_rate"]
    if payload.get("vat_rate") not in (None, ""):
        rate = float(decimal(payload["vat_rate"]))
        if rate < 0 or rate > 100:
            raise ValueError(m(lang, "نسبة الضريبة بين ٠ و١٠٠", "VAT rate must be between 0 and 100"))

    def person(key: str, name_ar: str, name_en: str) -> dict[str, Any]:
        block = payload.get(key) or {}
        if not isinstance(block, dict):
            raise ValueError(m(lang, "بيانات الطرف غير صالحة", "invalid party details"))
        name = str(block.get("name") or "").strip()
        if not name:
            raise ValueError(m(lang, f"{name_ar} مطلوب", f"{name_en} is required"))
        return {
            "name": name[:160],
            "vat_number": str(block.get("vat_number") or "").strip()[:40],
            "address": str(block.get("address") or "").strip()[:240],
            "email": str(block.get("email") or "").strip()[:120],
            "phone": str(block.get("phone") or "").strip()[:40],
        }

    seller = person("seller", "اسم المورد", "seller name")
    buyer = person("buyer", "اسم العميل", "customer name")
    if not seller["vat_number"]:
        raise ValueError(m(lang, f"{meta['tax_no_label']} للمورد مطلوب لإصدار فاتورة معتمدة",
                           f"seller VAT number is required on a tax invoice"))
    if rate > 0:
        validate_tax_no(code, seller["vat_number"], meta["tax_no_label"], lang)

    computed = compute_lines(payload.get("items") or [], rate, bool(payload.get("prices_include_vat")), lang)

    issued_raw = str(payload.get("date") or "").strip()
    try:
        issued = date.fromisoformat(issued_raw) if issued_raw else date.today()
    except ValueError as exc:
        raise ValueError(m(lang, "تاريخ الفاتورة يجب أن يكون بصيغة YYYY-MM-DD", "invoice date must be YYYY-MM-DD")) from exc
    number = str(payload.get("number") or "").strip()[:60] or invoice_number(code, issued)

    stamp = datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload_qr = zatca_tlv(seller["name"], seller["vat_number"], stamp, computed["total"], computed["tax"])
    fingerprint = base64.b64encode(hashlib.sha256(
        json.dumps({"number": number, "seller": seller["vat_number"], "total": computed["total"],
                    "tax": computed["tax"], "stamp": stamp}, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).digest()).decode("ascii")

    notes: list[str] = []
    if rate == 0:
        notes.append(m(lang, f"{meta['name']}: لا تُطبَّق ضريبة قيمة مضافة حاليًا — الفاتورة صادرة بنسبة ٠٪.",
                       f"{meta['name']}: VAT is not applied yet — this invoice is issued at 0%."))
    if computed["discount"] > 0:
        notes.append(m(lang, "الخصم مطبَّق قبل حساب الضريبة في كل بند.",
                       "Discounts are applied before VAT on every line."))
    if payload.get("prices_include_vat"):
        notes.append(m(lang, "أُدخلت الأسعار شاملة الضريبة وتم استخراج الصافي والضريبة منها.",
                       "Prices were entered VAT-inclusive; net and VAT were extracted."))
    if not qr_svg("test"):
        notes.append(m(lang, "مكتبة segno غير مثبتة — يُعرض نص QR فقط. نفّذ: python -m pip install segno",
                       "segno is not installed — showing the QR payload only. Run: python -m pip install segno"))

    return {
        "ok": True,
        "lang": lang,
        "uuid": str(uuid.uuid4()),
        "number": number,
        "invoice_number": number,
        "issued_at": issued.isoformat(),
        "stamp": stamp,
        "country": meta,
        "currency": meta["currency"],
        "currency_info": meta["currency_info"],
        "vat_rate": float(rate),
        "seller": seller,
        "buyer": buyer,
        "items": computed["rows"],
        "subtotal": computed["subtotal"],
        "discount": computed["discount"],
        "tax": computed["tax"],
        "total": computed["total"],
        "totals": {"subtotal": computed["subtotal"], "discount": computed["discount"],
                   "tax": computed["tax"], "total": computed["total"], "vat_rate": float(rate)},
        "qr": {"payload": payload_qr, "svg": qr_svg(payload_qr), "spec": meta["qr_spec"]},
        "hash": fingerprint,
        "notes": notes,
        "totals_source": "einvoice.py",
    }


def periods(country: str, back: int = 8) -> list[str]:
    """أحدث الفترات (شهور) بصيغة YYYY-MM لملء قائمة الإقرار."""
    meta = country_meta(country)
    today = date.today().replace(day=1)
    out: list[str] = []
    cursor = today
    for _ in range(max(1, back)):
        out.append(cursor.strftime("%Y-%m"))
        cursor = (cursor - timedelta(days=1)).replace(day=1)
    if meta["period"] == "quarterly":
        out = [p for p in out if int(p[5:7]) % 3 == 0] or out
    return out


def due_date(country: str, period: str, lang: str = "ar") -> dict[str, str]:
    """آخر موعد تقديم الإقرار للفترة المحددة (تقديري حسب الدورية)."""
    meta = country_meta(country, lang)
    try:
        year, month = int(period[:4]), int(period[5:7])
    except (ValueError, IndexError) as exc:
        raise ValueError(m(lang, "الفترة يجب أن تكون بصيغة YYYY-MM", "period must be YYYY-MM")) from exc
    if meta["period"] == "quarterly":
        end_month = min(((month - 1) // 3 + 1) * 3, 12)
        end = date(year, end_month, 1)
        nxt = date(end.year + (1 if end_month == 12 else 0), 1 if end_month == 12 else end_month + 1, 1)
        due = nxt + timedelta(days=27)
    else:
        nxt = date(year + (1 if month == 12 else 0), 1 if month == 12 else month + 1, 1)
        following = date(nxt.year + (1 if nxt.month == 12 else 0), 1 if nxt.month == 12 else nxt.month + 1, 1)
        due = following - timedelta(days=1)
    return {"due": due.isoformat(), "note": meta["filing"]}
