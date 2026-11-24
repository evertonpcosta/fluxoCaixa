# Evidência — Recuperação após outage (RNF-02)

## Critério

> Eventos não consumidos devem ser recuperáveis após retorno do consolidado (zero perda de lançamentos aceitos).

## Como executar

```bash
python3 scripts/recuperacao_outbox.py
```

## O que o script faz

1. Lê saldo base
2. Para o consolidado
3. Cria 5 lançamentos (devem ser aceitos)
4. Sobe o consolidado novamente
5. Aguarda o saldo alcançar o valor esperado (drain da fila/outbox)

## Resultado

Ver JSON gerado: [recuperacao-outbox.json](recuperacao-outbox.json)

Passa se `saldo_observado >= saldo_esperado` após o recover.
