# Monitoramento e observabilidade

Stack de observabilidade **faz parte da arquitetura alvo** e sobe junto com o `docker-compose`.

## Pilares

| Pilar | MVP (Compose) | Evolução |
|---|---|---|
| Logs | stdout dos containers (`docker compose logs`) | Loki / ELK |
| Métricas | **Prometheus** coleta + **Grafana** dashboards | Alertmanager |
| Traces | `X-Request-Id` / `event_id` nos logs | OpenTelemetry |

## Arquitetura da stack

```text
API Lançamentos ──/metrics──► Prometheus ──► Grafana
API Consolidado ──/metrics──┘      ▲
RabbitMQ ────────/metrics──────────┘
```

| Componente | Porta | Função |
|---|---|---|
| Prometheus | `9090` | Scrape e armazenamento de métricas |
| Grafana | `3000` | Dashboards e exploração (admin/admin) |
| APIs | `8001`, `8002` | Exportam `/metrics` (formato Prometheus) |
| RabbitMQ | `15692` | Plugin `rabbitmq_prometheus` |

Datasource e dashboard base são **provisionados automaticamente** em:

- `infra/prometheus/prometheus.yml`
- `infra/grafana/provisioning/`
- `infra/grafana/dashboards/`

## Métricas por componente

### API Lançamentos

- Taxa de `POST /lancamentos` (sucesso/4xx/5xx)
- Latência HTTP (histogram)
- Lag do outbox (gauge: pendentes)
- Falhas de publish no RabbitMQ

### API Consolidado

- Taxa de `GET /saldo` (meta: ~50 rps, perda ≤ 5%)
- Latência p95/p99 da consulta
- Throughput do consumer (msgs/s)
- Erros de processamento / requeues

### RabbitMQ

- Queue depth
- Consumers ativos
- Unacked / ready messages
- Publish/deliver rates

### Frontend

- Erros/timeouts tratados na UI (sinal de degradação do consolidado)
- Métricas HTTP do front ficam como evolução (foco nos backends + broker no MVP)

## Healthchecks

| Endpoint | Significado |
|---|---|
| `GET /health` | Processo no ar (liveness) |
| `GET /metrics` | Exposição Prometheus |

Para **lançamentos**, readiness **não** depende do consolidado (RNF-01).

## SLIs / SLOs

| SLI | SLO |
|---|---|
| Disponibilidade POST lançamentos | 99.9% (produção sugerido) |
| Sucesso GET saldo sob carga | ≥ 95% (máx. 5% perda) |
| Lag consolidação (evento → saldo) | p95 &lt; 5 s |
| Outbox pendente | Alerta se crescer sem drenagem |

## Alertas mínimos (produção / Grafana Alerting)

1. Fila crescendo sem consumer
2. Taxa de erro 5xx acima do limiar
3. Outbox sem drenagem
4. Latência p95 do saldo acima do alvo

## Como acessar localmente

```bash
docker compose up -d
# Grafana:     http://localhost:3000  (admin / admin)
# Prometheus:  http://localhost:9090
```

## Popular o dashboard (obrigatório para ver gráficos)

Os targets sobem automaticamente, mas **sem tráfego de negócio os painéis ficam vazios**.

```bash
# opção 1 — script no host
pip install -r scripts/requirements.txt
python3 scripts/gerar_observabilidade.py

# opção 2 — container one-shot
docker compose --profile obs up --build gerar-observabilidade
```

Passo a passo (Grafana + PromQL): [`como-usar-observabilidade.md`](como-usar-observabilidade.md)
