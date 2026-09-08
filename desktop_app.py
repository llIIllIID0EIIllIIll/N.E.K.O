# -*- coding: utf-8 -*-
"""Standalone Windows desktop host for the local N.E.K.O. web application."""

from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

MAIN_PORT = int(os.environ.get("NEKO_MAIN_SERVER_PORT", "48911"))
APP_URL = f"http://127.0.0.1:{MAIN_PORT}/"


def _backend_command() -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable, "--neko-webview-backend"]
    return [sys.executable, str(Path(__file__).with_name("launcher.py"))]


def _backend_mode() -> int:
    from launcher import start_launcher

    return int(start_launcher())


def _wait_for_backend(process: subprocess.Popen[bytes], timeout: float = 90.0) -> None:
    deadline = time.monotonic() + timeout
    health_url = f"http://127.0.0.1:{MAIN_PORT}/health"
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                f"N.E.K.O. backend exited before becoming ready (code {process.returncode})."
            )
        try:
            with urllib.request.urlopen(health_url, timeout=1):
                return
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(0.25)
    raise TimeoutError(f"N.E.K.O. backend did not become ready on port {MAIN_PORT}.")


def _stop_backend(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def main() -> int:
    try:
        import webview
    except ImportError as exc:
        raise RuntimeError(
            "The desktop WebView dependency is missing. Install pywebview before running."
        ) from exc

    backend = subprocess.Popen(_backend_command())
    try:
        _wait_for_backend(backend)
        webview.create_window("N.E.K.O", APP_URL, width=1280, height=820, min_size=(960, 640))
        webview.start()
        return 0
    finally:
        _stop_backend(backend)


if __name__ == "__main__":
    if sys.argv[1:] == ["--neko-webview-backend"]:
        raise SystemExit(_backend_mode())
    raise SystemExit(main())
