# Evidência — Carga no consolidado (RNF-03/04)

## Critério

> Em dias de picos, o serviço de consolidado diário recebe 50 requisições por segundo, com no máximo 5% de perda de requisições.

## Como executar

```bash
python3 scripts/carga_consolidado.py --rps 50 --duration 10
```

## O que o script faz

- Dispara ~500 `GET /saldo` com pacing de 50 rps
- Mede sucesso/falha, RPS efetivo e latências (p50/p95/p99)

## Resultado

Ver JSON gerado: [carga-consolidado.json](carga-consolidado.json)

Passa se `resultado.perda_pct <= 5`.
