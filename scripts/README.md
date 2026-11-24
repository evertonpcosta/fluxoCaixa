# Scripts de evidência NFR

Pré-requisitos: stack no ar (`docker compose up -d --build`) e Python com `httpx`.

```bash
pip install -r scripts/requirements.txt
```

| Script | Critério | Saída |
|---|---|---|
| `isolamento_consolidado.py` | RNF-01 — lançamentos UP com consolidado DOWN | `docs/resultados/isolamento-consolidado.json` |
| `carga_consolidado.py` | RNF-03/04 — ~50 rps, perda ≤ 5% | `docs/resultados/carga-consolidado.json` |
| `atraso_saldo.py` | Lag evento → saldo (alvo &lt; 5s) | `docs/resultados/atraso-saldo.json` |
| `recuperacao_outbox.py` | RNF-02 — drain após recover | `docs/resultados/recuperacao-outbox.json` |

## Ordem sugerida

```bash
# 1) atraso (stack saudável)
python3 scripts/atraso_saldo.py

# 2) carga
python3 scripts/carga_consolidado.py --rps 50 --duration 10

# 3) isolamento (para/reinicia consolidado)
python3 scripts/isolamento_consolidado.py

# 4) recuperação outbox (para/reinicia consolidado)
python3 scripts/recuperacao_outbox.py
```

Resumos em Markdown: `docs/resultados/*.md`.
