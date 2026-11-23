# Atraso do saldo (meta 5s)

Meta de operação normal: após o `POST /v1/lancamentos` retornar 201, o `GET /v1/saldos` deve refletir o movimento em até 5 segundos.

## Comando

```bash
python3 scripts/atraso_saldo.py --amostras 20
```

O script mede, amostra a amostra, o tempo entre o 201 e a primeira leitura do saldo com o valor esperado.

## Resultado

| Métrica | Valor |
| --- | --- |
| Amostras | 20 |
| Atraso p50 | 0.5115 s |
| Atraso p95 | 0.5465 s |
| Atraso máximo | 0.5476 s |
| Amostras dentro da meta | 20 / 20 |
| Meta ≤ 5s | atingida |

JSON bruto: [atraso-saldo.json](atraso-saldo.json).
