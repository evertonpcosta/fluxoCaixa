#!/usr/bin/env python3
"""Demonstra que lançamentos seguem com o consolidado parado.

Passos:
1. Confirma saldo atual
2. Para o serviço consolidado (docker compose stop consolidado)
3. Registra créditos e débitos
4. Confirma HTTP 201
5. Sobe o consolidado de novo
6. Espera o saldo fechar sem duplicidade

Uso (com Compose no ar):
  python3 scripts/isolamento_consolidado.py
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
import urllib.error
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


def saldo(url: str, comerciante: str, dia: str) -> dict:
    _, payload = http_json("GET", f"{url}/v1/saldos/{comerciante}?data={dia}")
    return payload


def docker_bin() -> str:
    for candidato in ("docker.exe", "docker"):
        from shutil import which

        encontrado = which(candidato)
        if encontrado:
            return encontrado
    raise RuntimeError("docker não encontrado no PATH")


def compose(*args: str) -> None:
    cmd = [docker_bin(), "compose", *args]
    subprocess.run(cmd, check=True)


def esperar_saldo(url: str, comerciante: str, dia: str, esperado: Decimal, tentativas: int = 60) -> dict:
    ultimo = {}
    for _ in range(tentativas):
        try:
            atual = saldo(url, comerciante, dia)
            ultimo = atual
            if Decimal(atual["saldo"]) == esperado:
                return atual
        except Exception:  # noqa: BLE001
            pass
        time.sleep(1)
    raise RuntimeError(f"saldo não convergiu; ultimo={ultimo} esperado={esperado}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lancamentos", default="http://localhost:8001")
    parser.add_argument("--consolidado", default="http://localhost:8002")
    parser.add_argument("--data", default=date.today().isoformat())
    parser.add_argument("--saida", default="docs/resultados/isolamento-consolidado.json")
    args = parser.parse_args()

    comerciante = str(uuid4())
    movimentos = [
        ("CREDITO", "100.00"),
        ("DEBITO", "30.00"),
        ("CREDITO", "20.50"),
        ("DEBITO", "5.00"),
    ]
    esperado = Decimal("85.50")
    aceitos = []

    inicio = datetime.now(timezone.utc).isoformat()
    compose("stop", "consolidado")

    consolidado_fora = False
    try:
        http_json("GET", f"{args.consolidado}/health", timeout=2)
    except Exception:  # noqa: BLE001
        consolidado_fora = True

    for tipo, valor in movimentos:
        status, payload = http_json(
            "POST",
            f"{args.lancamentos}/v1/lancamentos",
            {
                "comerciante_id": comerciante,
                "tipo": tipo,
                "valor": valor,
                "descricao": f"isolamento-{tipo.lower()}",
                "data_lancamento": args.data,
            },
        )
        if status != 201:
            raise RuntimeError(f"lançamento recusado status={status}")
        aceitos.append(payload)

    compose("start", "consolidado")
    for _ in range(30):
        try:
            http_json("GET", f"{args.consolidado}/health", timeout=2)
            break
        except Exception:  # noqa: BLE001
            time.sleep(1)
    else:
        raise RuntimeError("consolidado não voltou")

    final = esperar_saldo(args.consolidado, comerciante, args.data, esperado)
    # segunda leitura após espera curta: se houvesse duplicidade o saldo mudaria
    time.sleep(3)
    conferido = saldo(args.consolidado, comerciante, args.data)

    relatorio = {
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "inicio": inicio,
        "ambiente": {
            "lancamentos": args.lancamentos,
            "consolidado": args.consolidado,
            "data": args.data,
            "comerciante_id": comerciante,
        },
        "procedimento": [
            "docker compose stop consolidado",
            "POST /v1/lancamentos com créditos e débitos",
            "docker compose start consolidado",
            "GET /v1/saldos até convergência",
        ],
        "resultado": {
            "consolidado_indisponivel_durante_escrita": consolidado_fora,
            "lancamentos_aceitos": len(aceitos),
            "ids": [item["id"] for item in aceitos],
            "saldo_esperado": f"{esperado:.2f}",
            "saldo_final": conferido["saldo"],
            "total_creditos": conferido["total_creditos"],
            "total_debitos": conferido["total_debitos"],
            "sem_duplicidade": Decimal(conferido["saldo"]) == esperado
            and Decimal(final["saldo"]) == Decimal(conferido["saldo"]),
        },
    }

    saida = Path(args.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps(relatorio, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(relatorio["resultado"], indent=2, ensure_ascii=False))
    print(f"relatorio={saida}")


if __name__ == "__main__":
    main()
