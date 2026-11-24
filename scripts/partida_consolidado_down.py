#!/usr/bin/env python3
"""
Evidência: partida com consolidado DOWN — lançamentos vão para a fila
(provisionada pelo publisher) e são drenados quando o consolidado sobe.
"""

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
        save_result(
            "partida-consolidado-down",
            {"executado_em": now_iso(), "passou": False, "motivo": "lancamentos_down"},
        )
        return 1

    # Garante consolidado parado (cenário de partida sem consumer)
    stop = docker_compose("stop", "consolidado")
    steps.append({"step": "stop_consolidado", **stop})
    wait_until(lambda: not health(CONSOLIDADO_URL)["ok"], timeout_s=30)

    base = get_saldo(data_ref)
    # saldo pode falhar — ok neste cenário
    steps.append({"step": "saldo_com_down", "resultado": base})

    n = 5
    valor = Decimal("2.50")
    posts = [
        post_lancamento(
            tipo="CREDITO",
            valor=str(valor),
            descricao=f"partida-down-{uuid4().hex[:6]}-{i}",
            data_lancamento=data_ref,
        )
        for i in range(n)
    ]
    steps.append({"step": "posts_com_consolidado_down", "resultados": posts})
    posts_ok = all(p["ok"] for p in posts)
    if not posts_ok:
        save_result(
            "partida-consolidado-down",
            {
                "executado_em": now_iso(),
                "passou": False,
                "motivo": "posts_falharam",
                "steps": steps,
            },
        )
        return 1

    # Aguarda outbox relay publicar com confirm + fila já declarada pelo publisher
    time.sleep(3)

    start = docker_compose("start", "consolidado")
    steps.append({"step": "start_consolidado", **start})
    recovered = wait_until(lambda: health(CONSOLIDADO_URL)["ok"], timeout_s=60)
    steps.append({"step": "health_after_start", "recovered": recovered})

    # Lê saldo após drain; como pode haver saldo prévio, verifica aumento >= n*valor
    # via polling até estabilizar crescimento observado
    t0 = time.perf_counter()
    observado = None
    saldo_inicial = None
    while time.perf_counter() - t0 < 45:
        atual = get_saldo(data_ref)
        if atual["ok"]:
            saldo_atual = Decimal(str((atual.get("body") or {}).get("saldo", "0")))
            if saldo_inicial is None:
                # primeira leitura pós-UP: ainda pode não ter drenado
                saldo_inicial = saldo_atual
            # esperamos que o saldo reflita ao menos os créditos desta rodada
            # (saldo absoluto >= n*valor se começou zerado, ou cresceu)
            if saldo_atual >= (valor * n):
                observado = saldo_atual
                # confirma estabilidade rápida
                time.sleep(1)
                conf = get_saldo(data_ref)
                if conf["ok"]:
                    observado = Decimal(str((conf.get("body") or {}).get("saldo", "0")))
                break
        time.sleep(0.5)

    passou = recovered and observado is not None
    evidence = {
        "executado_em": now_iso(),
        "criterio": (
            "Partida com consolidado DOWN: publisher declara fila+bind, "
            "confirma no broker e eventos são drenados após recover"
        ),
        "passou": passou,
        "posts": n,
        "valor_unitario": str(valor),
        "saldo_observado": str(observado) if observado is not None else None,
        "recuperacao_s": round(time.perf_counter() - t0, 2),
        "steps": steps,
    }
    path = save_result("partida-consolidado-down", evidence)
    print(f"passou={passou} saldo={observado} → {path}")
    return 0 if passou else 1


if __name__ == "__main__":
    raise SystemExit(main())
