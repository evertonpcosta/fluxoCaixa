#!/usr/bin/env python3
"""
Gera tráfego de negócio para popular Prometheus/Grafana.

Produz métricas usadas no dashboard FluxoCaixa — Overview:
  - http_requests_total / http_request_duration_seconds (APIs)
  - consolidado_events_processed_total (consumer)
  - outbox_pending / filas RabbitMQ (indiretamente via fluxo)

Uso:
  pip install -r scripts/requirements.txt
  python3 scripts/gerar_observabilidade.py
  python3 scripts/gerar_observabilidade.py --duration 120 --rps 8
"""

from __future__ import annotations

import argparse
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    CONSOLIDADO_URL,
    LANCAMENTOS_URL,
    TIMEOUT,
    get_saldo,
    health,
    now_iso,
    post_lancamento,
    save_result,
)
import httpx


def listar() -> dict:
    started = time.perf_counter()
    try:
        response = httpx.get(
            f"{LANCAMENTOS_URL}/lancamentos",
            params={"limit": 20},
            timeout=TIMEOUT,
        )
        return {
            "ok": response.status_code == 200,
            "status_code": response.status_code,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "latency_ms": 0}


def one_cycle(i: int, data_ref: date) -> dict:
    tipo = random.choice(["CREDITO", "DEBITO"])
    valor = Decimal(str(round(random.uniform(1, 50), 2)))
    created = post_lancamento(
        tipo=tipo,
        valor=str(valor),
        descricao=f"obs-{uuid4().hex[:8]}-{i}",
        data_lancamento=data_ref,
    )
    listed = listar()
    saldo = get_saldo(data_ref)
    return {
        "i": i,
        "post_ok": created.get("ok", False),
        "list_ok": listed.get("ok", False),
        "saldo_ok": saldo.get("ok", False),
        "lat_post": created.get("latency_ms"),
        "lat_saldo": saldo.get("latency_ms"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera dados de observabilidade")
    parser.add_argument("--duration", type=float, default=90.0, help="Duração em segundos")
    parser.add_argument("--rps", type=float, default=5.0, help="Ciclos por segundo (cada ciclo = post+list+saldo)")
    parser.add_argument("--workers", type=int, default=8, help="Threads")
    args = parser.parse_args()

    if not health(LANCAMENTOS_URL)["ok"]:
        print(f"API lançamentos DOWN ({LANCAMENTOS_URL}). Suba a stack antes.")
        return 1
    if not health(CONSOLIDADO_URL)["ok"]:
        print(f"API consolidado DOWN ({CONSOLIDADO_URL}). Suba a stack antes.")
        return 1

    total = max(1, int(args.rps * args.duration))
    interval = 1.0 / args.rps if args.rps > 0 else 0.2
    data_ref = date.today()

    print(
        f"Gerando observabilidade: {total} ciclos ≈ {args.rps} rps por {args.duration}s"
    )
    print(f"APIs: {LANCAMENTOS_URL} | {CONSOLIDADO_URL}")
    print("Grafana: http://localhost:3000  |  dashboard FluxoCaixa — Overview")
    print("Prometheus: http://localhost:9090")

    ok = 0
    fail = 0
    started = time.perf_counter()

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = []
        for i in range(total):
            target = started + (i * interval)
            delay = target - time.perf_counter()
            if delay > 0:
                time.sleep(delay)
            futures.append(pool.submit(one_cycle, i, data_ref))

        for fut in as_completed(futures):
            result = fut.result()
            if result["post_ok"] and result["saldo_ok"]:
                ok += 1
            else:
                fail += 1

    elapsed = time.perf_counter() - started
    evidence = {
        "executado_em": now_iso(),
        "objetivo": "Popular Prometheus/Grafana com métricas de negócio",
        "config": {
            "duration_s": args.duration,
            "rps": args.rps,
            "workers": args.workers,
            "ciclos": total,
        },
        "resultado": {
            "elapsed_s": round(elapsed, 2),
            "ciclos_ok": ok,
            "ciclos_fail": fail,
        },
        "proximos_passos": [
            "Abrir http://localhost:3000 (admin/admin)",
            "Dashboards → FluxoCaixa → FluxoCaixa — Overview",
            "Ajustar range para Last 15 minutes",
            "Explorar http://localhost:9090/graph com rate(http_requests_total[1m])",
        ],
    }
    path = save_result("gerar-observabilidade", evidence)
    print(f"ok={ok} fail={fail} elapsed={elapsed:.1f}s → {path}")
    print("Aguarde ~15–30s para o scrape do Prometheus e atualize o Grafana.")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
