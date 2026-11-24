#!/usr/bin/env python3
"""Mede atraso de consistência eventual: POST lançamento → saldo refletir."""

from __future__ import annotations

import sys
import time
from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import get_saldo, health, now_iso, post_lancamento, save_result  # noqa: E402


def main() -> int:
    if not health("http://localhost:8001")["ok"] or not health("http://localhost:8002")["ok"]:
        print("Pré-requisito: lançamentos e consolidado UP.")
        save_result("atraso-saldo", {"executado_em": now_iso(), "passou": False, "motivo": "deps_down"})
        return 1

    data_ref = date.today()
    antes = get_saldo(data_ref)
    saldo_antes = Decimal(str((antes.get("body") or {}).get("saldo", "0"))) if antes["ok"] else Decimal("0")

    valor = Decimal("7.77")
    descricao = f"atraso-{uuid4().hex[:8]}"
    created = post_lancamento(
        tipo="CREDITO",
        valor=str(valor),
        descricao=descricao,
        data_lancamento=data_ref,
    )
    if not created["ok"]:
        save_result(
            "atraso-saldo",
            {"executado_em": now_iso(), "passou": False, "motivo": "post_falhou", "created": created},
        )
        return 1

    esperado = (saldo_antes + valor).quantize(Decimal("0.01"))
    t0 = time.perf_counter()
    observado = None
    tentativas = []
    timeout_s = 20.0

    while time.perf_counter() - t0 < timeout_s:
        atual = get_saldo(data_ref)
        tentativas.append(atual)
        if atual["ok"]:
            saldo_atual = Decimal(str((atual.get("body") or {}).get("saldo", "0")))
            if saldo_atual >= esperado:
                observado = saldo_atual
                break
        time.sleep(0.25)

    atraso_ms = round((time.perf_counter() - t0) * 1000, 2)
    passou = observado is not None and atraso_ms <= 5000  # alvo p95 < 5s (docs)

    evidence = {
        "executado_em": now_iso(),
        "criterio": "Lag consolidação (evento → saldo) — alvo p95 < 5s",
        "passou": passou,
        "saldo_antes": str(saldo_antes),
        "valor_lancado": str(valor),
        "saldo_esperado": str(esperado),
        "saldo_observado": str(observado) if observado is not None else None,
        "atraso_ms": atraso_ms,
        "timeout_s": timeout_s,
        "created": created,
        "tentativas": len(tentativas),
    }
    path = save_result("atraso-saldo", evidence)
    print(f"passou={passou} atraso_ms={atraso_ms} → {path}")
    return 0 if passou else 1


if __name__ == "__main__":
    raise SystemExit(main())
