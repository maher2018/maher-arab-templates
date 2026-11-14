#!/usr/bin/env python3
"""يشغّل سرب الوكلاء ولوحة التحكم في الخلفية، ثم يفتح المتصفح.

    python scripts/start_services.py            # بلا فتح المتصفح
    python scripts/start_services.py --open     # يفتح اللوحة تلقائيًا

الخدمتان مستقلتان عن هذه العملية (DETACHED_PROCESS)، فلا تتوقفان عند إغلاق
النافذة. يمنع التكرار عبر logs/swarm.pid وlogs/dashboard.pid وفحص المنفذ.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGS = ROOT / "logs"
DETACHED = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP


def _alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        out = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
            capture_output=True, text=True, timeout=15,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return False
    return str(pid) in out and "python" in out.lower()


def _read_pid(name: str) -> int | None:
    try:
        return int((LOGS / name).read_text(encoding="utf-8").strip())
    except (FileNotFoundError, ValueError):
        return None


def _spawn(args: list[str], log_name: str) -> int:
    LOGS.mkdir(parents=True, exist_ok=True)
    handle = open(LOGS / log_name, "ab")
    try:
        proc = subprocess.Popen(
            [sys.executable, *args],
            cwd=str(ROOT),
            stdin=subprocess.DEVNULL,
            stdout=handle,
            stderr=subprocess.STDOUT,
            creationflags=DETACHED,
            close_fds=True,
        )
    finally:
        handle.close()
    return proc.pid


def _dashboard_ready(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=1.5) as response:
            return response.status == 200
    except Exception:
        return False


def _tail(path: Path, lines: int = 5) -> str:
    try:
        return "\n".join(path.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-lines:])
    except FileNotFoundError:
        return ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="تشغيل خدمات Arab Templates المحلية.")
    parser.add_argument("--port", type=int, default=5050)
    parser.add_argument("--open", action="store_true")
    parser.add_argument("--no-swarm", action="store_true")
    args = parser.parse_args(argv)

    LOGS.mkdir(parents=True, exist_ok=True)
    print("Arab Templates — تشغيل الخدمات المحلية")

    if not args.no_swarm:
        swarm_pid = _read_pid("swarm.pid")
        if _alive(swarm_pid):
            print(f"  [ok] السرب يعمل بالفعل (PID {swarm_pid})")
        else:
            pid = _spawn(
                [
                    "scripts/agents_swarm_core.py",
                    "--loop",
                    "--templates",
                    "--log-file",
                    "logs/swarm_loop.log",
                ],
                "swarm_console.log",
            )
            (LOGS / "swarm.pid").write_text(str(pid), encoding="utf-8")
            print(f"  [ok] شُغّل السرب في الخلفية (PID {pid}) — سجله logs/swarm_loop.log")
            time.sleep(1.5)

    dash_pid = _read_pid("dashboard.pid")
    if _dashboard_ready(args.port) or _alive(dash_pid):
        print(f"  [ok] لوحة التحكم تعمل بالفعل على المنفذ {args.port}")
    else:
        pid = _spawn(
            ["admin_dashboard.py", "--port", str(args.port)],
            "dashboard_console.log",
        )
        (LOGS / "dashboard.pid").write_text(str(pid), encoding="utf-8")
        print(f"  [..] شُغّلت لوحة التحكم (PID {pid}) — بانتظار الجاهزية…")
        for _ in range(30):
            if _dashboard_ready(args.port):
                print(f"  [ok] اللوحة جاهزة على المنفذ {args.port}")
                break
            time.sleep(1)
        else:
            print("  [warn] اللوحة لم تستجب خلال 30 ثانية — آخر السجل:")
            print("     " + (_tail(LOGS / "dashboard_console.log") or "لا سجل"))

    url = f"http://127.0.0.1:{args.port}/"
    print(f"\nاللوحة : {url}")
    print("السرب  : logs/swarm_loop.log")
    print("النشاط : logs/swarm_activity.log")
    if args.open:
        webbrowser.open(url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
