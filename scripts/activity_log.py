#!/usr/bin/env python3
"""سجل موحّد لأنشطة السرب والأخطاء التقنية.

كل الأحداث تُكتب في logs/swarm_activity.log (تدوير عند 2 ميغابايت، 3 نسخ)
وتظهر أيضًا على الطرفية. لا يُسجَّل أي سر أو توكن.

    from activity_log import setup
    log = setup("swarm")
    log.info("دورة بدأت")
    log.exception("فشل الاتصال")   # عند وجود استثناء ضمن except
"""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT / "logs"
LOG_FILE = LOG_DIR / "swarm_activity.log"
MAX_BYTES = 2 * 1024 * 1024
BACKUPS = 3

_configured = False


def log_file() -> Path:
    return LOG_FILE


def setup(component: str = "app", *, level: int = logging.INFO, console: bool = True) -> logging.Logger:
    """يجهّز السجل مرة واحدة لكل عملية، ويُرجع سجلًا فرعيًا باسم المكوّن."""
    global _configured
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger("arab_templates")
    if not _configured:
        root.setLevel(logging.DEBUG)
        root.propagate = False
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUPS, encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
        if console:
            stream = logging.StreamHandler(sys.stderr)
            stream.setLevel(level)
            stream.setFormatter(formatter)
            root.addHandler(stream)
        _configured = True
    return root.getChild(component)


def log_error(logger: logging.Logger, message: str, exc: BaseException | None = None) -> None:
    """يسجّل خطأ تقنيًا مع نوعه ونصه، ومع التتبع الكامل عند وجود استثناء."""
    if exc is None:
        logger.error(message)
    else:
        logger.error("%s — %s: %s", message, type(exc).__name__, exc, exc_info=exc)
