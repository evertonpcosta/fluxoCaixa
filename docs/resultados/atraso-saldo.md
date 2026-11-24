# Evidência — Atraso do saldo (consistência eventual)

## Critério

Lag entre aceite do lançamento e atualização do saldo diário. Alvo documentado: p95 &lt; 5s.

## Como executar

```bash
python3 scripts/atraso_saldo.py
```

## O que o script faz

1. Lê saldo atual
2. Cria um crédito conhecido
3. Faz polling em `GET /saldo` até refletir (ou timeout 20s)

## Resultado

Ver JSON gerado: [atraso-saldo.json](atraso-saldo.json)

Passa se o saldo esperado aparecer em até 5s (`atraso_ms <= 5000`).
