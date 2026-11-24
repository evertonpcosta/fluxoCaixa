# Evidência — Isolamento do consolidado (RNF-01)

## Critério

> O serviço de controle de lançamento não deve ficar indisponível se o sistema de consolidado diário cair.

## Como executar

```bash
python3 scripts/isolamento_consolidado.py
```

## O que o script faz

1. Confere health de lançamentos/consolidado
2. `docker compose stop consolidado`
3. Envia 5 `POST /lancamentos` (devem retornar 201)
4. Tenta `GET /saldo` (deve falhar)
5. `docker compose start consolidado` e aguarda recover

## Resultado

Ver JSON gerado: [isolamento-consolidado.json](isolamento-consolidado.json)

Interpretação esperada:

- `resumo.posts_ok == posts_total`
- `resumo.saldo_falhou_como_esperado == true`
- `passou == true`
