"""Clientes HTTP para as APIs de Lançamentos e Consolidado."""

from __future__ import annotations

import os
from datetime import date
from decimal import Decimal
from typing import Any

import httpx

LANCAMENTOS_URL = os.getenv("LANCAMENTOS_URL", "http://localhost:8001").rstrip("/")
CONSOLIDADO_URL = os.getenv("CONSOLIDADO_URL", "http://localhost:8002").rstrip("/")
TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "5.0"))


class ApiError(Exception):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class ServiceUnavailable(ApiError):
    """Serviço inacessível (timeout, conexão, 5xx)."""


def _raise_for_response(response: httpx.Response, service: str) -> None:
    if response.status_code >= 500:
        raise ServiceUnavailable(
            f"{service} retornou {response.status_code}",
            status_code=response.status_code,
        )
    if response.status_code >= 400:
        detail = response.text
        try:
            payload = response.json()
            detail = str(payload.get("detail", payload))
        except Exception:  # noqa: BLE001
            pass
        raise ApiError(detail, status_code=response.status_code)


def health(url: str) -> tuple[bool, str]:
    try:
        response = httpx.get(f"{url}/health", timeout=TIMEOUT)
        if response.status_code == 200:
            return True, response.text
        return False, f"HTTP {response.status_code}: {response.text}"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def criar_lancamento(
    *,
    tipo: str,
    valor: Decimal | str,
    descricao: str,
    data_lancamento: date,
) -> dict[str, Any]:
    payload = {
        "tipo": tipo,
        "valor": str(valor),
        "descricao": descricao,
        "data_lancamento": data_lancamento.isoformat(),
    }
    try:
        response = httpx.post(
            f"{LANCAMENTOS_URL}/lancamentos",
            json=payload,
            timeout=TIMEOUT,
        )
    except httpx.RequestError as exc:
        raise ServiceUnavailable(f"Lançamentos indisponível: {exc}") from exc

    _raise_for_response(response, "Lançamentos")
    return response.json()


def listar_lancamentos(
    *,
    data_filtro: date | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    params: dict[str, Any] = {"limit": limit}
    if data_filtro is not None:
        params["data"] = data_filtro.isoformat()
    try:
        response = httpx.get(
            f"{LANCAMENTOS_URL}/lancamentos",
            params=params,
            timeout=TIMEOUT,
        )
    except httpx.RequestError as exc:
        raise ServiceUnavailable(f"Lançamentos indisponível: {exc}") from exc

    _raise_for_response(response, "Lançamentos")
    return response.json()


def consultar_saldo(data_referencia: date) -> dict[str, Any]:
    try:
        response = httpx.get(
            f"{CONSOLIDADO_URL}/saldo",
            params={"data": data_referencia.isoformat()},
            timeout=TIMEOUT,
        )
    except httpx.RequestError as exc:
        raise ServiceUnavailable(f"Consolidado indisponível: {exc}") from exc

    _raise_for_response(response, "Consolidado")
    return response.json()
