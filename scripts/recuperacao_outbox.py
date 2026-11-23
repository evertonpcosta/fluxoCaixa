#!/usr/bin/env python3
"""Simula perda de eventos na fila e reconstrói o saldo via republicação.

1. Cria lançamentos
2. Espera o saldo
3. Apaga o stream Redis (perda prolongada / truncamento)
4. Zera o banco do consolidado para o comerciante/dia
5. Chama POST /v1/outbox/republicar
6. Confere se o saldo volta sem duplicidade

Uso:
  python3 scripts/recuperacao_outbox.py
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
import urllib.request
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4


def http_json(method: str, url: str, body: dict | None = None, timeout: float = 10.0):
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode()
        return resp.status, json.loads(raw) if raw else {}


def docker_bin() -> str:
    from shutil import which

    for candidato in ("docker.exe", "docker"):
        encontrado = which(candidato)
        if encontrado:
            return encontrado
    raise RuntimeError("docker não encontrado no PATH")


def redis_cli(*args: str) -> str:
    cmd = [docker_bin(), "compose", "exec", "-T", "redis", "redis-cli", *args]
    return subprocess.check_output(cmd, text=True).strip()


def psql(database: str, sql: str) -> str:
    cmd = [
        docker_bin(),
        "compose",
        "exec",
        "-T",
        "postgres",
        "psql",
        "-U",
        "fluxo",
        "-d",
        database,
        "-t",
        "-A",
        "-c",
        sql,
    ]
    return subprocess.check_output(cmd, text=True).strip()


def esperar_saldo(url: str, comerciante: str, dia: str, esperado: Decimal, tentativas: int = 60) -> dict:
    ultimo = {}
    for _ in range(tentativas):
        _, atual = http_json("GET", f"{url}/v1/saldos/{comerciante}?data={dia}")
        ultimo = atual
        if Decimal(atual["saldo"]) == esperado:
            return atual
        time.sleep(1)
    raise RuntimeError(f"saldo não convergiu; ultimo={ultimo} esperado={esperado}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lancamentos", default="http://localhost:8001")
    parser.add_argument("--consolidado", default="http://localhost:8002")
    parser.add_argument("--data", default=date.today().isoformat())
    parser.add_argument("--saida", default="docs/resultados/recuperacao-outbox.json")
    args = parser.parse_args()

    comerciante = str(uuid4())
    movimentos = [
        ("CREDITO", "70.00"),
        ("DEBITO", "15.25"),
        ("CREDITO", "10.00"),
    ]
    esperado = Decimal("64.75")
    ids = []

    for tipo, valor in movimentos:
        status, payload = http_json(
            "POST",
            f"{args.lancamentos}/v1/lancamentos",
            {
                "comerciante_id": comerciante,
                "tipo": tipo,
                "valor": valor,
                "descricao": "recuperacao",
                "data_lancamento": args.data,
            },
        )
        if status != 201:
            raise RuntimeError(f"falha ao lançar status={status}")
        ids.append(payload["id"])

    saldo_inicial = esperar_saldo(args.consolidado, comerciante, args.data, esperado)

    # perda da fila
    redis_cli("DEL", "fluxo.lancamentos")
    tamanho_stream = redis_cli("XLEN", "fluxo.lancamentos")

    # remove o estado do consolidado para o dia (como se o consumidor nunca tivesse visto)
    ids_sql = ",".join(f"'{i}'" for i in ids)
    psql("consolidado", f"DELETE FROM eventos_processados WHERE evento_id IN ({ids_sql});")
    psql(
        "consolidado",
        f"DELETE FROM saldos_diarios WHERE comerciante_id = '{comerciante}' AND data = '{args.data}';",
    )

    _, apos_perda = http_json("GET", f"{args.consolidado}/v1/saldos/{comerciante}?data={args.data}")
    status, republicado = http_json(
        "POST",
        f"{args.lancamentos}/v1/outbox/republicar",
        {"data_inicio": args.data, "data_fim": args.data},
    )
    if status != 200:
        raise RuntimeError(f"republicar falhou status={status}")

    saldo_final = esperar_saldo(args.consolidado, comerciante, args.data, esperado)
    time.sleep(3)
    conferido = http_json("GET", f"{args.consolidado}/v1/saldos/{comerciante}?data={args.data}")[1]

    relatorio = {
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "ambiente": {
            "lancamentos": args.lancamentos,
            "consolidado": args.consolidado,
            "data": args.data,
            "comerciante_id": comerciante,
        },
        "procedimento": [
            "criar lançamentos e esperar saldo",
            "DEL fluxo.lancamentos no Redis",
            "apagar eventos_processados e saldos_diarios do dia",
            "POST /v1/outbox/republicar",
            "esperar reconstrução do saldo",
        ],
        "resultado": {
            "ids": ids,
            "saldo_antes_da_perda": saldo_inicial["saldo"],
            "stream_apos_del": tamanho_stream,
            "saldo_apos_perda": apos_perda["saldo"],
            "marcados_para_republicar": republicado.get("marcados"),
            "saldo_reconstruido": conferido["saldo"],
            "sem_duplicidade": Decimal(conferido["saldo"]) == esperado,
            "recuperacao_ok": Decimal(conferido["saldo"]) == esperado,
        },
    }

    saida = Path(args.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps(relatorio, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(relatorio["resultado"], indent=2, ensure_ascii=False))
    print(f"relatorio={saida}")


if __name__ == "__main__":
    main()
