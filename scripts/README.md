# Scripts

Pré-requisitos: stack no ar (`docker compose up -d --build`) e Python com `httpx`.

```bash
pip install -r scripts/requirements.txt
```

## Observabilidade (Prometheus / Grafana)

Sem tráfego, o Grafana fica “vazio”. Gere dados assim:

```bash
# no host
python3 scripts/gerar_observabilidade.py

# ou via Compose (profile obs)
docker compose --profile obs up --build gerar-observabilidade
```

Guia completo: [`docs/arquitetura/como-usar-observabilidade.md`](../docs/arquitetura/como-usar-observabilidade.md)

| Script | Objetivo | Saída |
|---|---|---|
| `gerar_observabilidade.py` | Popular métricas no Prometheus/Grafana | `docs/resultados/gerar-observabilidade.json` |

## Evidências NFR

| Script | Critério | Saída |
|---|---|---|
| `isolamento_consolidado.py` | RNF-01 — lançamentos UP com consolidado DOWN | `docs/resultados/isolamento-consolidado.json` |
| `carga_consolidado.py` | RNF-03/04 — ~50 rps, perda ≤ 5% | `docs/resultados/carga-consolidado.json` |
| `atraso_saldo.py` | Lag evento → saldo (alvo &lt; 5s) | `docs/resultados/atraso-saldo.json` |
| `recuperacao_outbox.py` | RNF-02 — drain após recover | `docs/resultados/recuperacao-outbox.json` |
| `partida_consolidado_down.py` | Fila provisionada pelo publisher + drain após recover | `docs/resultados/partida-consolidado-down.json` |

### Ordem sugerida (NFR)

```bash
python3 scripts/atraso_saldo.py
python3 scripts/carga_consolidado.py --rps 50 --duration 10
python3 scripts/isolamento_consolidado.py
python3 scripts/recuperacao_outbox.py
python3 scripts/partida_consolidado_down.py
```

Resumos em Markdown: `docs/resultados/*.md`.
