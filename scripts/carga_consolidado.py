#!/usr/bin/env python3
"""Evidência RNF-03/04: carga ~50 req/s no consolidado, perda ≤ 5%."""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import CONSOLIDADO_URL, get_saldo, health, now_iso, save_result  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Carga no GET /saldo")
    parser.add_argument("--rps", type=float, default=50.0, help="Requisições por segundo alvo")
    parser.add_argument("--duration", type=float, default=10.0, help="Duração em segundos")
    parser.add_argument("--workers", type=int, default=32, help="Threads concorrentes")
    parser.add_argument(
        "--min-rps-ratio",
        type=float,
        default=0.90,
        help="Fração mínima do RPS alvo para aprovar (ex.: 0.90 = 90%%)",
    )
    parser.add_argument(
        "--max-perda-pct",
        type=float,
        default=5.0,
        help="Perda máxima aceitável (%%)",
    )
    args = parser.parse_args()

    if not health(CONSOLIDADO_URL)["ok"]:
        print("Pré-requisito: API consolidado precisa estar UP.")
        save_result(
            "carga-consolidado",
            {"executado_em": now_iso(), "passou": False, "motivo": "consolidado_down"},
        )
        return 1

    total = max(1, int(args.rps * args.duration))
    interval = 1.0 / args.rps
    data_ref = date.today()
    latencies: list[float] = []
    sucesso = 0
    falha = 0
    erros: list[str] = []

    def one_call(_: int) -> dict:
        result = get_saldo(data_ref)
        return result

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = []
        for i in range(total):
            # pacing aproximado do RPS
            target = started + (i * interval)
            delay = target - time.perf_counter()
            if delay > 0:
                time.sleep(delay)
            futures.append(pool.submit(one_call, i))

        for fut in as_completed(futures):
            result = fut.result()
            latencies.append(result["latency_ms"])
            if result["ok"]:
                sucesso += 1
            else:
                falha += 1
                if len(erros) < 20:
                    erros.append(result.get("error") or str(result.get("status_code")))

    elapsed = time.perf_counter() - started
    perda_pct = (falha / total) * 100 if total else 0.0
    rps_efetivo = total / elapsed if elapsed else 0.0
    rps_minimo = args.rps * args.min_rps_ratio
    perda_ok = perda_pct <= args.max_perda_pct
    vazao_ok = rps_efetivo >= rps_minimo
    passou = perda_ok and vazao_ok

    latencies_sorted = sorted(latencies) if latencies else [0.0]

    def percentile(values: list[float], p: float) -> float:
        if not values:
            return 0.0
        k = (len(values) - 1) * p
        f = int(k)
        c = min(f + 1, len(values) - 1)
        if f == c:
            return values[f]
        return values[f] + (values[c] - values[f]) * (k - f)

    evidence = {
        "executado_em": now_iso(),
        "criterio": (
            f"RNF-03/04 — vazão ≥ {args.min_rps_ratio:.0%} de {args.rps} rps "
            f"e perda ≤ {args.max_perda_pct}%"
        ),
        "passou": passou,
        "config": {
            "rps_alvo": args.rps,
            "rps_minimo": round(rps_minimo, 2),
            "min_rps_ratio": args.min_rps_ratio,
            "max_perda_pct": args.max_perda_pct,
            "duration_s": args.duration,
            "workers": args.workers,
            "total_requests": total,
        },
        "resultado": {
            "elapsed_s": round(elapsed, 3),
            "rps_efetivo": round(rps_efetivo, 2),
            "vazao_ok": vazao_ok,
            "perda_ok": perda_ok,
            "sucesso": sucesso,
            "falha": falha,
            "perda_pct": round(perda_pct, 3),
            "latencia_ms": {
                "avg": round(statistics.mean(latencies_sorted), 2) if latencies_sorted else 0,
                "p50": round(percentile(latencies_sorted, 0.50), 2),
                "p95": round(percentile(latencies_sorted, 0.95), 2),
                "p99": round(percentile(latencies_sorted, 0.99), 2),
                "max": round(max(latencies_sorted), 2) if latencies_sorted else 0,
            },
            "erros_amostra": erros,
        },
    }
    path = save_result("carga-consolidado", evidence)
    print(
        f"passou={passou} rps={rps_efetivo:.1f}/{rps_minimo:.1f}min "
        f"perda={perda_pct:.2f}% vazao_ok={vazao_ok} perda_ok={perda_ok} "
        f"p95={evidence['resultado']['latencia_ms']['p95']}ms → {path}"
    )
    return 0 if passou else 1


if __name__ == "__main__":
    raise SystemExit(main())
