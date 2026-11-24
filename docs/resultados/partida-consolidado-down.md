# Evidência — Partida com consolidado DOWN

## Critério

Publisher declara exchange+fila+bind **antes** de publicar, exige **confirmação do broker** e só então marca o outbox. Com consolidado parado, os eventos ficam na fila e são drenados no recover.

## Como executar

```bash
python3 scripts/partida_consolidado_down.py
```

## Resultado

Ver [partida-consolidado-down.json](partida-consolidado-down.json).
