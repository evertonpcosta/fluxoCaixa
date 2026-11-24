#!/usr/bin/env python3
"""Evidência RNF-02: eventos acumulados são processados após consolidado voltar."""

from __future__ import annotations

import sys
import time
from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    CONSOLIDADO_URL,
    LANCAMENTOS_URL,
    docker_compose,
    get_saldo,
    health,
    now_iso,
    post_lancamento,
    save_result,
    wait_until,
)


def main() -> int:
    steps: list[dict] = []
    data_ref = date.today()

    if not health(LANCAMENTOS_URL)["ok"]:
        save_result("recuperacao-outbox", {"executado_em": now_iso(), "passou": False, "motivo": "lancamentos_down"})
        return 1

    # Garante consolidado up para ler saldo base
    if not health(CONSOLIDADO_URL)["ok"]:
        docker_compose("start", "consolidado")
        wait_until(lambda: health(CONSOLIDADO_URL)["ok"], timeout_s=60)

    base = get_saldo(data_ref)
    saldo_antes = Decimal(str((base.get("body") or {}).get("saldo", "0"))) if base["ok"] else Decimal("0")
    steps.append({"step": "saldo_base", "resultado": base, "saldo_antes": str(saldo_antes)})

    stop = docker_compose("stop", "consolidado")
    steps.append({"step": "stop_consolidado", **stop})
    wait_until(lambda: not health(CONSOLIDADO_URL)["ok"], timeout_s=20)

    n = 5
    valor = Decimal("1.25")
    posts = []
    for i in range(n):
        posts.append(
            post_lancamento(
                tipo="CREDITO",
                valor=str(valor),
                descricao=f"recuperacao-{uuid4().hex[:6]}-{i}",
                data_lancamento=data_ref,
            )
        )
    steps.append({"step": "posts_com_down", "resultados": posts})
    if not all(p["ok"] for p in posts):
        save_result(
            "recuperacao-outbox",
            {"executado_em": now_iso(), "passou": False, "motivo": "posts_falharam", "steps": steps},
        )
        return 1

    start = docker_compose("start", "consolidado")
    steps.append({"step": "start_consolidado", **start})
    recovered = wait_until(lambda: health(CONSOLIDADO_URL)["ok"], timeout_s=60)
    steps.append({"step": "health_after_start", "recovered": recovered})

    esperado = (saldo_antes + (valor * n)).quantize(Decimal("0.01"))
    t0 = time.perf_counter()
    observado = None
    while time.perf_counter() - t0 < 45:
        atual = get_saldo(data_ref)
        if atual["ok"]:
            saldo_atual = Decimal(str((atual.get("body") or {}).get("saldo", "0")))
            if saldo_atual >= esperado:
                observado = saldo_atual
                break
        time.sleep(0.5)

    atraso_ms = round((time.perf_counter() - t0) * 1000, 2)
    passou = observado is not None

    evidence = {
        "executado_em": now_iso(),
        "criterio": "RNF-02 — eventos não consumidos são recuperáveis após retorno do consolidado",
        "passou": passou,
        "saldo_antes": str(saldo_antes),
        "lancamentos": n,
        "valor_unitario": str(valor),
        "saldo_esperado": str(esperado),
        "saldo_observado": str(observado) if observado is not None else None,
        "recuperacao_ms": atraso_ms,
        "steps": steps,
    }
    path = save_result("recuperacao-outbox", evidence)
    print(f"passou={passou} recuperacao_ms={atraso_ms} → {path}")
    return 0 if passou else 1


if __name__ == "__main__":
    raise SystemExit(main())
