#!/usr/bin/env python3
"""Evidência RNF-01: lançamentos permanecem disponíveis com consolidado DOWN."""

from __future__ import annotations

import sys
from pathlib import Path

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
    passed = True

    steps.append({"step": "baseline_health", "lancamentos": health(LANCAMENTOS_URL), "consolidado": health(CONSOLIDADO_URL)})
    if not steps[-1]["lancamentos"]["ok"]:
        print("Pré-requisito: API lançamentos precisa estar UP.")
        save_result(
            "isolamento-consolidado",
            {"executado_em": now_iso(), "passou": False, "motivo": "lancamentos_down", "steps": steps},
        )
        return 1

    stop = docker_compose("stop", "consolidado")
    steps.append({"step": "stop_consolidado", **stop})
    if not stop["ok"]:
        passed = False

    wait_until(lambda: not health(CONSOLIDADO_URL)["ok"], timeout_s=20)
    steps.append({"step": "consolidado_down_check", "consolidado": health(CONSOLIDADO_URL)})

    resultados_post = [post_lancamento(descricao=f"isolamento-{i}") for i in range(5)]
    steps.append({"step": "posts_com_consolidado_down", "resultados": resultados_post})
    if not all(r["ok"] for r in resultados_post):
        passed = False

    saldo = get_saldo()
    steps.append({"step": "get_saldo_esperado_falhar", "resultado": saldo})
    if saldo["ok"]:
        # Se ainda estiver up, o stop falhou — marca como falha do teste
        passed = False

    start = docker_compose("start", "consolidado")
    steps.append({"step": "start_consolidado", **start})
    recovered = wait_until(lambda: health(CONSOLIDADO_URL)["ok"], timeout_s=60)
    steps.append({"step": "consolidado_up_check", "recovered": recovered, "consolidado": health(CONSOLIDADO_URL)})
    if not recovered:
        passed = False

    evidence = {
        "executado_em": now_iso(),
        "criterio": "RNF-01 — serviço de lançamentos não fica indisponível se consolidado cair",
        "passou": passed,
        "resumo": {
            "posts_ok": sum(1 for r in resultados_post if r["ok"]),
            "posts_total": len(resultados_post),
            "saldo_falhou_como_esperado": not saldo["ok"],
            "consolidado_recuperado": recovered,
        },
        "steps": steps,
    }
    path = save_result("isolamento-consolidado", evidence)
    print(f"passou={passed} → {path}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
