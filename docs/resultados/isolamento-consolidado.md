# Isolamento: lançamentos com consolidado parado

## Procedimento

```bash
python3 scripts/isolamento_consolidado.py
```

O script:

1. `docker compose stop consolidado`
2. Registra 4 lançamentos (créditos e débitos) em `/v1/lancamentos`
3. Confirma HTTP 201 com o consolidado fora
4. `docker compose start consolidado`
5. Espera o saldo convergir e confere se não duplicou

## Resultado

| Checagem | Valor |
| --- | --- |
| Consolidado indisponível na escrita | sim |
| Lançamentos aceitos | 4 |
| Saldo esperado | 85.50 |
| Saldo final | 85.50 |
| Créditos / débitos | 120.50 / 35.00 |
| Sem duplicidade | sim |

JSON bruto: [isolamento-consolidado.json](isolamento-consolidado.json).
