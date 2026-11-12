#!/usr/bin/env python3
"""محرك الفواتير الإلكترونية الخليجية.

يحسب الضريبة حسب دولة الإصدار (السعودية ١٥٪، الإمارات وعُمان ٥٪، البحرين ١٠٪،
قطر والكويت بلا ضريبة قيمة مضافة حاليًا)، ويبني حمولة رمز الاستجابة السريعة
بصيغة ZATCA Phase 1 (TLV ثم Base64) وهي الصيغة نفسها التي تعتمدها FTA في
الإمارات لحقول: اسم المورد، الرقم الضريبي، الطابع الزمني، الإجمالي، الضريبة.

الوحدة تعمل بمكتبة بايثون القياسية فقط. توليد صورة QR يحتاج حزمة ``segno``
(اختيارية) — عند غيابها يُعاد النص المشفّر فقط وتُعرض رسالة في الواجهة.

    from einvoice import build_invoice
    inv = build_invoice({...})
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

COUNTRIES: dict[str, dict[str, Any]] = {
    "SA": {
        "name": "السعودية",
        "authority": "هيئة الزكاة والضريبة والجمارك (ZATCA)",
        "vat_rate": 15.0,
        "currency": "SAR",
        "tax_no_label": "الرقم الضريبي (VAT)",
        "tax_no_regex": r"^\d{15}$",
        "tax_no_hint": "١٥ رقمًا",
        "filing": "إقرار شهري أو ربع سنوي — يُقدَّم خلال الشهر التالي لنهاية الفترة",
        "qr_spec": "ZATCA TLV — المرحلة الأولى (Phase 1)",
        "period": "monthly",
    },
    "AE": {
        "name": "الإمارات",
        "authority": "الهيئة الاتحادية للضرائب (FTA)",
        "vat_rate": 5.0,
        "currency": "AED",
        "tax_no_label": "رقم التسجيل الضريبي (TRN)",
        "tax_no_regex": r"^\d{15}$",
        "tax_no_hint": "١٥ رقمًا",
        "filing": "إقرار ربع سنوي — خلال ٢٨ يومًا من نهاية الربع",
        "qr_spec": "FTA QR — اسم المورد، TRN، التاريخ، الإجمالي، الضريبة",
        "period": "quarterly",
    },
    "OM": {
        "name": "عُمان",
        "authority": "جهاز الضرائب",
        "vat_rate": 5.0,
        "currency": "OMR",
        "tax_no_label": "الرقم الضريبي",
        "tax_no_regex": r"^[A-Za-z0-9]{5,20}$",
        "tax_no_hint": "رقم التسجيل الضريبي",
        "filing": "إقرار شهري أو ربع سنوي حسب تصنيف المنشأة",
        "qr_spec": "QR ضريبي — بيانات المورد والإجمالي والضريبة",
        "period": "monthly",
    },
    "BH": {
        "name": "البحرين",
        "authority": "الجهاز الوطني للإيرادات (NBR)",
        "vat_rate": 10.0,
        "currency": "BHD",
        "tax_no_label": "الرقم الضريبي",
        "tax_no_regex": r"^\d{10,15}$",
        "tax_no_hint": "١٠ إلى ١٥ رقمًا",
        "filing": "إقرار شهري أو ربع سنوي حسب حجم التوريدات",
        "qr_spec": "QR ضريبي — بيانات المورد والإجمالي والضريبة",
        "period": "monthly",
    },
    "QA": {
        "name": "قطر",
        "authority": "الهيئة العامة للضرائب",
        "vat_rate": 0.0,
        "currency": "QAR",
        "tax_no_label": "الرقم الضريبي",
        "tax_no_regex": r"^[A-Za-z0-9]{5,20}$",
        "tax_no_hint": "رقم التسجيل الضريبي",
        "filing": "لا ضريبة قيمة مضافة مطبقة حاليًا — القالب جاهز عند تفعيلها",
        "qr_spec": "QR ضريبي",
        "period": "monthly",
    },
    "KW": {
        "name": "الكويت",
        "authority": "وزارة المالية — الإدارة الضريبية",
        "vat_rate": 0.0,
        "currency": "KWD",
        "tax_no_label": "الرقم الضريبي",
        "tax_no_regex": r"^[A-Za-z0-9]{5,20}$",
        "tax_no_hint": "رقم التسجيل الضريبي",
        "filing": "لا ضريبة قيمة مضافة مطبقة حاليًا — القالب جاهز عند تفعيلها",
        "qr_spec": "QR ضريبي",
        "period": "monthly",
    },
}

DEFAULT_COUNTRY = "SA"
MAX_ITEMS = 200


def decimal(value: Any, default: str = "0") -> Decimal:
    """تحويل آمن إلى Decimal — يقبل «١٢٣٤٫٥» والفاصلة العربية."""
    if value is None or value == "":
        return Decimal(default)
    if isinstance(value, bool):
        raise ValueError("قيمة رقمية غير صالحة")
    text = str(value).strip()
    text = (text.replace("٬", "").replace(",", "").replace("٫", ".")
            .replace("−", "-").replace("—", "-"))
    arabic = "٠١٢٣٤٥٦٧٨٩"
    text = "".join(str(arabic.index(ch)) if ch in arabic else ch for ch in text)
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"قيمة رقمية غير صالحة: {value}") from exc


def money(value: Any) -> Decimal:
    return decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def fnum(value: Any) -> float:
    return float(money(value))


def country_meta(code: str | None) -> dict[str, Any]:
    key = (code or DEFAULT_COUNTRY).strip().upper()
    if key not in COUNTRIES:
        raise ValueError(f"دولة غير مدعومة: {code}")
    return {"code": key, **COUNTRIES[key]}


def countries_public() -> list[dict[str, Any]]:
    return [{"code": key, **meta} for key, meta in COUNTRIES.items()]


def compute_lines(items: list[dict[str, Any]], rate: float, prices_include_vat: bool = False) -> dict[str, Any]:
    """يحسب كل بند ثم الإجماليات. الأسعار قد تُدخل شاملة الضريبة أو قبلها."""
    if not isinstance(items, list) or not items:
        raise ValueError("أضف بندًا واحدًا على الأقل للفاتورة")
    if len(items) > MAX_ITEMS:
        raise ValueError(f"الحد الأقصى {MAX_ITEMS} بندًا في الفاتورة")
    factor = Decimal("1") + Decimal(str(rate)) / Decimal("100")
    rows: list[dict[str, Any]] = []
    subtotal = Decimal("0")
    discount_total = Decimal("0")
    tax_total = Decimal("0")
    for index, item in enumerate(items, start=1):
        desc = str(item.get("description") or "").strip()
        if not desc:
            raise ValueError(f"البند {index}: الوصف مطلوب")
        qty = decimal(item.get("quantity", 1))
        if qty <= 0:
            raise ValueError(f"البند {index}: الكمية يجب أن تكون أكبر من صفر")
        price = decimal(item.get("unit_price", 0))
        if price < 0:
            raise ValueError(f"البند {index}: السعر لا يكون سالبًا")
        discount_pct = decimal(item.get("discount", 0))
        if discount_pct < 0 or discount_pct > 100:
            raise ValueError(f"البند {index}: نسبة الخصم بين ٠ و١٠٠")
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


def validate_tax_no(code: str, value: str, label: str) -> str:
    clean = (value or "").strip()
    if not clean:
        raise ValueError(f"{label} مطلوب")
    pattern = COUNTRIES[code]["tax_no_regex"]
    if pattern and not re.match(pattern, clean):
        raise ValueError(f"{label} غير صالح — {COUNTRIES[code]['tax_no_hint']}")
    return clean


def build_invoice(payload: dict[str, Any]) -> dict[str, Any]:
    """يبني فاتورة كاملة (تحقق + حسابات + QR + تجزئة) دون أي تخزين."""
    if not isinstance(payload, dict):
        raise ValueError("حمولة غير صالحة")
    meta = country_meta(payload.get("country"))
    code = meta["code"]
    rate = meta["vat_rate"]
    if payload.get("vat_rate") not in (None, ""):
        rate = float(decimal(payload["vat_rate"]))
        if rate < 0 or rate > 100:
            raise ValueError("نسبة الضريبة بين ٠ و١٠٠")

    def person(key: str, name_label: str) -> dict[str, Any]:
        block = payload.get(key) or {}
        if not isinstance(block, dict):
            raise ValueError("بيانات الطرف غير صالحة")
        name = str(block.get("name") or "").strip()
        if not name:
            raise ValueError(f"{name_label} مطلوب")
        return {
            "name": name[:160],
            "vat_number": str(block.get("vat_number") or "").strip()[:40],
            "address": str(block.get("address") or "").strip()[:240],
            "email": str(block.get("email") or "").strip()[:120],
            "phone": str(block.get("phone") or "").strip()[:40],
        }

    seller = person("seller", "اسم المورد")
    buyer = person("buyer", "اسم العميل")
    if not seller["vat_number"]:
        raise ValueError(f"{meta['tax_no_label']} للمورد مطلوب لإصدار فاتورة معتمدة")
    if rate > 0:
        validate_tax_no(code, seller["vat_number"], meta["tax_no_label"])

    computed = compute_lines(payload.get("items") or [], rate, bool(payload.get("prices_include_vat")))

    issued_raw = str(payload.get("date") or "").strip()
    try:
        issued = date.fromisoformat(issued_raw) if issued_raw else date.today()
    except ValueError as exc:
        raise ValueError("تاريخ الفاتورة يجب أن يكون بصيغة YYYY-MM-DD") from exc
    number = str(payload.get("number") or "").strip()[:60] or invoice_number(code, issued)
    sequence = payload.get("sequence")

    stamp = datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload_qr = zatca_tlv(seller["name"], seller["vat_number"], stamp, computed["total"], computed["tax"])
    fingerprint = base64.b64encode(hashlib.sha256(
        json.dumps({"number": number, "seller": seller["vat_number"], "total": computed["total"],
                    "tax": computed["tax"], "stamp": stamp}, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).digest()).decode("ascii")

    notes: list[str] = []
    if rate == 0:
        notes.append(f"{meta['name']}: لا تُطبَّق ضريبة قيمة مضافة حاليًا — الفاتورة صادرة بنسبة ٠٪.")
    if computed["discount"] > 0:
        notes.append("الخصم مطبَّق قبل حساب الضريبة في كل بند.")
    if payload.get("prices_include_vat"):
        notes.append("أُدخلت الأسعار شاملة الضريبة وتم استخراج الصافي والضريبة منها.")
    if not qr_svg("test"):
        notes.append("مكتبة segno غير مثبتة — يُعرض نص QR فقط. نفّذ: python -m pip install segno")

    return {
        "ok": True,
        "uuid": str(uuid.uuid4()),
        "number": number,
        "invoice_number": number,
        "sequence": sequence,
        "issued_at": issued.isoformat(),
        "stamp": stamp,
        "country": meta,
        "currency": meta["currency"],
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


def due_date(country: str, period: str) -> dict[str, str]:
    """آخر موعد تقديم الإقرار للفترة المحددة (تقديري حسب الدورية)."""
    meta = country_meta(country)
    try:
        year, month = int(period[:4]), int(period[5:7])
    except (ValueError, IndexError) as exc:
        raise ValueError("الفترة يجب أن تكون بصيغة YYYY-MM") from exc
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
