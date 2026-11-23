#!/usr/bin/env python3
"""Carga no consolidado: ~50 req/s na consulta de saldo.

Uso:
  python3 scripts/carga_consolidado.py --url http://localhost:8002 --rps 50 --segundos 60
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path


def consultar(url: str, timeout: float) -> tuple[str, float]:
    inicio = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resposta:
            codigo = resposta.status
            resposta.read()
        return ("ok" if 200 <= codigo < 400 else f"http_{codigo}", time.perf_counter() - inicio)
    except urllib.error.HTTPError as exc:
        return (f"http_{exc.code}", time.perf_counter() - inicio)
    except TimeoutError:
        return ("timeout", time.perf_counter() - inicio)
    except Exception as exc:  # noqa: BLE001
        nome = type(exc).__name__.lower()
        if "timeout" in nome or "timed out" in str(exc).lower():
            return ("timeout", time.perf_counter() - inicio)
        return (f"erro:{type(exc).__name__}", time.perf_counter() - inicio)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8002")
    parser.add_argument("--comerciante", default="11111111-1111-1111-1111-111111111111")
    parser.add_argument("--data", default="2026-11-23")
    parser.add_argument("--rps", type=int, default=50)
    parser.add_argument("--segundos", type=int, default=60)
    parser.add_argument("--timeout", type=float, default=2.0)
    parser.add_argument(
        "--saida",
        default="docs/resultados/carga-consolidado.json",
    )
    args = parser.parse_args()

    alvo = f"{args.url.rstrip('/')}/v1/saldos/{args.comerciante}?data={args.data}"
    total = args.rps * args.segundos
    intervalo = 1.0 / args.rps
    inicio = time.perf_counter()
    resultados: list[tuple[str, float]] = []

    with ThreadPoolExecutor(max_workers=args.rps * 2) as pool:
        futuros = []
        for i in range(total):
            alvo_envio = inicio + (i * intervalo)
            espera = alvo_envio - time.perf_counter()
            if espera > 0:
                time.sleep(espera)
            futuros.append(pool.submit(consultar, alvo, args.timeout))
        for futuro in as_completed(futuros):
            resultados.append(futuro.result())

    duracao = time.perf_counter() - inicio
    ok = sum(1 for status, _ in resultados if status == "ok")
    timeouts = sum(1 for status, _ in resultados if status == "timeout")
    erros = total - ok
    perda = (erros / total) * 100 if total else 0.0
    latencias = [lat for status, lat in resultados if status == "ok"]
    por_status: dict[str, int] = {}
    for status, _ in resultados:
        por_status[status] = por_status.get(status, 0) + 1

    relatorio = {
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "ambiente": {
            "alvo": alvo,
            "rps_alvo": args.rps,
            "duracao_planejada_s": args.segundos,
            "timeout_s": args.timeout,
            "workers": args.rps * 2,
        },
        "resultado": {
            "duracao_real_s": round(duracao, 3),
            "volume_enviado": total,
            "sucesso": ok,
            "erros": erros,
            "timeouts": timeouts,
            "perda_percentual": round(perda, 3),
            "rps_efetivo": round(total / duracao, 3) if duracao else 0,
            "latencia_p50_ms": round(statistics.median(latencias) * 1000, 3) if latencias else None,
            "latencia_p95_ms": (
                round(sorted(latencias)[max(0, int(len(latencias) * 0.95) - 1)] * 1000, 3)
                if latencias
                else None
            ),
            "por_status": por_status,
            "meta_perda_maxima_percentual": 5.0,
            "meta_atingida": perda <= 5.0,
        },
    }

    saida = Path(args.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps(relatorio, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    resumo = (
        f"enviados={total} ok={ok} erros={erros} timeouts={timeouts} "
        f"perda={perda:.3f}% duracao={duracao:.2f}s meta={'OK' if perda <= 5 else 'FALHOU'}"
    )
    print(resumo)
    print(f"relatorio={saida}")


if __name__ == "__main__":
    main()
