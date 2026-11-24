"""Utilitários compartilhados pelos scripts de evidência NFR."""

from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
RESULTADOS = ROOT / "docs" / "resultados"

LANCAMENTOS_URL = os.getenv("LANCAMENTOS_URL", "http://localhost:8001").rstrip("/")
CONSOLIDADO_URL = os.getenv("CONSOLIDADO_URL", "http://localhost:8002").rstrip("/")
TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "5.0"))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_result(name: str, payload: dict[str, Any]) -> Path:
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    path = RESULTADOS / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def health(url: str) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        response = httpx.get(f"{url}/health", timeout=TIMEOUT)
        return {
            "ok": response.status_code == 200,
            "status_code": response.status_code,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "body": response.text,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "status_code": None,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "error": str(exc),
        }


def post_lancamento(
    *,
    tipo: str = "CREDITO",
    valor: str = "10.00",
    descricao: str = "evidencia-nfr",
    data_lancamento: date | None = None,
) -> dict[str, Any]:
    data_lancamento = data_lancamento or date.today()
    started = time.perf_counter()
    try:
        response = httpx.post(
            f"{LANCAMENTOS_URL}/lancamentos",
            json={
                "tipo": tipo,
                "valor": valor,
                "descricao": descricao,
                "data_lancamento": data_lancamento.isoformat(),
            },
            timeout=TIMEOUT,
        )
        return {
            "ok": response.status_code == 201,
            "status_code": response.status_code,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "body": _safe_json(response),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "status_code": None,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "error": str(exc),
        }


def get_saldo(data_referencia: date | None = None) -> dict[str, Any]:
    data_referencia = data_referencia or date.today()
    started = time.perf_counter()
    try:
        response = httpx.get(
            f"{CONSOLIDADO_URL}/saldo",
            params={"data": data_referencia.isoformat()},
            timeout=TIMEOUT,
        )
        return {
            "ok": response.status_code == 200,
            "status_code": response.status_code,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "body": _safe_json(response),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "status_code": None,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "error": str(exc),
        }


def docker_compose(*args: str) -> dict[str, Any]:
    cmd = ["docker", "compose", *args]
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            cmd,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        return {
            "ok": completed.returncode == 0,
            "cmd": cmd,
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "cmd": cmd,
            "error": str(exc),
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        }


def wait_until(predicate, *, timeout_s: float = 30.0, interval_s: float = 0.5) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(interval_s)
    return False


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except Exception:  # noqa: BLE001
        return response.text
