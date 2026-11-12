#!/usr/bin/env python3
"""ماسح فواتير من صورة — OCR حقيقي عند توفر Tesseract، ومحاكاة صريحة بدونه.

الجهاز الحالي لا يحتوي Tesseract، لذلك الوضع الافتراضي ``simulation``:
يستخرج الطالب بيانات متسقة (مورد، تاريخ، صافي، ضريبة ١٥٪، إجمالي) من بصمة
الصورة نفسها — أي أن نفس الصورة تعطي النتيجة نفسها في كل مرة. الواجهة تعرض
وضوحًا أن النتيجة محاكاة وليست قراءة بصرية فعلية، ويمكن تصحيحها قبل الحفظ.

عند تثبيت Tesseract (‏https://github.com/UB-Mannheim/tesseract) مع حزمة
اللغة العربية، يتحول الوضع تلقائيًا إلى ``tesseract`` ويُقرأ النص فعليًا ثم
يُمرَّر إلى ``whatsapp_invoice_parser.parse_invoice``.
"""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
sys.path.insert(0, str(ROOT / "scripts"))

SUPPLIERS = [
    "شركة النخيل للتجارة",
    "مؤسسة الخليج للمقاولات",
    "متجر الواحة",
    "شركة الأفق للتقنية",
    "مصنع الدانة للبلاستيك",
    "مؤسسة الريان للنقل",
    "شركة سماء اللوجستية",
]
ALLOWED = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff", ".pdf"}
MAX_BYTES = 6 * 1024 * 1024


def tesseract_path() -> str | None:
    return shutil.which("tesseract")


def _simulated(raw: bytes, filename: str) -> dict:
    digest = hashlib.sha256(raw).digest()
    supplier = SUPPLIERS[digest[0] % len(SUPPLIERS)]
    days_back = digest[1] % 45
    issued = date.today() - timedelta(days=days_back)
    subtotal = round(180 + digest[2] * 3.7, 2)
    rate = 15 if digest[3] % 4 else 5
    tax = round(subtotal * rate / 100, 2)
    confidence = round(0.62 + (digest[4] % 30) / 100, 2)
    return {
        "ok": True,
        "mode": "simulation",
        "engine": "محاكاة محلية (بلا OCR)",
        "file": filename,
        "invoice": {
            "supplier": supplier,
            "date": issued.isoformat(),
            "subtotal": subtotal,
            "tax": tax,
            "total": round(subtotal + tax, 2),
            "rate": rate,
            "currency": "SAR",
            "confidence": confidence,
            "warnings": ["نتيجة محاكاة — راجع الحقول أو اكتبها يدويًا قبل الاعتماد"],
        },
        "note": ("هذه محاكاة استخراج وليست قراءة بصرية: Tesseract غير مثبت على هذا الجهاز. "
                 "ثبّته لتفعيل OCR فعلي، أو صحّح الحقول ثم أضف الفاتورة للسجل."),
    }


def _tesseract(raw: bytes, filename: str) -> dict:
    from whatsapp_invoice_parser import parse_invoice  # noqa: E402

    suffix = Path(filename).suffix.lower() or ".png"
    tmp = Path(tempfile.gettempdir()) / f"gtp-ocr-{hashlib.sha256(raw).hexdigest()[:10]}{suffix}"
    tmp.write_bytes(raw)
    try:
        proc = subprocess.run([tesseract_path() or "tesseract", str(tmp), "stdout", "-l", "ara+eng"],
                              capture_output=True, text=True, timeout=45)
    finally:
        tmp.unlink(missing_ok=True)
    text = (proc.stdout or "").strip()
    if not text:
        return {**_simulated(raw, filename), "note": "تعذّر استخراج نص من الصورة — عُرضت نتيجة المحاكاة."}
    parsed = parse_invoice(text)
    return {
        "ok": True,
        "mode": "tesseract",
        "engine": "Tesseract OCR",
        "file": filename,
        "text_preview": text[:600],
        "invoice": {
            "supplier": parsed.supplier,
            "date": parsed.invoice_date,
            "subtotal": parsed.subtotal,
            "tax": parsed.tax,
            "total": parsed.total,
            "rate": parsed.vat_rate,
            "currency": parsed.currency,
            "confidence": round(float(parsed.confidence or 0), 2),
            "warnings": parsed.warnings,
        },
        "note": "قُرئت الصورة عبر Tesseract — راجع الحقول قبل الحفظ.",
    }


def extract(raw: bytes, filename: str) -> dict:
    suffix = Path(filename or "").suffix.lower()
    if suffix not in ALLOWED:
        raise ValueError("صيغة غير مدعومة — استخدم PNG أو JPG أو WEBP أو PDF")
    if not raw:
        raise ValueError("الملف فارغ")
    if len(raw) > MAX_BYTES:
        raise ValueError("حجم الصورة أكبر من ٦ ميغابايت")
    if tesseract_path():
        try:
            return _tesseract(raw, filename)
        except Exception:
            pass
    return _simulated(raw, filename)
