# Carga no consolidado

Meta: 50 req/s por 60s, perda máxima de 5%.

## Comando

Com o stack no ar (`docker compose up --build -d`):

```bash
python3 scripts/carga_consolidado.py --url http://localhost:8002 --rps 50 --segundos 60
```

O script grava o JSON em `docs/resultados/carga-consolidado.json`.

## Ambiente da execução

- Host: Windows 11 + Docker Desktop 29.9.3
- Stack: `docker compose` local (Postgres 16, Redis 7, lançamentos, consolidado)
- Alvo: `GET /v1/saldos/{id}?data=2026-11-23`
- Timeout por requisição: 2s
- Workers: 100

## Resultado

| Métrica | Valor |
| --- | --- |
| Duração | 59.991 s |
| Volume enviado | 3000 |
| Sucesso | 3000 |
| Erros | 0 |
| Timeouts | 0 |
| Perda | 0.000% |
| RPS efetivo | 50.007 |
| Latência p50 | 5.018 ms |
| Latência p95 | 8.949 ms |
| Meta ≤ 5% | atingida |

JSON bruto: [carga-consolidado.json](carga-consolidado.json).
