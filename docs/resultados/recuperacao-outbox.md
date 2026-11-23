# Recuperação após perda da fila

O stream Redis não usa `MAXLEN`. Mesmo assim, se a fila for apagada ou truncada, a outbox no Postgres é a fonte de verdade. `POST /v1/outbox/republicar` marca o período e o publicador reenvia. O consolidado ignora `evento_id` já processado.

## Procedimento

```bash
python3 scripts/recuperacao_outbox.py
```

O script:

1. Cria lançamentos e espera o saldo
2. `DEL fluxo.lancamentos` no Redis
3. Remove `eventos_processados` e `saldos_diarios` do comerciante/dia
4. Chama `POST /v1/outbox/republicar`
5. Confere o saldo reconstruído

Republicação manual:

```bash
curl -s -X POST http://localhost:8001/v1/outbox/republicar \
  -H 'Content-Type: application/json' \
  -d '{"data_inicio":"2026-11-23","data_fim":"2026-11-23"}'
```

## Resultado

| Checagem | Valor |
| --- | --- |
| Saldo antes da perda | 64.75 |
| Tamanho do stream após `DEL` | 0 |
| Saldo após limpar o consolidado | 0.00 |
| Marcados para republicar | 7 |
| Saldo reconstruído | 64.75 |
| Sem duplicidade | sim |

Os 7 marcados incluem lançamentos do teste de isolamento no mesmo dia. A idempotência do consolidado evita somar de novo o que já estava certo para outros comerciantes; para o comerciante sob teste o saldo voltou ao valor esperado.

JSON bruto: [recuperacao-outbox.json](recuperacao-outbox.json).
