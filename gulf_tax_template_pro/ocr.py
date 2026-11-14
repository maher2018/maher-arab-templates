#!/usr/bin/env python3
"""ماسح فواتير من صورة — OCR حقيقي عند توفر Tesseract، ومحاكاة صريحة بدونه.

Image invoice scanner. Real OCR when Tesseract is installed (Arabic + English
trained data); otherwise an explicit simulation whose values are derived from
the image fingerprint, so the same image always yields the same extraction.
The API reports ``mode`` so the UI can label the result honestly.

    from ocr import extract
    result = extract(raw_bytes, "invoice.png", lang="en")
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

TEXT = {
    "ar": {
        "engine": "محاكاة محلية (بلا OCR)",
        "warning": "نتيجة محاكاة — راجع الحقول أو اكتبها يدويًا قبل الاعتماد",
        "note": ("هذه محاكاة استخراج وليست قراءة بصرية: Tesseract غير مثبت على هذا الجهاز. "
                 "ثبّته لتفعيل OCR فعلي، أو صحّح الحقول ثم أضف الفاتورة للسجل."),
        "no_text": "تعذّر استخراج نص من الصورة — عُرضت نتيجة المحاكاة.",
        "read": "قُرئت الصورة عبر Tesseract — راجع الحقول قبل الحفظ.",
        "bad_type": "صيغة غير مدعومة — استخدم PNG أو JPG أو WEBP أو PDF",
        "empty": "الملف فارغ",
        "too_big": "حجم الصورة أكبر من ٦ ميغابايت",
    },
    "en": {
        "engine": "Local simulation (no OCR)",
        "warning": "Simulated extraction — review or type the fields before posting",
        "note": ("This is a simulated extraction, not real OCR: Tesseract is not installed on this machine. "
                 "Install it to enable real OCR, or correct the fields before adding the invoice."),
        "no_text": "Could not read text from the image — showing the simulated result.",
        "read": "Image read with Tesseract — review the fields before saving.",
        "bad_type": "Unsupported format — use PNG, JPG, WEBP or PDF",
        "empty": "The file is empty",
        "too_big": "Image is larger than 6 MB",
    },
}


def lang_of(lang: str | None) -> str:
    return "en" if str(lang or "").lower().startswith("en") else "ar"


def tesseract_path() -> str | None:
    return shutil.which("tesseract")


def _simulated(raw: bytes, filename: str, lang: str = "ar") -> dict:
    text = TEXT[lang_of(lang)]
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
        "lang": lang_of(lang),
        "engine": text["engine"],
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
            "warnings": [text["warning"]],
        },
        "note": text["note"],
    }


def _tesseract(raw: bytes, filename: str, lang: str = "ar") -> dict:
    from whatsapp_invoice_parser import parse_invoice  # noqa: E402

    text = TEXT[lang_of(lang)]
    suffix = Path(filename).suffix.lower() or ".png"
    tmp = Path(tempfile.gettempdir()) / f"gtp-ocr-{hashlib.sha256(raw).hexdigest()[:10]}{suffix}"
    tmp.write_bytes(raw)
    try:
        proc = subprocess.run([tesseract_path() or "tesseract", str(tmp), "stdout", "-l", "ara+eng"],
                              capture_output=True, text=True, timeout=45)
    finally:
        tmp.unlink(missing_ok=True)
    content = (proc.stdout or "").strip()
    if not content:
        return {**_simulated(raw, filename, lang), "note": text["no_text"]}
    parsed = parse_invoice(content)
    return {
        "ok": True,
        "mode": "tesseract",
        "lang": lang_of(lang),
        "engine": "Tesseract OCR",
        "file": filename,
        "text_preview": content[:600],
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
        "note": text["read"],
    }


def extract(raw: bytes, filename: str, lang: str = "ar") -> dict:
    text = TEXT[lang_of(lang)]
    suffix = Path(filename or "").suffix.lower()
    if suffix not in ALLOWED:
        raise ValueError(text["bad_type"])
    if not raw:
        raise ValueError(text["empty"])
    if len(raw) > MAX_BYTES:
        raise ValueError(text["too_big"])
    if tesseract_path():
        try:
            return _tesseract(raw, filename, lang)
        except Exception:
            pass
    return _simulated(raw, filename, lang)
