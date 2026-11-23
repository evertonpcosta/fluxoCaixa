#!/usr/bin/env python3
"""Mede o atraso entre o commit do lançamento e o saldo refletir o valor.

Uso:
  python3 scripts/atraso_saldo.py --amostras 20
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.request
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4


def http_json(method: str, url: str, body: dict | None = None, timeout: float = 5.0):
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode()
        return resp.status, json.loads(raw) if raw else {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lancamentos", default="http://localhost:8001")
    parser.add_argument("--consolidado", default="http://localhost:8002")
    parser.add_argument("--amostras", type=int, default=20)
    parser.add_argument("--meta_s", type=float, default=5.0)
    parser.add_argument("--saida", default="docs/resultados/atraso-saldo.json")
    args = parser.parse_args()

    dia = date.today().isoformat()
    comerciante = str(uuid4())
    atrasos: list[float] = []
    detalhes = []

    for i in range(args.amostras):
        valor = Decimal("1.00")
        # saldo acumulado esperado após esta amostra
        esperado = valor * (i + 1)
        t0 = time.perf_counter()
        status, _ = http_json(
            "POST",
            f"{args.lancamentos}/v1/lancamentos",
            {
                "comerciante_id": comerciante,
                "tipo": "CREDITO",
                "valor": f"{valor:.2f}",
                "descricao": f"atraso-{i}",
                "data_lancamento": dia,
            },
        )
        if status != 201:
            raise RuntimeError(f"lançamento falhou status={status}")

        while True:
            _, saldo = http_json(
                "GET",
                f"{args.consolidado}/v1/saldos/{comerciante}?data={dia}",
            )
            if Decimal(saldo["saldo"]) == esperado:
                atraso = time.perf_counter() - t0
                atrasos.append(atraso)
                detalhes.append({"amostra": i + 1, "atraso_s": round(atraso, 4)})
                break
            if time.perf_counter() - t0 > args.meta_s * 4:
                raise RuntimeError(f"saldo não convergiu na amostra {i + 1}")
            time.sleep(0.05)

    relatorio = {
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "ambiente": {
            "lancamentos": args.lancamentos,
            "consolidado": args.consolidado,
            "amostras": args.amostras,
            "meta_s": args.meta_s,
            "comerciante_id": comerciante,
            "data": dia,
        },
        "resultado": {
            "atraso_p50_s": round(statistics.median(atrasos), 4),
            "atraso_p95_s": round(sorted(atrasos)[max(0, int(len(atrasos) * 0.95) - 1)], 4),
            "atraso_max_s": round(max(atrasos), 4),
            "atraso_medio_s": round(statistics.mean(atrasos), 4),
            "amostras_dentro_da_meta": sum(1 for a in atrasos if a <= args.meta_s),
            "meta_atingida": max(atrasos) <= args.meta_s,
            "detalhes": detalhes,
        },
    }

    saida = Path(args.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps(relatorio, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(relatorio["resultado"], indent=2, ensure_ascii=False))
    print(f"relatorio={saida}")


if __name__ == "__main__":
    main()
