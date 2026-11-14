#!/usr/bin/env python3
"""سجل المبيعات والمشتريات لكل حساب (ملف JSON مستقل لكل حساب).

يُستخدم لحساب صافي الإقرار الضريبي: ضريبة المبيعات المحصَّلة ناقص ضريبة
المشتريات المدفوعة. التخزين محلي داخل ``reports/gulf/`` ولا يحتوي أي أسرار.

    import ledger
    ledger.add_sale("acc-1", invoice)
    ledger.summary("acc-1", "SA", "2026-11")
"""
from __future__ import annotations

import json
import re
import threading
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
STORE = ROOT / "reports" / "gulf"

_lock = threading.Lock()
_SAFE = re.compile(r"[^A-Za-z0-9._-]+")
MAX_ROWS = 20000


def _slug(account: str) -> str:
    clean = _SAFE.sub("-", (account or "").strip())[:48].strip("-.")
    return clean or "demo"


def _file(account: str) -> Path:
    return STORE / f"{_slug(account)}.json"


def load(account: str) -> dict[str, list[dict[str, Any]]]:
    path = _file(account)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    for key in ("sales", "purchases", "messages"):
        rows = data.get(key)
        data[key] = rows if isinstance(rows, list) else []
    return {"sales": data["sales"], "purchases": data["purchases"], "messages": data["messages"]}


def _save(account: str, data: dict[str, list[dict[str, Any]]]) -> None:
    STORE.mkdir(parents=True, exist_ok=True)
    _file(account).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_sale(account: str, invoice: dict[str, Any]) -> dict[str, Any]:
    """يحفظ فاتورة صادرة مختصرة (بلا بيانات عميل حساسة أكثر من اللازم)."""
    entry = {
        "id": invoice.get("uuid") or uuid.uuid4().hex[:12],
        "number": invoice.get("number"),
        "date": invoice.get("issued_at"),
        "country": (invoice.get("country") or {}).get("code"),
        "currency": invoice.get("currency"),
        "seller": (invoice.get("seller") or {}).get("name"),
        "buyer": (invoice.get("buyer") or {}).get("name"),
        "subtotal": invoice.get("subtotal"),
        "tax": invoice.get("tax"),
        "total": invoice.get("total"),
        "vat_rate": invoice.get("vat_rate"),
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    with _lock:
        data = load(account)
        data["sales"].insert(0, entry)
        del data["sales"][MAX_ROWS:]
        _save(account, data)
    return entry


def add_purchases(account: str, rows: list[dict[str, Any]], source: str = "scan") -> list[dict[str, Any]]:
    """يضيف صفوف مشتريات مستخرجة من المسح النصي أو صورة الفاتورة."""
    added: list[dict[str, Any]] = []
    stamp = datetime.now().isoformat(timespec="seconds")
    with _lock:
        data = load(account)
        for row in rows or []:
            if not isinstance(row, dict):
                continue
            total = row.get("total")
            tax = row.get("tax")
            subtotal = row.get("subtotal")
            if subtotal is None and total is not None and tax is not None:
                try:
                    subtotal = round(float(total) - float(tax), 2)
                except (TypeError, ValueError):
                    subtotal = None
            entry = {
                "id": uuid.uuid4().hex[:12],
                "supplier": str(row.get("supplier") or "مورد غير معروف")[:160],
                "date": str(row.get("date") or date.today().isoformat())[:10],
                "subtotal": subtotal,
                "tax": tax,
                "total": total,
                "rate": row.get("rate"),
                "currency": row.get("currency") or "SAR",
                "confidence": row.get("confidence"),
                "source": source,
                "created_at": stamp,
            }
            data["purchases"].insert(0, entry)
            added.append(entry)
        del data["purchases"][MAX_ROWS:]
        _save(account, data)
    return added


def delete_entry(account: str, kind: str, entry_id: str) -> bool:
    key = "sales" if kind in ("sales", "sale") else "purchases" if kind in ("purchases", "purchase") else ""
    if not key or not entry_id:
        return False
    with _lock:
        data = load(account)
        before = len(data[key])
        data[key] = [row for row in data[key] if row.get("id") != entry_id]
        changed = len(data[key]) != before
        if changed:
            _save(account, data)
    return changed


def add_message(account: str, topic: str, message: str, sender: str = "client") -> dict[str, Any]:
    entry = {
        "id": uuid.uuid4().hex[:10],
        "topic": (topic or "استشارة ضريبية")[:120],
        "message": (message or "")[:2000],
        "sender": "client" if sender != "accountant" else "accountant",
        "ticket": "GT-" + uuid.uuid4().hex[:6].upper(),
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    with _lock:
        data = load(account)
        data["messages"].insert(0, entry)
        del data["messages"][500:]
        _save(account, data)
    return entry


def list_messages(account: str) -> list[dict[str, Any]]:
    with _lock:
        return list(load(account)["messages"])


def _amount(value: Any) -> float:
    try:
        return round(float(value or 0), 2)
    except (TypeError, ValueError):
        return 0.0


def summary(account: str, country: str, period: str, lang: str = "ar") -> dict[str, Any]:
    """صافي الإقرار: ضريبة المبيعات − ضريبة المشتريات، مع تفصيل الفواتير."""
    import einvoice  # استيراد متأخر لتفادي دورة الاستيراد

    use_en = einvoice.normalize_lang(lang) == "en"
    meta = einvoice.country_meta(country, lang)
    code = meta["code"]
    clean_period = (period or date.today().strftime("%Y-%m"))[:7]
    with _lock:
        data = load(account)

    sales = [row for row in data["sales"]
             if (row.get("country") or code) == code and str(row.get("date") or "").startswith(clean_period)]
    purchases = [row for row in data["purchases"] if str(row.get("date") or "").startswith(clean_period)]

    output_tax = round(sum(_amount(row.get("tax")) for row in sales), 2)
    input_tax = round(sum(_amount(row.get("tax")) for row in purchases), 2)
    net = round(output_tax - input_tax, 2)
    taxable_sales = round(sum(_amount(row.get("subtotal")) for row in sales), 2)
    taxable_purchases = round(sum(_amount(row.get("subtotal")) for row in purchases), 2)

    if taxable_sales > 0:
        effective = round(output_tax / taxable_sales * 100, 2)
    elif meta["vat_rate"]:
        effective = meta["vat_rate"]
    else:
        effective = 0.0

    due = einvoice.due_date(code, clean_period, lang)
    status = (("Payable to the authority" if net > 0 else "Credit carried forward" if net < 0 else "Balanced")
              if use_en else
              ("مستحق للدفع" if net > 0 else "رصيد دائن للترحيل" if net < 0 else "متعادل"))
    return {
        "ok": True,
        "lang": "en" if use_en else "ar",
        "account": _slug(account),
        "country": meta,
        "period": clean_period,
        "output_tax": output_tax,
        "input_tax": input_tax,
        "net": net,
        "payable": max(net, 0.0),
        "credit": max(-net, 0.0),
        "taxable_sales": taxable_sales,
        "taxable_purchases": taxable_purchases,
        "effective_rate": effective,
        "sales_count": len(sales),
        "purchases_count": len(purchases),
        "sales": sales[:200],
        "purchases": purchases[:200],
        "due": due,
        "currency": meta["currency"],
        "status": status,
    }
